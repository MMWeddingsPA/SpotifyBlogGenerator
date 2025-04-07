import streamlit as st
import pandas as pd
from utils.youtube_api import YouTubeAPI
from utils.spotify_api import SpotifyAPI
from utils.openai_api import generate_blog_post
from utils.wordpress_api import WordPressAPI
from utils.csv_handler import load_csv, save_csv
import os
import json
from datetime import datetime

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

    /* Global styles and background */
    .main {
        background-color: #FFFFFF;
        background-image: 
            linear-gradient(rgba(255, 255, 255, 0.95), rgba(255, 255, 255, 0.95)),
            url("https://mmweddingspa.com/wp-content/uploads/2020/01/cropped-MM-Icon.webp");
        background-size: 400px;
        background-repeat: repeat;
        background-position: center;
        background-attachment: fixed;
    }
    
    /* Main text and headers */
    .stMarkdown, .stText, p, div {
        font-family: 'Lato', sans-serif;
        color: #1A2A44;
    }

    /* Page divider */
    hr {
        border: 0;
        height: 1px;
        background-image: linear-gradient(to right, rgba(212, 175, 55, 0), rgba(212, 175, 55, 0.75), rgba(212, 175, 55, 0));
        margin: 1.5rem 0;
    }

    /* Headings */
    h1, h2, h3 {
        font-family: 'Playfair Display', serif;
        color: #1A2A44;
        letter-spacing: 0.02em;
    }

    h1 {
        font-weight: 700;
        padding-bottom: 1.5rem;
        font-size: 2.8rem;
        background: linear-gradient(45deg, #D4AF37, #C19B20);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.1);
        margin-top: 0.5rem;
    }
    
    h2 {
        font-size: 2rem;
        margin-bottom: 1rem;
        color: #1A2A44;
    }
    
    h3 {
        font-size: 1.5rem;
        font-weight: 500;
        margin-top: 1.5rem;
        margin-bottom: 0.75rem;
    }

    /* Buttons and interactive elements */
    .stButton button {
        background-color: #D4AF37;
        color: #1A2A44;
        border-radius: 30px;
        padding: 0.75rem 1.8rem;
        border: none;
        font-weight: 500;
        font-family: 'Lato', sans-serif;
        transition: all 0.3s ease;
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        font-size: 1rem;
        letter-spacing: 0.5px;
        text-transform: uppercase;
    }

    .stButton button:hover {
        background-color: #C19B20;
        transform: translateY(-2px);
        box-shadow: 0 6px 12px rgba(0,0,0,0.15);
    }

    /* File uploader */
    .uploadedFile {
        border: 2px dashed #D4AF37;
        border-radius: 12px;
        padding: 1.5rem;
        background-color: rgba(212, 175, 55, 0.05);
        transition: all 0.3s ease;
    }
    
    .uploadedFile:hover {
        border-color: #C19B20;
        background-color: rgba(212, 175, 55, 0.08);
    }

    /* Cards and expandable sections */
    .stExpander {
        background-color: white;
        border-radius: 12px;
        box-shadow: 0 8px 20px rgba(0,0,0,0.08);
        border: 1px solid rgba(245, 198, 203, 0.3);
        transition: all 0.3s ease;
        margin: 1rem 0;
    }

    .stExpander:hover {
        transform: translateY(-3px);
        box-shadow: 0 12px 24px rgba(0,0,0,0.12);
    }
    
    /* Container styling */
    [data-testid="stVerticalBlock"] {
        padding: 0 1rem;
    }

    /* Progress bars */
    .stProgress > div > div {
        background-color: #D4AF37;
        background: linear-gradient(45deg, #D4AF37, #C19B20);
        border-radius: 30px;
        height: 10px !important;
    }
    
    .stProgress {
        height: 10px !important;
    }

    /* Success messages */
    .stSuccess {
        background-color: rgba(212, 175, 55, 0.1);
        border-color: #D4AF37;
        color: #1A2A44;
        border-radius: 12px;
        padding: 1rem;
        font-weight: 500;
    }

    /* Warning messages */
    .stWarning {
        background-color: rgba(245, 198, 203, 0.1);
        border-color: #F5C6CB;
        border-radius: 12px;
        padding: 1rem;
    }
    
    /* Error messages */
    .stError {
        background-color: rgba(245, 198, 203, 0.2);
        border-color: #F5C6CB;
        color: #721c24;
        border-radius: 12px;
        padding: 1rem;
    }
    
    /* Data tables */
    .stDataFrame {
        border: 1px solid rgba(212, 175, 55, 0.3);
        border-radius: 12px;
        overflow: hidden;
    }
    
    [data-testid="stDataFrameResizable"] {
        border-radius: 12px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.05);
    }
    
    /* Checkbox styling */
    [data-testid="stCheckbox"] {
        opacity: 0.9;
        transition: all 0.2s ease;
    }
    
    [data-testid="stCheckbox"]:hover {
        opacity: 1;
        transform: scale(1.02);
    }
    
    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background-color: #1A2A44;
        border-right: 1px solid rgba(212, 175, 55, 0.3);
        padding-top: 2rem;
    }
    
    [data-testid="stSidebar"] [data-testid="stVerticalBlock"] {
        padding: 0.5rem;
    }
    
    [data-testid="stSidebar"] h1, 
    [data-testid="stSidebar"] h2, 
    [data-testid="stSidebar"] h3, 
    [data-testid="stSidebar"] .stMarkdown p {
        color: #FFFFFF !important;
    }
    
    [data-testid="stSidebar"] h1 {
        background: linear-gradient(45deg, #D4AF37, #F5C6CB);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    
    /* Text areas and input fields */
    .stTextArea textarea, .stTextInput input {
        border-radius: 8px;
        border: 1px solid rgba(212, 175, 55, 0.3);
        padding: 1rem;
        font-family: 'Lato', sans-serif;
        transition: all 0.3s ease;
    }
    
    .stTextArea textarea:focus, .stTextInput input:focus {
        border-color: #D4AF37;
        box-shadow: 0 0 0 2px rgba(212, 175, 55, 0.2);
    }
    
    /* Multiselect */
    .stMultiSelect {
        border-radius: 8px;
    }
    
    /* Text area for blog post */
    [data-baseweb="textarea"] {
        font-family: 'Lato', sans-serif !important;
        line-height: 1.6 !important;
    }
</style>
""", unsafe_allow_html=True)

# Add elegant header with logo
st.markdown("""
<div style="display: flex; align-items: center; padding: 1.5rem 0; margin-bottom: 2rem; border-bottom: 1px solid rgba(212, 175, 55, 0.3);">
    <img src="https://mmweddingspa.com/wp-content/uploads/2020/01/cropped-MM-Icon.webp" style="width: 120px; margin-right: 2rem; filter: drop-shadow(0 4px 8px rgba(0,0,0,0.15));">
    <div>
        <h1 style="margin-bottom: 0.2rem; margin-top: 0;">Moments & Memories</h1>
        <p style="font-family: 'Playfair Display', serif; font-size: 1.5rem; color: #1A2A44; margin-bottom: 0; font-weight: 400; font-style: italic; letter-spacing: 0.05em;">
            Blog Generator
        </p>
        <p style="font-family: 'Lato', sans-serif; font-size: 1rem; color: #1A2A44; margin-top: 0.5rem; opacity: 0.8;">
            Creating Moments & Memories, One Wedding at a Time
        </p>
    </div>
</div>
""", unsafe_allow_html=True)

# Initialize session state
if 'df' not in st.session_state:
    st.session_state.df = None
if 'last_saved_csv' not in st.session_state:
    st.session_state.last_saved_csv = None
    
# Check for previously saved CSV files at startup
def find_latest_csv():
    """Find the most recently modified CSV file from previous sessions"""
    import glob
    import os
    from datetime import datetime
    
    # Look for processed CSV files
    csv_files = glob.glob("processed_playlists_*.csv")
    
    if not csv_files:
        return None
    
    # Get file with the latest modification time
    latest_file = max(csv_files, key=os.path.getmtime)
    return latest_file

# Auto-load the latest CSV if available and we don't already have data
if 'auto_loaded' not in st.session_state:
    st.session_state.auto_loaded = False

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

def save_processed_csv(df, operation_type):
    """Save CSV with timestamp and operation type"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"processed_playlists_{operation_type}_{timestamp}.csv"
    save_csv(df, filename)
    st.session_state.last_saved_csv = filename
    return filename

def process_playlist(playlist, youtube_api, spotify_api, operations):
    """Process a single playlist with error handling and progress tracking"""
    try:
        # Filter dataset for selected playlist
        playlist_df = st.session_state.df[
            st.session_state.df['Playlist'] == playlist
        ].copy()

        results = {}

        # Fetch YouTube links if selected
        if "YouTube" in operations:
            with st.spinner("🎵 Fetching YouTube links..."):
                songs_to_process = playlist_df[
                    (playlist_df['YouTube_Link'].isna()) | 
                    (playlist_df['YouTube_Link'] == '')
                ]

                total_songs = len(songs_to_process)
                if total_songs > 0:
                    progress_bar = st.progress(0)
                    for idx, row in enumerate(songs_to_process.itertuples(), 1):
                        search_query = f"{row.Song} {row.Artist}"
                        youtube_link = youtube_api.get_video_link(search_query)
                        playlist_df.at[row.Index, 'YouTube_Link'] = youtube_link
                        progress = min(1.0, idx / total_songs)
                        progress_bar.progress(progress)

                    st.session_state.df.update(playlist_df)
                    filename = save_processed_csv(st.session_state.df, "youtube")
                    results['youtube_file'] = filename

        # Fetch Spotify playlist if selected
        if "Spotify" in operations:
            with st.spinner("🎧 Fetching Spotify playlist link..."):
                spotify_link = spotify_api.get_playlist_link(
                    "bm8eje5tcjj9eazftizqoikwm",
                    playlist
                )
                results['spotify_link'] = spotify_link

        # Generate blog post if selected
        if "Blog" in operations:
            with st.spinner("✍️ Generating blog post..."):
                blog_post = generate_blog_post(
                    playlist_name=playlist,
                    songs_df=playlist_df,
                    spotify_link=results.get('spotify_link')
                )
                results['blog_post'] = blog_post

        return True, results

    except Exception as e:
        return False, str(e)

def main():
    # Initialize API clients
    youtube_api = YouTubeAPI(os.getenv("YOUTUBE_API_KEY"))
    spotify_api = SpotifyAPI(
        os.getenv("SPOTIFY_CLIENT_ID"),
        os.getenv("SPOTIFY_CLIENT_SECRET")
    )
    
    # Initialize WordPress API with error handling
    wordpress_api = None
    try:
        # Check if WordPress credentials are available
        if all([
            os.getenv("WORDPRESS_API_URL"),
            os.getenv("WORDPRESS_USERNAME"),
            os.getenv("WORDPRESS_PASSWORD")
        ]):
            wordpress_api = WordPressAPI(
                os.getenv("WORDPRESS_API_URL"),
                os.getenv("WORDPRESS_USERNAME"),
                os.getenv("WORDPRESS_PASSWORD")
            )
    except Exception as e:
        st.sidebar.warning(f"⚠️ WordPress API initialization failed: {str(e)}")
    
    # Display auto-load notification if needed
    if st.session_state.auto_loaded and st.session_state.last_saved_csv:
        st.markdown(f"""
        <div style="margin-bottom: 1.5rem; padding: 1rem; background-color: rgba(212, 175, 55, 0.1); 
            border-radius: 12px; border-left: 4px solid #D4AF37; display: flex; align-items: center;">
            <span style="font-size: 1.5rem; margin-right: 1rem;">🔄</span>
            <div>
                <p style="margin: 0; color: #1A2A44; font-weight: 500;">
                    Previous work automatically restored from last session
                </p>
                <p style="margin: 0.2rem 0 0 0; font-size: 0.9rem; color: #666; opacity: 0.8;">
                    Loaded file: {st.session_state.last_saved_csv}
                </p>
            </div>
        </div>
        """, unsafe_allow_html=True)
        # Reset the flag so notification only shows once
        st.session_state.auto_loaded = False

    # Left sidebar for file operations
    with st.sidebar:
        st.header("📁 File Operations")

        # File upload section with styling
        uploaded_file = st.file_uploader(
            "Upload New CSV",
            type="csv",
            help="Upload a CSV file containing your playlists"
        )

        # CSV Format Instructions
        with st.expander("📝 CSV Format Guide", expanded=False):
            st.markdown("""
            ### Required Format:
            - Each playlist starts with 'Wedding Cocktail Hour'
            - Include Song Title and Artist
            - Optional: YouTube links

            ### Example:
            ```
            001 The Classic Wedding Cocktail Hour
            Song1-Artist1,Song1,Artist1,youtube_link1
            Song2-Artist2,Song2,Artist2,youtube_link2
            ```
            """)

        # Load previous CSV if available
        if st.session_state.last_saved_csv and os.path.exists(st.session_state.last_saved_csv):
            if st.button("📂 Load Last Saved CSV"):
                try:
                    st.session_state.df = load_csv(st.session_state.last_saved_csv)
                    st.success(f"✅ Loaded {st.session_state.last_saved_csv}")
                except Exception as e:
                    st.error(f"❌ Error loading saved CSV: {str(e)}")

    # Main content area
    if uploaded_file is not None:
        try:
            st.session_state.df = load_csv(uploaded_file)
            st.success("✅ CSV file loaded successfully!")

            total_playlists = st.session_state.df['Playlist'].nunique()
            total_songs = len(st.session_state.df)

            # Stats cards with enhanced styling
            st.markdown("""
            <div style="display: flex; gap: 1.5rem; margin-bottom: 2rem; flex-wrap: wrap;">
            """, unsafe_allow_html=True)
            
            # Playlist card
            st.markdown(f"""
            <div style="flex: 1; min-width: 200px; background: linear-gradient(135deg, #FFFFFF 0%, #F9F9F9 100%); 
                padding: 1.5rem; border-radius: 12px; box-shadow: 0 10px 20px rgba(26, 42, 68, 0.07); 
                border-left: 5px solid #D4AF37; transition: all 0.3s ease;">
                <div style="display: flex; align-items: center; margin-bottom: 0.7rem;">
                    <span style="background-color: rgba(212, 175, 55, 0.15); padding: 0.5rem; border-radius: 50%; margin-right: 0.8rem;">
                        <span style="font-size: 1.2rem;">📊</span>
                    </span>
                    <h3 style="margin: 0; color: #1A2A44; font-family: 'Playfair Display', serif; font-weight: 600;">Playlists</h3>
                </div>
                <p style="font-size: 2.5rem; margin: 0.5rem 0 0 0; color: #1A2A44; font-weight: 600;">{total_playlists}</p>
                <p style="margin: 0.2rem 0 0 0; font-size: 0.9rem; color: #666; opacity: 0.8;">Ready to process</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Songs card
            st.markdown(f"""
            <div style="flex: 1; min-width: 200px; background: linear-gradient(135deg, #FFFFFF 0%, #F9F9F9 100%); 
                padding: 1.5rem; border-radius: 12px; box-shadow: 0 10px 20px rgba(26, 42, 68, 0.07); 
                border-left: 5px solid #F5C6CB; transition: all 0.3s ease;">
                <div style="display: flex; align-items: center; margin-bottom: 0.7rem;">
                    <span style="background-color: rgba(245, 198, 203, 0.15); padding: 0.5rem; border-radius: 50%; margin-right: 0.8rem;">
                        <span style="font-size: 1.2rem;">🎵</span>
                    </span>
                    <h3 style="margin: 0; color: #1A2A44; font-family: 'Playfair Display', serif; font-weight: 600;">Songs</h3>
                </div>
                <p style="font-size: 2.5rem; margin: 0.5rem 0 0 0; color: #1A2A44; font-weight: 600;">{total_songs}</p>
                <p style="margin: 0.2rem 0 0 0; font-size: 0.9rem; color: #666; opacity: 0.8;">Total songs across all playlists</p>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("""</div>""", unsafe_allow_html=True)

        except Exception as e:
            st.error(f"❌ Error loading CSV: {str(e)}")
            return

    if st.session_state.df is not None:
        st.markdown("---")
        st.header("🎵 Available Playlists")
        playlists = st.session_state.df['Playlist'].unique()

        # Elegant playlist selection section
        st.markdown("""
        <div style="background: linear-gradient(135deg, rgba(212, 175, 55, 0.05) 0%, rgba(245, 198, 203, 0.05) 100%); 
            padding: 2rem; border-radius: 12px; margin-bottom: 2rem; 
            border: 1px solid rgba(212, 175, 55, 0.2); box-shadow: 0 10px 30px rgba(0,0,0,0.03);">
            <h3 style="margin-top: 0; font-family: 'Playfair Display', serif; color: #1A2A44; 
                border-bottom: 2px solid rgba(212, 175, 55, 0.3); padding-bottom: 0.8rem; margin-bottom: 1.5rem;">
                Select Playlists & Operations
            </h3>
        """, unsafe_allow_html=True)
        
        # Create columns for playlist selection and operations
        col1, col2 = st.columns([2, 1])

        with col1:
            st.markdown("""
            <p style="font-weight: 500; margin-bottom: 0.5rem; color: #1A2A44;">
                <span style="background-color: rgba(212, 175, 55, 0.15); padding: 0.3rem 0.5rem; border-radius: 4px; margin-right: 0.5rem;">
                    🎵
                </span>
                Select playlists to process:
            </p>
            """, unsafe_allow_html=True)
            
            selected_playlists = st.multiselect(
                "",
                playlists,
                format_func=lambda x: x.split("Wedding Cocktail Hour")[0].strip()
            )

        with col2:
            st.markdown("""
            <p style="font-weight: 500; margin-bottom: 0.5rem; color: #1A2A44;">
                <span style="background-color: rgba(212, 175, 55, 0.15); padding: 0.3rem 0.5rem; border-radius: 4px; margin-right: 0.5rem;">
                    ⚙️
                </span>
                Operations:
            </p>
            """, unsafe_allow_html=True)
            
            fetch_youtube = st.checkbox("🎥 Fetch YouTube Links", value=True)
            fetch_spotify = st.checkbox("🎧 Fetch Spotify Playlist", value=True)
            generate_blog = st.checkbox("✍️ Generate Blog Post", value=True)
        
        st.markdown("</div>", unsafe_allow_html=True)
        
        # Action buttons container
        if selected_playlists:
            st.markdown("""
            <div style="display: flex; gap: 1rem; margin-bottom: 2rem; flex-wrap: wrap;">
            """, unsafe_allow_html=True)
            
            # Preview button
            col1, col2 = st.columns([1, 1])
            with col1:
                preview_button = st.button("👁️ Preview Selected Playlists", use_container_width=True)
            
            # Process button
            with col2:
                process_button = st.button("🚀 Process Selected Playlists", use_container_width=True)
            
            st.markdown("</div>", unsafe_allow_html=True)
            
            # Preview section
            if preview_button:
                for playlist in selected_playlists:
                    clean_name = playlist.split('Wedding Cocktail Hour')[0].strip()
                    with st.expander(f"Preview: {clean_name}", expanded=True):
                        st.markdown(f"""
                        <p style="color: #1A2A44; font-family: 'Playfair Display', serif; 
                        font-size: 1.2rem; font-style: italic; margin-bottom: 1rem;">
                        Showing songs from <span style="color: #D4AF37; font-weight: 500;">{clean_name}</span>
                        </p>
                        """, unsafe_allow_html=True)
                        
                        playlist_df = st.session_state.df[st.session_state.df['Playlist'] == playlist]
                        st.dataframe(
                            playlist_df[['Song', 'Artist', 'YouTube_Link']],
                            hide_index=True,
                            use_container_width=True
                        )

            # Process section
            if process_button:
                operations = []
                if fetch_youtube: operations.append("YouTube")
                if fetch_spotify: operations.append("Spotify")
                if generate_blog: operations.append("Blog")

                if not operations:
                    st.warning("⚠️ Please select at least one operation to perform.")
                    return
                    
                # Display selected operations
                ops_text = ", ".join([f"{op}" for op in operations])
                st.markdown(f"""
                <div style="margin-bottom: 1.5rem; padding: 1rem; background-color: rgba(212, 175, 55, 0.08); 
                    border-radius: 8px; border-left: 4px solid #D4AF37;">
                    <p style="margin: 0; color: #1A2A44; font-weight: 500;">
                        <span style="color: #D4AF37; margin-right: 0.5rem;">⚙️</span>
                        Processing operations: {ops_text}
                    </p>
                </div>
                """, unsafe_allow_html=True)

                # Process each playlist
                for playlist in selected_playlists:
                    clean_name = playlist.split('Wedding Cocktail Hour')[0].strip()
                    with st.expander(f"Processing: {clean_name}", expanded=True):
                        success, results = process_playlist(playlist, youtube_api, spotify_api, operations)

                        if success:
                            # Create a more attractive results display
                            st.markdown("""
                            <div style="margin-top: 1rem; margin-bottom: 1rem;">
                            """, unsafe_allow_html=True)
                            
                            if 'youtube_file' in results:
                                st.success(f"✅ YouTube links updated and saved to {results['youtube_file']}")
                                
                            if 'spotify_link' in results:
                                st.markdown(f"""
                                <div style="margin: 1rem 0; padding: 1rem; background-color: rgba(245, 198, 203, 0.1); 
                                    border-radius: 8px; border: 1px solid rgba(245, 198, 203, 0.3);">
                                    <p style="margin: 0; display: flex; align-items: center;">
                                        <span style="font-size: 1.5rem; margin-right: 1rem;">🎧</span>
                                        <span>
                                            <strong style="display: block; color: #1A2A44;">Spotify Playlist Link:</strong>
                                            <a href="{results['spotify_link']}" target="_blank">{results['spotify_link']}</a>
                                        </span>
                                    </p>
                                </div>
                                """, unsafe_allow_html=True)
                                
                            if 'blog_post' in results:
                                st.markdown("""
                                <h4 style="font-family: 'Playfair Display', serif; color: #1A2A44; 
                                    margin-top: 1.5rem; margin-bottom: 0.5rem;">
                                    <span style="color: #D4AF37; margin-right: 0.5rem;">✨</span> Generated Blog Post
                                </h4>
                                <p style="font-style: italic; opacity: 0.8; margin-bottom: 1rem;">
                                    Copy the content below or post directly to WordPress
                                </p>
                                """, unsafe_allow_html=True)
                                
                                # Create a unique key for the session state to store blog post content
                                blog_key = f"blog_content_{playlist}"
                                if blog_key not in st.session_state:
                                    st.session_state[blog_key] = results['blog_post']
                                
                                # Text area for blog content with option to edit
                                st.session_state[blog_key] = st.text_area(
                                    "",
                                    st.session_state[blog_key],
                                    height=400,
                                    key=f"blog_editor_{playlist}"
                                )
                                
                                # WordPress posting section
                                col1, col2 = st.columns([3, 1])
                                
                                # Input for blog post title
                                with col1:
                                    title_key = f"blog_title_{playlist}"
                                    if title_key not in st.session_state:
                                        # Generate default title based on playlist name
                                        clean_name = playlist.split('Wedding Cocktail Hour')[0].strip()
                                        default_title = f"The {clean_name} Wedding Cocktail Hour"
                                        st.session_state[title_key] = default_title
                                    
                                    st.session_state[title_key] = st.text_input(
                                        "Blog Post Title",
                                        value=st.session_state[title_key],
                                        key=f"title_input_{playlist}"
                                    )
                                
                                # WordPress posting section - only show if API is initialized
                                with col2:
                                    st.markdown("<br>", unsafe_allow_html=True)  # Add spacing
                                    wp_button_key = f"wp_button_{playlist}"
                                    
                                    if wordpress_api is None:
                                        # Show message if WordPress API is not configured
                                        st.button("🔐 WordPress API Not Configured", key=wp_button_key, disabled=True)
                                        with st.expander("ℹ️ Configure WordPress", expanded=False):
                                            st.markdown("""
                                            To enable posting to WordPress, add these environment variables:
                                            - `WORDPRESS_API_URL`
                                            - `WORDPRESS_USERNAME`
                                            - `WORDPRESS_PASSWORD`
                                            """)
                                    else:
                                        # Show WordPress posting button
                                        if st.button("🚀 Post to WordPress", key=wp_button_key):
                                            with st.spinner("📝 Creating draft post in WordPress..."):
                                                try:
                                                    # Post to WordPress as draft
                                                    result = wordpress_api.create_post(
                                                        title=st.session_state[title_key],
                                                        content=st.session_state[blog_key],
                                                        status="draft"
                                                    )
                                                    
                                                    if result.get('success'):
                                                        post_id = result.get('post_id')
                                                        post_url = result.get('post_url')
                                                        edit_url = result.get('edit_url')
                                                        
                                                        st.success("✅ Draft blog post created successfully!")
                                                        st.markdown(f"""
                                                        <div style="margin-top: 0.5rem; padding: 1rem; background-color: rgba(212, 175, 55, 0.1); 
                                                            border-radius: 8px; border: 1px solid rgba(212, 175, 55, 0.3);">
                                                            <p style="margin: 0 0 0.5rem 0; font-weight: 500; color: #1A2A44;">
                                                                <span style="color: #D4AF37;">✨</span> Post #{post_id} created as draft
                                                            </p>
                                                            <p style="margin: 0 0 0.2rem 0; font-size: 0.9rem;">
                                                                <a href="{post_url}" target="_blank" style="color: #1A2A44;">View post preview</a>
                                                            </p>
                                                            <p style="margin: 0; font-size: 0.9rem;">
                                                                <a href="{edit_url}" target="_blank" style="color: #1A2A44;">Edit in WordPress</a>
                                                            </p>
                                                        </div>
                                                        """, unsafe_allow_html=True)
                                                    else:
                                                        error_msg = result.get('error', 'Unknown error')
                                                        st.error(f"❌ Error creating WordPress post: {error_msg}")
                                                
                                                except Exception as e:
                                                    st.error(f"❌ Error: {str(e)}")
                                        
                                        # Warning about draft post status when WordPress is configured
                                        st.info("ℹ️ Posts are created as drafts and need to be reviewed before publishing.")
                                
                            st.markdown("</div>", unsafe_allow_html=True)
                        else:
                            st.error(f"❌ Error processing playlist: {results}")

                # Success message at the end
                st.markdown("""
                <div style="margin: 2rem 0; padding: 1.5rem; background: linear-gradient(135deg, rgba(212, 175, 55, 0.1) 0%, rgba(245, 198, 203, 0.1) 100%); 
                    border-radius: 12px; text-align: center; box-shadow: 0 8px 20px rgba(0,0,0,0.05);">
                    <h3 style="margin: 0; color: #1A2A44; font-family: 'Playfair Display', serif; font-weight: 600;">
                        <span style="color: #D4AF37; margin-right: 0.5rem;">✨</span> All Selected Playlists Processed Successfully!
                    </h3>
                    <p style="margin-top: 0.5rem; margin-bottom: 0; opacity: 0.8;">
                        Your content is ready to be shared with the world.
                    </p>
                </div>
                """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()