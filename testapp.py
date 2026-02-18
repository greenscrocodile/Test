import streamlit as st
import pandas as pd
from docxtpl import DocxTemplate
from num2words import num2words
import io
from datetime import date, datetime
import uuid
import re
import os

# --- APP CONFIGURATION ---
st.set_page_config(page_title="Challan Master Pro", layout="wide")

# (Keep your existing CSS here...)
st.markdown("""
    <style>
    [data-testid="stVerticalBlock"] > div { gap: 0.5rem !important; }
    div[data-testid="column"] button { margin-top: 28px !important; }
    .stMarkdown p { font-size: 14px !important; line-height: 1.6 !important; margin-bottom: 0px !important; }
    </style>
    """, unsafe_allow_html=True)

# --- CONFIGURATION DATA ---
BANKS = [
    {"name": "State Bank of India", "file": "logos/SBI.jpg"},
    {"name": "HDFC Bank", "file": "logos/HDFC.jpg"},
    # ... (Keep your full bank list here)
]

PURPOSE_MAP = {
    "Advance Payment": ["Monthly Energy Advance", "Pre-paid Top-up"],
    "Advance Security Deposit": ["Initial ASD", "Additional ASD"],
    "Security Deposit": ["New Connection SD", "Load Enhancement SD"],
    "Meter Security Deposit": ["Single Phase Meter", "Three Phase Meter", "CT Meter"],
    "Processing Fee": ["Standard Registration Fee"]
}

# --- HELPER FUNCTIONS ---
def format_indian_currency(number):
    try:
        main = str(int(float(number)))
        if len(main) <= 3: return main
        last_three = main[-3:]
        remaining = main[:-3]
        res = ""
        while len(remaining) > 2:
            res = "," + remaining[-2:] + res
            remaining = remaining[:-2]
        if remaining: res = remaining + res
        return f"{res},{last_three}"
    except: return "0"

@st.dialog("Select Bank", width="medium")
def bank_selection_dialog():
    st.write("### 🏦 Select Bank")
    cols = st.columns(7, gap="small")
    for i, bank in enumerate(BANKS):
        with cols[i % 7]:
            if os.path.exists(bank['file']): st.image(bank['file'])
            else: st.caption(bank['name'])
            if st.button("Select", key=f"btn_{i}"):
                st.session_state.selected_bank = bank['name']
                st.rerun()

# --- INITIALIZATION ---
if 'all_receipts' not in st.session_state: st.session_state.all_receipts = []
if 'locked' not in st.session_state: st.session_state.locked = False
if 'selected_bank' not in st.session_state: st.session_state.selected_bank = ""
if 'consumer_key' not in st.session_state: st.session_state.consumer_key = 0
if 'temp_instruments' not in st.session_state: st.session_state.temp_instruments = []

# --- SIDEBAR ---
with st.sidebar:
    st.header("⚙️ Configuration")
    
    # 1. NEW RADIO BUTTON
    app_mode = st.radio("Challan Type", ["💠 C. C", "💠 OTHER"], disabled=st.session_state.locked)
    
    s_challan = st.text_input("Starting Challan", disabled=st.session_state.locked)
    s_pdate = st.date_input("Challan Date", disabled=st.session_state.locked)

    st.divider()
    
    # Master Data Upload
    data_file = st.file_uploader("Upload Master Data (.xlsx)", type=["xlsx"])

    if not st.session_state.locked:
        if st.button("Confirm Setup", type="primary"):
            if not s_challan.isdigit(): st.error("Invalid Challan No.")
            elif not data_file: st.error("Upload Master Data.")
            else:
                st.session_state.locked = True
                st.session_state.app_mode = app_mode
                st.session_state.start_no = int(s_challan)
                st.session_state.formatted_pdate = s_pdate.strftime("%d.%m.%Y")
                st.rerun()
    else:
        st.info(f"Mode: {st.session_state.app_mode}")
        if st.button("Reset Session"):
            st.session_state.locked = False
            st.session_state.all_receipts = []
            st.rerun()

# --- MAIN FLOW ---
if st.session_state.locked:
    curr_count = len(st.session_state.all_receipts)
    next_no = st.session_state.start_no + curr_count

    m1, m2, m3 = st.columns(3)
    m1.metric("Current No.", next_no)
    m2.metric("Date", st.session_state.formatted_pdate)
    m3.metric("Entered", curr_count)

    try:
        df = pd.read_excel(data_file, sheet_name="BILL")
    except:
        st.error("Sheet 'BILL' not found."); st.stop()

    st.divider()
    has_active_instruments = len(st.session_state.temp_instruments) > 0

    # ---------------------------
    # FLOW A: C.C (Original)
    # ---------------------------
    if st.session_state.app_mode == "💠 C. C":
        # ... (Insert your existing Month/Year selection and Total Amount calculation here)
        # For brevity, assuming total_amt and display_month_text are calculated as per your old code
        total_amt = 1000 # Placeholder for your existing logic
        display_month_text = "Jan-2026" # Placeholder
        purpose_val = "C.C. Charges"
        desc_val = display_month_text

    # ---------------------------
    # FLOW B: OTHER (New)
    # ---------------------------
    else:
        c1, c2 = st.columns(2)
        with c1:
            purpose_val = st.selectbox("Purpose", options=list(PURPOSE_MAP.keys()))
        with c2:
            desc_val = st.selectbox("Description", options=PURPOSE_MAP[purpose_val])
        
        # Manual Amount Logic
        if purpose_val == "Processing Fee":
            total_amt = 20000
            st.info("💰 Processing Fee is fixed at ₹20,000")
        else:
            total_amt = st.number_input("Enter Amount (₹)", min_value=1, step=1)

    # ---------------------------
    # COMMON CONSUMER SEARCH
    # ---------------------------
    search_num = st.text_input("Enter Consumer Number", max_chars=3, key=f"c_{st.session_state.consumer_key}")
    
    if search_num and len(search_num) == 3:
        result = df[df['Consumer Number'].astype(str).str.zfill(3) == search_num]
        
        if not result.empty:
            row = result.iloc[0]
            st.success(f"**Target:** {row['Name']} | **Purpose:** {purpose_val}")
            
            # --- BANK & INSTRUMENTS (Your existing logic) ---
            b_col1, b_col2 = st.columns([0.9, 0.1], vertical_alignment="bottom")
            with b_col1: bank_name = st.text_input("Bank Name", value=st.session_state.selected_bank)
            with b_col2: 
                if st.button("🔍"): bank_selection_dialog()

            # (Add Payment Details Form here - same as your old code)
            # ...
            
            if st.button("🚀 Add to Batch", type="primary"):
                if not st.session_state.temp_instruments: st.error("Add payment details first.")
                else:
                    st.session_state.all_receipts.append({
                        'id': str(uuid.uuid4()), 
                        'challan': next_no, 
                        'pdate': st.session_state.formatted_pdate,
                        'name': row['Name'], 
                        'num': row['Consumer Number'],
                        'purpose': purpose_val, # NEW FIELD
                        'description': desc_val, # NEW FIELD
                        'amount': format_indian_currency(total_amt),
                        'words': num2words(total_amt, lang='en_IN').title(),
                        'bank': bank_name,
                        'pay_no': ", ".join([i['no'] for i in st.session_state.temp_instruments]),
                        # ... other fields
                    })
                    st.session_state.temp_instruments = []; st.rerun()

    # --- FINALIZATION ---
    if st.session_state.all_receipts:
        if st.button("📥 Generate File"):
            # Select template based on mode
            tpl_path = "Test.docx" if st.session_state.app_mode == "💠 C. C" else "Other_Template.docx"
            
            if os.path.exists(tpl_path):
                doc = DocxTemplate(tpl_path)
                doc.render({'receipts': st.session_state.all_receipts})
                output = io.BytesIO()
                doc.save(output)
                st.download_button("Download Now", output.getvalue(), file_name=f"Challans_{app_mode}.docx")
            else:
                st.error(f"Template {tpl_path} not found.")
