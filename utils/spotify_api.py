import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

class SpotifyAPI:
    def __init__(self, client_id, client_secret):
        if not client_id or not client_secret:
            raise ValueError("Spotify client ID and secret are required")
        
        auth_manager = SpotifyClientCredentials(
            client_id=client_id,
            client_secret=client_secret
        )
        self.spotify = spotipy.Spotify(auth_manager=auth_manager)

    def get_playlist_link(self, user_id, playlist_name):
        """
        Find and return the Spotify playlist link by name
        """
        try:
            playlists = self.spotify.user_playlists(user_id)
            
            while playlists:
                for playlist in playlists['items']:
                    if playlist['name'].lower() == playlist_name.lower():
                        return playlist['external_urls']['spotify']
                
                if playlists['next']:
                    playlists = self.spotify.next(playlists)
                else:
                    break

            raise ValueError(f"Playlist '{playlist_name}' not found")

        except Exception as e:
            raise Exception(f"Error fetching Spotify playlist: {str(e)}")
