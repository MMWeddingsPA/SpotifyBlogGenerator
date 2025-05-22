import os
import re
from openai import OpenAI
import trafilatura
import logging
import streamlit as st
from utils.secrets_manager import get_secret

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
        # First, attempt to find linked songs
        song_pattern = r'<a[^>]*href="([^"]*)"[^>]*>(.*?)(?:–|&ndash;|&#8211;|\s*-\s*)(.*?)</a>|(?:<p>|<li>)(.*?)(?:–|&ndash;|&#8211;|\s*-\s*)(.*?)(?:</p>|</li>)'
        matches = re.finditer(song_pattern, html_content, re.IGNORECASE | re.DOTALL)
        
        # Second pattern to look for song names in plain paragraphs (not in links)
        # This will capture more song references that aren't formatted with the dash/hyphen
        plain_pattern = r'<p>([^<]{2,50})\s+by\s+([^<]{2,50})<\/p>'
        plain_matches = re.finditer(plain_pattern, html_content, re.IGNORECASE | re.DOTALL)
        
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
        
        # Process additional "song by artist" mentions
        for match in plain_matches:
            if match.group(1) and match.group(2):
                song = match.group(1).strip()
                artist = match.group(2).strip()
                
                # Check if this song is already in our list
                exists = False
                for existing in songs:
                    if existing['Song'].lower() == song.lower() and existing['Artist'].lower() == artist.lower():
                        exists = True
                        break
                
                # Add if it's a new song
                if not exists:
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
        # Check for multiple possible Spotify link formats
        
        # 1. Try finding iframe embed first (most common in WordPress posts)
        iframe_pattern = r'<iframe[^>]*src="(https://open\.spotify\.com/embed/playlist/[^"]+)"[^>]*>'
        iframe_match = re.search(iframe_pattern, html_content)
        if iframe_match:
            spotify_url = iframe_match.group(1)
            # Convert embed URL to regular URL if needed
            if '/embed/' in spotify_url:
                spotify_url = spotify_url.replace('/embed/', '/')
            return spotify_url
        
        # 2. Regular anchor link (fallback)
        anchor_pattern = r'<a[^>]*href="(https://open\.spotify\.com/[^"]*)"[^>]*>'
        match = re.search(anchor_pattern, html_content)
        if match:
            return match.group(1)
        
        # 3. Last resort: just look for URLs directly
        url_pattern = r'(https://open\.spotify\.com/playlist/[a-zA-Z0-9]+)'
        url_match = re.search(url_pattern, html_content)
        if url_match:
            return url_match.group(1)
            
        return None
    except Exception as e:
        logger.error(f"Error extracting Spotify link: {str(e)}")
        return None

def extract_spotify_playlist_id(spotify_url):
    """
    Extract the playlist ID from a Spotify URL
    Example: https://open.spotify.com/playlist/37i9dQZF1DXdPec7aLTmlC -> 37i9dQZF1DXdPec7aLTmlC
    """
    if not spotify_url:
        return None
        
    try:
        # Match playlist ID using regex pattern
        # Format could be: 
        # - https://open.spotify.com/playlist/37i9dQZF1DXdPec7aLTmlC
        # - https://open.spotify.com/playlist/37i9dQZF1DXdPec7aLTmlC?si=abc123
        # - spotify:playlist:37i9dQZF1DXdPec7aLTmlC
        pattern = r'(?:spotify:playlist:|spotify\.com/playlist/)([a-zA-Z0-9]{22})'
        match = re.search(pattern, spotify_url)
        
        if match:
            return match.group(1)
        else:
            logger.warning(f"Could not extract playlist ID from Spotify URL: {spotify_url}")
            return None
    except Exception as e:
        logger.error(f"Error extracting Spotify playlist ID: {str(e)}")
        return None

def revamp_existing_blog(post_content, post_title, youtube_api=None, style_options=None, spotify_api=None):
    """
    Revamp an existing blog post to match current format and style
    :param post_content: HTML content from WordPress post
    :param post_title: Title of the blog post
    :param youtube_api: Optional YouTube API client to fetch missing links
    :param style_options: Dictionary of style options to customize the blog post (tone, mood, audience, etc.)
    :param spotify_api: Optional Spotify API client to fetch fresh playlist data
    :return: Revamped blog post content in HTML format
    """
    # Extract songs and Spotify link from the existing content
    extracted_songs = extract_songs_from_html(post_content)
    spotify_link = extract_spotify_link(post_content)
    
    # Extract Spotify playlist ID if we have a link
    spotify_playlist_id = None
    
    # By default, use the songs extracted from the blog post
    songs = extracted_songs
    
    if spotify_link:
        spotify_playlist_id = extract_spotify_playlist_id(spotify_link)
        logger.info(f"Extracted Spotify playlist ID: {spotify_playlist_id}")
        
        # If we have a Spotify API client and playlist ID, try to fetch fresh song data
        if spotify_api and spotify_playlist_id:
            try:
                logger.info(f"Attempting to fetch fresh song data from Spotify playlist: {spotify_playlist_id}")
                # Get fresh song data from Spotify playlist
                spotify_tracks = spotify_api.get_playlist_tracks(spotify_playlist_id)
                
                if spotify_tracks and len(spotify_tracks) > 0:
                    logger.info(f"Successfully fetched {len(spotify_tracks)} songs from Spotify playlist")
                    
                    # Format songs into the expected structure
                    spotify_songs = []
                    for track in spotify_tracks:
                        artist_names = ', '.join([artist.get('name', '') for artist in track.get('artists', [])])
                        spotify_songs.append({
                            'Song': track.get('name', ''),
                            'Artist': artist_names,
                            'YouTube_Link': ''  # Will be populated later if YouTube API is provided
                        })
                    
                    if spotify_songs:
                        logger.info(f"Using {len(spotify_songs)} songs from Spotify playlist instead of {len(extracted_songs)} extracted songs")
                        songs = spotify_songs
                    else:
                        logger.warning("Could not format Spotify tracks, using extracted songs instead")
            except Exception as e:
                logger.error(f"Error fetching Spotify playlist data: {str(e)}")
                logger.info(f"Using {len(extracted_songs)} extracted songs as fallback")
    
    # Clean the content by removing HTML tags to get plain text for analysis
    try:
        plain_content = trafilatura.extract(post_content)
        if plain_content is None:
            # Fallback if trafilatura extraction fails
            # Use regex to strip HTML tags as a backup
            logger.info("Trafilatura extraction returned None. Using regex fallback to clean HTML.")
            import re
            plain_content = re.sub(r'<[^>]+>', ' ', post_content)
            # Remove extra whitespace
            plain_content = re.sub(r'\s+', ' ', plain_content).strip()
            
            # If still empty, use post_content directly with a warning
            if not plain_content or plain_content.isspace():
                plain_content = post_content
                logger.warning("Fallback HTML cleaning resulted in empty content. Using raw content.")
    except Exception as e:
        logger.warning(f"Error extracting plain text from HTML: {str(e)}")
        # Failsafe - use the original content if extraction fails
        plain_content = post_content
    
    # Fetch YouTube links for songs if they're missing and YouTube API is provided
    if youtube_api and songs:
        logger.info(f"Found {len(songs)} songs, checking for missing YouTube links...")
        songs_missing_links = [s for s in songs if not s['YouTube_Link']]
        
        if songs_missing_links:
            logger.info(f"Fetching YouTube links for {len(songs_missing_links)} songs...")
            
            for i, song in enumerate(songs_missing_links):
                try:
                    # Create a search query combining song and artist
                    search_query = f"{song['Song']} - {song['Artist']}"
                    
                    # Get YouTube link with error handling
                    youtube_link = youtube_api.get_video_link(search_query)
                    
                    # Update the link in the songs list
                    if youtube_link:
                        # Find this song in the original songs list and update it
                        for s in songs:
                            if s['Song'] == song['Song'] and s['Artist'] == song['Artist']:
                                s['YouTube_Link'] = youtube_link
                                break
                        
                        logger.info(f"Found YouTube link for '{search_query}': {youtube_link}")
                    else:
                        logger.warning(f"No YouTube link found for '{search_query}'")
                        
                except Exception as e:
                    # Handle YouTube API errors gracefully
                    if "quota" in str(e).lower():
                        logger.warning("YouTube API quota exceeded. Stopping YouTube link fetching.")
                        break
                    else:
                        query = f"{song['Song']} - {song['Artist']}"
                        logger.warning(f"Could not fetch YouTube link for '{query}': {str(e)}")
    
    # Initialize OpenAI client
    client = OpenAI(api_key=get_secret("OPENAI_API_KEY"))
    
    # Prepare extracted song information in a readable format
    songs_list = "\n".join([f"{s['Song']} – {s['Artist']} | YouTube Link: {s['YouTube_Link'] or 'None'}" for s in songs])
    
    # Initialize default style options if not provided
    if style_options is None:
        style_options = {}
    
    # Extract style parameters with defaults
    tone = style_options.get('tone', 'Professional')
    mood = style_options.get('mood', 'Elegant')
    audience = style_options.get('audience', 'Modern Couples')
    
    prompt = f"""
    Revamp this existing wedding blog post to match our new format and style.
    
    Original Post Title: {post_title}
    
    Original Post Content (plain text for reference):
    {plain_content[:3000] if plain_content else "No plain text content available"}
    
    Extracted Songs:
    {songs_list}
    
    Spotify Link: {spotify_link or "Not found in original content"}
    
    Style Guidelines:
    - Tone: {tone}
    - Mood: {mood}
    - Target Audience: {audience}
    
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
    - If Spotify link exists, format as: 
      * First add text link: <p><strong>Listen to the full playlist: </strong><a href="SPOTIFY_LINK" target="_blank">Spotify Playlist</a></p>
      * Then add embedded player: <iframe src="https://open.spotify.com/embed/playlist/PLAYLIST_ID" width="100%" height="380" frameborder="0" allowtransparency="true" allow="encrypted-media"></iframe>
        (where PLAYLIST_ID is extracted from the Spotify link - it's the part after "playlist/" in the URL)
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
            raise Exception("OpenAI API key not found. Please check the OPENAI_API_KEY secret.")
            
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
        
        # Replace PLAYLIST_ID with actual Spotify playlist ID if available
        if spotify_playlist_id:
            # Replace the PLAYLIST_ID placeholder with the actual ID in the iframe
            iframe_pattern = r'src="https://open\.spotify\.com/embed/playlist/PLAYLIST_ID"'
            iframe_replacement = f'src="https://open.spotify.com/embed/playlist/{spotify_playlist_id}"'
            content = re.sub(iframe_pattern, iframe_replacement, content)
            
            # Replace SPOTIFY_LINK placeholder with actual Spotify link
            link_pattern = r'href="SPOTIFY_LINK"'
            link_replacement = f'href="{spotify_link}"'
            content = re.sub(link_pattern, link_replacement, content)
        
        logger.info(f"Revamped content first 100 chars: {content[:100]}")
        logger.info(f"Revamped content last 100 chars: {content[-100:]}")
        
        return content
        
    except Exception as e:
        logger.error(f"Error generating revamped content: {str(e)}")
        raise Exception(f"Failed to revamp blog post: {str(e)}")

def generate_blog_post(playlist_name, songs_df, spotify_link=None, 
                  style_options=None):
    """
    Generate a formatted blog post using AI with consistent structure and style
    
    Parameters:
    - playlist_name: Name of the playlist
    - songs_df: DataFrame containing songs
    - spotify_link: Optional Spotify playlist link
    - style_options: Dictionary of style options to customize the blog post:
        - tone: Tone of the blog post (e.g., 'conversational', 'professional', 'romantic', 'upbeat')
        - section_count: Number of sections to divide songs into (e.g., 3, 4, 5)
        - mood: Overall mood to emphasize (e.g., 'elegant', 'fun', 'emotional', 'energetic')
        - audience: Target audience focus (e.g., 'couples', 'brides', 'modern couples', 'traditional')
        - title_style: Style for section titles (e.g., 'descriptive', 'short', 'playful', 'elegant')
    """
    # Use standard OpenAI client with GPT-4o
    client = OpenAI(api_key=get_secret("OPENAI_API_KEY"))

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
    Create a wedding DJ blog post for the playlist "{clean_name}" following this exact structure and HTML format:

    1. Introduction:
    - First, include an <h3> subtitle saying "Your Perfect Soundtrack for Love, Laughter, and Celebration"
    - Write 2-3 engaging paragraphs about this playlist's mood and purpose, wrapped in <p> tags
    - Explain how these songs create the perfect atmosphere for a wedding cocktail hour

    2. 3-5 Themed Sections:
    - For each section, create an <h2> heading with a catchy title describing the mood/theme
    - Write 1-2 paragraphs explaining why these songs work well together
    - List the songs from each section including YouTube links when available

    3. Conclusion:
    - <h2> heading: "Why This Playlist Works for Your Wedding"
    - 1-2 paragraphs explaining the overall flow and impact of the playlist
    - End with a call to action for couples to consider these songs

    4. Spotify Embed:
    - <h2> heading: "Listen to the Complete Playlist"
    - If a Spotify link is available, include both a text link and embedded player

    Song List to Feature:
    {sections_text}

    Spotify Link: {spotify_link or "Not available"}

    Important Style Notes:
    - Tone: {style_options.get('tone', 'Professional but warm')}
    - Target mood: {style_options.get('mood', 'Elegant and sophisticated')}
    - Audience focus: {style_options.get('audience', 'Modern couples planning their wedding')}
    - Section title style: {style_options.get('title_style', 'Descriptive and evocative')}
    - Number of sections: {style_options.get('section_count', 4)}
    - Introduction emphasis: {style_options.get('intro_theme', 'Setting the perfect atmosphere')}
    - Conclusion emphasis: {style_options.get('conclusion_theme', 'Creating memorable moments')}
    {f"- Custom style: {style_options.get('writing_style', '')}" if style_options and 'writing_style' in style_options else ""}
    {f"- Language style: {style_options.get('language_style', '')}" if style_options and 'language_style' in style_options else ""}
    {f"- Sentence structure: {style_options.get('sentence_structure', '')}" if style_options and 'sentence_structure' in style_options else ""}
    {f"- Custom guidance: {style_options.get('custom_guidance', '')}" if style_options and 'custom_guidance' in style_options else ""}

    HTML Formatting Guidelines:
    - Start content directly with the H3 subtitle (no HTML or body tags)
    - Use <h3> for subtitle, <h2> for section headers, <p> for paragraphs
    - For song links, format as: <p><a href="YouTube_Link" target="_blank">Song Name – Artist Name</a></p>
    - Add proper spacing between sections using empty lines
    - If Spotify link exists, format as: 
      <p><strong>Listen to the full playlist:</strong> <a href="{spotify_link}" target="_blank">Spotify Playlist</a></p>
      <iframe src="https://open.spotify.com/embed/playlist/{extract_spotify_playlist_id(spotify_link) if spotify_link else 'PLAYLIST_ID'}" width="100%" height="380" frameborder="0" allowtransparency="true" allow="encrypted-media"></iframe>
    - Add a class to important elements: class="highlight-section" for key section headers
    """

    # Extract Spotify playlist ID if available
    spotify_playlist_id = None
    if spotify_link:
        try:
            spotify_playlist_id = extract_spotify_playlist_id(spotify_link)
        except Exception as e:
            logger.warning(f"Could not extract Spotify playlist ID from {spotify_link}: {str(e)}")
            spotify_playlist_id = None

    try:
        # Check if API key is available
        if client.api_key:
            logging.info(f"OpenAI API Key found: {client.api_key[:5]}...[REDACTED]")
        else:
            raise ValueError("OpenAI API key not found.")
        
        # Set model and temperature parameters
        model = "gpt-4o"  # Default to GPT-4o
        temperature = 0.7  # Default temperature
        
        # Check if model/temperature settings are provided in style_options
        if style_options:
            if 'model' in style_options:
                model = style_options['model']
            if 'temperature' in style_options:
                temperature = float(style_options['temperature'])
        
        response = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system", 
                    "content": """You are an expert wedding DJ and blog writer for Moments & Memories, a premier wedding DJ company.
                    
                    Your task is to create engaging, informative blog posts about wedding playlists.
                    Follow the structure provided exactly. Use appropriate HTML tags as instructed.
                    Write in a professional yet warm tone that speaks directly to engaged couples.
                    
                    Your blog posts should:
                    - Balance expertise with approachability
                    - Include descriptive language that evokes mood and setting
                    - Group songs into thematic sections that make sense together
                    - Explain why certain songs work well for specific moments
                    - Use proper HTML formatting while maintaining readability
                    - Emphasize the emotional impact of the music selections
                    
                    Each section should have a clear purpose and flow naturally to the next.
                    Be specific about how these songs enhance the wedding experience."""
                },
                {"role": "user", "content": prompt}
            ],
            temperature=temperature,
            max_tokens=3000
        )
        
        blog_post = response.choices[0].message.content
        
        # Clean up response by removing any markdown code blocks that might be present
        if blog_post.startswith('```html'):
            blog_post = blog_post.replace('```html', '', 1)
            if blog_post.endswith('```'):
                blog_post = blog_post[:-3]
        
        # Remove any quotes that might be wrapping the content
        blog_post = blog_post.strip('"\'')
        
        # If we have a Spotify playlist ID, replace any instances of PLAYLIST_ID in iframes
        if spotify_playlist_id:
            blog_post = blog_post.replace('PLAYLIST_ID', spotify_playlist_id)
            
        return blog_post
        
    except Exception as e:
        error_msg = f"Error generating blog post: {str(e)}"
        logging.error(error_msg)
        raise Exception(error_msg)