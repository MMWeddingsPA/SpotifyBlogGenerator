import streamlit as st
import pandas as pd
from utils.youtube_api import YouTubeAPI
from utils.spotify_api import SpotifyAPI
from utils.openai_api import generate_blog_post
from utils.csv_handler import load_csv, save_csv
import os
import json
from datetime import datetime

# Page configuration
st.set_page_config(
    page_title="Wedding DJ Blog Generator",
    page_icon="🎵",
    layout="wide"
)

# Initialize session state
if 'df' not in st.session_state:
    st.session_state.df = None
if 'last_saved_csv' not in st.session_state:
    st.session_state.last_saved_csv = None

def save_processed_csv(df, operation_type):
    """Save CSV with timestamp and operation type"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"processed_playlists_{operation_type}_{timestamp}.csv"
    save_csv(df, filename)
    st.session_state.last_saved_csv = filename
    return filename

def main():
    st.title("Wedding DJ Blog Generator 🎵")

    # Initialize API clients
    youtube_api = YouTubeAPI(os.getenv("YOUTUBE_API_KEY"))
    spotify_api = SpotifyAPI(
        os.getenv("SPOTIFY_CLIENT_ID"),
        os.getenv("SPOTIFY_CLIENT_SECRET")
    )

    # Left sidebar for file operations and saved files
    with st.sidebar:
        st.header("File Operations")

        # File upload section
        uploaded_file = st.file_uploader(
            "Upload New CSV",
            type="csv",
            help="Upload a CSV file containing songs and artists"
        )

        # CSV Format Instructions
        with st.expander("CSV Format Instructions", expanded=False):
            st.markdown("""
            The CSV should be formatted as follows:
            - Playlist names should end with 'Wedding Cocktail Hour'
            - Each song should have: Song Title, Artist
            - Optional: Existing YouTube links

            Example:
            ```
            001 The Classic Wedding Cocktail Hour
            Song1-Artist1,Song1,Artist1,youtube_link1
            Song2-Artist2,Song2,Artist2,youtube_link2
            ```
            """)

        # Load previous CSV if available
        if st.session_state.last_saved_csv and os.path.exists(st.session_state.last_saved_csv):
            if st.button("Load Last Saved CSV"):
                try:
                    st.session_state.df = pd.read_csv(st.session_state.last_saved_csv)
                    st.success(f"Loaded {st.session_state.last_saved_csv}")
                except Exception as e:
                    st.error(f"Error loading saved CSV: {str(e)}")

    # Main content area
    if uploaded_file is not None:
        try:
            st.session_state.df = load_csv(uploaded_file)
            st.success("CSV file loaded successfully!")

            # Display summary
            total_playlists = st.session_state.df['Playlist'].nunique()
            total_songs = len(st.session_state.df)
            st.write(f"📊 Found {total_playlists} playlists with {total_songs} total songs")

        except Exception as e:
            st.error(f"Error loading CSV: {str(e)}")
            return

    if st.session_state.df is not None:
        # Display unique playlists with multi-select
        st.header("Available Playlists")
        playlists = st.session_state.df['Playlist'].unique()

        # Create columns for playlist selection and operations
        col1, col2 = st.columns([2, 1])

        with col1:
            selected_playlists = st.multiselect(
                "Select playlists to process",
                playlists,
                format_func=lambda x: x.split("Wedding Cocktail Hour")[0].strip()
            )

        with col2:
            st.write("Operations")
            fetch_youtube = st.checkbox("Fetch YouTube Links", value=True)
            fetch_spotify = st.checkbox("Fetch Spotify Playlist", value=True)
            generate_blog = st.checkbox("Generate Blog Post", value=True)

        # Preview button for selected playlists
        if selected_playlists and st.button("Preview Selected Playlists"):
            for playlist in selected_playlists:
                st.subheader(f"Preview: {playlist.split('Wedding Cocktail Hour')[0].strip()}")
                playlist_df = st.session_state.df[
                    st.session_state.df['Playlist'] == playlist
                ]
                st.dataframe(
                    playlist_df[['Song', 'Artist', 'YouTube_Link']],
                    hide_index=True
                )

        # Process button
        if selected_playlists and st.button("Process Selected Playlists"):
            operations = []
            if fetch_youtube: operations.append("YouTube")
            if fetch_spotify: operations.append("Spotify")
            if generate_blog: operations.append("Blog")

            if not operations:
                st.warning("Please select at least one operation to perform.")
                return

            for playlist in selected_playlists:
                st.write(f"Processing: {playlist.split('Wedding Cocktail Hour')[0].strip()}")

                try:
                    # Filter dataset for selected playlist
                    playlist_df = st.session_state.df[
                        st.session_state.df['Playlist'] == playlist
                    ].copy()

                    # Fetch YouTube links if selected
                    if fetch_youtube:
                        with st.spinner("Fetching YouTube links..."):
                            progress_bar = st.progress(0)
                            songs_to_process = playlist_df[
                                (playlist_df['YouTube_Link'].isna()) | 
                                (playlist_df['YouTube_Link'] == '')
                            ]

                            total_songs = len(songs_to_process)
                            for idx, row in songs_to_process.iterrows():
                                search_query = f"{row['Song']} {row['Artist']}"
                                youtube_link = youtube_api.get_video_link(search_query)
                                playlist_df.at[idx, 'YouTube_Link'] = youtube_link
                                progress_bar.progress((idx + 1) / total_songs)

                            # Update main dataframe
                            st.session_state.df.update(playlist_df)

                            # Save progress
                            filename = save_processed_csv(st.session_state.df, "youtube")
                            st.success(f"YouTube links updated and saved to {filename}")

                    # Fetch Spotify playlist if selected
                    if fetch_spotify:
                        with st.spinner("Fetching Spotify playlist link..."):
                            spotify_link = spotify_api.get_playlist_link(
                                "bm8eje5tcjj9eazftizqoikwm",
                                playlist
                            )
                            st.success(f"Spotify playlist link: {spotify_link}")

                    # Generate blog post if selected
                    if generate_blog:
                        with st.spinner("Generating blog post..."):
                            blog_post = generate_blog_post(
                                playlist_name=playlist,
                                songs_df=playlist_df,
                                spotify_link=spotify_link if fetch_spotify else None
                            )

                            st.header(f"Blog Post: {playlist.split('Wedding Cocktail Hour')[0].strip()}")
                            st.text_area(
                                "Copy the blog post below:",
                                blog_post,
                                height=400,
                                key=f"blog_{playlist}"
                            )

                except Exception as e:
                    st.error(f"Error processing {playlist}: {str(e)}")
                    continue

            st.success("All selected playlists processed successfully!")

if __name__ == "__main__":
    main()