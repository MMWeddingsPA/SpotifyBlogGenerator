import logging
from datetime import datetime
from .fixed_wordpress_api import WordPressAPI
import json

logger = logging.getLogger(__name__)

def check_post_revisions(api_url, username, password, post_id):
    """
    Check post revisions and understand why updates aren't showing
    """
    try:
        wp = WordPressAPI(api_url, username, password)
        
        results = {
            'post_id': post_id,
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'checks': {}
        }
        
        # 1. Get the main post
        logger.info(f"Fetching post {post_id}...")
        post = wp.get_post(post_id, context='edit')
        
        if not post:
            return {'error': f'Post {post_id} not found'}
        
        results['post_status'] = post.get('status')
        results['post_modified'] = post.get('modified')
        results['post_title'] = post.get('title')
        
        # 2. Check for Elementor
        meta = post.get('meta', {})
        has_elementor = '_elementor_data' in meta
        results['has_elementor'] = has_elementor
        
        if has_elementor:
            elementor_data = meta.get('_elementor_data', '')
            results['elementor_data_length'] = len(elementor_data)
            
            # Check if Elementor data is valid JSON
            try:
                parsed = json.loads(elementor_data)
                results['elementor_valid_json'] = True
                results['elementor_sections'] = len(parsed) if isinstance(parsed, list) else 0
            except:
                results['elementor_valid_json'] = False
        
        # 3. Check revisions
        try:
            # Try to get revisions (this might not work via REST API without additional setup)
            revisions_url = f"{wp.api_url}/posts/{post_id}/revisions"
            headers = wp.standard_headers.copy()
            headers.update(wp.auth_header)
            
            import requests
            response = requests.get(revisions_url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                revisions = response.json()
                results['revision_count'] = len(revisions)
                
                # Get latest revision
                if revisions:
                    latest = revisions[0]
                    results['latest_revision'] = {
                        'id': latest.get('id'),
                        'date': latest.get('date'),
                        'modified': latest.get('modified'),
                        'author': latest.get('author')
                    }
            else:
                results['revisions_accessible'] = False
                results['revision_error'] = f"Status {response.status_code}"
        except Exception as e:
            results['revision_error'] = str(e)
        
        # 4. Diagnosis
        diagnosis = []
        
        if has_elementor:
            diagnosis.append("❌ Post uses Elementor - updates to content field won't show on frontend")
            
            if not meta:
                diagnosis.append("❌ Meta fields not accessible - Code Snippet may not be active")
            elif '_elementor_data' not in meta:
                diagnosis.append("❌ Elementor data not exposed to REST API")
            else:
                diagnosis.append("✅ Elementor data is accessible via REST API")
        
        if post.get('status') == 'draft':
            diagnosis.append("📝 Post is in draft status - changes won't show on public site")
        elif post.get('status') == 'publish':
            diagnosis.append("✅ Post is published")
        
        results['diagnosis'] = diagnosis
        
        # 5. Recommendations
        recommendations = []
        
        if has_elementor and '_elementor_data' not in meta:
            recommendations.append("1. Add the Code Snippet to expose Elementor meta fields")
            recommendations.append("2. Clear all caches after adding the snippet")
        
        if has_elementor:
            recommendations.append("3. Updates must modify _elementor_data, not just content field")
            recommendations.append("4. Or create new posts without Elementor for simpler updates")
        
        results['recommendations'] = recommendations
        
        return results
        
    except Exception as e:
        logger.error(f"Error checking revisions: {str(e)}")
        return {'error': str(e)}

def verify_elementor_endpoint(api_url):
    """
    Check if the Elementor verification endpoint is working
    """
    try:
        import requests
        verify_url = f"{api_url}/wp-json/spotify-blog/v1/verify-elementor-meta"
        
        response = requests.get(verify_url, timeout=5)
        
        if response.status_code == 200:
            return response.json()
        else:
            return {
                'success': False,
                'error': f'Endpoint returned status {response.status_code}',
                'message': 'Code Snippet may not be active'
            }
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'message': 'Could not reach verification endpoint'
        }