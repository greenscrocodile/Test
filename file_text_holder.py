import streamlit as st
import os
import json
from github_utils import list_files_github, upload_file_github, delete_file_github, get_github_config

FILES_FOLDER = "user_files"
TEXT_FOLDER = "persistent_data"
TEXT_FILE = "text_holder.json"
TEXT_KEY = "stored_text"


def _load_local_text():
    os.makedirs(TEXT_FOLDER, exist_ok=True)
    path = os.path.join(TEXT_FOLDER, TEXT_FILE)
    if not os.path.exists(path):
        return ""
    try:
        with open(path, "r", encoding="utf-8") as f:
            payload = json.load(f)
        return payload.get("text", "")
    except Exception:
        return ""


def _save_local_text(text_value):
    os.makedirs(TEXT_FOLDER, exist_ok=True)
    path = os.path.join(TEXT_FOLDER, TEXT_FILE)
    with open(path, "w", encoding="utf-8") as f:
        json.dump({"text": text_value}, f, ensure_ascii=False, indent=2)

def show_file_text_holder():
    st.title("🗂️ File Holder (GitHub Sync)")

    config = get_github_config()
    if config:
        st.success(f"🔗 Connected to: `{config['repo']}`")
    else:
        st.warning("⚠️ GitHub is not configured. File sync is disabled, but text notes still work locally.")
        with st.expander("ℹ️ Optional: Configure GitHub sync"):
            st.markdown("""
            1. Go to your Streamlit Cloud Dashboard.
            2. Open **Settings** > **Secrets**.
            3. Add the following:
               ```toml
               GITHUB_TOKEN = "your_personal_access_token"
               GITHUB_REPO = "your_username/your_repo_name"
               GITHUB_BRANCH = "main" # Optional
               ```
            """)

    tabs = st.tabs(["📄 Managed Files", "📝 Text Material"])

    with tabs[0]:
        st.subheader("📤 Upload New Files")
        if not config:
            st.info("Enable GitHub secrets to use file upload/download/delete.")
        else:
            uploaded_files = st.file_uploader(
                "Select files to sync with repository",
                accept_multiple_files=True,
                type=["docx", "pdf", "xlsx", "dbf"]
            )

            if uploaded_files:
                for f in uploaded_files:
                    with st.spinner(f"Syncing {f.name} to GitHub..."):
                        success, error = upload_file_github(FILES_FOLDER, f.name, f.getvalue())
                        if success:
                            st.toast(f"✅ {f.name} synced!")
                        else:
                            st.error(f"❌ Failed to sync {f.name}: {error}")
                st.rerun()

            st.divider()
            st.subheader("📂 Repository Storage")
            with st.spinner("Loading files from GitHub..."):
                files, error = list_files_github(FILES_FOLDER)

            if error:
                st.error(f"Error connecting to GitHub: {error}")
            elif files:
                st.caption(f"Currently storing {len(files)} files in `{FILES_FOLDER}/`")
                for idx, f_meta in enumerate(files):
                    filename = f_meta["name"]
                    with st.container(border=True):
                        col1, col2, col3 = st.columns([3, 1, 1])
                        col1.write(f"**{filename}**")

                        raw_url = f_meta["download_url"]
                        col2.markdown(f"[📥 Download]({raw_url})")

                        if col3.button("🗑️ Delete", key=f"del_gh_{idx}", type="secondary"):
                            with st.status(f"Deleting {filename} from repo..."):
                                success, error = delete_file_github(FILES_FOLDER, filename)
                                if success:
                                    st.toast(f"🗑️ {filename} removed from GitHub")
                                    st.rerun()
                                else:
                                    st.error(f"❌ Delete failed: {error}")
            else:
                st.info("Your repository file holder is empty. Upload files to see them here across all systems.")

    with tabs[1]:
        st.subheader("📝 Persistent Text Material")
        if TEXT_KEY not in st.session_state:
            st.session_state[TEXT_KEY] = _load_local_text()

        updated_text = st.text_area(
            "Paste text here (auto-saved locally):",
            value=st.session_state[TEXT_KEY],
            height=300
        )
        if updated_text != st.session_state[TEXT_KEY]:
            st.session_state[TEXT_KEY] = updated_text
            _save_local_text(updated_text)
            st.toast("💾 Text saved")

        st.caption("Text is persisted to `persistent_data/text_holder.json`.")
