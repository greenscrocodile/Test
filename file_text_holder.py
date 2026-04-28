import streamlit as st
import os
import json

DATA_DIR = "persistent_data"
FILES_DIR = os.path.join(DATA_DIR, "files")
TEXT_FILE = os.path.join(DATA_DIR, "text_holder.json")

def init_storage():
    if not os.path.exists(FILES_DIR):
        os.makedirs(FILES_DIR, exist_ok=True)
    if not os.path.exists(TEXT_FILE):
        os.makedirs(DATA_DIR, exist_ok=True)
        with open(TEXT_FILE, "w") as f:
            json.dump({"stored_text": ""}, f)

def get_stored_text():
    try:
        with open(TEXT_FILE, "r") as f:
            return json.load(f).get("stored_text", "")
    except Exception:
        return ""

def save_stored_text(text):
    with open(TEXT_FILE, "w") as f:
        json.dump({"stored_text": text}, f)

def list_stored_files():
    if not os.path.exists(FILES_DIR):
        return []
    # Return sorted list of basenames
    return sorted([f for f in os.listdir(FILES_DIR) if os.path.isfile(os.path.join(FILES_DIR, f))])

def show_file_text_holder():
    init_storage()
    st.title("🗂️ File & Text Holder")

    tabs = st.tabs(["📄 Files", "📝 Text Material"])

    with tabs[0]:
        st.subheader("Persistent File Storage")
        uploaded_files = st.file_uploader(
            "Upload files for all systems",
            accept_multiple_files=True,
            type=["docx", "pdf", "xlsx", "dbf"]
        )

        if uploaded_files:
            for f in uploaded_files:
                # Sanitize filename to prevent path traversal
                safe_name = os.path.basename(f.name)
                target_path = os.path.join(FILES_DIR, safe_name)
                with open(target_path, "wb") as out:
                    out.write(f.getvalue())
            st.success(f"Uploaded {len(uploaded_files)} files.")
            st.rerun()

        files = list_stored_files()
        if files:
            st.write("### Available Files")
            for idx, filename in enumerate(files):
                col1, col2 = st.columns([4, 1])
                col1.write(f"📎 {filename}")
                # Re-sanitize on retrieval to be extra safe
                safe_name = os.path.basename(filename)
                file_path = os.path.join(FILES_DIR, safe_name)

                if os.path.exists(file_path):
                    with open(file_path, "rb") as f:
                        col2.download_button("Download", f.read(), file_name=safe_name, key=f"dl_{idx}")

                    s1, s2 = st.columns([0.1, 1])
                    with s2:
                        if st.button("🗑️ Delete", key=f"del_{idx}"):
                            os.remove(file_path)
                            st.rerun()
        else:
            st.info("No files stored yet.")

    with tabs[1]:
        st.subheader("Persistent Text Material")
        current_text = get_stored_text()
        new_text = st.text_area(
            "Enter text to be available on all systems:",
            value=current_text,
            height=300
        )

        c1, c2 = st.columns(2)
        if c1.button("💾 Save Text", type="primary"):
            save_stored_text(new_text)
            st.success("Text saved successfully!")

        if c2.button("🗑️ Clear Text"):
            save_stored_text("")
            st.rerun()
