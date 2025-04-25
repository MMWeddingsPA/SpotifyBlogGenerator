import os
import re
from openai import OpenAI
import trafilatura
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Updated to use standard OpenAI API with GPT-4o (since Gemini integration is having issues)
# This is a temporary fallback to ensure functionality

def extract_songs_from_html(html_content):
    """
    Extract song information from an existing blog post HTML content
    Returns a list of dictionaries with song and artist information
    """
    try:
        # Look for song links in anchor tags or plain text references
        song_pattern = r'<a[^>]*href="([^"]*)"[^>]*>(.*?)(?:–|&ndash;|&#8211;|\s*-\s*)(.*?)</a>|(?:<p>|<li>)(.*?)(?:–|&ndash;|&#8211;|\s*-\s*)(.*?)(?:</p>|</li>)'
        matches = re.finditer(song_pattern, html_content, re.IGNORECASE | re.DOTALL)
        
        songs = []
        for match in matches:
            if match.group(1):  # Link match
                youtube_link = match.group(1).strip()
                song = match.group(2).strip()
                artist = match.group(3).strip()
                songs.append({
                    'Song': song,
                    'Artist': artist,
                    'YouTube_Link': youtube_link if ('youtube.com' in youtube_link or 'youtu.be' in youtube_link) else ''
                })
            elif match.group(4):  # Text-only match
                song = match.group(4).strip()
                artist = match.group(5).strip()
                songs.append({
                    'Song': song, 
                    'Artist': artist,
                    'YouTube_Link': ''
                })
        
        # Filter out any false positives (very short song names, etc.)
        valid_songs = [s for s in songs if len(s['Song']) > 2 and len(s['Artist']) > 2]
        
        logger.info(f"Extracted {len(valid_songs)} songs from HTML content")
        return valid_songs
    
    except Exception as e:
        logger.error(f"Error extracting songs from HTML: {str(e)}")
        return []

def extract_spotify_link(html_content):
    """Extract Spotify playlist link from blog post content"""
    try:
        spotify_pattern = r'<a[^>]*href="(https://open.spotify.com/[^"]*)"[^>]*>'
        match = re.search(spotify_pattern, html_content)
        if match:
            return match.group(1)
        return None
    except Exception as e:
        logger.error(f"Error extracting Spotify link: {str(e)}")
        return None

def revamp_existing_blog(post_content, post_title):
    """
    Revamp an existing blog post to match current format and style
    :param post_content: HTML content from WordPress post
    :param post_title: Title of the blog post
    :return: Revamped blog post content in HTML format
    """
    # Extract songs and Spotify link from the existing content
    songs = extract_songs_from_html(post_content)
    spotify_link = extract_spotify_link(post_content)
    
    # Clean the content by removing HTML tags to get plain text for analysis
    plain_content = trafilatura.extract(post_content)
    
    # Initialize OpenAI client
    client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
    
    # Prepare extracted song information in a readable format
    songs_list = "\n".join([f"{s['Song']} – {s['Artist']} | YouTube Link: {s['YouTube_Link'] or 'None'}" for s in songs])
    
    prompt = f"""
    Revamp this existing wedding blog post to match our new format and style.
    
    Original Post Title: {post_title}
    
    Original Post Content (plain text for reference):
    {plain_content[:3000]}  # Limit content length to avoid token limits
    
    Extracted Songs:
    {songs_list}
    
    Spotify Link: {spotify_link or "Not found in original content"}
    
    Please rewrite this blog post following these guidelines:
    
    1. Format and HTML Structure:
    - Main title: Already provided by WordPress (don't include an H1 tag)
    - Subtitle: Use an <h3> tag with the text "Your Perfect Soundtrack for Love, Laughter, and Celebration"
    - Introduction: Use proper <p> tags for an engaging opening about the playlist's mood and purpose (2-3 paragraphs)
    - 4-5 themed sections with catchy titles, each with:
        * <h2> tag for section titles like "Find Great Vibes from Day One" or "Smooth Moves That Elevate the Fun" 
        * <p> tags for paragraphs explaining why these songs work well together
        * List the extracted songs with <p> tags for each song, including their YouTube links when available
    - Conclusion: <h2> tag for "Why This Playlist Works for Your Wedding" with <p> tags for content
    - Call to action: <h2> tag for "Listen to the Complete Playlist" that includes the Spotify playlist link if available
    
    2. HTML Style Guidelines:
    - Use proper HTML tags: <h2> for section headers, <h3> for subtitles, <p> for paragraphs
    - For song links, format as: <p><a href="YOUTUBE_LINK" target="_blank">SONG NAME – ARTIST NAME</a></p>
    - Add proper spacing between sections using line breaks
    - If Spotify link exists, format as: <p><strong>Listen to the full playlist: </strong><a href="SPOTIFY_LINK" target="_blank">Spotify Playlist</a></p>
    - Add a class to important elements: class="highlight-section" for key section headers
    - Make sure all HTML is properly structured and WordPress-compatible
    
    3. Content Style Guidelines:
    - Preserve the core theme and focus of the original post but enhance the wording and structure
    - Conversational and warm tone like an expert wedding DJ
    - Focus on creating atmosphere and emotional moments for each section
    - Blend practical details with romantic storytelling
    - Keep each section concise but meaningful (3-4 paragraphs max per section)
    - Use compelling descriptive language that evokes mood and setting
    
    IMPORTANT FORMATTING RULES:
    - DO NOT include opening or closing HTML tags like <html>, </html> or ```html
    - DO NOT wrap your response in quotation marks or any markdown code blocks
    - Start directly with the H3 subtitle and end with the final paragraph
    - Do not include any stray characters, quotes, or HTML comments
    """
    
    try:
        # Debug API key (only showing if it exists, not the actual value)
        if client.api_key:
            logger.info(f"OpenAI API Key exists: True (length: {len(client.api_key)})")
        else:
            logger.error("OpenAI API Key does not exist")
            raise Exception("OpenAI API key not found in environment variables. Please check the OPENAI_API_KEY secret.")
            
        # Using the standard OpenAI GPT-4o model
        # the newest OpenAI model is "gpt-4o" which was released May 13, 2024.
        # do not change this unless explicitly requested by the user
        response = client.chat.completions.create(
            model="gpt-4o",
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
                    
                    Your task is to revamp an existing blog post to match the premium brand voice
                    of Moments & Memories, which balances professional expertise with warm, personal engagement.
                    Maintain the original intent and key songs, but enhance the structure, formatting, and phrasing."""
                },
                {"role": "user", "content": prompt}
            ],
            max_tokens=3000,
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
        logger.info(f"Revamped content first 100 chars: {content[:100]}")
        logger.info(f"Revamped content last 100 chars: {content[-100:]}")
        
        return content
        
    except Exception as e:
        logger.error(f"Error revamping blog post: {str(e)}")
        raise Exception(f"Error revamping blog post: {str(e)}")

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