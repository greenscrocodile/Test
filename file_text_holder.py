import streamlit as st
import os

def show_file_text_holder():
    st.title("🗂️ File & Text Holder")

    # Initialize session state for persistent text and file list (simulated)
    if "stored_text" not in st.session_state:
        st.session_state.stored_text = ""
    if "stored_files" not in st.session_state:
        st.session_state.stored_files = []

    tabs = st.tabs(["📄 Files", "📝 Text Material"])

    with tabs[0]:
        st.subheader("Upload & Manage Files")
        uploaded_files = st.file_uploader(
            "Choose files",
            accept_multiple_files=True,
            type=["docx", "pdf", "xlsx", "dbf"]
        )

        if uploaded_files:
            for f in uploaded_files:
                if f.name not in [sf["name"] for sf in st.session_state.stored_files]:
                    # In a real app, we might save to disk, but here we'll keep in session
                    st.session_state.stored_files.append({
                        "name": f.name,
                        "content": f.getvalue()
                    })
            st.success(f"Added {len(uploaded_files)} files to holder.")

        if st.session_state.stored_files:
            st.write("### Available Files")
            for idx, f in enumerate(st.session_state.stored_files):
                col1, col2 = st.columns([4, 1])
                col1.write(f"📎 {f['name']}")
                col2.download_button("Download", f["content"], file_name=f["name"], key=f"dl_{idx}")
                if st.button("Delete", key=f"del_{idx}"):
                    st.session_state.stored_files.pop(idx)
                    st.rerun()
        else:
            st.info("No files stored yet.")

    with tabs[1]:
        st.subheader("Text Material Holder")
        st.session_state.stored_text = st.text_area(
            "Paste or type text to save:",
            value=st.session_state.stored_text,
            height=300
        )
        st.info("💡 This text is saved in your current session.")

        if st.button("Clear Text"):
            st.session_state.stored_text = ""
            st.rerun()
