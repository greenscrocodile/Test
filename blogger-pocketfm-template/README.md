# Pocket FM Story Information Blogger Template

This package contains a production-oriented Blogger XML template for building a searchable Pocket FM story information website. It does **not** host audio files. Each Blogger post stores one story's metadata as JSON, and the template renders story cards, detail pages, related stories, filters, search, pagination/load-more, SEO tags, schema, and a light/dark theme toggle.

## Files

- `pocketfm-story-template.xml` — complete Blogger XML template with embedded HTML, CSS, and vanilla JavaScript.
- `docs/admin-guide.md` — how to create story posts and manage global settings.
- `docs/metadata-example.html` — copy/paste metadata block for Blogger posts.

## Key Features

- Fixed stylish navbar with mobile hamburger menu.
- Light/dark theme toggle in the navigator using `localStorage` and system preference fallback.
- Responsive story card grid with lazy-loaded square posters.
- Instant search by story name, voice artist, and genre.
- Instant filters for genre, sub genre, voice artist, status, and language.
- Universal story detail page generated from post JSON.
- Global Pocket FM button switch: `SHOW_POCKETFM_BUTTON`.
- Related stories by same voice artist from Blogger feed data.
- Blogger JSON feed loading in batches for large catalogs.
- SEO title, description, Open Graph, Twitter Card, CreativeWork schema, and Breadcrumb schema.

## Installation

1. In Blogger, open **Theme**.
2. Back up the current theme.
3. Choose **Edit HTML**.
4. Replace the existing template with the contents of `pocketfm-story-template.xml`.
5. Save.
6. Create story posts using the metadata block from `docs/metadata-example.html`.
7. Publish posts. They automatically appear on the homepage and in filters/search after Blogger's feed updates.

## Customization

Edit the global settings near the top of the XML template:

```js
window.PFM_SETTINGS = {
  SHOW_POCKETFM_BUTTON: true,
  SITE_NAME: '<data:blog.title/>',
  FEED_BATCH_SIZE: 150,
  INITIAL_CARD_LIMIT: 24,
  LOAD_MORE_SIZE: 24,
  DEFAULT_POSTER: 'https://...',
  OFFICIAL_BUTTON_TEXT: 'Listen on Pocket FM'
};
```

Use `SHOW_POCKETFM_BUTTON: false` to hide the Pocket FM button on every story page without editing individual posts.

Design colors are controlled with CSS variables in `:root` and `[data-theme="dark"]` inside the `<b:skin>` block.

## Scalability Notes

Blogger feeds are requested in batches. The homepage initially renders a limited number of cards and uses **Load More** for additional stories. Search and filters run client-side over loaded feed records; if a user loads more, additional batches are cached in the browser session.

For catalogs above 1,000 posts, keep story JSON compact, use optimized poster URLs, and maintain consistent metadata values so filters remain clean.
