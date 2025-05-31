<?php
/**
 * Expose Elementor Meta Fields to WordPress REST API
 * 
 * This file should be placed in: /wp-content/mu-plugins/expose-elementor-meta.php
 * 
 * It exposes the Elementor data structure to the REST API so that external
 * applications can read and update Elementor content.
 * 
 * @package SpotifyBlogGenerator
 * @version 1.0
 */

// Exit if accessed directly
if (!defined('ABSPATH')) {
    exit;
}

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
    
    // Optional: Register additional Elementor meta fields if needed
    register_post_meta('post', '_elementor_template_type', [
        'show_in_rest' => true,
        'single'       => true,
        'type'         => 'string',
        'auth_callback' => function () { 
            return current_user_can('edit_posts'); 
        },
    ]);
    
    // Log that the plugin is active (for debugging)
    if (defined('WP_DEBUG') && WP_DEBUG) {
        error_log('SpotifyBlogGenerator: Elementor meta fields exposed to REST API');
    }
});

// Optional: Add a REST API endpoint to verify the setup
add_action('rest_api_init', function () {
    register_rest_route('spotify-blog/v1', '/verify-elementor-meta', [
        'methods'  => 'GET',
        'callback' => function () {
            return [
                'success' => true,
                'message' => 'Elementor meta fields are exposed',
                'fields'  => [
                    '_elementor_data' => 'exposed',
                    '_elementor_edit_mode' => 'exposed',
                    '_elementor_template_type' => 'exposed'
                ]
            ];
        },
        'permission_callback' => '__return_true'
    ]);
});