import streamlit as st
from challan_generator import show_challan_generator
from recon_editor import show_recon_editor
from receipt_generator import show_receipt_generator
from bill_calculator import show_bill_calculator
from bill_corrector import show_bill_corrector
from file_manager import show_file_manager

# --- APP CONFIGURATION ---
st.set_page_config(page_title="HTS WORKS", layout="wide")

# --- APP CONFIGURATION ---
st.set_page_config(page_title="Multi-Tool Master", layout="wide")

# --- GLOBAL CSS (Migrated Tool Styles) ---
GLOBAL_CSS = r"""
<style>
[data-testid="stVerticalBlock"] > div { gap: 0.5rem !important; }

[data-testid="stImage"] img {
    width: 65px !important; height: 65px !important;
    object-fit: contain !important; border-radius: 5px;
    border: 1px solid #eee; display: block;
    margin-left: auto; margin-right: auto;
}

.stMarkdown p {
    font-size: 14px !important;
    line-height: 1.6 !important;
    margin-bottom: 0px !important;
}

.instrument-row {
    background-color: #f9f9f9;
    padding: 5px;
    border-radius: 5px;
    margin-bottom: 2px;
}
</style>
"""
st.markdown(GLOBAL_CSS, unsafe_allow_html=True)

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
            font-size: 6rem !important;
            font-weight: 900 !important;
            margin-top: 1rem !important;
            margin-bottom: 3rem !important;
            color: #1E3A8A !important;
            letter-spacing: 5px !important;
            text-transform: uppercase;
        }
        /* Target all buttons on home page */
        .stButton button {
            height: 250px !important;
            width: 100% !important;
            border-radius: 5px !important;
            border: 3px solid #E5E7EB !important;
            background-color: #FFFFFF !important;
            transition: all 0.3s ease !important;
        }
        .stButton button:hover {
            border-color: #3B82F6 !important;
            background-color: #F9FAFB !important;
            transform: translateY(-5px) !important;
            box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1) !important;
        }
        .stButton button p {
            font-size: 1.5rem !important;
            font-weight: 800 !important;
            line-height: 1.2 !important;
            color: #111827 !important;
            white-space: pre-wrap !important;
        }
        /* Attempt to make symbols/emojis larger */
        /* Since emojis are often the first character or line */
        .stButton button p::first-line {
            font-size: 4rem !important;
        }
        </style>
    """, unsafe_allow_html=True)

    st.markdown("<h1 class='main-title'>HTS WORKS</h1>", unsafe_allow_html=True)
    # Dashboard-specific CSS
    st.markdown(r"""
    <style>
    .main-title {
        text-align: center;
        font-size: 3.5rem;
        font-weight: 800;
        margin-bottom: 3rem;
        color: #1E3A8A;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.1);
    }
    div.stButton > button {
        width: 100% !important;
        height: 180px !important;
        font-size: 1.5rem !important;
        font-weight: bold !important;
        border-radius: 20px !important;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
        border: 3px solid #E5E7EB !important;
        background-color: white !important;
        color: #1F2937 !important;
        white-space: pre-line !important;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1) !important;
    }
    div.stButton > button:hover {
        transform: translateY(-5px) !important;
        box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1) !important;
        border-color: #3B82F6 !important;
        color: #3B82F6 !important;
        background-color: #F9FAFB !important;
    }
    </style>
    """, unsafe_allow_html=True)

    st.markdown("<h1 class='main-title'>🛠️ Multi-Tool Dashboard</h1>", unsafe_allow_html=True)

    # 3x3 Grid
    cols = [st.columns(3, gap="large") for _ in range(3)]

    tools = [
        ("📝\nChallan Generator", "Challan Generator"),
        ("🔄\nRecon Editor", "Recon Editor"),
        ("🧾\nReceipt Generator", "Receipt Generator"),
        ("🧮\nBill Calculator", "Bill Calculator"),
        ("✏️\nBill Corrector", "Bill Corrector"),
        ("📁\nFile manager", "File manager"),
        ("6️⃣\nEmpty 6", None),
        ("7️⃣\nEmpty 7", None),
        ("8️⃣\nEmpty 8", None),
        ("9️⃣\nEmpty 9", None),
    ]

    for i in range(0, 9, 3):
        cols = st.columns(3, gap="large")
        for j in range(3):
            idx = i + j
            label, page = tools[idx]
            with cols[j]:
                if st.button(label, key=f"dash_btn_{idx}"):
                    if page:
                        navigate_to(page)
                    else:
                        st.toast("🚀 Coming Soon!")

else:
    st.markdown(r"""
        <style>
        /* Reset button styles for tool pages */
        .stButton button {
            height: auto !important;
            width: auto !important;
            padding: 0.5rem 1.5rem !important;
            font-size: 1rem !important;
            border-radius: 5px !important;
        }
        .stButton button p {
            font-size: 1rem !important;
        }
        /* Global styles for tool elements */
        [data-testid="stVerticalBlock"] > div { gap: 0.5rem !important; }
        .stMarkdown p { font-size: 14px !important; line-height: 1.6 !important; }
        .instrument-row { background-color: #f9f9f9; padding: 5px; border-radius: 5px; margin-bottom: 2px; }
        [data-testid="stImage"] img { width: 65px !important; height: 65px !important; object-fit: contain !important; border-radius: 5px; border: 1px solid #eee; display: block; margin-left: auto; margin-right: auto; }
        </style>
    for i in range(9):
        label, page = tools[i]
        with cols[i // 3][i % 3]:
            if st.button(label, key=f"tool_btn_{i}"):
                if page:
                    navigate_to(page)
                else:
                    st.toast("🚀 This tool is coming soon!", icon="⏳")

else:
    # Tool-specific CSS (Reset buttons)
    st.markdown(
    """
    <style>
    div.stButton > button {
        height: auto !important;
        width: auto !important;
        padding: 0.5rem 1rem !important;
        font-size: 1rem !important;
        border-radius: 8px !important;
        border: 1px solid #dcdcdc !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)
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
    elif st.session_state.active_page == "File manager":
        show_file_manager()
