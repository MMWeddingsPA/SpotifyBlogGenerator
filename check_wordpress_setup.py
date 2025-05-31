#!/usr/bin/env python3
"""
WordPress Setup Checker
This script helps diagnose WordPress configuration issues
"""

import sys
import os
from datetime import datetime

# Add the project directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.fixed_wordpress_api import WordPressAPI
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_wordpress_setup(api_url, username, password, test_post_id=None):
    """
    Check various aspects of WordPress setup
    """
    print("\n" + "="*60)
    print("WORDPRESS SETUP DIAGNOSTIC")
    print("="*60 + "\n")
    
    try:
        # Initialize API
        wp = WordPressAPI(api_url, username, password)
        
        # 1. Test basic connection
        print("1. Testing API Connection...")
        if wp.test_connection():
            print("   ✓ API Connection successful")
        else:
            print("   ✗ API Connection failed")
            return
        
        # 2. Check API discovery
        print("\n2. Checking WordPress REST API...")
        import requests
        response = requests.get(f"{api_url}/wp-json")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✓ Site Name: {data.get('name', 'Unknown')}")
            print(f"   ✓ WordPress Version: {data.get('version', 'Unknown')}")
            namespaces = data.get('namespaces', [])
            print(f"   ✓ Available namespaces: {', '.join(namespaces[:5])}...")
            
            # Check for important plugins
            if 'elementor/v1' in namespaces:
                print("   ⚠️  Elementor API detected")
            if 'jwt-auth/v1' in namespaces:
                print("   ℹ️  JWT Authentication detected")
        
        # 3. Create a test post to check capabilities
        print("\n3. Testing Post Creation...")
        test_title = f"Diagnostic Test - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        test_content = "<p>This is a diagnostic test post. It can be safely deleted.</p>"
        
        result = wp.create_post(
            title=test_title,
            content=test_content,
            status='draft'
        )
        
        if result.get('success'):
            created_post_id = result.get('post_id')
            print(f"   ✓ Post created successfully (ID: {created_post_id})")
            
            # 4. Test meta field access
            print("\n4. Testing Meta Field Access...")
            post_with_edit = wp.get_post(created_post_id, context='edit')
            post_with_view = wp.get_post(created_post_id, context='view')
            
            if post_with_edit and post_with_edit.get('meta'):
                meta_fields = list(post_with_edit['meta'].keys())
                print(f"   ✓ Meta fields accessible with edit context: {len(meta_fields)} fields")
                if meta_fields:
                    print(f"   ℹ️  Sample fields: {', '.join(meta_fields[:5])}...")
                if '_elementor_data' in meta_fields:
                    print("   ✓ Elementor meta fields are exposed")
                else:
                    print("   ⚠️  Elementor meta fields NOT exposed (this is normal)")
            else:
                print("   ⚠️  No meta fields returned with edit context")
            
            if post_with_view and post_with_view.get('meta'):
                print("   ℹ️  Meta fields also visible in view context")
            else:
                print("   ℹ️  Meta fields not visible in view context (this is normal)")
            
            # 5. Test update capability
            print("\n5. Testing Post Update...")
            update_result = wp.update_post(
                post_id=created_post_id,
                title=test_title + " - UPDATED",
                content=test_content + "<p>Updated at " + datetime.now().strftime('%H:%M:%S') + "</p>",
                status='draft'
            )
            
            if update_result.get('success'):
                print("   ✓ Post update successful")
            else:
                print("   ✗ Post update failed")
        else:
            print(f"   ✗ Post creation failed: {result.get('error')}")
        
        # 6. Test specific post if provided
        if test_post_id:
            print(f"\n6. Checking Specific Post (ID: {test_post_id})...")
            post = wp.get_post(test_post_id, context='edit')
            if post:
                print(f"   ✓ Post found: {post.get('title', 'No title')}")
                print(f"   ℹ️  Status: {post.get('status')}")
                print(f"   ℹ️  Modified: {post.get('modified')}")
                
                meta = post.get('meta', {})
                if '_elementor_data' in meta:
                    print("   ⚠️  This post uses Elementor!")
                    print("   ℹ️  Elementor data length: " + str(len(meta['_elementor_data'])))
                else:
                    print("   ✓ This post does NOT use Elementor")
            else:
                print(f"   ✗ Post {test_post_id} not found")
        
        print("\n" + "="*60)
        print("RECOMMENDATIONS:")
        print("="*60)
        
        print("""
1. If Elementor meta fields are NOT exposed:
   - Add this code to /wp-content/mu-plugins/expose-elementor-meta.php:
   
   <?php
   add_action('init', function() {
       register_post_meta('post', '_elementor_data', [
           'show_in_rest' => true,
           'single' => true,
           'type' => 'string',
           'auth_callback' => function() { 
               return current_user_can('edit_posts'); 
           },
       ]);
   });

2. To see Custom Fields in WordPress admin:
   - They might be hidden in newer WordPress versions
   - Try installing "Advanced Custom Fields" plugin
   - Or use "Custom Field Suite" plugin

3. To verify updates are working:
   - Check WordPress admin → Posts → All Posts
   - Look in both "Published" and "Draft" tabs
   - Check post revision history

4. For Elementor posts:
   - Updates to 'content' field won't show on frontend
   - Must update '_elementor_data' or edit in Classic Editor
        """)
        
    except Exception as e:
        print(f"\n✗ Error during diagnostics: {str(e)}")
        logger.exception("Full error:")

if __name__ == "__main__":
    print("WordPress Setup Checker")
    print("-" * 30)
    
    # Get credentials
    api_url = input("WordPress URL (e.g., https://example.com): ").strip()
    username = input("WordPress username: ").strip()
    password = input("WordPress password: ").strip()
    
    test_post = input("Specific post ID to test (optional, press Enter to skip): ").strip()
    test_post_id = int(test_post) if test_post else None
    
    check_wordpress_setup(api_url, username, password, test_post_id)