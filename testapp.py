
-import streamlit as st
+import io
+import os
+import re
+import uuid
+from datetime import date, datetime
+
 import pandas as pd
+import streamlit as st
 from docxtpl import DocxTemplate
 from num2words import num2words
-import io
-from datetime import date, datetime
-import uuid
-import re
-import os
 
 # --- APP CONFIGURATION ---
-st.set_page_config(page_title="Challan Master Pro", layout="wide")
+st.set_page_config(page_title="Challan Master", layout="wide")
 
-# (Keep your existing CSS here...)
-st.markdown("""
+# --- CUSTOM CSS ---
+st.markdown(
+    """
     <style>
     [data-testid="stVerticalBlock"] > div { gap: 1rem !important; }
     div[data-testid="column"] button { margin-top: 28px !important; }
-    .stMarkdown p { font-size: 14px !important; line-height: 1.6 !important; margin-bottom: 0px !important; }
+
+    [data-testid="stImage"] img {
+        width: 65px !important; height: 65px !important;
+        object-fit: contain !important; border-radius: 5px;
+        border: 1px solid #eee; display: block;
+        margin-left: auto; margin-right: auto;
+    }
+
+    .stMarkdown p {
+        font-size: 14px !important;
+        line-height: 1.6 !important;
+        margin-bottom: 0px !important;
+    }
+
+    .instrument-row {
+        background-color: #f9f9f9;
+        padding: 5px;
+        border-radius: 5px;
+        margin-bottom: 2px;
+    }
     </style>
-    """, unsafe_allow_html=True)
+    """,
+    unsafe_allow_html=True,
+)
 
-# --- CONFIGURATION DATA ---
+# --- BANK LOGOS CONFIGURATION ---
 BANKS = [
     {"name": "State Bank of India", "file": "logos/SBI.jpg"},
     {"name": "HDFC Bank", "file": "logos/HDFC.jpg"},
-    # ... (Keep your full bank list here)
+    {"name": "ICICI Bank", "file": "logos/ICICI Bank.jpg"},
+    {"name": "Axis Bank", "file": "logos/Axis Bank.jpg"},
+    {"name": "Indian Bank", "file": "logos/Indian Bank.jpg"},
+    {"name": "Canara Bank", "file": "logos/Canara.jpg"},
+    {"name": "Bank of Baroda", "file": "logos/Bank of Baroda.jpg"},
+    {"name": "Union Bank of India", "file": "logos/Union Bank of India.jpg"},
+    {"name": "Karur Vysya Bank", "file": "logos/KVB.jpg"},
+    {"name": "Yes Bank", "file": "logos/Yes Bank.jpg"},
+    {"name": "IDFC First Bank", "file": "logos/IDFC First Bank.jpg"},
+    {"name": "Bandhan Bank", "file": "logos/Bandhan Bank.jpg"},
+    {"name": "Kotak Mahindra Bank", "file": "logos/KMB.jpg"},
+    {"name": "South Indian Bank", "file": "logos/South Indian Bank.jpg"},
+    {"name": "Central Bank of India", "file": "logos/Central Bank of India.jpg"},
+    {"name": "Indian Overseas Bank", "file": "logos/Indian Overseas Bank.jpg"},
+    {"name": "Bank of India", "file": "logos/Bank of India.jpg"},
+    {"name": "UCO Bank", "file": "logos/UCO Bank.jpg"},
+    {"name": "City Union Bank", "file": "logos/City Union Bank.jpg"},
+    {"name": "Deutsche Bank", "file": "logos/Deutsche Bank.jpg"},
+    {"name": "Equitas Bank", "file": "logos/Equitas Bank.jpg"},
+    {"name": "IDBI Bank", "file": "logos/IDBI Bank.jpg"},
+    {
+        "name": "The Hongkong and Shanghai Banking Corporation",
+        "file": "logos/HSBC.jpg",
+    },
+    {
+        "name": "Tamilnad Mercantile Bank",
+        "file": "logos/Tamilnad Mercantile Bank.jpg",
+    },
+    {"name": "Karnataka Bank", "file": "logos/Karnataka Bank.jpg"},
+    {"name": "CSB Bank", "file": "logos/CSB Bank.jpg"},
+    {"name": "Punjab National Bank", "file": "logos/Punjab National Bank.jpg"},
+    {"name": "Federal Bank", "file": "logos/Federal Bank.jpg"},
+]
+
+CC_TEMPLATE = "Test.docx"
+OTHER_ADVANCE_TEMPLATE = "Other_Advance_Payment.docx"
+OTHER_SECONDARY_TEMPLATE = "Other_ASD_SDMSD_Processing.docx"
+
+OTHER_PURPOSES = [
+    "Advance Payment",
+    "Advance Security Deposit (ASD)",
+    "Security Deposit and Meter Security Deposit (SD and MSD)",
+    "Processing Fee",
+]
+
+MONTH_LIST = [
+    "January",
+    "February",
+    "March",
+    "April",
+    "May",
+    "June",
+    "July",
+    "August",
+    "September",
+    "October",
+    "November",
+    "December",
 ]
+MONTH_ABBR = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
+YEAR_OPTIONS = [2026, 2025]
 
-PURPOSE_MAP = {
-    "Advance Payment": ["Monthly Energy Advance", "Pre-paid Top-up"],
-    "Advance Security Deposit": ["Initial ASD", "Additional ASD"],
-    "Security Deposit": ["New Connection SD", "Load Enhancement SD"],
-    "Meter Security Deposit": ["Single Phase Meter", "Three Phase Meter", "CT Meter"],
-    "Processing Fee": ["Standard Registration Fee"]
-}
 
-# --- HELPER FUNCTIONS ---
 def format_indian_currency(number):
     try:
         main = str(int(float(number)))
-        if len(main) <= 3: return main
+        if len(main) <= 3:
+            return main
         last_three = main[-3:]
         remaining = main[:-3]
         res = ""
         while len(remaining) > 2:
             res = "," + remaining[-2:] + res
             remaining = remaining[:-2]
-        if remaining: res = remaining + res
+        if remaining:
+            res = remaining + res
         return f"{res},{last_three}"
-    except: return "0"
+    except Exception:
+        return "0"
+
+
+def amount_words(number):
+    return (
+        num2words(int(number), lang="en_IN")
+        .replace(",", "")
+        .replace(" And ", " and ")
+        .title()
+        .replace(" And ", " and ")
+    )
+
 
 @st.dialog("Select Bank", width="medium")
 def bank_selection_dialog():
     st.write("### 🏦 Select Bank")
     cols = st.columns(7, gap="small")
     for i, bank in enumerate(BANKS):
         with cols[i % 7]:
-            if os.path.exists(bank['file']): st.image(bank['file'])
-            else: st.caption(bank['name'])
+            if os.path.exists(bank["file"]):
+                st.image(bank["file"])
+            else:
+                st.caption(bank["name"])
             if st.button("Select", key=f"btn_{i}"):
-                st.session_state.selected_bank = bank['name']
+                st.session_state.selected_bank = bank["name"]
                 st.rerun()
 
-# --- INITIALIZATION ---
-if 'all_receipts' not in st.session_state: st.session_state.all_receipts = []
-if 'locked' not in st.session_state: st.session_state.locked = False
-if 'selected_bank' not in st.session_state: st.session_state.selected_bank = ""
-if 'consumer_key' not in st.session_state: st.session_state.consumer_key = 0
-if 'temp_instruments' not in st.session_state: st.session_state.temp_instruments = []
 
-# --- SIDEBAR ---
+@st.dialog("Edit Amount")
+def edit_amount_dialog(index):
+    rec = st.session_state.all_receipts[index]
+    current_val = rec["amount"].replace(",", "")
+    new_amt_str = st.text_input("Enter New Amount", value=current_val)
+
+    if st.button("Save Changes"):
+        try:
+            new_amt = int(new_amt_str)
+            st.session_state.all_receipts[index]["amount"] = format_indian_currency(new_amt)
+            st.session_state.all_receipts[index]["words"] = amount_words(new_amt)
+            st.rerun()
+        except ValueError:
+            st.error("Please enter a valid whole number.")
+
+
+if "all_receipts" not in st.session_state:
+    st.session_state.all_receipts = []
+if "locked" not in st.session_state:
+    st.session_state.locked = False
+if "selected_bank" not in st.session_state:
+    st.session_state.selected_bank = ""
+if "show_batch" not in st.session_state:
+    st.session_state.show_batch = False
+if "is_period" not in st.session_state:
+    st.session_state.is_period = False
+if "consumer_key" not in st.session_state:
+    st.session_state.consumer_key = 0
+if "temp_instruments" not in st.session_state:
+    st.session_state.temp_instruments = []
+if "challan_type" not in st.session_state:
+    st.session_state.challan_type = "C. C"
+
 with st.sidebar:
     st.header("⚙️ Configuration")
-    
-    # 1. NEW RADIO BUTTON
-    app_mode = st.radio("Challan Type", ["💠 C. C", "💠 OTHER"], disabled=st.session_state.locked)
-    
+    challan_type = st.radio(
+        "Challan Type",
+        ["C. C", "OTHER"],
+        index=0 if st.session_state.challan_type == "C. C" else 1,
+        disabled=st.session_state.locked,
+    )
+
     s_challan = st.text_input("Starting Challan", disabled=st.session_state.locked)
     s_pdate = st.date_input("Challan Date", disabled=st.session_state.locked)
 
+    if s_challan and not s_challan.isdigit():
+        st.error("Challan Number must contain Numbers only.")
+
     st.divider()
-    
-    # Master Data Upload
+
+    template_bytes = None
+    secondary_template_bytes = None
+
+    if challan_type == "C. C":
+        if os.path.exists(CC_TEMPLATE):
+            st.success("✅ C. C Template Loaded")
+            with open(CC_TEMPLATE, "rb") as f:
+                template_bytes = f.read()
+        else:
+            st.error(f"❌ {CC_TEMPLATE} Missing!")
+    else:
+        if os.path.exists(OTHER_ADVANCE_TEMPLATE):
+            st.success("✅ OTHER Advance Template Loaded")
+            with open(OTHER_ADVANCE_TEMPLATE, "rb") as f:
+                template_bytes = f.read()
+        else:
+            st.error(f"❌ {OTHER_ADVANCE_TEMPLATE} Missing!")
+
+        if os.path.exists(OTHER_SECONDARY_TEMPLATE):
+            st.success("✅ OTHER ASD/SDMSD/Processing Template Loaded")
+            with open(OTHER_SECONDARY_TEMPLATE, "rb") as f:
+                secondary_template_bytes = f.read()
+        else:
+            st.error(f"❌ {OTHER_SECONDARY_TEMPLATE} Missing!")
+
     data_file = st.file_uploader("Upload Master Data (.xlsx)", type=["xlsx"])
 
     if not st.session_state.locked:
         if st.button("Confirm Setup", type="primary"):
-            if not s_challan.isdigit(): st.error("Invalid Challan No.")
-            elif not data_file: st.error("Upload Master Data.")
+            if not s_challan or not s_challan.isdigit():
+                st.error("Enter a valid Numeric Challan Number.")
+            elif challan_type == "C. C" and not template_bytes:
+                st.error("C. C template not loaded.")
+            elif challan_type == "OTHER" and (not template_bytes or not secondary_template_bytes):
+                st.error("Load both OTHER templates.")
+            elif not data_file:
+                st.error("Upload Master Data.")
             else:
                 st.session_state.locked = True
-                st.session_state.app_mode = app_mode
+                st.session_state.challan_type = challan_type
                 st.session_state.start_no = int(s_challan)
                 st.session_state.formatted_pdate = s_pdate.strftime("%d.%m.%Y")
                 st.rerun()
     else:
-        st.info(f"Mode: {st.session_state.app_mode}")
         if st.button("Reset Session"):
             st.session_state.locked = False
             st.session_state.all_receipts = []
+            st.session_state.temp_instruments = []
+            st.session_state.selected_bank = ""
             st.rerun()
 
-# --- MAIN FLOW ---
 if st.session_state.locked:
     curr_count = len(st.session_state.all_receipts)
     next_no = st.session_state.start_no + curr_count
 
-    m1, m2, m3 = st.columns(3)
-    m1.metric("Current No.", next_no)
-    m2.metric("Date", st.session_state.formatted_pdate)
-    m3.metric("Entered", curr_count)
+    if st.session_state.challan_type == "C. C":
+        m1, m2, m3, m4 = st.columns(4)
+        m1.metric("First Challan", st.session_state.start_no)
+        m2.metric("Current No.", next_no)
+        m3.metric("Date", st.session_state.formatted_pdate)
+        m4.metric("Entered", curr_count)
+    else:
+        m1, m2 = st.columns(2)
+        m1.metric("Current No.", next_no)
+        m2.metric("Date", st.session_state.formatted_pdate)
 
     try:
         df = pd.read_excel(data_file, sheet_name="BILL")
-    except:
-        st.error("Sheet 'BILL' not found."); st.stop()
+    except Exception:
+        st.error("Sheet 'BILL' not found.")
+        st.stop()
 
     st.divider()
+
     has_active_instruments = len(st.session_state.temp_instruments) > 0
+    row = None
+    total_amt = None
+    display_month_text = ""
+    purpose_value = ""
+    description_value = ""
+
+    if st.session_state.challan_type == "C. C":
+        col_t1, _ = st.columns([0.2, 0.8])
+        with col_t1:
+            toggle_label = "Single Month Mode" if not st.session_state.is_period else "Period Mode"
+            if st.button(toggle_label, disabled=has_active_instruments):
+                st.session_state.is_period = not st.session_state.is_period
+                st.rerun()
+
+        if not st.session_state.is_period:
+            c1, c2 = st.columns(2)
+            with c1:
+                sel_month = st.selectbox(
+                    "Select Month", options=MONTH_LIST, disabled=has_active_instruments
+                )
+            with c2:
+                sel_year = st.selectbox(
+                    "Select Year", options=YEAR_OPTIONS, index=0, disabled=has_active_instruments
+                )
+
+            display_month_text = f"{sel_month} - {sel_year}"
+            target_months = [(sel_month, sel_year)]
+        else:
+            c1, c2, c3, c4 = st.columns(4)
+            with c1:
+                f_month = st.selectbox("From Month", options=MONTH_LIST, disabled=has_active_instruments)
+            with c2:
+                f_year = st.selectbox(
+                    "From Year", options=YEAR_OPTIONS, index=0, disabled=has_active_instruments
+                )
+            with c3:
+                t_month = st.selectbox("To Month", options=MONTH_LIST, disabled=has_active_instruments)
+            with c4:
+                t_year = st.selectbox(
+                    "To Year", options=YEAR_OPTIONS, index=0, disabled=has_active_instruments
+                )
+
+            start_date = datetime(f_year, MONTH_LIST.index(f_month) + 1, 1)
+            end_date = datetime(t_year, MONTH_LIST.index(t_month) + 1, 1)
+
+            target_months = []
+
+            if start_date <= end_date:
+                curr = start_date
+                while curr <= end_date:
+                    target_months.append((MONTH_LIST[curr.month - 1], curr.year))
+                    curr = (
+                        datetime(curr.year + 1, 1, 1)
+                        if curr.month == 12
+                        else datetime(curr.year, curr.month + 1, 1)
+                    )
+                display_month_text = f"{f_month} {f_year} to {t_month} {t_year}"
+            else:
+                st.error("'From' date must be before 'To' date.")
+
+            if not target_months:
+                st.warning("Selected Month-Year range is empty.")
+
+        search_num = st.text_input(
+            "Enter Consumer Number",
+            max_chars=3,
+            key=f"consumer_{st.session_state.consumer_key}",
+            disabled=has_active_instruments,
+        )
+
+        if search_num and not re.match(r"^\d*$", search_num):
+            st.error("Consumer Number must contain numbers only.")
+        elif search_num and len(search_num) == 3 and re.match(r"^\d{3}$", search_num):
+            result = df[df["Consumer Number"].astype(str).str.zfill(3) == search_num]
+
+            if result.empty:
+                st.error("Consumer not found in Master Data.")
+            else:
+                row = result.iloc[0]
+                total_amt = 0
+                month_found = False
+
+                for m, y in target_months:
+                    t_abbr = f"{MONTH_ABBR[MONTH_LIST.index(m)]}-{str(y)[2:]}"
+                    t_col = next(
+                        (
+                            col
+                            for col in df.columns
+                            if str(col).strip() == t_abbr
+                            or (
+                                isinstance(col, (datetime, pd.Timestamp))
+                                and col.month == MONTH_LIST.index(m) + 1
+                                and col.year == y
+                            )
+                        ),
+                        None,
+                    )
+
+                    if t_col is not None:
+                        month_found = True
+                        total_amt += row[t_col] if not pd.isna(row[t_col]) else 0
+
+                if not month_found:
+                    st.error("Selected Month-Year column not found in Master Data.")
+                elif total_amt <= 0:
+                    st.warning("Amount is zero for selected Month-Year.")
+                else:
+                    purpose_value = "C. C"
+                    description_value = display_month_text
+                    st.success(
+                        f"**Found:** {row['Name']} | **Total Amt:** ₹{format_indian_currency(total_amt)}"
+                    )
 
-    # ---------------------------
-    # FLOW A: C.C (Original)
-    # ---------------------------
-    if st.session_state.app_mode == "💠 C. C":
-        # ... (Insert your existing Month/Year selection and Total Amount calculation here)
-        # For brevity, assuming total_amt and display_month_text are calculated as per your old code
-        total_amt = 1000 # Placeholder for your existing logic
-        display_month_text = "Jan-2026" # Placeholder
-        purpose_val = "C.C. Charges"
-        desc_val = display_month_text
-
-    # ---------------------------
-    # FLOW B: OTHER (New)
-    # ---------------------------
     else:
-        c1, c2 = st.columns(2)
-        with c1:
-            purpose_val = st.selectbox("Purpose", options=list(PURPOSE_MAP.keys()))
-        with c2:
-            desc_val = st.selectbox("Description", options=PURPOSE_MAP[purpose_val])
-        
-        # Manual Amount Logic
-        if purpose_val == "Processing Fee":
+        purpose_value = st.selectbox("Purpose", OTHER_PURPOSES, disabled=has_active_instruments)
+
+        if purpose_value == "Advance Payment":
+            c1, c2 = st.columns(2)
+            with c1:
+                adv_month = st.selectbox("Month", MONTH_LIST, disabled=has_active_instruments)
+            with c2:
+                adv_year = st.selectbox(
+                    "Year", YEAR_OPTIONS, index=0, disabled=has_active_instruments
+                )
+            description_value = f"{adv_month} - {adv_year}"
+        elif purpose_value in [
+            "Advance Security Deposit (ASD)",
+            "Security Deposit and Meter Security Deposit (SD and MSD)",
+        ]:
+            description_value = st.text_input(
+                "Description",
+                placeholder="Enter purpose description",
+                disabled=has_active_instruments,
+            )
+        else:
+            description_value = ""
+
+        if purpose_value == "Processing Fee":
             total_amt = 20000
-            st.info("💰 Processing Fee is fixed at ₹20,000")
+            st.info("Processing Fee amount is fixed at ₹20,000")
         else:
-            total_amt = st.number_input("Enter Amount (₹)", min_value=1, step=1)
-
-    # ---------------------------
-    # COMMON CONSUMER SEARCH
-    # ---------------------------
-    search_num = st.text_input("Enter Consumer Number", max_chars=3, key=f"c_{st.session_state.consumer_key}")
-    
-    if search_num and len(search_num) == 3:
-        result = df[df['Consumer Number'].astype(str).str.zfill(3) == search_num]
-        
-        if not result.empty:
-            row = result.iloc[0]
-            st.success(f"**Target:** {row['Name']} | **Purpose:** {purpose_val}")
-            
-            # --- BANK & INSTRUMENTS (Your existing logic) ---
-            b_col1, b_col2 = st.columns([0.9, 0.1], vertical_alignment="bottom")
-            with b_col1: bank_name = st.text_input("Bank Name", value=st.session_state.selected_bank)
-            with b_col2: 
-                if st.button("🔍"): bank_selection_dialog()
-
-            # (Add Payment Details Form here - same as your old code)
-            # ...
-            
-            if st.button("🚀 Add to Batch", type="primary"):
-                if not st.session_state.temp_instruments: st.error("Add payment details first.")
-                else:
-                    st.session_state.all_receipts.append({
-                        'id': str(uuid.uuid4()), 
-                        'challan': next_no, 
-                        'pdate': st.session_state.formatted_pdate,
-                        'name': row['Name'], 
-                        'num': row['Consumer Number'],
-                        'purpose': purpose_val, # NEW FIELD
-                        'description': desc_val, # NEW FIELD
-                        'amount': format_indian_currency(total_amt),
-                        'words': num2words(total_amt, lang='en_IN').title(),
-                        'bank': bank_name,
-                        'pay_no': ", ".join([i['no'] for i in st.session_state.temp_instruments]),
-                        # ... other fields
-                    })
-                    st.session_state.temp_instruments = []; st.rerun()
-
-    # --- FINALIZATION ---
+            total_amt = st.number_input(
+                "Amount",
+                min_value=1,
+                step=1,
+                value=1,
+                disabled=has_active_instruments,
+            )
+
+        is_new_consumer = purpose_value == "Security Deposit and Meter Security Deposit (SD and MSD)"
+        if is_new_consumer:
+            search_num = st.text_input(
+                "Enter Consumer Number",
+                value="NEW",
+                disabled=True,
+                key=f"consumer_new_{st.session_state.consumer_key}",
+            )
+        else:
+            search_num = st.text_input(
+                "Enter Consumer Number",
+                max_chars=3,
+                key=f"consumer_{st.session_state.consumer_key}",
+                disabled=has_active_instruments,
+            )
+
+        if is_new_consumer:
+            row = {"Name": "NEW CONSUMER", "Consumer Number": "NEW"}
+        elif search_num and not re.match(r"^\d*$", search_num):
+            st.error("Consumer Number must contain numbers only.")
+        elif search_num and len(search_num) == 3 and re.match(r"^\d{3}$", search_num):
+            result = df[df["Consumer Number"].astype(str).str.zfill(3) == search_num]
+            if result.empty:
+                st.error("Consumer not found in Master Data.")
+            else:
+                row = result.iloc[0]
+
+        if row is not None:
+            st.success(f"**Found:** {row['Name']} | **Purpose:** {purpose_value}")
+
+    if row is not None and total_amt is not None:
+        b_col1, b_col2 = st.columns([0.9, 0.1], vertical_alignment="bottom")
+        with b_col1:
+            bank_name = st.text_input(
+                "Bank Name", value=st.session_state.selected_bank, disabled=has_active_instruments
+            )
+        with b_col2:
+            if st.button("🔍 Select", disabled=has_active_instruments):
+                bank_selection_dialog()
+
+        with st.expander("💳 Add Payment Details", expanded=True):
+            restricted_mode = None
+            if st.session_state.temp_instruments:
+                restricted_mode = st.session_state.temp_instruments[0]["type"]
+
+            with st.form("instrument_form", clear_on_submit=True):
+                f1, f2, f3 = st.columns(3)
+                with f1:
+                    if restricted_mode:
+                        st.markdown("🔒 Locked")
+                        st.info(f"Mode: {restricted_mode}")
+                        i_type = restricted_mode
+                    else:
+                        i_type = st.selectbox("Type", ["Cheque", "Demand Draft"])
+                with f2:
+                    i_no = st.text_input("No.", max_chars=6)
+                with f3:
+                    i_date = st.date_input("Date")
+
+                if st.form_submit_button("➕ Add Payment"):
+                    if bank_name and re.match(r"^\d{6}$", i_no):
+                        st.session_state.temp_instruments.append(
+                            {
+                                "bank": bank_name,
+                                "type": i_type,
+                                "no": i_no,
+                                "date": i_date.strftime("%d.%m.%Y"),
+                            }
+                        )
+                        st.rerun()
+                    else:
+                        st.error("Check Bank Name and Cheque/DD No.")
+
+            for idx, inst in enumerate(st.session_state.temp_instruments):
+                cols = st.columns([2.5, 2, 2, 2, 0.5])
+                cols[0].write(f"🏦 {inst['bank']}")
+                cols[1].write(f"📄 {inst['type']}")
+                cols[2].write(f"🔢 {inst['no']}")
+                cols[3].write(f"📅 {inst['date']}")
+                if cols[4].button("🗑️", key=f"del_tmp_{idx}"):
+                    st.session_state.temp_instruments.pop(idx)
+                    st.rerun()
+
+        if st.button("🚀 Add to Batch", type="primary"):
+            if not st.session_state.temp_instruments:
+                st.error("Add at least One Payment Details.")
+            elif not bank_name:
+                st.error("Bank Name is required.")
+            elif st.session_state.challan_type == "OTHER" and purpose_value in [
+                "Advance Security Deposit (ASD)",
+                "Security Deposit and Meter Security Deposit (SD and MSD)",
+            ] and not description_value.strip():
+                st.error("Description is required for selected purpose.")
+            else:
+                receipt = {
+                    "id": str(uuid.uuid4()),
+                    "challan": next_no,
+                    "pdate": st.session_state.formatted_pdate,
+                    "name": row["Name"],
+                    "num": row["Consumer Number"],
+                    "purpose": purpose_value,
+                    "description": description_value,
+                    "amount": format_indian_currency(total_amt),
+                    "words": amount_words(total_amt),
+                    "pay_type": st.session_state.temp_instruments[0]["type"],
+                    "pay_no": ", ".join([i["no"] for i in st.session_state.temp_instruments]),
+                    "bank": bank_name,
+                    "date": ", ".join(list(set([i["date"] for i in st.session_state.temp_instruments]))),
+                }
+                if st.session_state.challan_type == "C. C":
+                    receipt["month"] = display_month_text
+                st.session_state.all_receipts.append(receipt)
+                st.session_state.temp_instruments = []
+                st.session_state.selected_bank = ""
+                st.session_state.is_period = False
+                st.session_state.consumer_key += 1
+                st.rerun()
+
     if st.session_state.all_receipts:
-        if st.button("📥 Generate File"):
-            # Select template based on mode
-            tpl_path = "Test.docx" if st.session_state.app_mode == "💠 C. C" else "Other_Template.docx"
-            
-            if os.path.exists(tpl_path):
-                doc = DocxTemplate(tpl_path)
-                doc.render({'receipts': st.session_state.all_receipts})
-                output = io.BytesIO()
-                doc.save(output)
-                st.download_button("Download Now", output.getvalue(), file_name=f"Challans_{app_mode}.docx")
+        st.divider()
+        if st.checkbox("👁️ View Batch Table", value=st.session_state.show_batch):
+            st.session_state.show_batch = True
+            t_head = st.columns([0.7, 2.2, 1.7, 1.2, 1.2, 2, 1.1])
+            t_head[0].write("**No.**")
+            t_head[1].write("**Consumer**")
+            t_head[2].write("**Amount**")
+            t_head[3].write("**Mode**")
+            t_head[4].write("**No.**")
+            t_head[5].write("**Purpose**")
+            t_head[6].write("**Actions**")
+            for i, rec in enumerate(st.session_state.all_receipts):
+                tcol = st.columns([0.7, 2.2, 1.7, 1.2, 1.2, 2, 1.1])
+                tcol[0].write(rec["challan"])
+                tcol[1].write(rec["name"])
+                tcol[2].write(f"₹{rec['amount']}")
+                tcol[3].write(rec["pay_type"])
+                tcol[4].write(rec["pay_no"])
+                tcol[5].write(rec.get("purpose", "C. C"))
+                with tcol[6]:
+                    s1, s2 = st.columns(2)
+                    if s1.button("✏️", key=f"e_{rec['id']}"):
+                        edit_amount_dialog(i)
+                    if s2.button("🗑️", key=f"d_{rec['id']}"):
+                        st.session_state.all_receipts.pop(i)
+                        for j in range(i, len(st.session_state.all_receipts)):
+                            st.session_state.all_receipts[j]["challan"] -= 1
+                        st.rerun()
+
+        if st.button("🚀 Finalize Word File", type="primary"):
+            if st.session_state.challan_type == "C. C":
+                with open(CC_TEMPLATE, "rb") as f:
+                    doc = DocxTemplate(io.BytesIO(f.read()))
             else:
-                st.error(f"Template {tpl_path} not found.")
+                first_receipt_purpose = st.session_state.all_receipts[0].get("purpose", "")
+                tpl = (
+                    OTHER_ADVANCE_TEMPLATE
+                    if first_receipt_purpose == "Advance Payment"
+                    else OTHER_SECONDARY_TEMPLATE
+                )
+                if not os.path.exists(tpl):
+                    st.error(f"Template missing: {tpl}")
+                    st.stop()
+                with open(tpl, "rb") as f:
+                    doc = DocxTemplate(io.BytesIO(f.read()))
+
+            doc.render({"receipts": st.session_state.all_receipts})
+            output = io.BytesIO()
+            doc.save(output)
+            output.seek(0)
+            st.download_button(
+                "📥 Download",
+                output.getvalue(),
+                file_name=f"Challans_{date.today()}.docx",
+            )
