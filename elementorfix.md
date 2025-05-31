# Updating Elementor Posts via REST API — Implementation Brief

> **Goal:** Let the Spotify Blog Generator fetch an existing Elementor‑edited post, regenerate its content, and push the update so it appears live while preserving the Elementor layout.

---

## 1. Why the current version fails

| Root cause                             | What the app does                                                                       | Result                                                                                               |
| -------------------------------------- | --------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------- |
| \*\*Elementor ignores \*\*\`\`         | Generator rewrites only the `content` field via REST `PUT`.                             | Front‑end still shows the old layout because Elementor renders the JSON stored in `_elementor_data`. |
| **Elementor meta not exposed to REST** | `_elementor_data` is not registered with `show_in_rest`; WP strips it from the payload. | Your update never reaches Elementor’s data.                                                          |
| \*\*Status not forced to \*\*\`\`      | `status` omitted in `PUT`.                                                              | WordPress saves a *revision* instead of the live post row.                                           |
| **Cached CSS**                         | Elementor serves previously compiled CSS.                                               | Even if meta changed, styling may reference the old content until cache flush.                       |

---

## 2. Required changes (preserve Elementor)

### 2.1 Register Elementor meta for REST (one‑time server patch)

```php
<?php
// /wp-content/mu-plugins/expose-elementor-meta.php
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

### 2.2 App‑side flow (pseudo‑code)

```text
1. GET  /wp-json/wp/v2/posts/{id}?context=edit
     → grab meta._elementor_data (JSON string)
2. Parse JSON, update desired widgets (e.g., Text‑Editor → settings.editor)
3. Serialize back to JSON string
4. PUT /wp-json/wp/v2/posts/{id}
   {
     "status": "publish",
     "content": "Plain‑text fallback for SEO",
     "meta": {
       "_elementor_data": "<escaped JSON string>",
       "_elementor_edit_mode": "builder"
     }
   }
```

**Notes**

* Always send `status: "publish"` to overwrite the live row.
* `_elementor_edit_mode` keeps the page editable in Elementor.
* REST expects the Elementor data as an **escaped JSON string**.
* Optionally update `content` with stripped‑tags text for search.

### 2.3 (Optional) Flush Elementor CSS

```shell
# WP‑CLI
wp elementor flush-css --post_id=123
```

—or—

```php
Elementor\Plugin::$instance->files_manager->clear_css( 123 );
```

### 2.4 Alternate approach (custom endpoint)

If you cannot register meta keys, add a bespoke route:

```php
register_rest_route( 'ai-sync/v1', '/elementor/(?P<id>\d+)', [
  'methods'  => 'POST',
  'callback' => function ( WP_REST_Request $r ) {
      $id   = $r['id'];
      $json = $r->get_param( 'data' );
      update_post_meta( $id, '_elementor_data', wp_slash( $json ) );
      return rest_ensure_response( [ 'ok' => true ] );
  },
  'permission_callback' => function () { return current_user_can( 'edit_posts' ); },
] );
```

---

## 3. Implementation checklist for dev agent

1. **Add server patch** (`register_post_meta` snippet or custom endpoint).
2. **Modify generator client logic**:

   ```js
   const post = await wp.posts().id(id).context('edit').get();
   const data = JSON.parse(post.meta._elementor_data);
   // mutate data …
   await wp.posts().id(id).update({
     status : 'publish',
     content: stripTags(newHtml),
     meta   : {
       _elementor_data     : JSON.stringify(data),
       _elementor_edit_mode: 'builder'
     }
   });
   ```
3. **(Optional) Trigger CSS flush** after successful update.

---

## 4. QA smoke test

| ✔︎ | Test                            | Expectation                              |
| -- | ------------------------------- | ---------------------------------------- |
| 1  | Run generator on a staging post | REST returns 200 OK                      |
| 2  | Load page front‑end             | New content visible                      |
| 3  | Open in Elementor editor        | Updated content present, no layout break |
| 4  | View source / CSS hash          | Changed if CSS flushed                   |

If all pass, roll out to production.

---

### TL;DR

Expose Elementor meta to REST, update `_elementor_data` + `status:publish`, (optionally) flush CSS. This lets your app push regenerated content live **without breaking Elementor layouts**.
