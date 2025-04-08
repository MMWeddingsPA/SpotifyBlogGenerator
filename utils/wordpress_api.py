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
            
        # Try multiple API URL formats to find the right one for this specific site
        self.api_url = api_url.rstrip('/')
        
        # We'll try several URL formats because different WordPress sites might use different paths
        self.possible_urls = [
            f"{self.api_url}/wp-json/wp/v2",           # Standard format
            f"{self.api_url}/index.php/wp-json/wp/v2", # Some WordPress sites use this
            f"{self.api_url}/wp-json/api/v1",          # Some custom API endpoints
            f"{self.api_url}/wp-json",                 # Root API path
        ]
        
        # Use the standard format as the default
        self.api_url = self.possible_urls[0]
        logger.info(f"Initial API URL: {self.api_url}")
        logger.info(f"Will try these URL variations if needed: {', '.join(self.possible_urls[1:])}")
        
        self.username = username
        self.password = password
        self.auth_header = self._get_auth_header()
        
        # Test connection
        self.test_connection()
    
    def test_connection(self):
        """Test the connection to WordPress API by trying various URL formats"""
        # First, try the default URL
        if self._test_single_url(self.api_url):
            return True
            
        # If that fails, try each of the alternative URL formats
        for url in self.possible_urls[1:]:
            logger.info(f"Trying alternative API URL: {url}")
            if self._test_single_url(url):
                # Use this URL for subsequent requests
                self.api_url = url
                logger.info(f"Found working API URL: {self.api_url}")
                return True
                
        # If we've tried all URLs and still fail, then try to check API access
        try:
            # Sometimes the API root is available even if specific endpoints aren't
            root_url = self.api_url.split('/wp/v2')[0]
            logger.info(f"Trying API root: {root_url}")
            response = requests.get(root_url, timeout=10)
            
            if response.status_code == 200:
                logger.info(f"API root is accessible: {root_url}")
                logger.info(f"Response: {response.text[:200]}...")
                # We might be able to parse available routes
                try:
                    if 'routes' in response.json():
                        available_routes = list(response.json()['routes'].keys())
                        logger.info(f"Available routes: {available_routes[:10]}")
                except:
                    pass
            else:
                logger.error(f"API root is not accessible: {response.status_code}")
        except Exception as e:
            logger.error(f"Error checking API root: {str(e)}")
            
        # If all attempts failed
        logger.error("All WordPress API connection attempts failed")
        return False
        
    def _test_single_url(self, url):
        """Test a single API URL"""
        try:
            # Try to get a list of posts (simple request)
            endpoint = f"{url}/posts?per_page=1"
            logger.info(f"Testing connection to: {endpoint}")
            
            headers = self.auth_header.copy()
            
            # Some WP sites require additional headers
            headers['Content-Type'] = 'application/json'
            
            # Try the standard request
            response = requests.get(
                endpoint,
                headers=headers,
                timeout=10
            )
            
            logger.info(f"Connection test response code: {response.status_code}")
            
            if response.status_code == 200:
                logger.info("WordPress API connection successful")
                return True
            else:
                # Try with direct auth instead of auth header
                try:
                    logger.info("Trying with direct auth parameters")
                    auth_response = requests.get(
                        endpoint,
                        auth=(self.username, self.password),
                        timeout=10
                    )
                    
                    if auth_response.status_code == 200:
                        logger.info("Connection successful with direct auth")
                        # Update our approach for future requests
                        self.use_direct_auth = True
                        return True
                except Exception as e:
                    logger.error(f"Error with direct auth: {str(e)}")
                
                # Check response for clues
                logger.error(f"WordPress API connection failed: {response.status_code}")
                logger.error(f"Response: {response.text}")
                
                # If we got HTML instead of JSON, the endpoint might be wrong
                if '<html' in response.text.lower():
                    logger.error("Received HTML response instead of JSON - endpoint might be incorrect")
                
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
            
            # Create headers with content type
            headers = self.auth_header.copy()
            headers['Content-Type'] = 'application/json'
            logger.info(f"Headers: {headers.keys()}")
            logger.info(f"Post data keys: {post_data.keys()}")
            
            # Response variable for tracking
            response = None
            
            # Try different methods for posting content
            methods_to_try = [
                {
                    'name': 'standard_auth_header',
                    'func': lambda: requests.post(
                        endpoint,
                        headers=headers,
                        json=post_data,
                        timeout=20
                    )
                },
                {
                    'name': 'direct_auth',
                    'func': lambda: requests.post(
                        endpoint,
                        auth=(self.username, self.password),
                        json=post_data,
                        headers={'Content-Type': 'application/json'},
                        timeout=20
                    )
                },
                {
                    'name': 'form_encoded',
                    'func': lambda: requests.post(
                        endpoint,
                        headers=headers,
                        data=post_data,  # Use data instead of json
                        timeout=20
                    )
                }
            ]
            
            # If we've found a working auth method in test_connection, try that first
            if hasattr(self, 'use_direct_auth') and self.use_direct_auth:
                # Reorder to try direct auth first
                methods_to_try = [methods_to_try[1]] + [methods_to_try[0]] + [methods_to_try[2]]
            
            # Try each method until one works
            success = False
            for method in methods_to_try:
                try:
                    logger.info(f"Trying {method['name']} method")
                    response = method['func']()
                    logger.info(f"{method['name']} response code: {response.status_code}")
                    
                    if response.status_code in (200, 201):
                        logger.info(f"Post created successfully with {method['name']} method!")
                        success = True
                        break
                except Exception as e:
                    logger.error(f"Error with {method['name']} method: {str(e)}")
            
            # Final success check
            if success:
                return {
                    'success': True,
                    'post_id': response.json().get('id'),
                    'post_url': response.json().get('link'),
                    'edit_url': response.json().get('_links', {}).get('wp:action-edit', [{}])[0].get('href'),
                }
            else:
                # If we have a response, log it
                if response:
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
                else:
                    return {
                        'success': False,
                        'error': "All posting methods failed"
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
            logger.info(f"Getting categories from: {endpoint}")
            
            # Try with auth header first
            headers = self.auth_header.copy()
            headers['Content-Type'] = 'application/json'
            
            # If we've determined that direct auth works better, use that
            if hasattr(self, 'use_direct_auth') and self.use_direct_auth:
                logger.info("Using direct auth for categories request")
                response = requests.get(
                    endpoint,
                    auth=(self.username, self.password),
                    timeout=10
                )
            else:
                # Otherwise use standard auth header
                response = requests.get(
                    endpoint,
                    headers=headers,
                    timeout=10
                )
            
            if response.status_code == 200:
                categories = response.json()
                logger.info(f"Found {len(categories)} categories")
                return categories
            else:
                logger.error(f"Error getting categories: {response.status_code}")
                logger.error(f"Response: {response.text}")
                return []
                
        except Exception as e:
            logger.error(f"Exception getting categories: {str(e)}")
            return []

    def create_or_get_tag(self, tag_name):
        """Create a tag if it doesn't exist, or get its ID if it does"""
        try:
            # First try to find if tag exists
            endpoint = f"{self.api_url}/tags?search={tag_name}"
            logger.info(f"Searching for tag '{tag_name}' at: {endpoint}")
            
            # Headers for the request
            headers = self.auth_header.copy()
            headers['Content-Type'] = 'application/json'
            
            # Make the get request using the appropriate auth method
            if hasattr(self, 'use_direct_auth') and self.use_direct_auth:
                response = requests.get(
                    endpoint,
                    auth=(self.username, self.password),
                    timeout=10
                )
            else:
                response = requests.get(
                    endpoint,
                    headers=headers,
                    timeout=10
                )
            
            if response.status_code == 200:
                json_data = response.json()
                if json_data:
                    # Tag found, return its ID
                    for tag in json_data:
                        if tag.get('name', '').lower() == tag_name.lower():
                            tag_id = tag.get('id')
                            logger.info(f"Found existing tag '{tag_name}' with ID: {tag_id}")
                            return tag_id
            
            # If we're here, tag doesn't exist - create it
            logger.info(f"Tag '{tag_name}' not found, creating new tag")
            endpoint = f"{self.api_url}/tags"
            
            # Try different posting methods as needed
            tag_data = {'name': tag_name}
            
            if hasattr(self, 'use_direct_auth') and self.use_direct_auth:
                response = requests.post(
                    endpoint,
                    auth=(self.username, self.password),
                    json=tag_data,
                    headers={'Content-Type': 'application/json'},
                    timeout=10
                )
            else:
                response = requests.post(
                    endpoint,
                    headers=headers,
                    json=tag_data,
                    timeout=10
                )
            
            if response.status_code in (200, 201):
                tag_id = response.json().get('id')
                logger.info(f"Created new tag '{tag_name}' with ID: {tag_id}")
                return tag_id
            else:
                logger.error(f"Error creating tag: {response.status_code}")
                logger.error(f"Response: {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Exception in create_or_get_tag: {str(e)}")
            return None