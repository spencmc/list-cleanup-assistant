# ============================================================
# reporters/pdf_generator.py
# ============================================================

import os
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from utils.logger import get_logger

logger = get_logger(__name__)


# --- Color Palette ---
COLOR_PRIMARY    = colors.HexColor("#1a1a2e")
COLOR_ACCENT     = colors.HexColor("#0f3460")
COLOR_SUCCESS    = colors.HexColor("#2d6a4f")
COLOR_WARNING    = colors.HexColor("#e76f51")
COLOR_DANGER     = colors.HexColor("#d62828")
COLOR_LIGHT      = colors.HexColor("#f8f9fa")
COLOR_BORDER     = colors.HexColor("#dee2e6")


def get_risk_color(risk_level: str):
    mapping = {
        "Low":      COLOR_SUCCESS,
        "Medium":   COLOR_WARNING,
        "High":     COLOR_DANGER,
        "Critical": COLOR_DANGER,
    }
    return mapping.get(risk_level, COLOR_PRIMARY)


def build_styles():
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "ReportTitle",
        fontSize=24,
        textColor=COLOR_PRIMARY,
        alignment=TA_CENTER,
        spaceAfter=6,
        fontName="Helvetica-Bold",
    )

    subtitle_style = ParagraphStyle(
        "ReportSubtitle",
        fontSize=11,
        textColor=colors.grey,
        alignment=TA_CENTER,
        spaceAfter=20,
        fontName="Helvetica",
    )

    section_style = ParagraphStyle(
        "SectionHeader",
        fontSize=13,
        textColor=COLOR_ACCENT,
        spaceBefore=16,
        spaceAfter=8,
        fontName="Helvetica-Bold",
    )

    body_style = ParagraphStyle(
        "BodyText",
        fontSize=10,
        textColor=COLOR_PRIMARY,
        spaceAfter=4,
        fontName="Helvetica",
    )

    return {
        "title": title_style,
        "subtitle": subtitle_style,
        "section": section_style,
        "body": body_style,
    }


def make_summary_table(report: dict, styles: dict) -> Table:
    summary = report["summary"]
    email = report["email"]
    duplicates = report["duplicates"]
    required = report["required_fields"]

    risk_color = get_risk_color(summary["risk_level"])

    data = [
        ["Metric", "Value"],
        ["Total Records", str(summary["total_records"])],
        ["Valid Records", str(summary["valid_records"])],
        ["Quality Score", f"{summary['quality_score']} / 100"],
        ["Risk Level", summary["risk_level"]],
        ["Blank Emails", str(email["blank"])],
        ["Invalid Emails", str(email["invalid"])],
        ["Duplicate Emails", str(email["duplicate"])],
        ["Disposable Emails", str(email["disposable"])],
        ["Personal Emails", str(email["personal"])],
        ["Total Duplicates", str(duplicates["total_duplicates"])],
        ["Rows Missing Required Fields", str(required["rows_missing_required"])],
        ["Required Fields Complete", f"{required['complete_rate_pct']}%"],
    ]

    table = Table(data, colWidths=[3.5 * inch, 3.5 * inch])

    style = TableStyle([
        ("BACKGROUND",    (0, 0), (-1, 0), COLOR_ACCENT),
        ("TEXTCOLOR",     (0, 0), (-1, 0), colors.white),
        ("FONTNAME",      (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE",      (0, 0), (-1, 0), 11),
        ("ALIGN",         (0, 0), (-1, -1), "LEFT"),
        ("FONTNAME",      (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE",      (0, 1), (-1, -1), 10),
        ("ROWBACKGROUNDS",(0, 1), (-1, -1), [COLOR_LIGHT, colors.white]),
        ("GRID",          (0, 0), (-1, -1), 0.5, COLOR_BORDER),
        ("TOPPADDING",    (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING",   (0, 0), (-1, -1), 10),
    ])

    # Highlight risk level row
    for i, row in enumerate(data):
        if row[0] == "Risk Level":
            style.add("TEXTCOLOR", (1, i), (1, i), risk_color)
            style.add("FONTNAME",  (1, i), (1, i), "Helvetica-Bold")

    table.setStyle(style)
    return table


def make_breakdown_table(title: str, data_dict: dict) -> Table:
    rows = [[title, "Count"]]
    for key, val in list(data_dict.items())[:10]:
        rows.append([str(key), str(val)])

    if len(rows) == 1:
        rows.append(["No data available", ""])

    table = Table(rows, colWidths=[4.0 * inch, 3.0 * inch])
    table.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, 0), COLOR_ACCENT),
        ("TEXTCOLOR",     (0, 0), (-1, 0), colors.white),
        ("FONTNAME",      (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE",      (0, 0), (-1, 0), 10),
        ("FONTNAME",      (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE",      (0, 1), (-1, -1), 9),
        ("ROWBACKGROUNDS",(0, 1), (-1, -1), [COLOR_LIGHT, colors.white]),
        ("GRID",          (0, 0), (-1, -1), 0.5, COLOR_BORDER),
        ("TOPPADDING",    (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING",   (0, 0), (-1, -1), 10),
    ]))
    return table


def generate_pdf(report: dict, output_path: str) -> str:
    """
    Generates a professional QA report PDF.

    Args:
        report: The QA report dictionary from qa_report.py
        output_path: Full path where the PDF should be saved

    Returns:
        The output path of the saved PDF
    """

    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        rightMargin=0.75 * inch,
        leftMargin=0.75 * inch,
        topMargin=0.75 * inch,
        bottomMargin=0.75 * inch,
    )

    styles = build_styles()
    story = []

    # --- Title ---
    story.append(Paragraph("AI List Cleanup Assistant", styles["title"]))
    story.append(Paragraph("QA Report — Marketing Operations", styles["subtitle"]))
    story.append(HRFlowable(width="100%", thickness=1, color=COLOR_BORDER))
    story.append(Spacer(1, 0.2 * inch))

    # --- Summary Table ---
    story.append(Paragraph("Summary", styles["section"]))
    story.append(make_summary_table(report, styles))
    story.append(Spacer(1, 0.2 * inch))

    # --- Country Breakdown ---
    story.append(Paragraph("Top Countries", styles["section"]))
    story.append(make_breakdown_table("Country", report["breakdowns"]["top_countries"]))
    story.append(Spacer(1, 0.2 * inch))

    # --- Top Job Titles ---
    story.append(Paragraph("Top Job Titles", styles["section"]))
    story.append(make_breakdown_table("Job Title", report["breakdowns"]["top_titles"]))
    story.append(Spacer(1, 0.2 * inch))

    # --- Top Companies ---
    story.append(Paragraph("Top Companies", styles["section"]))
    story.append(make_breakdown_table("Company", report["breakdowns"]["top_companies"]))
    story.append(Spacer(1, 0.2 * inch))

    # --- Footer ---
    story.append(HRFlowable(width="100%", thickness=1, color=COLOR_BORDER))
    story.append(Spacer(1, 0.1 * inch))
    story.append(Paragraph(
        "Generated by AI List Cleanup Assistant — For internal Marketing Operations use only.",
        styles["body"]
    ))

    doc.build(story)
    logger.info(f"PDF report saved to: {output_path}")
    return output_path
