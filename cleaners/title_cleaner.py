# ============================================================
# cleaners/title_cleaner.py
# ============================================================

import pandas as pd
import yaml
from utils.logger import get_logger

logger = get_logger(__name__)


def load_config(config_path: str = "config/rules.yaml") -> dict:
    with open(config_path, "r") as f:
        return yaml.safe_load(f)


def normalize_title(value: str, always_upper: list, always_lower: list) -> str:
    """
    Normalizes a job title with smart casing rules.

    Examples:
        vp sales           -> VP Sales
        director marketing -> Director Marketing
        head of it         -> Head of IT
    """
    if not isinstance(value, str) or value.strip() == "":
        return value

    words = value.strip().split()
    result = []

    for i, word in enumerate(words):
        upper_map = {w.lower(): w for w in always_upper}
        lower_list = [w.lower() for w in always_lower]

        if word.lower() in upper_map:
            result.append(upper_map[word.lower()])
        elif word.lower() in lower_list and i != 0:
            result.append(word.lower())
        else:
            result.append(word.capitalize())

    return " ".join(result)


def is_suspicious(value: str, suspicious_list: list) -> bool:
    if not isinstance(value, str):
        return False
    return value.strip().lower() in [s.lower() for s in suspicious_list]


def clean_titles(df: pd.DataFrame, config_path: str = "config/rules.yaml") -> pd.DataFrame:
    config = load_config(config_path)
    title_config = config.get("job_title", {})

    col = title_config.get("column_name", "Job Title")
    always_upper = title_config.get("always_uppercase_words", [])
    always_lower = title_config.get("always_lowercase_words", [])
    suspicious_values = title_config.get("suspicious_title_values", [])

    if col not in df.columns:
        logger.warning(f"Job title column '{col}' not found. Skipping.")
        return df

    logger.info(f"Cleaning job title column: '{col}'")

    df["title_original"] = df[col].copy()

    df["title_cleaned"] = df[col].apply(
        lambda x: normalize_title(x, always_upper, always_lower)
        if isinstance(x, str) else x
    )

    df[col] = df["title_cleaned"]

    df["title_flag_suspicious"] = df[col].apply(
        lambda x: is_suspicious(x, suspicious_values)
    )

    logger.info(f"Title cleanup complete — Suspicious: {df['title_flag_suspicious'].sum()}")

    return df
