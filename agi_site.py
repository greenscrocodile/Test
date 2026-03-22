import json
import re
from datetime import datetime
from pathlib import Path

import streamlit as st

st.set_page_config(page_title="AGI — Gaming & Entertainment", layout="wide")

POSTS_DIR = Path("data/posts")
IMAGES_DIR = Path("data/images")
POSTS_DIR.mkdir(parents=True, exist_ok=True)
IMAGES_DIR.mkdir(parents=True, exist_ok=True)

NAV_ITEMS = ["News", "Reviews", "Guides", "Videos", "Deals", "More"]

POST_TEMPLATES = {
    "News": {
        "label": "News Post",
        "required_fields": ["summary", "body"],
    },
    "Review": {
        "label": "Review Post",
        "required_fields": ["summary", "body", "score", "pros", "cons"],
    },
    "Guide": {
        "label": "Guide Post",
        "required_fields": ["summary", "body", "difficulty", "estimated_time"],
    },
    "List": {
        "label": "List Post",
        "required_fields": ["summary", "body", "list_items"],
    },
}


def slugify(value: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9\s-]", "", value).strip().lower()
    return re.sub(r"[\s-]+", "-", cleaned)


def inject_theme(theme: str) -> None:
    dark = theme == "Dark"
    bg = "#0f1115" if dark else "#ffffff"
    panel = "#171a21" if dark else "#f4f5f7"
    text = "#f8f8f8" if dark else "#141414"
    muted = "#9da7b4" if dark else "#57606a"
    accent = "#e50914"

    st.markdown(
        f"""
        <style>
            .stApp {{ background-color: {bg}; color: {text}; }}
            .agi-shell {{ border: 1px solid rgba(128,128,128,.25); border-radius: 14px; overflow: hidden; }}
            .agi-top {{ background: {accent}; color: white; padding: 10px 18px; font-weight: 700; display:flex; justify-content:space-between; align-items:center; }}
            .agi-nav {{ background: {panel}; padding: 10px 18px; display:flex; flex-wrap:wrap; gap:18px; border-bottom:1px solid rgba(128,128,128,.2); }}
            .agi-nav span {{ font-size:14px; font-weight:700; text-transform: uppercase; letter-spacing: .04em; }}
            .agi-card {{ background: {panel}; border: 1px solid rgba(128,128,128,.2); border-radius: 12px; padding: 14px; margin-bottom: 10px; }}
            .agi-muted {{ color:{muted}; font-size: 13px; }}
            h1, h2, h3 {{ color: {text} !important; }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def load_posts() -> list[dict]:
    posts = []
    for post_file in sorted(POSTS_DIR.glob("*.json"), reverse=True):
        with post_file.open("r", encoding="utf-8") as f:
            posts.append(json.load(f))
    return posts


def save_post(post: dict, image_bytes: bytes | None, image_name: str | None) -> Path:
    stamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    slug = slugify(post["title"]) or "post"
    post_id = f"{stamp}-{slug}"
    post["id"] = post_id
    post["created_at"] = datetime.utcnow().isoformat(timespec="seconds") + "Z"

    if image_bytes and image_name:
        extension = Path(image_name).suffix.lower() or ".jpg"
        image_file = IMAGES_DIR / f"{post_id}{extension}"
        image_file.write_bytes(image_bytes)
        post["image"] = str(image_file)
    else:
        post["image"] = ""

    output_file = POSTS_DIR / f"{post_id}.json"
    with output_file.open("w", encoding="utf-8") as f:
        json.dump(post, f, indent=2, ensure_ascii=False)

    return output_file


if "theme" not in st.session_state:
    st.session_state.theme = "Dark"

inject_theme(st.session_state.theme)

st.markdown('<div class="agi-shell">', unsafe_allow_html=True)
st.markdown(
    f"""
    <div class="agi-top">
        <div>AGI</div>
        <div>Gaming • Movies • TV • Tech</div>
    </div>
    <div class="agi-nav">{"".join([f"<span>{item}</span>" for item in NAV_ITEMS])}</div>
    """,
    unsafe_allow_html=True,
)
st.markdown("</div>", unsafe_allow_html=True)

col_a, col_b = st.columns([2, 1], gap="large")

with col_a:
    st.title("AGI Homepage")
    st.caption("IGN-inspired navigation and content sections, with a built-in publishing workflow.")

    posts = load_posts()
    if posts:
        st.subheader("Latest Published Posts")
        for post in posts[:12]:
            st.markdown('<div class="agi-card">', unsafe_allow_html=True)
            st.markdown(f"### {post['title']}")
            st.markdown(
                f"<div class='agi-muted'>{post['template']} • {post['category']} • {post['created_at']}</div>",
                unsafe_allow_html=True,
            )
            st.write(post.get("summary", ""))
            tags = ", ".join(post.get("tags", []))
            st.markdown(f"**Tags:** {tags if tags else 'None'}")
            st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.info("No posts yet. Use the Publish Post panel to create your first post.")

with col_b:
    st.subheader("Theme Setup")
    st.session_state.theme = st.radio(
        "Choose theme",
        ["Dark", "Light"],
        index=0 if st.session_state.theme == "Dark" else 1,
        help="Switching theme updates the AGI layout colors.",
    )

    st.subheader("Publish Post")
    with st.form("publish_form", clear_on_submit=True):
        template = st.selectbox("Template", list(POST_TEMPLATES.keys()))
        title = st.text_input("Title")
        category = st.selectbox("Category", NAV_ITEMS)
        tags_raw = st.text_input("Tags (comma-separated)", placeholder="xbox, fps, review")
        summary = st.text_area("Summary", height=90)
        body = st.text_area("Main content", height=160)
        image = st.file_uploader("Featured image", type=["png", "jpg", "jpeg", "webp"])

        # Template-specific fields
        score = st.text_input("Score (Review template)") if template == "Review" else ""
        pros = st.text_area("Pros (one per line)", height=90) if template == "Review" else ""
        cons = st.text_area("Cons (one per line)", height=90) if template == "Review" else ""

        difficulty = st.selectbox("Difficulty", ["Beginner", "Intermediate", "Advanced"]) if template == "Guide" else ""
        estimated_time = st.text_input("Estimated time") if template == "Guide" else ""

        list_items = st.text_area("List items (one per line)", height=100) if template == "List" else ""

        submitted = st.form_submit_button("Publish")

        if submitted:
            post = {
                "title": title.strip(),
                "template": template,
                "category": category,
                "summary": summary.strip(),
                "body": body.strip(),
                "tags": [tag.strip() for tag in tags_raw.split(",") if tag.strip()],
                "score": score.strip(),
                "pros": [x.strip() for x in pros.splitlines() if x.strip()],
                "cons": [x.strip() for x in cons.splitlines() if x.strip()],
                "difficulty": difficulty,
                "estimated_time": estimated_time.strip(),
                "list_items": [x.strip() for x in list_items.splitlines() if x.strip()],
            }

            required_fields = POST_TEMPLATES[template]["required_fields"]
            missing = [field for field in required_fields if not post.get(field)]
            if not title.strip():
                missing.insert(0, "title")

            if missing:
                st.error(f"Please complete required fields: {', '.join(dict.fromkeys(missing))}")
            else:
                image_bytes = image.getvalue() if image else None
                image_name = image.name if image else None
                file_path = save_post(post, image_bytes, image_name)
                st.success(f"Published successfully: {file_path.name}")
                st.rerun()

st.caption("Posts are stored locally in data/posts as JSON and appear instantly on the homepage.")
