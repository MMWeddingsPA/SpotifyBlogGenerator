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
        
        # Verify that the credentials look correct
        if len(username) < 1:
            raise ValueError("WordPress username cannot be empty")
        if len(password) < 1:
            raise ValueError("WordPress password cannot be empty")
            
        # Validate and clean the WordPress URL 
        if not api_url.startswith('http'):
            api_url = f"https://{api_url}"
        elif api_url.startswith('http://'):
            api_url = api_url.replace('http://', 'https://')
        
        # Make sure URL doesn't have trailing `/wp-json`
        if api_url.endswith('/wp-json'):
            api_url = api_url[:-8]  # Remove trailing /wp-json
        
        # Strip any trailing slashes for consistency
        api_url = api_url.rstrip('/')
            
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
        """Create authorization header using WordPress application password format"""
        try:
            # Check if the password looks like an application password (usually contains spaces)
            is_app_password = ' ' in self.password
            
            if is_app_password:
                logger.info("Password appears to be a WordPress Application Password (contains spaces)")
                # For application passwords, we need to handle the format correctly
                # The spaces need to be preserved in the encoding
                
                # Log credential format (without exposing the actual values)
                logger.info(f"Using application password auth with username length: {len(self.username)}")
                
                # WordPress application passwords use the username in full and the application password as provided
                auth_string = f"{self.username}:{self.password}"
                
                # This is the standard Basic Auth encoding with base64, but preserving spaces
                encoded = base64.b64encode(auth_string.encode('utf-8')).decode('utf-8')
                
                # Check if the token seems unusual or problematic
                if len(encoded) < 10:
                    logger.warning(f"Auth token is unusually short ({len(encoded)} chars), possible encoding issue")
                
                # Log first few characters to help with debugging (without exposing the whole token)
                token_preview = encoded[:5] + "..." if len(encoded) > 5 else encoded
                logger.info(f"Auth token preview (first 5 chars): {token_preview}")
                
                # Return WordPress application password format
                return {'Authorization': f'Basic {encoded}'}
            else:
                # For regular passwords (not application passwords)
                logger.info("Using standard WordPress authentication (no spaces in password)")
                
                # Log credential format (without exposing the actual values)
                logger.info(f"Using basic auth credentials with username length: {len(self.username)}")
                
                # Standard Basic Auth encoding with base64
                auth_string = f"{self.username}:{self.password}"
                encoded = base64.b64encode(auth_string.encode('utf-8')).decode('utf-8')
                
                # Log auth header format (without exposing the actual token)
                logger.info(f"Auth header format: Authorization: Basic [base64 token]")
                
                # Check if the token seems unusual or problematic
                if len(encoded) < 10:
                    logger.warning(f"Auth token is unusually short ({len(encoded)} chars), possible encoding issue")
                
                # Log first few characters to help with debugging (without exposing the whole token)
                token_preview = encoded[:5] + "..." if len(encoded) > 5 else encoded
                logger.info(f"Auth token preview (first 5 chars): {token_preview}")
                
                return {'Authorization': f'Basic {encoded}'}
            
        except Exception as e:
            logger.error(f"Error creating auth header: {str(e)}")
            logger.exception("Full exception traceback:")
            
            # Fall back to a simple header if there's an error
            auth_string = f"{self.username}:{self.password}"
            encoded = base64.b64encode(auth_string.encode()).decode('utf-8')
            return {'Authorization': f'Basic {encoded}'}
    
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
            
            # Prepare post data with proper formatting based on the WordPress response format
            # We can see from the sample data that WordPress expects title and content in this format
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
                
                # Add WordPress informational error messages for common issues
                if response.status_code == 401:
                    logger.error("Authentication failed: WordPress returned 401 Unauthorized")
                    logger.error("Possible causes: incorrect username/password or insufficient permissions")
                    
                    # Try to help troubleshoot
                    if len(self.password) < 5:
                        logger.error("Password is very short, this might be incorrect")
                    
                    # Check for common WordPress application password format issues
                    if ' ' in self.password:
                        # App password often formatted like "XXXX XXXX XXXX XXXX"
                        logger.info("Using WordPress Application Password format (detected spaces)")
                        
                        # Let's see if it looks like a properly formatted app password
                        app_password_segments = self.password.split()
                        if all(len(segment) == 4 for segment in app_password_segments):
                            logger.info(f"Password appears to be in correct App Password format with {len(app_password_segments)} segments of 4 characters each")
                        else:
                            logger.warning(f"Password contains spaces but doesn't match typical app password format (XXXX XXXX XXXX XXXX)")
                            segment_lengths = [len(s) for s in app_password_segments]
                            logger.warning(f"Password segment lengths: {segment_lengths} (should all be 4)")
                        
                        # Suggest a possible fix for app password format if it's not perfectly formatted
                        if any(len(segment) != 4 for segment in app_password_segments):
                            logger.warning("WordPress application passwords should be in format: XXXX XXXX XXXX XXXX")
                            logger.warning("Please check if there are extra spaces or missing characters")
                    
                    if "wordpress.com" in self.base_url:
                        logger.error("For WordPress.com sites, special API endpoints and authentication may be required")
                    
                    # Add a specific note about JWT authentication
                    logger.info("Note: Some WordPress sites use JWT authentication instead of Basic Auth")
                    logger.info("If you have a plugin like JWT Authentication installed, a different approach may be needed")
                
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
            
    def diagnose_connection(self):
        """
        Comprehensive WordPress API connection diagnostics
        Tests various aspects of the connection and returns detailed information
        """
        try:
            logger.info("===== WORDPRESS API DIAGNOSTIC INFORMATION =====")
            logger.info(f"WordPress Base URL: {self.base_url}")
            logger.info(f"WordPress API Endpoint: {self.api_url}")
            logger.info(f"Username Length: {len(self.username)}")
            logger.info(f"Password Length: {len(self.password)}")
            
            # Check if password looks like a WordPress application password
            if ' ' in self.password:
                pw_segments = self.password.split()
                segment_info = [len(s) for s in pw_segments]
                logger.info(f"Password appears to be in Application Password format with {len(pw_segments)} segments: {segment_info}")
                if any(len(s) != 4 for s in pw_segments):
                    logger.warning("WARNING: Application password segments should normally be 4 characters each")
            else:
                logger.info("Using standard password format (not an application password)")
            
            # Test server connection without authentication
            logger.info("\n--- Testing basic server connection ---")
            try:
                # Just ping the site without authentication to see if it's reachable
                response = requests.get(
                    self.base_url,
                    timeout=5
                )
                logger.info(f"Server connection: {response.status_code} ({response.reason})")
                if response.status_code == 200:
                    logger.info("✓ Server connection successful")
                else:
                    logger.warning(f"✗ Server returned non-200 status: {response.status_code}")
            except Exception as e:
                logger.error(f"✗ Server connection failed: {str(e)}")
            
            # Test WordPress REST API discovery
            logger.info("\n--- Testing WordPress REST API discovery ---")
            try:
                # Try to access the root of the WordPress REST API to see if it's available
                api_root = f"{self.base_url}/wp-json"
                response = requests.get(
                    api_root,
                    timeout=5
                )
                logger.info(f"WordPress API discovery: {response.status_code} ({response.reason})")
                if response.status_code == 200:
                    logger.info("✓ WordPress REST API found")
                else:
                    logger.warning(f"✗ WordPress REST API not found at {api_root}")
            except Exception as e:
                logger.error(f"✗ WordPress API discovery failed: {str(e)}")
            
            # Test authentication
            logger.info("\n--- Testing Authentication ---")
            # Use the test_connection method which checks authentication
            auth_success = self.test_connection()
            if auth_success:
                logger.info("✓ Authentication successful")
            else:
                logger.error("✗ Authentication failed")
            
            # Try special WordPress debugging endpoints
            logger.info("\n--- Testing WordPress Version Endpoint ---")
            try:
                response = requests.get(
                    f"{self.base_url}/wp-json",
                    headers=self.standard_headers,
                    timeout=5
                )
                if response.status_code == 200:
                    data = response.json()
                    if 'name' in data:
                        logger.info(f"WordPress Site Name: {data['name']}")
                    if 'description' in data:
                        logger.info(f"WordPress Site Description: {data['description']}")
                    if 'url' in data:
                        logger.info(f"WordPress Site URL: {data['url']}")
                    if 'namespaces' in data:
                        logger.info(f"Available namespaces: {', '.join(data['namespaces'])}")
                        if 'wp/v2' not in data['namespaces']:
                            logger.warning("! 'wp/v2' namespace not found - this suggests an issue with WordPress REST API")
                else:
                    logger.warning(f"Could not get WordPress version info: {response.status_code}")
            except Exception as e:
                logger.error(f"Error getting WordPress version: {str(e)}")
                
            logger.info("===== END WORDPRESS API DIAGNOSTICS =====")
            return auth_success
            
        except Exception as e:
            logger.error(f"Error during WordPress diagnostics: {str(e)}")
            logger.exception("Full exception traceback:")
            return False