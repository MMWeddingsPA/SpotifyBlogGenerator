import requests
import base64
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
        :param api_url: WordPress site URL (e.g., https://example.com)
        :param username: WordPress username or application password name
        :param password: WordPress password or application password
        """
        if not api_url or not username or not password:
            raise ValueError("WordPress API URL, username, and password are required")
        
        # Log the initialization (without credentials)
        logger.info(f"Initializing WordPress API with URL: {api_url}")
        logger.info(f"Username length: {len(username)}")
        logger.info(f"Password available: {'Yes' if password else 'No'}")
            
        # Clean the base URL and set the API endpoint
        self.base_url = api_url.rstrip('/')
        self.api_url = f"{self.base_url}/wp-json/wp/v2"
        
        # Store credentials
        self.username = username
        self.password = password
        
        # Set up authentication mechanisms
        self.auth = (self.username, self.password)
        self.auth_header = self._get_auth_header()
        
        # Log the endpoint
        logger.info(f"WordPress API endpoint: {self.api_url}")
        
    def _get_auth_header(self):
        """Create authorization header using basic auth"""
        credentials = f"{self.username}:{self.password}"
        token = base64.b64encode(credentials.encode()).decode('utf-8')
        auth_header = {'Authorization': f'Basic {token}'}
        return auth_header
    
    def test_connection(self):
        """Test the connection to the WordPress API"""
        try:
            endpoint = f"{self.api_url}/posts?per_page=1"
            logger.info(f"Testing connection to: {endpoint}")
            
            headers = {'Content-Type': 'application/json'}
            headers.update(self.auth_header)
            
            # First try with auth header
            logger.info("Trying connection with auth header...")
            response = requests.get(
                endpoint,
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                logger.info("WordPress API connection successful (header auth)")
                return True
            
            # Try with direct auth tuple
            logger.info("Trying connection with direct auth...")
            response = requests.get(
                endpoint,
                auth=self.auth,
                timeout=10
            )
            
            if response.status_code == 200:
                logger.info("WordPress API connection successful (direct auth)")
                return True
                
            # If neither method worked, log the error
            logger.error(f"WordPress API connection failed: {response.status_code}")
            logger.error(f"Response: {response.text[:500]}")
            return False
            
        except Exception as e:
            logger.error(f"WordPress API connection test failed: {str(e)}")
            return False
    
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
            # Prepare endpoint URL
            endpoint = f"{self.api_url}/posts"
            logger.info(f"Creating post at: {endpoint}")
            
            # Prepare post data
            post_data = {
                'title': title,
                'content': content,
                'status': status,
            }
            
            # Add optional fields if provided
            if featured_media:
                post_data['featured_media'] = featured_media
            
            if categories:
                post_data['categories'] = categories
            
            if tags:
                post_data['tags'] = tags
            
            # Log what we're sending
            logger.info(f"Title: {title[:30]}...")
            logger.info(f"Content length: {len(content)} characters")
            logger.info(f"Status: {status}")
            logger.info(f"Post data keys: {list(post_data.keys())}")
            
            # First attempt: try with auth tuple (direct auth)
            try:
                logger.info("Attempting to create post with direct auth...")
                headers = {'Content-Type': 'application/json'}
                
                response = requests.post(
                    endpoint,
                    auth=self.auth,
                    headers=headers,
                    json=post_data,
                    timeout=20
                )
                
                # Check if successful
                if response.status_code in (200, 201):
                    logger.info(f"Post created successfully with direct auth!")
                    json_data = response.json()
                    return {
                        'success': True,
                        'post_id': json_data.get('id'),
                        'post_url': json_data.get('link'),
                    }
            except Exception as e:
                logger.error(f"Error creating post with direct auth: {str(e)}")
            
            # Second attempt: try with auth header
            try:
                logger.info("Attempting to create post with auth header...")
                headers = {'Content-Type': 'application/json'}
                headers.update(self.auth_header)
                
                response = requests.post(
                    endpoint,
                    headers=headers,
                    json=post_data,
                    timeout=20
                )
                
                # Check if successful
                if response.status_code in (200, 201):
                    logger.info(f"Post created successfully with auth header!")
                    json_data = response.json()
                    return {
                        'success': True,
                        'post_id': json_data.get('id'),
                        'post_url': json_data.get('link'),
                    }
            except Exception as e:
                logger.error(f"Error creating post with auth header: {str(e)}")
            
            # If we get here, both methods failed
            error_message = "Failed to create post with both auth methods"
            if 'response' in locals() and response:
                error_message = f"Failed with status code: {response.status_code}"
                logger.error(f"Response text: {response.text[:500]}")
            
            logger.error(error_message)
            return {
                'success': False,
                'error': error_message
            }
            
        except Exception as e:
            logger.error(f"Exception creating WordPress post: {str(e)}")
            return {
                'success': False,
                'error': f"Error creating WordPress post: {str(e)}"
            }
    
    def get_categories(self):
        """Get available categories from WordPress"""
        try:
            endpoint = f"{self.api_url}/categories"
            logger.info(f"Getting categories from: {endpoint}")
            
            # Try with direct auth first
            response = requests.get(
                endpoint,
                auth=self.auth,
                timeout=10
            )
            
            if response.status_code == 200:
                categories = response.json()
                logger.info(f"Found {len(categories)} categories")
                return categories
            
            # Try with auth header
            headers = self.auth_header.copy()
            response = requests.get(
                endpoint,
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                categories = response.json()
                logger.info(f"Found {len(categories)} categories")
                return categories
            
            # If both methods failed
            logger.error(f"Failed to get categories: {response.status_code}")
            return []
            
        except Exception as e:
            logger.error(f"Error getting categories: {str(e)}")
            return []