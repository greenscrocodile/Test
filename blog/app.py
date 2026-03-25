import json
import re
import sqlite3
from datetime import datetime
from pathlib import Path

from flask import Flask, flash, redirect, render_template, request, url_for
from werkzeug.utils import secure_filename

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "blog.db"
UPLOADS_DIR = BASE_DIR / "static" / "uploads"
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}
NAV_ITEMS = ["News", "Reviews", "Guides", "Videos", "Deals", "More"]
POST_TYPES = {
    "News": ["summary", "content"],
    "Review": ["summary", "content", "score", "pros", "cons"],
    "Guide": ["summary", "content", "difficulty", "read_time"],
    "List": ["summary", "content", "list_items"],
}

app = Flask(__name__)
app.config["SECRET_KEY"] = "agi-dev-secret"
app.config["UPLOAD_FOLDER"] = str(UPLOADS_DIR)


def get_db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with get_db() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS posts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                slug TEXT NOT NULL UNIQUE,
                title TEXT NOT NULL,
                category TEXT NOT NULL,
                post_type TEXT NOT NULL,
                tags TEXT NOT NULL,
                summary TEXT NOT NULL,
                content TEXT NOT NULL,
                score TEXT,
                pros TEXT,
                cons TEXT,
                difficulty TEXT,
                read_time TEXT,
                list_items TEXT,
                image_path TEXT,
                created_at TEXT NOT NULL
            )
            """
        )


def slugify(value: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9\s-]", "", value).strip().lower()
    return re.sub(r"[\s-]+", "-", cleaned)


def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def parse_line_items(value: str) -> list[str]:
    return [item.strip() for item in value.splitlines() if item.strip()]


def validate_payload(payload: dict, post_type: str) -> list[str]:
    required = POST_TYPES[post_type]
    missing = [field for field in required if not payload.get(field)]
    if not payload.get("title", "").strip():
        missing.insert(0, "title")
    return list(dict.fromkeys(missing))


def save_post(payload: dict, image_file) -> str:
    slug = slugify(payload["title"]) or "post"
    slug = f"{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{slug}"

    image_path = ""
    if image_file and image_file.filename and allowed_file(image_file.filename):
        ext = secure_filename(image_file.filename).rsplit(".", 1)[1].lower()
        filename = f"{slug}.{ext}"
        destination = UPLOADS_DIR / filename
        image_file.save(destination)
        image_path = f"uploads/{filename}"

    with get_db() as conn:
        conn.execute(
            """
            INSERT INTO posts (
                slug, title, category, post_type, tags, summary, content, score,
                pros, cons, difficulty, read_time, list_items, image_path, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                slug,
                payload["title"],
                payload["category"],
                payload["post_type"],
                json.dumps(payload["tags"]),
                payload["summary"],
                payload["content"],
                payload["score"],
                json.dumps(payload["pros"]),
                json.dumps(payload["cons"]),
                payload["difficulty"],
                payload["read_time"],
                json.dumps(payload["list_items"]),
                image_path,
                datetime.utcnow().isoformat(timespec="seconds") + "Z",
            ),
        )
    return slug


def fetch_posts(limit: int = 30) -> list[dict]:
    with get_db() as conn:
        rows = conn.execute("SELECT * FROM posts ORDER BY id DESC LIMIT ?", (limit,)).fetchall()

    posts = []
    for row in rows:
        post = dict(row)
        post["tags"] = json.loads(post["tags"])
        post["pros"] = json.loads(post["pros"] or "[]")
        post["cons"] = json.loads(post["cons"] or "[]")
        post["list_items"] = json.loads(post["list_items"] or "[]")
        posts.append(post)
    return posts


def fetch_post_by_slug(slug: str):
    with get_db() as conn:
        row = conn.execute("SELECT * FROM posts WHERE slug = ?", (slug,)).fetchone()
    if not row:
        return None
    post = dict(row)
    post["tags"] = json.loads(post["tags"])
    post["pros"] = json.loads(post["pros"] or "[]")
    post["cons"] = json.loads(post["cons"] or "[]")
    post["list_items"] = json.loads(post["list_items"] or "[]")
    return post


@app.route("/")
def home():
    posts = fetch_posts()
    featured = posts[0] if posts else None
    latest = posts[1:9] if len(posts) > 1 else []
    return render_template("home.html", posts=posts, featured=featured, latest=latest, nav_items=NAV_ITEMS)


@app.route("/post/<slug>")
def post_detail(slug: str):
    post = fetch_post_by_slug(slug)
    if not post:
        return render_template("404.html", nav_items=NAV_ITEMS), 404
    return render_template("post_detail.html", post=post, nav_items=NAV_ITEMS)


@app.route("/studio", methods=["GET", "POST"])
def studio():
    if request.method == "POST":
        post_type = request.form.get("post_type", "News")
        payload = {
            "title": request.form.get("title", "").strip(),
            "post_type": post_type,
            "category": request.form.get("category", "News"),
            "tags": [tag.strip() for tag in request.form.get("tags", "").split(",") if tag.strip()],
            "summary": request.form.get("summary", "").strip(),
            "content": request.form.get("content", "").strip(),
            "score": request.form.get("score", "").strip(),
            "pros": parse_line_items(request.form.get("pros", "")),
            "cons": parse_line_items(request.form.get("cons", "")),
            "difficulty": request.form.get("difficulty", ""),
            "read_time": request.form.get("read_time", "").strip(),
            "list_items": parse_line_items(request.form.get("list_items", "")),
        }

        missing = validate_payload(payload, post_type)
        image = request.files.get("image")
        if image and image.filename and not allowed_file(image.filename):
            missing.append("image (allowed: png, jpg, jpeg, webp)")

        if missing:
            flash(f"Please complete required fields: {', '.join(dict.fromkeys(missing))}", "error")
            return render_template(
                "studio.html",
                nav_items=NAV_ITEMS,
                post_types=list(POST_TYPES.keys()),
                categories=NAV_ITEMS,
                form_data=request.form,
            )

        slug = save_post(payload, image)
        flash("Post published successfully.", "success")
        return redirect(url_for("post_detail", slug=slug))

    return render_template(
        "studio.html",
        nav_items=NAV_ITEMS,
        post_types=list(POST_TYPES.keys()),
        categories=NAV_ITEMS,
        form_data={},
    )


@app.route("/about")
def about():
    return render_template("about.html", nav_items=NAV_ITEMS)


init_db()


if __name__ == "__main__":
    app.run(debug=True)
