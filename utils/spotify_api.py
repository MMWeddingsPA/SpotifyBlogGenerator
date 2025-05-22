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
        if playlist_name is None:
            return ""
        # Remove numeric prefix and any leading spaces
        cleaned_name = re.sub(r'^\d+\s*', '', str(playlist_name))
        return cleaned_name.strip()

    def get_playlist_tracks(self, playlist_id):
        """
        Get all tracks from a Spotify playlist by playlist ID
        :param playlist_id: Spotify playlist ID
        :return: List of track objects with name and artist information
        """
        try:
            # Get the playlist tracks
            results = self.spotify.playlist_tracks(playlist_id)
            tracks = results['items']
            
            # Continue fetching if there are more tracks
            while results['next']:
                results = self.spotify.next(results)
                tracks.extend(results['items'])
            
            # Extract track info
            track_info = []
            for item in tracks:
                track = item.get('track') if item else None
                if track and isinstance(track, dict):
                    # Safely extract track name and artists
                    track_name = track.get('name', '')
                    artists = track.get('artists', [])
                    
                    # Only add if we have valid data
                    if track_name and isinstance(artists, list):
                        track_info.append({
                            'name': track_name,
                            'artists': artists
                        })
            
            return track_info
        except Exception as e:
            print(f"Error fetching playlist tracks: {str(e)}")
            return []
            
    def get_playlist_link(self, user_id, playlist_name):
        """
        Find and return the Spotify playlist link by name
        """
        try:
            # Clean the input playlist name
            search_name = playlist_name.strip()
            print(f"Looking for Spotify playlist: '{search_name}'")
            
            # Try to get user playlists
            try:
                playlists = self.spotify.user_playlists(user_id)
                
                # Store all playlist names for debugging
                matching_names = []
                
                # First pass: Try exact match (case-insensitive)
                max_iterations = 100  # Prevent infinite loops
                iteration_count = 0
                
                while playlists and iteration_count < max_iterations:
                    iteration_count += 1
                    
                    # Validate playlists structure
                    if not isinstance(playlists, dict) or 'items' not in playlists:
                        break
                        
                    for playlist in playlists.get('items', []):
                        if not isinstance(playlist, dict):
                            continue
                            
                        # Get the Spotify playlist name
                        spotify_name = playlist.get('name', '').strip()
                        if spotify_name:
                            matching_names.append(spotify_name)
                        
                        # Compare names (case-insensitive)
                        if spotify_name.lower() == search_name.lower():
                            print(f"Found exact match: '{spotify_name}'")
                            external_urls = playlist.get('external_urls', {})
                            if isinstance(external_urls, dict) and 'spotify' in external_urls:
                                return external_urls['spotify']
    
                    # Get the next page of results if available
                    if playlists.get('next'):
                        playlists = self.spotify.next(playlists)
                    else:
                        break
                
                # Reset for second pass
                playlists = self.spotify.user_playlists(user_id)
                
                # Second pass: Try looking for the distinctive part of the name
                # For example: "The Fresh Takes Wedding Cocktail Hour" might be "Fresh Takes"
                base_name = search_name.split("Wedding Cocktail Hour")[0].strip()
                
                print(f"Trying with base name: '{base_name}'")
                iteration_count = 0
                
                while playlists and base_name and iteration_count < max_iterations:
                    iteration_count += 1
                    
                    # Validate playlists structure
                    if not isinstance(playlists, dict) or 'items' not in playlists:
                        break
                        
                    for playlist in playlists.get('items', []):
                        if not isinstance(playlist, dict):
                            continue
                            
                        spotify_name = playlist.get('name', '').strip()
                        
                        # Try partial matching
                        if spotify_name and base_name.lower() in spotify_name.lower():
                            print(f"Found partial match with base name: '{spotify_name}'")
                            external_urls = playlist.get('external_urls', {})
                            if isinstance(external_urls, dict) and 'spotify' in external_urls:
                                return external_urls['spotify']
                    
                    # Get the next page of results if available
                    if playlists.get('next'):
                        playlists = self.spotify.next(playlists)
                    else:
                        break
                
                # Third pass: Try broader fuzzy matching for special cases
                playlists = self.spotify.user_playlists(user_id)
                
                # Extract key terms from the playlist name (e.g., "Yacht Rock", "EDM", etc.)
                # This will help with "The Yacht Rock Wedding Cocktail Hour"
                key_terms = []
                if "Volume" in search_name:
                    volume_match = re.search(r'Volume\s+(\d+)', search_name)
                    if volume_match:
                        volume_num = volume_match.group(1)
                        key_terms.append(f"Vol. {volume_num}")
                        key_terms.append(f"Vol {volume_num}")
                        key_terms.append(f"Volume {volume_num}")
                
                # Add other distinctive words
                for word in search_name.split():
                    if word.lower() not in ['the', 'wedding', 'cocktail', 'hour', 'volume', 'and', 'of']:
                        key_terms.append(word)
                
                print(f"Trying with key terms: {key_terms}")
                while playlists and key_terms:
                    for playlist in playlists['items']:
                        spotify_name = playlist['name'].strip()
                        
                        # Count how many key terms match
                        match_count = 0
                        for term in key_terms:
                            if term.lower() in spotify_name.lower():
                                match_count += 1
                        
                        # If more than half the terms match, consider it a good match
                        if match_count >= len(key_terms) // 2 and match_count > 0:
                            print(f"Found fuzzy match with key terms: '{spotify_name}'")
                            return playlist['external_urls']['spotify']
                    
                    # Get the next page of results if available
                    if playlists['next']:
                        playlists = self.spotify.next(playlists)
                    else:
                        break
                
                # If we get here, no match was found
                available_names = ", ".join(matching_names[:10])
                if len(matching_names) > 10:
                    available_names += f" and {len(matching_names) - 10} more"
                    
                print(f"Available playlists: {available_names}")
                return None
                
            except Exception as e:
                print(f"Error accessing user playlists: {str(e)}")
                
                # If user_id not found, try a search API call instead
                query = f"user:{user_id} playlist:{search_name}"
                print(f"Trying search with query: {query}")
                
                try:
                    results = self.spotify.search(q=query, type='playlist', limit=10)
                    playlists = results.get('playlists', {}).get('items', [])
                    
                    if playlists:
                        # Try to find the most similar playlist
                        print(f"Found {len(playlists)} playlists in search results")
                        best_match = None
                        best_score = 0
                        
                        for playlist in playlists:
                            spotify_name = playlist['name'].strip()
                            score = 0
                            
                            # Calculate a similarity score
                            if spotify_name.lower() == search_name.lower():
                                score = 100  # Perfect match
                            elif search_name.lower() in spotify_name.lower():
                                score = 80  # Contains full name
                            elif any(term.lower() in spotify_name.lower() for term in search_name.split()):
                                score = 50  # Contains some words
                            
                            if score > best_score:
                                best_score = score
                                best_match = playlist
                        
                        if best_match and best_score >= 50:
                            print(f"Found search match: '{best_match['name']}' with score {best_score}")
                            return best_match['external_urls']['spotify']
                except Exception as search_error:
                    print(f"Search failed: {str(search_error)}")
                
                # If all attempts fail, return None
                return None

        except Exception as e:
            print(f"Error in Spotify playlist lookup: {str(e)}")
            return None