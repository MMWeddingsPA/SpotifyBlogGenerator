#!/usr/bin/env python3
"""
Debug tool to understand where WordPress updates are going
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.fixed_wordpress_api import WordPressAPI
import json

def debug_post_update(api_url, username, password, post_id):
    """
    Debug where updates are being saved in WordPress
    """
    print("\n" + "="*60)
    print("WORDPRESS UPDATE LOCATION DEBUGGER")
    print("="*60 + "\n")
    
    try:
        wp = WordPressAPI(api_url, username, password)
        
        # Get the post with both contexts
        print(f"1. Fetching post {post_id} details...\n")
        
        # Get with view context
        post_view = wp.get_post(post_id, context='view')
        if post_view:
            print("✓ Post found (view context)")
            print(f"  Title: {post_view.get('title', 'No title')}")
            print(f"  Status: {post_view.get('status')}")
            print(f"  Modified: {post_view.get('modified')}")
            print(f"  Content length: {len(post_view.get('content', ''))}")
            
        # Get with edit context  
        post_edit = wp.get_post(post_id, context='edit')
        if post_edit:
            print("\n✓ Post found (edit context)")
            meta = post_edit.get('meta', {})
            print(f"  Has meta fields: {'Yes' if meta else 'No'}")
            
            if meta:
                print(f"  Meta fields available: {len(meta)}")
                if '_elementor_data' in meta:
                    print("  ✓ Has Elementor data")
                    elementor_data = meta['_elementor_data']
                    if elementor_data:
                        try:
                            # Parse to see structure
                            parsed = json.loads(elementor_data)
                            print(f"  Elementor sections: {len(parsed)}")
                            
                            # Find text widgets
                            text_widgets = []
                            def find_widgets(elements):
                                for el in elements:
                                    if el.get('widgetType'):
                                        text_widgets.append({
                                            'type': el.get('widgetType'),
                                            'id': el.get('id')
                                        })
                                    if 'elements' in el:
                                        find_widgets(el['elements'])
                            
                            find_widgets(parsed)
                            print(f"  Found {len(text_widgets)} widgets:")
                            for w in text_widgets[:5]:  # Show first 5
                                print(f"    - {w['type']} (id: {w['id']})")
                            if len(text_widgets) > 5:
                                print(f"    ... and {len(text_widgets) - 5} more")
                        except:
                            print("  ⚠️ Could not parse Elementor data")
                else:
                    print("  ✗ No Elementor data found")
        
        print("\n" + "-"*60)
        print("2. WHERE YOUR UPDATES ARE GOING:\n")
        
        print("Currently, your updates go to the WordPress 'content' field:")
        print("  • This is the standard WordPress post content")
        print("  • Visible in: WordPress Admin → Edit Post → Text tab")
        print("  • NOT visible on frontend if Elementor is active\n")
        
        print("Why you don't see updates on the frontend:")
        print("  • Elementor renders from '_elementor_data' meta field")
        print("  • It ignores the WordPress content field")
        print("  • Your updates ARE saved, but in the wrong place\n")
        
        print("To verify your updates are working:")
        print("  1. Go to WordPress Admin → Posts → All Posts")
        print("  2. Find your post and click 'Edit' (NOT 'Edit with Elementor')")
        print("  3. You should see your updated content in the editor")
        print("  4. But the frontend still shows old Elementor content\n")
        
        if post_edit and '_elementor_data' in post_edit.get('meta', {}):
            print("This post DOES use Elementor. Updates need to go to:")
            print("  • _elementor_data meta field (requires PHP setup)")
            print("  • Specific widget settings within the Elementor structure")
        else:
            print("This post does NOT appear to use Elementor.")
            print("Updates to the content field should be visible.")
        
        print("\n" + "-"*60)
        print("3. WHAT ELEMENTOR WIDGETS CAN BE UPDATED:\n")
        
        print("Text-based widgets that can receive updates:")
        print("  • text-editor - Rich text content")
        print("  • heading - Titles and headings")  
        print("  • text - Basic text")
        print("  • theme-post-content - Dynamic post content\n")
        
        print("The updates will go to the FIRST main content widget found.")
        print("Usually this is a 'text-editor' or 'theme-post-content' widget.\n")
        
        print("4. NEXT STEPS:\n")
        
        print("Option A: See your updates now (without Elementor)")
        print("  1. Edit post in WordPress Classic Editor")
        print("  2. Your updates are there in the content field")
        print("  3. Temporarily disable Elementor for this post\n")
        
        print("Option B: Make updates work with Elementor")
        print("  1. Add the PHP file to /wp-content/mu-plugins/")
        print("  2. This exposes Elementor data to REST API")
        print("  3. Updates will then modify Elementor widgets directly\n")
        
        print("Option C: Create new posts without Elementor")
        print("  1. Create new posts in WordPress (not Elementor)")
        print("  2. Updates will work immediately")
        print("  3. No special setup needed")
        
    except Exception as e:
        print(f"\n✗ Error: {str(e)}")

if __name__ == "__main__":
    print("WordPress Update Location Debugger")
    print("-" * 30)
    
    api_url = input("WordPress URL: ").strip()
    username = input("Username: ").strip()
    password = input("Password: ").strip()
    post_id = input("Post ID to debug: ").strip()
    
    debug_post_update(api_url, username, password, int(post_id))