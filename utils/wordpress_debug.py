"""
WordPress Update Debug Utilities
This module provides comprehensive debugging tools to diagnose why WordPress updates aren't showing.
"""

import requests
import json
import logging
from datetime import datetime
from typing import Dict, Optional, List

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class WordPressDebugger:
    def __init__(self, wp_api_instance):
        """Initialize with an existing WordPressAPI instance"""
        self.wp = wp_api_instance
        self.test_results = []
    
    def run_comprehensive_test(self, test_post_id: Optional[int] = None) -> Dict:
        """
        Run a comprehensive test suite to diagnose WordPress update issues
        
        :param test_post_id: Optional existing post ID to test. If None, creates a new test post
        :return: Dictionary with all test results
        """
        logger.info("=" * 80)
        logger.info("STARTING WORDPRESS UPDATE DIAGNOSTIC TEST SUITE")
        logger.info("=" * 80)
        
        results = {
            'timestamp': datetime.now().isoformat(),
            'tests': [],
            'summary': {}
        }
        
        # Test 1: Basic Connection
        logger.info("\n[TEST 1] Testing basic WordPress connection...")
        connection_test = self._test_connection()
        results['tests'].append(connection_test)
        
        # Test 2: Create Test Post
        logger.info("\n[TEST 2] Creating test post...")
        if not test_post_id:
            create_test = self._test_create_post()
            results['tests'].append(create_test)
            if create_test['success']:
                test_post_id = create_test['post_id']
        
        # Test 3: Update Test
        if test_post_id:
            logger.info(f"\n[TEST 3] Testing post update on ID: {test_post_id}...")
            update_test = self._test_update_post(test_post_id)
            results['tests'].append(update_test)
            
            # Test 4: Verify Update
            logger.info("\n[TEST 4] Verifying update was applied...")
            verify_test = self._test_verify_update(test_post_id, update_test.get('update_marker', ''))
            results['tests'].append(verify_test)
            
            # Test 5: Check Revisions
            logger.info("\n[TEST 5] Checking WordPress revisions...")
            revision_test = self._test_check_revisions(test_post_id)
            results['tests'].append(revision_test)
            
            # Test 6: Meta Fields Access
            logger.info("\n[TEST 6] Testing meta field access...")
            meta_test = self._test_meta_fields(test_post_id)
            results['tests'].append(meta_test)
            
            # Test 7: Elementor Detection
            logger.info("\n[TEST 7] Checking for Elementor...")
            elementor_test = self._test_elementor_detection(test_post_id)
            results['tests'].append(elementor_test)
        
        # Generate summary
        results['summary'] = self._generate_summary(results['tests'])
        
        # Print comprehensive report
        self._print_report(results)
        
        return results
    
    def _test_connection(self) -> Dict:
        """Test basic WordPress API connection"""
        try:
            success = self.wp.test_connection()
            return {
                'name': 'Basic Connection',
                'success': success,
                'details': 'WordPress API connection successful' if success else 'Connection failed'
            }
        except Exception as e:
            return {
                'name': 'Basic Connection',
                'success': False,
                'error': str(e)
            }
    
    def _test_create_post(self) -> Dict:
        """Create a test post"""
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            test_title = f"Debug Test Post - {timestamp}"
            test_content = f"""
            <h2>Debug Test Post</h2>
            <p>Created at: {timestamp}</p>
            <p>This post is used to test WordPress update functionality.</p>
            <p class="test-marker">Initial content marker: INITIAL_{timestamp}</p>
            """
            
            result = self.wp.create_post(test_title, test_content, status='draft')
            
            return {
                'name': 'Create Test Post',
                'success': result.get('success', False),
                'post_id': result.get('post_id'),
                'details': f"Post ID: {result.get('post_id')}" if result.get('success') else result.get('error')
            }
        except Exception as e:
            return {
                'name': 'Create Test Post',
                'success': False,
                'error': str(e)
            }
    
    def _test_update_post(self, post_id: int) -> Dict:
        """Test updating a post"""
        try:
            update_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
            update_marker = f"UPDATED_{update_timestamp}"
            
            # First, try with fixed_wordpress_api if available
            if hasattr(self.wp, 'update_post'):
                logger.info("Using update_post method from fixed_wordpress_api")
                
                updated_title = f"Debug Test Post - Updated at {update_timestamp}"
                updated_content = f"""
                <h2>Debug Test Post - UPDATED</h2>
                <p>Original creation time: Check revision history</p>
                <p><strong>Last updated at: {update_timestamp}</strong></p>
                <p class="test-marker">Update marker: {update_marker}</p>
                <ul>
                    <li>This content was updated via WordPress REST API</li>
                    <li>If you see this, the update was successful</li>
                    <li>Check WordPress admin to verify</li>
                </ul>
                """
                
                # Test both with and without preserving Elementor
                result = self.wp.update_post(
                    post_id=post_id,
                    title=updated_title,
                    content=updated_content,
                    status='publish',  # Force publish status
                    preserve_elementor=True
                )
                
                return {
                    'name': 'Update Post',
                    'success': result.get('success', False),
                    'post_id': post_id,
                    'update_marker': update_marker,
                    'method': 'update_post',
                    'details': f"Modified: {result.get('modified')}" if result.get('success') else result.get('error')
                }
            else:
                # Fallback to manual PUT request
                logger.info("Using manual PUT request for update")
                
                endpoint = f"{self.wp.api_url}/posts/{post_id}"
                
                updated_title = f"Debug Test Post - Updated at {update_timestamp}"
                updated_content = f"""
                <h2>Debug Test Post - UPDATED via Manual PUT</h2>
                <p>Updated at: {update_timestamp}</p>
                <p class="test-marker">Update marker: {update_marker}</p>
                """
                
                post_data = {
                    'title': updated_title,
                    'content': updated_content,
                    'status': 'publish'
                }
                
                headers = self.wp.standard_headers.copy()
                headers.update(self.wp.auth_header)
                
                response = requests.put(
                    endpoint,
                    headers=headers,
                    json=post_data,
                    timeout=20
                )
                
                success = response.status_code in (200, 201)
                
                return {
                    'name': 'Update Post',
                    'success': success,
                    'post_id': post_id,
                    'update_marker': update_marker,
                    'method': 'manual_put',
                    'status_code': response.status_code,
                    'details': f"Status: {response.status_code}" if success else response.text[:200]
                }
                
        except Exception as e:
            return {
                'name': 'Update Post',
                'success': False,
                'error': str(e)
            }
    
    def _test_verify_update(self, post_id: int, update_marker: str) -> Dict:
        """Verify the update was applied"""
        try:
            # Get the post with both contexts
            post_view = self.wp.get_post(post_id, context='view')
            post_edit = self.wp.get_post(post_id, context='edit')
            
            if not post_view:
                return {
                    'name': 'Verify Update',
                    'success': False,
                    'details': 'Could not fetch post'
                }
            
            # Check if update marker is present
            content = post_view.get('content', '')
            marker_found = update_marker in content
            
            # Get modification times
            modified = post_view.get('modified', 'unknown')
            
            # Check status
            status = post_view.get('status', 'unknown')
            
            return {
                'name': 'Verify Update',
                'success': marker_found,
                'post_id': post_id,
                'marker_found': marker_found,
                'post_status': status,
                'modified_date': modified,
                'content_preview': content[:200] + '...' if len(content) > 200 else content,
                'details': f"Update marker {'found' if marker_found else 'NOT FOUND'} in content. Status: {status}"
            }
            
        except Exception as e:
            return {
                'name': 'Verify Update',
                'success': False,
                'error': str(e)
            }
    
    def _test_check_revisions(self, post_id: int) -> Dict:
        """Check post revisions"""
        try:
            endpoint = f"{self.wp.api_url}/posts/{post_id}/revisions"
            
            headers = self.wp.standard_headers.copy()
            headers.update(self.wp.auth_header)
            
            response = requests.get(
                endpoint,
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                revisions = response.json()
                
                return {
                    'name': 'Check Revisions',
                    'success': True,
                    'revision_count': len(revisions),
                    'latest_revision': revisions[0] if revisions else None,
                    'details': f"Found {len(revisions)} revisions"
                }
            else:
                return {
                    'name': 'Check Revisions',
                    'success': False,
                    'status_code': response.status_code,
                    'details': 'Could not fetch revisions - this is normal if revisions are disabled'
                }
                
        except Exception as e:
            return {
                'name': 'Check Revisions',
                'success': False,
                'error': str(e)
            }
    
    def _test_meta_fields(self, post_id: int) -> Dict:
        """Test meta field access"""
        try:
            if hasattr(self.wp, 'test_meta_fields'):
                return self.wp.test_meta_fields(post_id)
            else:
                # Manual test
                post = self.wp.get_post(post_id, context='edit')
                
                if post and 'meta' in post:
                    meta_keys = list(post['meta'].keys())
                    has_elementor = '_elementor_data' in meta_keys
                    
                    return {
                        'name': 'Meta Fields Access',
                        'success': True,
                        'meta_field_count': len(meta_keys),
                        'has_elementor_meta': has_elementor,
                        'meta_keys': meta_keys[:10],  # First 10 keys
                        'details': f"Found {len(meta_keys)} meta fields. Elementor: {'Yes' if has_elementor else 'No'}"
                    }
                else:
                    return {
                        'name': 'Meta Fields Access',
                        'success': False,
                        'details': 'No meta fields found or access denied'
                    }
                    
        except Exception as e:
            return {
                'name': 'Meta Fields Access',
                'success': False,
                'error': str(e)
            }
    
    def _test_elementor_detection(self, post_id: int) -> Dict:
        """Detect if Elementor is being used"""
        try:
            post = self.wp.get_post(post_id, context='edit')
            
            if not post:
                return {
                    'name': 'Elementor Detection',
                    'success': False,
                    'details': 'Could not fetch post'
                }
            
            # Check various Elementor indicators
            checks = {
                'has_elementor_class': 'elementor' in post.get('content', ''),
                'has_elementor_meta': False,
                'elementor_edit_mode': None,
                'elementor_data_length': 0
            }
            
            if 'meta' in post:
                meta = post['meta']
                checks['has_elementor_meta'] = '_elementor_data' in meta
                checks['elementor_edit_mode'] = meta.get('_elementor_edit_mode')
                
                if '_elementor_data' in meta and meta['_elementor_data']:
                    checks['elementor_data_length'] = len(meta['_elementor_data'])
            
            elementor_active = checks['has_elementor_class'] or checks['has_elementor_meta']
            
            return {
                'name': 'Elementor Detection',
                'success': True,
                'elementor_active': elementor_active,
                'checks': checks,
                'details': f"Elementor {'detected' if elementor_active else 'not detected'}"
            }
            
        except Exception as e:
            return {
                'name': 'Elementor Detection',
                'success': False,
                'error': str(e)
            }
    
    def _generate_summary(self, tests: List[Dict]) -> Dict:
        """Generate a summary of all tests"""
        total_tests = len(tests)
        passed_tests = sum(1 for test in tests if test.get('success', False))
        
        issues = []
        recommendations = []
        
        # Analyze results
        for test in tests:
            if not test.get('success', False):
                if test['name'] == 'Basic Connection':
                    issues.append("WordPress API connection failed")
                    recommendations.append("Check WordPress URL, username, and password")
                    recommendations.append("Verify REST API is enabled")
                    
                elif test['name'] == 'Update Post':
                    issues.append("Post update failed")
                    recommendations.append("Check user permissions for editing posts")
                    recommendations.append("Verify the post exists and is not locked")
                    
                elif test['name'] == 'Verify Update':
                    issues.append("Update was sent but changes not visible")
                    recommendations.append("Check if WordPress caching is enabled")
                    recommendations.append("Verify post status (should be 'publish' not 'draft')")
                    recommendations.append("Check for revision instead of live update")
        
        # Check for Elementor-specific issues
        elementor_test = next((t for t in tests if t['name'] == 'Elementor Detection'), None)
        if elementor_test and elementor_test.get('elementor_active'):
            issues.append("Elementor is active on this post")
            recommendations.append("Elementor stores content in _elementor_data meta field")
            recommendations.append("Standard content updates may not show on frontend")
            recommendations.append("See elementorfix.md for Elementor-specific update process")
        
        # Check meta field access
        meta_test = next((t for t in tests if t['name'] == 'Meta Fields Access'), None)
        if meta_test and not meta_test.get('has_elementor_meta', False) and elementor_test and elementor_test.get('elementor_active'):
            issues.append("Elementor meta fields not accessible via REST API")
            recommendations.append("Add server-side code to expose Elementor meta fields")
            recommendations.append("See elementorfix.md section 2.1 for the required PHP code")
        
        return {
            'total_tests': total_tests,
            'passed_tests': passed_tests,
            'failed_tests': total_tests - passed_tests,
            'success_rate': f"{(passed_tests/total_tests)*100:.1f}%",
            'issues': issues,
            'recommendations': recommendations
        }
    
    def _print_report(self, results: Dict):
        """Print a formatted report"""
        logger.info("\n" + "=" * 80)
        logger.info("WORDPRESS UPDATE DIAGNOSTIC REPORT")
        logger.info("=" * 80)
        logger.info(f"Test run at: {results['timestamp']}")
        
        # Test results
        logger.info("\nTEST RESULTS:")
        logger.info("-" * 80)
        
        for test in results['tests']:
            status = "✓ PASS" if test.get('success') else "✗ FAIL"
            logger.info(f"{status} | {test['name']}: {test.get('details', 'No details')}")
            
            if not test.get('success') and 'error' in test:
                logger.error(f"      Error: {test['error']}")
        
        # Summary
        summary = results['summary']
        logger.info("\n" + "-" * 80)
        logger.info(f"SUMMARY: {summary['passed_tests']}/{summary['total_tests']} tests passed ({summary['success_rate']})")
        
        # Issues found
        if summary['issues']:
            logger.info("\nISSUES DETECTED:")
            for issue in summary['issues']:
                logger.warning(f"  • {issue}")
        
        # Recommendations
        if summary['recommendations']:
            logger.info("\nRECOMMENDATIONS:")
            for rec in summary['recommendations']:
                logger.info(f"  → {rec}")
        
        logger.info("\n" + "=" * 80)


def create_simple_test_update_function(wp_api_instance):
    """
    Create a simple function to test WordPress post updates
    
    Usage:
        test_update = create_simple_test_update_function(wp_api)
        result = test_update(post_id=123)
    """
    def test_update(post_id: int) -> Dict:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        logger.info(f"\nTesting simple update on post {post_id}...")
        logger.info(f"Timestamp: {timestamp}")
        
        # Create unique content
        test_content = f"""
        <div style="border: 2px solid red; padding: 20px; margin: 20px 0;">
            <h2>🔧 TEST UPDATE - {timestamp}</h2>
            <p>If you can see this box with the timestamp above, the update was successful!</p>
            <ul>
                <li>Update method: WordPress REST API</li>
                <li>Timestamp: {timestamp}</li>
                <li>Post ID: {post_id}</li>
            </ul>
        </div>
        """
        
        try:
            # Try to update
            if hasattr(wp_api_instance, 'update_post'):
                result = wp_api_instance.update_post(
                    post_id=post_id,
                    title=f"Test Update - {timestamp}",
                    content=test_content,
                    status='publish'
                )
            else:
                # Fallback to manual update
                endpoint = f"{wp_api_instance.api_url}/posts/{post_id}"
                headers = wp_api_instance.standard_headers.copy()
                headers.update(wp_api_instance.auth_header)
                
                response = requests.put(
                    endpoint,
                    headers=headers,
                    json={
                        'title': f"Test Update - {timestamp}",
                        'content': test_content,
                        'status': 'publish'
                    }
                )
                
                result = {
                    'success': response.status_code in (200, 201),
                    'status_code': response.status_code
                }
            
            logger.info(f"Update result: {result}")
            
            # Verify
            post = wp_api_instance.get_post(post_id)
            if post:
                logger.info(f"Post status: {post.get('status')}")
                logger.info(f"Post modified: {post.get('modified')}")
                logger.info(f"Timestamp in content: {timestamp in post.get('content', '')}")
            
            return result
            
        except Exception as e:
            logger.error(f"Test update failed: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    return test_update


# Common WordPress/Elementor Update Issues Checklist
WORDPRESS_UPDATE_CHECKLIST = """
WORDPRESS UPDATE TROUBLESHOOTING CHECKLIST
==========================================

1. AUTHENTICATION ISSUES
   □ Verify WordPress username and password are correct
   □ Check if using Application Password (should have spaces like "xxxx xxxx xxxx xxxx")
   □ Ensure user has 'edit_posts' capability
   □ Test with admin account to rule out permission issues

2. POST STATUS ISSUES  
   □ Always include 'status': 'publish' in update payload
   □ Without status, WordPress may create a revision instead of updating live post
   □ Check post status after update (should be 'publish' not 'draft')

3. CACHING ISSUES
   □ WordPress caching plugins (WP Super Cache, W3 Total Cache, etc.)
   □ Server-level caching (Varnish, Nginx, Cloudflare)
   □ Browser caching - test in incognito/private mode
   □ Elementor's own CSS/JS caching

4. ELEMENTOR-SPECIFIC ISSUES
   □ Elementor renders from _elementor_data meta field, not post content
   □ Standard content field updates won't show if Elementor is active
   □ _elementor_data must be registered with 'show_in_rest' => true
   □ Need to update both content (for SEO) and _elementor_data (for display)

5. REST API ISSUES
   □ Verify REST API is enabled (some security plugins disable it)
   □ Check .htaccess for REST API blocking rules
   □ Ensure permalink structure is not 'Plain' (REST API requires pretty permalinks)
   □ Test REST API discovery: GET /wp-json/

6. REVISION ISSUES
   □ Check if updates are creating revisions instead of updating main post
   □ Compare post modified date before/after update
   □ Check WordPress revision settings in wp-config.php

7. META FIELD ACCESS
   □ Custom fields must be registered with 'show_in_rest' => true
   □ Some plugins protect meta fields from REST API access
   □ Use context=edit when fetching posts to see meta fields

8. DEBUGGING STEPS
   □ Enable WordPress debug mode: define('WP_DEBUG', true);
   □ Check WordPress error logs
   □ Monitor browser network tab for API responses
   □ Test with a simple non-Elementor post first
   □ Use WordPress REST API explorer/documentation

9. COMMON FIXES
   □ Force publish status in updates
   □ Clear all caches after update
   □ For Elementor: update _elementor_data instead of content
   □ Add delay between update and verification (cache propagation)
   □ Use WordPress admin to manually save post (triggers cache clear)

10. SERVER CONFIGURATION
    □ Check PHP memory limit (min 256M for Elementor)
    □ Verify max_input_vars is sufficient (min 3000)
    □ Check mod_security rules that might block updates
    □ Ensure server timezone matches WordPress timezone
"""


def print_checklist():
    """Print the WordPress update troubleshooting checklist"""
    print(WORDPRESS_UPDATE_CHECKLIST)


if __name__ == "__main__":
    # This allows the module to be run standalone for testing
    print("WordPress Debug Utilities")
    print("========================")
    print("\nThis module provides debugging tools for WordPress update issues.")
    print("\nUsage:")
    print("  from wordpress_debug import WordPressDebugger, create_simple_test_update_function")
    print("  debugger = WordPressDebugger(wp_api_instance)")
    print("  results = debugger.run_comprehensive_test()")
    print("\nOr print the checklist:")
    print("  from wordpress_debug import print_checklist")
    print("  print_checklist()")