# ============================================================
# cleaners/email_cleaner.py
# ============================================================

import re
import pandas as pd
import yaml
from utils.logger import get_logger

logger = get_logger(__name__)


def load_config(config_path: str = "config/rules.yaml") -> dict:
    with open(config_path, "r") as f:
        return yaml.safe_load(f)


def is_valid_email_syntax(email: str) -> bool:
    """
    Validates email syntax using a robust regex pattern.
    Checks for: local@domain.tld structure
    """
    if not email or not isinstance(email, str):
        return False
    pattern = r'^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email.strip()))


def get_email_domain(email: str) -> str:
    """Extracts the domain from an email address."""
    try:
        return email.strip().lower().split("@")[1]
    except (IndexError, AttributeError):
        return ""


def clean_emails(df: pd.DataFrame, config_path: str = "config/rules.yaml") -> pd.DataFrame:
    """
    Main email cleaning function.

    Adds the following flag columns to the DataFrame:
      - email_original        : the raw value before any changes
      - email_cleaned         : normalized email (lowercase, stripped)
      - email_flag_blank      : True if email is missing
      - email_flag_invalid    : True if email fails syntax check
      - email_flag_duplicate  : True if email appears more than once
      - email_flag_disposable : True if domain is a disposable service
      - email_flag_personal   : True if domain is a personal provider
      - email_domain          : extracted domain for reporting
    """

    config = load_config(config_path)
    email_config = config.get("email", {})

    col = email_config.get("column_name", "Email")

    if col not in df.columns:
        logger.warning(f"Email column '{col}' not found in file. Skipping email cleaning.")
        return df

    logger.info(f"Starting email cleanup on column: '{col}'")

    disposable = set(email_config.get("disposable_domains", []))
    personal = set(email_config.get("personal_domains", []))

    # Preserve original value
    df["email_original"] = df[col].copy()

    # Clean: strip whitespace and normalize to lowercase
    df["email_cleaned"] = df[col].apply(
        lambda x: x.strip().lower() if isinstance(x, str) else x
    )

    # Write cleaned value back to the main column
    df[col] = df["email_cleaned"]

    # Flag: blank emails
    df["email_flag_blank"] = df[col].isna() | (df[col].str.strip() == "")

    # Flag: invalid syntax
    df["email_flag_invalid"] = df[col].apply(
        lambda x: not is_valid_email_syntax(x) if isinstance(x, str) and x.strip() != "" else False
    )

    # Flag: duplicates
    df["email_flag_duplicate"] = df[col].duplicated(keep="first") & df[col].notna()

    # Extract domain
    df["email_domain"] = df[col].apply(
        lambda x: get_email_domain(x) if isinstance(x, str) else ""
    )

    # Flag: disposable domains
    df["email_flag_disposable"] = df["email_domain"].apply(
        lambda d: d in disposable
    )

    # Flag: personal domains
    df["email_flag_personal"] = df["email_domain"].apply(
        lambda d: d in personal
    )

    # Summary logging
    blank_count = df["email_flag_blank"].sum()
    invalid_count = df["email_flag_invalid"].sum()
    duplicate_count = df["email_flag_duplicate"].sum()
    disposable_count = df["email_flag_disposable"].sum()
    personal_count = df["email_flag_personal"].sum()

    logger.info(f"Email cleanup complete — Blank: {blank_count} | Invalid: {invalid_count} | "
                f"Duplicate: {duplicate_count} | Disposable: {disposable_count} | Personal: {personal_count}")

    return df
