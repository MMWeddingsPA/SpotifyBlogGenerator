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
        # Check if username/password have special characters that need URL encoding
        safe_username = urllib.parse.quote(self.username)
        safe_password = urllib.parse.quote(self.password)
        
        # Log if encoding was applied (without exposing credentials)
        if safe_username != self.username:
            logger.info("Username contains special characters and was URL encoded")
        if safe_password != self.password:
            logger.info("Password contains special characters and was URL encoded")
            
        # Create both versions of credentials - with and without URL encoding
        credentials_raw = f"{self.username}:{self.password}"
        credentials_safe = f"{safe_username}:{safe_password}"
        
        # Generate token with original credentials (standard method)
        token = base64.b64encode(credentials_raw.encode()).decode('utf-8')
        auth_header = {'Authorization': f'Basic {token}'}
        
        # Log auth header format (without exposing the actual token)
        logger.info(f"Auth header format: Authorization: Basic [base64 token]")
        
        return auth_header
    
    def test_connection(self):
        """Test the connection to the WordPress API"""
        try:
            # We'll try a very simple query - just get a single post
            endpoint = f"{self.api_url}/posts?per_page=1"
            logger.info(f"Testing connection to: {endpoint}")
            
            # Initialize response variable
            response = None
            
            # First try with auth header
            try:
                logger.info("Trying connection with auth header...")
                headers = {'Content-Type': 'application/json'}
                headers.update(self.auth_header)
                
                response = requests.get(
                    endpoint,
                    headers=headers,
                    timeout=10
                )
                
                logger.info(f"Response status with auth header: {response.status_code}")
                
                if response.status_code == 200:
                    logger.info("WordPress API connection successful (header auth)")
                    return True
            except Exception as e:
                logger.error(f"Error testing with auth header: {str(e)}")
            
            # Then try with direct auth tuple
            try:
                logger.info("Trying connection with direct auth...")
                response = requests.get(
                    endpoint,
                    auth=self.auth,
                    headers={'Content-Type': 'application/json'},
                    timeout=10
                )
                
                logger.info(f"Response status with direct auth: {response.status_code}")
                
                if response.status_code == 200:
                    logger.info("WordPress API connection successful (direct auth)")
                    return True
            except Exception as e:
                logger.error(f"Error testing with direct auth: {str(e)}")
                
            # If neither method worked, log the error
            logger.error(f"WordPress API connection failed")
            if response:
                logger.error(f"Last response code: {response.status_code}")
                logger.error(f"Response text: {response.text[:500]}")
                
                # Try to parse JSON error if available
                try:
                    error_json = response.json()
                    logger.error(f"Error details: {json.dumps(error_json, indent=2)}")
                except:
                    pass
                    
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
            
            # Prepare post data with proper formatting
            post_data = {
                'title': {'raw': title},
                'content': {'raw': content},
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
            logger.info(f"Post data structure: {json.dumps(post_data, indent=2)}")
            
            # Initialize response variable
            response = None
            
            # First attempt: try with auth tuple (direct auth)
            try:
                logger.info("Attempting to create post with direct auth...")
                headers = {'Content-Type': 'application/json'}
                
                # Log exact request being sent
                logger.info(f"Request headers: {json.dumps(headers)}")
                logger.info(f"Using direct auth with username: {self.username} (password hidden)")
                
                response = requests.post(
                    endpoint,
                    auth=self.auth,
                    headers=headers,
                    json=post_data,
                    timeout=20
                )
                
                # Log complete response details
                logger.info(f"Response status: {response.status_code}")
                logger.info(f"Response headers: {dict(response.headers)}")
                
                # Check if successful
                if response.status_code in (200, 201):
                    logger.info(f"Post created successfully with direct auth!")
                    json_data = response.json()
                    logger.info(f"Response data: {json.dumps(json_data, indent=2)}")
                    
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
                    logger.error(f"Direct auth failed with status: {response.status_code}")
                    logger.error(f"Response text: {response.text}")
            except Exception as e:
                logger.error(f"Error creating post with direct auth: {str(e)}")
            
            # Second attempt: try with auth header
            try:
                logger.info("Attempting to create post with auth header...")
                headers = {'Content-Type': 'application/json'}
                headers.update(self.auth_header)
                
                # Log request details (redact actual token value)
                safe_headers = headers.copy()
                if 'Authorization' in safe_headers:
                    safe_headers['Authorization'] = 'Basic [REDACTED]'
                logger.info(f"Request headers: {json.dumps(safe_headers)}")
                
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
                    logger.info(f"Post created successfully with auth header!")
                    json_data = response.json()
                    logger.info(f"Response data: {json.dumps(json_data, indent=2)}")
                    
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
                    logger.error(f"Auth header failed with status: {response.status_code}")
                    logger.error(f"Response text: {response.text}")
            except Exception as e:
                logger.error(f"Error creating post with auth header: {str(e)}")
            
            # If we get here, both methods failed
            error_message = "Failed to create post with both auth methods"
            if response:
                error_message = f"Failed with status code: {response.status_code}"
                logger.error(f"Response text: {response.text[:1000]}")
                # Try to parse JSON response for more details
                try:
                    error_json = response.json()
                    logger.error(f"Error details: {json.dumps(error_json, indent=2)}")
                except:
                    pass
            
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
    
    def create_test_post(self):
        """Simple function to test WordPress POST capability with minimal content"""
        test_title = "Test Post from Replit"
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
            
            # Initialize response variable
            response = None
            
            # Try with direct auth first
            try:
                logger.info("Getting categories with direct auth...")
                response = requests.get(
                    endpoint,
                    auth=self.auth,
                    headers={'Content-Type': 'application/json'},
                    timeout=10
                )
                
                logger.info(f"Categories response code: {response.status_code}")
                
                if response.status_code == 200:
                    categories = response.json()
                    logger.info(f"Found {len(categories)} categories")
                    return categories
            except Exception as e:
                logger.error(f"Error getting categories with direct auth: {str(e)}")
            
            # Try with auth header
            try:
                logger.info("Getting categories with auth header...")
                headers = {'Content-Type': 'application/json'}
                headers.update(self.auth_header)
                
                response = requests.get(
                    endpoint,
                    headers=headers,
                    timeout=10
                )
                
                logger.info(f"Categories response code: {response.status_code}")
                
                if response.status_code == 200:
                    categories = response.json()
                    logger.info(f"Found {len(categories)} categories")
                    return categories
            except Exception as e:
                logger.error(f"Error getting categories with auth header: {str(e)}")
            
            # If both methods failed
            logger.error(f"Failed to get categories")
            if response:
                logger.error(f"Response code: {response.status_code}")
                logger.error(f"Response text: {response.text[:500]}")
            
            return []
            
        except Exception as e:
            logger.error(f"Error getting categories: {str(e)}")
            return []