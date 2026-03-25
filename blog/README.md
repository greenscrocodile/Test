# AGI Blog (IGN-style)

This is a fresh **blog project** inside `blog/` with:

- IGN-inspired top navigation.
- Dark/Light theme toggle.
- A **Post Studio** page to publish content with a form.
- SQLite-based storage so posts are immediately visible on the homepage.

## Run locally

```bash
cd blog
pip install -r requirements.txt
streamlit run app.py
```

## Run tests

From the repository root:

```bash
python -m unittest tests/test_blog_app.py
```

## Publishing workflow

1. Open **Studio** from the sidebar page switcher.
2. Choose a template (`News`, `Review`, `Guide`, `List`).
3. Fill title, tags, summary, main content, and optional image.
4. Click **Publish Post**.
5. Return to **Home** to see your newly published post.

## New Git repository setup

If you want this as a completely separate repository named `blog`:

```bash
cd blog
git init
git add .
git commit -m "Initial AGI blog project"
```
