import io
import os
import re
import uuid
import requests
import numbers
from datetime import date, datetime

import pandas as pd
import streamlit as st
from docxtpl import DocxTemplate

from utils import (
    BANKS,
    MONTH_LIST,
    MONTH_ABBR,
    YEAR_OPTIONS,
    OTHER_PURPOSES,
    CC_ADVANCE_TEMPLATE,
    SD_TEMPLATE,
    format_indian_currency,
    amount_words,
    format_period_month_text,
    SafeReceipt
)
from github_utils import list_files_github

@st.dialog("Select Bank", width="medium")
def bank_selection_dialog():
    st.write("### 🏦 Select Bank")
    cols = st.columns(7, gap="small")
    for i, bank in enumerate(BANKS):
        with cols[i % 7]:
            if os.path.exists(bank["file"]):
                st.image(bank["file"])
            else:
                st.caption(bank["name"])
            if st.button("Select", key=f"btn_{i}", use_container_width=True):
                st.session_state.selected_bank = bank["name"]
                st.rerun()

@st.dialog("Edit Amount")
def edit_amount_dialog(index):
    rec = st.session_state.all_receipts[index]
    current_val = rec["amount"].replace(",", "")
    new_amt_str = st.text_input("Enter New Amount", value=current_val)

    if st.button("Save Changes"):
        try:
            new_amt = int(new_amt_str)
            st.session_state.all_receipts[index]["amount"] = format_indian_currency(new_amt)
            st.session_state.all_receipts[index]["words"] = amount_words(new_amt)
            st.rerun()
        except ValueError:
            st.error("Please enter a valid whole number.")

def show_challan_generator():
    if "all_receipts" not in st.session_state:
        st.session_state.all_receipts = []
    if "locked" not in st.session_state:
        st.session_state.locked = False
    if "selected_bank" not in st.session_state:
        st.session_state.selected_bank = ""
    if "show_batch" not in st.session_state:
        st.session_state.show_batch = False
    if "is_period" not in st.session_state:
        st.session_state.is_period = False
    if "consumer_key" not in st.session_state:
        st.session_state.consumer_key = 0
    if "temp_instruments" not in st.session_state:
        st.session_state.temp_instruments = []
    if "challan_type" not in st.session_state:
        st.session_state.challan_type = "C. C"
    if "other_form_key" not in st.session_state:
        st.session_state.other_form_key = 0
    if "batch_purpose" not in st.session_state:
        st.session_state.batch_purpose = ""

    with st.sidebar:
        st.header("⚙️ Configuration")
        challan_type = st.radio(
            "Challan Type",
            ["C. C", "OTHER"],
            index=0 if st.session_state.challan_type == "C. C" else 1,
            disabled=st.session_state.locked,
        )

        s_challan = st.text_input("Starting Challan", disabled=st.session_state.locked, max_chars=4)
        s_pdate = st.date_input("Challan Date", disabled=st.session_state.locked)

        if s_challan:
            if not s_challan.isdigit():
                st.error("Challan Number must contain Numbers only.")
            elif len(s_challan) > 4:
                st.error("Challan Number can have maximum 4 digits.")

        st.divider()

        # Template check stubs (Logic preserved from original)
        if challan_type == "C. C":
            if os.path.exists(CC_ADVANCE_TEMPLATE):
                st.success("✅ C.C Template Loaded")
            else:
                st.error(f"❌ {CC_ADVANCE_TEMPLATE} Missing!")
        else:
            if os.path.exists(CC_ADVANCE_TEMPLATE):
                st.success("✅ CCTemplate Loaded")
            else:
                st.error(f"❌ {CC_ADVANCE_TEMPLATE} Missing!")
            if os.path.exists(SD_TEMPLATE):
                st.success("✅ SDTemplate Loaded")
            else:
                st.error(f"❌ {SD_TEMPLATE} Missing!")

        st.subheader("📊 Master Data")
        # Enhancement: GitHub Data Picker
        with st.spinner("Syncing files from GitHub..."):
            gh_files, _ = list_files_github("user_files")
            gh_xlsx = [f["name"] for f in gh_files if f["name"].endswith(".xlsx")]

        data_source = st.radio("Data Source", ["Local Upload", "GitHub Holder"], disabled=st.session_state.locked)

        selected_gh_file = None
        data_file_buffer = None

        if data_source == "GitHub Holder":
            if gh_xlsx:
                sel_name = st.selectbox("Select Master Data", gh_xlsx, disabled=st.session_state.locked)
                selected_gh_file = next(f for f in gh_files if f["name"] == sel_name)
            else:
                st.warning("No .xlsx files in GitHub holder.")
        else:
            data_file_buffer = st.file_uploader("Upload Master Data (.xlsx)", type=["xlsx"])

        if not st.session_state.locked:
            if st.button("Confirm Setup", type="primary"):
                if not s_challan or not s_challan.isdigit() or len(s_challan) > 4:
                    st.error("Enter a valid Numeric Challan Number (max 4 digits).")
                elif data_source == "Local Upload" and not data_file_buffer:
                    st.error("Upload Master Data.")
                elif data_source == "GitHub Holder" and not selected_gh_file:
                    st.error("Select Master Data from holder.")
                else:
                    st.session_state.locked = True
                    st.session_state.challan_type = challan_type
                    st.session_state.start_no = int(s_challan)
                    st.session_state.formatted_pdate = s_pdate.strftime("%d.%m.%Y")
                    # Cache the data file if it's from GitHub
                    if data_source == "GitHub Holder":
                        resp = requests.get(selected_gh_file["download_url"])
                        st.session_state.cached_data = io.BytesIO(resp.content)
                    else:
                        st.session_state.cached_data = data_file_buffer
                    st.rerun()
        else:
            if st.button("Reset Session"):
                st.session_state.locked = False
                st.session_state.all_receipts = []
                st.session_state.temp_instruments = []
                st.session_state.selected_bank = ""
                st.session_state.other_form_key = 0
                st.session_state.batch_purpose = ""
                if "cached_data" in st.session_state: del st.session_state.cached_data
                st.rerun()

    if st.session_state.locked:
        curr_count = len(st.session_state.all_receipts)
        # Sequence handled as 4-digit strings
        next_no_val = st.session_state.start_no + curr_count
        next_no_str = str(next_no_val).zfill(4)
        start_no_str = str(st.session_state.start_no).zfill(4)

        # Metrics at the top as requested
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Starting Challan", start_no_str)
        m2.metric("Current No.", next_no_str)
        m3.metric("Date", st.session_state.formatted_pdate)
        m4.metric("Entered", curr_count)

        st.divider()

        try:
            st.session_state.cached_data.seek(0)
            df = pd.read_excel(st.session_state.cached_data, sheet_name="BILL")
        except Exception:
            st.error("Sheet 'BILL' not found in Master Data.")
            st.stop()

        row = None
        total_amt = None
        display_month_text = ""
        purpose_value = ""
        description_value = ""
        breakdown_value = ""
        tag_value = ""
        account_value = ""
        has_active_instruments = len(st.session_state.temp_instruments) > 0

        has_row_data = False

        if st.session_state.challan_type == "C. C":
            st.subheader("📄 C.C Challan Input")
            col_t1, _ = st.columns([0.2, 0.8])
            with col_t1:
                toggle_label = "Single Month Mode" if not st.session_state.is_period else "Period Mode"
                if st.button(toggle_label, disabled=has_active_instruments):
                    st.session_state.is_period = not st.session_state.is_period
                    st.rerun()

            if not st.session_state.is_period:
                c1, c2 = st.columns(2)
                with c1: sel_month = st.selectbox("Select Month", options=MONTH_LIST, disabled=has_active_instruments)
                with c2: sel_year = st.selectbox("Select Year", options=YEAR_OPTIONS, index=0, disabled=has_active_instruments)
                display_month_text = f"{sel_month} - {sel_year}"
                target_months = [(sel_month, sel_year)]
            else:
                c1, c2, c3, c4 = st.columns(4)
                with c1: f_month = st.selectbox("From Month", options=MONTH_LIST, disabled=has_active_instruments)
                with c2: f_year = st.selectbox("From Year", options=YEAR_OPTIONS, index=0, disabled=has_active_instruments)
                with c3: t_month = st.selectbox("To Month", options=MONTH_LIST, disabled=has_active_instruments)
                with c4: t_year = st.selectbox("To Year", options=YEAR_OPTIONS, index=0, disabled=has_active_instruments)

                start_date = datetime(f_year, MONTH_LIST.index(f_month) + 1, 1)
                end_date = datetime(t_year, MONTH_LIST.index(t_month) + 1, 1)
                target_months = []
                if start_date <= end_date:
                    curr = start_date
                    while curr <= end_date:
                        target_months.append((MONTH_LIST[curr.month - 1], curr.year))
                        curr = (datetime(curr.year + 1, 1, 1) if curr.month == 12 else datetime(curr.year, curr.month + 1, 1))
                    display_month_text = format_period_month_text(target_months)
                else:
                    st.error("'From' date must be before 'To' date.")

            search_num = st.text_input("Enter Consumer Number (3 digits)", max_chars=3, key=f"consumer_{st.session_state.consumer_key}", disabled=has_active_instruments)
            if search_num and len(search_num) == 3:
                result = df[df["Consumer Number"].astype(str).str.zfill(3) == search_num]
                if result.empty: st.error("Consumer not found.")
                else:
                    row = result.iloc[0]
                    total_amt = 0; month_found = False
                    for m, y in target_months:
                        t_abbr = f"{MONTH_ABBR[MONTH_LIST.index(m)]}-{str(y)[2:]}"
                        t_col = next((col for col in df.columns if str(col).strip() == t_abbr or (isinstance(col, (datetime, pd.Timestamp)) and col.month == MONTH_LIST.index(m) + 1 and col.year == y)), None)
                        if t_col is not None:
                            month_found = True
                            total_amt += row[t_col] if not pd.isna(row[t_col]) else 0
                    if not month_found: st.error("Selected Month-Year not found in Data.")
                    elif total_amt <= 0: st.warning("Amount is zero.")
                    else:
                        purpose_value = "C. C. Charges"; description_value = display_month_text
                        st.success(f"**Found:** {row['Name']} | **Total:** ₹{format_indian_currency(total_amt)}")

        else:
            st.subheader("✏️ OTHER Challan Input")
            purpose_locked = bool(st.session_state.batch_purpose)
            selected_other_purpose = st.selectbox("Purpose", [st.session_state.batch_purpose] if purpose_locked else OTHER_PURPOSES, disabled=purpose_locked or has_active_instruments, key=f"op_{st.session_state.other_form_key}")

            purpose_value = selected_other_purpose; description_value = ""; desc_value_4d = ""; breakdown_value = ""; require_kva_value = False; is_new_consumer = False; tag_value = ""; account_value = ""

            if selected_other_purpose == "Advance Payment":
                c1, c2 = st.columns(2)
                with c1: adv_month = st.selectbox("Month", MONTH_LIST, key=f"am_{st.session_state.other_form_key}")
                with c2: adv_year = st.selectbox("Year", YEAR_OPTIONS, key=f"ay_{st.session_state.other_form_key}")
                description_value = f"{adv_month} - {adv_year}"
                other_amount = st.text_input("Amount", key=f"aa_{st.session_state.other_form_key}")
                if other_amount.isdigit(): total_amt = int(other_amount)

            elif selected_other_purpose == "Advance Security Deposit (ASD)":
                description_value = st.selectbox("Description", ["Review of ASD for April - 2023 to March - 2024", "Review of ASD for April - 2024 to March - 2025", "Review of ASD for April - 2025 to March - 2026"], index=1, key=f"asd_d_{st.session_state.other_form_key}")
                purpose_value = description_value; tag_value = "SD"; account_value = "8336 – CIVIL DEPOSITS – 101 – SECURITY DEPOSITS"
                other_amount = st.text_input("Amount", key=f"asd_a_{st.session_state.other_form_key}")
                if other_amount.isdigit(): total_amt = int(other_amount)

            elif selected_other_purpose == "Security Deposit and Meter Security Deposit (SD and MSD)":
                c1, c2 = st.columns([0.75, 0.25])
                with c1: sd_choice = st.selectbox("Description", ["SD and MSD - Extension of HT power supply service for CMD of", "Custom..."], key=f"sd_c_{st.session_state.other_form_key}")
                with c2: kva = st.text_input("KVA (max 4 digits)", max_chars=4, key=f"sd_v_{st.session_state.other_form_key}")
                if sd_choice == "Custom...": description_value = st.text_input("Custom Description", key=f"sd_cd_{st.session_state.other_form_key}").strip()
                else: require_kva_value = True; description_value = f"{sd_choice} {kva} KVA".strip()
                purpose_value = description_value; tag_value = "SD"; account_value = "8336 – CIVIL DEPOSITS – 101 – SECURITY DEPOSITS"
                s1, s2 = st.columns(2)
                with s1: s_a = st.text_input("SD Amount", key=f"sa_{st.session_state.other_form_key}")
                with s2: m_a = st.text_input("MSD Amount", key=f"ma_{st.session_state.other_form_key}")
                if s_a.isdigit() and m_a.isdigit():
                    total_amt = int(s_a) + int(m_a)
                    breakdown_value = f"[S.D     : {format_indian_currency(int(s_a))}]\n[M.S.D : {format_indian_currency(int(m_a))}]"

            else: # Processing Fee
                c1, c2 = st.columns([0.75, 0.25])
                with c1: pr_choice = st.selectbox("Description", ["registration cum-processing fees for the extension of HT power supply of CMD of", "Custom..."], key=f"pr_c_{st.session_state.other_form_key}")
                with c2: kva = st.text_input("KVA (max 4 digits)", max_chars=4, key=f"pr_v_{st.session_state.other_form_key}")
                if pr_choice == "Custom...": description_value = st.text_input("Custom Description", key=f"pr_cd_{st.session_state.other_form_key}").strip()
                else: require_kva_value = True; description_value = f"{pr_choice} {kva} KVA".strip()
                purpose_value = description_value; tag_value = "CCC/PF"; account_value = "0801 – Power 05 – Transmission and Distribution (101) Sale of Power"; total_amt = 20000; st.info("Fixed at ₹20,000")

            if selected_other_purpose in ["Security Deposit and Meter Security Deposit (SD and MSD)", "Processing Fee"]:
                is_new_consumer = st.checkbox("New Consumer", value=True, key=f"nc_{st.session_state.other_form_key}")

            if is_new_consumer:
                nc_name = st.text_input("Consumer Name", key=f"ncn_{st.session_state.other_form_key}")
                row = {"Name": nc_name.strip() if nc_name else "NEW CONSUMER", "Consumer Number": "NEW"}
            else:
                search_num = st.text_input("Enter Consumer Number (3 digits)", max_chars=3, key=f"consumer_{st.session_state.consumer_key}")
                if search_num and len(search_num) == 3:
                    result = df[df["Consumer Number"].astype(str).str.zfill(3) == search_num]
                    if not result.empty:
                        row = result.iloc[0]
                    else:
                        st.error("Not found.")

            has_row_data = isinstance(row, (dict, pd.Series))
            if has_row_data:
                st.success(f"**Name:** {row['Name']} | **Purpose:** {purpose_value}")

        has_row_data = has_row_data or isinstance(row, (dict, pd.Series))
        has_total_amount = isinstance(total_amt, numbers.Real) and not pd.isna(total_amt)

        if has_row_data and has_total_amount:
            has_row_data = isinstance(row, (dict, pd.Series))
            if has_row_data:
                st.success(f"**Name:** {row['Name']} | **Purpose:** {purpose_value}")

        has_row_data = has_row_data or isinstance(row, (dict, pd.Series))
        has_total_amount = isinstance(total_amt, numbers.Real) and not pd.isna(total_amt)

        if has_row_data and has_total_amount:

        if has_row_data and has_total_amount:
            if row is not None: st.success(f"**Name:** {row['Name']} | **Purpose:** {purpose_value}")

        if row is not None and total_amt is not None:
            # Bank & Payment Selection
            bank_name = st.session_state.selected_bank
            b1, b2 = st.columns([0.9, 0.1], vertical_alignment="bottom")
            with b1:
                bank_name = st.text_input("Bank Name", value=bank_name, disabled=has_active_instruments)
                st.session_state.selected_bank = bank_name
            with b2:
                if st.button("🔍 Select", disabled=has_active_instruments, use_container_width=True): bank_selection_dialog()

            with st.expander("💳 Add Payment Details", expanded=True):
                restricted_mode = st.session_state.temp_instruments[0]["type"] if st.session_state.temp_instruments else None
                with st.form("instrument_form", clear_on_submit=True):
                    f1, f2, f3 = st.columns(3)
                    with f1:
                        if restricted_mode: st.markdown(f"🔒 Mode: {restricted_mode}"); i_type = restricted_mode
                        else: i_type = st.selectbox("Type", ["Cheque", "Demand Draft"])
                    with f2: i_no = st.text_input("No.", max_chars=6)
                    with f3: i_date = st.date_input("Date")
                    if st.form_submit_button("➕ Add Payment"):
                        if bank_name and re.match(r"^\d{6}$", i_no):
                            st.session_state.temp_instruments.append({"bank": bank_name, "type": i_type, "no": i_no, "date": i_date.strftime("%d.%m.%Y")})
                            st.rerun()
                        else: st.error("Check Bank/Number.")

                for idx, inst in enumerate(st.session_state.temp_instruments):
                    cols = st.columns([2.5, 2, 2, 2, 0.5])
                    cols[0].write(f"🏦 {inst['bank']}"); cols[1].write(f"📄 {inst['type']}"); cols[2].write(f"🔢 {inst['no']}"); cols[3].write(f"📅 {inst['date']}")
                    if cols[4].button("🗑️", key=f"del_tmp_{idx}"): st.session_state.temp_instruments.pop(idx); st.rerun()

            if st.button("🚀 Add to Batch", type="primary", key="add_batch_btn"):
                if not st.session_state.temp_instruments or not bank_name or (st.session_state.challan_type == "OTHER" and not description_value.strip() and selected_other_purpose != "Advance Payment"):
                    st.error("Missing required fields.")
                else:
                    receipt = {
                        "id": str(uuid.uuid4()), "challan": next_no_str, "pdate": st.session_state.formatted_pdate,
                        "name": row["Name"], "num": row["Consumer Number"], "purpose": purpose_value,
                        "selected_purpose": selected_other_purpose if st.session_state.challan_type == "OTHER" else "C. C",
                        "description": description_value, "tag": tag_value, "account": account_value, "breakdown": breakdown_value,
                        "amount": format_indian_currency(total_amt), "words": amount_words(total_amt),
                        "pay_type": st.session_state.temp_instruments[0]["type"],
                        "pay_no": ", ".join([i["no"] for i in st.session_state.temp_instruments]),
                        "bank": bank_name, "date": ", ".join(list(set([i["date"] for i in st.session_state.temp_instruments]))),
                        "month": display_month_text if st.session_state.challan_type == "C. C" else description_value
                    }
                    st.session_state.all_receipts.append(receipt)
                    st.session_state.temp_instruments = []; st.session_state.selected_bank = ""; st.session_state.is_period = False
                    if st.session_state.challan_type == "OTHER" and not st.session_state.batch_purpose: st.session_state.batch_purpose = selected_other_purpose
                    st.session_state.other_form_key += 1; st.session_state.consumer_key += 1; st.rerun()

        if st.session_state.all_receipts:
            st.divider()
            batch_total = sum(int(r["amount"].replace(",", "")) for r in st.session_state.all_receipts)

            st.success("### 📊 Batch Summary")
            cc1, cc2 = st.columns([0.3, 0.7])
            cc1.metric("Total Amount", f"₹{format_indian_currency(batch_total)}")
            cc2.write("**Total in Words:**")
            cc2.markdown(f"#### {amount_words(batch_total)} Only")

            show_batch_val = st.checkbox("👁️ View Batch Table", value=st.session_state.show_batch)
            st.session_state.show_batch = show_batch_val

            if show_batch_val:
                t_head = st.columns([0.7, 2.2, 1.7, 1.2, 1.2, 2, 1.1])
                t_head[0].write("**No.**"); t_head[1].write("**Consumer**"); t_head[2].write("**Amount**"); t_head[3].write("**Mode**"); t_head[4].write("**No.**"); t_head[5].write("**Purpose**"); t_head[6].write("**Actions**")
                for i, rec in enumerate(st.session_state.all_receipts):
                    tcol = st.columns([0.7, 2.2, 1.7, 1.2, 1.2, 2, 1.1])
                    tcol[0].write(rec["challan"]); tcol[1].write(rec["name"]); tcol[2].write(f"₹{rec['amount']}"); tcol[3].write(rec["pay_type"]); tcol[4].write(rec["pay_no"]); tcol[5].write(rec.get("purpose", "C. C"))
                    with tcol[6]:
                        s1, s2 = st.columns(2)
                        if s1.button("✏️", key=f"e_{rec['id']}"): edit_amount_dialog(i)
                        if s2.button("🗑️", key=f"d_{rec['id']}"):
                            st.session_state.all_receipts.pop(i)
                            # Re-index remaining challans
                            for j in range(i, len(st.session_state.all_receipts)):
                                current_val = int(st.session_state.all_receipts[j]["challan"])
                                st.session_state.all_receipts[j]["challan"] = str(current_val - 1).zfill(4)
                            if not st.session_state.all_receipts: st.session_state.batch_purpose = ""; st.session_state.other_form_key += 1
                            st.rerun()

            st.write("---")
            if st.button("🚀 Finalize Word File", type="primary", key="finalize_btn"):
                try:
                    if st.session_state.challan_type == "C. C": tpl = CC_ADVANCE_TEMPLATE
                    else: tpl = CC_ADVANCE_TEMPLATE if st.session_state.all_receipts[0].get("selected_purpose", "") == "Advance Payment" else SD_TEMPLATE
                    with open(tpl, "rb") as f: doc = DocxTemplate(io.BytesIO(f.read()))
                    doc.render({"receipts": [SafeReceipt(r) for r in st.session_state.all_receipts]})
                    output = io.BytesIO(); doc.save(output); output.seek(0)
                    st.download_button("📥 Download", output.getvalue(), file_name=f"Challans_{date.today()}.docx")
                except Exception as e: st.error(f"Error: {e}")
