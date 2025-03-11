from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

class YouTubeAPI:
    def __init__(self, api_key):
        if not api_key:
            raise ValueError("YouTube API key is required")
        self.youtube = build('youtube', 'v3', developerKey=api_key)

    def get_video_link(self, search_query):
        """
        Search for a video and return its link
        """
        try:
            search_response = self.youtube.search().list(
                q=search_query,
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
