# Playlist Blog Generator Deployment Guide

This guide explains how to set up your Moments & Memories Playlist Blog Generator for both local development and Streamlit Cloud deployment.

## Local Development Setup

1. **Environment Variables**: Create a `.env` file in the root of your project with the following secrets:

```
OPENAI_API_KEY=your_openai_api_key
SPOTIFY_CLIENT_ID=your_spotify_client_id
SPOTIFY_CLIENT_SECRET=your_spotify_client_secret
WORDPRESS_API_URL=your_wordpress_url
WORDPRESS_USERNAME=your_wordpress_username
WORDPRESS_PASSWORD=your_wordpress_password
YOUTUBE_API_KEY=your_youtube_api_key
```

2. **Run the Application**: Use the following command to run the application locally:

```
streamlit run main.py
```

## Streamlit Cloud Deployment

1. **Create a Streamlit Cloud Account**: Go to [Streamlit Cloud](https://streamlit.io/cloud) and sign up for an account if you haven't already.

2. **Connect Your GitHub Repository**: Link your GitHub repository containing this project to Streamlit Cloud.

3. **Configure Secrets**: In the Streamlit Cloud dashboard:
   - Select your app
   - Go to "Settings" > "Secrets"
   - Add the following secrets in the specified format:

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

4. **Deploy**: 
   - Configure your app to use `main.py` as the entrypoint
   - Important: Do not include custom port or address settings in your `.streamlit/config.toml` file when deploying to Streamlit Cloud, as it can cause deployment errors
   - Click "Deploy" and Streamlit Cloud will handle the rest of the process

5. **Troubleshooting Deployment**:
   - If you get health check errors during deployment, make sure there's no `.streamlit/config.toml` file with custom server settings
   - Verify that all your dependencies are properly listed in requirements.txt or pyproject.toml
   - Check the deployment logs for specific error messages

## Folder Structure

- `/blogs`: Stores generated blog post files
- `/utils`: Contains API integration modules for OpenAI, WordPress, Spotify, and YouTube
- `.streamlit/config.toml`: Contains Streamlit configuration settings

## Key Features

- Process playlists from CSV files
- Fetch YouTube links for songs
- Find matching Spotify playlists
- Generate professional blog posts with AI
- Customize blog style and content
- Publish directly to WordPress (as drafts)
- Revamp existing WordPress posts

## Troubleshooting

- **API Connection Issues**: Verify your API keys are correctly set in your secrets.
- **Streamlit Cloud Secrets**: Double-check the secret format follows the nested structure shown above.
- **WordPress API**: Ensure your WordPress site has REST API and Application Passwords enabled.