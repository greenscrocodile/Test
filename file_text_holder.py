import streamlit as st
import os
from github_utils import list_files_github, upload_file_github, delete_file_github, get_github_config

FILES_FOLDER = "user_files"

def show_file_text_holder():
    st.title("🗂️ File Holder (GitHub Sync)")

    config = get_github_config()
    if not config:
        st.warning("⚠️ GitHub Integration not configured. Please add `GITHUB_TOKEN` and `GITHUB_REPO` to Streamlit Secrets.")
        with st.expander("ℹ️ How to configure"):
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
        return

    st.success(f"🔗 Connected to: `{config['repo']}`")

    tabs = st.tabs(["📄 Managed Files", "📝 Text Material"])

    with tabs[0]:
        st.subheader("📤 Upload New Files")
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
        # For text material, we can also use GitHub if we want true persistence
        # across sessions without local storage. Let's stick to session for now
        # as the user emphasized "Files" specifically for the creator.

        if "stored_text" not in st.session_state:
            st.session_state.stored_text = ""

        st.session_state.stored_text = st.text_area(
            "Paste text here to keep it during your current session:",
            value=st.session_state.stored_text,
            height=300
        )
        st.caption("Note: Text material is currently session-only. Use the File tab for cross-system persistence.")
