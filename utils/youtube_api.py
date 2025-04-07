from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

class YouTubeAPI:
    def __init__(self, api_key):
        if not api_key:
            raise ValueError("YouTube API key is required")
        self.youtube = build('youtube', 'v3', developerKey=api_key)
        
    def verify_connection(self):
        """
        Verify the YouTube API connection is working properly
        Returns True if successful, False otherwise
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
                # Return the full response for debugging
                return True, "API connection successful"
            else:
                return False, "API returned empty response"
                
        except Exception as e:
            return False, f"API error: {str(e)}"

    def get_video_link(self, search_query):
        """
        Search for a video and return its link with more specific search terms
        """
        # Refine search query to get better matches for songs
        if " - " in search_query or " – " in search_query:
            # The search query already contains artist, just add "official music video"
            refined_query = f"{search_query} official music video"
        else:
            # Add some context for better results
            refined_query = f"{search_query} music song"

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
                search_response = self.youtube.search().list(
                    q=search_query,  # Use original query
                    part='id',
                    maxResults=1,
                    type='video'
                ).execute()
                
                if not search_response.get('items'):
                    raise ValueError(f"No YouTube results found for: {search_query}")

            video_id = search_response['items'][0]['id']['videoId']
            return f"https://www.youtube.com/watch?v={video_id}"

        except HttpError as e:
            raise Exception(f"YouTube API error: {str(e)}")
        except Exception as e:
            raise Exception(f"Error fetching YouTube link: {str(e)}")
