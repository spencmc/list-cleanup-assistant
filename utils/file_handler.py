# ============================================================
# utils/file_handler.py
# ============================================================

import os
import json
import pandas as pd
from utils.logger import get_logger

logger = get_logger(__name__)


def load_csv(file_path: str) -> pd.DataFrame:
    if not os.path.exists(file_path):
        logger.error(f"File not found: {file_path}")
        raise FileNotFoundError(f"No file found at: {file_path}")

    encodings = ["utf-8", "latin-1", "windows-1252"]

    for encoding in encodings:
        try:
            df = pd.read_csv(file_path, encoding=encoding, dtype=str)
            df.columns = df.columns.str.strip()
            df = df.where(df.notna(), other=pd.NA)

            if df.empty:
                raise ValueError("The uploaded CSV file is empty.")

            logger.info(f"Loaded {len(df)} rows and {len(df.columns)} columns from {file_path}")
            return df

        except UnicodeDecodeError:
            logger.warning(f"Encoding {encoding} failed, trying next...")
            continue

    raise ValueError("Could not read the file. Please save it as UTF-8 CSV and try again.")


def load_csv_from_upload(uploaded_file) -> pd.DataFrame:
    encodings = ["utf-8", "latin-1", "windows-1252"]

    for encoding in encodings:
        try:
            uploaded_file.seek(0)
            df = pd.read_csv(uploaded_file, encoding=encoding, dtype=str)
            df.columns = df.columns.str.strip()
            df = df.where(df.notna(), other=pd.NA)

            if df.empty:
                raise ValueError("The uploaded CSV file is empty.")

            logger.info(f"Loaded {len(df)} rows and {len(df.columns)} columns from uploaded file")
            return df

        except UnicodeDecodeError:
            logger.warning(f"Encoding {encoding} failed, trying next...")
            continue

    raise ValueError("Could not read the file. Please save it as UTF-8 CSV and try again.")


def save_cleaned_csv(df: pd.DataFrame, output_dir: str, filename: str) -> str:
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, filename)
    df.to_csv(output_path, index=False, encoding="utf-8")
    logger.info(f"Cleaned CSV saved to: {output_path}")
    return output_path


def save_json_report(report: dict, output_dir: str, filename: str) -> str:
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, filename)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, default=str)

    logger.info(f"JSON report saved to: {output_path}")
    return output_path


def get_column_mapping(df: pd.DataFrame, expected_columns: list) -> dict:
    actual_columns = df.columns.tolist()
    mapping = {}

    for expected in expected_columns:
        if expected in actual_columns:
            mapping[expected] = expected
            continue

        for actual in actual_columns:
            if expected.lower() == actual.lower():
                mapping[expected] = actual
                logger.warning(f"Column '{expected}' matched to '{actual}' (case-insensitive)")
                break

    return mapping
