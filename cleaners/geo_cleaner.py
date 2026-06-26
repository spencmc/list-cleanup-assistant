# ============================================================
# cleaners/geo_cleaner.py
# ============================================================

import pandas as pd
import yaml
from utils.logger import get_logger

logger = get_logger(__name__)


def load_config(config_path: str = "config/rules.yaml") -> dict:
    with open(config_path, "r") as f:
        return yaml.safe_load(f)


def normalize_value(value: str, lookup: dict) -> tuple:
    """
    Looks up a value in the normalization map.
    Returns (normalized_value, was_changed).

    Tries exact match first, then case-insensitive match.
    """
    if not isinstance(value, str) or value.strip() == "":
        return value, False

    value_stripped = value.strip()

    # Exact match
    if value_stripped in lookup:
        normalized = lookup[value_stripped]
        return normalized, normalized != value_stripped

    # Case-insensitive match
    for key, normalized in lookup.items():
        if value_stripped.lower() == key.lower():
            return normalized, normalized != value_stripped

    # No match found — return original
    return value_stripped, False


def clean_geo(df: pd.DataFrame, config_path: str = "config/rules.yaml") -> pd.DataFrame:
    """
    Normalizes Country and State columns using lookup tables in rules.yaml.

    Adds the following flag columns:
      - country_original      : raw value before changes
      - country_cleaned       : normalized value
      - country_flag_changed  : True if the value was normalized
      - country_flag_unknown  : True if no match was found in the lookup
      - state_original        : raw value before changes
      - state_cleaned         : normalized value
      - state_flag_changed    : True if the value was normalized
    """
    config = load_config(config_path)

    # --- Country ---
    country_config = config.get("country", {})
    country_col = country_config.get("column_name", "Country")
    country_map = country_config.get("normalization_map", {})

    if country_col in df.columns:
        logger.info(f"Normalizing country column: '{country_col}'")

        df["country_original"] = df[country_col].copy()

        results = df[country_col].apply(
            lambda x: normalize_value(x, country_map)
        )

        df["country_cleaned"] = results.apply(lambda x: x[0])
        df["country_flag_changed"] = results.apply(lambda x: x[1])
        df[country_col] = df["country_cleaned"]

        # Flag countries that couldn't be matched to anything in the lookup
        known_countries = set(country_map.values())
        df["country_flag_unknown"] = df[country_col].apply(
            lambda x: isinstance(x, str) and x.strip() != "" and x not in known_countries
        )

        logger.info(
            f"Country cleanup complete — "
            f"Normalized: {df['country_flag_changed'].sum()} | "
            f"Unknown: {df['country_flag_unknown'].sum()}"
        )

    else:
        logger.warning(f"Country column '{country_col}' not found. Skipping.")

    # --- State ---
    state_config = config.get("state", {})
    state_col = state_config.get("column_name", "State")
    state_map = state_config.get("normalization_map", {})

    if state_col in df.columns:
        logger.info(f"Normalizing state column: '{state_col}'")

        df["state_original"] = df[state_col].copy()

        results = df[state_col].apply(
            lambda x: normalize_value(x, state_map)
        )

        df["state_cleaned"] = results.apply(lambda x: x[0])
        df["state_flag_changed"] = results.apply(lambda x: x[1])
        df[state_col] = df["state_cleaned"]

        logger.info(
            f"State cleanup complete — "
            f"Normalized: {df['state_flag_changed'].sum()}"
        )

    else:
        logger.warning(f"State column '{state_col}' not found. Skipping.")

    return df
