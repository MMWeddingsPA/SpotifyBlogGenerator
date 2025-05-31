# Code Snippets Plugin Setup for Elementor Integration

This guide shows you how to add the required code using the WordPress Code Snippets plugin.

## Step-by-Step Instructions

### 1. Access Code Snippets Plugin
- In WordPress Admin, go to **Snippets → Add New**
- Or go to **Snippets → All Snippets** and click **Add New**

### 2. Create New PHP Snippet
- Click on **Add New** button
- You'll see options for different snippet types - select **PHP Snippet**

### 3. Configure the Snippet

**Title:** `Expose Elementor Meta Fields to REST API`

**Description:** 
```
Enables the Spotify Blog Generator to update Elementor content via REST API.
This exposes _elementor_data and _elementor_edit_mode meta fields.
```

**Code:** Copy and paste this exact code:

```php
// Exit if this is not a WordPress environment
if (!defined('ABSPATH')) {
    return;
}

// Register Elementor meta fields to be accessible via REST API
add_action('init', function () {
    // Register _elementor_data meta field
    register_post_meta('post', '_elementor_data', [
        'show_in_rest'  => true,
        'single'        => true,
        'type'          => 'string',
        'description'   => 'Elementor page builder data',
        'auth_callback' => function () { 
            return current_user_can('edit_posts'); 
        },
    ]);
    
    // Register _elementor_edit_mode meta field
    register_post_meta('post', '_elementor_edit_mode', [
        'show_in_rest' => true,
        'single'       => true,
        'type'         => 'string',
        'description'  => 'Elementor edit mode setting',
        'auth_callback' => function () { 
            return current_user_can('edit_posts'); 
        },
    ]);
    
    // Optional: Register additional Elementor meta fields
    register_post_meta('post', '_elementor_template_type', [
        'show_in_rest' => true,
        'single'       => true,
        'type'         => 'string',
        'auth_callback' => function () { 
            return current_user_can('edit_posts'); 
        },
    ]);
});

// Add a REST API endpoint to verify the setup
add_action('rest_api_init', function () {
    register_rest_route('spotify-blog/v1', '/verify-elementor-meta', [
        'methods'  => 'GET',
        'callback' => function () {
            $test_meta = get_registered_meta_keys('post');
            $elementor_fields = [];
            
            foreach (['_elementor_data', '_elementor_edit_mode', '_elementor_template_type'] as $field) {
                if (isset($test_meta[$field])) {
                    $elementor_fields[$field] = 'registered';
                }
            }
            
            return [
                'success' => !empty($elementor_fields),
                'message' => !empty($elementor_fields) 
                    ? 'Elementor meta fields are exposed' 
                    : 'No Elementor fields found',
                'fields'  => $elementor_fields,
                'wordpress_version' => get_bloginfo('version'),
                'rest_url' => get_rest_url()
            ];
        },
        'permission_callback' => '__return_true'
    ]);
});

// Log activation if in debug mode
if (defined('WP_DEBUG') && WP_DEBUG && defined('WP_DEBUG_LOG') && WP_DEBUG_LOG) {
    error_log('SpotifyBlogGenerator: Elementor meta fields exposed to REST API via Code Snippets');
}
```

### 4. Configure Snippet Settings

**Tags:** `elementor, rest-api, spotify-blog`

**Priority:** `10` (default is fine)

**Location:** Choose **Run snippet everywhere**

**Auto Insert:** Leave as default (Admin, Frontend, REST API)

### 5. Save and Activate

1. Click **Save Snippet** at the bottom
2. Make sure the toggle switch is **ON** (activated)
3. You should see a success message

### 6. Verify Installation

Visit this URL in your browser (replace with your domain):
```
https://your-site.com/wp-json/spotify-blog/v1/verify-elementor-meta
```

You should see:
```json
{
  "success": true,
  "message": "Elementor meta fields are exposed",
  "fields": {
    "_elementor_data": "registered",
    "_elementor_edit_mode": "registered",
    "_elementor_template_type": "registered"
  }
}
```

## Troubleshooting

### If the snippet causes an error:
- Code Snippets has built-in error protection
- It will automatically deactivate if there's an error
- Check the error message and ensure you copied the code correctly

### If the verification URL returns 404:
1. Go to **Settings → Permalinks**
2. Click **Save Changes** (without changing anything)
3. This flushes the rewrite rules
4. Try the verification URL again

### If meta fields aren't showing:
1. Clear all caches (browser, WordPress, CDN)
2. Ensure the snippet is activated
3. Check that you're logged in with proper permissions

## What This Code Does

1. **Exposes Elementor Meta Fields**: Makes `_elementor_data` accessible via REST API
2. **Adds Security**: Only users who can edit posts can update these fields
3. **Creates Verification Endpoint**: Provides a way to test if setup is working
4. **Maintains Compatibility**: Works with all WordPress and Elementor versions

## Next Steps

Once verified:
1. Try updating a post with the Blog Generator
2. Updates will now modify Elementor content directly
3. Changes will be visible on the frontend
4. Posts will save as drafts for review

## Benefits of Using Code Snippets

- ✅ No file access needed
- ✅ Survives theme updates
- ✅ Easy to enable/disable
- ✅ Built-in error protection
- ✅ Export/import capability
- ✅ Version control friendly

The Code Snippets plugin is perfect for this use case as it safely manages the code and won't break your site if there's an error.