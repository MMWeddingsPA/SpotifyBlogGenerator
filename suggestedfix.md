# Elementor REST Update — **Draft‑First** Workflow (Option A)

> **Goal:** The Spotify Blog Generator should regenerate an Elementor‑edited post **and save it as a Draft** so the editorial team can review inside WordPress/Elementor before manually publishing.

---

## 1 Why use Draft‑First?

1. **Zero‑risk editing** – The live URL is never updated until a human clicks **Publish**.
2. **Native WP controls** – Editors can open the draft in *Edit with Elementor*, check layout, SEO, etc.
3. **No duplicate posts needed** – We simply flip the post’s own `status` from `publish` → `draft`, then back to `publish` after approval.

*Caveat*: During review, the public URL 404s. If that window must stay live, choose Pattern B (duplicate) instead.

---

## 2 Server‑side prerequisite (same as main brief)

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

*Exposes Elementor layout JSON to REST so the app can update it.*

---

## 3 App‑side flow (Option A)

```text
1. GET  /wp-json/wp/v2/posts/{id}?context=edit
     → read meta._elementor_data (JSON string)
2. Modify that JSON → inject new text into widgets
3. PUT /wp-json/wp/v2/posts/{id}
   {
     "status": "draft",                 // *** key change: save as draft ***
     "content": "Plain‑text fallback (SEO)",
     "meta": {
       "_elementor_data"     : "<escaped JSON>",
       "_elementor_edit_mode": "builder"
     }
   }
4. Return success (HTTP 200). The post is now **Draft**.
```

> **Important**: setting `"status":"draft"` *unpublishes* the post. Reviewers will see it in **Posts → Drafts**.

---

## 4 Reviewer workflow

1. **WP Admin → Posts → Drafts** – locate the updated post.
2. Click **Edit with Elementor** → verify text, images, layout.
3. *(Optional)* tweak SEO, permalinks, etc.
4. Click **Publish**. ‑ Done.

### CSS flush (only if styling changed)

```shell
wp elementor flush-css --post_id=<ID>
```

---

## 5 Implementation checklist for dev agent

| Step | Action                                                                                |
| ---- | ------------------------------------------------------------------------------------- |
| 1    | Ensure the `register_post_meta` snippet is deployed (or custom route if preferred).   |
| 2    | **Client update** – change update call:<br>`status : 'draft'` instead of `'publish'`. |
| 3    | Parse & update `_elementor_data` JSON as per main brief.                              |
| 4    | (Optional) add a UI toggle: **Draft** vs **Publish immediately**.                     |
| 5    | Document for editors: “Find drafts here → Edit → Publish.”                            |

---

## 6 QA checklist (staging)

| ✔︎ | Test                   | Expected                       |
| -- | ---------------------- | ------------------------------ |
| 1  | Run generator          | REST 200 OK                    |
| 2  | Front‑end (logged‑out) | URL 404s (post is draft)       |
| 3  | Admin → Drafts         | Post appears with updated date |
| 4  | Open in Elementor      | Content updated                |
| 5  | Click Publish          | Page live, new content visible |

---

### TL;DR

*Send the Elementor‑updated JSON with* `status:"draft"` *to create a review‑ready draft. Editors open it in Elementor, verify, then press **Publish**. No live site change until approved.*
