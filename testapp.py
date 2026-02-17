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
st.set_page_config(page_title="Challan Master", layout="wide")

# --- CUSTOM CSS ---
st.markdown("""
    <style>
    [data-testid="stVerticalBlock"] > div { gap: 0.5rem !important; }
    div[data-testid="column"] button { margin-top: 28px !important; }
    
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
    """, unsafe_allow_html=True)

# --- BANK LOGOS CONFIGURATION ---
BANKS = [
    {"name": "State Bank of India", "file": "logos/SBI.jpg"},
    {"name": "HDFC Bank", "file": "logos/HDFC.jpg"},
    {"name": "ICICI Bank", "file": "logos/ICICI Bank.jpg"},
    {"name": "Axis Bank", "file": "logos/Axis Bank.jpg"},
    {"name": "Indian Bank", "file": "logos/Indian Bank.jpg"},
    {"name": "Canara Bank", "file": "logos/Canara.jpg"},
    {"name": "Bank of Baroda", "file": "logos/Bank of Baroda.jpg"},
    {"name": "Union Bank of India", "file": "logos/Union Bank of India.jpg"},
    {"name": "Karur Vysya Bank", "file": "logos/KVB.jpg"},
    {"name": "Yes Bank", "file": "logos/Yes Bank.jpg"},
    {"name": "IDFC First Bank", "file": "logos/IDFC First Bank.jpg"},
    {"name": "Bandhan Bank", "file": "logos/Bandhan Bank.jpg"},
    {"name": "Kotak Mahindra Bank", "file": "logos/KMB.jpg"},
    {"name": "South Indian Bank", "file": "logos/South Indian Bank.jpg"},
    {"name": "Central Bank of India", "file": "logos/Central Bank of India.jpg"},
    {"name": "Indian Overseas Bank", "file": "logos/Indian Overseas Bank.jpg"},
    {"name": "Bank of India", "file": "logos/Bank of India.jpg"},
    {"name": "UCO Bank", "file": "logos/UCO Bank.jpg"},
    {"name": "City Union Bank", "file": "logos/City Union Bank.jpg"},
    {"name": "Deutsche Bank", "file": "logos/Deutsche Bank.jpg"},
    {"name": "Equitas Bank", "file": "logos/Equitas Bank.jpg"},
    {"name": "IDBI Bank", "file": "logos/IDBI Bank.jpg"},
    {"name": "The Hongkong and Shanghai Banking Corporation", "file": "logos/HSBC.jpg"},
    {"name": "Tamilnad Mercantile Bank", "file": "logos/Tamilnad Mercantile Bank.jpg"},
    {"name": "Karnataka Bank", "file": "logos/Karnataka Bank.jpg"},
    {"name": "CSB Bank", "file": "logos/CSB Bank.jpg"},
    {"name": "Punjab National Bank", "file": "logos/Punjab National Bank.jpg"},
    {"name": "Federal Bank", "file": "logos/Federal Bank.jpg"},
]

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
    except:
        return "0"

@st.dialog("Select Bank", width="medium")
def bank_selection_dialog():
    st.write("### 🏦 Select Bank")
    cols = st.columns(7, gap="small")
    for i, bank in enumerate(BANKS):
        with cols[i % 7]:
            if os.path.exists(bank['file']):
                st.image(bank['file'])
            else:
                st.caption(bank['name'])
            if st.button("Select", key=f"btn_{i}"):
                st.session_state.selected_bank = bank['name']
                st.rerun()

@st.dialog("Edit Amount")
def edit_amount_dialog(index):
    rec = st.session_state.all_receipts[index]
    current_val = rec['amount'].replace(",", "")
    new_amt_str = st.text_input("Enter New Amount ", value=current_val)

    if st.button("Save Changes"):
        try:
            new_amt = int(new_amt_str)
            ind_amt = format_indian_currency(new_amt)
            new_words = num2words(new_amt, lang='en_IN').replace(",", "").replace(" And ", " and ").title().replace(" And ", " and ")
            st.session_state.all_receipts[index]['amount'] = ind_amt
            st.session_state.all_receipts[index]['words'] = new_words
            st.rerun()
        except ValueError:
            st.error("Please enter a valid whole number.")

# --- INITIALIZATION ---
if 'all_receipts' not in st.session_state: st.session_state.all_receipts = []
if 'locked' not in st.session_state: st.session_state.locked = False
if 'selected_bank' not in st.session_state: st.session_state.selected_bank = ""
if 'show_batch' not in st.session_state: st.session_state.show_batch = False
if 'is_period' not in st.session_state: st.session_state.is_period = False
if 'consumer_key' not in st.session_state: st.session_state.consumer_key = 0
if 'temp_instruments' not in st.session_state: st.session_state.temp_instruments = []

with st.sidebar:
    st.header("⚙️ Configuration")
    s_challan = st.text_input("Starting Challan", disabled=st.session_state.locked)
    s_pdate = st.date_input("Challan Date", disabled=st.session_state.locked)

    # --- VALIDATION ---
    if s_challan and not s_challan.isdigit():
        st.error("Starting Challan must contain numbers only.")

    st.divider()
    TEMPLATE_NAME = "Test.docx"
    template_bytes = None

    if os.path.exists(TEMPLATE_NAME):
        st.success("✅ Challan Template Loaded")
        with open(TEMPLATE_NAME, "rb") as f:
            template_bytes = f.read()
    else:
        st.error(f"❌ {TEMPLATE_NAME} missing!")

    data_file = st.file_uploader("Upload Master Data (.xlsx)", type=["xlsx"])

    if not st.session_state.locked:
        if st.button("Confirm Setup", type="primary"):
            if not s_challan or not s_challan.isdigit():
                st.error("Enter valid numeric Starting Challan.")
            elif not template_bytes:
                st.error("Template not loaded.")
            elif not data_file:
                st.error("Upload Master Data.")
            else:
                st.session_state.locked = True
                st.session_state.start_no = int(s_challan)
                st.session_state.formatted_pdate = s_pdate.strftime("%d.%m.%Y")
                st.rerun()
    else:
        if st.button("Reset Session"):
            st.session_state.locked = False
            st.session_state.all_receipts = []
            st.rerun()

# =============================
# EXISTING LOGIC CONTINUES
# =============================

if st.session_state.locked:

    curr_count = len(st.session_state.all_receipts)
    next_no = st.session_state.start_no + curr_count

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("First Challan", st.session_state.start_no)
    m2.metric("Current No.", next_no)
    m3.metric("Date", st.session_state.formatted_pdate)
    m4.metric("Entered", curr_count)

    try:
        df = pd.read_excel(data_file, sheet_name="BILL")
    except:
        st.error("Sheet 'BILL' not found.")
        st.stop()

    st.divider()

    has_active_instruments = len(st.session_state.temp_instruments) > 0

    col_t1, col_t2 = st.columns([0.2, 0.8])
    with col_t1:
        toggle_label = "Single Month Mode" if not st.session_state.is_period else "Period Mode"
        if st.button(toggle_label, disabled=has_active_instruments):
            st.session_state.is_period = not st.session_state.is_period
            st.rerun()

    month_list = ["January","February","March","April","May","June","July","August","September","October","November","December"]
    month_abbr = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
    year_options = [2026, 2025]

    if not st.session_state.is_period:
        c1, c2 = st.columns(2)
        with c1:
            sel_month = st.selectbox("Select Month", options=month_list, disabled=has_active_instruments)
        with c2:
            sel_year = st.selectbox("Select Year", options=year_options, index=0, disabled=has_active_instruments)

        display_month_text = f"{sel_month} - {sel_year}"
        target_months = [(sel_month, sel_year)]

    else:
        c1, c2, c3, c4 = st.columns(4)
        with c1: f_month = st.selectbox("From Month", options=month_list, disabled=has_active_instruments)
        with c2: f_year = st.selectbox("From Year", options=year_options, index=0, disabled=has_active_instruments)
        with c3: t_month = st.selectbox("To Month", options=month_list, disabled=has_active_instruments)
        with c4: t_year = st.selectbox("To Year", options=year_options, index=0, disabled=has_active_instruments)

        start_date = datetime(f_year, month_list.index(f_month)+1, 1)
        end_date = datetime(t_year, month_list.index(t_month)+1, 1)

        target_months = []

        if start_date <= end_date:
            curr = start_date
            while curr <= end_date:
                target_months.append((month_list[curr.month-1], curr.year))
                curr = datetime(curr.year+1,1,1) if curr.month==12 else datetime(curr.year,curr.month+1,1)
        else:
            st.error("'From' date must be before 'To' date.")

        if not target_months:
            st.warning("Selected Month-Year range is empty.")

    search_num = st.text_input(
        "Enter Consumer Number",
        max_chars=3,
        key=f"consumer_{st.session_state.consumer_key}",
        disabled=has_active_instruments
    )

    if search_num and not re.match(r"^\d*$", search_num):
        st.error("Consumer Number must contain numbers only.")

    elif search_num and len(search_num)==3 and re.match(r"^\d{3}$", search_num):

        result = df[df['Consumer Number'].astype(str).str.zfill(3)==search_num]

        if result.empty:
            st.error("Consumer not found in Master Data.")

        else:
            row = result.iloc[0]
            total_amt = 0
            month_found = False

            for m, y in target_months:
                t_abbr = f"{month_abbr[month_list.index(m)]}-{str(y)[2:]}"
                t_col = next((col for col in df.columns if str(col).strip()==t_abbr or
                             (isinstance(col,(datetime,pd.Timestamp)) and col.month==month_list.index(m)+1 and col.year==y)),None)

                if t_col is not None:
                    month_found = True
                    total_amt += row[t_col] if not pd.isna(row[t_col]) else 0

            if not month_found:
                st.error("Selected Month-Year column not found in Master Data.")

            elif total_amt <= 0:
                st.warning("Amount is zero for selected Month-Year.")

            else:
                st.success(f"**Found:** {row['Name']} | **Total Amt:** ₹{format_indian_currency(total_amt)}")

# --- REMAINING ORIGINAL CODE CONTINUES EXACTLY AS YOUR VERSION ---
# (No logic changed below)
