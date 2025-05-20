import streamlit as st
import pandas as pd
import os
import json
import re
import traceback
from datetime import datetime
from utils.fixed_youtube_api import YouTubeAPI
from utils.spotify_api import SpotifyAPI
from utils.openai_api import generate_blog_post, revamp_existing_blog
from utils.fixed_wordpress_api import WordPressAPI
from utils.corrected_csv_handler import load_csv, save_csv, create_empty_playlist_df
from utils.secrets_manager import get_secret

# Page configuration
st.set_page_config(
    page_title="WordPress Blog Revamp - Fixed Version",
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
    <h1>WordPress Blog Revamp</h1>
    <p style="font-family: 'Playfair Display', serif; font-size: 1.2rem; color: #1A2A44; margin-bottom: 0; font-style: italic;">
        Creating Moments & Memories, One Wedding at a Time
    </p>
</div>
""", unsafe_allow_html=True)

# Initialize session state variables
if 'wordpress_posts' not in st.session_state:
    st.session_state.wordpress_posts = []
if 'selected_post_id' not in st.session_state:
    st.session_state.selected_post_id = None
if 'selected_post_title' not in st.session_state:
    st.session_state.selected_post_title = None
if 'current_post' not in st.session_state:
    st.session_state.current_post = None
if 'revamp_model' not in st.session_state:
    st.session_state.revamp_model = "gpt-4o"
if 'revamp_temperature' not in st.session_state:
    st.session_state.revamp_temperature = 0.7
if 'revamp_tone' not in st.session_state:
    st.session_state.revamp_tone = "Professional"
if 'revamp_section_count' not in st.session_state:
    st.session_state.revamp_section_count = "Default (3-4)"

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
    
    # WordPress API initialization
    try:
        wordpress_api = None  # Initialize to None first
        # Check if WordPress credentials are available
        if all([
            get_secret("WORDPRESS_API_URL"),
            get_secret("WORDPRESS_USERNAME"),
            get_secret("WORDPRESS_PASSWORD")
        ]):
            # Create WordPress API client
            wordpress_api = WordPressAPI(
                api_url=get_secret("WORDPRESS_API_URL"),
                username=get_secret("WORDPRESS_USERNAME"),
                password=get_secret("WORDPRESS_PASSWORD")
            )
            
            # Test connection to WordPress
            test_result = wordpress_api.test_connection()
            if not test_result[0]:  # Connection failed
                st.sidebar.error(f"⚠️ WordPress API error: {test_result[1]}")
                # Don't set to None since we want to show diagnostic information
                st.sidebar.error("WordPress API is not connected properly. Publishing features will be limited.")
        else:
            st.sidebar.warning("⚠️ WordPress API credentials are missing. Publishing features will be disabled.")
    except Exception as e:
        st.sidebar.error(f"⚠️ WordPress API error: {str(e)}")
        wordpress_api = None
    
    # WordPress Revamp Feature
    st.markdown("## Revamp Existing WordPress Posts")
    st.markdown("This feature allows you to revamp existing blog posts from your WordPress site.")
    
    # Check WordPress API connection
    if wordpress_api is None:
        st.warning("WordPress API is not connected. Please check your settings and ensure you have WordPress credentials configured.")
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
                
                selected_category_id = category_options[selected_category]
            except Exception as e:
                st.warning(f"Could not load categories: {str(e)}")
                selected_category_id = None
        
        # Only try to fetch posts if there are actual search parameters
        fetch_posts = st.button("🔍 Search Posts", key="search_posts")
        if fetch_posts or ('wordpress_posts' in st.session_state and st.session_state.wordpress_posts):
            # Show spinner during API call
            with st.spinner("Fetching posts..."):
                try:
                    # Only make API call if button is pressed or we don't have posts yet
                    if fetch_posts or 'wordpress_posts' not in st.session_state:
                        # Get posts from WordPress
                        posts = wordpress_api.get_posts(
                            search_term=search_term if search_term else None,
                            category=selected_category_id,
                            per_page=20,  # Limit to most recent 20 posts
                            status="publish"
                        )
                        
                        # Store in session state
                        st.session_state.wordpress_posts = posts
                        
                        # Show result count
                        st.write(f"Found {len(posts)} post(s).")
                except Exception as e:
                    st.error(f"Error fetching posts: {str(e)}")
                    st.session_state.wordpress_posts = []
        
        # Post selection and revamping
        st.write("### Revamp Selected Post")
        
        if st.session_state.wordpress_posts:
            # Create a dictionary of post titles mapped to IDs for selection
            post_options = {f"{post['id']}: {post['title']['rendered'][:50]}...": post['id'] 
                           for post in st.session_state.wordpress_posts}
            
            # Two-step process with a "Load Post" button
            col1, col2 = st.columns([3, 1])
            
            with col1:
                selected_post_title = st.selectbox(
                    "Select a post to revamp",
                    options=list(post_options.keys()),
                    index=0,
                    key="post_selection"
                )
            
            with col2:
                load_post_button = st.button("📄 Load Post", key="load_post")
            
            # Store selected post in session state regardless of button click
            if selected_post_title:
                # Save selection to session state
                st.session_state.selected_post_title = selected_post_title
                st.session_state.selected_post_id = post_options[selected_post_title]
            
            # Only proceed if load button is clicked OR we already have a post loaded
            if (load_post_button and st.session_state.selected_post_id) or st.session_state.current_post:
                # Get post ID from appropriate source
                if load_post_button and st.session_state.selected_post_id:
                    selected_post_id = st.session_state.selected_post_id
                    
                    # Fetch the post content and store it
                    with st.spinner("Loading post content..."):
                        try:
                            post = wordpress_api.get_post(selected_post_id)
                            if post:
                                # Store in session state
                                st.session_state.current_post = post
                                st.success(f"Post loaded: {post['title']['rendered']}")
                            else:
                                st.error("Could not load post.")
                        except Exception as e:
                            st.error(f"Error loading post: {str(e)}")
                
                # If we have a post (either newly loaded or from session state), display and allow revamp
                if st.session_state.current_post:
                    post = st.session_state.current_post
                    
                    # Show existing post details
                    st.subheader(f"Post: {post['title']['rendered']}")
                    
                    # Display tabs to show the original content and revamp options
                    post_tabs = st.tabs(["Original Content", "Revamp Options"])
                    
                    with post_tabs[0]:
                        # Show the original content
                        st.markdown(post['content']['rendered'], unsafe_allow_html=True)
                    
                    with post_tabs[1]:
                        st.write("#### Customize Your Revamp")
                        
                        # Initialize form for revamp options
                        with st.form(key="revamp_form"):
                            # AI model settings at the top level
                            st.subheader("AI Model Settings")
                            
                            # Model selection
                            model_options = ["gpt-4o", "gpt-3.5-turbo"]
                            model_index = 0
                            if st.session_state.revamp_model in model_options:
                                model_index = model_options.index(st.session_state.revamp_model)
                            
                            model = st.selectbox(
                                "AI Model",
                                model_options,
                                index=model_index,
                                help="Choose the AI model to use for blog generation. GPT-4o is recommended for best quality but may cost more."
                            )
                            
                            # Temperature slider (creativity level)
                            temperature = st.slider(
                                "AI Creativity",
                                min_value=0.0,
                                max_value=1.0,
                                value=st.session_state.revamp_temperature,
                                step=0.1,
                                format="%.1f",
                                help="Higher values make output more creative but potentially less factual. Lower values make output more predictable and focused."
                            )
                            
                            # Basic style options
                            st.subheader("Content Style")
                            
                            # Tone options with custom option
                            tone_options = ["Professional", "Conversational", "Romantic", "Upbeat", "Elegant", "Playful", "Custom"]
                            tone_index = 0
                            if st.session_state.revamp_tone in tone_options:
                                tone_index = tone_options.index(st.session_state.revamp_tone)
                            
                            tone = st.selectbox(
                                "Writing Tone",
                                tone_options,
                                index=tone_index
                            )
                            
                            # Handle custom tone input
                            if tone == "Custom":
                                custom_tone_default = ""
                                if not st.session_state.revamp_tone in tone_options:
                                    custom_tone_default = st.session_state.revamp_tone
                                    
                                custom_tone = st.text_input(
                                    "Custom tone", 
                                    value=custom_tone_default,
                                    placeholder="e.g., 'Inspirational with a touch of humor'"
                                )
                                tone = custom_tone if custom_tone else "Professional"
                            
                            # Section count options
                            section_count_options = ["Default (3-4)", "Minimal (2-3)", "Comprehensive (4-5)", "Detailed (5-6)", "Custom"]
                            section_index = 0
                            if st.session_state.revamp_section_count in section_count_options:
                                section_index = section_count_options.index(st.session_state.revamp_section_count)
                                
                            section_count = st.selectbox(
                                "Number of Song Sections",
                                section_count_options,
                                index=section_index
                            )
                            
                            # Handle custom section count
                            if section_count == "Custom":
                                custom_section_default = ""
                                if not st.session_state.revamp_section_count in section_count_options:
                                    custom_section_default = st.session_state.revamp_section_count
                                
                                custom_section = st.text_input(
                                    "Custom section count", 
                                    value=custom_section_default,
                                    placeholder="e.g., '3 sections with 5 songs each'"
                                )
                                section_count = custom_section if custom_section else "Default (3-4)"
                            
                            # Two-column layout for more options
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                # Introduction theme options
                                intro_themes = ["Wedding Day Experience", "Musical Journey", "Setting the Mood", "Guest Experience", "Custom"]
                                intro_theme = st.selectbox("Introduction Theme", intro_themes)
                                
                                if intro_theme == "Custom":
                                    custom_intro = st.text_input("Custom introduction theme", 
                                        placeholder="e.g., 'Romantic Beginnings'")
                                    intro_theme = custom_intro if custom_intro else intro_theme
                            
                            with col2:
                                # Conclusion theme options
                                conclusion_themes = ["Memorable Moments", "Perfect Soundtrack", "Guest Enjoyment", "Atmosphere Creation", "Custom"]
                                conclusion_theme = st.selectbox("Conclusion Theme", conclusion_themes)
                                
                                if conclusion_theme == "Custom":
                                    custom_conclusion = st.text_input("Custom conclusion theme", 
                                        placeholder="e.g., 'Lasting Impressions'")
                                    conclusion_theme = custom_conclusion if custom_conclusion else conclusion_theme
                            
                            # Create a dictionary of all style options
                            style_options = {
                                "tone": tone,
                                "section_count": section_count,
                                "intro_theme": intro_theme,
                                "conclusion_theme": conclusion_theme,
                                "model": model,
                                "temperature": temperature
                            }
                            
                            # Revamp button with submit
                            revamp_submitted = st.form_submit_button("✨ Revamp This Post")
                            
                            if revamp_submitted:
                                # Save all settings to session state
                                st.session_state.revamp_model = model
                                st.session_state.revamp_temperature = temperature
                                st.session_state.revamp_tone = tone
                                st.session_state.revamp_section_count = section_count
                                
                                with st.spinner("🪄 Revamping your blog post..."):
                                    try:
                                        # Extract content from existing post
                                        post_content = post['content']['rendered']
                                        post_title = post['title']['rendered']
                                        
                                        # Revamp the post content using AI
                                        revamped_content = revamp_existing_blog(
                                            post_content=post_content,
                                            post_title=post_title,
                                            youtube_api=youtube_api,
                                            style_options=style_options
                                        )
                                        
                                        # Store the revamped content in session state
                                        st.session_state.revamped_content = revamped_content
                                        st.session_state.revamp_original_id = post['id']
                                        st.session_state.revamp_original_title = post_title
                                        
                                        st.success("✅ Post revamped successfully!")
                                    except Exception as e:
                                        st.error(f"Error revamping post: {str(e)}")
                                        st.error(traceback.format_exc())
                        
                        # Display revamped content if available
                        if 'revamped_content' in st.session_state and st.session_state.revamped_content:
                            st.markdown("### Revamped Post Preview")
                            st.markdown(st.session_state.revamped_content, unsafe_allow_html=True)
                            
                            # Provide options to save locally or publish to WordPress
                            save_col1, save_col2 = st.columns(2)
                            
                            with save_col1:
                                # Save locally button
                                if st.button("💾 Save Locally", key="save_revamp_local"):
                                    try:
                                        # Generate a local filename
                                        original_title = st.session_state.revamp_original_title
                                        cleaned_title = "".join([c if c.isalnum() or c.isspace() else "_" for c in original_title]).strip()
                                        filename = save_blog_post(
                                            playlist_name=cleaned_title,
                                            blog_content=st.session_state.revamped_content,
                                            title=f"Revamped: {original_title}"
                                        )
                                        st.success(f"✅ Saved revamped post locally as {filename}")
                                    except Exception as e:
                                        st.error(f"Error saving revamped post: {str(e)}")
                            
                            with save_col2:
                                # Publish as new draft or update existing post
                                publish_options = [
                                    "Create new draft post",
                                    "Update this post (keep as draft)",
                                    "Update and publish immediately"
                                ]
                                publish_action = st.selectbox(
                                    "WordPress action",
                                    publish_options
                                )
                                
                                # Submit to WordPress button
                                if st.button("📤 Submit to WordPress", key="submit_revamp_wp"):
                                    with st.spinner("Submitting to WordPress..."):
                                        try:
                                            original_title = st.session_state.revamp_original_title
                                            
                                            # Determine action based on selection
                                            if publish_action == publish_options[0]:
                                                # Create new draft
                                                result = wordpress_api.create_post(
                                                    title=f"Revamped: {original_title}",
                                                    content=st.session_state.revamped_content,
                                                    status="draft"
                                                )
                                                st.success(f"✅ Created new draft post in WordPress")
                                                
                                            elif publish_action == publish_options[1]:
                                                # Update but keep as draft
                                                # Implementation needed - requires WordPress update_post functionality
                                                st.error("This functionality is not yet implemented.")
                                                
                                            else:
                                                # Update and publish immediately
                                                # Implementation needed - requires WordPress update_post functionality
                                                st.error("This functionality is not yet implemented.")
                                                
                                        except Exception as e:
                                            st.error(f"Error submitting to WordPress: {str(e)}")
                else:
                    st.info("No post loaded. Please select and load a post to revamp.")

if __name__ == "__main__":
    main()