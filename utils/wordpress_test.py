import logging
from datetime import datetime
from .fixed_wordpress_api import WordPressAPI

logger = logging.getLogger(__name__)

def test_simple_update(api_url, username, password, post_id):
    """
    Test a simple, visible update to a WordPress post
    """
    try:
        # Initialize API
        wp = WordPressAPI(api_url, username, password)
        
        # Create a very visible test content with timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        test_content = f"""
        <div style="border: 5px solid red; padding: 20px; background: yellow; margin: 20px 0;">
            <h2>TEST UPDATE - {timestamp}</h2>
            <p>If you can see this red-bordered box with timestamp {timestamp}, the update worked!</p>
            <p>This content was added by the Blog Generator update test.</p>
        </div>
        """
        
        # First, get the current post
        logger.info(f"Fetching post {post_id} to check current state...")
        current_post = wp.get_post(post_id)
        
        if not current_post:
            return {
                'success': False,
                'error': f'Post {post_id} not found'
            }
        
        logger.info(f"Current post status: {current_post.get('status')}")
        logger.info(f"Current post title: {current_post.get('title')}")
        
        # Update with very simple content
        logger.info("Attempting simple update...")
        result = wp.update_post(
            post_id=post_id,
            title=f"TEST UPDATE - {timestamp}",
            content=test_content,
            status='publish',  # Force publish to ensure it's live
            preserve_elementor=False  # Don't preserve Elementor for this test
        )
        
        if result.get('success'):
            logger.info("Update reported as successful")
            
            # Verify the update
            logger.info("Verifying update...")
            updated_post = wp.get_post(post_id)
            
            return {
                'success': True,
                'message': 'Update completed',
                'timestamp': timestamp,
                'post_url': result.get('post_url'),
                'edit_url': result.get('edit_url'),
                'original_status': current_post.get('status'),
                'new_status': updated_post.get('status') if updated_post else 'unknown',
                'content_preview': updated_post.get('content', '')[:200] if updated_post else ''
            }
        else:
            return {
                'success': False,
                'error': result.get('error', 'Unknown error')
            }
            
    except Exception as e:
        logger.error(f"Test update failed: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }

def check_elementor_status(api_url, username, password, post_id):
    """
    Check if a post is using Elementor and what data it has
    """
    try:
        wp = WordPressAPI(api_url, username, password)
        
        # Get post with edit context to see meta fields
        post = wp.get_post(post_id, context='edit')
        
        if not post:
            return {'error': 'Post not found'}
        
        meta = post.get('meta', {})
        
        return {
            'post_id': post_id,
            'has_meta': bool(meta),
            'meta_fields': list(meta.keys()),
            'has_elementor_data': '_elementor_data' in meta,
            'elementor_data_length': len(meta.get('_elementor_data', '')) if '_elementor_data' in meta else 0,
            'elementor_edit_mode': meta.get('_elementor_edit_mode', 'not found'),
            'post_status': post.get('status'),
            'content_length': len(post.get('content', ''))
        }
        
    except Exception as e:
        return {'error': str(e)}