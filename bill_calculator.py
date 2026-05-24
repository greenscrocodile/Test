import io
import re

import pandas as pd
import requests
import streamlit as st

from github_utils import get_github_config, list_files_github


def _find_file_meta(files, name_without_ext):
    for item in files:
        if item["name"].lower() == f"{name_without_ext.lower()}.xlsx":
            return item
    return None


def _load_master_from_github(file_meta):
    response = requests.get(file_meta["download_url"], timeout=30)
    response.raise_for_status()
    return pd.read_excel(io.BytesIO(response.content))


def _value_from_row(row, key, default="-"):
    return str(row.get(key, default)) if pd.notna(row.get(key, None)) else default

def show_bill_calculator():
    st.title("🧮 Bill Collector")
    st.write("---")

    mode = st.sidebar.radio(
        "Calculator Type",
        ["Normal Bill Calculator", "BPSC Calculator"],
    )

    if mode == "BPSC Calculator":
        st.info("BPSC calculator setup will be added next.")
        return

    st.subheader("Normal Bill Calculator")

    config = get_github_config()
    if not config:
        st.error("GitHub is not configured. Please set GITHUB_TOKEN and GITHUB_REPO in Streamlit secrets.")
        return

    with st.spinner("Loading master files from GitHub..."):
        files, error = list_files_github("user_files")

    if error:
        st.error(f"Unable to load master files: {error}")
        return

    namemast_meta = _find_file_meta(files, "NAMEMAST")
    billmast_meta = _find_file_meta(files, "BILLMAST")

    if not namemast_meta or not billmast_meta:
        st.error("Required files missing in user_files/: NAMEMAST.xlsx and BILLMAST.xlsx")
        return

    try:
        df_name = _load_master_from_github(namemast_meta)
        df_bill = _load_master_from_github(billmast_meta)
    except Exception as exc:
        st.error(f"Failed to open master files: {exc}")
        return

    st.sidebar.markdown("### Consumer Lookup")
    consumer_no = st.sidebar.text_input("Consumer No.", max_chars=3)

    if consumer_no and not re.match(r"^\d{0,3}$", consumer_no):
        st.sidebar.error("Consumer No. must contain digits only.")

    is_valid_consumer = bool(re.match(r"^\d{3}$", consumer_no or ""))
    info = None

    if is_valid_consumer:
        name_row_df = df_name[df_name["CON_CODE"].astype(str).str.zfill(3) == consumer_no]
        bill_row_df = df_bill[df_bill["CON_CODE"].astype(str).str.zfill(3) == consumer_no]

        if name_row_df.empty:
            st.sidebar.error("Consumer not found in NAMEMAST.")
        elif bill_row_df.empty:
            st.sidebar.error("Consumer not found in BILLMAST.")
        else:
            name_row = name_row_df.iloc[0]
            bill_row = bill_row_df.iloc[0]
            info = {
                "consumer_no": consumer_no,
                "name": _value_from_row(name_row, "CON_NAME"),
                "priv": _value_from_row(name_row, "PRIV_CON"),
                "indl": _value_from_row(name_row, "INDLTYPE"),
                "sanct_md": _value_from_row(bill_row, "SANCT_MD"),
                "meter_type": _value_from_row(bill_row, "METER_TYPE"),
                "serv_cat": _value_from_row(bill_row, "SERV_CAT"),
            }

    st.sidebar.markdown("### Consumer Information")
    if info:
        st.sidebar.write(f"**Consumer No.:** {info['consumer_no']}")
        st.sidebar.write(f"**Name:** {info['name']}")
        st.sidebar.write(f"**Private/Government:** {info['priv']}")
        st.sidebar.write(f"**Industry/Commercial:** {info['indl']}")
        st.sidebar.write(f"**Sanction Demand:** {info['sanct_md']}")
        st.sidebar.write(f"**Meter Type:** {info['meter_type']}")
        st.sidebar.write(f"**Service Cat No.:** {info['serv_cat']}")
    else:
        st.sidebar.caption("Enter a valid 3-digit Consumer No. to fetch details.")

    ok_disabled = not (is_valid_consumer and info is not None)
    ok_clicked = st.sidebar.button("OK", type="primary", disabled=ok_disabled)

    if ok_clicked:
        st.success("Consumer data confirmed. Bill calculation flow will start next.")
        st.json(info)
    else:
        st.info("Fill Consumer No. and click OK to proceed.")
