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
        Clean playlist name by removing numeric prefix while preserving the full name
        Example: '006 The Smooth Sail Wedding Cocktail Hour' -> 'The Smooth Sail Wedding Cocktail Hour'
        """
        # Remove numeric prefix and any leading spaces
        cleaned_name = re.sub(r'^\d+\s*', '', str(playlist_name))
        return cleaned_name.strip()

    def get_playlist_link(self, user_id, playlist_name):
        """
        Find and return the Spotify playlist link by name
        """
        try:
            # Clean the input playlist name
            search_name = self.clean_playlist_name(playlist_name)
            playlists = self.spotify.user_playlists(user_id)
            
            # Debug information
            print(f"Looking for cleaned playlist name: '{search_name}'")
            matching_names = []
            
            while playlists:
                for playlist in playlists['items']:
                    # Clean each Spotify playlist name for comparison
                    spotify_name = playlist['name'].strip()
                    matching_names.append(spotify_name)
                    
                    # Compare cleaned names (case-insensitive)
                    if spotify_name.lower() == search_name.lower():
                        return playlist['external_urls']['spotify']

                if playlists['next']:
                    playlists = self.spotify.next(playlists)
                else:
                    break
            
            # Try partial matching as fallback
            playlists = self.spotify.user_playlists(user_id)
            while playlists:
                for playlist in playlists['items']:
                    spotify_name = playlist['name'].strip()
                    
                    # Try more fuzzy matching
                    if (search_name.lower() in spotify_name.lower() or 
                        spotify_name.lower() in search_name.lower()):
                        return playlist['external_urls']['spotify']
                
                if playlists['next']:
                    playlists = self.spotify.next(playlists)
                else:
                    break

            # If we get here, no match was found
            available_names = ", ".join(matching_names[:10])
            if len(matching_names) > 10:
                available_names += f" and {len(matching_names) - 10} more"
                
            raise ValueError(f"Playlist '{search_name}' not found in Spotify account '{user_id}'. Available playlists: {available_names}")

        except Exception as e:
            raise Exception(f"Error fetching Spotify playlist: {str(e)}")