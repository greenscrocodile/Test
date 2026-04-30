import streamlit as st
from challan_generator import show_challan_generator
from recon_editor import show_recon_editor
from receipt_generator import show_receipt_generator
from bill_calculator import show_bill_calculator
from bill_corrector import show_bill_corrector
from file_text_holder import show_file_text_holder

# --- APP CONFIGURATION ---
st.set_page_config(page_title="HTS WORKS", layout="wide")

# --- NAVIGATION LOGIC ---
if "active_page" not in st.session_state:
    st.session_state.active_page = "Home"

def navigate_to(page):
    st.session_state.active_page = page
    st.rerun()

# --- PAGE RENDERING ---

if st.session_state.active_page == "Home":
    st.markdown(r"""
        <style>
        .main-title {
            text-align: center;
            font-size: clamp(3rem, 10vw, 5rem) !important;
            font-weight: 900 !important;
            margin-top: 0.5rem !important;
            margin-bottom: 2rem !important;
            color: #1E3A8A !important;
            letter-spacing: 2px !important;
            text-transform: uppercase;
        }
        /* Dashboard Button Styling */
        .stButton button {
            height: 220px !important;
            width: 100% !important;
            max-width: 350px !important; /* Prevent huge buttons on wide screens */
            margin: 0 auto !important;
            display: flex !important;
            border-radius: 10px !important;
            border: 3px solid #E5E7EB !important;
            background-color: #FFFFFF !important;
            transition: all 0.3s ease !important;
            padding: 20px !important;
        }
        .stButton button:hover {
            border-color: #3B82F6 !important;
            background-color: #F9FAFB !important;
            transform: translateY(-5px) !important;
            box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1) !important;
        }
        .stButton button p {
            font-size: 1.4rem !important;
            font-weight: 800 !important;
            line-height: 1.3 !important;
            color: #111827 !important;
            white-space: pre-wrap !important;
            text-align: center !important;
            word-wrap: break-word !important;
        }
        /* Center the button grid on very wide screens */
        [data-testid="column"] {
            display: flex !important;
            justify-content: center !important;
        }
        </style>
    """, unsafe_allow_html=True)

    st.markdown("<h1 class='main-title'>HTS WORKS</h1>", unsafe_allow_html=True)

    tools = [
        ("📝\nChallan Generator", "Challan Generator"),
        ("🔄\nRecon Editor", "Recon Editor"),
        ("🧾\nReceipt Generator", "Receipt Generator"),
        ("🧮\nBill Calculator", "Bill Calculator"),
        ("✏️\nBill Corrector", "Bill Corrector"),
        ("📁\nFile Manager", "File Manager"),
        ("🗂️\nFile & Text Holder", "File & Text Holder"),
        ("🚀\nComing Soon", "Coming Soon"),
    ]

    for i in range(0, 8, 4):
        cols = st.columns(4, gap="medium")
        for j in range(4):
            idx = i + j
            if idx < len(tools):
                label_display, page_name = tools[idx]
                with cols[j]:
                    if st.button(label_display, key=f"dash_btn_{idx}"):
                        if page_name != "Coming Soon":
                            navigate_to(page_name)
                        else:
                            st.toast("🚀 Coming Soon!")

else:
    st.markdown(r"""
        <style>
        /* Reset button styles for tool pages */
        .stButton button {
            height: auto !important;
            width: auto !important;
            max-width: none !important;
            padding: 0.4rem 1rem !important;
            font-size: 1rem !important;
            border-radius: 10px !important;
        }
        .stButton button p {
            font-size: 1rem !important;
        }
        /* Adjust action buttons in columns to fill width and align height with inputs */
        div[data-testid="column"] .stButton button {
            width: 100% !important;
            height: 45px !important;
            margin-top: 0px !important;
        }
        /* Global styles for tool elements */
        [data-testid="stVerticalBlock"] > div { gap: 0.5rem !important; }
        .stMarkdown p { font-size: 14px !important; line-height: 1.6 !important; }
        .instrument-row { background-color: #f9f9f9; padding: 5px; border-radius: 10px; margin-bottom: 2px; }
        [data-testid="stImage"] img { width: 65px !important; height: 65px !important; object-fit: contain !important; border-radius: 5px; border: 1px solid #eee; display: block; margin-left: auto; margin-right: auto; }
        </style>
    """, unsafe_allow_html=True)

    # Tool Header with Back Button
    col_back, col_title = st.columns([1, 6])
    with col_back:
        if st.button("⬅️ Back to Home"):
            navigate_to("Home")
    with col_title:
        st.subheader(f"Tool: {st.session_state.active_page}")

    st.write("---")

    # Render the selected tool
    if st.session_state.active_page == "Challan Generator":
        show_challan_generator()
    elif st.session_state.active_page == "Recon Editor":
        show_recon_editor()
    elif st.session_state.active_page == "Receipt Generator":
        show_receipt_generator()
    elif st.session_state.active_page == "Bill Calculator":
        show_bill_calculator()
    elif st.session_state.active_page == "Bill Corrector":
        show_bill_corrector()
    elif st.session_state.active_page == "File Manager":
        from file_manager import show_file_manager
        show_file_manager()
    elif st.session_state.active_page == "File & Text Holder":
        show_file_text_holder()
