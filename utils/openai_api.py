import os
from openai import OpenAI

# Updated to use standard OpenAI API with GPT-4o (since Gemini integration is having issues)
# This is a temporary fallback to ensure functionality

def generate_blog_post(playlist_name, songs_df, spotify_link=None):
    """
    Generate a formatted blog post using AI with consistent structure and style
    """
    # Use standard OpenAI client with GPT-4o
    client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

    # Clean playlist name for display
    clean_name = playlist_name.split('Wedding Cocktail Hour')[0].strip()

    # Group songs into sections (4-5 songs per section)
    total_songs = len(songs_df)
    songs_per_section = min(5, max(3, total_songs // 4))

    # Prepare song sections - always use YouTube links for individual songs
    sections = []
    for i in range(0, total_songs, songs_per_section):
        section_songs = songs_df.iloc[i:i + songs_per_section]
        songs_list = []
        
        for _, row in section_songs.iterrows():
            song = row['Song']
            artist = row['Artist']
            youtube_link = row['YouTube_Link']
            
            # Only use YouTube links (not Spotify) for individual songs
            if youtube_link and str(youtube_link).strip():
                # Check if YouTube link is valid and contains youtube.com
                if 'youtube.com' in str(youtube_link) or 'youtu.be' in str(youtube_link):
                    # Format using HTML for better WordPress compatibility
                    songs_list.append(f'<p><a href="{youtube_link}" target="_blank">{song} – {artist}</a></p>')
                else:
                    songs_list.append(f'<p>{song} – {artist}</p>')
            else:
                songs_list.append(f'<p>{song} – {artist}</p>')
                
        sections.append("\n".join(songs_list))

    sections_text = "\n\n".join(f"Section {i+1} - Songs for the {['Opening', 'Middle', 'Peak', 'Wind-down', 'Finale'][i % 5]} Phase:\n{songs}" for i, songs in enumerate(sections))

    prompt = f"""
    Create a wedding DJ blog post for the playlist "{clean_name}" following this exact structure and HTML formatting:

    1. Format and HTML Structure:
    - Main title: Already provided by WordPress (don't include an H1 tag)
    - Subtitle: Use an <h3> tag with the text "Your Perfect Soundtrack for Love, Laughter, and Celebration"
    - Introduction: Use proper <p> tags for an engaging opening about the playlist's mood and purpose (2-3 paragraphs)
    - 4-5 themed sections with catchy titles similar to these examples, each with:
        * <h2> tag for section titles like "Find Great Vibes from Day One" or "Smooth Moves That Elevate the Fun" 
        * <p> tags for paragraphs explaining why these songs work well together
        * Listed songs with <p> tags for each song, including the YouTube links exactly as provided
    - Conclusion: <h2> tag for "Why This Playlist Works for Your Wedding" with <p> tags for content
    - Call to action: <h2> tag for "Listen to the Complete Playlist" that includes the Spotify playlist link

    2. HTML Style Guidelines:
    - Use proper HTML tags: <h2> for section headers, <h3> for subtitles, <p> for paragraphs
    - For song links, format as: <p><a href="YOUTUBE_LINK" target="_blank">SONG NAME – ARTIST NAME</a></p>
    - Add proper spacing between sections using <div> tags or line breaks
    - Format the Spotify link as: <p><strong>Listen to the full playlist: </strong><a href="SPOTIFY_LINK" target="_blank">Spotify Playlist</a></p>
    - Add a class to important elements: class="highlight-section" for key section headers
    - Make sure all HTML is properly structured and WordPress-compatible

    3. Content Style Guidelines:
    - Conversational and warm tone like an expert wedding DJ
    - Focus on creating atmosphere and emotional moments for each section
    - Blend practical details with romantic storytelling
    - Keep each section concise but meaningful (3-4 paragraphs max per section)
    - Use compelling descriptive language that evokes mood and setting
    - Emphasize how these songs enhance specific wedding moments

    4. Available Songs (already properly formatted with YouTube links, use exactly as provided):
    {sections_text}

    5. Additional Details:
    Spotify Playlist Link: {spotify_link if spotify_link else '[Insert Spotify Playlist Link]'}
    ONLY use this Spotify link at the end of the blog post in a final call to action section.

    Reference the sample blog format from the Moments & Memories website with clean formatting, proper headings, and well-structured content sections. Ensure the final product has the professional appearance of a high-quality wedding blog post.
    """

    try:
        # Debug API key (only showing if it exists, not the actual value)
        if client.api_key:
            print(f"OpenAI API Key exists: True (length: {len(client.api_key)})")
        else:
            print("OpenAI API Key does not exist")
            raise Exception("OpenAI API key not found in environment variables. Please check the OPENAI_API_KEY secret.")
            
        # Using the standard OpenAI GPT-4o model for better reliability
        # gpt-4o is the newest OpenAI model released after knowledge cutoff
        # do not change this unless explicitly requested by the user
        response = client.chat.completions.create(
            model="gpt-4o",  # Using the latest OpenAI model
            messages=[
                {
                    "role": "system",
                    "content": """You are an expert wedding DJ and blog writer for Moments & Memories, a premium wedding DJ company.
                    
                    Your writing style has these key characteristics:
                    - Professional yet conversational tone that speaks directly to engaged couples
                    - Clear section headings that divide content into readable chunks
                    - Expert insights about music selection for different wedding moments
                    - Proper HTML formatting with h2, h3, p tags, and well-structured content
                    - Engaging descriptions that evoke the atmosphere created by each music section
                    - Thoughtful song selections with YouTube links for couples to preview
                    - Clean, visually appealing formatting similar to existing blog posts
                    
                    IMPORTANT FORMATTING RULES:
                    - DO NOT include opening or closing HTML tags like <html>, </html> or ```html
                    - DO NOT wrap your response in quotation marks or any markdown code blocks
                    - Start directly with the H3 subtitle and end with the final paragraph
                    - Do not include any stray characters, quotes, or HTML comments
                    
                    Your content should match the premium brand voice of Moments & Memories, which balances professional expertise with warm, 
                    personal engagement. Format songs and sections similar to existing blog posts on mmweddingspa.com."""
                },
                {"role": "user", "content": prompt}
            ],
            max_tokens=2500,
            temperature=0.7
        )
        
        # Return the generated content
        content = response.choices[0].message.content
        
        # Minimal cleanup - only remove markdown code blocks and surrounding quotes
        # Be careful NOT to alter HTML tags
        if content.startswith('```html'):
            content = content.replace('```html', '', 1)
            if content.endswith('```'):
                content = content[:-3]
        
        # Remove any surrounding quotes but preserve HTML tags
        content = content.strip('"\'')
        
        # Debug output of content structure
        print(f"Content first 100 chars: {content[:100]}")
        print(f"Content last 100 chars: {content[-100:]}")
        
        return content

    except Exception as e:
        raise Exception(f"Error generating blog post: {str(e)}")