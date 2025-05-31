#!/usr/bin/env python3
"""
Test script to diagnose WordPress update issues
Run this script to perform a comprehensive test of WordPress post updates
"""

import os
import sys
import logging
from datetime import datetime

# Add the project directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import the WordPress API and debug utilities
try:
    from utils.fixed_wordpress_api import WordPressAPI
except ImportError:
    from utils.wordpress_api import WordPressAPI

from utils.wordpress_debug import WordPressDebugger, create_simple_test_update_function, print_checklist

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Main test function"""
    print("\n" + "="*80)
    print("WORDPRESS UPDATE DIAGNOSTIC TOOL")
    print("="*80)
    print("\nThis tool will help diagnose why WordPress updates aren't showing.")
    print("\nYou'll need:")
    print("  1. WordPress site URL")
    print("  2. WordPress username") 
    print("  3. WordPress password or application password")
    print("  4. (Optional) An existing post ID to test updates on")
    print("\n" + "-"*80)
    
    # Get credentials
    wp_url = input("\nWordPress URL (e.g., https://example.com): ").strip()
    if not wp_url:
        print("ERROR: WordPress URL is required")
        return
    
    wp_username = input("WordPress username: ").strip()
    if not wp_username:
        print("ERROR: WordPress username is required")
        return
    
    wp_password = input("WordPress password (or application password): ").strip()
    if not wp_password:
        print("ERROR: WordPress password is required")
        return
    
    # Optional: get existing post ID
    post_id_str = input("\n(Optional) Enter an existing post ID to test, or press Enter to create a new test post: ").strip()
    test_post_id = int(post_id_str) if post_id_str.isdigit() else None
    
    print("\n" + "-"*80)
    print("Starting diagnostic tests...")
    print("-"*80)
    
    try:
        # Initialize WordPress API
        logger.info("Initializing WordPress API...")
        wp_api = WordPressAPI(wp_url, wp_username, wp_password)
        
        # Create debugger instance
        debugger = WordPressDebugger(wp_api)
        
        # Run comprehensive test
        results = debugger.run_comprehensive_test(test_post_id)
        
        # Ask if user wants to run a simple update test
        if results['summary']['passed_tests'] > 0:
            print("\n" + "-"*80)
            response = input("\nWould you like to run a simple visual update test? (y/n): ").strip().lower()
            
            if response == 'y':
                # Get post ID for simple test
                if test_post_id:
                    simple_test_id = test_post_id
                else:
                    simple_test_id = input("Enter post ID for simple update test: ").strip()
                    if not simple_test_id.isdigit():
                        print("Invalid post ID")
                        return
                    simple_test_id = int(simple_test_id)
                
                # Run simple update test
                print(f"\nRunning simple update test on post {simple_test_id}...")
                test_update = create_simple_test_update_function(wp_api)
                result = test_update(simple_test_id)
                
                if result.get('success'):
                    print(f"\n✓ Update sent successfully!")
                    print(f"→ Check your post at: {wp_url}/?p={simple_test_id}")
                    print(f"→ Edit in WordPress admin: {wp_url}/wp-admin/post.php?post={simple_test_id}&action=edit")
                    print("\nLook for a RED BORDERED BOX with the current timestamp.")
                    print("If you don't see it, check the recommendations above.")
                else:
                    print(f"\n✗ Update failed: {result.get('error', 'Unknown error')}")
        
        # Ask if user wants to see the troubleshooting checklist
        print("\n" + "-"*80)
        response = input("\nWould you like to see the troubleshooting checklist? (y/n): ").strip().lower()
        if response == 'y':
            print_checklist()
        
        # Save results to file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = f"wordpress_debug_report_{timestamp}.json"
        
        import json
        with open(report_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        print(f"\n✓ Diagnostic report saved to: {report_file}")
        
    except Exception as e:
        logger.error(f"ERROR: {str(e)}")
        logger.exception("Full error details:")
        print(f"\n✗ Test failed with error: {str(e)}")
        print("\nCheck the logs above for more details.")


def quick_test():
    """Quick test using environment variables"""
    print("\nRunning quick test using environment variables...")
    
    # Try to get credentials from environment
    wp_url = os.getenv('WORDPRESS_URL')
    wp_username = os.getenv('WORDPRESS_USERNAME')
    wp_password = os.getenv('WORDPRESS_PASSWORD')
    test_post_id = os.getenv('TEST_POST_ID')
    
    if not all([wp_url, wp_username, wp_password]):
        print("ERROR: Set environment variables WORDPRESS_URL, WORDPRESS_USERNAME, and WORDPRESS_PASSWORD")
        print("Optional: Set TEST_POST_ID to test on existing post")
        return
    
    try:
        # Initialize WordPress API
        wp_api = WordPressAPI(wp_url, wp_username, wp_password)
        
        # Create debugger instance
        debugger = WordPressDebugger(wp_api)
        
        # Run comprehensive test
        test_id = int(test_post_id) if test_post_id and test_post_id.isdigit() else None
        results = debugger.run_comprehensive_test(test_id)
        
        # Save results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = f"wordpress_debug_report_{timestamp}.json"
        
        import json
        with open(report_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        print(f"\n✓ Report saved to: {report_file}")
        
    except Exception as e:
        logger.error(f"Quick test failed: {str(e)}")


if __name__ == "__main__":
    # Check if running in quick mode
    if "--quick" in sys.argv:
        quick_test()
    else:
        main()