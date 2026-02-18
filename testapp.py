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
    width: 65px !important;
    height: 65px !important;
    object-fit: contain !important;
    border-radius: 5px;
    border: 1px solid #eee;
    display: block;
    margin-left: auto;
    margin-right: auto;
}
</style>
""", unsafe_allow_html=True)

# --- BANK LOGOS ---
BANKS = [
    {"name": "State Bank of India", "file": "logos/SBI.jpg"},
    {"name": "HDFC Bank", "file": "logos/HDFC.jpg"},
    {"name": "ICICI Bank", "file": "logos/ICICI Bank.jpg"},
    {"name": "Axis Bank", "file": "logos/Axis Bank.jpg"},
]

def format_indian_currency(number):
    try:
        main = str(int(float(number)))
        if len(main) <= 3:
            return main
        last_three = main[-3:]
        remaining = main[:-3]
        res = ""
        while len(remaining) > 2:
            res = "," + remaining[-2:] + res
            remaining = remaining[:-2]
        if remaining:
            res = remaining + res
        return f"{res},{last_three}"
    except:
        return "0"

# --- INITIALIZATION ---
if 'all_receipts' not in st.session_state:
    st.session_state.all_receipts = []
if 'locked' not in st.session_state:
    st.session_state.locked = False
if 'selected_bank' not in st.session_state:
    st.session_state.selected_bank = ""
if 'show_batch' not in st.session_state:
    st.session_state.show_batch = False
if 'is_period' not in st.session_state:
    st.session_state.is_period = False
if 'consumer_key' not in st.session_state:
    st.session_state.consumer_key = 0
if 'temp_instruments' not in st.session_state:
    st.session_state.temp_instruments = []

# --- SIDEBAR ---
with st.sidebar:
    st.header("⚙️ Configuration")

    s_challan = st.text_input("Starting Challan", disabled=st.session_state.locked)
    if s_challan and not s_challan.isdigit():
        st.error("Starting Challan must be numeric only.")

    s_pdate = st.date_input("Challan Date", disabled=st.session_state.locked)

    TEMPLATE_NAME = "Test.docx"
    template_bytes = None

    if os.path.exists(TEMPLATE_NAME):
        with open(TEMPLATE_NAME, "rb") as f:
            template_bytes = f.read()
        st.success("✅ Template Loaded")
    else:
        st.error("Template Missing")

    data_file = st.file_uploader("Upload Master Data", type=["xlsx"])

    if not st.session_state.locked:
        if st.button("Confirm Setup"):
            if not s_challan or not s_challan.isdigit():
                st.error("Enter valid numeric Starting Challan.")
            elif not data_file:
                st.error("Upload Master Data.")
            else:
                st.session_state.locked = True
                st.session_state.start_no = int(s_challan)
                st.session_state.formatted_pdate = s_pdate.strftime("%d.%m.%Y")
                st.rerun()

# --- MAIN ---
if st.session_state.locked:

    df = pd.read_excel(data_file, sheet_name="BILL")

    month_list = ["January","February","March","April","May","June",
                  "July","August","September","October","November","December"]

    month_abbr = ["Jan","Feb","Mar","Apr","May","Jun",
                  "Jul","Aug","Sep","Oct","Nov","Dec"]

    year_options = [2026, 2025]

    # ----- MODE TOGGLE -----
    if st.button("Toggle Month/Period Mode"):
        st.session_state.is_period = not st.session_state.is_period
        st.rerun()

    if not st.session_state.is_period:
        c1, c2 = st.columns(2)
        with c1:
            sel_month = st.selectbox("Select Month", month_list)
        with c2:
            sel_year = st.selectbox("Select Year", year_options)
        target_months = [(sel_month, sel_year)]
        display_month_text = f"{sel_month} - {sel_year}"

    else:
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            f_month = st.selectbox("From Month", month_list)
        with c2:
            f_year = st.selectbox("From Year", year_options)
        with c3:
            t_month = st.selectbox("To Month", month_list)
        with c4:
            t_year = st.selectbox("To Year", year_options)

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

        display_month_text = f"{f_month}-{f_year} to {t_month}-{t_year}"

    # ----- CONSUMER -----
    search_num = st.text_input(
        "Enter Consumer Number",
        max_chars=3,
        key=f"consumer_{st.session_state.consumer_key}"
    )

    if search_num:
        if not search_num.isdigit():
            st.error("Consumer number must be numeric only.")
        elif len(search_num) != 3:
            st.error("Consumer number must be exactly 3 digits.")

    # ----- PAYMENT ENTRY -----
    with st.form("instrument_form"):
        c1, c2, c3 = st.columns(3)

        with c1:
            i_type = st.selectbox("Type", ["Cheque","Demand Draft"])

        with c2:
            i_no = st.text_input("Cheque/DD Number", max_chars=6)
            if i_no:
                if not i_no.isdigit():
                    st.error("Cheque/DD must be numeric only.")
                elif len(i_no) != 6:
                    st.error("Cheque/DD must be exactly 6 digits.")

        with c3:
            i_date = st.date_input("Date")

        if st.form_submit_button("Add Payment"):
            if not i_no.isdigit() or len(i_no) != 6:
                st.error("Cheque/DD must be 6 digit numeric value.")
            else:
                st.session_state.temp_instruments.append({
                    "type": i_type,
                    "no": i_no,
                    "date": i_date.strftime("%d.%m.%Y")
                })
                st.rerun()
    # -------------------------------
    # CONSUMER SEARCH & AMOUNT LOGIC
    # -------------------------------
    if search_num and search_num.isdigit() and len(search_num) == 3:

        result = df[df['Consumer Number'].astype(str).str.zfill(3) == search_num]

        if result.empty:
            st.error("Consumer not found in Master Data.")
        else:
            row = result.iloc[0]

            total_amt = 0
            month_found = False

            for m, y in target_months:
                t_abbr = f"{month_abbr[month_list.index(m)]}-{str(y)[2:]}"
                t_col = next(
                    (
                        col for col in df.columns
                        if str(col).strip() == t_abbr
                        or (
                            isinstance(col, (datetime, pd.Timestamp))
                            and col.month == month_list.index(m) + 1
                            and col.year == y
                        )
                    ),
                    None
                )

                if t_col is not None:
                    month_found = True
                    total_amt += row[t_col] if not pd.isna(row[t_col]) else 0

            if not month_found:
                st.error("Selected Month-Year not found in Master Data.")
            elif total_amt <= 0:
                st.warning("Amount is zero for selected Month-Year.")
            else:
                st.success(
                    f"**Found:** {row['Name']} | **Total Amt:** ₹{format_indian_currency(total_amt)}"
                )

                # -----------------------
                # BANK SELECTION
                # -----------------------
                b_col1, b_col2 = st.columns([0.9, 0.1])

                with b_col1:
                    bank_name = st.text_input(
                        "Bank Name",
                        value=st.session_state.selected_bank
                    )

                with b_col2:
                    if st.button("🔍 Select"):
                        bank_selection_dialog()

                # -----------------------
                # ADD TO BATCH
                # -----------------------
                curr_count = len(st.session_state.all_receipts)
                next_no = st.session_state.start_no + curr_count

                if st.button("🚀 Add to Batch", type="primary"):

                    if not st.session_state.temp_instruments:
                        st.error("Add at least one payment detail.")
                    else:
                        st.session_state.all_receipts.append({
                            'id': str(uuid.uuid4()),
                            'challan': next_no,
                            'pdate': st.session_state.formatted_pdate,
                            'name': row['Name'],
                            'num': row['Consumer Number'],
                            'month': display_month_text,
                            'amount': format_indian_currency(total_amt),
                            'words': num2words(total_amt, lang='en_IN').title(),
                            'pay_type': st.session_state.temp_instruments[0]['type'],
                            'pay_no': ", ".join(
                                [i['no'] for i in st.session_state.temp_instruments]
                            ),
                            'bank': bank_name,
                            'date': ", ".join(
                                list(set([i['date'] for i in st.session_state.temp_instruments]))
                            )
                        })

                        st.session_state.temp_instruments = []
                        st.session_state.selected_bank = ""
                        st.session_state.is_period = False
                        st.session_state.consumer_key += 1

                        st.rerun()

    # -------------------------------
    # BATCH TABLE
    # -------------------------------
    if st.session_state.all_receipts:

        st.divider()

        if st.checkbox("👁️ View Batch Table", value=st.session_state.show_batch):
            st.session_state.show_batch = True

            t_head = st.columns([0.7, 2.5, 1.5, 1.2, 1.2, 1.8, 1.1])
            t_head[0].write("**No.**")
            t_head[1].write("**Consumer**")
            t_head[2].write("**Amount**")
            t_head[3].write("**Mode**")
            t_head[4].write("**No.**")
            t_head[5].write("**Bank**")
            t_head[6].write("**Actions**")

            for i, rec in enumerate(st.session_state.all_receipts):

                tcol = st.columns([0.7, 2.5, 1.5, 1.2, 1.2, 1.8, 1.1])

                tcol[0].write(rec['challan'])
                tcol[1].write(rec['name'])
                tcol[2].write(f"₹{rec['amount']}")
                tcol[3].write(rec['pay_type'])
                tcol[4].write(rec['pay_no'])
                tcol[5].write(rec['bank'])

                with tcol[6]:
                    s1, s2 = st.columns(2)

                    if s1.button("✏️", key=f"e_{rec['id']}"):
                        edit_amount_dialog(i)

                    if s2.button("🗑️", key=f"d_{rec['id']}"):
                        st.session_state.all_receipts.pop(i)

                        for j in range(i, len(st.session_state.all_receipts)):
                            st.session_state.all_receipts[j]['challan'] -= 1

                        st.rerun()

        # -------------------------------
        # FINALIZE WORD FILE
        # -------------------------------
        if st.button("🚀 Finalize Word File", type="primary"):

            doc = DocxTemplate(io.BytesIO(template_bytes))
            doc.render({'receipts': st.session_state.all_receipts})

            output = io.BytesIO()
            doc.save(output)

            st.download_button(
                "📥 Download",
                output.getvalue(),
                file_name=f"Challans_{date.today()}.docx"
            )
