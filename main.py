import streamlit as st
import pandas as pd
import os
import json
from datetime import datetime
import traceback
from utils.fixed_youtube_api import YouTubeAPI
from utils.spotify_api import SpotifyAPI
from utils.openai_api import generate_blog_post
from utils.fixed_wordpress_api import WordPressAPI
from utils.corrected_csv_handler import load_csv, save_csv, create_empty_playlist_df

# Page configuration
st.set_page_config(
    page_title="Moments & Memories Blog Generator",
    page_icon="✨",
    layout="wide"
)

# Custom CSS to match Moments & Memories branding
st.markdown("""
<style>
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

def save_processed_csv(df, operation_type):
    """Save CSV with timestamp and operation type"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"processed_playlists_{operation_type}_{timestamp}.csv"
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
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(f"<h1>{title}</h1>\n\n{blog_content}")
    
    return filename
    
def save_wordpress_post(post_data, post_content=None):
    """Save selected WordPress post for editing
    
    Args:
        post_data: The post data from WordPress API
        post_content: Optional processed content if available
    """
    # Create wordpress_posts directory if it doesn't exist
    if not os.path.exists("wordpress_posts"):
        os.makedirs("wordpress_posts")
    
    # Handle different title formats
    post_title = post_data.get('title', '')
    if isinstance(post_title, dict) and 'rendered' in post_title:
        post_title = post_title.get('rendered', 'Untitled')
    elif not isinstance(post_title, str):
        post_title = 'Untitled'
    
    # Clean the title for use in filename
    clean_title = "".join([c if c.isalnum() or c.isspace() else "_" for c in post_title]).strip()
    post_id = post_data.get('id', 'unknown_id')
    
    # Format post information for storage
    post_info = {
        'id': post_id,
        'title': post_title,
        'post_data': post_data,
        'saved_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'processed_content': post_content
    }
    
    # Save to file
    filename = f"{clean_title}_{post_id}.json"
    filepath = os.path.join("wordpress_posts", filename)
    with open(filepath, 'w') as f:
        json.dump(post_info, f, indent=2, default=str)
    
    return filepath

def list_wordpress_posts():
    """List all saved WordPress posts from the wordpress_posts directory"""
    if not os.path.exists("wordpress_posts"):
        return []
    
    posts = []
    for filename in os.listdir("wordpress_posts"):
        if filename.endswith(".json"):
            filepath = os.path.join("wordpress_posts", filename)
            try:
                with open(filepath, 'r') as f:
                    post_info = json.load(f)
                    # Add filepath to the post info
                    post_info['filepath'] = filepath
                    posts.append(post_info)
            except Exception as e:
                print(f"Error loading {filepath}: {str(e)}")
    
    # Sort by saved_at date (newest first)
    posts.sort(key=lambda x: x.get('saved_at', ''), reverse=True)
    return posts

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

def process_playlist(playlist, youtube_api, spotify_api, operations):
    """Process a single playlist with error handling and progress tracking"""
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
                            st.warning(f"⚠️ Could not fetch YouTube link for '{search_query}': {str(e)}")
                
                # Update the main DataFrame with the new YouTube links
                st.session_state.df.update(playlist_df)
                save_updates = True
                
                # Note the file in results for display purposes
                filename = save_processed_csv(st.session_state.df, "youtube")
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
            filename = save_processed_csv(st.session_state.df, "updated")
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
                
                # Get blog customization options
                style_options = {}
                
                # Check for standard dropdown selections
                try:
                    if 'model' in st.session_state:
                        style_options['model'] = st.session_state.model
                    
                    if 'temperature' in st.session_state:
                        style_options['temperature'] = st.session_state.temperature
                    
                    if 'tone' in st.session_state:
                        style_options['tone'] = st.session_state.tone
                    
                    if 'mood' in st.session_state:
                        style_options['mood'] = st.session_state.mood
                    
                    if 'intro_theme' in st.session_state:
                        style_options['intro_theme'] = st.session_state.intro_theme
                    
                    if 'conclusion_theme' in st.session_state:
                        style_options['conclusion_theme'] = st.session_state.conclusion_theme
                    
                    if 'section_count' in st.session_state:
                        style_options['section_count'] = st.session_state.section_count
                    
                    if 'title_style' in st.session_state:
                        style_options['title_style'] = st.session_state.title_style
                    
                    if 'audience' in st.session_state:
                        style_options['audience'] = st.session_state.audience
                    
                    # Free form style options
                    if 'writing_style' in st.session_state and st.session_state.writing_style:
                        style_options['writing_style'] = st.session_state.writing_style
                    
                    if 'language_style' in st.session_state and st.session_state.language_style:
                        style_options['language_style'] = st.session_state.language_style
                    
                    if 'sentence_structure' in st.session_state and st.session_state.sentence_structure:
                        style_options['sentence_structure'] = st.session_state.sentence_structure
                    
                    if 'emotional_tone' in st.session_state and st.session_state.emotional_tone:
                        style_options['emotional_tone'] = st.session_state.emotional_tone
                    
                    if 'custom_guidance' in st.session_state and st.session_state.custom_guidance:
                        style_options['custom_guidance'] = st.session_state.custom_guidance
                except Exception as e:
                    st.warning(f"Note: Not all customization options could be applied. {str(e)}")
                    # Continue with whatever options were successfully retrieved
                
                # Generate the blog post with style options
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
        youtube_key = os.getenv("YOUTUBE_API_KEY")
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
            os.getenv("SPOTIFY_CLIENT_ID"),
            os.getenv("SPOTIFY_CLIENT_SECRET")
        )
    except Exception as e:
        st.sidebar.error(f"⚠️ Spotify API error: {str(e)}")
        spotify_api = None
    
    # WordPress API initialization
    try:
        wordpress_api = None  # Initialize to None first
        # Check if WordPress credentials are available
        if all([
            os.getenv("WORDPRESS_API_URL"),
            os.getenv("WORDPRESS_USERNAME"),
            os.getenv("WORDPRESS_PASSWORD")
        ]):
            # Get the credentials from environment variables
            api_url = os.getenv("WORDPRESS_API_URL")
            username = os.getenv("WORDPRESS_USERNAME")
            password = os.getenv("WORDPRESS_PASSWORD")
            
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
                    wp_url = os.environ.get("WORDPRESS_API_URL", "").strip()
                    wp_username = os.environ.get("WORDPRESS_USERNAME", "").strip()
                    wp_password = os.environ.get("WORDPRESS_PASSWORD", "").strip()
                    
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
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["Process Playlists", "Edit CSV Data", "Saved Blog Posts", "WordPress Revamp", "WordPress Edit"])
    
    # Auto-load the latest CSV if available
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
        
        # CSV upload section
        uploaded_file = st.file_uploader("Upload CSV File", type=["csv"])
        
        # Process the uploaded file
        if uploaded_file is not None:
            try:
                st.session_state.df = load_csv(uploaded_file)
                st.success("✅ CSV file loaded successfully!")
                
                # Show a preview of the data
                if st.session_state.df is not None and not st.session_state.df.empty:
                    st.write(f"Found {len(st.session_state.df)} songs across {st.session_state.df['Playlist'].nunique()} playlists")
                    
                    # Show a small sample
                    st.write("Preview of loaded data:")
                    preview_cols = ['Playlist', 'Song', 'Artist', 'YouTube_Link', 'Spotify_Link']
                    st.dataframe(st.session_state.df[preview_cols].head(5))
                    
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
            
            # Blog customization options
            if generate_blog:
                with st.expander("Blog Customization Options", expanded=False):
                    # Initialize session state for all customization options
                    if 'model' not in st.session_state:
                        st.session_state.model = "gpt-4o"
                    if 'temperature' not in st.session_state:
                        st.session_state.temperature = 0.7
                    if 'tone' not in st.session_state:
                        st.session_state.tone = "Professional"
                    if 'mood' not in st.session_state:
                        st.session_state.mood = "Elegant"
                    if 'intro_theme' not in st.session_state:
                        st.session_state.intro_theme = "Elegant Opening"
                    if 'conclusion_theme' not in st.session_state:
                        st.session_state.conclusion_theme = "Standard Closing"
                    if 'section_count' not in st.session_state:
                        st.session_state.section_count = "Default (3-4)"
                    if 'title_style' not in st.session_state:
                        st.session_state.title_style = "Descriptive"
                    if 'audience' not in st.session_state:
                        st.session_state.audience = "Modern Couples"
                    if 'writing_style' not in st.session_state:
                        st.session_state.writing_style = ""
                    if 'language_style' not in st.session_state:
                        st.session_state.language_style = ""
                    if 'sentence_structure' not in st.session_state:
                        st.session_state.sentence_structure = ""
                    if 'emotional_tone' not in st.session_state:
                        st.session_state.emotional_tone = ""
                    if 'custom_guidance' not in st.session_state:
                        st.session_state.custom_guidance = ""
                    
                    # Model selection
                    st.subheader("AI Model Settings")
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.session_state.model = st.selectbox(
                            "AI Model",
                            ["gpt-4o", "gpt-4.1", "gpt-4.1-mini", "gpt-4.1-nano"],
                            index=["gpt-4o", "gpt-4.1", "gpt-4.1-mini", "gpt-4.1-nano"].index(st.session_state.model),
                            help="Select which OpenAI model to use for content generation",
                            key="model_selectbox"
                        )
                    
                    with col2:
                        st.session_state.temperature = st.slider(
                            "Creativity Level", 
                            min_value=0.0, 
                            max_value=1.0, 
                            value=st.session_state.temperature, 
                            step=0.1,
                            help="Higher values make output more creative, lower values make it more predictable",
                            key="temperature_slider"
                        )
                    
                    # Style options
                    st.subheader("Blog Style Options")
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        # Tone options with custom option
                        tone_options = ["Professional", "Conversational", "Romantic", "Upbeat", "Elegant", "Playful", "Custom"]
                        tone_index = 0
                        if st.session_state.tone in tone_options:
                            tone_index = tone_options.index(st.session_state.tone)
                        
                        selected_tone = st.selectbox(
                            "Tone",
                            tone_options,
                            index=tone_index,
                            key="tone_selectbox"
                        )
                        
                        # Handle custom tone input
                        if selected_tone == "Custom":
                            custom_tone = st.text_input(
                                "Custom tone", 
                                value="" if st.session_state.tone not in tone_options else st.session_state.tone,
                                placeholder="e.g., 'Friendly yet professional'",
                                key="custom_tone_input"
                            )
                            st.session_state.tone = custom_tone if custom_tone else "Professional"
                        else:
                            st.session_state.tone = selected_tone
                        
                        # Introduction theme
                        intro_options = ["Elegant Opening", "Wedding Story", "Music Importance", "Playlist Introduction", "Custom"]
                        intro_index = 0
                        if st.session_state.intro_theme in intro_options:
                            intro_index = intro_options.index(st.session_state.intro_theme)
                        
                        selected_intro = st.selectbox(
                            "Introduction Theme",
                            intro_options,
                            index=intro_index,
                            key="intro_selectbox"
                        )
                        
                        # Handle custom intro input
                        if selected_intro == "Custom":
                            custom_intro = st.text_input(
                                "Custom introduction theme", 
                                value="" if st.session_state.intro_theme not in intro_options else st.session_state.intro_theme,
                                placeholder="e.g., 'Start with a quote about music'",
                                key="custom_intro_input"
                            )
                            st.session_state.intro_theme = custom_intro if custom_intro else "Elegant Opening"
                        else:
                            st.session_state.intro_theme = selected_intro
                    
                    with col2:
                        # Mood options
                        mood_options = ["Elegant", "Fun", "Emotional", "Energetic", "Romantic", "Nostalgic", "Custom"]
                        mood_index = 0
                        if st.session_state.mood in mood_options:
                            mood_index = mood_options.index(st.session_state.mood)
                        
                        selected_mood = st.selectbox(
                            "Mood",
                            mood_options,
                            index=mood_index,
                            key="mood_selectbox"
                        )
                        
                        # Handle custom mood input
                        if selected_mood == "Custom":
                            custom_mood = st.text_input(
                                "Custom mood", 
                                value="" if st.session_state.mood not in mood_options else st.session_state.mood,
                                placeholder="e.g., 'Sophisticated with a touch of whimsy'",
                                key="custom_mood_input"
                            )
                            st.session_state.mood = custom_mood if custom_mood else "Elegant"
                        else:
                            st.session_state.mood = selected_mood
                        
                        # Conclusion theme
                        conclusion_options = ["Standard Closing", "Planning Tips", "Guest Experience", "DJ Perspective", "Custom"]
                        conclusion_index = 0
                        if st.session_state.conclusion_theme in conclusion_options:
                            conclusion_index = conclusion_options.index(st.session_state.conclusion_theme)
                        
                        selected_conclusion = st.selectbox(
                            "Conclusion Theme",
                            conclusion_options,
                            index=conclusion_index,
                            key="conclusion_selectbox"
                        )
                        
                        # Handle custom conclusion input
                        if selected_conclusion == "Custom":
                            custom_conclusion = st.text_input(
                                "Custom conclusion theme", 
                                value="" if st.session_state.conclusion_theme not in conclusion_options else st.session_state.conclusion_theme,
                                placeholder="e.g., 'End with planning tips'",
                                key="custom_conclusion_input"
                            )
                            st.session_state.conclusion_theme = custom_conclusion if custom_conclusion else "Standard Closing"
                        else:
                            st.session_state.conclusion_theme = selected_conclusion
                    
                    # Section count with dropdown and custom
                    section_count_options = ["Default (3-4)", "Minimal (2-3)", "Comprehensive (4-5)", "Detailed (5-6)", "Custom"]
                    section_index = 0
                    if st.session_state.section_count in section_count_options:
                        section_index = section_count_options.index(st.session_state.section_count)
                    
                    selected_section_count = st.selectbox(
                        "Content Sections",
                        section_count_options,
                        index=section_index,
                        key="section_count_selectbox"
                    )
                    
                    # Handle custom section count input
                    if selected_section_count == "Custom":
                        custom_section_count = st.text_input(
                            "Custom section count", 
                            value="" if st.session_state.section_count not in section_count_options else st.session_state.section_count,
                            placeholder="e.g., '3 focused sections'",
                            key="custom_section_count_input"
                        )
                        st.session_state.section_count = custom_section_count if custom_section_count else "Default (3-4)"
                    else:
                        st.session_state.section_count = selected_section_count
                    
                    # Advanced options section (not an expander to avoid nesting issues)
                    st.subheader("Advanced Customization")
                    
                    # Title style options
                    title_style_options = ["Descriptive", "Short", "Playful", "Elegant", "Question", "Custom"]
                    title_index = 0
                    if st.session_state.title_style in title_style_options:
                        title_index = title_style_options.index(st.session_state.title_style)
                    
                    selected_title_style = st.selectbox(
                        "Section Title Style",
                        title_style_options,
                        index=title_index,
                        key="title_style_selectbox"
                    )
                    
                    # Handle custom title style input
                    if selected_title_style == "Custom":
                        custom_title = st.text_input(
                            "Custom title style", 
                            value="" if st.session_state.title_style not in title_style_options else st.session_state.title_style,
                            placeholder="e.g., 'Alliterative and punchy'",
                            key="custom_title_style_input"
                        )
                        st.session_state.title_style = custom_title if custom_title else "Descriptive"
                    else:
                        st.session_state.title_style = selected_title_style
                    
                    # Target audience options
                    audience_options = ["Modern Couples", "Traditional Couples", "Brides", "Grooms", "Parents", "All Couples", "Custom"]
                    audience_index = 0
                    if st.session_state.audience in audience_options:
                        audience_index = audience_options.index(st.session_state.audience)
                    
                    selected_audience = st.selectbox(
                        "Target Audience",
                        audience_options,
                        index=audience_index,
                        key="audience_selectbox"
                    )
                    
                    # Handle custom audience input
                    if selected_audience == "Custom":
                        custom_audience = st.text_input(
                            "Custom target audience", 
                            value="" if st.session_state.audience not in audience_options else st.session_state.audience,
                            placeholder="e.g., 'Music-loving couples'",
                            key="custom_audience_input"
                        )
                        st.session_state.audience = custom_audience if custom_audience else "Modern Couples"
                    else:
                        st.session_state.audience = selected_audience
                    
                    # Free form style options
                    st.subheader("Free-Form Style Options")
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        # Free-form writing style
                        st.session_state.writing_style = st.text_input(
                            "Writing Style",
                            value=st.session_state.writing_style,
                            placeholder="e.g., Elegant and poetic, Modern and trendy",
                            help="Describe the writing style you want the AI to use",
                            key="writing_style_input"
                        )
                        
                        # Free-form language style
                        st.session_state.language_style = st.text_input(
                            "Language Style",
                            value=st.session_state.language_style,
                            placeholder="e.g., Sophisticated vocabulary, Simple and clear",
                            help="Describe how complex or simple the language should be",
                            key="language_style_input"
                        )
                    
                    with col2:
                        # Free-form sentence structure
                        st.session_state.sentence_structure = st.text_input(
                            "Sentence Structure",
                            value=st.session_state.sentence_structure,
                            placeholder="e.g., Varied length, Short and punchy",
                            help="Describe the desired sentence structure and flow",
                            key="sentence_structure_input"
                        )
                        
                        # Free-form emotional tone
                        st.session_state.emotional_tone = st.text_input(
                            "Emotional Tone",
                            value=st.session_state.emotional_tone,
                            placeholder="e.g., Heartfelt, Exciting, Calm and peaceful",
                            help="Describe the emotional feeling you want the blog to convey",
                            key="emotional_tone_input"
                        )
                    
                    # Custom guidance
                    st.session_state.custom_guidance = st.text_area(
                        "Additional Style Guidance (Optional)",
                        value=st.session_state.custom_guidance,
                        placeholder="Add any additional style guidance or specific requests for the AI blog writer",
                        height=100,
                        key="custom_guidance_textarea"
                    )
            
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
                                success, results = process_playlist(playlist, youtube_api, spotify_api, operations)
                                
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
                                        
                                        # Show the blog content in a text area
                                        blog_content = results['blog_post']
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
            # Get unique playlists from the dataframe
            playlists = st.session_state.df['Playlist'].unique()
            
            # Format the playlist names for display (remove numeric prefixes)
            display_names = {p: re.sub(r'^\d{3}\s+', '', p) for p in playlists}
            
            # Dropdown to select a playlist to edit
            selected_edit_playlist = st.selectbox(
                "Select a playlist to edit:",
                options=playlists,
                format_func=lambda x: display_names[x]
            )
            
            if selected_edit_playlist:
                # Filter dataframe for selected playlist
                edit_df = st.session_state.df[st.session_state.df['Playlist'] == selected_edit_playlist].copy()
                
                # Determine columns to display
                edit_columns = ['Song', 'Artist', 'YouTube_Link', 'Spotify_Link']
                
                # Display the dataframe for viewing
                st.dataframe(
                    edit_df[edit_columns],
                    use_container_width=True,
                    hide_index=True
                )
                
                # Button to add new songs
                if st.button("➕ Add New Song"):
                    # Create a new row with the current playlist
                    new_row = {
                        'Playlist': selected_edit_playlist,
                        'Song': 'New Song',
                        'Artist': 'Artist Name',
                        'Song_Artist': 'New Song-Artist Name',
                        'YouTube_Link': '',
                        'Spotify_Link': edit_df['Spotify_Link'].iloc[0] if 'Spotify_Link' in edit_df.columns else ''
                    }
                    
                    # Add the new row to the dataframe
                    st.session_state.df = pd.concat([
                        st.session_state.df, 
                        pd.DataFrame([new_row])
                    ], ignore_index=True)
                    
                    # Save the updated dataframe
                    filename = save_processed_csv(st.session_state.df, "added_song")
                    st.success(f"✅ Added new song to playlist and saved to {filename}!")
                    st.experimental_rerun()
            
            # Create new playlist section
            st.markdown("---")
            st.subheader("Create New Playlist")
            
            # Input fields for new playlist
            new_playlist_name = st.text_input(
                "New Playlist Name",
                placeholder="e.g., The Elegant Wedding Cocktail Hour"
            )
            
            # Create button
            if st.button("✨ Create New Playlist"):
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
                    
                    # Add empty row with the new playlist
                    new_row = {
                        'Playlist': formatted_playlist_name,
                        'Song': 'First Song',
                        'Artist': 'Artist Name',
                        'Song_Artist': 'First Song-Artist Name',
                        'YouTube_Link': '',
                        'Spotify_Link': ''
                    }
                    
                    # Add to dataframe
                    st.session_state.df = pd.concat([
                        st.session_state.df, 
                        pd.DataFrame([new_row])
                    ], ignore_index=True)
                    
                    # Save updated dataframe
                    filename = save_processed_csv(st.session_state.df, "new_playlist")
                    st.success(f"✅ Created new playlist '{new_playlist_name}' and saved to {filename}!")
                    st.experimental_rerun()
                else:
                    st.warning("⚠️ Please enter a playlist name")
        else:
            st.warning("⚠️ Please upload a CSV file first or select a previously saved file.")
    
    # Tab 3: Saved Blog Posts
    with tab3:
        st.subheader("Saved Blog Posts")
        
        # Find all saved blog posts
        blog_files = find_saved_blog_posts()
        
        if blog_files:
            # Create a dropdown to select a blog post
            selected_blog = st.selectbox("Select a saved blog post:", blog_files)
            
            if selected_blog:
                # Load the selected blog post
                title, content = load_saved_blog_post(selected_blog)
                
                # Display the title and content
                st.write(f"### {title}")
                st.text_area("Blog Content", content, height=300)
                
                # WordPress posting section
                if wordpress_api:
                    # Add a unique key for this button to avoid duplicate element IDs
                    button_key = f"post_wordpress_{selected_blog}"
                    if st.button("🚀 Post to WordPress", key=button_key):
                        with st.spinner("📝 Creating draft post in WordPress..."):
                            try:
                                # Post to WordPress as draft
                                result = wordpress_api.create_post(
                                    title=title,
                                    content=content,
                                    status="draft"
                                )
                                
                                if result.get('success'):
                                    post_id = result.get('post_id')
                                    post_url = result.get('post_url')
                                    edit_url = result.get('edit_url')
                                    
                                    st.success(f"✅ Draft post created! ID: {post_id}")
                                    st.write(f"View/Edit: {edit_url}")
                                else:
                                    error_msg = result.get('error', 'Unknown error')
                                    st.error(f"❌ Failed to create post: {error_msg}")
                            except Exception as e:
                                st.error(f"❌ Error posting to WordPress: {str(e)}")
        else:
            st.info("No saved blog posts found. Generate some blog posts first!")

# WordPress Revamp Tab
    with tab4:
        st.subheader("WordPress Revamp")
        
        # Check if WordPress API is available
        if wordpress_api is None:
            st.error("WordPress API is not configured. Please configure it in the environment settings.")
            st.info("WordPress connection requires WORDPRESS_API_URL, WORDPRESS_USERNAME, and WORDPRESS_PASSWORD environment variables.")
        else:
            # Initialize session state variables for WordPress revamp tab
            if 'wp_search_term' not in st.session_state:
                st.session_state.wp_search_term = ""
            if 'wp_posts' not in st.session_state:
                st.session_state.wp_posts = []
            if 'wp_selected_post' not in st.session_state:
                st.session_state.wp_selected_post = None
            if 'wp_post_confirmed' not in st.session_state:
                st.session_state.wp_post_confirmed = False
            if 'wp_revamped_content' not in st.session_state:
                st.session_state.wp_revamped_content = None
                
            if not st.session_state.wp_post_confirmed:
                # Stage 1: Post Selection
                st.write("Find WordPress posts to revamp by searching or browsing categories.")
                
                # Initialize category state if needed
                if 'wp_categories' not in st.session_state:
                    st.session_state.wp_categories = []
                    try:
                        with st.spinner("Loading categories..."):
                            categories = wordpress_api.get_categories()
                            if categories:
                                st.session_state.wp_categories = categories
                    except Exception as e:
                        st.error(f"Could not load categories: {str(e)}")
                
                # Create tabs for different ways to find posts
                find_tabs = st.tabs(["Search by Title", "Browse by Category"])
                
                # Tab 1: Search by title
                with find_tabs[0]:
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        search_term = st.text_input(
                            "Search by title", 
                            value=st.session_state.wp_search_term,
                            key="wordpress_search_input"
                        )
                    with col2:
                        if st.button("🔍 Search", key="wordpress_search_button"):
                            with st.spinner("Searching WordPress posts..."):
                                st.session_state.wp_search_term = search_term
                                try:
                                    result = wordpress_api.get_posts(
                                        search_term=search_term,
                                        per_page=10,
                                        page=1
                                    )
                                    
                                    if result and 'posts' in result and result['posts']:
                                        st.session_state.wp_posts = result['posts']
                                        st.success(f"Found {len(result['posts'])} posts matching your search.")
                                    else:
                                        st.info("No posts found matching your search criteria.")
                                        st.session_state.wp_posts = []
                                except Exception as e:
                                    st.error(f"Error searching WordPress posts: {str(e)}")
                                    st.session_state.wp_posts = []
                
                # Tab 2: Browse by category
                with find_tabs[1]:
                    if st.session_state.wp_categories:
                        # Format categories for display
                        category_options = []
                        category_display = {}
                        
                        for category in st.session_state.wp_categories:
                            cat_id = category.get('id')
                            cat_name = category.get('name', 'Unnamed')
                            cat_count = category.get('count', 0)
                            
                            if cat_count > 0:  # Only show categories with posts
                                display_text = f"{cat_name} ({cat_count} posts)"
                                category_options.append(cat_id)
                                category_display[cat_id] = display_text
                        
                        if category_options:
                            # Category selection dropdown
                            selected_category = st.selectbox(
                                "Select a category",
                                options=category_options,
                                format_func=lambda x: category_display.get(x, f"Category {x}"),
                                key="wordpress_category_selector"
                            )
                            
                            # Button to load posts for selected category
                            if st.button("Load Posts", key="wordpress_load_category_button"):
                                with st.spinner(f"Loading posts from selected category..."):
                                    try:
                                        result = wordpress_api.get_posts(
                                            category=selected_category,
                                            per_page=20,
                                            page=1
                                        )
                                        
                                        if result and 'posts' in result and result['posts']:
                                            st.session_state.wp_posts = result['posts']
                                            st.session_state.wp_search_term = ""  # Clear search term
                                            st.success(f"Found {len(result['posts'])} posts in the selected category.")
                                        else:
                                            st.info("No posts found in this category.")
                                            st.session_state.wp_posts = []
                                    except Exception as e:
                                        st.error(f"Error loading posts from category: {str(e)}")
                                        st.session_state.wp_posts = []
                        else:
                            st.info("No categories with posts available.")
                    else:
                        st.info("No categories found. Please check your WordPress site configuration.")
                        # Reload categories button
                        if st.button("Reload Categories", key="wordpress_reload_categories"):
                            with st.spinner("Loading categories..."):
                                try:
                                    categories = wordpress_api.get_categories()
                                    if categories:
                                        st.session_state.wp_categories = categories
                                        st.success(f"Loaded {len(categories)} categories.")
                                    else:
                                        st.warning("No categories found on your WordPress site.")
                                except Exception as e:
                                    st.error(f"Error loading categories: {str(e)}")
                
                # Display results if available
                if st.session_state.wp_posts:
                    # Format for display
                    post_options = []
                    post_display = {}
                    
                    for post in st.session_state.wp_posts:
                        post_id = post.get('id')
                        post_title = post.get('title')
                        post_date = post.get('date', '').split('T')[0] if post.get('date') else ''
                        
                        # Handle different title formats
                        if isinstance(post_title, dict) and 'rendered' in post_title:
                            post_title = post_title.get('rendered', 'Untitled')
                        elif isinstance(post_title, str):
                            post_title = post_title
                        else:
                            post_title = 'Untitled'
                        
                        display_text = f"{post_title} ({post_date})"
                        post_options.append(post_id)
                        post_display[post_id] = display_text
                    
                    # Post selection UI
                    selected_post_id = st.selectbox(
                        "Select a post to revamp:",
                        options=post_options,
                        format_func=lambda x: post_display.get(x, f"Post ID: {x}"),
                        key="wordpress_post_selector"
                    )
                    
                    # Get the full post data for the selected post
                    selected_post = None
                    for post in st.session_state.wp_posts:
                        if post.get('id') == selected_post_id:
                            selected_post = post
                            st.session_state.wp_selected_post = post  # Save to session state
                            break
                    
                    if selected_post:
                        # Handle post title (could be string or dict with rendered property)
                        post_title = selected_post.get('title', '')
                        if isinstance(post_title, dict) and 'rendered' in post_title:
                            post_title = post_title.get('rendered', 'Untitled')
                        elif not isinstance(post_title, str):
                            post_title = 'Untitled'
                            
                        # Handle post date
                        post_date = selected_post.get('date', '')
                        if post_date and isinstance(post_date, str):
                            post_date = post_date.split('T')[0] if 'T' in post_date else post_date
                        
                        st.write(f"**Selected Post:** {post_title}")
                        st.write(f"**Date Published:** {post_date}")
                        
                        # Preview button
                        if st.button("👁️ Preview Post", key="wordpress_preview_button"):
                            # Handle post content (could be string or dict with rendered property)
                            post_content = selected_post.get('content', '')
                            if isinstance(post_content, dict) and 'rendered' in post_content:
                                post_content = post_content.get('rendered', 'No content available')
                            elif not isinstance(post_content, str):
                                post_content = 'No content available'
                                
                            with st.expander("Post Content", expanded=True):
                                st.markdown(post_content, unsafe_allow_html=True)
                        
                        # Save post for editing button
                        if st.button("💾 Save for Editing", key="wordpress_save_button"):
                            # Extract the content with proper handling of different formats
                            post_content = selected_post.get('content', '')
                            if isinstance(post_content, dict) and 'rendered' in post_content:
                                post_content = post_content.get('rendered', '')
                            
                            # Save the post to file
                            saved_path = save_wordpress_post(selected_post, post_content)
                            st.success(f"Post '{post_title}' saved for editing! Go to the 'Saved Posts' tab to edit it.")
                            # Rather than rerun here (which can cause issues), we'll let the page refresh naturally
            
            else:
                # Stage 2: Post Customization and Revamp (post is confirmed)
                selected_post = st.session_state.wp_selected_post
                
                if not selected_post:
                    st.error("No post selected. Please go back and select a post.")
                    if st.button("⬅️ Back to Selection", key="wordpress_back_button"):
                        st.session_state.wp_post_confirmed = False
                        st.session_state.wp_selected_post = None
                else:
                    # Post header - handle different title formats
                    post_title = selected_post.get('title', '')
                    if isinstance(post_title, dict) and 'rendered' in post_title:
                        post_title = post_title.get('rendered', 'Untitled')
                    elif not isinstance(post_title, str):
                        post_title = 'Untitled'
                        
                    post_id = selected_post.get('id')
                    post_date = selected_post.get('date', '').split('T')[0]
                    
                    st.write(f"### Revamping: {post_title}")
                    st.write(f"**ID:** {post_id} | **Published:** {post_date}")
                    
                    # Back button
                    if st.button("⬅️ Back to Selection", key="wordpress_back_button2"):
                        st.session_state.wp_post_confirmed = False
                        # Keep the selected post in memory, but don't mark it as confirmed
                    
                    # Initialize blog style options in session state if not present
                    if 'wp_revamp_model' not in st.session_state:
                        st.session_state.wp_revamp_model = "gpt-4o"
                    if 'wp_revamp_temp' not in st.session_state:
                        st.session_state.wp_revamp_temp = 0.7
                    if 'wp_revamp_tone' not in st.session_state:
                        st.session_state.wp_revamp_tone = "Professional"
                    if 'wp_revamp_mood' not in st.session_state:
                        st.session_state.wp_revamp_mood = "Elegant"
                    if 'wp_revamp_audience' not in st.session_state:
                        st.session_state.wp_revamp_audience = "Modern Couples"
                    
                    # Original content expander
                    with st.expander("Original Content", expanded=False):
                        post_content = selected_post.get('content', '')
                        if isinstance(post_content, dict) and 'rendered' in post_content:
                            post_content = post_content.get('rendered', 'No content available')
                        elif not isinstance(post_content, str):
                            post_content = 'No content available'
                            
                        st.markdown(post_content, unsafe_allow_html=True)
                    
                    # Style customization options
                    st.subheader("Blog Style Options")
                    
                    # Two columns for model options
                    col1, col2 = st.columns(2)
                    with col1:
                        # Use session state to maintain selection
                        model = st.selectbox(
                            "AI Model",
                            ["gpt-4o", "gpt-4.1", "gpt-4.1-mini"],
                            index=["gpt-4o", "gpt-4.1", "gpt-4.1-mini"].index(st.session_state.wp_revamp_model),
                            key="wp_model_select"
                        )
                        st.session_state.wp_revamp_model = model
                    
                    with col2:
                        # Use session state to maintain slider value
                        temp = st.slider(
                            "Creativity Level",
                            min_value=0.0,
                            max_value=1.0,
                            value=st.session_state.wp_revamp_temp,
                            step=0.1,
                            key="wp_temp_slider"
                        )
                        st.session_state.wp_revamp_temp = temp
                    
                    # Two columns for style options
                    col1, col2 = st.columns(2)
                    with col1:
                        # Tone options
                        tone_options = ["Professional", "Conversational", "Romantic", "Upbeat", "Elegant", "Custom"]
                        tone_index = 0
                        if st.session_state.wp_revamp_tone in tone_options:
                            tone_index = tone_options.index(st.session_state.wp_revamp_tone)
                        
                        tone = st.selectbox(
                            "Tone",
                            tone_options,
                            index=tone_index,
                            key="wp_tone_select"
                        )
                        
                        if tone == "Custom":
                            custom_tone = st.text_input(
                                "Custom tone",
                                value="" if st.session_state.wp_revamp_tone not in tone_options else st.session_state.wp_revamp_tone,
                                key="wp_custom_tone_input"
                            )
                            st.session_state.wp_revamp_tone = custom_tone if custom_tone else "Professional"
                        else:
                            st.session_state.wp_revamp_tone = tone
                    
                    with col2:
                        # Mood options
                        mood_options = ["Elegant", "Fun", "Emotional", "Energetic", "Romantic", "Custom"]
                        mood_index = 0
                        if st.session_state.wp_revamp_mood in mood_options:
                            mood_index = mood_options.index(st.session_state.wp_revamp_mood)
                        
                        mood = st.selectbox(
                            "Mood",
                            mood_options,
                            index=mood_index,
                            key="wp_mood_select"
                        )
                        
                        if mood == "Custom":
                            custom_mood = st.text_input(
                                "Custom mood",
                                value="" if st.session_state.wp_revamp_mood not in mood_options else st.session_state.wp_revamp_mood,
                                key="wp_custom_mood_input"
                            )
                            st.session_state.wp_revamp_mood = custom_mood if custom_mood else "Elegant"
                        else:
                            st.session_state.wp_revamp_mood = mood
                    
                    # Audience selection
                    audience_options = ["Modern Couples", "Traditional Couples", "Brides", "Grooms", "All Couples", "Custom"]
                    audience_index = 0
                    if st.session_state.wp_revamp_audience in audience_options:
                        audience_index = audience_options.index(st.session_state.wp_revamp_audience)
                    
                    audience = st.selectbox(
                        "Target Audience",
                        audience_options,
                        index=audience_index,
                        key="wp_audience_select"
                    )
                    
                    if audience == "Custom":
                        custom_audience = st.text_input(
                            "Custom audience",
                            value="" if st.session_state.wp_revamp_audience not in audience_options else st.session_state.wp_revamp_audience,
                            key="wp_custom_audience_input"
                        )
                        st.session_state.wp_revamp_audience = custom_audience if custom_audience else "Modern Couples"
                    else:
                        st.session_state.wp_revamp_audience = audience
                    
                    # Additional guidance
                    if 'wp_revamp_guidance' not in st.session_state:
                        st.session_state.wp_revamp_guidance = ""
                    
                    guidance = st.text_area(
                        "Additional Style Guidance (Optional)",
                        value=st.session_state.wp_revamp_guidance,
                        placeholder="Add any specific style instructions or requirements for the revamped blog post",
                        height=100,
                        key="wp_guidance_input"
                    )
                    st.session_state.wp_revamp_guidance = guidance
                    
                    # Save for editing button (add alongside revamp button)
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("💾 Save for Editing Later", key="wp_save_for_edit_button"):
                            # Extract content properly
                            post_content = selected_post.get('content', '')
                            if isinstance(post_content, dict) and 'rendered' in post_content:
                                post_content = post_content.get('rendered', '')
                            elif not isinstance(post_content, str):
                                post_content = ''
                                
                            # Save post data
                            saved_path = save_wordpress_post(selected_post, post_content)
                            st.success(f"Post '{post_title}' saved for editing! Go to the WordPress Edit tab to edit it.")
                    
                    with col2:
                        # Revamp button
                        if st.button("✨ Revamp Blog Post", key="wp_revamp_button"):
                            with st.spinner("Revamping blog post content..."):
                                try:
                                    # Get post content with proper handling for different formats
                                    post_content = selected_post.get('content', '')
                                    if isinstance(post_content, dict) and 'rendered' in post_content:
                                        post_content = post_content.get('rendered', '')
                                    elif not isinstance(post_content, str):
                                        post_content = ''
                                
                                    # Get post title with proper handling for different formats
                                    post_title = selected_post.get('title', '')
                                    if isinstance(post_title, dict) and 'rendered' in post_title:
                                        post_title = post_title.get('rendered', 'Untitled')
                                    elif not isinstance(post_title, str):
                                        post_title = 'Untitled'
                                
                                    # Import necessary functions
                                    from utils.openai_api import revamp_existing_blog, extract_spotify_link
                                    
                                    # Extract Spotify link if available
                                    spotify_link = extract_spotify_link(post_content)
                                    
                                    # Create style options dictionary
                                    style_options = {
                                        'model': st.session_state.wp_revamp_model,
                                        'temperature': st.session_state.wp_revamp_temp,
                                        'tone': st.session_state.wp_revamp_tone,
                                        'mood': st.session_state.wp_revamp_mood,
                                        'audience': st.session_state.wp_revamp_audience
                                    }
                                    
                                    if st.session_state.wp_revamp_guidance:
                                        style_options['custom_guidance'] = st.session_state.wp_revamp_guidance
                                    
                                    # Generate revamped content
                                    revamped_content = revamp_existing_blog(
                                        post_content=post_content,
                                        post_title=post_title,
                                        youtube_api=youtube_api,
                                        style_options=style_options
                                    )
                                    
                                    # Store in session state
                                    st.session_state.wp_revamped_content = revamped_content
                                    
                                    # Show success message
                                    st.success("✨ Blog post successfully revamped!")
                                    
                                    # Show the revamped content preview
                                    with st.expander("Revamped Content Preview", expanded=True):
                                        st.markdown(revamped_content, unsafe_allow_html=True)
                                    
                                    # Post to WordPress options
                                    st.subheader("Publish Options")
                                    
                                    # Title and status
                                    new_title = st.text_input("Post Title", value=post_title)
                                    status = st.selectbox(
                                        "Post Status",
                                        options=["draft", "publish"],
                                        index=0,
                                        key="wp_status_select"
                                    )
                                
                                    # Posting actions
                                    # Use 3 columns for buttons
                                    col1, col2, col3 = st.columns(3)
                                    
                                    with col1:
                                        # Post to WordPress
                                        if st.button("🚀 Post to WordPress", key="wp_post_button"):
                                            with st.spinner("Creating post in WordPress..."):
                                                try:
                                                    result = wordpress_api.create_post(
                                                        title=new_title,
                                                        content=revamped_content,
                                                        status=status
                                                    )
                                                    
                                                    if result.get('success'):
                                                        st.success(f"✅ Post created successfully! ID: {result.get('post_id')}")
                                                        if result.get('edit_url'):
                                                            st.markdown(f"[View/Edit Post on WordPress]({result.get('edit_url')})")
                                                    else:
                                                        st.error(f"❌ Failed to create post: {result.get('error')}")
                                                except Exception as e:
                                                    st.error(f"❌ Error creating post: {str(e)}")
                                    
                                    with col2:
                                        # Save locally
                                        if st.button("💾 Save Locally", key="wp_save_local_button"):
                                            try:
                                                filename = save_blog_post(
                                                    playlist_name=f"Revamped-{post_id}",
                                                    blog_content=revamped_content,
                                                    title=new_title
                                                )
                                                st.success(f"✅ Revamped blog post saved to {filename}")
                                            except Exception as e:
                                                st.error(f"❌ Error saving blog post: {str(e)}")
                                    
                                    with col3:
                                        # Save for editing in WordPress Edit tab
                                        if st.button("✏️ Save for Editing", key="wp_save_for_edit_button"):
                                            try:
                                                # Save the post data and revamped content for editing
                                                original_post = st.session_state.wp_selected_post
                                                filepath = save_wordpress_post(
                                                    post_data=original_post,
                                                    post_content=revamped_content
                                                )
                                                st.success(f"✅ Post saved for editing! Go to the WordPress Edit tab to continue.")
                                            except Exception as e:
                                                st.error(f"❌ Error saving post for editing: {str(e)}")
                                except Exception as e:
                                    st.error(f"❌ Error revamping blog post: {str(e)}")
                                    st.error(traceback.format_exc())
    
    # Tab 5: WordPress Edit
    with tab5:
        st.subheader("WordPress Edit")
        
        # List all saved WordPress posts
        saved_posts = list_wordpress_posts()
        
        if not saved_posts:
            st.info("No saved WordPress posts found. Go to the WordPress Revamp tab to browse and save posts first.")
        else:
            # Create dropdown with post titles
            post_options = []
            post_display = {}
            
            for post in saved_posts:
                post_id = post.get('id', 'unknown')
                post_title = post.get('title', 'Untitled')
                if isinstance(post_title, dict) and 'rendered' in post_title:
                    post_title = post_title.get('rendered', 'Untitled')
                
                saved_at = post.get('saved_at', '')
                filepath = post.get('filepath', '')
                
                display_text = f"{post_title} (Saved: {saved_at})"
                post_options.append(filepath)
                post_display[filepath] = display_text
            
            selected_post_path = st.selectbox(
                "Select a saved post to edit:",
                options=post_options,
                format_func=lambda x: post_display.get(x, f"Post: {x}"),
                key="wordpress_edit_select_1"
            )
            
            # Load selected post
            if selected_post_path:
                try:
                    with open(selected_post_path, 'r') as f:
                        post_data = json.load(f)
                        
                    post_title = post_data.get('title', 'Untitled')
                    if isinstance(post_title, dict) and 'rendered' in post_title:
                        post_title = post_title.get('rendered', 'Untitled')
                    
                    post_id = post_data.get('id', 'unknown')
                    post_content = post_data.get('post_data', {}).get('content', '')
                    
                    # Handle content format (could be string or dict with rendered property)
                    if isinstance(post_content, dict) and 'rendered' in post_content:
                        post_content = post_content.get('rendered', '')
                    
                    st.write(f"### Editing: {post_title}")
                    st.write(f"**Post ID:** {post_id}")
                    
                    # Show original content in expander
                    with st.expander("Original Content", expanded=False):
                        st.markdown(post_content, unsafe_allow_html=True)
                    
                    # Initialize blog style options 
                    if 'wp_edit_model' not in st.session_state:
                        st.session_state.wp_edit_model = "gpt-4o"
                    if 'wp_edit_temp' not in st.session_state:
                        st.session_state.wp_edit_temp = 0.7
                    if 'wp_edit_tone' not in st.session_state:
                        st.session_state.wp_edit_tone = "Professional"
                    if 'wp_edit_mood' not in st.session_state:
                        st.session_state.wp_edit_mood = "Elegant"
                    if 'wp_edit_audience' not in st.session_state:
                        st.session_state.wp_edit_audience = "Modern Couples"
                    
                    # Style customization options
                    st.subheader("Blog Style Options")
                    
                    # Two columns for model options
                    col1, col2 = st.columns(2)
                    with col1:
                        model = st.selectbox(
                            "AI Model",
                            ["gpt-4o", "gpt-4.1", "gpt-4.1-mini"],
                            index=["gpt-4o", "gpt-4.1", "gpt-4.1-mini"].index(st.session_state.wp_edit_model),
                            key="wp_edit_model_select_1"
                        )
                        st.session_state.wp_edit_model = model
                    
                    with col2:
                        temp = st.slider(
                            "Creativity Level",
                            min_value=0.0,
                            max_value=1.0,
                            value=st.session_state.wp_edit_temp,
                            step=0.1,
                            key="wp_edit_temp_slider_1"
                        )
                        st.session_state.wp_edit_temp = temp
                    
                    # Two columns for style options
                    col1, col2 = st.columns(2)
                    
                    # Column 1: Tone
                    with col1:
                        tone_options = ["Professional", "Conversational", "Romantic", "Upbeat", "Elegant", "Custom"]
                        tone_index = 0
                        if st.session_state.wp_edit_tone in tone_options:
                            tone_index = tone_options.index(st.session_state.wp_edit_tone)
                        
                        tone = st.selectbox(
                            "Writing Tone",
                            tone_options,
                            index=tone_index,
                            key="wp_edit_tone_select"
                        )
                        
                        if tone == "Custom":
                            custom_tone = st.text_input(
                                "Custom tone",
                                value="" if st.session_state.wp_edit_tone not in tone_options else st.session_state.wp_edit_tone,
                                key="wp_edit_custom_tone_input"
                            )
                            st.session_state.wp_edit_tone = custom_tone if custom_tone else "Professional"
                        else:
                            st.session_state.wp_edit_tone = tone
                    
                    # Column 2: Mood
                    with col2:
                        mood_options = ["Elegant", "Fun", "Emotional", "Energetic", "Nostalgic", "Custom"]
                        mood_index = 0
                        if st.session_state.wp_edit_mood in mood_options:
                            mood_index = mood_options.index(st.session_state.wp_edit_mood)
                        
                        mood = st.selectbox(
                            "Overall Mood",
                            mood_options,
                            index=mood_index,
                            key="wp_edit_mood_select"
                        )
                        
                        if mood == "Custom":
                            custom_mood = st.text_input(
                                "Custom mood",
                                value="" if st.session_state.wp_edit_mood not in mood_options else st.session_state.wp_edit_mood,
                                key="wp_edit_custom_mood_input"
                            )
                            st.session_state.wp_edit_mood = custom_mood if custom_mood else "Elegant"
                        else:
                            st.session_state.wp_edit_mood = mood
                    
                    # Audience selection
                    audience_options = ["Modern Couples", "Traditional Couples", "Brides", "Grooms", "All Couples", "Custom"]
                    audience_index = 0
                    if st.session_state.wp_edit_audience in audience_options:
                        audience_index = audience_options.index(st.session_state.wp_edit_audience)
                    
                    audience = st.selectbox(
                        "Target Audience",
                        audience_options,
                        index=audience_index,
                        key="wp_edit_audience_select"
                    )
                    
                    if audience == "Custom":
                        custom_audience = st.text_input(
                            "Custom audience",
                            value="" if st.session_state.wp_edit_audience not in audience_options else st.session_state.wp_edit_audience,
                            key="wp_edit_custom_audience_input"
                        )
                        st.session_state.wp_edit_audience = custom_audience if custom_audience else "Modern Couples"
                    else:
                        st.session_state.wp_edit_audience = audience
                    
                    # Additional guidance
                    if 'wp_edit_guidance' not in st.session_state:
                        st.session_state.wp_edit_guidance = ""
                    
                    guidance = st.text_area(
                        "Additional Style Guidance (Optional)",
                        value=st.session_state.wp_edit_guidance,
                        placeholder="Add any specific style instructions or requirements for the revamped blog post",
                        height=100,
                        key="wp_edit_guidance_input"
                    )
                    st.session_state.wp_edit_guidance = guidance
                    
                    # Revamp button
                    if st.button("✨ Revamp Blog Post", key="wp_edit_revamp_button"):
                        with st.spinner("Revamping blog post content..."):
                            try:
                                # Import necessary functions
                                from utils.openai_api import revamp_existing_blog, extract_spotify_link
                                
                                # Extract Spotify link if available
                                spotify_link = extract_spotify_link(post_content)
                                
                                # Create style options dictionary
                                style_options = {
                                    'model': st.session_state.wp_edit_model,
                                    'temperature': st.session_state.wp_edit_temp,
                                    'tone': st.session_state.wp_edit_tone,
                                    'mood': st.session_state.wp_edit_mood,
                                    'audience': st.session_state.wp_edit_audience
                                }
                                
                                if st.session_state.wp_edit_guidance:
                                    style_options['custom_guidance'] = st.session_state.wp_edit_guidance
                                
                                # Generate revamped content
                                revamped_content = revamp_existing_blog(
                                    post_content=post_content,
                                    post_title=post_title,
                                    youtube_api=youtube_api,
                                    style_options=style_options
                                )
                                
                                # Update the saved post with the revamped content
                                post_data['processed_content'] = revamped_content
                                post_data['revamped_at'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                post_data['style_options'] = style_options
                                
                                # Save updated post data
                                with open(selected_post_path, 'w') as f:
                                    json.dump(post_data, f, indent=2, default=str)
                                
                                # Display the revamped content
                                st.session_state.wp_edit_revamped_content = revamped_content
                                
                                st.success("✅ Blog post successfully revamped!")
                                
                            except Exception as e:
                                st.error(f"Error revamping blog post: {str(e)}")
                                st.error(traceback.format_exc())
                    
                    # Display revamped content if available
                    if 'wp_edit_revamped_content' in st.session_state and st.session_state.wp_edit_revamped_content:
                        st.subheader("Revamped Content")
                        
                        # Show in expander
                        with st.expander("Revamped Content", expanded=True):
                            st.markdown(st.session_state.wp_edit_revamped_content, unsafe_allow_html=True)
                        
                        # Post to WordPress button
                        if st.button("🚀 Post to WordPress as Draft", key="wp_edit_post_button"):
                            with st.spinner("Creating draft post in WordPress..."):
                                try:
                                    # Post to WordPress as draft
                                    result = wordpress_api.create_post(
                                        title=post_title,
                                        content=st.session_state.wp_edit_revamped_content,
                                        status="draft"
                                    )
                                    
                                    if result.get('success'):
                                        post_id = result.get('post_id')
                                        post_url = result.get('post_url')
                                        edit_url = result.get('edit_url')
                                        
                                        st.success(f"✅ Draft post created successfully! ID: {post_id}")
                                        
                                        # Create markdown links to view/edit post
                                        st.markdown(f"[View Post]({post_url}) | [Edit on WordPress]({edit_url})")
                                    else:
                                        st.error(f"❌ Failed to create post: {result.get('error')}")
                                except Exception as e:
                                    st.error(f"❌ Error posting to WordPress: {str(e)}")
                except Exception as e:
                    st.error(f"Error loading post data: {str(e)}")

# This line has been removed
        
        # List all saved WordPress posts
        saved_posts = list_wordpress_posts()
        
        if not saved_posts:
            st.info("No saved WordPress posts found. Go to the WordPress Revamp tab to browse and save posts first.")
        else:
            # Create dropdown with post titles
            post_options = []
            post_display = {}
            
            for post in saved_posts:
                post_id = post.get('id', 'unknown')
                post_title = post.get('title', 'Untitled')
                if isinstance(post_title, dict) and 'rendered' in post_title:
                    post_title = post_title.get('rendered', 'Untitled')
                
                saved_at = post.get('saved_at', '')
                filepath = post.get('filepath', '')
                
                display_text = f"{post_title} (Saved: {saved_at})"
                post_options.append(filepath)
                post_display[filepath] = display_text
            
            selected_post_path = st.selectbox(
                "Select a saved post to edit:",
                options=post_options,
                format_func=lambda x: post_display.get(x, f"Post: {x}"),
                key="wordpress_edit_select_2"
            )
            
            # Load selected post
            if selected_post_path:
                try:
                    with open(selected_post_path, 'r') as f:
                        post_data = json.load(f)
                        
                    post_title = post_data.get('title', 'Untitled')
                    if isinstance(post_title, dict) and 'rendered' in post_title:
                        post_title = post_title.get('rendered', 'Untitled')
                    
                    post_id = post_data.get('id', 'unknown')
                    post_content = post_data.get('post_data', {}).get('content', '')
                    
                    # Handle content format (could be string or dict with rendered property)
                    if isinstance(post_content, dict) and 'rendered' in post_content:
                        post_content = post_content.get('rendered', '')
                    
                    st.write(f"### Editing: {post_title}")
                    st.write(f"**Post ID:** {post_id}")
                    
                    # Show original content in expander
                    with st.expander("Original Content", expanded=False):
                        st.markdown(post_content, unsafe_allow_html=True)
                    
                    # Initialize blog style options 
                    if 'wp_edit_model' not in st.session_state:
                        st.session_state.wp_edit_model = "gpt-4o"
                    if 'wp_edit_temp' not in st.session_state:
                        st.session_state.wp_edit_temp = 0.7
                    if 'wp_edit_tone' not in st.session_state:
                        st.session_state.wp_edit_tone = "Professional"
                    if 'wp_edit_mood' not in st.session_state:
                        st.session_state.wp_edit_mood = "Elegant"
                    if 'wp_edit_audience' not in st.session_state:
                        st.session_state.wp_edit_audience = "Modern Couples"
                    
                    # Style customization options
                    st.subheader("Blog Style Options")
                    
                    # Two columns for model options
                    col1, col2 = st.columns(2)
                    with col1:
                        model = st.selectbox(
                            "AI Model",
                            ["gpt-4o", "gpt-4.1", "gpt-4.1-mini"],
                            index=["gpt-4o", "gpt-4.1", "gpt-4.1-mini"].index(st.session_state.wp_edit_model),
                            key="wp_edit_model_select_2"
                        )
                        st.session_state.wp_edit_model = model
                    
                    with col2:
                        temp = st.slider(
                            "Creativity Level",
                            min_value=0.0,
                            max_value=1.0,
                            value=st.session_state.wp_edit_temp,
                            step=0.1,
                            key="wp_edit_temp_slider_2"
                        )
                        st.session_state.wp_edit_temp = temp
                    
                    # Two columns for style options
                    col1, col2 = st.columns(2)
                    
                    # Column 1: Tone
                    with col1:
                        tone_options = ["Professional", "Conversational", "Romantic", "Upbeat", "Elegant", "Custom"]
                        tone_index = 0
                        if st.session_state.wp_edit_tone in tone_options:
                            tone_index = tone_options.index(st.session_state.wp_edit_tone)
                        
                        tone = st.selectbox(
                            "Writing Tone",
                            tone_options,
                            index=tone_index,
                            key="wp_edit_tone_select"
                        )
                        
                        if tone == "Custom":
                            custom_tone = st.text_input(
                                "Custom tone",
                                value="" if st.session_state.wp_edit_tone not in tone_options else st.session_state.wp_edit_tone,
                                key="wp_edit_custom_tone_input"
                            )
                            st.session_state.wp_edit_tone = custom_tone if custom_tone else "Professional"
                        else:
                            st.session_state.wp_edit_tone = tone
                    
                    # Column 2: Mood
                    with col2:
                        mood_options = ["Elegant", "Fun", "Emotional", "Energetic", "Nostalgic", "Custom"]
                        mood_index = 0
                        if st.session_state.wp_edit_mood in mood_options:
                            mood_index = mood_options.index(st.session_state.wp_edit_mood)
                        
                        mood = st.selectbox(
                            "Overall Mood",
                            mood_options,
                            index=mood_index,
                            key="wp_edit_mood_select"
                        )
                        
                        if mood == "Custom":
                            custom_mood = st.text_input(
                                "Custom mood",
                                value="" if st.session_state.wp_edit_mood not in mood_options else st.session_state.wp_edit_mood,
                                key="wp_edit_custom_mood_input"
                            )
                            st.session_state.wp_edit_mood = custom_mood if custom_mood else "Elegant"
                        else:
                            st.session_state.wp_edit_mood = mood
                    
                    # Audience selection
                    audience_options = ["Modern Couples", "Traditional Couples", "Brides", "Grooms", "All Couples", "Custom"]
                    audience_index = 0
                    if st.session_state.wp_edit_audience in audience_options:
                        audience_index = audience_options.index(st.session_state.wp_edit_audience)
                    
                    audience = st.selectbox(
                        "Target Audience",
                        audience_options,
                        index=audience_index,
                        key="wp_edit_audience_select"
                    )
                    
                    if audience == "Custom":
                        custom_audience = st.text_input(
                            "Custom audience",
                            value="" if st.session_state.wp_edit_audience not in audience_options else st.session_state.wp_edit_audience,
                            key="wp_edit_custom_audience_input"
                        )
                        st.session_state.wp_edit_audience = custom_audience if custom_audience else "Modern Couples"
                    else:
                        st.session_state.wp_edit_audience = audience
                    
                    # Additional guidance
                    if 'wp_edit_guidance' not in st.session_state:
                        st.session_state.wp_edit_guidance = ""
                    
                    guidance = st.text_area(
                        "Additional Style Guidance (Optional)",
                        value=st.session_state.wp_edit_guidance,
                        placeholder="Add any specific style instructions or requirements for the revamped blog post",
                        height=100,
                        key="wp_edit_guidance_input"
                    )
                    st.session_state.wp_edit_guidance = guidance
                    
                    # Revamp button
                    if st.button("✨ Revamp Blog Post", key="wp_edit_revamp_button"):
                        with st.spinner("Revamping blog post content..."):
                            try:
                                # Import necessary functions
                                from utils.openai_api import revamp_existing_blog, extract_spotify_link
                                
                                # Extract Spotify link if available
                                spotify_link = extract_spotify_link(post_content)
                                
                                # Create style options dictionary
                                style_options = {
                                    'model': st.session_state.wp_edit_model,
                                    'temperature': st.session_state.wp_edit_temp,
                                    'tone': st.session_state.wp_edit_tone,
                                    'mood': st.session_state.wp_edit_mood,
                                    'audience': st.session_state.wp_edit_audience
                                }
                                
                                if st.session_state.wp_edit_guidance:
                                    style_options['custom_guidance'] = st.session_state.wp_edit_guidance
                                
                                # Generate revamped content
                                revamped_content = revamp_existing_blog(
                                    post_content=post_content,
                                    post_title=post_title,
                                    youtube_api=youtube_api,
                                    style_options=style_options
                                )
                                
                                # Update the saved post with the revamped content
                                post_data['processed_content'] = revamped_content
                                post_data['revamped_at'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                post_data['style_options'] = style_options
                                
                                # Save updated post data
                                with open(selected_post_path, 'w') as f:
                                    json.dump(post_data, f, indent=2, default=str)
                                
                                # Display the revamped content
                                st.session_state.wp_edit_revamped_content = revamped_content
                                
                                st.success("✅ Blog post successfully revamped!")
                                
                            except Exception as e:
                                st.error(f"Error revamping blog post: {str(e)}")
                                st.error(traceback.format_exc())
                    
                    # Display revamped content if available
                    if 'wp_edit_revamped_content' in st.session_state and st.session_state.wp_edit_revamped_content:
                        st.subheader("Revamped Content")
                        
                        # Show in expander
                        with st.expander("Revamped Content", expanded=True):
                            st.markdown(st.session_state.wp_edit_revamped_content, unsafe_allow_html=True)
                        
                        # Post to WordPress button
                        if st.button("🚀 Post to WordPress as Draft", key="wp_edit_post_button"):
                            with st.spinner("Creating draft post in WordPress..."):
                                try:
                                    # Post to WordPress as draft
                                    result = wordpress_api.create_post(
                                        title=post_title,
                                        content=st.session_state.wp_edit_revamped_content,
                                        status="draft"
                                    )
                                    
                                    if result.get('success'):
                                        post_id = result.get('post_id')
                                        post_url = result.get('post_url')
                                        edit_url = result.get('edit_url')
                                        
                                        st.success(f"✅ Draft post created successfully! ID: {post_id}")
                                        
                                        # Create markdown links to view/edit post
                                        st.markdown(f"[View Post]({post_url}) | [Edit on WordPress]({edit_url})")
                                    else:
                                        st.error(f"❌ Failed to create post: {result.get('error')}")
                                except Exception as e:
                                    st.error(f"❌ Error posting to WordPress: {str(e)}")
                except Exception as e:
                    st.error(f"Error loading post data: {str(e)}")

    # Tab 5: WordPress Edit
    with tab5:
        st.subheader("Edit Saved WordPress Posts")
        
        # Ensure wordpress_posts directory exists
        os.makedirs("wordpress_posts", exist_ok=True)
        
        # List all saved WordPress posts
        saved_posts = list_wordpress_posts()
        
        if not saved_posts:
            st.info("No saved WordPress posts found. Go to the WordPress Revamp tab, select a post, and click 'Save for Editing' first.")
            
            # Add a button to go to WordPress Revamp tab
            if st.button("Go to WordPress Revamp", key="go_to_revamp_button"):
                st.session_state.active_tab = "WordPress Revamp"
                # Note: This won't work directly in Streamlit, but provides a visual cue
        else:
            # Create dropdown with post titles
            post_options = []
            post_display = {}
            
            for post in saved_posts:
                post_id = post.get('id', 'unknown')
                post_title = post.get('title', 'Untitled')
                if isinstance(post_title, dict) and 'rendered' in post_title:
                    post_title = post_title.get('rendered', 'Untitled')
                
                saved_at = post.get('saved_at', '')
                filepath = post.get('filepath', '')
                
                display_text = f"{post_title} (Saved: {saved_at})"
                post_options.append(filepath)
                post_display[filepath] = display_text
            
            selected_post_path = st.selectbox(
                "Select a saved post to edit:",
                options=post_options,
                format_func=lambda x: post_display.get(x, f"Post: {x}"),
                key="wordpress_edit_select_3"
            )
            
            # Load selected post
            if selected_post_path:
                try:
                    with open(selected_post_path, 'r') as f:
                        post_data = json.load(f)
                        
                    post_title = post_data.get('title', 'Untitled')
                    if isinstance(post_title, dict) and 'rendered' in post_title:
                        post_title = post_title.get('rendered', 'Untitled')
                    
                    post_id = post_data.get('id', 'unknown')
                    post_content = post_data.get('post_data', {}).get('content', '')
                    
                    # Handle content format (could be string or dict with rendered property)
                    if isinstance(post_content, dict) and 'rendered' in post_content:
                        post_content = post_content.get('rendered', '')
                    
                    st.write(f"### Editing: {post_title}")
                    st.write(f"**Post ID:** {post_id}")
                    
                    # Show original content in expander
                    with st.expander("Original Content", expanded=False):
                        st.markdown(post_content, unsafe_allow_html=True)
                    
                    # Initialize blog style options 
                    if 'wp_edit_model' not in st.session_state:
                        st.session_state.wp_edit_model = "gpt-4o"
                    if 'wp_edit_temp' not in st.session_state:
                        st.session_state.wp_edit_temp = 0.7
                    if 'wp_edit_tone' not in st.session_state:
                        st.session_state.wp_edit_tone = "Professional"
                    if 'wp_edit_mood' not in st.session_state:
                        st.session_state.wp_edit_mood = "Elegant"
                    if 'wp_edit_audience' not in st.session_state:
                        st.session_state.wp_edit_audience = "Modern Couples"
                    
                    # Style customization options
                    st.subheader("Blog Style Options")
                    
                    # Two columns for model options
                    col1, col2 = st.columns(2)
                    with col1:
                        model = st.selectbox(
                            "AI Model",
                            ["gpt-4o", "gpt-4.1", "gpt-4.1-mini"],
                            index=["gpt-4o", "gpt-4.1", "gpt-4.1-mini"].index(st.session_state.wp_edit_model),
                            key="wp_edit_model_select_3"
                        )
                        st.session_state.wp_edit_model = model
                    
                    with col2:
                        temp = st.slider(
                            "Creativity Level",
                            min_value=0.0,
                            max_value=1.0,
                            value=st.session_state.wp_edit_temp,
                            step=0.1,
                            key="wp_edit_temp_slider_3"
                        )
                        st.session_state.wp_edit_temp = temp
                    
                    # Two columns for style options
                    col1, col2 = st.columns(2)
                    
                    # Column 1: Tone
                    with col1:
                        tone_options = ["Professional", "Conversational", "Romantic", "Upbeat", "Elegant", "Custom"]
                        tone_index = 0
                        if st.session_state.wp_edit_tone in tone_options:
                            tone_index = tone_options.index(st.session_state.wp_edit_tone)
                        
                        tone = st.selectbox(
                            "Writing Tone",
                            tone_options,
                            index=tone_index,
                            key="wp_edit_tone_select"
                        )
                        
                        if tone == "Custom":
                            custom_tone = st.text_input(
                                "Custom tone",
                                value="" if st.session_state.wp_edit_tone not in tone_options else st.session_state.wp_edit_tone,
                                key="wp_edit_custom_tone_input"
                            )
                            st.session_state.wp_edit_tone = custom_tone if custom_tone else "Professional"
                        else:
                            st.session_state.wp_edit_tone = tone
                    
                    # Column 2: Mood
                    with col2:
                        mood_options = ["Elegant", "Fun", "Emotional", "Energetic", "Nostalgic", "Custom"]
                        mood_index = 0
                        if st.session_state.wp_edit_mood in mood_options:
                            mood_index = mood_options.index(st.session_state.wp_edit_mood)
                        
                        mood = st.selectbox(
                            "Overall Mood",
                            mood_options,
                            index=mood_index,
                            key="wp_edit_mood_select"
                        )
                        
                        if mood == "Custom":
                            custom_mood = st.text_input(
                                "Custom mood",
                                value="" if st.session_state.wp_edit_mood not in mood_options else st.session_state.wp_edit_mood,
                                key="wp_edit_custom_mood_input"
                            )
                            st.session_state.wp_edit_mood = custom_mood if custom_mood else "Elegant"
                        else:
                            st.session_state.wp_edit_mood = mood
                    
                    # Audience selection
                    audience_options = ["Modern Couples", "Traditional Couples", "Brides", "Grooms", "All Couples", "Custom"]
                    audience_index = 0
                    if st.session_state.wp_edit_audience in audience_options:
                        audience_index = audience_options.index(st.session_state.wp_edit_audience)
                    
                    audience = st.selectbox(
                        "Target Audience",
                        audience_options,
                        index=audience_index,
                        key="wp_edit_audience_select"
                    )
                    
                    if audience == "Custom":
                        custom_audience = st.text_input(
                            "Custom audience",
                            value="" if st.session_state.wp_edit_audience not in audience_options else st.session_state.wp_edit_audience,
                            key="wp_edit_custom_audience_input"
                        )
                        st.session_state.wp_edit_audience = custom_audience if custom_audience else "Modern Couples"
                    else:
                        st.session_state.wp_edit_audience = audience
                    
                    # Additional guidance
                    if 'wp_edit_guidance' not in st.session_state:
                        st.session_state.wp_edit_guidance = ""
                    
                    guidance = st.text_area(
                        "Additional Style Guidance (Optional)",
                        value=st.session_state.wp_edit_guidance,
                        placeholder="Add any specific style instructions or requirements for the revamped blog post",
                        height=100,
                        key="wp_edit_guidance_input"
                    )
                    st.session_state.wp_edit_guidance = guidance
                    
                    # Revamp button
                    if st.button("✨ Revamp Blog Post", key="wp_edit_revamp_button"):
                        with st.spinner("Revamping blog post content..."):
                            try:
                                # Import necessary functions
                                from utils.openai_api import revamp_existing_blog, extract_spotify_link
                                
                                # Extract Spotify link if available
                                spotify_link = extract_spotify_link(post_content)
                                
                                # Create style options dictionary
                                style_options = {
                                    'model': st.session_state.wp_edit_model,
                                    'temperature': st.session_state.wp_edit_temp,
                                    'tone': st.session_state.wp_edit_tone,
                                    'mood': st.session_state.wp_edit_mood,
                                    'audience': st.session_state.wp_edit_audience
                                }
                                
                                if st.session_state.wp_edit_guidance:
                                    style_options['custom_guidance'] = st.session_state.wp_edit_guidance
                                
                                # Generate revamped content
                                revamped_content = revamp_existing_blog(
                                    post_content=post_content,
                                    post_title=post_title,
                                    youtube_api=youtube_api,
                                    style_options=style_options
                                )
                                
                                # Update the saved post with the revamped content
                                post_data['processed_content'] = revamped_content
                                post_data['revamped_at'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                post_data['style_options'] = style_options
                                
                                # Save updated post data
                                with open(selected_post_path, 'w') as f:
                                    json.dump(post_data, f, indent=2, default=str)
                                
                                # Display the revamped content
                                st.session_state.wp_edit_revamped_content = revamped_content
                                
                                st.success("✅ Blog post successfully revamped!")
                                
                            except Exception as e:
                                st.error(f"Error revamping blog post: {str(e)}")
                                st.error(traceback.format_exc())
                    
                    # Display revamped content if available
                    if 'wp_edit_revamped_content' in st.session_state and st.session_state.wp_edit_revamped_content:
                        st.subheader("Revamped Content")
                        
                        # Show in expander
                        with st.expander("Revamped Content", expanded=True):
                            st.markdown(st.session_state.wp_edit_revamped_content, unsafe_allow_html=True)
                        
                        # Post to WordPress button
                        if st.button("🚀 Post to WordPress as Draft", key="wp_edit_post_button"):
                            with st.spinner("Creating draft post in WordPress..."):
                                try:
                                    # Post to WordPress as draft
                                    result = wordpress_api.create_post(
                                        title=post_title,
                                        content=st.session_state.wp_edit_revamped_content,
                                        status="draft"
                                    )
                                    
                                    if result.get('success'):
                                        post_id = result.get('post_id')
                                        post_url = result.get('post_url')
                                        edit_url = result.get('edit_url')
                                        
                                        st.success(f"✅ Draft post created successfully! ID: {post_id}")
                                        
                                        # Create markdown links to view/edit post
                                        st.markdown(f"[View Post]({post_url}) | [Edit on WordPress]({edit_url})")
                                    else:
                                        st.error(f"❌ Failed to create post: {result.get('error')}")
                                except Exception as e:
                                    st.error(f"❌ Error posting to WordPress: {str(e)}")
                except Exception as e:
                    st.error(f"Error loading post data: {str(e)}")


if __name__ == "__main__":
    import re  # Import at the top
    print("Starting application")
    try:
        main()
        print("Main function completed successfully")
    except Exception as e:
        print(f"Error in main function: {str(e)}")
        traceback.print_exc()