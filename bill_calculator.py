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


def _map_priv(value):
    mapping = {"P": "Private", "G": "Government"}
    return mapping.get(str(value).strip().upper(), str(value))


def _map_indl(value):
    mapping = {
        "I": "Industry",
        "C": "Commercial",
        "E": "EV Charging Station",
        "G": "Central Govt.",
    }
    return mapping.get(str(value).strip().upper(), str(value))


def _to_float(value):
    try:
        return float(value)
    except Exception:
        return None


def show_bill_calculator():
    st.title("🧮 Bill Collector")
    st.write("---")

    if "bill_collector_ok" not in st.session_state:
        st.session_state.bill_collector_ok = False
    if "bill_collector_consumer" not in st.session_state:
        st.session_state.bill_collector_consumer = None

    locked = st.session_state.bill_collector_ok

    mode = st.sidebar.radio(
        "Calculator Type",
        ["Normal Bill Calculator", "BPSC Calculator"],
        disabled=locked,
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
    readmast_meta = _find_file_meta(files, "READMAST")

    if not namemast_meta or not billmast_meta or not readmast_meta:
        st.error("Required files missing in user_files/: NAMEMAST.xlsx, BILLMAST.xlsx, READMAST.xlsx")
        return

    try:
        df_name = _load_master_from_github(namemast_meta)
        df_bill = _load_master_from_github(billmast_meta)
        df_read = _load_master_from_github(readmast_meta)
    except Exception as exc:
        st.error(f"Failed to open master files: {exc}")
        return

    st.sidebar.markdown("### Consumer Lookup")
    default_consumer = st.session_state.bill_collector_consumer or ""
    consumer_no = st.sidebar.text_input("Consumer No.", max_chars=3, value=default_consumer, disabled=locked)

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
                "priv": _map_priv(_value_from_row(name_row, "PRIV_CON")),
                "indl": _map_indl(_value_from_row(name_row, "INDLTYPE")),
                "sanct_md": _value_from_row(bill_row, "SANCT_MD"),
                "meter_type": _value_from_row(bill_row, "METER_TYPE"),
                "serv_cat": _value_from_row(bill_row, "SERV_CAT"),
            }

    st.sidebar.markdown("### Consumer Information")
    if info:
        st.sidebar.success(
            f"""
            {info['consumer_no']}  
            {info['name']}  
            {info['priv']} | {info['indl']}
            """
        )
        st.sidebar.markdown(
            f"""
            <div style="border:1px solid #86efac; background:#f0fdf4; border-radius:10px; padding:10px;">
                <b>Sanction Demand:</b> {info['sanct_md']}<br>
                <b>Meter Type:</b> {info['meter_type']}<br>
                <b>Service Cat No.:</b> {info['serv_cat']}
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.sidebar.caption("Enter a valid 3-digit Consumer No. to fetch details.")

    ok_disabled = locked or not (is_valid_consumer and info is not None)
    ok_clicked = st.sidebar.button("OK", type="primary", disabled=ok_disabled)
    reset_clicked = st.sidebar.button("Reset", type="secondary", disabled=not locked)

    if ok_clicked:
        st.session_state.bill_collector_ok = True
        st.session_state.bill_collector_consumer = info["consumer_no"]
        st.rerun()
    if reset_clicked:
        st.session_state.bill_collector_ok = False
        st.session_state.bill_collector_consumer = None
        st.rerun()

    if not st.session_state.bill_collector_ok or st.session_state.get("bill_collector_consumer") != (info["consumer_no"] if info else None):
        st.info("Fill Consumer No. and click OK to proceed.")
        return

    read_row_df = df_read[df_read["CON_CODE"].astype(str).str.zfill(3) == info["consumer_no"]]
    if read_row_df.empty:
        st.error("Consumer not found in READMAST.")
        return

    read_row = read_row_df.iloc[0]
    kwh_mf = _to_float(read_row.get("KWH_MF"))
    kwd_mf = _to_float(read_row.get("KWD_MF"))
    kvad_mf = _to_float(read_row.get("KVAD_MF"))

    if kwh_mf is None or kwd_mf is None or kvad_mf is None:
        st.error("MF values missing/invalid in READMAST.")
        return

    if not (kwh_mf == kwd_mf == kvad_mf):
        st.error("MF mismatch in READMAST: KWH_MF, KWD_MF, KVAD_MF should be same.")
        return

    mf_factor = kwh_mf
    st.success(f"Consumer Name: {info['name']}")

    st.subheader("KWH")
    kwh_cols = st.columns(5)
    prev_kwh = kwh_cols[0].text_input("Previous KWH", value="0", key="prev_kwh")
    pres_kwh = kwh_cols[1].text_input("Present KWH", value="0", key="pres_kwh")
    prev_kwh_num = _to_float(prev_kwh)
    pres_kwh_num = _to_float(pres_kwh)
    if prev_kwh_num is None or pres_kwh_num is None:
        st.error("KWH readings must be numeric.")
        return
    kwh_diff = pres_kwh_num - prev_kwh_num
    kwh_cols[2].number_input("KWH Difference", value=float(kwh_diff), disabled=True, key="kwh_diff")
    kwh_cols[3].number_input("MF factor", value=float(mf_factor), disabled=True, key="kwh_mf")
    kwh_cols[4].number_input("Consumption", value=float(kwh_diff * mf_factor), disabled=True, key="kwh_consumption")

    st.subheader("KVAH")
    kvah_cols = st.columns(5)
    prev_kvah = kvah_cols[0].text_input("Previous KVAH", value="0", key="prev_kvah")
    pres_kvah = kvah_cols[1].text_input("Present KVAH", value="0", key="pres_kvah")
    prev_kvah_num = _to_float(prev_kvah)
    pres_kvah_num = _to_float(pres_kvah)
    if prev_kvah_num is None or pres_kvah_num is None:
        st.error("KVAH readings must be numeric.")
        return
    kvah_diff = pres_kvah_num - prev_kvah_num
    kvah_cols[2].number_input("KVAH Difference", value=float(kvah_diff), disabled=True, key="kvah_diff")
    kvah_cols[3].number_input("MF factor", value=float(mf_factor), disabled=True, key="kvah_mf")
    kvah_cols[4].number_input("Consumption", value=float(kvah_diff * mf_factor), disabled=True, key="kvah_consumption")
