import requests
import base64
import os
import json
from datetime import datetime

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
        
        self.api_url = api_url.rstrip('/')
        self.username = username
        self.password = password
        self.auth_header = self._get_auth_header()
    
    def _get_auth_header(self):
        """Create authorization header using basic auth"""
        credentials = f"{self.username}:{self.password}"
        token = base64.b64encode(credentials.encode()).decode('utf-8')
        return {'Authorization': f'Basic {token}'}
    
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
            
            # Make API request
            response = requests.post(
                endpoint,
                headers=self.auth_header,
                json=post_data
            )
            
            # Check for success
            if response.status_code in (200, 201):
                return {
                    'success': True,
                    'post_id': response.json().get('id'),
                    'post_url': response.json().get('link'),
                    'edit_url': response.json().get('_links', {}).get('wp:action-edit', [{}])[0].get('href'),
                }
            else:
                return {
                    'success': False,
                    'error': f"Error {response.status_code}: {response.text}"
                }
                
        except Exception as e:
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