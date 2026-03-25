# AGI Website (IGN-style)

This project is now a **full Flask website** (not Streamlit) with:

- IGN-style top navigation and homepage sections.
- Dark/Light theme toggle stored in browser localStorage.
- A Post Studio page (`/studio`) to publish posts from a form.
- SQLite database persistence plus image uploads.
- Individual post pages (`/post/<slug>`).

## Run locally

```bash
cd blog
pip install -r requirements.txt
python app.py
```

Then open `http://127.0.0.1:5000`.

## Routes

- `/` → homepage with featured and latest posts
- `/studio` → form-based post publishing page
- `/post/<slug>` → post details page
- `/about` → basic about page

## Run tests

From repository root:

```bash
python -m unittest tests/test_blog_app.py
```

## New Git repository setup

If you want this as a completely separate repository named `blog`:

```bash
cd blog
git init
git add .
git commit -m "Initial AGI website"
```
