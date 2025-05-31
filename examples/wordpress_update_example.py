#!/usr/bin/env python3
"""
Example script showing the correct way to update WordPress posts
This handles both standard WordPress and Elementor-based posts
"""

import os
import sys
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.fixed_wordpress_api import WordPressAPI
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def update_standard_post(wp_api, post_id):
    """
    Example: Update a standard WordPress post (non-Elementor)
    """
    logger.info(f"\n{'='*60}")
    logger.info("EXAMPLE 1: Updating Standard WordPress Post")
    logger.info(f"{'='*60}")
    
    # IMPORTANT: Always include status='publish' to update the live post
    result = wp_api.update_post(
        post_id=post_id,
        title=f"Updated Post - {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        content=f"""
        <h2>This post was updated via REST API</h2>
        <p>Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        <p>The key to successful updates:</p>
        <ul>
            <li>Always include status='publish'</li>
            <li>Clear caches after updating</li>
            <li>Verify the update was applied</li>
        </ul>
        """,
        status='publish'  # Critical! Without this, WordPress may create a revision
    )
    
    if result['success']:
        logger.info(f"✓ Post updated successfully!")
        logger.info(f"  Post ID: {result['post_id']}")
        logger.info(f"  Modified: {result['modified']}")
        logger.info(f"  View at: {result['post_url']}")
        logger.info(f"  Edit at: {result['edit_url']}")
    else:
        logger.error(f"✗ Update failed: {result['error']}")
    
    return result


def update_elementor_post(wp_api, post_id):
    """
    Example: Update an Elementor-based post correctly
    """
    logger.info(f"\n{'='*60}")
    logger.info("EXAMPLE 2: Updating Elementor Post")
    logger.info(f"{'='*60}")
    
    # For Elementor posts, we need to preserve the Elementor data
    result = wp_api.update_post(
        post_id=post_id,
        title=f"Elementor Post Updated - {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        content=f"""
        <p>This content is for SEO and fallback display.</p>
        <p>Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        <p>Note: If Elementor is active, the frontend may show Elementor's rendered content instead.</p>
        """,
        status='publish',
        preserve_elementor=True  # This preserves Elementor's _elementor_data
    )
    
    if result['success']:
        logger.info(f"✓ Elementor post updated successfully!")
        logger.info(f"  Post ID: {result['post_id']}")
        logger.info(f"  Modified: {result['modified']}")
        logger.info("  Note: Elementor content preserved")
    else:
        logger.error(f"✗ Update failed: {result['error']}")
    
    return result


def verify_update(wp_api, post_id, expected_content):
    """
    Example: Verify that an update was applied
    """
    logger.info(f"\n{'='*60}")
    logger.info("EXAMPLE 3: Verifying Update")
    logger.info(f"{'='*60}")
    
    # Fetch the post
    post = wp_api.get_post(post_id)
    
    if post:
        logger.info(f"Post fetched successfully:")
        logger.info(f"  Title: {post['title']}")
        logger.info(f"  Status: {post['status']}")
        logger.info(f"  Modified: {post['modified']}")
        
        # Check if our content is present
        if expected_content in post['content']:
            logger.info(f"✓ Expected content found in post!")
        else:
            logger.warning(f"✗ Expected content NOT found in post")
            logger.info(f"  Content preview: {post['content'][:200]}...")
    else:
        logger.error("✗ Could not fetch post")
    
    return post


def bulk_update_example(wp_api, post_ids):
    """
    Example: Bulk update multiple posts with error handling
    """
    logger.info(f"\n{'='*60}")
    logger.info("EXAMPLE 4: Bulk Update with Error Handling")
    logger.info(f"{'='*60}")
    
    success_count = 0
    error_count = 0
    
    for post_id in post_ids:
        try:
            logger.info(f"\nUpdating post {post_id}...")
            
            # Get current post to preserve some data
            current_post = wp_api.get_post(post_id)
            if not current_post:
                logger.error(f"  ✗ Post {post_id} not found")
                error_count += 1
                continue
            
            # Update with new content
            result = wp_api.update_post(
                post_id=post_id,
                title=current_post['title'],  # Keep existing title
                content=f"""
                {current_post['content']}
                <hr>
                <p><em>Bulk updated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</em></p>
                """,
                status='publish'
            )
            
            if result['success']:
                logger.info(f"  ✓ Post {post_id} updated")
                success_count += 1
            else:
                logger.error(f"  ✗ Post {post_id} failed: {result['error']}")
                error_count += 1
                
        except Exception as e:
            logger.error(f"  ✗ Error updating post {post_id}: {str(e)}")
            error_count += 1
    
    logger.info(f"\nBulk update complete:")
    logger.info(f"  ✓ Success: {success_count}")
    logger.info(f"  ✗ Errors: {error_count}")


def main():
    """
    Main example runner
    """
    print("\nWordPress Update Examples")
    print("=" * 60)
    print("\nThis script demonstrates the correct way to update WordPress posts.")
    print("\nYou can run specific examples or use it as a reference.")
    
    # Check for credentials
    wp_url = os.getenv('WORDPRESS_URL')
    wp_username = os.getenv('WORDPRESS_USERNAME')
    wp_password = os.getenv('WORDPRESS_PASSWORD')
    
    if not all([wp_url, wp_username, wp_password]):
        print("\nTo run these examples, set environment variables:")
        print("  export WORDPRESS_URL='https://your-site.com'")
        print("  export WORDPRESS_USERNAME='your-username'")
        print("  export WORDPRESS_PASSWORD='your-app-password'")
        print("\nOr modify this script with your credentials.")
        return
    
    # Initialize WordPress API
    try:
        wp_api = WordPressAPI(wp_url, wp_username, wp_password)
        
        # Test connection
        if not wp_api.test_connection():
            print("\n✗ Failed to connect to WordPress API")
            return
        
        print("\n✓ Connected to WordPress successfully!")
        
        # Get a test post ID
        test_post_id = input("\nEnter a post ID to test updates (or press Enter to skip): ").strip()
        
        if test_post_id and test_post_id.isdigit():
            post_id = int(test_post_id)
            
            # Run examples
            print("\nWhich example would you like to run?")
            print("1. Update standard post")
            print("2. Update Elementor post")
            print("3. Verify update")
            print("4. All examples")
            
            choice = input("\nEnter choice (1-4): ").strip()
            
            if choice == '1' or choice == '4':
                update_standard_post(wp_api, post_id)
            
            if choice == '2' or choice == '4':
                update_elementor_post(wp_api, post_id)
            
            if choice == '3' or choice == '4':
                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                verify_update(wp_api, post_id, timestamp)
        
        else:
            print("\nNo post ID provided. Showing example code only.")
            print("\nExample usage:")
            print("```python")
            print("# Initialize API")
            print("wp_api = WordPressAPI('https://site.com', 'user', 'pass')")
            print("")
            print("# Update a post (ALWAYS include status='publish')")
            print("result = wp_api.update_post(")
            print("    post_id=123,")
            print("    title='Updated Title',")
            print("    content='<p>Updated content</p>',")
            print("    status='publish'  # Critical!")
            print(")")
            print("```")
            
    except Exception as e:
        logger.error(f"Error: {str(e)}")


if __name__ == "__main__":
    main()