import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import re

class SpotifyAPI:
    def __init__(self, client_id, client_secret):
        if not client_id or not client_secret:
            raise ValueError("Spotify client ID and secret are required")

        auth_manager = SpotifyClientCredentials(
            client_id=client_id,
            client_secret=client_secret
        )
        self.spotify = spotipy.Spotify(auth_manager=auth_manager)

    def clean_playlist_name(self, playlist_name):
        """
        Clean playlist name by:
        1. Removing numeric prefix (e.g., '001 ')
        2. Removing 'Wedding Cocktail Hour' suffix
        3. Trimming whitespace
        """
        # Remove numeric prefix and any leading spaces
        cleaned_name = re.sub(r'^\d+\s*', '', playlist_name)

        # Remove "Wedding Cocktail Hour" suffix
        cleaned_name = cleaned_name.replace('Wedding Cocktail Hour', '').strip()

        return cleaned_name

    def get_playlist_link(self, user_id, playlist_name):
        """
        Find and return the Spotify playlist link by name
        """
        try:
            # Clean the input playlist name
            search_name = self.clean_playlist_name(playlist_name)
            playlists = self.spotify.user_playlists(user_id)

            while playlists:
                for playlist in playlists['items']:
                    # Clean each Spotify playlist name for comparison
                    spotify_name = playlist['name'].strip()

                    # Compare cleaned names (case-insensitive)
                    if spotify_name.lower() == search_name.lower():
                        return playlist['external_urls']['spotify']

                    # Try alternate formats (with/without "The")
                    if search_name.lower().startswith('the '):
                        alt_name = search_name[4:]  # Remove "The "
                    else:
                        alt_name = 'The ' + search_name

                    if spotify_name.lower() == alt_name.lower():
                        return playlist['external_urls']['spotify']

                if playlists['next']:
                    playlists = self.spotify.next(playlists)
                else:
                    break

            raise ValueError(f"Playlist '{search_name}' not found in Spotify account '{user_id}'")

        except Exception as e:
            raise Exception(f"Error fetching Spotify playlist: {str(e)}")