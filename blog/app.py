import json
import re
import sqlite3
from datetime import datetime
from pathlib import Path

import streamlit as st

st.set_page_config(page_title="AGI Blog", page_icon="🎮", layout="wide")

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "blog.db"
UPLOADS_DIR = BASE_DIR / "uploads"
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)

IGN_STYLE_NAV = ["News", "Reviews", "Guides", "Videos", "Deals", "More"]
POST_TYPES = {
    "News": ["summary", "content"],
    "Review": ["summary", "content", "score", "pros", "cons"],
    "Guide": ["summary", "content", "difficulty", "read_time"],
    "List": ["summary", "content", "list_items"],
}


def get_db() -> sqlite3.Connection:
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


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
    clean = re.sub(r"[^a-zA-Z0-9\s-]", "", value).strip().lower()
    return re.sub(r"[\s-]+", "-", clean)


def set_theme_styles(theme: str) -> None:
    is_dark = theme == "Dark"
    background = "#0e1117" if is_dark else "#ffffff"
    foreground = "#f2f5f8" if is_dark else "#14171c"
    panel = "#161b22" if is_dark else "#f4f6f8"
    muted = "#8b96a5" if is_dark else "#5a6675"
    accent = "#e50914"

    st.markdown(
        f"""
        <style>
            .stApp {{ background-color: {background}; color: {foreground}; }}
            .top-header {{ background: {accent}; color: #fff; border-radius: 12px 12px 0 0; padding: 12px 18px; font-weight: 700; display:flex; justify-content:space-between; }}
            .top-nav {{ background: {panel}; padding: 10px 18px; border-radius: 0 0 12px 12px; display:flex; gap:16px; flex-wrap:wrap; margin-bottom: 1rem; border: 1px solid rgba(128,128,128,.20); border-top: none; }}
            .top-nav span {{ font-size: 14px; text-transform: uppercase; font-weight: 700; letter-spacing: .04em; }}
            .post-card {{ background: {panel}; border: 1px solid rgba(128,128,128,.2); border-radius: 12px; padding: 16px; margin-bottom: 12px; }}
            .muted {{ color: {muted}; font-size: 13px; }}
            h1, h2, h3 {{ color: {foreground} !important; }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def save_post(post: dict, image_bytes: bytes | None, image_name: str | None) -> None:
    slug = slugify(post["title"]) or "post"
    slug = f"{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{slug}"

    image_path = ""
    if image_bytes and image_name:
        extension = Path(image_name).suffix.lower() or ".jpg"
        target = UPLOADS_DIR / f"{slug}{extension}"
        target.write_bytes(image_bytes)
        image_path = str(target.relative_to(BASE_DIR))

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
                post["title"],
                post["category"],
                post["post_type"],
                json.dumps(post["tags"]),
                post["summary"],
                post["content"],
                post["score"],
                json.dumps(post["pros"]),
                json.dumps(post["cons"]),
                post["difficulty"],
                post["read_time"],
                json.dumps(post["list_items"]),
                image_path,
                datetime.utcnow().isoformat(timespec="seconds") + "Z",
            ),
        )


def load_posts(limit: int = 20) -> list[sqlite3.Row]:
    with get_db() as conn:
        result = conn.execute(
            "SELECT * FROM posts ORDER BY id DESC LIMIT ?",
            (limit,),
        ).fetchall()
    return result


def render_header() -> None:
    st.markdown('<div class="top-header"><span>AGI</span><span>Gaming • Movies • TV • Tech</span></div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="top-nav">' + "".join([f"<span>{item}</span>" for item in IGN_STYLE_NAV]) + "</div>",
        unsafe_allow_html=True,
    )


def render_home() -> None:
    st.title("AGI Homepage")
    posts = load_posts()
    if not posts:
        st.info("No posts published yet. Open Studio to publish your first post.")
        return

    for row in posts:
        tags = ", ".join(json.loads(row["tags"]))
        st.markdown('<div class="post-card">', unsafe_allow_html=True)
        st.markdown(f"### {row['title']}")
        st.markdown(
            f"<div class='muted'>{row['post_type']} • {row['category']} • {row['created_at']}</div>",
            unsafe_allow_html=True,
        )
        st.write(row["summary"])
        st.markdown(f"**Tags:** {tags if tags else 'None'}")
        st.markdown("</div>", unsafe_allow_html=True)


def render_studio() -> None:
    st.title("Post Studio")
    st.caption("Fill in the form and click publish. Your post appears instantly on Home.")

    with st.form("publish_form", clear_on_submit=True):
        post_type = st.selectbox("Template", list(POST_TYPES.keys()))
        title = st.text_input("Title")
        category = st.selectbox("Category", IGN_STYLE_NAV)
        tags_raw = st.text_input("Tags (comma-separated)", placeholder="ps5, action, rpg")
        summary = st.text_area("Summary", height=100)
        content = st.text_area("Main content", height=190)
        image = st.file_uploader("Featured image", type=["png", "jpg", "jpeg", "webp"])

        score = st.text_input("Score (for Review)") if post_type == "Review" else ""
        pros = st.text_area("Pros (one per line)", height=80) if post_type == "Review" else ""
        cons = st.text_area("Cons (one per line)", height=80) if post_type == "Review" else ""
        difficulty = (
            st.selectbox("Difficulty", ["Beginner", "Intermediate", "Advanced"]) if post_type == "Guide" else ""
        )
        read_time = st.text_input("Estimated read time") if post_type == "Guide" else ""
        list_items = st.text_area("List items (one per line)", height=100) if post_type == "List" else ""

        publish = st.form_submit_button("Publish Post")

        if publish:
            payload = {
                "title": title.strip(),
                "post_type": post_type,
                "category": category,
                "tags": [tag.strip() for tag in tags_raw.split(",") if tag.strip()],
                "summary": summary.strip(),
                "content": content.strip(),
                "score": score.strip(),
                "pros": [line.strip() for line in pros.splitlines() if line.strip()],
                "cons": [line.strip() for line in cons.splitlines() if line.strip()],
                "difficulty": difficulty,
                "read_time": read_time.strip(),
                "list_items": [line.strip() for line in list_items.splitlines() if line.strip()],
            }
            required = POST_TYPES[post_type]
            missing = [field for field in required if not payload.get(field)]
            if not payload["title"]:
                missing.insert(0, "title")

            if missing:
                st.error(f"Please complete required fields: {', '.join(dict.fromkeys(missing))}")
            else:
                image_bytes = image.getvalue() if image else None
                image_name = image.name if image else None
                save_post(payload, image_bytes, image_name)
                st.success("Post published successfully.")
                st.rerun()


def main() -> None:
    init_db()

    if "theme" not in st.session_state:
        st.session_state.theme = "Dark"

    with st.sidebar:
        st.header("AGI Controls")
        st.session_state.theme = st.radio(
            "Theme",
            ["Dark", "Light"],
            index=0 if st.session_state.theme == "Dark" else 1,
        )
        page = st.radio("Page", ["Home", "Studio"], index=0)

    set_theme_styles(st.session_state.theme)
    render_header()

    if page == "Home":
        render_home()
    else:
        render_studio()


if __name__ == "__main__":
    main()
