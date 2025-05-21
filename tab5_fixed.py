    # Tab 5: WordPress Edit
    with tab5:
        st.subheader("WordPress Edit")
        
        # Ensure wordpress_posts directory exists
        os.makedirs("wordpress_posts", exist_ok=True)
        
        # List all saved WordPress posts
        saved_posts = list_wordpress_posts()
        
        if not saved_posts:
            st.info("No saved WordPress posts found. Go to the WordPress Revamp tab, select a post, and click 'Save for Editing' first.")
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
                key="wordpress_edit_select"
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
                    
                    # Check for stored processed content first
                    post_content = post_data.get('processed_content', None)
                    
                    # If no processed content, get from post_data
                    if not post_content:
                        post_content = post_data.get('post_data', {}).get('content', '')
                        
                        # Handle content format (could be string or dict with rendered property)
                        if isinstance(post_content, dict) and 'rendered' in post_content:
                            post_content = post_content.get('rendered', '')
                    
                    # Ensure post_content is never None or empty
                    if not post_content:
                        post_content = f"<p>No content available for post ID: {post_id}</p>"
                    
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
                            key="wp_edit_model_select"
                        )
                        st.session_state.wp_edit_model = model
                    
                    with col2:
                        temp = st.slider(
                            "Creativity Level",
                            min_value=0.0,
                            max_value=1.0,
                            value=st.session_state.wp_edit_temp,
                            step=0.1,
                            key="wp_edit_temp_slider"
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
            
            # Add a button to go to WordPress Revamp tab
            if st.button("Go to WordPress Revamp", key="go_to_revamp_button"):
                st.session_state.active_tab = "WordPress Revamp"
                # Note: This won't work directly in Streamlit, but provides a visual cue