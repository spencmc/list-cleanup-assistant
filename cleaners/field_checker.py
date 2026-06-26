# ============================================================
# cleaners/field_checker.py
# ============================================================

import pandas as pd
import yaml
from utils.logger import get_logger

logger = get_logger(__name__)


def load_config(config_path: str = "config/rules.yaml") -> dict:
    with open(config_path, "r") as f:
        return yaml.safe_load(f)


def check_required_fields(df: pd.DataFrame, config_path: str = "config/rules.yaml") -> pd.DataFrame:
    """
    Checks every row for missing required fields defined in rules.yaml.

    Adds the following flag columns:
      - missing_fields        : comma-separated list of missing field names
      - missing_fields_count  : number of missing required fields in that row
      - flag_missing_required : True if ANY required field is missing
    """

    config = load_config(config_path)
    required_fields = config.get("required_fields", [])

    if not required_fields:
        logger.warning("No required fields defined in rules.yaml. Skipping field check.")
        return df

    logger.info(f"Checking required fields: {required_fields}")

    # Only check fields that actually exist as columns in the file
    fields_to_check = [f for f in required_fields if f in df.columns]
    missing_from_file = [f for f in required_fields if f not in df.columns]

    if missing_from_file:
        logger.warning(f"These required fields are not columns in the file: {missing_from_file}")

    def get_missing(row):
        missing = []
        for field in fields_to_check:
            value = row.get(field)
            if pd.isna(value) or str(value).strip() == "":
                missing.append(field)
        return missing

    df["missing_fields"] = df.apply(
        lambda row: ", ".join(get_missing(row)), axis=1
    )

    df["missing_fields_count"] = df.apply(
        lambda row: len(get_missing(row)), axis=1
    )

    df["flag_missing_required"] = df["missing_fields_count"] > 0

    total_flagged = df["flag_missing_required"].sum()
    logger.info(f"Required field check complete — Rows with missing fields: {total_flagged}")

    return df
