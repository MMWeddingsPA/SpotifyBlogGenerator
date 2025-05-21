def extract_spotify_link(html_content):
    """Extract Spotify playlist link from blog post content"""
    try:
        import re
        import logging
        
        logger = logging.getLogger(__name__)
        
        # Check for multiple possible Spotify link formats
        
        # 1. Try finding iframe embed
        iframe_pattern = r'<iframe[^>]*src="(https://open\.spotify\.com/embed/playlist/[^"]+)"[^>]*>'
        iframe_match = re.search(iframe_pattern, html_content)
        if iframe_match:
            spotify_url = iframe_match.group(1)
            # Convert embed URL to regular URL if needed
            if '/embed/' in spotify_url:
                spotify_url = spotify_url.replace('/embed/', '/')
            logger.info(f"Found Spotify link in iframe: {spotify_url}")
            return spotify_url
        
        # 2. Try finding anchor link
        anchor_pattern = r'<a[^>]*href="(https://open\.spotify\.com/[^"]+)"[^>]*>'
        anchor_match = re.search(anchor_pattern, html_content)
        if anchor_match:
            logger.info(f"Found Spotify link in anchor: {anchor_match.group(1)}")
            return anchor_match.group(1)
        
        # 3. Try finding any Spotify URL in the HTML
        url_pattern = r'(https://open\.spotify\.com/playlist/[a-zA-Z0-9]+)'
        url_match = re.search(url_pattern, html_content)
        if url_match:
            logger.info(f"Found Spotify URL in content: {url_match.group(1)}")
            return url_match.group(1)
        
        # If nothing found, log and return None
        logger.warning("No Spotify link found in HTML content")
        # Print a short sample of the HTML for debugging
        sample = html_content[:200] + "..." if len(html_content) > 200 else html_content
        logger.debug(f"Content sample: {sample}")
        return None
    except Exception as e:
        logger.error(f"Error extracting Spotify link: {str(e)}")
        return None