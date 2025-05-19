"""
Secrets manager to handle both local environment variables and Streamlit Cloud secrets.
This allows the app to run both locally and when deployed to Streamlit Cloud.
"""
import os
import streamlit as st

def get_secret(key, default=None):
    """
    Get a secret from environment variables or Streamlit secrets.
    
    Args:
        key: The secret key to retrieve
        default: Default value if secret is not found
        
    Returns:
        The secret value or default if not found
    """
    # Try to get from environment variables first (local development)
    value = os.environ.get(key)
    
    # If not found in environment, try Streamlit secrets (cloud deployment)
    if value is None:
        try:
            # Convert key format if needed (e.g., OPENAI_API_KEY -> openai.OPENAI_API_KEY)
            if key == "OPENAI_API_KEY":
                value = st.secrets.get("openai", {}).get("OPENAI_API_KEY")
            elif key == "SPOTIFY_CLIENT_ID":
                value = st.secrets.get("spotify", {}).get("SPOTIFY_CLIENT_ID")
            elif key == "SPOTIFY_CLIENT_SECRET":
                value = st.secrets.get("spotify", {}).get("SPOTIFY_CLIENT_SECRET")
            elif key == "WORDPRESS_API_URL":
                value = st.secrets.get("wordpress", {}).get("WORDPRESS_API_URL")
            elif key == "WORDPRESS_USERNAME":
                value = st.secrets.get("wordpress", {}).get("WORDPRESS_USERNAME")
            elif key == "WORDPRESS_PASSWORD":
                value = st.secrets.get("wordpress", {}).get("WORDPRESS_PASSWORD")
            elif key == "YOUTUBE_API_KEY":
                value = st.secrets.get("youtube", {}).get("YOUTUBE_API_KEY")
            else:
                # For any other keys, try direct access
                value = st.secrets.get(key)
        except:
            # If Streamlit secrets are not configured (running locally), this will fail
            pass
    
    return value if value is not None else default