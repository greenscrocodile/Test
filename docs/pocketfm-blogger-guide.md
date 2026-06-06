# Pocket FM Story Information Blogger Template Guide

This guide documents the production Blogger XML template in `pocketfm-blogger-template.xml`.

## Purpose and Compliance

The template creates an unofficial Pocket FM story information website. It does **not** host, embed, proxy, or download audio files. Each story page displays metadata and a single redirect button to the official Pocket FM story page.

## Installation Guide

1. In Blogger, open **Theme**.
2. Click **Customize** next to the current theme, then choose **Edit HTML**.
3. Back up the existing template.
4. Paste the full contents of `pocketfm-blogger-template.xml`.
5. Save the theme.
6. In **Settings**, set **Site feed** to **Full** (or at least make sure post contents are included) so the homepage JavaScript can read story metadata from Blogger posts.
7. Create static Blogger pages for `/p/about.html` and `/p/contact.html`, or update the navbar links in the XML.

## Required Blogger Post Metadata Structure

Each story is one Blogger post. Put the metadata block at the top of the post in **HTML view**. Edit values only; keep JSON keys unchanged when possible.

### Recommended Blogger-safe format

Blogger can strip or rewrite `<script>` tags inside posts on some accounts/editors. For that reason, the safest format is a hidden `<pre>` block:

```html
<pre class="story-json" style="display:none">
{
  "storyName": "The Royal Contract",
  "posterUrl": "https://example.com/poster.jpg",
  "pocketFmUrl": "https://www.pocketfm.com/show/example-story",
  "genre": "Romance",
  "subGenre": "Royal Romance",
  "language": "English",
  "voiceArtist": "Rahul Sharma",
  "status": "Ongoing",
  "episodes": "128",
  "author": "A. Writer",
  "description": "A short SEO-friendly description of the story.",
  "releaseYear": "2026",
  "totalListeningHours": "2M+",
  "rating": "4.7",
  "tags": ["romance", "drama", "royal"]
}
</pre>
```

### Marker format for raw Blogger content

The story page and homepage parser both support metadata stored between `STORY_DATA_START` and `STORY_DATA_END`. This is useful when you want to paste readable metadata directly into a Blogger post without relying on hidden HTML wrappers:

```text
STORY_DATA_START
{
  "storyName": "The Royal Contract",
  "posterUrl": "https://example.com/poster.jpg",
  "pocketFmUrl": "https://www.pocketfm.com/show/example-story",
  "genre": "Romance",
  "subGenre": "Royal Romance",
  "language": "English",
  "voiceArtist": "Rahul Sharma",
  "status": "Ongoing",
  "episodes": "128",
  "author": "A. Writer",
  "description": "A short SEO-friendly description of the story."
}
STORY_DATA_END
```

### Raw JSON fallback

If you already pasted only the JSON into the Blogger post body, the updated template can also read that. The parser searches the post body text for the first `{ ... }` JSON object, so this also works:

```json
{
  "storyName": "The Royal Contract",
  "posterUrl": "https://example.com/poster.jpg",
  "pocketFmUrl": "https://www.pocketfm.com/show/example-story",
  "genre": "Romance",
  "subGenre": "Royal Romance",
  "language": "English",
  "voiceArtist": "Rahul Sharma",
  "status": "Ongoing",
  "episodes": "128",
  "author": "A. Writer",
  "description": "A short SEO-friendly description of the story."
}
```

You may add normal article text after the JSON block. The template uses the JSON block for cards, filters, search, related stories, and detail-page fields. If the detail template stays empty, check the browser console for an `Invalid story metadata JSON` warning and verify that the post uses straight double quotes (`"`) instead of curly quotes.

## Admin Guide

### Adding a New Story

1. Create a new Blogger post.
2. Switch to HTML view.
3. Paste the recommended hidden `<pre class="story-json">` metadata block, or paste the raw JSON block if you prefer the fallback format.
4. Fill in the story values.
5. Add any extra editorial text below the metadata if desired.
6. Add labels such as `Genre`, `Romance`, `Voice Artist`, `Completed`, or `Ongoing` to support Blogger label URLs.
7. Publish.

The story automatically appears in the homepage feed, search results, filters, related stories, and status/genre/voice-artist discovery views.

### Global Pocket FM Button Control

The template has one global setting in the JavaScript configuration:

```js
const POCKETFM_CONFIG = {
  SHOW_POCKETFM_BUTTON: true
};
```

Set `SHOW_POCKETFM_BUTTON` to `false` to hide the "Listen on Pocket FM" button across all story pages without editing posts.

## Customization Guide

### Brand Colors

Edit the CSS variables at the top of the `<b:skin>` block:

```css
:root {
  --brand: #ef3f5a;
  --brand-2: #7c3aed;
}
```

### Logo Text and Mark

The navbar uses the Blogger blog title automatically. Change the music-note logo mark inside the `.logo-mark` span if you want a different symbol.

### Feed Batch and Pagination Size

For larger sites, adjust the JavaScript configuration:

```js
FEED_BATCH_SIZE: 150,
INITIAL_VISIBLE_COUNT: 24,
VISIBLE_INCREMENT: 24
```

The homepage loads stories in batches and renders only the currently visible subset, which keeps the page usable with 1000+ stories.

## SEO Setup Guide

The template includes:

- Responsive viewport metadata.
- Dynamic title and meta description fallbacks.
- Canonical URL output through Blogger data tags.
- Open Graph and Twitter Card tags.
- JSON-LD `BreadcrumbList` schema on story pages.
- JSON-LD `CreativeWork` schema on story pages.
- Semantic HTML sections, article markup, and accessible navigation.

For best SEO results:

1. Write a unique `description` value in every story metadata block.
2. Use descriptive poster alt-equivalent titles by keeping `storyName` accurate.
3. Add Blogger labels for genre, status, language, and voice artist.
4. Submit the Blogger sitemap in Google Search Console.
5. Avoid duplicate posts with the same story name.

## Genre, Voice Artist, and Status Pages

Blogger cannot create true dynamic archive pages without posts, labels, or JavaScript. This template supports automatic discovery in two ways:

1. The homepage filters instantly by genre, sub-genre, voice artist, status, and language.
2. Blogger label pages work automatically when posts are labeled consistently, for example:
   - `/search/label/Romance`
   - `/search/label/Rahul%20Sharma`
   - `/search/label/Completed`

For clean navigation pages, create Blogger pages named `Genres` or `Voice Artists` that link to label URLs, or keep users on the homepage filter system.

## Image Optimization

- Story card images use `loading="lazy"`, fixed width/height attributes, and square aspect-ratio containers to prevent layout shift.
- The detail-page poster loads eagerly because it is above the fold.
- Use compressed WebP or optimized JPEG poster images where possible.
- Recommended poster size: 720 × 720 or larger square image.

## Future Expansion Notes

Potential future additions can be added without changing the data model drastically:

- Dark-mode toggle stored in `localStorage`.
- Featured stories carousel controlled by a `featured` metadata field.
- Top-rated sort using the existing `rating` field.
- Language landing pages using Blogger labels.
- Custom author pages using Blogger labels.
- A lightweight client-side cache using `sessionStorage` for the feed response.
