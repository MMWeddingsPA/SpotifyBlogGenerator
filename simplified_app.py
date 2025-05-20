import streamlit as st
import pandas as pd
from datetime import datetime
import os

st.set_page_config(
    page_title="Playlist Blog Generator",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Add custom CSS
st.markdown("""
<style>
    .main .block-container {
        padding-top: 2rem;
    }
    h1, h2, h3 {
        color: #1A2A44;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 1rem;
    }
    .stTabs [data-baseweb="tab"] {
        height: 4rem;
        white-space: pre-wrap;
        background-color: #F5F5F5;
        border-radius: 4px 4px 0 0;
        gap: 1rem;
        padding: 1rem 1rem;
    }
    .stTabs [aria-selected="true"] {
        background-color: #D4AF37 !important;
        color: white !important;
    }
</style>
""", unsafe_allow_html=True)

def main():
    st.title("📋 Playlist Blog Generator")
    
    # Create tabs for different functions
    tabs = st.tabs(["Process Playlists", "Blog Generator", "Manage Data", "Revamp Posts"])
    
    with tabs[0]:
        st.header("Process Playlists")
        st.write("This tab allows you to process playlists from CSV files, fetch YouTube links, and find Spotify playlists.")
        
        # Simple example form
        with st.form(key="process_form"):
            st.selectbox("CSV File", ["Cocktail-Hours.csv", "Playlists.csv"])
            st.multiselect("Playlists to Process", ["The Summer Pop Wedding Cocktail Hour", "The Smooth Sail Wedding Cocktail Hour"])
            col1, col2, col3 = st.columns(3)
            with col1:
                st.checkbox("YouTube", value=True)
            with col2:
                st.checkbox("Spotify", value=True)
            with col3:
                st.checkbox("Generate Blog", value=True)
            
            st.form_submit_button("Start Processing")
    
    with tabs[1]:
        st.header("Blog Generator")
        st.write("Generate blog posts from processed playlists.")
        
        st.selectbox("Select Playlist", ["The Summer Pop Wedding Cocktail Hour", "The Smooth Sail Wedding Cocktail Hour"])
        
        st.subheader("Customization Options")
        model = st.selectbox("AI Model", ["gpt-4o", "gpt-4.1", "gpt-4.1-mini", "gpt-4.1-nano"])
        temperature = st.slider("Creativity Level", 0.0, 1.0, 0.7)
        
        with st.expander("Style Options", expanded=True):
            col1, col2 = st.columns(2)
            with col1:
                st.selectbox("Tone", ["Professional", "Conversational", "Romantic", "Upbeat"])
                st.selectbox("Mood", ["Elegant", "Fun", "Emotional", "Energetic"])
            with col2:
                st.selectbox("Audience", ["Modern Couples", "Traditional Couples", "Brides"])
                st.selectbox("Sections", ["Default (3-4)", "Minimal (2-3)", "Comprehensive (4-5)"])
        
        if st.button("Generate Blog Post"):
            st.success("Blog post generated successfully!")
    
    with tabs[2]:
        st.header("Manage Data")
        st.write("Manage your CSV files and saved blog posts.")
        
        st.subheader("CSV Files")
        st.dataframe(pd.DataFrame({
            "Filename": ["processed_playlists_updated_20250425_194937.csv", "Cocktail-Hours.csv"],
            "Date Modified": ["Apr 25, 2025", "Mar 15, 2025"],
            "Playlists": [56, 72]
        }))
        
        st.subheader("Saved Blog Posts")
        st.dataframe(pd.DataFrame({
            "Title": ["The Summer Pop Wedding Cocktail Hour", "The Smooth Sail Wedding Cocktail Hour"],
            "Date Created": ["Apr 28, 2025", "Apr 27, 2025"],
            "Status": ["Saved locally", "Published to WordPress"]
        }))
    
    with tabs[3]:
        st.header("Revamp Existing Posts")
        st.write("Search and revamp existing WordPress blog posts.")
        
        with st.form(key="search_form"):
            st.text_input("Search Terms", placeholder="Enter keywords to search for posts...")
            st.form_submit_button("Search Posts")
        
        st.selectbox("Select Post", ["The Valentine's Day Wedding Cocktail Hour", "The Summer Pop Wedding Cocktail Hour"])
        
        if st.button("Load Post"):
            st.success("Post loaded successfully!")
            
            st.subheader("Blog Style Options")
            
            # Model selection
            st.selectbox(
                "AI Model",
                ["gpt-4o", "gpt-4.1", "gpt-4.1-mini", "gpt-4.1-nano"],
                index=0,
                help="Select which OpenAI model to use for content generation"
            )
            
            st.slider(
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
                
                tone_options = ["Professional", "Conversational", "Romantic", "Upbeat", "Elegant", "Playful", "Custom"]
                st.selectbox(
                    "Writing Tone",
                    tone_options,
                    index=0
                )
                
                st.selectbox(
                    "Content Sections",
                    ["Default (3-4)", "Minimal (2-3)", "Comprehensive (4-5)", "Detailed (5-6)"]
                )
                
                # Submit button for the form
                st.form_submit_button("✨ Revamp This Post")
            
            # Display mockup of a revamped post
            st.subheader("Revamped Post Preview")
            st.markdown("""
            <h2>The Summer Pop Wedding Cocktail Hour</h2>
            <p>Looking for the perfect soundtrack to set the tone during your wedding cocktail hour? The Summer Pop Wedding Cocktail Hour playlist offers a refreshing blend of contemporary hits and timeless classics that will keep your guests engaged while they mingle and celebrate your special day.</p>
            <h3>Upbeat Contemporary Vibes</h3>
            <p>Start the celebration with lively tracks like "Blinding Lights" by The Weeknd and "Watermelon Sugar" by Harry Styles. These modern hits create an atmosphere of joy and celebration, perfect for the beginning of your wedding festivities.</p>
            """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
