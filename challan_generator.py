import io
import os
import re
import uuid
import requests
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
            st.error("Please enter a valid number.")

def show_challan_generator():
    if "locked" not in st.session_state:
        st.session_state.locked = False
    if "challan_type" not in st.session_state:
        st.session_state.challan_type = "C. C"
    if "all_receipts" not in st.session_state:
        st.session_state.all_receipts = []
    if "temp_instruments" not in st.session_state:
        st.session_state.temp_instruments = []
    if "selected_bank" not in st.session_state:
        st.session_state.selected_bank = ""
    if "show_batch" not in st.session_state:
        st.session_state.show_batch = False
    if "consumer_key" not in st.session_state:
        st.session_state.consumer_key = 0
    if "other_form_key" not in st.session_state:
        st.session_state.other_form_key = 0
    if "batch_purpose" not in st.session_state:
        st.session_state.batch_purpose = ""
    if "is_period" not in st.session_state:
        st.session_state.is_period = False
    if "active_cc_tpl" not in st.session_state:
        st.session_state.active_cc_tpl = CC_ADVANCE_TEMPLATE
    if "active_sd_tpl" not in st.session_state:
        st.session_state.active_sd_tpl = SD_TEMPLATE

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

        if s_challan and not s_challan.isdigit():
            st.error("Challan Number must contain Numbers only.")

        st.divider()

        # GitHub Template Selection
        st.subheader("📄 Dynamic Templates")
        with st.spinner("Syncing templates..."):
            gh_files, _ = list_files_github("user_files")
            gh_docx = [f["name"] for f in gh_files if f["name"].endswith(".docx")]

        if challan_type == "C. C":
            options = ["Default (CCTemplate.docx)"] + gh_docx
            sel_cc = st.selectbox("C.C Template", options, disabled=st.session_state.locked)
            if sel_cc == "Default (CCTemplate.docx)":
                st.session_state.active_cc_tpl = CC_ADVANCE_TEMPLATE
            else:
                st.session_state.active_cc_tpl = next(f["download_url"] for f in gh_files if f["name"] == sel_cc)

            if st.session_state.active_cc_tpl.startswith("http") or os.path.exists(st.session_state.active_cc_tpl):
                st.success("✅ C.C Template Ready")
            else:
                st.error("❌ C.C Template Missing")
        else:
            # OTHER type needs both
            options_cc = ["Default (CCTemplate.docx)"] + gh_docx
            options_sd = ["Default (SDTemplate.docx)"] + gh_docx

            sel_cc = st.selectbox("C.C Template (Advance)", options_cc, disabled=st.session_state.locked)
            sel_sd = st.selectbox("SD Template", options_sd, disabled=st.session_state.locked)

            if sel_cc == "Default (CCTemplate.docx)":
                st.session_state.active_cc_tpl = CC_ADVANCE_TEMPLATE
            else:
                st.session_state.active_cc_tpl = next(f["download_url"] for f in gh_files if f["name"] == sel_cc)

            if sel_sd == "Default (SDTemplate.docx)":
                st.session_state.active_sd_tpl = SD_TEMPLATE
            else:
                st.session_state.active_sd_tpl = next(f["download_url"] for f in gh_files if f["name"] == sel_sd)

            if st.session_state.active_cc_tpl.startswith("http") or os.path.exists(st.session_state.active_cc_tpl):
                st.success("✅ C.C Template Ready")
            if st.session_state.active_sd_tpl.startswith("http") or os.path.exists(st.session_state.active_sd_tpl):
                st.success("✅ SD Template Ready")

        st.divider()

        data_file = st.file_uploader("Upload Master Data (.xlsx)", type=["xlsx"])

        if not st.session_state.locked:
            if st.button("Confirm Setup", type="primary"):
                if not s_challan or not s_challan.isdigit():
                    st.error("Enter a valid Numeric Challan Number.")
                elif not data_file:
                    st.error("Upload Master Data.")
                else:
                    st.session_state.locked = True
                    st.session_state.challan_type = challan_type
                    st.session_state.start_no = int(s_challan)
                    st.session_state.formatted_pdate = s_pdate.strftime("%d.%m.%Y")
                    st.rerun()
        else:
            if st.button("Reset Session"):
                st.session_state.locked = False
                st.session_state.all_receipts = []
                st.session_state.temp_instruments = []
                st.session_state.selected_bank = ""
                st.session_state.other_form_key = 0
                st.session_state.batch_purpose = ""
                st.rerun()

    if st.session_state.locked:
        curr_count = len(st.session_state.all_receipts)
        next_val = st.session_state.start_no + curr_count
        next_no_str = str(next_val).zfill(4)
        start_no_str = str(st.session_state.start_no).zfill(4)

        if st.session_state.challan_type == "C. C":
            st.title("📄 C.C Challan Generator")
            st.info(f"Generating from Challan No: **{start_no_str}** | Date: **{st.session_state.formatted_pdate}**")

            df = pd.read_excel(data_file)
            search_term = st.text_input("Search Consumer (Name or Number)")

            if search_term:
                filtered_df = df[
                    df["Name"].str.contains(search_term, case=False, na=False) |
                    df["Consumer Number"].astype(str).str.contains(search_term, na=False)
                ]
            else:
                filtered_df = df.head(10)

            if not filtered_df.empty:
                selected_consumer = st.selectbox("Select Consumer", filtered_df["Name"] + " - " + filtered_df["Consumer Number"].astype(str))
                row = filtered_df[filtered_df["Name"] + " - " + filtered_df["Consumer Number"].astype(str) == selected_consumer].iloc[0]

                st.write("---")
                st.write(f"### Consumer: **{row['Name']}**")

                p1, p2 = st.columns(2)
                with p1:
                    is_period = st.checkbox("Multiple Months (Period)", value=st.session_state.is_period)
                    st.session_state.is_period = is_period

                if is_period:
                    st.write("**Select Period**")
                    pcol1, pcol2 = st.columns(2)
                    with pcol1:
                        start_m = st.selectbox("From Month", MONTH_LIST, index=0)
                        start_y = st.selectbox("From Year", YEAR_OPTIONS, index=1)
                    with pcol2:
                        end_m = st.selectbox("To Month", MONTH_LIST, index=0)
                        end_y = st.selectbox("To Year", YEAR_OPTIONS, index=1)

                    # Logic to generate display text
                    display_month_text = f"{start_m} {start_y} to {end_m} {end_y}"
                else:
                    c1, c2 = st.columns(2)
                    with c1:
                        target_m = st.selectbox("Month", MONTH_LIST, index=date.today().month - 1)
                    with c2:
                        target_y = st.selectbox("Year", YEAR_OPTIONS, index=1)
                    display_month_text = f"{target_m} {target_y}"

                total_amt = st.number_input("Amount (₹)", min_value=0, step=1)

                st.write("---")
                # Bank & Payment
                bank_name = st.session_state.selected_bank
                b1, b2 = st.columns([3, 1], vertical_alignment="bottom")
                with b1:
                    bank_name = st.text_input("Bank Name", value=bank_name)
                    st.session_state.selected_bank = bank_name
                with b2:
                    has_active_instruments = len(st.session_state.temp_instruments) > 0
                    if st.button("🔍 Select", disabled=has_active_instruments, use_container_width=True):
                        bank_selection_dialog()

                with st.expander("💳 Add Payment Details", expanded=True):
                    restricted_mode = None
                    if st.session_state.temp_instruments:
                        restricted_mode = st.session_state.temp_instruments[0]["type"]

                    with st.form("instrument_form", clear_on_submit=True):
                        f1, f2, f3 = st.columns(3)
                        with f1:
                            if restricted_mode:
                                st.markdown("🔒 Locked")
                                st.info(f"Mode: {restricted_mode}")
                                i_type = restricted_mode
                            else:
                                i_type = st.selectbox("Type", ["Cheque", "Demand Draft"])
                        with f2:
                            i_no = st.text_input("No.", max_chars=6)
                        with f3:
                            i_date = st.date_input("Date")

                        if st.form_submit_button("➕ Add Payment"):
                            if bank_name and re.match(r"^\d{6}$", i_no):
                                st.session_state.temp_instruments.append(
                                    {
                                        "bank": bank_name,
                                        "type": i_type,
                                        "no": i_no,
                                        "date": i_date.strftime("%d.%m.%Y"),
                                    }
                                )
                                st.rerun()
                            else:
                                st.error("Check Bank Name and Cheque/DD No.")

                    for idx, inst in enumerate(st.session_state.temp_instruments):
                        cols = st.columns([2.5, 2, 2, 2, 0.5])
                        cols[0].write(f"🏦 {inst['bank']}")
                        cols[1].write(f"📄 {inst['type']}")
                        cols[2].write(f"🔢 {inst['no']}")
                        cols[3].write(f"📅 {inst['date']}")
                        if cols[4].button("🗑️", key=f"del_tmp_{idx}"):
                            st.session_state.temp_instruments.pop(idx)
                            st.rerun()

                if st.button("🚀 Add to Batch", type="primary", key="add_batch_cc"):
                    if not st.session_state.temp_instruments:
                        st.error("Add at least One Payment Details.")
                    elif not bank_name:
                        st.error("Bank Name is required.")
                    elif total_amt == 0:
                        st.error("Amount must be greater than 0.")
                    else:
                        receipt = {
                            "id": str(uuid.uuid4()),
                            "challan": next_no_str,
                            "pdate": st.session_state.formatted_pdate,
                            "name": row["Name"],
                            "num": row["Consumer Number"],
                            "month": display_month_text,
                            "amount": format_indian_currency(total_amt),
                            "words": amount_words(total_amt),
                            "pay_type": st.session_state.temp_instruments[0]["type"],
                            "pay_no": ", ".join([i["no"] for i in st.session_state.temp_instruments]),
                            "bank": bank_name,
                            "date": ", ".join(list(set([i["date"] for i in st.session_state.temp_instruments]))),
                        }
                        st.session_state.all_receipts.append(receipt)
                        st.session_state.temp_instruments = []
                        st.session_state.selected_bank = ""
                        st.session_state.is_period = False
                        st.rerun()
            else:
                st.warning("No consumers found.")

        else:
            st.title("✏️ OTHER Challan Generator")
            st.info(f"Generating from Challan No: **{start_no_str}** | Date: **{st.session_state.formatted_pdate}**")

            # Logic for OTHER challan types (similar to C.C but with purpose selection)
            df = pd.read_excel(data_file)

            with st.container(border=True, key=f"consumer_box_{st.session_state.consumer_key}"):
                sc1, sc2 = st.columns([2, 1])
                with sc1:
                    search_term = st.text_input("Search Consumer", key=f"search_{st.session_state.consumer_key}")
                with sc2:
                    is_new_consumer = st.checkbox("New Consumer", key=f"new_c_{st.session_state.consumer_key}")

                row = None
                if is_new_consumer:
                    new_consumer_name = st.text_input("Consumer Name")
                    if new_consumer_name:
                        row = {"Name": new_consumer_name, "Consumer Number": "NEW"}
                else:
                    if search_term:
                        filtered_df = df[
                            df["Name"].str.contains(search_term, case=False, na=False) |
                            df["Consumer Number"].astype(str).str.contains(search_term, na=False)
                        ]
                    else:
                        filtered_df = df.head(5)

                    if not filtered_df.empty:
                        sel_text = st.selectbox("Select Consumer", filtered_df["Name"] + " - " + filtered_df["Consumer Number"].astype(str))
                        row = filtered_df[filtered_df["Name"] + " - " + filtered_df["Consumer Number"].astype(str) == sel_text].iloc[0]
                    else:
                        st.warning("No consumers found.")

            if row:
                with st.container(border=True, key=f"purpose_box_{st.session_state.other_form_key}"):
                    st.write("#### Purpose & Description")

                    # If batch has started, lock the purpose
                    default_purpose = st.session_state.batch_purpose if st.session_state.batch_purpose else OTHER_PURPOSES[0]
                    selected_other_purpose = st.selectbox("Select Purpose", OTHER_PURPOSES, index=OTHER_PURPOSES.index(default_purpose), disabled=bool(st.session_state.batch_purpose))

                    description_value = ""
                    purpose_value = selected_other_purpose
                    tag_value = ""
                    account_value = ""
                    breakdown_value = ""
                    total_amt = None

                    require_kva_value = selected_other_purpose in ["Advance Security Deposit (ASD)", "Security Deposit and Meter Security Deposit (SD and MSD)", "Processing Fee"]

                    o1, o2 = st.columns(2)
                    with o1:
                        if selected_other_purpose == "Advance Payment":
                            target_m = st.selectbox("Month", MONTH_LIST, index=date.today().month - 1)
                            target_y = st.selectbox("Year", YEAR_OPTIONS, index=1)
                            description_value = f"{target_m} {target_y}"
                            total_amt = st.number_input("Amount (₹)", min_value=0, step=1)

                        elif selected_other_purpose == "Advance Security Deposit (ASD)":
                            kva_val = st.text_input("KVA Value (1-4 digits)", max_chars=4)
                            desc_value_4d = kva_val.zfill(4) if kva_val else ""
                            description_value = f"{desc_value_4d} ASD"
                            total_amt = st.number_input("Amount (₹)", min_value=0, step=1)
                            purpose_value = "A. S. D"

                        elif selected_other_purpose == "Processing Fee":
                            kva_val = st.text_input("KVA Value (1-4 digits)", max_chars=4)
                            desc_value_4d = kva_val.zfill(4) if kva_val else ""
                            description_value = f"{desc_value_4d} P. F"
                            total_amt = st.number_input("Amount (₹)", min_value=0, step=1)
                            purpose_value = "P. F"
                            tag_value = " (REGISTRATION CUM PROCESSING FEE)"
                            account_value = "9/831"

                        elif selected_other_purpose == "Security Deposit and Meter Security Deposit (SD and MSD)":
                            kva_val = st.text_input("KVA Value (1-4 digits)", max_chars=4)
                            desc_value_4d = kva_val.zfill(4) if kva_val else ""
                            description_value = f"{desc_value_4d} SD & MSD"
                            purpose_value = "S. D & M. S. D"
                            sd_amt = st.number_input("SD Amount", min_value=0)
                            msd_amt = st.number_input("MSD Amount", min_value=0)
                            if sd_amt or msd_amt:
                                total_amt = sd_amt + msd_amt
                                breakdown_value = f"SD: {format_indian_currency(sd_amt)}, MSD: {format_indian_currency(msd_amt)}"

                # Bank & Payment (Same as C.C)
                bank_name = st.session_state.selected_bank
                b1, b2 = st.columns([3, 1], vertical_alignment="bottom")
                with b1:
                    bank_name = st.text_input("Bank Name", value=bank_name)
                    st.session_state.selected_bank = bank_name
                with b2:
                    has_active_instruments = len(st.session_state.temp_instruments) > 0
                    if st.button("🔍 Select", disabled=has_active_instruments, use_container_width=True):
                        bank_selection_dialog()

                with st.expander("💳 Add Payment Details", expanded=True):
                    restricted_mode = None
                    if st.session_state.temp_instruments:
                        restricted_mode = st.session_state.temp_instruments[0]["type"]

                    with st.form("instrument_form_other", clear_on_submit=True):
                        f1, f2, f3 = st.columns(3)
                        with f1:
                            if restricted_mode:
                                st.markdown("🔒 Locked")
                                st.info(f"Mode: {restricted_mode}")
                                i_type = restricted_mode
                            else:
                                i_type = st.selectbox("Type", ["Cheque", "Demand Draft"])
                        with f2:
                            i_no = st.text_input("No.", max_chars=6)
                        with f3:
                            i_date = st.date_input("Date")

                        if st.form_submit_button("➕ Add Payment"):
                            if bank_name and re.match(r"^\d{6}$", i_no):
                                st.session_state.temp_instruments.append(
                                    {
                                        "bank": bank_name,
                                        "type": i_type,
                                        "no": i_no,
                                        "date": i_date.strftime("%d.%m.%Y"),
                                    }
                                )
                                st.rerun()
                            else:
                                st.error("Check Bank Name and Cheque/DD No.")

                    for idx, inst in enumerate(st.session_state.temp_instruments):
                        cols = st.columns([2.5, 2, 2, 2, 0.5])
                        cols[0].write(f"🏦 {inst['bank']}")
                        cols[1].write(f"📄 {inst['type']}")
                        cols[2].write(f"🔢 {inst['no']}")
                        cols[3].write(f"📅 {inst['date']}")
                        if cols[4].button("🗑️", key=f"del_tmp_other_{idx}"):
                            st.session_state.temp_instruments.pop(idx)
                            st.rerun()

                if st.button("🚀 Add to Batch", type="primary", key="add_batch_other"):
                    if not st.session_state.temp_instruments:
                        st.error("Add at least One Payment Details.")
                    elif not bank_name:
                        st.error("Bank Name is required.")
                    elif st.session_state.challan_type == "OTHER" and not description_value.strip() and selected_other_purpose != "Advance Payment":
                        st.error("Description is required for selected purpose.")
                    elif total_amt is None or total_amt == 0:
                        st.error("Please enter a valid Amount.")
                    else:
                        receipt = {
                            "id": str(uuid.uuid4()),
                            "challan": next_no_str,
                            "pdate": st.session_state.formatted_pdate,
                            "name": row["Name"],
                            "num": row["Consumer Number"],
                            "purpose": purpose_value,
                            "selected_purpose": selected_other_purpose,
                            "description": description_value,
                            "tag": tag_value,
                            "account": account_value,
                            "breakdown": breakdown_value,
                            "amount": format_indian_currency(total_amt),
                            "words": amount_words(total_amt),
                            "pay_type": st.session_state.temp_instruments[0]["type"],
                            "pay_no": ", ".join([i["no"] for i in st.session_state.temp_instruments]),
                            "bank": bank_name,
                            "date": ", ".join(list(set([i["date"] for i in st.session_state.temp_instruments]))),
                            "month": description_value
                        }
                        st.session_state.all_receipts.append(receipt)
                        st.session_state.temp_instruments = []
                        st.session_state.selected_bank = ""
                        st.session_state.is_period = False
                        if not st.session_state.batch_purpose:
                            st.session_state.batch_purpose = selected_other_purpose
                        st.rerun()

        if st.session_state.all_receipts:
            st.divider()

            batch_total = sum(int(r["amount"].replace(",", "")) for r in st.session_state.all_receipts)
            f_total_amt = format_indian_currency(batch_total)
            f_total_words = amount_words(batch_total)

            show_batch_val = st.checkbox("👁️ View/Edit Batch Table", value=st.session_state.show_batch)
            st.session_state.show_batch = show_batch_val
            if show_batch_val:
                t_head = st.columns([0.7, 2.2, 1.7, 1.2, 1.2, 2, 1.1])
                t_head[0].write("**No.**")
                t_head[1].write("**Consumer**")
                t_head[2].write("**Amount**")
                t_head[3].write("**Mode**")
                t_head[4].write("**No.**")
                t_head[5].write("**Purpose**")
                t_head[6].write("**Actions**")

                for i, rec in enumerate(st.session_state.all_receipts):
                    tcol = st.columns([0.7, 2.2, 1.7, 1.2, 1.2, 2, 1.1])
                    tcol[0].write(rec["challan"])
                    tcol[1].write(rec["name"])
                    tcol[2].write(f"₹{rec['amount']}")
                    tcol[3].write(rec["pay_type"])
                    tcol[4].write(rec["pay_no"])
                    tcol[5].write(rec.get("purpose", "C. C"))
                    with tcol[6]:
                        s1, s2, s3 = st.columns([0.2, 1, 1])
                        with s2:
                            if st.button("✏️", key=f"e_{rec['id']}"):
                                edit_amount_dialog(i)
                        with s3:
                            if st.button("🗑️", key=f"d_{rec['id']}"):
                                st.session_state.all_receipts.pop(i)
                                # Re-calculate challan numbers for the rest of the batch
                                for j in range(i, len(st.session_state.all_receipts)):
                                    current_val = int(st.session_state.all_receipts[j]["challan"])
                                    st.session_state.all_receipts[j]["challan"] = str(current_val - 1).zfill(4)
                                if not st.session_state.all_receipts:
                                    st.session_state.batch_purpose = ""
                                st.rerun()

                st.write("---")
                # Unified Summary at the bottom of the table, only visible when table is visible
                st.success("### 📊 Batch Summary")
                cc1, cc2 = st.columns([0.3, 0.7])
                with cc1:
                    st.metric("Total Amount", f"₹{f_total_amt}")
                with cc2:
                    st.write("**Total in Words:**")
                    st.markdown(f"#### {f_total_words} Only")

            st.write("---")

            if st.button("🚀 Finalize Word File", type="primary"):
                # Use dynamic templates
                try:
                    cc_tpl_path = st.session_state.active_cc_tpl
                    sd_tpl_path = st.session_state.active_sd_tpl

                    if st.session_state.challan_type == "C. C":
                        active_path = cc_tpl_path
                    else:
                        first_selected_purpose = st.session_state.all_receipts[0].get("selected_purpose", "")
                        active_path = cc_tpl_path if first_selected_purpose == "Advance Payment" else sd_tpl_path

                    if active_path.startswith("http"):
                        resp = requests.get(active_path)
                        tpl_io = io.BytesIO(resp.content)
                    else:
                        with open(active_path, "rb") as f:
                            tpl_io = io.BytesIO(f.read())

                    doc = DocxTemplate(tpl_io)
                    safe_receipts = [SafeReceipt(r) for r in st.session_state.all_receipts]
                    doc.render({"receipts": safe_receipts})
                    output = io.BytesIO()
                    doc.save(output)
                    output.seek(0)
                    st.download_button(
                        "📥 Download",
                        output.getvalue(),
                        file_name=f"Challans_{date.today()}.docx",
                    )
                except Exception as e:
                    st.error(f"Error generating file: {e}")
