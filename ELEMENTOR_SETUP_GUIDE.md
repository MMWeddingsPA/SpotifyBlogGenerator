# Elementor WordPress Setup Guide

This guide helps you set up your WordPress site to work with the Spotify Blog Generator's Elementor update feature.

## 🚀 Quick Setup (5 minutes)

### Step 1: Enable Elementor Meta Fields in WordPress

1. **Access your WordPress server** via FTP, cPanel File Manager, or SSH

2. **Navigate to**: `/wp-content/mu-plugins/`
   - If the `mu-plugins` folder doesn't exist, create it

3. **Upload the PHP file**: Copy `wordpress-setup/expose-elementor-meta.php` from this project to the `mu-plugins` folder

   Or create the file manually with this content:
   ```php
   <?php
   add_action('init', function () {
       register_post_meta('post', '_elementor_data', [
           'show_in_rest' => true,
           'single' => true,
           'type' => 'string',
           'auth_callback' => function() { 
               return current_user_can('edit_posts'); 
           },
       ]);
       register_post_meta('post', '_elementor_edit_mode', [
           'show_in_rest' => true,
           'single' => true,
           'type' => 'string',
       ]);
   });
   ```

4. **Verify installation**: Visit `https://your-site.com/wp-json/spotify-blog/v1/verify-elementor-meta`
   - You should see: `{"success":true,"message":"Elementor meta fields are exposed"}`

### Step 2: Clear WordPress Cache

1. If using a caching plugin (W3 Total Cache, WP Super Cache, etc.), clear all caches
2. If using Elementor Pro, go to Elementor → Tools → Regenerate CSS

## 📝 How the Update Process Works

### For Content Editors:

1. **Run the Blog Generator** to update a post
2. The app will:
   - Fetch the current Elementor layout
   - Update the text content within Elementor widgets
   - Save the post as a **Draft**
3. **In WordPress Admin**:
   - Go to Posts → Drafts
   - Find your updated post
   - Click "Edit with Elementor"
   - Review the changes
   - Click "Publish" when satisfied

### What Gets Updated:

- ✅ Text content in Elementor text widgets
- ✅ Heading widgets
- ✅ Text editor widgets
- ✅ Post content widgets
- ❌ Images, videos, or other media (preserved as-is)
- ❌ Styling and layout (preserved as-is)

## 🔧 Troubleshooting

### "Updates not showing in Elementor"

1. **Check if meta fields are exposed**:
   - Run the diagnostic tool: `python check_wordpress_setup.py`
   - Look for "Elementor meta fields are exposed" ✓

2. **Clear all caches**:
   ```bash
   # If you have WP-CLI:
   wp cache flush
   wp elementor flush-css
   ```

3. **Check WordPress permissions**:
   - Ensure your API user has `edit_posts` capability
   - Application passwords need full access

### "Post stays published instead of draft"

- Check the console logs for any errors
- Ensure the status is being set to 'draft' in the update request
- Some caching plugins might interfere - try disabling them temporarily

### "Can't find updated posts"

1. Check WordPress Admin → Posts → **Drafts** tab (not All Posts)
2. Sort by "Modified" date to see recent updates
3. Use the search box with the post title

## 🎯 Best Practices

1. **Test on staging first**: Always test on a staging site before production
2. **Backup regularly**: Keep backups of your WordPress database
3. **Monitor the logs**: Check console output for detailed update information
4. **Review before publishing**: Always review in Elementor before making changes live

## 🆘 Need Help?

1. Run diagnostics: `python check_wordpress_setup.py`
2. Check logs in the console when running updates
3. Verify the PHP file is in the correct location
4. Ensure WordPress REST API is accessible

## 📋 Checklist for Production

- [ ] PHP file uploaded to `/wp-content/mu-plugins/`
- [ ] Verified at `/wp-json/spotify-blog/v1/verify-elementor-meta`
- [ ] Tested update on a draft post
- [ ] Confirmed updates appear in Elementor editor
- [ ] Set up editorial workflow (who reviews drafts)
- [ ] Cleared all caches
- [ ] Documented the process for your team