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
    uploaded_file = st.file_uploader(
        "Choose a CSV file",
        type="csv",
        help="Upload a CSV file containing songs and artists"
    )

    if uploaded_file is not None:
        try:
            st.session_state.df = load_csv(uploaded_file)
            st.success("CSV file loaded successfully!")
        except Exception as e:
            st.error(f"Error loading CSV: {str(e)}")
            return

    if st.session_state.df is not None:
        # Display unique playlists
        playlists = st.session_state.df['Playlist'].unique()
        st.header("Available Playlists")
        
        selected_playlist = st.selectbox(
            "Select a playlist to generate blog post",
            playlists
        )
        
        if st.button("Generate Blog Post"):
            with st.spinner("Processing playlist..."):
                try:
                    # Filter dataset for selected playlist
                    playlist_df = st.session_state.df[
                        st.session_state.df['Playlist'] == selected_playlist
                    ].copy()
                    
                    # Fetch YouTube links
                    progress_bar = st.progress(0)
                    for idx, row in playlist_df.iterrows():
                        search_query = f"{row['Song']} {row['Artist']}"
                        youtube_link = youtube_api.get_video_link(search_query)
                        playlist_df.at[idx, 'YouTube_Link'] = youtube_link
                        progress_bar.progress((idx + 1) / len(playlist_df))
                    
                    # Fetch Spotify playlist link
                    spotify_link = spotify_api.get_playlist_link(
                        "bm8eje5tcjj9eazftizqoikwm",
                        selected_playlist
                    )
                    
                    # Generate blog post
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
                    
                except Exception as e:
                    st.error(f"Error generating blog post: {str(e)}")

if __name__ == "__main__":
    main()
