import streamlit as st
import os
import pandas as pd

# Page configuration
st.set_page_config(
    page_title="Moments & Memories Blog Generator - Simple Version",
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
    }
    
    /* Main text and headers */
    .stMarkdown, .stText, p, div {
        font-family: 'Lato', sans-serif;
        color: #1A2A44;
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
        color: #D4AF37;
        margin-top: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)

# Add elegant header
st.markdown("""
<div style="display: flex; align-items: center; padding: 1.5rem 0; margin-bottom: 2rem; border-bottom: 1px solid rgba(212, 175, 55, 0.3);">
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

# Create tabs
tab1, tab2 = st.tabs(["Process Playlists", "Edit CSV Data"])

with tab1:
    st.header("Process Wedding Playlists")
    st.write("This simplified version allows you to upload CSV files and view their contents.")
    
    # File uploader
    uploaded_file = st.file_uploader("Upload Playlist CSV File", type="csv")
    
    if uploaded_file is not None:
        try:
            # Read CSV file
            df = pd.read_csv(uploaded_file)
            
            # Display the data
            st.subheader("CSV Data Preview")
            st.dataframe(df)
            
            # Display unique playlists if available
            if 'Playlist' in df.columns:
                playlists = df['Playlist'].unique()
                st.subheader("Available Playlists")
                for playlist in playlists:
                    st.write(f"- {playlist}")
        except Exception as e:
            st.error(f"Error loading CSV file: {str(e)}")

with tab2:
    st.header("Edit CSV Data")
    st.write("This tab will allow editing of CSV files in the future.")
    
    # Placeholder for future editing functionality
    st.info("Editing functionality will be added soon.")

# Add sidebar information
with st.sidebar:
    st.header("About")
    st.write("This is a simplified version of the Moments & Memories Blog Generator.")
    st.write("The full version includes:")
    st.markdown("""
    - YouTube link fetching
    - Spotify playlist matching
    - Blog post generation
    - WordPress integration
    """)
    
    st.header("API Status")
    st.write("APIs are temporarily disabled in this simplified version.")

st.markdown("---")
st.markdown("© 2025 Moments & Memories Wedding DJ & Photography")