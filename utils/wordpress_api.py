import requests
import base64
import os
import json
import logging
import xml.etree.ElementTree as ET
from datetime import datetime
import urllib.parse

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class WordPressAPI:
    def __init__(self, api_url, username, password):
        """
        Initialize WordPress API client with support for both REST API and XML-RPC
        :param api_url: WordPress site URL (e.g., https://yoursite.com)
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
            
        # Clean the base URL
        self.base_url = api_url.rstrip('/')
        
        # REST API URLs to try
        self.rest_api_urls = [
            f"{self.base_url}/wp-json/wp/v2",                # Standard format
            f"{self.base_url}/index.php/wp-json/wp/v2",      # Some WordPress sites use this
            f"{self.base_url}/wp-json/api/v1",               # Some custom API endpoints
            f"{self.base_url}/wp-json",                      # Root API path
        ]
        
        # XML-RPC endpoint
        self.xmlrpc_url = f"{self.base_url}/xmlrpc.php"
        
        # Set our credentials
        self.username = username
        self.password = password
        self.auth_header = self._get_auth_header()
        
        # Start with REST API as default
        self.api_url = self.rest_api_urls[0]
        logger.info(f"Initial REST API URL: {self.api_url}")
        
        # Track which API type to use
        self.use_xmlrpc = False
        
        # Test connection
        self.test_connection()
    
    def test_connection(self):
        """Test the connection to WordPress API by trying REST API and XML-RPC"""
        # First, try REST API endpoints
        rest_api_working = False
        for url in self.rest_api_urls:
            logger.info(f"Trying REST API URL: {url}")
            if self._test_rest_api_url(url):
                # Use this URL for subsequent REST API requests
                self.api_url = url
                logger.info(f"Found working REST API URL: {self.api_url}")
                rest_api_working = True
                break
        
        if rest_api_working:
            return True
        
        # If REST API fails, try XML-RPC
        logger.info(f"REST API not working, trying XML-RPC endpoint: {self.xmlrpc_url}")
        if self._test_xmlrpc():
            logger.info("XML-RPC connection successful")
            self.use_xmlrpc = True
            return True
        
        # If all attempts failed
        logger.error("All WordPress API connection attempts failed")
        return False
        
    def _test_rest_api_url(self, url):
        """Test a single REST API URL"""
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
    
    def _test_xmlrpc(self):
        """Test XML-RPC connection"""
        try:
            # Prepare XML-RPC request
            xml_request = f"""<?xml version="1.0"?>
            <methodCall>
              <methodName>wp.getUsersBlogs</methodName>
              <params>
                <param><value><string>{self.username}</string></value></param>
                <param><value><string>{self.password}</string></value></param>
              </params>
            </methodCall>
            """
            
            logger.info(f"Testing XML-RPC connection to: {self.xmlrpc_url}")
            
            # Send the request
            headers = {'Content-Type': 'text/xml'}
            response = requests.post(
                self.xmlrpc_url,
                data=xml_request,
                headers=headers,
                timeout=10
            )
            
            logger.info(f"XML-RPC test response code: {response.status_code}")
            
            # Check for successful response
            if response.status_code == 200 and '<fault>' not in response.text.lower():
                logger.info("XML-RPC connection successful")
                # Try to parse out blog info from response
                try:
                    root = ET.fromstring(response.text)
                    logger.info(f"Parsed XML-RPC response successfully")
                    return True
                except Exception as e:
                    logger.error(f"Error parsing XML-RPC response: {e}")
                    # Still return True if we got a 200 response
                    return True
            else:
                logger.error(f"XML-RPC connection failed: {response.status_code}")
                logger.error(f"Response: {response.text[:200]}...")
                return False
                
        except Exception as e:
            logger.error(f"XML-RPC connection test failed: {str(e)}")
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
            # Log the basic post details
            logger.info(f"Creating post with title: {title[:30]}...")
            logger.info(f"Content length: {len(content) if content else 0} characters")
            logger.info(f"Status: {status}")
            
            # Check if we should use XML-RPC instead of REST API
            if self.use_xmlrpc:
                logger.info("Using XML-RPC to create post")
                return self._create_post_xmlrpc(title, content, status, categories, tags)
                
            # Otherwise use REST API
            endpoint = f"{self.api_url}/posts"
            logger.info(f"Using REST API to create post at: {endpoint}")
            
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
            if success and response is not None:
                try:
                    json_response = response.json()
                    return {
                        'success': True,
                        'post_id': json_response.get('id'),
                        'post_url': json_response.get('link'),
                        'edit_url': json_response.get('_links', {}).get('wp:action-edit', [{}])[0].get('href'),
                    }
                except Exception as e:
                    logger.error(f"Error parsing JSON response: {str(e)}")
                    # Return success but with limited details
                    return {
                        'success': True,
                        'post_id': 'unknown',
                        'post_url': '#',
                        'edit_url': '#',
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
                        
                        # As a fallback, try XML-RPC if REST API fails with 403
                        logger.info("REST API failed with 403, trying XML-RPC as fallback")
                        return self._create_post_xmlrpc(title, content, status, categories, tags)
                    
                    return {
                        'success': False,
                        'error': f"Error {response.status_code}: {response.text}"
                    }
                else:
                    # Try XML-RPC as a last resort
                    logger.info("All REST API methods failed, trying XML-RPC as fallback")
                    return self._create_post_xmlrpc(title, content, status, categories, tags)
                
        except Exception as e:
            logger.error(f"Exception creating WordPress post: {str(e)}")
            return {
                'success': False,
                'error': f"Error creating WordPress post: {str(e)}"
            }
            
    def _create_post_xmlrpc(self, title, content, status='draft', categories=None, tags=None):
        """Create a post using XML-RPC"""
        try:
            logger.info(f"Creating post via XML-RPC: {title[:30]}...")
            
            # Build content struct
            post_content = {
                'post_title': title,
                'post_content': content,
                'post_status': status,
            }
            
            # Add categories if provided
            if categories:
                post_content['terms_names'] = {'category': categories}
                
            # Add tags if provided
            if tags:
                if 'terms_names' not in post_content:
                    post_content['terms_names'] = {}
                post_content['terms_names']['post_tag'] = tags
            
            # Create XML-RPC request
            xml_request = f"""<?xml version="1.0"?>
            <methodCall>
              <methodName>wp.newPost</methodName>
              <params>
                <param><value><string>1</string></value></param>
                <param><value><string>{self.username}</string></value></param>
                <param><value><string>{self.password}</string></value></param>
                <param>
                  <value>
                    <struct>
                      <member>
                        <name>post_title</name>
                        <value><string>{title}</string></value>
                      </member>
                      <member>
                        <name>post_content</name>
                        <value><string>{content}</string></value>
                      </member>
                      <member>
                        <name>post_status</name>
                        <value><string>{status}</string></value>
                      </member>
                    </struct>
                  </value>
                </param>
              </params>
            </methodCall>
            """
            
            logger.info(f"Sending XML-RPC request to {self.xmlrpc_url}")
            
            # Send the request
            headers = {'Content-Type': 'text/xml'}
            response = requests.post(
                self.xmlrpc_url,
                data=xml_request,
                headers=headers,
                timeout=20
            )
            
            logger.info(f"XML-RPC response code: {response.status_code}")
            
            # Check for successful response
            if response.status_code == 200 and '<fault>' not in response.text.lower():
                logger.info("XML-RPC post creation successful")
                
                # Try to parse the post ID from the response
                try:
                    # Extract post ID from XML response
                    root = ET.fromstring(response.text)
                    # The post ID is in the response as an integer
                    post_id = None
                    for value in root.findall('.//value'):
                        try:
                            post_id = value.find('string').text
                            break
                        except:
                            pass
                        
                    logger.info(f"Created post with ID: {post_id}")
                    
                    return {
                        'success': True,
                        'post_id': post_id,
                        'post_url': f"{self.base_url}/?p={post_id}",
                        'edit_url': f"{self.base_url}/wp-admin/post.php?post={post_id}&action=edit",
                    }
                except Exception as e:
                    logger.error(f"Error parsing XML-RPC response: {e}")
                    # Still return success if we got a 200 response
                    return {
                        'success': True,
                        'post_id': 'unknown',
                        'post_url': '#',
                        'edit_url': '#',
                    }
            else:
                logger.error(f"XML-RPC post creation failed")
                logger.error(f"Response: {response.text[:200]}...")
                
                # Try to parse fault from response
                fault_msg = "Unknown error"
                try:
                    if '<fault>' in response.text.lower():
                        root = ET.fromstring(response.text)
                        fault = root.find('.//fault')
                        if fault:
                            fault_msg = ET.tostring(fault, encoding='unicode')
                except:
                    pass
                
                return {
                    'success': False,
                    'error': f"XML-RPC error: {fault_msg}"
                }
                
        except Exception as e:
            logger.error(f"Exception in XML-RPC post creation: {str(e)}")
            return {
                'success': False,
                'error': f"Error creating WordPress post via XML-RPC: {str(e)}"
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