import pandas as pd
import numpy as np

def load_csv(file):
    """
    Load and validate CSV file with the wedding DJ playlist format
    """
    try:
        # Read CSV without headers since our format is custom
        # Additional columns for Spotify_Link and any future data
        df = pd.read_csv(file, header=None, names=['Entry', 'Song', 'Artist', 'YouTube_Link', 'Spotify_Link', 'Notes'], 
                         usecols=range(6), na_values=['nan'], keep_default_na=True)

        # Initialize playlist tracking
        current_playlist = None
        playlist_rows = []
        playlists_data = []

        # Process rows to identify playlists and their songs
        for idx, row in df.iterrows():
            if pd.notna(row['Entry']) and 'Wedding Cocktail Hour' in str(row['Entry']):
                # If we have a previous playlist, save it
                if current_playlist and playlist_rows:
                    playlist_df = pd.DataFrame(playlist_rows)
                    playlist_df['Playlist'] = current_playlist
                    playlists_data.append(playlist_df)

                # Start new playlist
                current_playlist = row['Entry']
                playlist_rows = []
            elif pd.notna(row['Song']) and pd.notna(row['Artist']):
                # Add song to current playlist with all available data
                song_data = {
                    'Song': row['Song'],
                    'Artist': row['Artist'],
                    'YouTube_Link': row['YouTube_Link'] if pd.notna(row['YouTube_Link']) else '',
                    'Spotify_Link': row['Spotify_Link'] if pd.notna(row['Spotify_Link']) else '',
                    'Notes': row['Notes'] if pd.notna(row['Notes']) else ''
                }
                playlist_rows.append(song_data)

        # Add the last playlist
        if current_playlist and playlist_rows:
            playlist_df = pd.DataFrame(playlist_rows)
            playlist_df['Playlist'] = current_playlist
            playlists_data.append(playlist_df)

        # Combine all playlists
        if not playlists_data:
            raise ValueError("No valid playlists found in the CSV file")

        final_df = pd.concat(playlists_data, ignore_index=True)
        
        # Ensure all expected columns exist (for compatibility with older CSV files)
        for col in ['YouTube_Link', 'Spotify_Link', 'Notes']:
            if col not in final_df.columns:
                final_df[col] = ''
                
        return final_df

    except pd.errors.EmptyDataError:
        raise ValueError("The uploaded CSV file is empty")
    except pd.errors.ParserError:
        raise ValueError("Error parsing CSV file. Please check the format")
    except Exception as e:
        raise Exception(f"Error loading CSV: {str(e)}")

def save_csv(df, filename):
    """
    Save DataFrame back to CSV in the original format
    """
    try:
        # Group by playlist
        grouped = df.groupby('Playlist')

        # Create output rows
        output_rows = []

        for playlist_name, group in grouped:
            # Add playlist header
            output_rows.append([playlist_name, '', '', '', '', ''])

            # Add songs with all available data
            for _, row in group.iterrows():
                output_row = [
                    f"{row['Song']}-{row['Artist']}", 
                    row['Song'],
                    row['Artist'],
                    row['YouTube_Link'] if 'YouTube_Link' in row and pd.notna(row['YouTube_Link']) else '',
                    row['Spotify_Link'] if 'Spotify_Link' in row and pd.notna(row['Spotify_Link']) else '',
                    row['Notes'] if 'Notes' in row and pd.notna(row['Notes']) else ''
                ]
                output_rows.append(output_row)

            # Add separator
            output_rows.append(['', '', '', '', '', ''])

        # Convert to DataFrame and save
        output_df = pd.DataFrame(output_rows, columns=['Entry', 'Song', 'Artist', 'YouTube_Link', 'Spotify_Link', 'Notes'])
        output_df.to_csv(filename, index=False, header=False)

    except Exception as e:
        raise Exception(f"Error saving CSV: {str(e)}")

def create_empty_playlist_df():
    """
    Create an empty playlist DataFrame with the required columns
    """
    return pd.DataFrame(columns=['Song', 'Artist', 'YouTube_Link', 'Spotify_Link', 'Notes', 'Playlist'])