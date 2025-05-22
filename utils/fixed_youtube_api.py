from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import httplib2
import logging
import time
import random

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
        # Create HTTP object with timeout
        http = httplib2.Http(timeout=30)  # 30 second timeout
        self.youtube = build('youtube', 'v3', developerKey=api_key, http=http)
        self.quota_exceeded = False
        self.last_request_time = 0
        self.min_request_interval = 0.1  # 100ms between requests
    
    def _rate_limit(self):
        """Implement basic rate limiting to avoid hitting API limits"""
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time
        
        if time_since_last_request < self.min_request_interval:
            sleep_time = self.min_request_interval - time_since_last_request
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    def _retry_request(self, request_func, max_retries=3):
        """Retry API requests with exponential backoff"""
        for attempt in range(max_retries):
            try:
                self._rate_limit()
                return request_func()
            except HttpError as e:
                error_message = str(e)
                
                # Don't retry quota exceeded errors
                if "quotaExceeded" in error_message:
                    self.quota_exceeded = True
                    raise Exception("YouTube API quota exceeded. Please try again tomorrow.")
                
                # Retry on rate limit or server errors
                if attempt < max_retries - 1 and ("rateLimitExceeded" in error_message or "backendError" in error_message):
                    wait_time = (2 ** attempt) + random.uniform(0, 1)
                    logger.warning(f"YouTube API error (attempt {attempt + 1}), retrying in {wait_time:.1f}s: {error_message}")
                    time.sleep(wait_time)
                    continue
                else:
                    raise
            except Exception as e:
                if attempt < max_retries - 1:
                    wait_time = (2 ** attempt) + random.uniform(0, 1)
                    logger.warning(f"YouTube API error (attempt {attempt + 1}), retrying in {wait_time:.1f}s: {str(e)}")
                    time.sleep(wait_time)
                    continue
                else:
                    raise
        
    def verify_connection(self):
        """
        Verify the YouTube API connection is working properly
        Returns (success, message) tuple
        """
        try:
            def _make_test_request():
                return self.youtube.videos().list(
                    part='snippet',
                    chart='mostPopular',
                    maxResults=1,
                    regionCode='US'
                ).execute()
            
            # Use retry logic for the API call
            response = self._retry_request(_make_test_request)
            
            # Check if we got any items in the response
            if 'items' in response and len(response['items']) > 0:
                logger.info("YouTube API connection successful")
                return True, "API connection successful"
            else:
                logger.warning("YouTube API returned empty response")
                return False, "API returned empty response"
                
        except Exception as e:
            error_message = str(e)
            logger.error(f"YouTube API error: {error_message}")
            
            # Check specifically for quota exceeded errors
            if "quotaExceeded" in error_message or "quota exceeded" in error_message.lower():
                self.quota_exceeded = True
                logger.warning("YouTube API quota exceeded")
                return False, f"API error: {error_message}"
            
            return False, f"API error: {error_message}"

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
            def _make_search_request():
                return self.youtube.search().list(
                    q=refined_query,
                    part='id,snippet',
                    maxResults=1,
                    type='video',
                    videoEmbeddable='true',
                    safeSearch='moderate',
                    videoDefinition='high'
                ).execute()

            search_response = self._retry_request(_make_search_request)

            if not search_response.get('items'):
                # Try a more relaxed search if no results found
                logger.info(f"No results with refined query, trying original query: {search_query}")
                
                def _make_fallback_request():
                    return self.youtube.search().list(
                        q=search_query,  # Use original query
                        part='id',
                        maxResults=1,
                        type='video'
                    ).execute()
                
                search_response = self._retry_request(_make_fallback_request)
                
                if not search_response.get('items'):
                    logger.warning(f"No YouTube results found for: {search_query}")
                    return ""  # Return empty string instead of raising an exception

            video_id = search_response['items'][0]['id']['videoId']
            video_url = f"https://www.youtube.com/watch?v={video_id}"
            logger.info(f"Found YouTube video: {video_url}")
            return video_url

        except Exception as e:
            error_message = str(e)
            logger.error(f"Error fetching YouTube link: {error_message}")
            
            # Check specifically for quota exceeded errors
            if "quotaExceeded" in error_message or "quota exceeded" in error_message.lower():
                self.quota_exceeded = True
                raise Exception("YouTube API quota exceeded. Please try again tomorrow.")
            
            # For other API errors, return empty string instead of failing
            return ""