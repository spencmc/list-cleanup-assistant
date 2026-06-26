# ============================================================
# reporters/qa_report.py
# ============================================================

import pandas as pd
import yaml
from utils.logger import get_logger

logger = get_logger(__name__)


def load_config(config_path: str = "config/rules.yaml") -> dict:
    with open(config_path, "r") as f:
        return yaml.safe_load(f)


def calculate_quality_score(stats: dict, weights: dict) -> float:
    """
    Calculates a 0-100 quality score based on weighted metrics.
    """
    total = stats["total_records"]
    if total == 0:
        return 0.0

    valid_email_rate = (
        (total - stats["invalid_email_count"] - stats["blank_email_count"] - stats["duplicate_email_count"])
        / total
    )

    no_duplicate_rate = 1 - (stats["duplicate_email_count"] / total)

    required_score = stats.get("required_fields_complete_rate", 1.0)

    suspicious_count = stats.get("suspicious_name_count", 0) + stats.get("suspicious_company_count", 0)
    name_company_rate = 1 - (suspicious_count / (total * 2))
    name_company_rate = max(0, name_company_rate)

    disposable_personal = stats["disposable_email_count"] + stats["personal_email_count"]
    no_disposable_rate = 1 - (disposable_personal / total)
    no_disposable_rate = max(0, no_disposable_rate)

    score = (
        valid_email_rate       * weights.get("valid_email_rate", 30) +
        no_duplicate_rate      * weights.get("no_duplicates", 20) +
        required_score         * weights.get("required_fields_complete", 20) +
        name_company_rate      * weights.get("name_company_quality", 15) +
        no_disposable_rate     * weights.get("no_disposable_personal", 15)
    )

    return round(min(100, max(0, score)), 1)


def get_risk_level(score: float, thresholds: dict) -> str:
    """Returns a risk level label based on the quality score."""
    if score >= thresholds.get("low", 85):
        return "Low"
    elif score >= thresholds.get("medium", 65):
        return "Medium"
    elif score >= thresholds.get("high", 40):
        return "High"
    else:
        return "Critical"


def build_qa_report(df: pd.DataFrame, config_path: str = "config/rules.yaml") -> dict:
    """
    Builds the complete QA report as a Python dictionary.
    This dictionary is used by both the PDF generator and JSON export.
    """

    config = load_config(config_path)
    score_config = config.get("quality_score", {})
    weights = {k: v for k, v in score_config.items() if k != "risk_levels"}
    thresholds = score_config.get("risk_levels", {})

    email_col = config.get("email", {}).get("column_name", "Email")
    country_col = config.get("country", {}).get("column_name", "Country")
    title_col = config.get("job_title", {}).get("column_name", "Job Title")
    company_col = config.get("company", {}).get("column_name", "Company")

    total = len(df)

    # --- Email Stats ---
    blank_email = int(df["email_flag_blank"].sum()) if "email_flag_blank" in df.columns else 0
    invalid_email = int(df["email_flag_invalid"].sum()) if "email_flag_invalid" in df.columns else 0
    duplicate_email = int(df["email_flag_duplicate"].sum()) if "email_flag_duplicate" in df.columns else 0
    disposable_email = int(df["email_flag_disposable"].sum()) if "email_flag_disposable" in df.columns else 0
    personal_email = int(df["email_flag_personal"].sum()) if "email_flag_personal" in df.columns else 0

    # --- Duplicate Stats ---
    any_duplicate = int(df["flag_any_duplicate"].sum()) if "flag_any_duplicate" in df.columns else 0

    # --- Required Fields ---
    missing_required = int(df["flag_missing_required"].sum()) if "flag_missing_required" in df.columns else 0
    required_fields_complete_rate = 1 - (missing_required / total) if total > 0 else 1.0

    # --- Name / Company Quality ---
    suspicious_names = int(df["first_name_flag_suspicious"].sum()) if "first_name_flag_suspicious" in df.columns else 0
    suspicious_companies = int(df["company_flag_suspicious"].sum()) if "company_flag_suspicious" in df.columns else 0

    # --- Country Breakdown ---
    country_counts = {}
    if country_col in df.columns:
        country_counts = df[country_col].value_counts().head(10).to_dict()

    # --- Top Job Titles ---
    top_titles = {}
    if title_col in df.columns:
        top_titles = df[title_col].value_counts().head(10).to_dict()

    # --- Top Companies ---
    top_companies = {}
    if company_col in df.columns:
        top_companies = df[company_col].value_counts().head(10).to_dict()

    # --- Valid Record Count ---
    valid_records = total - blank_email - invalid_email
    valid_records = max(0, valid_records)

    stats = {
        "total_records": total,
        "valid_records": valid_records,
        "blank_email_count": blank_email,
        "invalid_email_count": invalid_email,
        "duplicate_email_count": duplicate_email,
        "disposable_email_count": disposable_email,
        "personal_email_count": personal_email,
        "any_duplicate_count": any_duplicate,
        "missing_required_fields_count": missing_required,
        "required_fields_complete_rate": required_fields_complete_rate,
        "suspicious_name_count": suspicious_names,
        "suspicious_company_count": suspicious_companies,
    }

    quality_score = calculate_quality_score(stats, weights)
    risk_level = get_risk_level(quality_score, thresholds)

    report = {
        "summary": {
            "total_records": total,
            "valid_records": valid_records,
            "quality_score": quality_score,
            "risk_level": risk_level,
        },
        "email": {
            "blank": blank_email,
            "invalid": invalid_email,
            "duplicate": duplicate_email,
            "disposable": disposable_email,
            "personal": personal_email,
        },
        "duplicates": {
            "total_duplicates": any_duplicate,
        },
        "required_fields": {
            "rows_missing_required": missing_required,
            "complete_rate_pct": round(required_fields_complete_rate * 100, 1),
        },
        "data_quality": {
            "suspicious_names": suspicious_names,
            "suspicious_companies": suspicious_companies,
        },
        "breakdowns": {
            "top_countries": country_counts,
            "top_titles": top_titles,
            "top_companies": top_companies,
        },
    }

    logger.info(f"QA Report built — Score: {quality_score} | Risk: {risk_level}")
    return report
