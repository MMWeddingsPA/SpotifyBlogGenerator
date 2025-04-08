import os
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import json

# Get credentials from environment variables
client_id = os.getenv("SPOTIFY_CLIENT_ID")
client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")

if not client_id or not client_secret:
    print("Error: Spotify credentials not found in environment variables")
    exit(1)
    
# Initialize Spotify client
auth_manager = SpotifyClientCredentials(
    client_id=client_id,
    client_secret=client_secret
)
spotify = spotipy.Spotify(auth_manager=auth_manager)

# Test user ID
user_id = "bm8eje5tcjj9eazftizqoikwm"

try:
    # Get the user's playlists
    print(f"Fetching playlists for user ID: {user_id}")
    playlists = spotify.user_playlists(user_id)
    
    # Count and show some playlist names
    total_playlists = playlists['total']
    print(f"Found {total_playlists} playlists")
    
    # Display the first 10 playlist names
    print("\nFirst 10 playlists:")
    count = 0
    playlist_names = []
    
    while playlists and count < 10:
        items = playlists['items']
        for i, playlist in enumerate(items):
            if count >= 10:
                break
            print(f"{count+1}. {playlist['name']} - {playlist['external_urls']['spotify']}")
            playlist_names.append(playlist['name'])
            count += 1
            
        if playlists['next'] and count < 10:
            playlists = spotify.next(playlists)
        else:
            break
            
    # Search for a specific playlist
    test_playlist = "The Beach Breeze Wedding Cocktail Hour"
    print(f"\nSearching for playlist: '{test_playlist}'")
    
    # Reset and search all playlists
    playlists = spotify.user_playlists(user_id)
    found = False
    
    while playlists and not found:
        for playlist in playlists['items']:
            name = playlist['name']
            if test_playlist.lower() in name.lower():
                print(f"✅ Found match: '{name}' - {playlist['external_urls']['spotify']}")
                found = True
                break
        
        if not found and playlists['next']:
            playlists = spotify.next(playlists)
        else:
            break
    
    if not found:
        print(f"❌ Could not find playlist '{test_playlist}'")
        
except Exception as e:
    print(f"Error: {str(e)}")