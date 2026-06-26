# ============================================================
# app.py
# AI List Cleanup Assistant — Streamlit UI
# ============================================================

import streamlit as st
import pandas as pd
import os
import json
from datetime import datetime

from utils.file_handler import load_csv_from_upload, save_cleaned_csv, save_json_report
from cleaners.email_cleaner import clean_emails
from cleaners.name_cleaner import clean_names
from cleaners.company_cleaner import clean_companies
from cleaners.title_cleaner import clean_titles
from cleaners.geo_cleaner import clean_geo
from cleaners.field_checker import check_required_fields
from detectors.duplicate_detector import detect_duplicates
from reporters.qa_report import build_qa_report
from reporters.pdf_generator import generate_pdf
from utils.logger import get_logger

logger = get_logger(__name__)

# --- Page Config ---
st.set_page_config(
    page_title="AI List Cleanup Assistant",
    page_icon="✅",
    layout="wide",
)

# --- Header ---
st.title("✅ AI List Cleanup Assistant")
st.caption("Marketing Operations — CSV QA & Cleanup Tool")
st.divider()

# --- Standard fields the app expects ---
STANDARD_FIELDS = [
    "Email",
    "First Name",
    "Last Name",
    "Company",
    "Job Title",
    "Country",
    "State",
]

def auto_match(file_columns: list, standard_fields: list) -> dict:
    """
    Tries to automatically match file columns to standard fields.
    Uses case-insensitive and partial matching.
    Returns a dict: {standard_field: matched_column or "-- Skip --"}
    """
    mapping = {}
    skip = "-- Skip --"

    for field in standard_fields:
        matched = skip
        for col in file_columns:
            if field.lower() == col.lower():
                matched = col
                break
        if matched == skip:
            for col in file_columns:
                if field.lower() in col.lower() or col.lower() in field.lower():
                    matched = col
                    break
        mapping[field] = matched

    return mapping


# --- File Upload ---
st.subheader("📁 Step 1: Upload Your CSV")
uploaded_file = st.file_uploader(
    "Drag and drop your CSV file here",
    type=["csv"],
    help="Supported format: CSV. Max recommended size: 50,000 rows."
)

if uploaded_file is not None:

    with st.spinner("Loading file..."):
        try:
            df_raw = load_csv_from_upload(uploaded_file)
        except Exception as e:
            st.error(f"Could not read file: {e}")
            st.stop()

    st.success(f"File loaded: **{uploaded_file.name}** — {len(df_raw):,} rows, {len(df_raw.columns)} columns")

    with st.expander("Preview Raw Data (first 10 rows)"):
        st.dataframe(df_raw.head(10), use_container_width=True)

    st.divider()

    # --- Column Mapping ---
    st.subheader("🗂 Step 2: Map Your Columns")
    st.caption("Match your file's columns to the standard fields the app expects. Select '-- Skip --' for fields not in your file.")

    file_columns = df_raw.columns.tolist()
    options = ["-- Skip --"] + file_columns
    auto_mapping = auto_match(file_columns, STANDARD_FIELDS)

    col1, col2 = st.columns(2)
    user_mapping = {}

    for i, field in enumerate(STANDARD_FIELDS):
        col = col1 if i % 2 == 0 else col2
        default = auto_mapping.get(field, "-- Skip --")
        default_index = options.index(default) if default in options else 0
        selected = col.selectbox(
            f"{field}",
            options=options,
            index=default_index,
            key=f"map_{field}"
        )
        user_mapping[field] = selected

    # Show mapping summary
    mapped = {k: v for k, v in user_mapping.items() if v != "-- Skip --"}
    skipped = [k for k, v in user_mapping.items() if v == "-- Skip --"]

    if mapped:
        st.success(f"✅ Mapped {len(mapped)} fields: {', '.join(mapped.keys())}")
    if skipped:
        st.info(f"⏭ Skipping: {', '.join(skipped)}")

    st.divider()

    # --- Run Cleanup ---
    st.subheader("🧹 Step 3: Run Cleanup")

    if st.button("▶ Run Full Cleanup & QA Analysis", type="primary", use_container_width=True):

        if not mapped:
            st.error("Please map at least one column before running.")
            st.stop()

        # Build a renamed DataFrame using the user's mapping
        rename_map = {v: k for k, v in mapped.items()}
        df = df_raw.rename(columns=rename_map).copy()

        # Keep unmapped columns too
        progress = st.progress(0, text="Starting...")

        try:
            progress.progress(10, text="Cleaning emails...")
            df = clean_emails(df)

            progress.progress(25, text="Cleaning names...")
            df = clean_names(df)

            progress.progress(40, text="Cleaning companies...")
            df = clean_companies(df)

            progress.progress(55, text="Cleaning job titles...")
            df = clean_titles(df)

            progress.progress(65, text="Normalizing countries and states...")
            df = clean_geo(df)

            progress.progress(75, text="Checking required fields...")
            df = check_required_fields(df)

            progress.progress(85, text="Detecting duplicates...")
            df = detect_duplicates(df)

            progress.progress(92, text="Building QA report...")
            report = build_qa_report(df)

            # --- Remove flagged records from cleaned output ---
            flag_cols = [c for c in df.columns if c.startswith("flag_") or c.startswith("email_flag_")]
            if flag_cols:
                clean_mask = ~df[flag_cols].any(axis=1)
                df_clean = df[clean_mask].copy()
            else:
                df_clean = df.copy()

            progress.progress(96, text="Saving outputs...")
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_dir = "outputs"

            cleaned_csv_path = save_cleaned_csv(df_clean, output_dir, f"cleaned_list_{timestamp}.csv")
            json_path = save_json_report(report, output_dir, f"qa_report_{timestamp}.json")
            pdf_path = os.path.join(output_dir, f"qa_report_{timestamp}.pdf")
            generate_pdf(report, pdf_path)

            progress.progress(100, text="Done!")
            st.session_state["report"] = report
            st.session_state["df"] = df
            st.session_state["cleaned_csv_path"] = cleaned_csv_path
            st.session_state["json_path"] = json_path
            st.session_state["pdf_path"] = pdf_path
            st.success("Cleanup complete!")

        except Exception as e:
            st.error(f"An error occurred during cleanup: {e}")
            logger.error(f"Cleanup pipeline error: {e}", exc_info=True)
            st.stop()

# --- Results ---
if "report" in st.session_state:
    report = st.session_state["report"]
    df = st.session_state["df"]
    summary = report["summary"]

    st.divider()
    st.subheader("📊 Step 4: Review QA Report")

    score = summary["quality_score"]
    risk = summary["risk_level"]
    risk_colors = {"Low": "🟢", "Medium": "🟡", "High": "🟠", "Critical": "🔴"}
    risk_icon = risk_colors.get(risk, "⚪")

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Records", f"{summary['total_records']:,}")
    col2.metric("Valid Records", f"{summary['valid_records']:,}")
    col3.metric("Quality Score", f"{score} / 100")
    col4.metric("Risk Level", f"{risk_icon} {risk}")

    st.divider()

    st.subheader("📧 Email Analysis")
    email = report["email"]
    e1, e2, e3, e4, e5 = st.columns(5)
    e1.metric("Blank",      email["blank"])
    e2.metric("Invalid",    email["invalid"])
    e3.metric("Duplicate",  email["duplicate"])
    e4.metric("Disposable", email["disposable"])
    e5.metric("Personal",   email["personal"])

    st.divider()

    st.subheader("🌍 Breakdowns")
    b1, b2, b3 = st.columns(3)

    with b1:
        st.markdown("**Top Countries**")
        if report["breakdowns"]["top_countries"]:
            st.dataframe(
                pd.DataFrame(report["breakdowns"]["top_countries"].items(), columns=["Country", "Count"]),
                use_container_width=True, hide_index=True
            )

    with b2:
        st.markdown("**Top Job Titles**")
        if report["breakdowns"]["top_titles"]:
            st.dataframe(
                pd.DataFrame(report["breakdowns"]["top_titles"].items(), columns=["Title", "Count"]),
                use_container_width=True, hide_index=True
            )

    with b3:
        st.markdown("**Top Companies**")
        if report["breakdowns"]["top_companies"]:
            st.dataframe(
                pd.DataFrame(report["breakdowns"]["top_companies"].items(), columns=["Company", "Count"]),
                use_container_width=True, hide_index=True
            )

    st.divider()

    st.subheader("🚩 Flagged Records")
    flag_cols = [c for c in df.columns if c.startswith("flag_") or c.startswith("email_flag_")]
    if flag_cols:
        any_flag = df[flag_cols].any(axis=1)
        flagged_df = df[any_flag]
        st.write(f"{len(flagged_df):,} records have at least one flag.")
        with st.expander("View Flagged Records"):
            st.dataframe(flagged_df, use_container_width=True)

    st.divider()

    st.subheader("⬇️ Step 5: Download Outputs")
    d1, d2, d3 = st.columns(3)

    with d1:
        with open(st.session_state["cleaned_csv_path"], "rb") as f:
            st.download_button(
                label="⬇️ Download Cleaned CSV",
                data=f,
                file_name="cleaned_list.csv",
                mime="text/csv",
                use_container_width=True,
            )

    with d2:
        with open(st.session_state["pdf_path"], "rb") as f:
            st.download_button(
                label="⬇️ Download QA Report PDF",
                data=f,
                file_name="qa_report.pdf",
                mime="application/pdf",
                use_container_width=True,
            )

    with d3:
        with open(st.session_state["json_path"], "rb") as f:
            st.download_button(
                label="⬇️ Download QA Report JSON",
                data=f,
                file_name="qa_report.json",
                mime="application/json",
                use_container_width=True,
            )

    st.divider()
    st.caption("AI List Cleanup Assistant — G2 Marketing Operations | Built by Spencer McKinney")
