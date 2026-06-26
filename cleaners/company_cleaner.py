# ============================================================
# cleaners/company_cleaner.py
# ============================================================

import re
import pandas as pd
import yaml
from utils.logger import get_logger

logger = get_logger(__name__)


def load_config(config_path: str = "config/rules.yaml") -> dict:
    with open(config_path, "r") as f:
        return yaml.safe_load(f)


def clean_company_name(value: str) -> str:
    if not isinstance(value, str) or value.strip() == "":
        return value
    value = value.strip()
    value = re.sub(r'\s+', ' ', value)
    value = value.title()
    return value


def is_suspicious(value: str, suspicious_list: list) -> bool:
    if not isinstance(value, str):
        return False
    return value.strip().lower() in [s.lower() for s in suspicious_list]


def clean_companies(df: pd.DataFrame, config_path: str = "config/rules.yaml") -> pd.DataFrame:
    config = load_config(config_path)
    company_config = config.get("company", {})

    col = company_config.get("column_name", "Company")
    suspicious_values = company_config.get("suspicious_company_values", [])

    if col not in df.columns:
        logger.warning(f"Company column '{col}' not found. Skipping.")
        return df

    logger.info(f"Cleaning company column: '{col}'")

    df["company_original"] = df[col].copy()

    df["company_cleaned"] = df[col].apply(clean_company_name)

    df[col] = df["company_cleaned"]

    df["company_flag_suspicious"] = df[col].apply(
        lambda x: is_suspicious(x, suspicious_values)
    )

    logger.info(f"Company cleanup complete — Suspicious: {df['company_flag_suspicious'].sum()}")

    return df
