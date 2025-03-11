import streamlit as st
import pandas as pd
from utils.youtube_api import YouTubeAPI
from utils.spotify_api import SpotifyAPI
from utils.openai_api import generate_blog_post
from utils.csv_handler import load_csv, save_csv
import os

# Page configuration
st.set_page_config(
    page_title="Wedding DJ Blog Generator",
    page_icon="🎵",
    layout="wide"
)

# Initialize session state
if 'df' not in st.session_state:
    st.session_state.df = None
if 'playlist_name' not in st.session_state:
    st.session_state.playlist_name = None

def main():
    st.title("Wedding DJ Blog Generator 🎵")

    # Initialize API clients
    youtube_api = YouTubeAPI(os.getenv("YOUTUBE_API_KEY"))
    spotify_api = SpotifyAPI(
        os.getenv("SPOTIFY_CLIENT_ID"),
        os.getenv("SPOTIFY_CLIENT_SECRET")
    )

    # File upload section
    st.header("Upload Playlist CSV")
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

    uploaded_file = st.file_uploader(
        "Choose a CSV file",
        type="csv",
        help="Upload a CSV file containing songs and artists"
    )

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
        # Display unique playlists in a more organized way
        st.header("Available Playlists")

        playlists = st.session_state.df['Playlist'].unique()

        # Create two columns
        col1, col2 = st.columns([2, 1])

        with col1:
            selected_playlist = st.selectbox(
                "Select a playlist to generate blog post",
                playlists,
                format_func=lambda x: x.split("Wedding Cocktail Hour")[0].strip()
            )

        with col2:
            if st.button("Preview Playlist", key="preview"):
                # Filter and display selected playlist
                playlist_df = st.session_state.df[
                    st.session_state.df['Playlist'] == selected_playlist
                ]
                st.write(f"Songs in {selected_playlist.split('Wedding Cocktail Hour')[0].strip()}:")
                st.dataframe(
                    playlist_df[['Song', 'Artist', 'YouTube_Link']],
                    hide_index=True
                )

        if st.button("Generate Blog Post"):
            with st.spinner("Processing playlist..."):
                try:
                    # Filter dataset for selected playlist
                    playlist_df = st.session_state.df[
                        st.session_state.df['Playlist'] == selected_playlist
                    ].copy()

                    # Create progress bar
                    progress_bar = st.progress(0)
                    st.write("Fetching YouTube links...")

                    # Fetch YouTube links for songs without them
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

                    # Update the main dataframe with new YouTube links
                    st.session_state.df.update(playlist_df)

                    # Fetch Spotify playlist link
                    st.write("Fetching Spotify playlist link...")
                    spotify_link = spotify_api.get_playlist_link(
                        "bm8eje5tcjj9eazftizqoikwm",
                        selected_playlist
                    )

                    # Generate blog post
                    st.write("Generating blog post...")
                    blog_post = generate_blog_post(
                        playlist_name=selected_playlist,
                        songs_df=playlist_df,
                        spotify_link=spotify_link
                    )

                    # Display and allow copying of blog post
                    st.header("Generated Blog Post")
                    st.text_area(
                        "Copy the blog post below:",
                        blog_post,
                        height=400
                    )

                    # Save updated CSV
                    save_csv(st.session_state.df, "updated_playlists.csv")
                    st.success("Blog post generated successfully! The CSV has been updated with new YouTube links.")

                except Exception as e:
                    st.error(f"Error generating blog post: {str(e)}")

if __name__ == "__main__":
    main()