import streamlit as st
import pandas as pd
from docxtpl import DocxTemplate
from num2words import num2words
import io
from datetime import date, datetime
import uuid
import re
import os

# ---------------- APP CONFIG ----------------
st.set_page_config(page_title="Challan Master", layout="wide")

# ---------------- CSS ----------------
st.markdown("""
<style>
[data-testid="stVerticalBlock"] > div { gap: 0.4rem !important; }
.instrument-row {
    background-color: #f9f9f9;
    padding: 6px;
    border-radius: 6px;
    margin-bottom: 3px;
}
</style>
""", unsafe_allow_html=True)

# ---------------- BANK LIST ----------------
BANKS = [
    {"name": "State Bank of India", "file": "logos/SBI.jpg"},
    {"name": "HDFC Bank", "file": "logos/HDFC.jpg"},
    {"name": "ICICI Bank", "file": "logos/ICICI Bank.jpg"},
    {"name": "Axis Bank", "file": "logos/Axis Bank.jpg"},
    {"name": "Indian Bank", "file": "logos/Indian Bank.jpg"},
]

# ---------------- HELPERS ----------------
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

@st.cache_data
def load_master_data(file):
    return pd.read_excel(file, sheet_name="BILL")

# ---------------- SESSION INIT ----------------
defaults = {
    "all_receipts": [],
    "locked": False,
    "selected_bank": "",
    "temp_instruments": [],
    "consumer_key": 0,
}
for k,v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ---------------- SIDEBAR ----------------
with st.sidebar:
    st.header("⚙️ Configuration")

    s_challan = st.text_input("Starting Challan",
                              disabled=st.session_state.locked)
    s_pdate = st.date_input("Challan Date",
                            disabled=st.session_state.locked)

    TEMPLATE_NAME = "Test.docx"
    template_bytes = None

    if os.path.exists(TEMPLATE_NAME):
        with open(TEMPLATE_NAME, "rb") as f:
            template_bytes = f.read()
        st.success("Template Loaded")
    else:
        st.error("Template Missing")

    data_file = st.file_uploader("Upload Master Data", type=["xlsx"])

    if not st.session_state.locked:
        if st.button("Confirm Setup"):
            if s_challan and data_file:
                st.session_state.locked = True
                st.session_state.start_no = int(s_challan)
                st.session_state.formatted_pdate = s_pdate.strftime("%d.%m.%Y")
                st.rerun()
    else:
        if st.button("Reset Session"):
            st.session_state.clear()
            st.rerun()

# ---------------- MAIN APP ----------------
if st.session_state.locked:

    # ---------- LOAD DATA ----------
    df = load_master_data(data_file)

    # ---------- TOP METRICS ----------
    curr_count = len(st.session_state.all_receipts)
    next_no = st.session_state.start_no + curr_count

    m1,m2,m3,m4 = st.columns(4)
    m1.metric("First Challan", st.session_state.start_no)
    m2.metric("Current No.", next_no)
    m3.metric("Date", st.session_state.formatted_pdate)
    m4.metric("Entered", curr_count)

    st.divider()

    # ---------- LAYOUT SPLIT ----------
    left, right = st.columns([1.2,1])

    # ==================================================
    # LEFT SIDE (ENTRY)
    # ==================================================
    with left:

        st.subheader("Consumer Entry")

        search_num = st.text_input(
            "Consumer Number",
            key=f"consumer_{st.session_state.consumer_key}"
        )

        selected_row = None

        # -------- DYNAMIC SEARCH --------
        if search_num:
            filtered = df[
                df['Consumer Number']
                .astype(str)
                .str.contains(search_num)
            ].head(10)

            for i,row in filtered.iterrows():
                if st.button(
                    f"{str(row['Consumer Number']).zfill(3)} - {row['Name']}",
                    key=f"sug_{i}"
                ):
                    selected_row = row
                    st.session_state.selected_consumer = row

        if "selected_consumer" in st.session_state:
            row = st.session_state.selected_consumer
            st.success(f"{row['Name']} Selected")

            bank_name = st.text_input(
                "Bank Name",
                value=st.session_state.selected_bank
            )

            # -------- INSTRUMENT ENTRY --------
            with st.form("instrument_form", clear_on_submit=True):
                c1,c2,c3 = st.columns(3)
                with c1:
                    i_type = st.selectbox("Type",
                                          ["Cheque","Demand Draft"])
                with c2:
                    i_no = st.text_input("Number", max_chars=6)
                with c3:
                    i_date = st.date_input("Date")

                if st.form_submit_button("Add Payment"):
                    if re.match(r"^\d{6}$", i_no):
                        st.session_state.temp_instruments.append({
                            "type": i_type,
                            "no": i_no,
                            "date": i_date.strftime("%d.%m.%Y")
                        })
                        st.session_state.selected_bank = bank_name
                        st.rerun()

            # show instruments
            for idx,inst in enumerate(st.session_state.temp_instruments):
                cols = st.columns([3,2,2,1])
                cols[0].write(inst['type'])
                cols[1].write(inst['no'])
                cols[2].write(inst['date'])
                if cols[3].button("🗑️", key=f"tmp{idx}"):
                    st.session_state.temp_instruments.pop(idx)
                    st.rerun()

            if st.button("Add to Batch", type="primary"):
                if st.session_state.temp_instruments:

                    amount = 1000   # <-- your existing calculation logic

                    st.session_state.all_receipts.append({
                        "id": str(uuid.uuid4()),
                        "challan": next_no,
                        "name": row['Name'],
                        "amount": format_indian_currency(amount),
                        "pay_type": st.session_state.temp_instruments[0]['type'],
                        "pay_no": ", ".join([i['no']
                                             for i in st.session_state.temp_instruments]),
                        "bank": bank_name
                    })

                    st.session_state.temp_instruments = []
                    st.session_state.consumer_key += 1
                    del st.session_state["selected_consumer"]
                    st.rerun()

    # ==================================================
    # RIGHT SIDE (BATCH VIEW)
    # ==================================================
    with right:

        st.subheader("Batch Summary")

        total_amt = sum(
            int(r['amount'].replace(",",""))
            for r in st.session_state.all_receipts
        )

        st.metric("Total Challans",
                  len(st.session_state.all_receipts))
        st.metric("Total Amount",
                  f"₹{format_indian_currency(total_amt)}")

        st.divider()

        for i,rec in enumerate(st.session_state.all_receipts):
            cols = st.columns([1,3,2,1])
            cols[0].write(rec['challan'])
            cols[1].write(rec['name'])
            cols[2].write(f"₹{rec['amount']}")
            if cols[3].button("🗑️", key=f"del{i}"):
                st.session_state.all_receipts.pop(i)
                st.rerun()

    # ---------- FINALIZE ----------
    if st.session_state.all_receipts:
        st.divider()

        if st.button("Finalize Word File", type="primary"):
            doc = DocxTemplate(io.BytesIO(template_bytes))
            doc.render({
                "receipts": st.session_state.all_receipts
            })

            output = io.BytesIO()
            doc.save(output)

            st.download_button(
                "Download",
                output.getvalue(),
                file_name=f"Challans_{date.today()}.docx"
            )
