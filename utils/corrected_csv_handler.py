import pandas as pd
import numpy as np
import logging
import re

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_csv(file):
    """
    Load and validate CSV file with the wedding DJ playlist format
    
    The format is:
    - Playlist titles in column A (starting with 3 digits)
    - Songs listed under each playlist with song+artist in column A
    - Column B contains just the song name
    - Column C contains just the artist name
    - Column D contains YouTube links (if available)
    - Column E should contain Spotify playlist links (next to playlist titles)
    """
    try:
        # Handle both file paths (strings) and file objects
        if isinstance(file, str):
            # It's a file path
            import os
            if os.path.exists(file):
                file_size = os.path.getsize(file)
                # Limit file size to 50MB
                max_size = 50 * 1024 * 1024  # 50MB
                if file_size > max_size:
                    raise ValueError(f"CSV file too large ({file_size / 1024 / 1024:.1f}MB). Maximum allowed size is 50MB.")
            else:
                raise ValueError(f"File not found: {file}")
        else:
            # It's a file object - check file size first to prevent memory exhaustion
            file.seek(0, 2)  # Move to end of file
            file_size = file.tell()
            file.seek(0)  # Reset to beginning
            
            # Limit file size to 50MB
            max_size = 50 * 1024 * 1024  # 50MB
            if file_size > max_size:
                raise ValueError(f"CSV file too large ({file_size / 1024 / 1024:.1f}MB). Maximum allowed size is 50MB.")
        
        # Read the CSV file without headers with proper encoding handling
        try:
            df_raw = pd.read_csv(file, header=None, encoding='utf-8')
        except UnicodeDecodeError:
            logger.warning("UTF-8 encoding failed, trying latin-1")
            if not isinstance(file, str):
                file.seek(0)  # Reset file position only for file objects
            df_raw = pd.read_csv(file, header=None, encoding='latin-1')
        except pd.errors.EmptyDataError:
            logger.error("CSV file is empty")
            raise ValueError("CSV file is empty or has no data")
        except pd.errors.ParserError as e:
            logger.error(f"CSV parsing error: {str(e)}")
            raise ValueError(f"Invalid CSV format: {str(e)}")
        
        logger.info(f"Read {len(df_raw)} rows from CSV")
        
        # Initialize a list to store the processed data
        processed_data = []
        
        # Track the current playlist and its Spotify link
        current_playlist = None
        spotify_link = None
        
        # Regular expression to identify playlist headers (start with 3 digits)
        playlist_regex = re.compile(r'^\d{3}\s+(.+)$')
        
        # Process each row in the CSV
        for _, row in df_raw.iterrows():
            row_values = row.tolist()
            
            # Ensure we have at least 4 columns
            while len(row_values) < 4:
                row_values.append(None)
                
            # Check if this is a playlist header row (matches the pattern in column A)
            if pd.notna(row_values[0]) and isinstance(row_values[0], str):
                match = playlist_regex.match(row_values[0])
                if match:
                    # This is a playlist header row
                    current_playlist = row_values[0]
                    
                    # Check if there's a Spotify link in column E
                    if len(row_values) > 4 and pd.notna(row_values[4]) and isinstance(row_values[4], str):
                        spotify_link = row_values[4]
                    else:
                        spotify_link = ""
                        
                    logger.info(f"Found playlist: {current_playlist}, Spotify: {spotify_link}")
                    continue
            
            # If we have a playlist and this is a song row (should have values in columns A, B, and C)
            if current_playlist and pd.notna(row_values[0]) and pd.notna(row_values[1]) and pd.notna(row_values[2]):
                # Extract data
                song_with_artist = row_values[0]
                song_title = row_values[1]
                artist = row_values[2]
                
                # YouTube link in column D if available
                youtube_link = row_values[3] if pd.notna(row_values[3]) else ""
                
                # Create a row for our processed dataframe
                processed_data.append({
                    'Playlist': current_playlist,
                    'Song': song_title,
                    'Artist': artist,
                    'Song_Artist': song_with_artist,
                    'YouTube_Link': youtube_link,
                    'Spotify_Link': spotify_link
                })
        
        # Create a DataFrame from the processed data
        df = pd.DataFrame(processed_data)
        
        # Check if we got any data
        if len(df) == 0:
            logger.error("No valid data found in CSV. Either the format is incorrect or the file is empty.")
            raise ValueError("No valid data found in CSV")
            
        logger.info(f"Successfully processed {len(df)} songs across {df['Playlist'].nunique()} playlists")
        return df
        
    except Exception as e:
        logger.error(f"Error loading CSV file: {str(e)}")
        raise

def save_csv(df, filename):
    """
    Save DataFrame back to CSV in the original format
    """
    try:
        # Group by playlist
        playlists = df['Playlist'].unique()
        
        # Create a list to store all rows for the CSV
        csv_rows = []
        
        # Process each playlist
        for playlist in playlists:
            # Get all songs for this playlist
            playlist_df = df[df['Playlist'] == playlist]
            
            # Get the Spotify link for this playlist (all rows should have the same value)
            spotify_link = ""
            if 'Spotify_Link' in playlist_df.columns and not playlist_df['Spotify_Link'].empty:
                spotify_link = playlist_df['Spotify_Link'].iloc[0]
            
            # Add the playlist header row
            row = [playlist, "", "", "", spotify_link]  # First col: playlist, Last col: Spotify link
            csv_rows.append(row)
            
            # Add each song row
            for _, song_row in playlist_df.iterrows():
                # Create proper song-artist format with validation
                song_artist = ""
                if 'Song_Artist' in song_row and pd.notna(song_row['Song_Artist']):
                    song_artist = str(song_row['Song_Artist'])
                elif pd.notna(song_row['Song']) and pd.notna(song_row['Artist']):
                    song_artist = f"{song_row['Song']} - {song_row['Artist']}"
                else:
                    song_artist = "Unknown Song - Unknown Artist"
                
                row = [
                    song_artist,
                    song_row['Song'] if pd.notna(song_row['Song']) else "Unknown Song",
                    song_row['Artist'] if pd.notna(song_row['Artist']) else "Unknown Artist",
                    song_row['YouTube_Link'] if pd.notna(song_row['YouTube_Link']) else "",
                    ""  # Empty for Spotify link in song rows
                ]
                csv_rows.append(row)
            
            # Add a blank row after each playlist
            csv_rows.append(["", "", "", "", ""])
        
        # Create a DataFrame from the rows
        output_df = pd.DataFrame(csv_rows)
        
        # Save to CSV without headers
        output_df.to_csv(filename, index=False, header=False)
        
        logger.info(f"Successfully saved {len(df)} songs to {filename}")
        return True
        
    except Exception as e:
        logger.error(f"Error saving CSV file: {str(e)}")
        raise

def create_empty_playlist_df():
    """
    Create an empty playlist DataFrame with the required columns
    """
    return pd.DataFrame(columns=['Playlist', 'Song', 'Artist', 'Song_Artist', 'YouTube_Link', 'Spotify_Link'])