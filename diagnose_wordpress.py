#!/usr/bin/env python3
"""
Simple diagnostic script for WordPress/Elementor issues
Run this from command line to bypass Streamlit UI issues
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.fixed_wordpress_api import WordPressAPI
from utils.revision_checker import verify_elementor_endpoint, check_post_revisions
from utils.wordpress_test import check_elementor_status
import json

def main():
    print("\n" + "="*60)
    print("WORDPRESS/ELEMENTOR DIAGNOSTIC TOOL")
    print("="*60 + "\n")
    
    # Get credentials
    print("Enter your WordPress credentials:")
    api_url = input("WordPress URL (e.g., https://example.com): ").strip()
    username = input("WordPress username: ").strip()
    password = input("WordPress password: ").strip()
    post_id = input("Post ID to check: ").strip()
    
    if not all([api_url, username, password, post_id]):
        print("❌ All fields are required!")
        return
    
    print("\n" + "-"*60)
    print("RUNNING DIAGNOSTICS...")
    print("-"*60 + "\n")
    
    # 1. Verify Code Snippet
    print("1. Checking Code Snippet Setup...")
    verify_result = verify_elementor_endpoint(api_url)
    
    if verify_result.get('success'):
        print("✅ Code Snippet is ACTIVE!")
        print(f"   Fields exposed: {verify_result.get('fields', {})}")
    else:
        print("❌ Code Snippet NOT FOUND!")
        print(f"   Error: {verify_result.get('error', 'Unknown')}")
        print("\n   ACTION REQUIRED:")
        print("   1. Go to WordPress Admin → Snippets → Add New")
        print("   2. Add the code from CODE_SNIPPETS_SETUP.md")
        print("   3. Activate the snippet")
    
    print("\n" + "-"*60)
    
    # 2. Check Elementor Status
    print("2. Checking Elementor Status...")
    try:
        elementor_status = check_elementor_status(api_url, username, password, int(post_id))
        
        if elementor_status.get('error'):
            print(f"❌ Error: {elementor_status['error']}")
        else:
            print(f"✅ Post found: ID {post_id}")
            print(f"   Has Elementor: {'YES' if elementor_status.get('has_elementor_data') else 'NO'}")
            print(f"   Has meta access: {'YES' if elementor_status.get('has_meta') else 'NO'}")
            print(f"   Meta fields: {elementor_status.get('meta_fields', [])}")
            
            if elementor_status.get('has_elementor_data') and '_elementor_data' not in elementor_status.get('meta_fields', []):
                print("\n   ⚠️ PROBLEM: Elementor data exists but not accessible via REST API!")
                print("   → Code Snippet needs to be activated")
    except Exception as e:
        print(f"❌ Error checking Elementor: {str(e)}")
    
    print("\n" + "-"*60)
    
    # 3. Analyze Post
    print("3. Analyzing Post Details...")
    try:
        post_analysis = check_post_revisions(api_url, username, password, int(post_id))
        
        if post_analysis.get('error'):
            print(f"❌ Error: {post_analysis['error']}")
        else:
            print(f"✅ Post Status: {post_analysis.get('post_status', 'Unknown')}")
            print(f"   Modified: {post_analysis.get('post_modified', 'Unknown')}")
            print(f"   Has Elementor: {'YES' if post_analysis.get('has_elementor') else 'NO'}")
            
            if post_analysis.get('has_elementor'):
                print(f"   Elementor data size: {post_analysis.get('elementor_data_length', 0)} chars")
                print(f"   Valid JSON: {'YES' if post_analysis.get('elementor_valid_json') else 'NO'}")
            
            print("\n   Diagnosis:")
            for diag in post_analysis.get('diagnosis', []):
                print(f"   {diag}")
            
            if post_analysis.get('recommendations'):
                print("\n   Recommendations:")
                for i, rec in enumerate(post_analysis.get('recommendations', []), 1):
                    print(f"   {rec}")
    except Exception as e:
        print(f"❌ Error analyzing post: {str(e)}")
    
    print("\n" + "-"*60)
    print("SUMMARY")
    print("-"*60 + "\n")
    
    if verify_result.get('success') and elementor_status.get('has_elementor_data'):
        if '_elementor_data' in elementor_status.get('meta_fields', []):
            print("✅ Everything looks configured correctly!")
            print("   Updates should modify Elementor content directly.")
        else:
            print("⚠️ Code Snippet is active but Elementor fields not exposed")
            print("   Try clearing all caches and check again")
    elif not verify_result.get('success'):
        print("❌ Code Snippet is not active - this is the main issue!")
        print("   Without it, updates go to WordPress content field only")
        print("   Elementor ignores the WordPress content field")
    elif not elementor_status.get('has_elementor_data'):
        print("✅ This post doesn't use Elementor")
        print("   Updates should work normally")
    
    print("\n" + "="*60)

if __name__ == "__main__":
    main()