# ============================================================
# detectors/duplicate_detector.py
# ============================================================

import pandas as pd
import yaml
from rapidfuzz import fuzz
from utils.logger import get_logger

logger = get_logger(__name__)


def load_config(config_path: str = "config/rules.yaml") -> dict:
    with open(config_path, "r") as f:
        return yaml.safe_load(f)


def normalize_for_matching(value: str) -> str:
    if not isinstance(value, str):
        return ""
    return value.strip().lower()


def detect_duplicates(df: pd.DataFrame, config_path: str = "config/rules.yaml") -> pd.DataFrame:
    config = load_config(config_path)
    dup_config = config.get("duplicates", {})

    check_email = dup_config.get("check_email", True)
    check_name_company = dup_config.get("check_company_and_name", True)
    check_email_company = dup_config.get("check_email_and_company", True)
    threshold = dup_config.get("fuzzy_match_threshold", 85)

    email_col = config.get("email", {}).get("column_name", "Email")
    first_col = config.get("names", {}).get("first_name_column", "First Name")
    last_col = config.get("names", {}).get("last_name_column", "Last Name")
    company_col = config.get("company", {}).get("column_name", "Company")

    df["dup_email"] = False
    df["dup_name_company"] = False
    df["dup_email_company"] = False

    if check_email and email_col in df.columns:
        logger.info("Checking for duplicate emails...")
        df["dup_email"] = df[email_col].duplicated(keep="first") & df[email_col].notna()
        logger.info(f"Duplicate emails found: {df['dup_email'].sum()}")

    if check_email_company and email_col in df.columns and company_col in df.columns:
        logger.info("Checking for duplicate email + company combinations...")
        combined = df[email_col].apply(normalize_for_matching) + "|" + \
                   df[company_col].apply(normalize_for_matching)
        df["dup_email_company"] = combined.duplicated(keep="first")
        logger.info(f"Duplicate email + company found: {df['dup_email_company'].sum()}")

    if check_name_company and first_col in df.columns and last_col in df.columns and company_col in df.columns:
        logger.info(f"Checking fuzzy duplicate name + company (threshold: {threshold})...")

        full_names = (
            df[first_col].apply(normalize_for_matching) + " " +
            df[last_col].apply(normalize_for_matching) + " " +
            df[company_col].apply(normalize_for_matching)
        ).tolist()

        fuzzy_flags = [False] * len(full_names)

        for i in range(len(full_names)):
            if fuzzy_flags[i]:
                continue
            for j in range(i + 1, len(full_names)):
                if fuzzy_flags[j]:
                    continue
                score = fuzz.ratio(full_names[i], full_names[j])
                if score >= threshold:
                    fuzzy_flags[j] = True

        df["dup_name_company"] = fuzzy_flags
        logger.info(f"Fuzzy duplicate name + company found: {df['dup_name_company'].sum()}")

    df["duplicate_reason"] = df.apply(
        lambda row: ", ".join(filter(None, [
            "duplicate email" if row["dup_email"] else "",
            "duplicate email+company" if row["dup_email_company"] else "",
            "fuzzy name+company match" if row["dup_name_company"] else "",
        ])), axis=1
    )

    df["flag_any_duplicate"] = (
        df["dup_email"] | df["dup_name_company"] | df["dup_email_company"]
    )

    logger.info(f"Duplicate detection complete — Total flagged: {df['flag_any_duplicate'].sum()}")

    return df
