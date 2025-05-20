import streamlit as st
import pandas as pd
import os
import json
from datetime import datetime
import traceback
from utils.fixed_youtube_api import YouTubeAPI
from utils.spotify_api import SpotifyAPI
from utils.openai_api import generate_blog_post, revamp_existing_blog
from utils.fixed_wordpress_api import WordPressAPI
from utils.corrected_csv_handler import load_csv, save_csv, create_empty_playlist_df
from utils.secrets_manager import get_secret

# Page configuration
st.set_page_config(
    page_title="Moments & Memories Blog Generator",
    page_icon="✨",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Force light mode
st.markdown("""
<style>
    /* Force light mode styles */
    .stApp {
        background-color: white !important;
        color: #1A2A44 !important;
    }
    .sidebar .sidebar-content {
        background-color: #F0F2F6 !important;
    }
    
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;500;600;700&family=Lato:wght@300;400;700&display=swap');

    /* Main text and headers */
    .stMarkdown, .stText, p, div {
        font-family: 'Lato', sans-serif;
        color: #1A2A44;
    }

    /* Headings */
    h1, h2, h3 {
        font-family: 'Playfair Display', serif;
        color: #1A2A44;
    }

    h1 {
        font-weight: 700;
        padding-bottom: 1.5rem;
        font-size: 2.5rem;
        color: #D4AF37;
    }
    
    /* Fix scrolling issues */
    .main .block-container {
        padding-bottom: 5rem;
        max-width: 95%;
    }
    
    /* Ensure containers can scroll properly */
    .stExpander {
        overflow: auto;
        max-height: 600px;
    }
</style>
""", unsafe_allow_html=True)

# Add header
st.markdown("""
<div style="padding: 1.5rem 0; margin-bottom: 2rem; border-bottom: 1px solid rgba(212, 175, 55, 0.3);">
    <h1>Moments & Memories Blog Generator</h1>
    <p style="font-family: 'Playfair Display', serif; font-size: 1.2rem; color: #1A2A44; margin-bottom: 0; font-style: italic;">
        Creating Moments & Memories, One Wedding at a Time
    </p>
</div>
""", unsafe_allow_html=True)

# Initialize session state
if 'df' not in st.session_state:
    st.session_state.df = None
if 'last_saved_csv' not in st.session_state:
    st.session_state.last_saved_csv = None
if 'auto_loaded' not in st.session_state:
    st.session_state.auto_loaded = False
    
# Functions for file management
def find_all_csv_files():
    """Find all available CSV files from previous sessions"""
    import glob
    import os
    
    # Look for all CSV files including user-uploaded ones
    csv_files = glob.glob("*.csv")
    
    if not csv_files:
        return []
    
    # Sort by modification time (newest first)
    csv_files.sort(key=os.path.getmtime, reverse=True)
    return csv_files

def find_latest_csv():
    """Find the most recently modified CSV file from previous sessions"""
    import glob
    import os
    
    # Look for processed CSV files
    csv_files = glob.glob("processed_playlists_*.csv")
    
    if not csv_files:
        return None
    
    # Get file with the latest modification time
    latest_file = max(csv_files, key=os.path.getmtime)
    return latest_file

def save_processed_csv(df, operation_type, overwrite_existing=False):
    """Save CSV with timestamp and operation type 
    If overwrite_existing is True, use the existing file if available instead of creating a new one"""
    
    if overwrite_existing and hasattr(st.session_state, 'last_saved_csv') and st.session_state.last_saved_csv:
        # Use the existing filename
        filename = st.session_state.last_saved_csv
    else:
        # Create a new filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"processed_playlists_{operation_type}_{timestamp}.csv"
        
    # Save the dataframe
    save_csv(df, filename)
    st.session_state.last_saved_csv = filename
    return filename

def save_blog_post(playlist_name, blog_content, title):
    """Save blog post to a file for persistence between sessions"""
    # Create blogs directory if it doesn't exist
    if not os.path.exists("blogs"):
        os.makedirs("blogs")
    
    # Clean the playlist name for use in filename
    clean_name = playlist_name.split('Wedding Cocktail Hour')[0].strip()
    # Remove any digits at the start (like "001 ")
    clean_name = re.sub(r'^\d+\s+', '', clean_name)
    clean_name = "".join([c if c.isalnum() or c.isspace() else "_" for c in clean_name]).strip()
    
    # Create filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"blogs/{clean_name}_{timestamp}.html"
    
    # Save blog as HTML with title
    with open(filename, "w") as f:
        f.write(f"<h1>{title}</h1>\n\n{blog_content}")
    
    return filename

def find_saved_blog_posts():
    """Find all saved blog posts in the blogs directory"""
    # Return empty list if directory doesn't exist
    if not os.path.exists("blogs"):
        return []
    
    # Get all HTML files in the blogs directory
    blog_files = [f for f in os.listdir("blogs") if f.endswith(".html")]
    
    # Sort by modification time (newest first)
    blog_files.sort(key=lambda x: os.path.getmtime(f"blogs/{x}"), reverse=True)
    
    return blog_files

def delete_saved_blog_post(filename):
    """Delete a saved blog post file"""
    try:
        file_path = os.path.join("blogs", filename)
        if os.path.exists(file_path):
            os.remove(file_path)
            return True
        return False
    except Exception as e:
        print(f"Error deleting blog post: {str(e)}")
        return False

def load_saved_blog_post(filename):
    """Load a saved blog post from a file"""
    try:
        with open(f"blogs/{filename}", "r") as f:
            content = f.read()
            
            # Extract title if available
            title = "Untitled Blog Post"
            if content.startswith("<h1>"):
                title_end = content.find("</h1>")
                if title_end > 0:
                    title = content[4:title_end]
                    content = content[title_end + 5:].strip()
            
            return title, content
    except Exception as e:
        st.error(f"Error loading blog post: {str(e)}")
        return "Error", f"Could not load blog post: {str(e)}"

def clean_playlist_name_for_blog(playlist_name):
    """Remove the numeric prefix from playlist names when creating blog posts"""
    import re
    # Remove the numeric prefix (like "001 ") 
    cleaned = re.sub(r'^\d{3}\s+', '', playlist_name)
    return cleaned

def process_playlist(playlist, youtube_api, spotify_api, operations, style_options=None):
    """
    Process a single playlist with error handling and progress tracking
    
    Parameters:
    - playlist: Name of the playlist to process
    - youtube_api: YouTube API client instance
    - spotify_api: Spotify API client instance
    - operations: List of operations to perform ('YouTube', 'Spotify', 'Blog')
    - style_options: Optional dictionary of style options for blog generation
    """
    try:
        # Filter dataframe to get only the songs for this playlist
        playlist_df = st.session_state.df[st.session_state.df['Playlist'] == playlist].copy()
        
        # Initialize an empty results dictionary
        results = {}
        
        # Save updates flag to track if we need to save the dataframe at the end
        save_updates = False
        
        # Fetch YouTube links if selected
        if "YouTube" in operations and youtube_api:
            # Check if we need to fetch YouTube links
            missing_links = playlist_df[
                (playlist_df['YouTube_Link'].isna()) | 
                (playlist_df['YouTube_Link'] == '')
            ]
            
            # Only proceed if we have missing links
            if not missing_links.empty:
                total_songs = len(missing_links)
                st.write(f"Fetching YouTube links for {total_songs} songs...")
                
                # Create progress bar
                progress_bar = st.progress(0)
                
                # Fetch YouTube links for each song with missing link
                for idx, row in missing_links.iterrows():
                    try:
                        # Create a search query combining song and artist
                        search_query = f"{row['Song']} - {row['Artist']}"
                        
                        # Get YouTube link with error handling
                        youtube_link = youtube_api.get_video_link(search_query)
                        
                        # Update the link in the dataframe (only if we got a valid link)
                        if youtube_link:
                            playlist_df.at[idx, 'YouTube_Link'] = youtube_link
                        
                        # Update progress bar
                        progress = min(1.0, (idx + 1) / total_songs)
                        progress_bar.progress(progress)
                        
                    except Exception as e:
                        # Handle YouTube API errors gracefully
                        if "quota" in str(e).lower():
                            st.warning("⚠️ YouTube API quota exceeded. Please try again tomorrow.")
                            break
                        else:
                            query = f"{row['Song']} - {row['Artist']}" if 'row' in locals() else "song"
                            st.warning(f"⚠️ Could not fetch YouTube link for '{query}': {str(e)}")
                
                # Update the main DataFrame with the new YouTube links
                st.session_state.df.update(playlist_df)
                save_updates = True
                
                # Note the file in results for display purposes
                filename = save_processed_csv(st.session_state.df, "youtube", overwrite_existing=True)
                results['youtube_file'] = filename
                st.success("✅ YouTube links fetched and saved")
            else:
                st.info("ℹ️ All songs already have YouTube links")

        # Fetch Spotify playlist if selected
        if "Spotify" in operations and spotify_api:
            with st.spinner("🎧 Fetching Spotify playlist link..."):
                try:
                    # Use the DJ's actual Spotify username from their profile link
                    user_id = "bm8eje5tcjj9eazftizqoikwm"  # The correct user ID from the Spotify URL
                    
                    # Clean the playlist name for Spotify search - just use one cleaning method
                    # Don't clean it twice as that can cause too much difference from actual Spotify names
                    spotify_clean_name = re.sub(r'^\d{3}\s+', '', playlist)
                    
                    st.info(f"Searching for Spotify playlist: '{spotify_clean_name}'")
                    spotify_link = spotify_api.get_playlist_link(user_id, spotify_clean_name)
                except Exception as e:
                    st.error(f"Error with Spotify API: {str(e)}")
                    spotify_link = None
                
                if spotify_link:
                    results['spotify_link'] = spotify_link
                    
                    # Save Spotify link to the DataFrame for all songs in this playlist
                    for idx in playlist_df.index:
                        playlist_df.at[idx, 'Spotify_Link'] = spotify_link
                    
                    # Update the main DataFrame with the new Spotify links
                    st.session_state.df.update(playlist_df)
                    save_updates = True
                    
                    st.success(f"✅ Spotify playlist found and saved to CSV")
                else:
                    st.warning("⚠️ Spotify playlist not found")

        # Save changes to CSV if we made updates
        if save_updates:
            filename = save_processed_csv(st.session_state.df, "updated", overwrite_existing=True)
            results['updated_file'] = filename

        # Generate blog post if selected
        if "Blog" in operations:
            with st.spinner("✍️ Generating blog post..."):
                # Use the Spotify link we just fetched, or look for one in the DataFrame
                spotify_link = results.get('spotify_link')
                
                # If we don't have a link from the API, check if there's one in the DataFrame
                if not spotify_link and 'Spotify_Link' in playlist_df.columns:
                    # Get the first non-empty Spotify link
                    spotify_links = playlist_df[
                        (playlist_df['Spotify_Link'].notna()) & 
                        (playlist_df['Spotify_Link'] != '')
                    ]['Spotify_Link']
                    
                    if not spotify_links.empty:
                        spotify_link = spotify_links.iloc[0]
                
                # Clean the playlist name for the blog post (remove numeric prefix)
                clean_name = clean_playlist_name_for_blog(playlist)
                
                # Generate the blog post
                blog_post = generate_blog_post(
                    playlist_name=clean_name,
                    songs_df=playlist_df,
                    spotify_link=spotify_link,
                    style_options=style_options
                )
                results['blog_post'] = blog_post
                
                # Generate a default title for the blog post
                title_base = clean_name.split('Wedding Cocktail Hour')[0].strip()
                default_title = f"The {title_base} Wedding Cocktail Hour"
                results['blog_title'] = default_title
                
                # Save the blog post to a file
                saved_file = save_blog_post(
                    playlist_name=playlist,
                    blog_content=blog_post,
                    title=default_title
                )
                results['blog_file'] = saved_file
                st.success(f"✅ Blog post generated and saved")

        return True, results

    except Exception as e:
        st.error(f"❌ Error processing playlist: {str(e)}")
        st.error(traceback.format_exc())
        return False, {}

def main():
    # Initialize API clients with error handling
    youtube_api = None
    spotify_api = None
    wordpress_api = None
    
    # YouTube API initialization
    try:
        youtube_key = get_secret("YOUTUBE_API_KEY")
        if youtube_key:
            youtube_api = YouTubeAPI(youtube_key)
            youtube_status, youtube_message = youtube_api.verify_connection()
            if not youtube_status and "quota" in youtube_message.lower():
                st.sidebar.warning("⚠️ YouTube API quota exceeded. Some features may be limited.")
                # Still allow the API client to be used, just with warnings about quota
            elif not youtube_status:
                st.sidebar.error(f"⚠️ YouTube API error: {youtube_message}")
                youtube_api = None
        else:
            st.sidebar.error("⚠️ YouTube API key is missing.")
    except Exception as e:
        st.sidebar.error(f"⚠️ YouTube API error: {str(e)}")
        youtube_api = None
    
    # Spotify API initialization
    try:
        spotify_api = SpotifyAPI(
            get_secret("SPOTIFY_CLIENT_ID"),
            get_secret("SPOTIFY_CLIENT_SECRET")
        )
    except Exception as e:
        st.sidebar.error(f"⚠️ Spotify API error: {str(e)}")
        spotify_api = None
    
    # WordPress API initialization
    try:
        wordpress_api = None  # Initialize to None first
        # Check if WordPress credentials are available
        if all([
            get_secret("WORDPRESS_API_URL"),
            get_secret("WORDPRESS_USERNAME"),
            get_secret("WORDPRESS_PASSWORD")
        ]):
            # Get the credentials from secrets
            api_url = get_secret("WORDPRESS_API_URL")
            username = get_secret("WORDPRESS_USERNAME")
            password = get_secret("WORDPRESS_PASSWORD")
            
            # Fix for common WordPress URL issues
            if api_url and (api_url.endswith('/wp-json') or api_url.endswith('/wp-json/')):
                api_url = api_url.rsplit('/wp-json', 1)[0]
            
            # Initialize WordPress API
            wordpress_api = WordPressAPI(api_url, username, password)
    except Exception as e:
        st.sidebar.error(f"⚠️ WordPress API initialization failed: {str(e)}")
        wordpress_api = None
        
    # Display API status in sidebar
    with st.sidebar:
        st.subheader("API Status")
        
        # YouTube API status
        if youtube_api:
            st.success("✅ YouTube API: Connected")
        else:
            st.error("❌ YouTube API: Not connected")
            
        # Spotify API status
        if spotify_api:
            st.success("✅ Spotify API: Connected")
        else:
            st.error("❌ Spotify API: Not connected")
            
        # WordPress API status
        if wordpress_api:
            if wordpress_api.test_connection():
                st.success("✅ WordPress API: Connected and authenticated")
            else:
                st.warning("⚠️ WordPress API: Connection issues")
                
                # Add WordPress troubleshooting expander
                with st.expander("WordPress Troubleshooting Tools"):
                    st.info("Diagnosing WordPress connection issues...")
                    
                    # Show formatted API URL
                    wp_url = get_secret("WORDPRESS_API_URL", "").strip() if get_secret("WORDPRESS_API_URL") else ""
                    wp_username = get_secret("WORDPRESS_USERNAME", "").strip() if get_secret("WORDPRESS_USERNAME") else ""
                    wp_password = get_secret("WORDPRESS_PASSWORD", "").strip() if get_secret("WORDPRESS_PASSWORD") else ""
                    
                    st.markdown("### WordPress Connection Info")
                    st.info(f"API URL: `{wp_url}`")
                    
                    # Check how API URL is being formatted
                    if not wp_url.startswith('http'):
                        st.warning("⚠️ URL does not start with http or https")
                    
                    # Check if URL already ends with /wp-json
                    if wp_url.endswith('/wp-json'):
                        st.warning("⚠️ URL should not end with /wp-json - this is added automatically")
                    
                    # Check if credentials look correct
                    if len(wp_username) < 2:
                        st.error("❌ Username is too short or empty")
                    else:
                        st.info(f"Username length: {len(wp_username)} characters")
                    
                    if len(wp_password) < 2:
                        st.error("❌ Password is too short or empty")
                    else:
                        st.info(f"Password length: {len(wp_password)} characters")
                    
                    # Application password check
                    if ' ' in wp_password:
                        st.info("📝 Using WordPress Application Password (contains spaces)")
                        segments = wp_password.split()
                        if all(len(s) == 4 for s in segments):
                            st.success("✅ Application password format looks correct")
                        else:
                            segment_lengths = [len(s) for s in segments]
                            st.warning(f"⚠️ Application password segments should be 4 characters each. Current segments: {segment_lengths}")
                    else:
                        st.info("📝 Using standard password (no spaces detected)")
                    
                    # Button to run complete WordPress diagnostics
                    if st.button("🔍 Run Full WordPress Diagnostics"):
                        with st.spinner("Running comprehensive WordPress diagnostics..."):
                            wordpress_api.diagnose_connection()
                            st.info("✅ Diagnostic information logged to the console")
                            st.info("Please check the application logs for detailed results")
            
            # Add WordPress test post button
            if st.button("🧪 Test WordPress Post"):
                with st.spinner("Creating test post..."):
                    try:
                        result = wordpress_api.create_test_post()
                        if result.get('success'):
                            st.success(f"✅ Test post created successfully! ID: {result.get('post_id')}")
                            if result.get('edit_url'):
                                st.markdown(f"[View Post on WordPress]({result.get('edit_url')})")
                        else:
                            st.error(f"❌ Test post failed: {result.get('error')}")
                    except Exception as e:
                        st.error(f"❌ Error creating test post: {str(e)}")
        else:
            st.error("❌ WordPress API: Not connected")
            # Show missing WordPress API details
            st.info("WordPress connection requires WORDPRESS_API_URL, WORDPRESS_USERNAME, and WORDPRESS_PASSWORD environment variables")
    
    # Create tabs for different functions
    tab1, tab2, tab3, tab4 = st.tabs(["Process Playlists", "Edit CSV Data", "Saved Blog Posts", "Revamp Existing Posts"])
    
    # Auto-load the latest CSV if available and no CSV is loaded yet
    if st.session_state.df is None:
        latest_csv = find_latest_csv()
        if latest_csv:
            try:
                st.session_state.df = load_csv(latest_csv)
                st.session_state.last_saved_csv = latest_csv
                st.session_state.auto_loaded = True
            except Exception:
                # Silent exception - we'll just not auto-load if there's an issue
                pass
    
    # Tab 1: Process Playlists
    with tab1:
        st.subheader("Process Wedding DJ Playlists")
        
        # File management section with columns
        col1, col2 = st.columns([3, 2])
        
        with col1:
            # CSV upload section
            uploaded_file = st.file_uploader("Upload New CSV File", type=["csv"])
        
        with col2:
            # Select from existing CSV files
            all_csv_files = find_all_csv_files()
            if all_csv_files:
                selected_csv = st.selectbox(
                    "Or select existing CSV file:",
                    options=["None"] + all_csv_files,
                    format_func=lambda x: f"{x} ({os.path.getmtime(x):.0f})" if x != "None" else "Select a file..."
                )
                
                if selected_csv != "None" and st.button("📂 Load Selected CSV"):
                    try:
                        st.session_state.df = load_csv(selected_csv)
                        st.session_state.last_saved_csv = selected_csv
                        st.success(f"✅ Loaded {selected_csv} successfully!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Error loading selected CSV: {str(e)}")
        
        # Process the uploaded file
        if uploaded_file is not None:
            try:
                # Option to merge with existing data or replace
                if st.session_state.df is not None:
                    merge_option = st.radio(
                        "How would you like to handle this new data?", 
                        ["Replace existing data", "Merge with existing data", "Cancel upload"]
                    )
                    
                    if merge_option == "Cancel upload":
                        st.info("Upload canceled. Using existing data.")
                    elif merge_option == "Replace existing data":
                        st.session_state.df = load_csv(uploaded_file)
                        st.success("✅ CSV file loaded successfully (replaced existing data)!")
                    else:  # Merge
                        new_df = load_csv(uploaded_file)
                        # Merge dataframes, keeping records from both
                        st.session_state.df = pd.concat([st.session_state.df, new_df], ignore_index=True)
                        # Remove any duplicate songs (same playlist, song and artist)
                        st.session_state.df = st.session_state.df.drop_duplicates(
                            subset=['Playlist', 'Song', 'Artist'], 
                            keep='first'
                        )
                        st.success("✅ CSV file merged with existing data successfully!")
                else:
                    # Just load the file if no data exists
                    st.session_state.df = load_csv(uploaded_file)
                    st.success("✅ CSV file loaded successfully!")
                
                # Show a preview of the data
                if st.session_state.df is not None and not st.session_state.df.empty:
                    st.write(f"Found {len(st.session_state.df)} songs across {st.session_state.df['Playlist'].nunique()} playlists")
                    
                    # Show a small sample
                    st.write("Preview of loaded data:")
                    preview_cols = ['Playlist', 'Song', 'Artist', 'YouTube_Link', 'Spotify_Link']
                    st.dataframe(st.session_state.df[preview_cols].head(5))
                    
                    # Save the merged/uploaded data with timestamp
                    if st.session_state.df is not None:
                        filename = save_processed_csv(st.session_state.df, "uploaded", overwrite_existing=True)
                        st.session_state.last_saved_csv = filename
                        st.info(f"💾 Data saved to {filename}")
                    
            except Exception as e:
                st.error(f"❌ Error loading CSV file: {str(e)}")
                st.error(traceback.format_exc())
        
        # Show what we're working with
        if st.session_state.auto_loaded and st.session_state.df is not None:
            st.info(f"ℹ️ Auto-loaded data from {st.session_state.last_saved_csv}")
            st.session_state.auto_loaded = False
        
        # If we have data, display playlist processing options
        if st.session_state.df is not None:
            playlists = st.session_state.df['Playlist'].unique()
            
            # Keep the numeric prefixes in the display names
            
            # Playlist selection and operations
            selected_playlists = st.multiselect(
                "Select playlists to process:", 
                options=playlists
            )
            
            # Operations selection
            st.write("Select operations to perform:")
            col1, col2, col3 = st.columns(3)
            with col1:
                fetch_youtube = st.checkbox("Fetch YouTube Links", value=True)
            with col2:
                fetch_spotify = st.checkbox("Fetch Spotify Playlist", value=True)
            with col3:
                generate_blog = st.checkbox("Generate Blog Post", value=True)
            
            # Blog customization options (shown when Generate Blog Post is selected)
            blog_style_options = {}
            if generate_blog:
                with st.expander("Blog Customization Options", expanded=False):
                    st.write("Customize your blog post style:")
                    
                    # Model selection with descriptions - available in both modes
                    st.markdown("### OpenAI Model Selection")
                    st.info("""
                    **Model Options:**
                    - **GPT-4.1**: Most capable model with highest quality output
                    - **GPT-4o-mini**: Very good performance with lower costs
                    - **GPT-4.1-mini**: Good balance of quality and cost
                    - **GPT-4.1-nano**: Fastest with lowest costs, good for testing
                    """)
                    model_options = [
                        "gpt-4.1", 
                        "gpt-4o-mini",
                        "gpt-4.1-mini", 
                        "gpt-4.1-nano"
                    ]
                    model = st.selectbox(
                        "Select Model",
                        options=model_options,
                        index=0,
                        help="Select which OpenAI model to use for blog generation."
                    )
                    blog_style_options['model'] = model
                    
                    # Temperature control for AI creativity
                    temperature = st.slider(
                        "Temperature", 
                        min_value=0.0, 
                        max_value=1.0, 
                        value=0.7, 
                        step=0.1,
                        help="Controls randomness in generation. Lower values are more focused and deterministic, higher values are more creative."
                    )
                    blog_style_options['temperature'] = temperature
                    
                    # Style customization mode toggle
                    st.markdown("### Style Customization")
                    custom_mode = st.radio(
                        "Customization Mode",
                        options=["Use Presets", "Free-form Input"],
                        horizontal=True
                    )
                    
                    if custom_mode == "Use Presets":
                        # Original dropdown-based options
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            tone = st.selectbox(
                                "Blog Tone",
                                options=["conversational and warm", "professional and elegant", 
                                         "fun and upbeat", "romantic and emotional"],
                                index=0
                            )
                            blog_style_options['tone'] = tone
                            
                            mood = st.selectbox(
                                "Overall Mood",
                                options=["romantic and celebratory", "elegant and sophisticated", 
                                         "fun and energetic", "nostalgic and sentimental", 
                                         "modern and trendy"],
                                index=0
                            )
                            blog_style_options['mood'] = mood
                        
                        with col2:
                            audience = st.selectbox(
                                "Target Audience",
                                options=["engaged couples", "modern couples", "traditional couples", 
                                         "brides", "wedding planners"],
                                index=0
                            )
                            blog_style_options['audience'] = audience
                            
                            section_count = st.select_slider(
                                "Number of Sections",
                                options=[3, 4, 5, 6, 7],
                                value=4
                            )
                            blog_style_options['section_count'] = section_count
                        
                        title_style = st.selectbox(
                            "Section Title Style",
                            options=["descriptive and catchy", "short and elegant", 
                                     "fun and playful", "romantic", "themed around moments"],
                            index=0
                        )
                        blog_style_options['title_style'] = title_style
                    else:
                        # Free-form text input based options
                        st.markdown("#### Enter your own custom style preferences:")
                        
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            tone = st.text_input(
                                "Blog Tone",
                                value="conversational and warm",
                                help="Example: playful and witty, sophisticated and elegant, etc."
                            )
                            blog_style_options['tone'] = tone
                            
                            mood = st.text_input(
                                "Overall Mood",
                                value="romantic and celebratory",
                                help="Example: laid-back beachy vibe, stylish urban feel, etc."
                            )
                            blog_style_options['mood'] = mood
                        
                        with col2:
                            audience = st.text_input(
                                "Target Audience",
                                value="engaged couples",
                                help="Example: music-loving couples, vintage enthusiasts, etc."
                            )
                            blog_style_options['audience'] = audience
                            
                            section_count = st.number_input(
                                "Number of Sections",
                                min_value=3,
                                max_value=8,
                                value=4
                            )
                            blog_style_options['section_count'] = section_count
                        
                        title_style = st.text_input(
                            "Section Title Style",
                            value="descriptive and catchy",
                            help="Example: questions, movie references, song lyrics, etc."
                        )
                        blog_style_options['title_style'] = title_style
                    
                    # Additional custom fields for more personalization - available in both modes
                    st.markdown("### Additional Content Guidance (Optional)")
                    
                    # Custom guidance fields
                    custom_guidance = st.text_area(
                        "Custom Writing Guidance",
                        value="",
                        height=100,
                        help="Additional instructions for how the blog should be written (e.g., mention specific themes, include quotes, focus on particular aspects of songs)"
                    )
                    if custom_guidance.strip():
                        blog_style_options['custom_guidance'] = custom_guidance
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        custom_intro = st.text_area(
                            "Custom Introduction Theme",
                            value="",
                            height=75,
                            help="Specific themes or ideas to include in the introduction"
                        )
                        if custom_intro.strip():
                            blog_style_options['custom_intro'] = custom_intro
                    
                    with col2:
                        custom_conclusion = st.text_area(
                            "Custom Conclusion Theme",
                            value="",
                            height=75,
                            help="Specific themes or ideas to include in the conclusion"
                        )
                        if custom_conclusion.strip():
                            blog_style_options['custom_conclusion'] = custom_conclusion
                    
                    st.info("These options will be used to customize the AI-generated blog post.")
            
            # Process button
            if selected_playlists:
                if st.button("🚀 Process Selected Playlists"):
                    operations = []
                    if fetch_youtube: operations.append("YouTube")
                    if fetch_spotify: operations.append("Spotify")
                    if generate_blog: operations.append("Blog")
                    
                    if not operations:
                        st.warning("⚠️ Please select at least one operation to perform.")
                    else:
                        # Process each playlist
                        for playlist in selected_playlists:
                            with st.expander(f"Processing: {playlist}", expanded=True):
                                success, results = process_playlist(playlist, youtube_api, spotify_api, operations, blog_style_options)
                                
                                if success:
                                    # Display results
                                    if 'youtube_file' in results:
                                        st.success(f"✅ YouTube links updated and saved to {results['youtube_file']}")
                                        
                                    if 'spotify_link' in results:
                                        st.markdown(f"""
                                        <p>Spotify Playlist Link: <a href="{results['spotify_link']}" target="_blank">{results['spotify_link']}</a></p>
                                        """, unsafe_allow_html=True)
                                        
                                    if 'blog_post' in results:
                                        st.write("✨ Generated Blog Post:")
                                        
                                        # If blog post was saved to a file, show a success message
                                        if 'blog_file' in results:
                                            st.success(f"✅ Blog post saved to {results['blog_file']} for future reference")
                                        
                                        # Display the formatted blog content with HTML rendering
                                        blog_content = results['blog_post']
                                        
                                        # First show a preview with HTML rendered
                                        st.subheader("Preview (as it will appear on WordPress)")
                                        st.markdown(blog_content, unsafe_allow_html=True)
                                        
                                        # Then show the raw HTML content in a text area for editing
                                        st.subheader("HTML Source (for editing)")
                                        st.text_area("", blog_content, height=300)
                                        
                                        # WordPress posting section
                                        blog_title = results.get('blog_title', '')
                                        title = st.text_input("Blog Post Title", value=blog_title)
                                        
                                        # WordPress posting section - only show if API is initialized
                                        if wordpress_api is None:
                                            st.error("WordPress API not configured - cannot post to WordPress")
                                        else:
                                            # Show WordPress posting button with a unique key
                                            button_key = f"post_wordpress_{playlist}_processed"
                                            if st.button("🚀 Post to WordPress", key=button_key):
                                                with st.spinner("📝 Creating draft post in WordPress..."):
                                                    try:
                                                        # Show a preview of what will be posted
                                                        st.subheader("Content being posted to WordPress:")
                                                        st.markdown(blog_content, unsafe_allow_html=True)
                                                        
                                                        # Post to WordPress as draft
                                                        post_result = wordpress_api.create_post(
                                                            title=title,
                                                            content=blog_content,
                                                            status="draft"
                                                        )
                                                        
                                                        if post_result.get('success'):
                                                            post_id = post_result.get('post_id')
                                                            post_url = post_result.get('post_url')
                                                            edit_url = post_result.get('edit_url')
                                                            
                                                            st.success(f"✅ Draft post created! ID: {post_id}")
                                                            st.write(f"View/Edit: {edit_url}")
                                                        else:
                                                            error_msg = post_result.get('error', 'Unknown error')
                                                            st.error(f"❌ Failed to create post: {error_msg}")
                                                    except Exception as e:
                                                        st.error(f"❌ Error posting to WordPress: {str(e)}")
                        
    # Tab 2: Edit CSV Data
    with tab2:
        st.subheader("Edit CSV Data")
        
        if st.session_state.df is not None:
            # Layout for edit and management options
            edit_tab1, edit_tab2, edit_tab3 = st.tabs(["Edit Songs", "Create Playlist", "Delete/Rename"])
            
            with edit_tab1:
                # Get unique playlists from the dataframe
                playlists = st.session_state.df['Playlist'].unique()
                
                # Format the playlist names for display (remove numeric prefixes)
                display_names = {p: re.sub(r'^\d{3}\s+', '', p) for p in playlists}
                
                # Dropdown to select a playlist to edit
                selected_edit_playlist = st.selectbox(
                    "Select a playlist to edit:",
                    options=playlists,
                    format_func=lambda x: display_names[x],
                    key="edit_playlist_selector"
                )
                
                if selected_edit_playlist:
                    # Filter dataframe for selected playlist
                    edit_df = st.session_state.df[st.session_state.df['Playlist'] == selected_edit_playlist].copy()
                    
                    # Determine columns to display
                    edit_columns = ['Song', 'Artist', 'YouTube_Link', 'Spotify_Link']
                    
                    # Add editing options with columns
                    col1, col2, col3 = st.columns([1, 1, 1])
                    
                    with col1:
                        # Button to add new songs
                        if st.button("➕ Add New Song", key="add_song_btn"):
                            # Create a new row with the current playlist
                            new_row = {
                                'Playlist': selected_edit_playlist,
                                'Song': 'New Song',
                                'Artist': 'Artist Name',
                                'Song_Artist': 'New Song-Artist Name',
                                'YouTube_Link': '',
                                'Spotify_Link': edit_df['Spotify_Link'].iloc[0] if 'Spotify_Link' in edit_df.columns and not edit_df['Spotify_Link'].iloc[0].isna() else ''
                            }
                            
                            # Add the new row to the dataframe
                            st.session_state.df = pd.concat([
                                st.session_state.df, 
                                pd.DataFrame([new_row])
                            ], ignore_index=True)
                            
                            # Save the updated dataframe
                            filename = save_processed_csv(st.session_state.df, "added_song", overwrite_existing=True)
                            st.success(f"✅ Added new song to playlist and saved to {filename}!")
                            st.rerun()
                    
                    with col2:
                        # Button to edit Spotify link for the entire playlist
                        if st.button("🎵 Edit Spotify Link", key="edit_spotify_btn"):
                            # Get current Spotify link if any
                            current_spotify = ""
                            if 'Spotify_Link' in edit_df.columns and len(edit_df) > 0:
                                spotify_links = edit_df['Spotify_Link'].unique()
                                if len(spotify_links) > 0 and not pd.isna(spotify_links[0]):
                                    current_spotify = spotify_links[0]
                            
                            # Show input for Spotify link
                            spotify_link = st.text_input(
                                "Spotify Playlist Link", 
                                value=current_spotify,
                                key="spotify_playlist_link"
                            )
                            
                            # Save button for Spotify link
                            if st.button("💾 Save Spotify Link", key="save_spotify_btn"):
                                if spotify_link.strip():
                                    # Update all songs in this playlist
                                    for idx in edit_df.index:
                                        st.session_state.df.at[idx, 'Spotify_Link'] = spotify_link
                                        
                                    # Save the updated dataframe
                                    filename = save_processed_csv(st.session_state.df, "updated_spotify", overwrite_existing=True)
                                    st.success(f"✅ Updated Spotify link for playlist '{selected_edit_playlist}' and saved to {filename}!")
                                    st.rerun()
                    
                    with col3:
                        # Export just this playlist to a CSV
                        if st.button("📤 Export Playlist", key="export_playlist_btn"):
                            # Create a CSV just for this playlist
                            import io
                            from datetime import datetime
                            
                            playlist_name_clean = re.sub(r'[^\w\s]', '', selected_edit_playlist).strip().replace(' ', '_').lower()
                            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                            export_filename = f"{playlist_name_clean}_{timestamp}.csv"
                            
                            # Save just this playlist
                            edit_df.to_csv(export_filename, index=False)
                            st.success(f"✅ Exported playlist to {export_filename}!")
                    
                    # Display the dataframe with editing capabilities
                    st.markdown("### Songs in Playlist")
                    
                    # Create a copy of the edit dataframe for editing
                    edited_df = st.data_editor(
                        edit_df[edit_columns],
                        use_container_width=True,
                        num_rows="dynamic",
                        key="song_editor"
                    )
                    
                    # Button to save edits
                    if st.button("💾 Save Changes to Songs", key="save_edits_btn"):
                        # Find the edited rows that have changes
                        if not edited_df.equals(edit_df[edit_columns]):
                            # Update the original dataframe with edited values
                            for idx, row in edited_df.iterrows():
                                # Update each column that's editable
                                for col in edit_columns:
                                    if idx < len(edit_df):
                                        orig_idx = edit_df.index[idx]
                                        st.session_state.df.at[orig_idx, col] = row[col]
                                        
                                        # Also update Song_Artist column if Song or Artist changed
                                        if col in ['Song', 'Artist']:
                                            song = st.session_state.df.at[orig_idx, 'Song']
                                            artist = st.session_state.df.at[orig_idx, 'Artist']
                                            st.session_state.df.at[orig_idx, 'Song_Artist'] = f"{song}-{artist}"
                            
                            # Save the updated dataframe
                            filename = save_processed_csv(st.session_state.df, "edited_songs", overwrite_existing=True)
                            st.success(f"✅ Saved changes to songs in playlist '{selected_edit_playlist}' to {filename}!")
                            st.rerun()
                        else:
                            st.info("No changes detected to save.")
            
            with edit_tab2:
                # Create new playlist section
                st.subheader("Create New Playlist")
                
                # Input fields for new playlist
                new_playlist_name = st.text_input(
                    "New Playlist Name",
                    placeholder="e.g., The Elegant Wedding Cocktail Hour",
                    key="new_playlist_name"
                )
                
                # Initial songs for the playlist
                with st.expander("Add Initial Songs"):
                    initial_songs = []
                    
                    # Add up to 5 initial songs
                    for i in range(1, 6):
                        col1, col2 = st.columns(2)
                        with col1:
                            song = st.text_input(f"Song {i}", key=f"init_song_{i}")
                        with col2:
                            artist = st.text_input(f"Artist {i}", key=f"init_artist_{i}")
                        
                        if song and artist:
                            initial_songs.append((song, artist))
                
                # Create button
                if st.button("✨ Create New Playlist", key="create_playlist_btn"):
                    if new_playlist_name:
                        # Make sure it has the right format
                        if "Wedding Cocktail Hour" not in new_playlist_name:
                            new_playlist_name = f"{new_playlist_name} Wedding Cocktail Hour"
                        
                        # Add numeric prefix (find the highest existing number and add 1)
                        max_number = 0
                        for playlist in playlists:
                            try:
                                # Extract the number from the playlist name
                                number = int(playlist.split(' ')[0])
                                max_number = max(max_number, number)
                            except:
                                # If we can't extract a number, just continue
                                pass
                        
                        # Format the playlist name with the next number
                        formatted_playlist_name = f"{max_number + 1:03d} {new_playlist_name}"
                        
                        # Create list of rows for new playlist
                        new_rows = []
                        
                        # Use provided initial songs or add a default one
                        if initial_songs:
                            for song, artist in initial_songs:
                                new_rows.append({
                                    'Playlist': formatted_playlist_name,
                                    'Song': song,
                                    'Artist': artist,
                                    'Song_Artist': f"{song}-{artist}",
                                    'YouTube_Link': '',
                                    'Spotify_Link': ''
                                })
                        else:
                            # Add one empty row if no songs provided
                            new_rows.append({
                                'Playlist': formatted_playlist_name,
                                'Song': 'First Song',
                                'Artist': 'Artist Name',
                                'Song_Artist': 'First Song-Artist Name',
                                'YouTube_Link': '',
                                'Spotify_Link': ''
                            })
                        
                        # Add to dataframe
                        st.session_state.df = pd.concat([
                            st.session_state.df, 
                            pd.DataFrame(new_rows)
                        ], ignore_index=True)
                        
                        # Save updated dataframe
                        filename = save_processed_csv(st.session_state.df, "new_playlist", overwrite_existing=True)
                        st.success(f"✅ Created new playlist '{new_playlist_name}' with {len(new_rows)} songs and saved to {filename}!")
                        st.rerun()
                    else:
                        st.warning("⚠️ Please enter a playlist name")
            
            with edit_tab3:
                st.subheader("Delete or Rename Playlist")
                
                # Get unique playlists from the dataframe again
                playlists = st.session_state.df['Playlist'].unique()
                
                # Dropdown to select a playlist to manage
                selected_manage_playlist = st.selectbox(
                    "Select a playlist to manage:",
                    options=playlists,
                    format_func=lambda x: re.sub(r'^\d{3}\s+', '', x),
                    key="manage_playlist_selector"
                )
                
                if selected_manage_playlist:
                    # Management options with columns
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        # Delete playlist
                        if st.button("🗑️ Delete Playlist", key="delete_playlist_btn"):
                            # Confirm deletion
                            if st.checkbox("⚠️ Are you sure? This cannot be undone!", key="confirm_delete"):
                                # Filter out the selected playlist
                                st.session_state.df = st.session_state.df[
                                    st.session_state.df['Playlist'] != selected_manage_playlist
                                ]
                                
                                # Save the updated dataframe
                                filename = save_processed_csv(st.session_state.df, "deleted_playlist", overwrite_existing=True)
                                st.success(f"✅ Deleted playlist '{selected_manage_playlist}' and saved to {filename}!")
                                st.rerun()
                    
                    with col2:
                        # Rename playlist
                        if st.button("✏️ Rename Playlist", key="rename_playlist_btn"):
                            # Input for new name
                            new_name = st.text_input(
                                "New Playlist Name",
                                value=re.sub(r'^\d{3}\s+', '', selected_manage_playlist),
                                key="rename_playlist_input"
                            )
                            
                            # Button to save new name
                            if st.button("💾 Save New Name", key="save_rename_btn"):
                                if new_name:
                                    # Extract the numeric prefix from the original name
                                    prefix_match = re.match(r'^(\d{3})\s+', selected_manage_playlist)
                                    prefix = prefix_match.group(1) if prefix_match else "000"
                                    
                                    # Make sure it has the right format
                                    if "Wedding Cocktail Hour" not in new_name:
                                        new_name = f"{new_name} Wedding Cocktail Hour"
                                    
                                    # Format the new name with the same prefix
                                    formatted_new_name = f"{prefix} {new_name}"
                                    
                                    # Update the playlist name in the dataframe
                                    st.session_state.df.loc[
                                        st.session_state.df['Playlist'] == selected_manage_playlist,
                                        'Playlist'
                                    ] = formatted_new_name
                                    
                                    # Save the updated dataframe
                                    filename = save_processed_csv(st.session_state.df, "renamed_playlist", overwrite_existing=True)
                                    st.success(f"✅ Renamed playlist to '{new_name}' and saved to {filename}!")
                                    st.rerun()
                                else:
                                    st.warning("⚠️ Please enter a new name for the playlist")
        else:
            st.warning("⚠️ Please upload a CSV file first or select a previously saved file.")
    
    # Tab 3: Saved Blog Posts
    with tab3:
        st.subheader("Saved Blog Posts")
        
        # Find all saved blog posts
        blog_files = find_saved_blog_posts()
        
        if blog_files:
            # Split into columns for layout (blog selection and management)
            col1, col2 = st.columns([7, 3])
            
            with col1:
                # Create a dropdown to select a blog post
                selected_blog = st.selectbox("Select a saved blog post:", blog_files)
            
            with col2:
                st.write("")
                st.write("")  # Add some spacing
                # Add a delete button
                if st.button("🗑️ Delete Selected Blog", key="delete_blog_btn"):
                    if selected_blog:
                        if delete_saved_blog_post(selected_blog):
                            st.success(f"✅ Deleted blog post: {selected_blog}")
                            # Update blog_files
                            blog_files = find_saved_blog_posts()
                            if blog_files:
                                # Auto-select another blog
                                selected_blog = blog_files[0]
                                st.rerun()
                            else:
                                st.info("No more blog posts available.")
                                st.stop()
                        else:
                            st.error(f"❌ Failed to delete blog post: {selected_blog}")
            
            if selected_blog:
                # Load the selected blog post
                title, content = load_saved_blog_post(selected_blog)
                
                # Allow editing the title and content
                edited_title = st.text_input("Blog Title", value=title, key="blog_title_edit")
                
                # Display the blog post in a pretty format with HTML rendered
                st.subheader("Blog Preview")
                st.markdown(content, unsafe_allow_html=True)
                
                # Edit in a text area
                st.subheader("Edit Content")
                edited_content = st.text_area("Blog Content", content, height=400, key="blog_content_edit")
                
                # Add a save button if edits were made
                if edited_title != title or edited_content != content:
                    if st.button("💾 Save Changes", key="save_blog_changes"):
                        try:
                            # Delete the old file
                            delete_saved_blog_post(selected_blog)
                            
                            # Create a new file with updated content
                            new_filename = save_blog_post(
                                playlist_name=edited_title.replace(" ", "_").lower(),
                                blog_content=edited_content,
                                title=edited_title
                            )
                            
                            st.success(f"✅ Changes saved to {new_filename}")
                            st.rerun()
                        except Exception as e:
                            st.error(f"❌ Error saving changes: {str(e)}")
                
                # WordPress posting section with columns for spacing
                col1, col2, col3 = st.columns([1, 1, 1])
                
                if wordpress_api:
                    with col2:
                        # Add a unique key for this button to avoid duplicate element IDs
                        button_key = f"post_wordpress_{selected_blog}"
                        if st.button("🚀 Post to WordPress", key=button_key):
                            with st.spinner("📝 Creating draft post in WordPress..."):
                                try:
                                    # Use edited title and content if available
                                    post_title = edited_title
                                    post_content = edited_content
                                    # Display a preview of what will be posted
                                    st.markdown("**Preview of content being posted to WordPress:**", unsafe_allow_html=True)
                                    st.markdown(post_content, unsafe_allow_html=True)
                                    
                                    # Post to WordPress as draft
                                    result = wordpress_api.create_post(
                                        title=post_title,
                                        content=post_content,
                                        status="draft"
                                    )
                                    
                                    if result.get('success'):
                                        post_id = result.get('post_id')
                                        post_url = result.get('post_url')
                                        edit_url = result.get('edit_url')
                                        
                                        st.success(f"✅ Draft post created! ID: {post_id}")
                                        st.markdown(f"[View/Edit on WordPress]({edit_url})")
                                    else:
                                        error_msg = result.get('error', 'Unknown error')
                                        st.error(f"❌ Failed to create post: {error_msg}")
                                except Exception as e:
                                    st.error(f"❌ Error posting to WordPress: {str(e)}")
        else:
            st.info("No saved blog posts found. Generate some blog posts first!")
            
    # Tab 4: Revamp Existing WordPress Posts
    with tab4:
        st.subheader("Revamp Existing WordPress Posts")
        
        # Only show if WordPress API is properly initialized
        if wordpress_api is None:
            st.error("WordPress API not configured. Please set up the WordPress API credentials in your environment variables.")
            st.info("Required: WORDPRESS_API_URL, WORDPRESS_USERNAME, WORDPRESS_PASSWORD")
        else:
            # Search options
            st.write("### Find WordPress Posts to Revamp")
            search_col1, search_col2 = st.columns(2)
            
            with search_col1:
                search_term = st.text_input("Search by keywords", 
                    placeholder="Enter keywords to search for posts...")
                
            with search_col2:
                # Get categories for filtering
                try:
                    categories = wordpress_api.get_categories()
                    category_options = {cat['name']: cat['id'] for cat in categories}
                    # Add "All Categories" option
                    category_options = {"All Categories": None, **category_options}
                    
                    selected_category = st.selectbox(
                        "Filter by category",
                        options=list(category_options.keys())
                    )
                    category_id = category_options.get(selected_category)
                except Exception as e:
                    st.error(f"Error loading categories: {str(e)}")
                    categories = []
                    selected_category = None
                    category_id = None
            
            # Get posts button
            posts_per_page = st.slider("Posts per page", min_value=5, max_value=50, value=10, step=5)
            if st.button("🔍 Search Posts"):
                with st.spinner("Fetching posts from WordPress..."):
                    try:
                        # Use the search term and category if provided
                        result = wordpress_api.get_posts(
                            search_term=search_term if search_term else None,
                            category=category_id,
                            per_page=posts_per_page
                        )
                        
                        if result and 'posts' in result and result['posts']:
                            posts = result['posts']
                            st.success(f"Found {result['total']} posts (showing page {result['current_page']} of {result['pages']})")
                            
                            # Store posts in session state
                            st.session_state.wordpress_posts = posts
                            
                            # Display posts in a table
                            post_data = []
                            for post in posts:
                                # Truncate title and excerpt for display
                                title = post['title'][:50] + "..." if len(post['title']) > 50 else post['title']
                                date = post['date'].split('T')[0] if 'T' in post['date'] else post['date']
                                post_data.append({
                                    "ID": post['id'],
                                    "Title": title,
                                    "Date": date,
                                    "Link": post['link']
                                })
                            
                            # Convert to DataFrame for display
                            post_df = pd.DataFrame(post_data)
                            st.dataframe(post_df, hide_index=True, use_container_width=True)
                        else:
                            st.warning("No posts found matching your criteria.")
                            st.session_state.wordpress_posts = []
                    except Exception as e:
                        st.error(f"Error fetching posts: {str(e)}")
                        st.session_state.wordpress_posts = []
            
            # Post selection and revamping
            st.write("### Revamp Selected Post")
            
            if 'wordpress_posts' in st.session_state and st.session_state.wordpress_posts:
                # Create a dictionary of post titles mapped to IDs for selection
                post_options = {f"{post['id']}: {post['title'][:50]}...": post['id'] 
                               for post in st.session_state.wordpress_posts}
                
                # Two-step process with a "Load Post" button
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    selected_post_title = st.selectbox(
                        "Select a post to revamp",
                        options=list(post_options.keys()),
                        index=0
                    )
                
                with col2:
                    load_post_button = st.button("📄 Load Post", key="load_post")
                
                # Only proceed if load button is clicked
                if load_post_button and selected_post_title:
                    selected_post_id = post_options[selected_post_title]
                    
                    # Fetch the post content and store it
                    with st.spinner("Loading post content..."):
                        try:
                            post = wordpress_api.get_post(selected_post_id)
                            if post:
                                # Store in session state
                                st.session_state['current_post'] = post
                                
                                # Show post preview
                                st.write("### Original Post Content")
                                with st.expander("View Original HTML Content", expanded=False):
                                    st.code(post['content'], language="html")
                                
                                # Show rendered preview
                                st.write("### Original Post Preview")
                                st.markdown(post['content'], unsafe_allow_html=True)
                                
                                # Blog style customization options - matching the original blog generator options
                                st.write("### Revamp Style Options")
                                
                                # Model selection
                                model = st.selectbox(
                                    "AI Model",
                                    ["gpt-4o", "gpt-4.1", "gpt-4.1-mini", "gpt-4.1-nano"],
                                    index=0,
                                    help="Select which OpenAI model to use for content generation"
                                )
                                
                                temperature = st.slider(
                                    "Creativity Level", 
                                    min_value=0.0, 
                                    max_value=1.0, 
                                    value=0.7, 
                                    step=0.1,
                                    help="Higher values make output more creative, lower values make it more predictable"
                                )
                                
                                # Initialize form for revamp options
                                with st.form(key="revamp_form"):
                                    # Basic style options with both dropdowns and custom inputs
                                    st.subheader("Basic Style")
                                    
                                    # Tone options with custom option
                                    tone_options = ["Professional", "Conversational", "Romantic", "Upbeat", "Elegant", "Playful", "Custom"]
                                    tone = st.selectbox(
                                        "Writing Tone",
                                        tone_options,
                                        index=0
                                    )
                                    
                                    if tone == "Custom":
                                        custom_tone = st.text_input("Custom tone", 
                                            placeholder="e.g., 'Inspirational with a touch of humor'")
                                        tone = custom_tone if custom_tone else "Professional"
                                    
                                    # Section count with dropdown and custom
                                    section_count_options = ["Default (3-4)", "Minimal (2-3)", "Comprehensive (4-5)", "Detailed (5-6)", "Custom"]
                                    section_count_selection = st.selectbox(
                                        "Content Sections",
                                        section_count_options,
                                        index=0
                                    )
                                    
                                    if section_count_selection == "Custom":
                                        section_count = st.number_input("Number of content sections", min_value=2, max_value=6, value=4)
                                    else:
                                        # Parse the selection to get the actual number
                                        if section_count_selection == "Default (3-4)":
                                            section_count = 4
                                        elif section_count_selection == "Minimal (2-3)":
                                            section_count = 3
                                        elif section_count_selection == "Comprehensive (4-5)":
                                            section_count = 5
                                        elif section_count_selection == "Detailed (5-6)":
                                            section_count = 6
                                    
                                    col1, col2 = st.columns(2)
                                    
                                    with col1:
                                        # Mood options with custom
                                        mood_options = ["Elegant", "Fun", "Emotional", "Energetic", "Romantic", "Sophisticated", "Custom"]
                                        mood = st.selectbox(
                                            "Overall Mood",
                                            mood_options,
                                            index=0
                                        )
                                        
                                        if mood == "Custom":
                                            custom_mood = st.text_input("Custom mood", 
                                                placeholder="e.g., 'Intimate and heartfelt'")
                                            mood = custom_mood if custom_mood else "Elegant"
                                        
                                        # Introduction theme
                                        intro_theme_options = ["Standard Welcome", "Personal Story", "Setting the Scene", "Custom"]
                                        intro_theme = st.selectbox(
                                            "Introduction Theme",
                                            intro_theme_options,
                                            index=0
                                        )
                                        
                                        if intro_theme == "Custom":
                                            custom_intro = st.text_input("Custom introduction theme", 
                                                placeholder="e.g., 'Begin with a quote about music and love'")
                                            intro_theme = custom_intro if custom_intro else "Standard Welcome"
                                    
                                    with col2:
                                        # Audience options with custom
                                        audience_options = ["Modern Couples", "Traditional Couples", "Brides", "Grooms", "Wedding Planners", "Custom"]
                                        audience = st.selectbox(
                                            "Target Audience",
                                            audience_options,
                                            index=0
                                        )
                                        
                                        if audience == "Custom":
                                            custom_audience = st.text_input("Custom audience", 
                                                placeholder="e.g., 'Music-loving couples'")
                                            audience = custom_audience if custom_audience else "Modern Couples"
                                        
                                        # Conclusion theme
                                        conclusion_options = ["Standard Closing", "Call to Action", "Personal Touch", "Custom"]
                                        conclusion_theme = st.selectbox(
                                            "Conclusion Theme",
                                            conclusion_options,
                                            index=0
                                        )
                                        
                                        if conclusion_theme == "Custom":
                                            custom_conclusion = st.text_input("Custom conclusion theme", 
                                                placeholder="e.g., 'End with planning tips'")
                                            conclusion_theme = custom_conclusion if custom_conclusion else "Standard Closing"
                                    
                                    # Advanced options
                                    with st.expander("Advanced Customization"):
                                        title_style_options = ["Descriptive", "Short", "Playful", "Elegant", "Question", "Custom"]
                                        title_style = st.selectbox(
                                            "Section Title Style",
                                            title_style_options,
                                            index=0
                                        )
                                        
                                        if title_style == "Custom":
                                            custom_title = st.text_input("Custom title style", 
                                                placeholder="e.g., 'Alliterative and punchy'")
                                            title_style = custom_title if custom_title else "Descriptive"
                                        
                                        custom_guidance = st.text_area(
                                            "Custom Writing Guidance", 
                                            placeholder="Add any specific instructions or guidance for the blog post generation...",
                                            height=100
                                        )
                                    
                                    # Submit button for the form
                                    revamp_button = st.form_submit_button("✨ Revamp This Post")
                                
                                # Process the revamp request if form was submitted
                                if revamp_button:
                                    # Initialize variables with defaults to avoid undefined errors
                                    section_count = 4
                                    custom_guidance = ""
                                    intro_theme = "Standard Welcome"
                                    conclusion_theme = "Standard Closing"
                                    title_style = "Descriptive"
                                    
                                    # Override defaults with form values if they exist
                                    if section_count_selection == "Default (3-4)":
                                        section_count = 4
                                    elif section_count_selection == "Minimal (2-3)":
                                        section_count = 3
                                    elif section_count_selection == "Comprehensive (4-5)":
                                        section_count = 5
                                    elif section_count_selection == "Detailed (5-6)":
                                        section_count = 6
                                
                                    # Create comprehensive style options dictionary
                                    style_options = {
                                        "tone": tone,
                                        "mood": mood,
                                        "audience": audience,
                                        "section_count": section_count,
                                        "intro_theme": intro_theme,
                                        "conclusion_theme": conclusion_theme,
                                        "title_style": title_style,
                                        "custom_guidance": custom_guidance,
                                        "model": model,
                                        "temperature": temperature
                                    }
                                    
                                    with st.spinner("Revamping post content... This may take a minute..."):
                                        try:
                                            # Perform the revamp
                                            revamped_content = revamp_existing_blog(
                                                post_content=post['content'],
                                                post_title=post['title'],
                                                youtube_api=youtube_api,
                                                style_options=style_options
                                            )
                                            
                                            # Store in session state to persist between reruns
                                            st.session_state.revamped_content = revamped_content
                                            st.session_state.revamp_post_id = post['id']
                                            st.session_state.revamp_post_title = post['title']
                                            st.session_state.revamp_post_categories = post.get('categories', [])
                                            
                                            # Success message
                                            st.success("✅ Post successfully revamped! See the preview below.")
                                        except Exception as e:
                                            st.error(f"Error revamping post: {str(e)}")
                                            st.error("Please try again or select a different post.")
                            else:
                                st.error("Could not fetch post content.")
                        except Exception as e:
                            st.error(f"Error fetching post: {str(e)}")
                    
                # Display revamped content at the bottom of the page (outside other containers) to ensure it stays visible
                with st.container():
                    if 'revamped_content' in st.session_state and 'revamp_post_id' in st.session_state:
                        st.markdown("---")
                        st.markdown("## Revamped Post Results")
                        
                        # Show revamped preview in a dedicated container
                        preview_container = st.container()
                        with preview_container:
                            st.subheader("Revamped Post Preview")
                            st.markdown(st.session_state.revamped_content, unsafe_allow_html=True)
                        
                        # Editing options in an expander to save space
                        with st.expander("Edit Revamped Content", expanded=True):
                            edited_content = st.text_area(
                                "HTML Content (you can edit this)",
                                value=st.session_state.revamped_content,
                                height=400
                            )
                            
                            # Action buttons in columns
                            action_col1, action_col2 = st.columns(2)
                            
                            with action_col1:
                                if st.button("📝 Create as New Draft", key="create_draft"):
                                    with st.spinner("Creating new draft post..."):
                                        try:
                                            # Create new draft
                                            title = f"Revamped: {st.session_state.revamp_post_title}"
                                            result = wordpress_api.create_post(
                                                title=title,
                                                content=edited_content,
                                                status="draft",
                                                categories=st.session_state.revamp_post_categories
                                            )
                                            
                                            if result and result.get('success'):
                                                st.success("✅ New draft post created successfully!")
                                                st.write(f"Edit URL: {result.get('edit_url', '')}")
                                            else:
                                                st.error(f"Error creating draft: {result.get('error', 'Unknown error')}")
                                        except Exception as e:
                                            st.error(f"Error creating draft: {str(e)}")
                            
                            with action_col2:
                                if st.button("💾 Save Locally", key="save_locally"):
                                    with st.spinner("Saving blog post locally..."):
                                        try:
                                            filename = f"revamped_{st.session_state.revamp_post_id}"
                                            save_blog_post(
                                                filename, 
                                                edited_content, 
                                                f"Revamped: {st.session_state.revamp_post_title}"
                                            )
                                            st.success(f"✅ Revamped post saved successfully!")
                                        except Exception as e:
                                            st.error(f"Error saving post: {str(e)}")
            else:
                st.info("Search for posts to begin revamping content.")

if __name__ == "__main__":
    import re  # Import at the top
    print("Starting application")
    try:
        main()
        print("Main function completed successfully")
    except Exception as e:
        print(f"Error in main function: {str(e)}")
        traceback.print_exc()