import streamlit as st
import pandas as pd
import os
import json
from datetime import datetime
import traceback
from utils.fixed_youtube_api import YouTubeAPI
from utils.spotify_api import SpotifyAPI
from utils.openai_api import generate_blog_post, revamp_existing_blog, extract_songs_from_html, extract_spotify_link
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
    
# WordPress revamp session state
if 'selected_post' not in st.session_state:
    st.session_state.selected_post = None
if 'wordpress_posts' not in st.session_state:
    st.session_state.wordpress_posts = None
if 'revamp_tone' not in st.session_state:
    st.session_state.revamp_tone = "Professional"
if 'revamp_section_count' not in st.session_state:
    st.session_state.revamp_section_count = "Default (3-4)"
if 'revamp_mood' not in st.session_state:
    st.session_state.revamp_mood = "Elegant"
if 'revamp_intro_theme' not in st.session_state:
    st.session_state.revamp_intro_theme = "Standard Welcome"
if 'revamp_conclusion_theme' not in st.session_state:
    st.session_state.revamp_conclusion_theme = "Invitation to Connect"
if 'revamp_title_style' not in st.session_state:
    st.session_state.revamp_title_style = "Descriptive"
if 'revamp_audience' not in st.session_state:
    st.session_state.revamp_audience = "Couples"
    
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
                
                # Generate the blog post with style options if provided
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
    tab1, tab2, tab3, tab4 = st.tabs(["Process Playlists", "Edit CSV Data", "Saved Blog Posts", "Revamp WordPress Posts"])
    
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

if __name__ == "__main__":
    import re  # Import at the top
    print("Starting application")
    try:
        main()
        print("Main function completed successfully")
    except Exception as e:
        print(f"Error in main function: {str(e)}")
        traceback.print_exc()