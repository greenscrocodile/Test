# Admin Guide

## Add a New Story

1. Open Blogger and create a **New Post**.
2. Switch to **HTML view**.
3. Paste the JSON block from `metadata-example.html`. The preferred block uses `<pre class="story-json" style="display:none">` because Blogger sometimes strips post-level `<script>` tags on the published page.
4. Fill every required field:
   - `storyName`
   - `posterUrl`
   - `pocketFmUrl`
   - `genre`
   - `subGenre`
   - `language`
   - `voiceArtist`
   - `status`
   - `episodes`
   - `author`
   - `description`
5. Set the Blogger post title to the story name.
6. Add optional Blogger labels such as `Fantasy`, `Rahul Sharma`, `Ongoing`, and `Hindi` if you want Blogger label archive pages.
7. Publish.

The homepage, detail page, search, filters, and related stories update automatically from the Blogger feed.

## Global Pocket FM Button Control

In `pocketfm-story-template.xml`, find:

```js
SHOW_POCKETFM_BUTTON: true
```

- `true` displays the button on every story with a `pocketFmUrl`.
- `false` hides it everywhere.

## Theme Toggle

The navbar contains a light/dark toggle. The visitor's selection is saved in `localStorage` under `pfm-theme`. If no selection exists, the site follows the visitor's operating-system color preference.

## Metadata Rules

- Keep field names exactly as shown in `metadata-example.html`. The template also supports the older `<script type="application/json" class="story-json">` format, but use the `<pre>` format if published pages do not show data.
- Use consistent capitalization for filter values, for example always use `Ongoing`, not both `ongoing` and `Ongoing`.
- Use square poster images when possible.
- Use official Pocket FM URLs only.

## SEO Setup

- Set a useful Blogger site title and description.
- Give each post a clear story title.
- Put a unique `description` in each JSON block.
- Use high-quality poster URLs.
- Keep the site disclaimer visible: audio is not hosted on the website.

## Future Expansion Ideas

- Add label-based landing pages for curated genres.
- Add a favorites system using browser storage.
- Add sorting by rating, episodes, or release year.
- Add structured FAQ blocks to post content.
- Add ads or affiliate disclosure widgets if needed.
