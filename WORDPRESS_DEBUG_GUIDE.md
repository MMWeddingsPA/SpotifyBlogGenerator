# WordPress Update Debugging Guide

This guide helps diagnose and fix issues where WordPress updates aren't showing on the frontend.

## Quick Start

Run the diagnostic tool:
```bash
python test_wordpress_updates.py
```

Or run with environment variables:
```bash
export WORDPRESS_URL="https://your-site.com"
export WORDPRESS_USERNAME="your-username"
export WORDPRESS_PASSWORD="your-app-password"
export TEST_POST_ID="123"  # Optional

python test_wordpress_updates.py --quick
```

## Common Issues and Solutions

### 1. Updates Creating Revisions Instead of Updating Live Post

**Problem**: WordPress saves changes as a revision instead of updating the live post.

**Solution**: Always include `'status': 'publish'` in your update payload:
```python
wp_api.update_post(
    post_id=123,
    title="Updated Title",
    content="Updated content",
    status='publish'  # Critical!
)
```

### 2. Elementor Posts Not Showing Updates

**Problem**: Elementor renders from `_elementor_data` meta field, not the post content field.

**Solution**: 
1. Add this code to your WordPress site (in `wp-content/mu-plugins/expose-elementor-meta.php`):
```php
<?php
add_action( 'init', function () {
  register_post_meta( 'post', '_elementor_data', [
    'show_in_rest'  => true,
    'single'        => true,
    'type'          => 'string',
    'auth_callback' => function () { return current_user_can( 'edit_posts' ); },
  ] );
  register_post_meta( 'post', '_elementor_edit_mode', [
    'show_in_rest' => true,
    'single'       => true,
    'type'         => 'string',
  ] );
} );
```

2. Use the `preserve_elementor=True` parameter when updating:
```python
wp_api.update_post(
    post_id=123,
    title="Updated Title",
    content="Updated content",
    status='publish',
    preserve_elementor=True
)
```

### 3. Caching Issues

**Problem**: Updates are saved but not visible due to caching.

**Solutions**:
- Clear WordPress cache plugins (WP Super Cache, W3 Total Cache, etc.)
- Clear server cache (Varnish, Nginx, Cloudflare)
- Clear Elementor cache
- Test in incognito/private browsing mode

### 4. Authentication Issues

**Problem**: 401 Unauthorized errors.

**Solutions**:
- Use WordPress Application Passwords (recommended)
- Format: `xxxx xxxx xxxx xxxx xxxx xxxx` (with spaces)
- Ensure user has `edit_posts` capability
- Test with admin account first

## Using the Debug Tools

### 1. WordPressDebugger Class

```python
from utils.wordpress_debug import WordPressDebugger
from utils.fixed_wordpress_api import WordPressAPI

# Initialize API
wp_api = WordPressAPI('https://site.com', 'username', 'password')

# Create debugger
debugger = WordPressDebugger(wp_api)

# Run comprehensive test
results = debugger.run_comprehensive_test(post_id=123)  # or None to create test post
```

### 2. Simple Test Update Function

```python
from utils.wordpress_debug import create_simple_test_update_function

# Create test function
test_update = create_simple_test_update_function(wp_api)

# Run test - creates a red-bordered box with timestamp
result = test_update(post_id=123)
```

### 3. Manual Testing

To manually test if updates are working:

1. Create a test post with unique content:
```python
result = wp_api.create_post(
    title="Test Post - " + datetime.now().isoformat(),
    content="<p>Original content created at: " + datetime.now().isoformat() + "</p>",
    status='draft'
)
post_id = result['post_id']
```

2. Update the post with new content:
```python
result = wp_api.update_post(
    post_id=post_id,
    title="Updated Test Post - " + datetime.now().isoformat(),
    content="<p>UPDATED content at: " + datetime.now().isoformat() + "</p>",
    status='publish'
)
```

3. Verify the update:
```python
post = wp_api.get_post(post_id)
print(f"Status: {post['status']}")
print(f"Modified: {post['modified']}")
print(f"Content: {post['content'][:200]}")
```

## Debug Checklist

Run `print_checklist()` to see the full troubleshooting checklist, or check these items:

- [ ] WordPress credentials are correct
- [ ] User has edit_posts capability
- [ ] Including 'status': 'publish' in updates
- [ ] REST API is enabled (test: GET /wp-json/)
- [ ] Pretty permalinks are enabled (not 'Plain')
- [ ] No security plugins blocking REST API
- [ ] All caches cleared after update
- [ ] Testing in incognito mode
- [ ] For Elementor: meta fields exposed to REST API
- [ ] For Elementor: updating _elementor_data field

## Understanding the Test Results

The diagnostic tool runs these tests:

1. **Basic Connection**: Tests if API credentials work
2. **Create Test Post**: Creates a draft post for testing
3. **Update Test**: Attempts to update the post
4. **Verify Update**: Checks if the update was applied
5. **Check Revisions**: Looks for revision creation
6. **Meta Fields Access**: Tests if meta fields are accessible
7. **Elementor Detection**: Checks if Elementor is active

### Reading the Report

```
✓ PASS | Basic Connection: WordPress API connection successful
✓ PASS | Create Test Post: Post ID: 123
✗ FAIL | Update Post: Status: 403
✗ FAIL | Verify Update: Update marker NOT FOUND in content
```

## Elementor-Specific Process

For sites using Elementor, follow this process:

1. **Server Setup** (one-time):
   - Add the PHP code above to expose Elementor meta fields
   - Or create a custom endpoint (see elementorfix.md)

2. **Update Process**:
   ```python
   # Fetch post with meta
   post = wp_api.get_post(post_id, context='edit')
   
   # Update with Elementor preservation
   result = wp_api.update_post(
       post_id=post_id,
       title="New Title",
       content="New content for SEO",
       status='publish',
       preserve_elementor=True  # Preserves Elementor data
   )
   ```

3. **Clear Caches**:
   - WordPress cache
   - Elementor CSS cache
   - CDN/server cache

## Getting Help

If issues persist after following this guide:

1. Run the diagnostic tool and save the report
2. Check WordPress error logs
3. Enable WP_DEBUG in wp-config.php
4. Test with a simple non-Elementor post
5. Verify with WordPress admin that changes are saved

## Important Notes

- Always test on staging/development first
- Back up your database before bulk updates
- Monitor server resources during updates
- Consider rate limiting for bulk operations
- Some hosting providers have additional security that may block REST API