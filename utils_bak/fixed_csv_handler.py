import pandas as pd
import numpy as np
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_csv(file):
    """
    Load and validate CSV file with the wedding DJ playlist format
    
    The format is:
    - First row is the playlist name (with empty columns after it)
    - Then rows with song entries (song title, artist, YouTube link)
    - Empty rows separate different playlists
    """
    try:
        # Read the CSV file without headers initially
        df_raw = pd.read_csv(file, header=None)
        logger.info(f"Read {len(df_raw)} rows from CSV")
        
        # Initialize a list to store the processed data
        processed_data = []
        
        # Track the current playlist
        current_playlist = None
        
        # Process each row in the CSV
        for _, row in df_raw.iterrows():
            # Convert row to list for easier handling
            row_values = row.tolist()
            
            # Skip completely empty rows
            if all(pd.isna(value) for value in row_values):
                continue
                
            # Check if this is a playlist header row (first column has value, others are empty)
            if pd.notna(row_values[0]) and all(pd.isna(value) for value in row_values[1:]):
                current_playlist = row_values[0]
                logger.info(f"Found playlist: {current_playlist}")
                continue
                
            # If we have a playlist and this is a song row (should have at least 2 non-empty values)
            if current_playlist and sum(1 for value in row_values if pd.notna(value)) >= 2:
                # Get song details - expecting format: SongTitle-Artist in column 0
                # and song title, artist in columns 1 and 2
                if len(row_values) >= 3:
                    song_title = row_values[1] if pd.notna(row_values[1]) else ""
                    artist = row_values[2] if pd.notna(row_values[2]) else ""
                    
                    # YouTube link might be in column 3
                    youtube_link = row_values[3] if len(row_values) > 3 and pd.notna(row_values[3]) else ""
                    
                    # Create a row for our processed dataframe
                    processed_data.append({
                        'Playlist': current_playlist,
                        'Song': song_title,
                        'Artist': artist,
                        'YouTube_Link': youtube_link
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
            # Add the playlist name row
            csv_rows.append([playlist, "", "", ""])
            
            # Get all songs for this playlist
            playlist_df = df[df['Playlist'] == playlist]
            
            # Add each song row
            for _, row in playlist_df.iterrows():
                song_artist = f"{row['Song']}-{row['Artist']}"
                csv_rows.append([song_artist, row['Song'], row['Artist'], row.get('YouTube_Link', '')])
            
            # Add a blank row after each playlist
            csv_rows.append(["", "", "", ""])
        
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
    return pd.DataFrame(columns=['Playlist', 'Song', 'Artist', 'YouTube_Link'])