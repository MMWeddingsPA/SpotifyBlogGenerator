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
        
        # Initialize session state variables if they don't exist
        if 'search_results' not in st.session_state:
            st.session_state.search_results = {}
        
        if 'revamped_content' not in st.session_state:
            st.session_state.revamped_content = None
            
        if 'current_post' not in st.session_state:
            st.session_state.current_post = None
            
        # Search form
        search_col1, search_col2 = st.columns([3, 1])
        with search_col1:
            search_term = st.text_input("Search WordPress Posts", placeholder="Enter keywords to search for posts...")
        
        with search_col2:
            search_button = st.button("🔍 Search")
            
        # Display search results and post selection
        if search_button and search_term:
            st.session_state.search_results = {
                "The Summer Pop Wedding Cocktail Hour": 123,
                "The Valentine's Day Wedding Cocktail Hour": 456,
                "The Smooth Sail Wedding Cocktail Hour": 789
            }
            
        # Display post selection if we have search results
        if st.session_state.search_results:
            post_options = list(st.session_state.search_results.keys())
            selected_post_title = st.selectbox("Select a Post", options=post_options)
            
            col1, col2 = st.columns([3, 1])
            with col2:
                load_post_button = st.button("📄 Load Post")
            
            # When a post is loaded, show its content and the revamp options
            if load_post_button and selected_post_title:
                selected_post_id = st.session_state.search_results[selected_post_title]
                
                # Mock loading post content
                with st.spinner("Loading post content..."):
                    # Simulate fetching post from WordPress
                    post = {
                        'id': selected_post_id,
                        'title': selected_post_title,
                        'content': f"""
                        <h2>{selected_post_title}</h2>
                        <p>This is the original content of the {selected_post_title} post. 
                        It contains information about the playlist and some of the songs included.</p>
                        <p>The songs in this playlist create a perfect atmosphere for your wedding cocktail hour.</p>
                        """,
                        'categories': [5, 8]
                    }
                    
                    # Store post in session state
                    st.session_state.current_post = post
                    
                    # Show post preview
                    st.write("### Original Post Content")
                    with st.expander("View Original HTML Content", expanded=False):
                        st.code(post['content'], language="html")
                    
                    # Show rendered preview
                    st.write("### Original Post Preview")
                    st.markdown(post['content'], unsafe_allow_html=True)
                    
                    # Blog style customization options
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
                        
                        section_count = 4
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
                        # Prepare style options dictionary
                        style_options = {
                            "tone": tone,
                            "mood": mood,
                            "audience": audience,
                            "section_count": section_count,
                            "intro_theme": intro_theme,
                            "conclusion_theme": conclusion_theme,
                            "title_style": title_style,
                            "custom_guidance": custom_guidance if 'custom_guidance' in locals() else "",
                            "model": model,
                            "temperature": temperature
                        }
                        
                        with st.spinner("Revamping post content... This may take a minute..."):
                            # Simulate blog revamping with OpenAI (mock for now)
                            revamped_content = f"""
                            <h2>{selected_post_title}</h2>
                            <p>Welcome to the perfect musical journey for your wedding celebration! The {selected_post_title} curates an exquisite selection of songs that will create the ideal atmosphere as your guests mingle and enjoy cocktails after your ceremony.</p>
                            
                            <h3>Setting the Perfect Mood</h3>
                            <p>This carefully curated playlist strikes the perfect balance between {mood.lower()} energy and romantic ambiance. The songs create a sophisticated backdrop that encourages conversation while maintaining the celebratory spirit of your special day.</p>
                            
                            <h3>Contemporary Classics</h3>
                            <p>Featuring modern hits that everyone will recognize alongside timeless classics, this playlist ensures all your guests - from college friends to family elders - will appreciate the musical selection.</p>
                            
                            <h3>Conversation Starters</h3>
                            <p>These musical selections aren't just background noise - they're conversation starters! Watch as your guests connect over favorite songs and share memories associated with these beloved tracks.</p>
                            
                            <h3>The Perfect Transition</h3>
                            <p>As your cocktail hour winds down, the playlist subtly shifts energy to prepare everyone for the reception festivities ahead, creating the perfect musical journey throughout your celebration.</p>
                            
                            <p>Need help implementing the perfect wedding soundtrack? Reach out to our team and we'll help craft the musical experience of your dreams!</p>
                            """
                            
                            # Store in session state to keep it visible
                            st.session_state.revamped_content = revamped_content
                            st.session_state.revamp_post_id = post['id']
                            st.session_state.revamp_post_title = post['title']
                            st.session_state.revamp_post_categories = post.get('categories', [])
                            
                            # Success message
                            st.success("✅ Post successfully revamped! See the preview below.")
        
        # Display revamped content if available in session state
        if 'revamped_content' in st.session_state and st.session_state.revamped_content:
            # Make sure this stays visible even when the page reloads
            st.markdown("---")
            st.markdown("## Revamped Post Results")
            
            # Show revamped preview
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
                            # Simulate WordPress API post creation
                            title = f"Revamped: {st.session_state.revamp_post_title}"
                            st.success(f"✅ New draft '{title}' created successfully!")
                            st.write("Edit URL: https://mmweddingspa.com/wp-admin/post.php?post=789&action=edit")
                
                with action_col2:
                    if st.button("💾 Save Locally", key="save_locally"):
                        with st.spinner("Saving blog post locally..."):
                            # Simulate local saving
                            filename = f"revamped_{st.session_state.revamp_post_id}"
                            st.success(f"✅ Revamped post saved successfully as '{filename}'")
        else:
            st.info("Search for posts to begin revamping content.")

if __name__ == "__main__":
    main()
