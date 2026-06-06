# Pocket FM Story Information Blogger Template Guide

This repository includes a production-ready Blogger XML template for a Pocket FM story information website. The site does **not** host or embed audio. It stores story data in Blogger posts, displays searchable story cards, and redirects visitors to the official Pocket FM story page.

## Files

- `pocketfm-blogger-template.xml` — the complete Blogger XML template containing the layout, CSS, JavaScript, SEO tags, schema output, story detail template, filters, search, pagination/load-more, and global Pocket FM button setting.
- `POCKETFM_BLOGGER_GUIDE.md` — installation, customization, admin, SEO, and expansion notes.

## Installation Guide

1. In Blogger, go to **Theme**.
2. Back up your current theme with **Backup**.
3. Choose **Edit HTML**.
4. Replace the existing theme code with the contents of `pocketfm-blogger-template.xml`.
5. Save the theme.
6. Go to **Settings → Site feed** and set **Allow blog feed** to **Full**. The template reads post metadata from the Blogger JSON feed.
7. Create optional static pages at `/p/about.html` and `/p/contact.html` if you want the navbar links to resolve.

## Metadata Structure

Each story is one Blogger post. Add the story metadata in the post body in HTML or Compose mode using this marker format:

```text
STORY_DATA_START
{
  "storyName": "The Royal Contract",
  "posterUrl": "https://example.com/poster.jpg",
  "pocketFmUrl": "https://www.pocketfm.com/show/example-story",
  "genre": "Romance",
  "subGenre": "Royal Romance",
  "language": "Hindi",
  "voiceArtist": "Rahul Sharma",
  "status": "Ongoing",
  "episodes": "120",
  "author": "Pocket FM",
  "description": "A short SEO-friendly description of the story.",
  "releaseYear": "2026",
  "totalListeningHours": "2M+",
  "rating": "4.7",
  "tags": ["romance", "contract", "royal"]
}
STORY_DATA_END
```

Required fields are `storyName`, `posterUrl`, `pocketFmUrl`, `genre`, `subGenre`, `language`, `voiceArtist`, `status`, `episodes`, `author`, and `description`. Optional fields are `releaseYear`, `totalListeningHours`, `rating`, and `tags`.

## Admin Guide

To add a story:

1. Create a new Blogger post.
2. Use the story name as the post title.
3. Paste and edit the metadata block.
4. Add labels matching important filter values, such as `Romance`, `Rahul Sharma`, `Ongoing`, and `Hindi`. Labels are optional for JavaScript filtering, but recommended for Blogger label archive URLs and SEO discovery.
5. Publish the post.

After publishing, the homepage, search results, filters, directory chips, detail page, and related stories update automatically from the feed.

## Customization Guide

### Global Pocket FM button

In `pocketfm-blogger-template.xml`, edit the `POCKETFM_CONFIG` object:

```js
const POCKETFM_CONFIG = {
  SHOW_POCKETFM_BUTTON: true
};
```

Set `SHOW_POCKETFM_BUTTON` to `false` to hide the "Listen on Pocket FM" button across every story page without editing individual posts.

### Branding

Edit CSS variables near the top of the template:

- `--brand` for the main accent color.
- `--brand-2` for the secondary gradient color.
- `--brand-dark` for button depth.
- `--container` for max page width.
- `--radius` for rounded corners.

### Pagination and scaling

The template uses batched Blogger feed loading:

- `FEED_BATCH_SIZE` controls how many posts are requested at a time.
- `INITIAL_VISIBLE_COUNT` controls initial cards displayed.
- `VISIBLE_INCREMENT` controls each Load More step.

The default values are designed for fast initial rendering while supporting 1000+ posts.

## Search and Filter Guide

The homepage supports instant filtering by:

- Genre
- Sub Genre
- Voice Artist
- Status
- Language

The search bar matches story name, voice artist, and genre.

URL filters are also supported, for example:

- `/?genre=Romance`
- `/?voiceArtist=Rahul%20Sharma`
- `/?status=Completed`
- `/?directory=genres`
- `/?directory=voice-artists`

Blogger label URLs like `/search/label/Romance` also hydrate the matching filter when the label value exists in story metadata.

## SEO Setup Guide

The template includes:

- Responsive viewport and mobile-friendly layout.
- Canonical URL support.
- Dynamic Blogger title and meta description logic.
- Open Graph tags.
- Twitter card tags.
- JSON-LD `BreadcrumbList` schema.
- JSON-LD `CreativeWork` story schema.
- Lazy-loaded responsive story card images.
- Fixed image dimensions to reduce layout shift.

For best SEO results:

1. Keep each post title equal to the story name.
2. Write a unique `description` field for every story.
3. Use real poster image URLs with stable dimensions.
4. Add Blogger labels for genre, voice artist, status, and language.
5. Submit the Blogger sitemap in Google Search Console.

## Genre, Voice Artist, and Status Pages

Because Blogger XML templates cannot create new physical pages from JavaScript metadata alone, this template provides automatic dynamic directory/filter views instead:

- Genre directory: `/?directory=genres`
- Voice artist directory: `/?directory=voice-artists`
- Completed stories: `/?status=Completed`
- Ongoing stories: `/?status=Ongoing`
- Incomplete stories: `/?status=Incomplete`

If you want classic Blogger archive URLs, add matching labels to posts. For example, posts labeled `Romance` can appear at `/search/label/Romance`.

## Future Expansion Notes

Possible future additions without changing the overall architecture:

- Add a favorites feature using `localStorage`.
- Add sort controls for rating, release year, or episodes.
- Add author directory filters.
- Add manual featured story sections using labels.
- Add ad slots through Blogger widgets.
- Add multilingual UI strings in the `POCKETFM_CONFIG` object.
- Add a sitemap-style directory page that preloads all feed batches.
