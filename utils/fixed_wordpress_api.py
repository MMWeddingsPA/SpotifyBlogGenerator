import requests
import base64
import json
import logging
import urllib.parse
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
        
        # Ensure HTTPS protocol
        if not api_url.startswith('http'):
            api_url = f"https://{api_url}"
        elif api_url.startswith('http://'):
            api_url = api_url.replace('http://', 'https://')
            
        # Clean the base URL and set the API endpoint
        self.base_url = api_url.rstrip('/')
        self.api_url = f"{self.base_url}/wp-json/wp/v2"
        
        # Store credentials
        self.username = username
        self.password = password
        
        # Set up authentication header
        self.auth_header = self._get_auth_header()
        
        # Standard headers that should be included in all requests
        self.standard_headers = {
            'User-Agent': 'WordPress API Client/1.0',
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
        
        # Log the endpoint and headers
        logger.info(f"WordPress API endpoint: {self.api_url}")
        logger.info(f"Using standard headers: {json.dumps(self.standard_headers)}")
        
    def _get_auth_header(self):
        """Create authorization header using basic auth"""
        # Use raw credentials without URL encoding for basic auth
        auth_string = f"{self.username}:{self.password}"
        encoded = base64.b64encode(auth_string.encode()).decode('utf-8')
        auth_header = {'Authorization': f'Basic {encoded}'}
        
        # Log auth header format (without exposing the actual token)
        logger.info(f"Auth header format: Authorization: Basic [base64 token]")
        
        return auth_header
    
    def test_connection(self):
        """Test the connection to the WordPress API"""
        try:
            # We'll try a very simple query - just get a single post
            endpoint = f"{self.api_url}/posts?per_page=1"
            logger.info(f"Testing connection to: {endpoint}")
            
            # Prepare headers with auth and standard headers
            headers = self.standard_headers.copy()
            headers.update(self.auth_header)
            
            # Log what we're sending (with redacted auth token)
            safe_headers = headers.copy()
            if 'Authorization' in safe_headers:
                safe_headers['Authorization'] = 'Basic [REDACTED]'
            logger.info(f"Request headers: {json.dumps(safe_headers)}")
            
            # Make the request
            response = requests.get(
                endpoint,
                headers=headers,
                timeout=10
            )
            
            # Log complete response details
            logger.info(f"Response status: {response.status_code}")
            logger.info(f"Response headers: {dict(response.headers)}")
            
            if response.status_code == 200:
                logger.info("WordPress API connection successful!")
                return True
            else:
                # Log the full error response
                logger.error(f"WordPress API connection failed with status code: {response.status_code}")
                logger.error(f"Response content: {response.text}")
                
                # Try to parse JSON error if available
                try:
                    error_json = response.json()
                    logger.error(f"Error details: {json.dumps(error_json, indent=2)}")
                except Exception as parse_error:
                    logger.error(f"Could not parse error response as JSON: {str(parse_error)}")
                
                return False
                
        except Exception as e:
            logger.error(f"WordPress API connection test failed: {str(e)}")
            logger.exception("Full exception traceback:")
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
            
            # Prepare post data with proper formatting
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
            logger.info(f"Title: {title[:50] + '...' if len(title) > 50 else title}")
            logger.info(f"Content length: {len(content)} characters")
            logger.info(f"Status: {status}")
            
            # Prepare headers with all required fields
            headers = self.standard_headers.copy()
            headers.update(self.auth_header)
            
            # Log request details (redact auth token)
            safe_headers = headers.copy()
            if 'Authorization' in safe_headers:
                safe_headers['Authorization'] = 'Basic [REDACTED]'
            logger.info(f"Request headers: {json.dumps(safe_headers)}")
            
            # Make the request
            response = requests.post(
                endpoint,
                headers=headers,
                json=post_data,
                timeout=20
            )
            
            # Log complete response details
            logger.info(f"Response status: {response.status_code}")
            logger.info(f"Response headers: {dict(response.headers)}")
            
            # Check if successful
            if response.status_code in (200, 201):
                logger.info(f"Post created successfully!")
                json_data = response.json()
                
                post_id = json_data.get('id')
                post_url = json_data.get('link')
                edit_url = f"{self.base_url}/wp-admin/post.php?post={post_id}&action=edit"
                
                return {
                    'success': True,
                    'post_id': post_id,
                    'post_url': post_url,
                    'edit_url': edit_url
                }
            else:
                # Log the full error response
                logger.error(f"Failed to create post. Status code: {response.status_code}")
                logger.error(f"Response content: {response.text}")
                
                # Try to parse JSON error if available
                try:
                    error_json = response.json()
                    logger.error(f"Error details: {json.dumps(error_json, indent=2)}")
                except Exception as parse_error:
                    logger.error(f"Could not parse error response as JSON: {str(parse_error)}")
                
                return {
                    'success': False,
                    'error': f"Failed with status code: {response.status_code}. See logs for details."
                }
        
        except Exception as e:
            logger.error(f"Exception creating WordPress post: {str(e)}")
            logger.exception("Full exception traceback:")
            return {
                'success': False,
                'error': f"Error creating WordPress post: {str(e)}"
            }
    
    def create_test_post(self):
        """Simple function to test WordPress POST capability with minimal content"""
        test_title = "Test Post from Blog Generator"
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        test_content = f"""
        <p>This is a simple test post created at {timestamp} to verify WordPress API integration.</p>
        <p>If you're seeing this post, it means the connection between the Blog Generator app and your WordPress site is working correctly!</p>
        """
        
        logger.info("Creating simple test post...")
        
        # Use existing create_post method
        result = self.create_post(test_title, test_content, status='draft')
        
        # Log the full result
        logger.info(f"Test post result: {json.dumps(result, indent=2)}")
        
        return result
    
    def get_categories(self):
        """Get available categories from WordPress"""
        try:
            endpoint = f"{self.api_url}/categories"
            logger.info(f"Getting categories from: {endpoint}")
            
            # Prepare headers with auth and standard headers
            headers = self.standard_headers.copy()
            headers.update(self.auth_header)
            
            # Make the request
            response = requests.get(
                endpoint,
                headers=headers,
                timeout=10
            )
            
            # Log response details
            logger.info(f"Categories response code: {response.status_code}")
            
            if response.status_code == 200:
                categories = response.json()
                logger.info(f"Found {len(categories)} categories")
                return categories
            else:
                # Log the full error response
                logger.error(f"Failed to get categories. Status code: {response.status_code}")
                logger.error(f"Response content: {response.text}")
                return []
            
        except Exception as e:
            logger.error(f"Error getting categories: {str(e)}")
            logger.exception("Full exception traceback:")
            return []