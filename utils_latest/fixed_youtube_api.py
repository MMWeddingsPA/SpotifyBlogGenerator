from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class YouTubeAPI:
    def __init__(self, api_key):
        """
        Initialize YouTube API client
        :param api_key: YouTube Data API v3 key
        """
        if not api_key:
            raise ValueError("YouTube API key is required")
        
        self.api_key = api_key
        self.youtube = build('youtube', 'v3', developerKey=api_key)
        self.quota_exceeded = False
        
    def verify_connection(self):
        """
        Verify the YouTube API connection is working properly
        Returns (success, message) tuple
        """
        try:
            # Make a simple API call to verify the key works
            response = self.youtube.videos().list(
                part='snippet',
                chart='mostPopular',
                maxResults=1,
                regionCode='US'
            ).execute()
            
            # Check if we got any items in the response
            if 'items' in response and len(response['items']) > 0:
                logger.info("YouTube API connection successful")
                return True, "API connection successful"
            else:
                logger.warning("YouTube API returned empty response")
                return False, "API returned empty response"
                
        except HttpError as e:
            error_message = str(e)
            logger.error(f"YouTube API error: {error_message}")
            
            # Check specifically for quota exceeded errors
            if "quotaExceeded" in error_message:
                self.quota_exceeded = True
                logger.warning("YouTube API quota exceeded")
                return False, f"API error: {error_message}"
            
            return False, f"API error: {error_message}"
            
        except Exception as e:
            logger.error(f"YouTube API general error: {str(e)}")
            return False, f"API error: {str(e)}"

    def get_video_link(self, search_query):
        """
        Search for a video and return its link with more specific search terms
        :param search_query: Song and artist to search for
        :return: YouTube video URL
        """
        # If we already know the quota is exceeded, fail fast
        if self.quota_exceeded:
            raise Exception("YouTube API quota exceeded. Please try again tomorrow.")
            
        # Refine search query to get better matches for songs
        if " - " in search_query or " – " in search_query:
            # The search query already contains artist, just add "official music video"
            refined_query = f"{search_query} official music video"
        else:
            # Add some context for better results
            refined_query = f"{search_query} music song"

        logger.info(f"Searching YouTube for: {refined_query}")
        
        try:
            search_response = self.youtube.search().list(
                q=refined_query,
                part='id,snippet',
                maxResults=1,
                type='video',
                videoEmbeddable='true',
                safeSearch='moderate',
                videoDefinition='high'
            ).execute()

            if not search_response.get('items'):
                # Try a more relaxed search if no results found
                logger.info(f"No results with refined query, trying original query: {search_query}")
                search_response = self.youtube.search().list(
                    q=search_query,  # Use original query
                    part='id',
                    maxResults=1,
                    type='video'
                ).execute()
                
                if not search_response.get('items'):
                    logger.warning(f"No YouTube results found for: {search_query}")
                    return ""  # Return empty string instead of raising an exception

            video_id = search_response['items'][0]['id']['videoId']
            video_url = f"https://www.youtube.com/watch?v={video_id}"
            logger.info(f"Found YouTube video: {video_url}")
            return video_url

        except HttpError as e:
            error_message = str(e)
            logger.error(f"YouTube API error during search: {error_message}")
            
            # Check specifically for quota exceeded errors
            if "quotaExceeded" in error_message:
                self.quota_exceeded = True
                raise Exception("YouTube API quota exceeded. Please try again tomorrow.")
            
            # For other API errors, return empty string instead of failing
            return ""
            
        except Exception as e:
            logger.error(f"Error fetching YouTube link: {str(e)}")
            return ""