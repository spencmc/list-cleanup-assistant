# AI List Cleanup Assistant

A production-grade CSV cleanup and QA tool built for Marketing Operations teams.

Upload a CSV, get a cleaned file and a professional QA report in seconds.

---

## What It Does

- **Email Validation** — flags blank, invalid, duplicate, disposable, and personal emails
- **Name Cleanup** — normalizes first and last names to proper title case
- **Company Cleanup** — removes extra spaces, fixes capitalization, flags suspicious values
- **Job Title Normalization** — standardizes titles with smart casing (VP, CEO, SVP, etc.)
- **Country & State Normalization** — converts USA/US/U.S.A. → United States, CA → California
- **Required Field Check** — flags rows missing critical fields
- **Duplicate Detection** — finds duplicates by email, email+company, and fuzzy name+company match
- **QA Report** — generates a quality score (0–100), risk level, and full breakdown
- **Three Output Formats** — cleaned CSV, QA report PDF, QA report JSON

---

## Quick Start

### 1. Clone the repository
```bash
git clone https://github.com/yourusername/list_cleanup_assistant.git
cd list_cleanup_assistant
```

### 2. Create and activate a virtual environment
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Run the app
```bash
streamlit run app.py
```

The app will open automatically in your browser at `http://localhost:8501`

---

## Project Structure

```
list_cleanup_assistant/
├── app.py                        # Streamlit UI
├── config/
│   └── rules.yaml                # All business rules and normalization maps
├── cleaners/
│   ├── email_cleaner.py          # Email validation and flagging
│   ├── name_cleaner.py           # First/last name normalization
│   ├── company_cleaner.py        # Company name cleanup
│   ├── title_cleaner.py          # Job title normalization
│   ├── geo_cleaner.py            # Country and state normalization
│   └── field_checker.py          # Required field validation
├── detectors/
│   └── duplicate_detector.py     # Duplicate detection
├── reporters/
│   ├── qa_report.py              # QA report builder
│   └── pdf_generator.py          # PDF report generator
├── utils/
│   ├── logger.py                 # Centralized logging
│   └── file_handler.py           # CSV ingestion and output
├── tests/
│   ├── test_email_cleaner.py
│   ├── test_name_cleaner.py
│   └── test_geo_cleaner.py
└── outputs/                      # Generated files (gitignored)
```

---

## Configuration

All business rules live in `config/rules.yaml`. You can edit this file without touching any Python code:

- Add or remove **required fields**
- Add **disposable or personal email domains**
- Add **country and state normalization mappings**
- Adjust **quality score weights**
- Change **risk level thresholds**

---

## Running Tests

```bash
pytest tests/ -v
```

To see test coverage:
```bash
pytest tests/ -v --cov=. --cov-report=term-missing
```

---

## Quality Score

The quality score (0–100) is calculated from five weighted metrics:

| Metric | Weight |
|---|---|
| Valid email rate | 30% |
| No duplicates | 20% |
| Required fields complete | 20% |
| Name & company quality | 15% |
| No disposable/personal emails | 15% |

**Risk Levels:**
- 🟢 **Low** — Score 85–100
- 🟡 **Medium** — Score 65–84
- 🟠 **High** — Score 40–64
- 🔴 **Critical** — Score 0–39

---

## Roadmap

| Version | Feature |
|---|---|
| v2 | NeverBounce API integration |
| v3 | Marketo REST API upload |
| v4 | Slack notifications |
| v5 | Automatic field mapping |
| v6 | AI-powered recommendations |
| v7 | Asana intake form |
| v8 | One-click upload approval |

---

## Built With

- [Streamlit](https://streamlit.io) — UI
- [Pandas](https://pandas.pydata.org) — Data processing
- [ReportLab](https://www.reportlab.com) — PDF generation
- [RapidFuzz](https://github.com/maxbachmann/RapidFuzz) — Fuzzy duplicate detection
- [PyYAML](https://pyyaml.org) — Configuration management

---

*Built for G2 Marketing Operations team. Designed for production use.*

By Spencer McKinney
