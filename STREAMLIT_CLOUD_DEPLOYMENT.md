# Streamlit Cloud Deployment Guide

## Fixing the "Localhost Health Check" Error

When deploying to Streamlit Cloud, you may encounter an error where the service fails during health checks. This usually happens because of port configuration issues. 

### Deployment Steps for Success

1. **Configuration File**
   - Make sure your `.streamlit/config.toml` file **only** contains theme settings:
   ```toml
   [theme]
   base = "light"
   primaryColor = "#D4AF37"
   backgroundColor = "#FFFFFF"
   secondaryBackgroundColor = "#F0F2F6"
   textColor = "#1A2A44"
   ```
   - Do NOT include any server settings like:
   ```toml
   [server]
   port = 5000
   address = "0.0.0.0"
   ```

2. **Streamlit Secrets**
   - Add your API credentials in the Streamlit Cloud secrets manager using this format:
   ```toml
   [openai]
   OPENAI_API_KEY = "your_openai_api_key"

   [spotify]
   SPOTIFY_CLIENT_ID = "your_spotify_client_id"
   SPOTIFY_CLIENT_SECRET = "your_spotify_client_secret"

   [wordpress]
   WORDPRESS_API_URL = "your_wordpress_url"
   WORDPRESS_USERNAME = "your_wordpress_username"
   WORDPRESS_PASSWORD = "your_wordpress_password"

   [youtube]
   YOUTUBE_API_KEY = "your_youtube_api_key"
   ```

3. **App Settings**
   - Set the main file to `main.py`
   - Do not set any custom command or port configurations in the Streamlit Cloud deployment settings

This setup ensures your app will run correctly on Streamlit Cloud without encountering the health check error.