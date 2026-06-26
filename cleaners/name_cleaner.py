# ============================================================
# cleaners/name_cleaner.py
# ============================================================

import pandas as pd
import yaml
from utils.logger import get_logger

logger = get_logger(__name__)


def load_config(config_path: str = "config/rules.yaml") -> dict:
    with open(config_path, "r") as f:
        return yaml.safe_load(f)


def smart_title_case(name: str) -> str:
    if not isinstance(name, str) or name.strip() == "":
        return name

    words = name.strip().split()
    result = []

    for word in words:
        if "'" in word:
            parts = word.split("'")
            word = "'".join(p.capitalize() for p in parts)
        elif word.lower().startswith("mc") and len(word) > 2:
            word = "Mc" + word[2:].capitalize()
        elif word.lower().startswith("mac") and len(word) > 3:
            word = "Mac" + word[3:].capitalize()
        else:
            word = word.capitalize()
        result.append(word)

    return " ".join(result)


def is_suspicious(value: str, suspicious_list: list) -> bool:
    if not isinstance(value, str):
        return False
    return value.strip().lower() in [s.lower() for s in suspicious_list]


def clean_names(df: pd.DataFrame, config_path: str = "config/rules.yaml") -> pd.DataFrame:
    config = load_config(config_path)
    name_config = config.get("names", {})

    first_col = name_config.get("first_name_column", "First Name")
    last_col = name_config.get("last_name_column", "Last Name")
    suspicious_values = name_config.get("suspicious_name_values", [])
    apply_title_case = name_config.get("apply_title_case", True)
    strip_whitespace = name_config.get("strip_whitespace", True)

    # --- First Name ---
    if first_col in df.columns:
        logger.info(f"Cleaning first name column: '{first_col}'")

        df["first_name_original"] = df[first_col].copy()

        df["first_name_cleaned"] = df[first_col].apply(
            lambda x: x.strip() if isinstance(x, str) and strip_whitespace else x
        )

        if apply_title_case:
            df["first_name_cleaned"] = df["first_name_cleaned"].apply(
                lambda x: smart_title_case(x) if isinstance(x, str) else x
            )

        df[first_col] = df["first_name_cleaned"]

        df["first_name_flag_suspicious"] = df[first_col].apply(
            lambda x: is_suspicious(x, suspicious_values)
        )

        logger.info(f"First name cleanup complete — Suspicious: {df['first_name_flag_suspicious'].sum()}")

    else:
        logger.warning(f"First name column '{first_col}' not found. Skipping.")

    # --- Last Name ---
    if last_col in df.columns:
        logger.info(f"Cleaning last name column: '{last_col}'")

        df["last_name_original"] = df[last_col].copy()

        df["last_name_cleaned"] = df[last_col].apply(
            lambda x: x.strip() if isinstance(x, str) and strip_whitespace else x
        )

        if apply_title_case:
            df["last_name_cleaned"] = df["last_name_cleaned"].apply(
                lambda x: smart_title_case(x) if isinstance(x, str) else x
            )

        df[last_col] = df["last_name_cleaned"]

        df["last_name_flag_suspicious"] = df[last_col].apply(
            lambda x: is_suspicious(x, suspicious_values)
        )

        logger.info(f"Last name cleanup complete — Suspicious: {df['last_name_flag_suspicious'].sum()}")

    else:
        logger.warning(f"Last name column '{last_col}' not found. Skipping.")

    return df
