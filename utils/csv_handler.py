import pandas as pd

def load_csv(file):
    """
    Load and validate CSV file
    """
    try:
        df = pd.read_csv(file)
        required_columns = ['Playlist', 'Song', 'Artist']
        
        # Validate required columns
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise ValueError(
                f"Missing required columns: {', '.join(missing_columns)}"
            )
        
        # Add YouTube_Link column if it doesn't exist
        if 'YouTube_Link' not in df.columns:
            df['YouTube_Link'] = ''
            
        return df
    
    except pd.errors.EmptyDataError:
        raise ValueError("The uploaded CSV file is empty")
    except pd.errors.ParserError:
        raise ValueError("Error parsing CSV file. Please check the format")
    except Exception as e:
        raise Exception(f"Error loading CSV: {str(e)}")

def save_csv(df, filename):
    """
    Save DataFrame to CSV
    """
    try:
        df.to_csv(filename, index=False)
    except Exception as e:
        raise Exception(f"Error saving CSV: {str(e)}")
