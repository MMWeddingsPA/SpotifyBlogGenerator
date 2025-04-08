import requests
import base64
import os
import json
import logging
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class WordPressAPI:
    def __init__(self, api_url, username, password):
        """
        Initialize WordPress API client
        :param api_url: WordPress API URL (e.g., https://yoursite.com/wp-json/wp/v2)
        :param username: WordPress username or application password name
        :param password: WordPress password or application password
        """
        if not api_url or not username or not password:
            raise ValueError("WordPress API URL, username, and password are required")
        
        if api_url is None or username is None or password is None:
            raise ValueError("WordPress API URL, username, and password are required")
        
        # Log the initialization (without credentials)
        logger.info(f"Initializing WordPress API with URL: {api_url}")
        logger.info(f"Username length: {len(username)}")
        logger.info(f"Password available: {'Yes' if password else 'No'}")
            
        # Make sure the API URL is properly formatted
        self.api_url = api_url.rstrip('/')
        if not self.api_url.endswith('/wp/v2'):
            # If URL doesn't end with /wp/v2, make sure it's added
            if not self.api_url.endswith('/wp-json'):
                self.api_url = f"{self.api_url}/wp-json/wp/v2"
            else:
                self.api_url = f"{self.api_url}/wp/v2"
                
        logger.info(f"Formatted API URL: {self.api_url}")
        
        self.username = username
        self.password = password
        self.auth_header = self._get_auth_header()
        
        # Test connection
        self.test_connection()
    
    def test_connection(self):
        """Test the connection to WordPress API"""
        try:
            # Try to get a list of posts (simple request)
            endpoint = f"{self.api_url}/posts?per_page=1"
            logger.info(f"Testing connection to: {endpoint}")
            
            response = requests.get(
                endpoint,
                headers=self.auth_header,
                timeout=10
            )
            
            logger.info(f"Connection test response code: {response.status_code}")
            
            if response.status_code == 200:
                logger.info("WordPress API connection successful")
                return True
            else:
                logger.error(f"WordPress API connection failed: {response.status_code}")
                logger.error(f"Response: {response.text}")
                return False
        except Exception as e:
            logger.error(f"WordPress API connection test failed: {str(e)}")
            return False
    
    def _get_auth_header(self):
        """Create authorization header using basic auth"""
        credentials = f"{self.username}:{self.password}"
        token = base64.b64encode(credentials.encode()).decode('utf-8')
        auth_header = {'Authorization': f'Basic {token}'}
        logger.info("Created authorization header successfully")
        return auth_header
    
    def create_post(self, title, content, status='draft', featured_media=None, categories=None, tags=None):
        """
        Create a new post in WordPress
        :param title: Post title
        :param content: Post content (can include HTML)
        :param status: Post status (draft, publish, pending, private)
        :param featured_media: Featured image ID (optional)
        :param categories: List of category IDs (optional)
        :param tags: List of tag IDs or names (optional)
        :return: Post details if successful, error message if failed
        """
        try:
            endpoint = f"{self.api_url}/posts"
            logger.info(f"Creating post with title: {title[:30]}...")
            logger.info(f"Post endpoint: {endpoint}")
            
            # Prepare post data
            post_data = {
                'title': title,
                'content': content,
                'status': status,
            }
            
            # Log the formatted data
            logger.info(f"Title: {title[:30]}...")
            logger.info(f"Content length: {len(content) if content else 0} characters")
            logger.info(f"Status: {status}")
            
            # Add optional fields if provided
            if featured_media:
                post_data['featured_media'] = featured_media
            
            if categories:
                post_data['categories'] = categories
            
            if tags:
                post_data['tags'] = tags
            
            # Log the request
            logger.info(f"Sending POST request to {endpoint}")
            logger.info(f"Headers: {self.auth_header.keys()}")
            logger.info(f"Post data keys: {post_data.keys()}")
            
            # Make API request with longer timeout
            response = requests.post(
                endpoint,
                headers=self.auth_header,
                json=post_data,
                timeout=20
            )
            
            # Log the response
            logger.info(f"WordPress API response code: {response.status_code}")
            
            # Check for success
            if response.status_code in (200, 201):
                logger.info("Post created successfully!")
                return {
                    'success': True,
                    'post_id': response.json().get('id'),
                    'post_url': response.json().get('link'),
                    'edit_url': response.json().get('_links', {}).get('wp:action-edit', [{}])[0].get('href'),
                }
            else:
                logger.error(f"Error creating post: {response.status_code}")
                logger.error(f"Response: {response.text}")
                
                # Check for specific error types
                if response.status_code == 403:
                    logger.error("403 Forbidden error - likely an authentication issue")
                    # Try to parse the error response
                    try:
                        error_data = response.json()
                        logger.error(f"Error details: {json.dumps(error_data, indent=2)}")
                    except:
                        pass
                
                return {
                    'success': False,
                    'error': f"Error {response.status_code}: {response.text}"
                }
                
        except Exception as e:
            logger.error(f"Exception creating WordPress post: {str(e)}")
            return {
                'success': False,
                'error': f"Error creating WordPress post: {str(e)}"
            }
            
    def get_categories(self):
        """Get all available categories"""
        try:
            endpoint = f"{self.api_url}/categories"
            response = requests.get(endpoint, headers=self.auth_header)
            
            if response.status_code == 200:
                return response.json()
            else:
                return []
                
        except Exception:
            return []

    def create_or_get_tag(self, tag_name):
        """Create a tag if it doesn't exist, or get its ID if it does"""
        try:
            # First try to find if tag exists
            endpoint = f"{self.api_url}/tags?search={tag_name}"
            response = requests.get(endpoint, headers=self.auth_header)
            
            if response.status_code == 200 and response.json():
                # Tag found, return its ID
                for tag in response.json():
                    if tag.get('name').lower() == tag_name.lower():
                        return tag.get('id')
            
            # If we're here, tag doesn't exist - create it
            endpoint = f"{self.api_url}/tags"
            response = requests.post(
                endpoint,
                headers=self.auth_header,
                json={'name': tag_name}
            )
            
            if response.status_code in (200, 201):
                return response.json().get('id')
            else:
                return None
                
        except Exception:
            return None