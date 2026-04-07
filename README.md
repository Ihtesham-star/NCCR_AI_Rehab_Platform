# NCCR AI Rehabilitation Platform

**Astana, Kazakhstan**

An AI-powered clinical platform for assessing motor and cognitive function in children with disabilities, built for the **National Center for Children's Rehabilitation (NCCR)**. The system ingests multimodal clinical data, runs automated assessments, and generates personalized rehabilitation recommendations.

---

## Overview

Clinicians at NCCR collect data from multiple sources — EMG machines, balance sensors, and clinical examinations. This platform unifies all of that data into a single system that:

- Automatically extracts structured data from Noraxon EMG and TecnoBody balance PDFs using Claude AI
- Calculates motor function scores, disability severity, and fall risk
- Generates personalized weekly rehabilitation protocols per patient
- Provides a clinician-facing dashboard for patient management and reporting

---

## Features

- **Multimodal Data Ingestion** — Parses Noraxon EMG PDFs, TecnoBody balance test PDFs, and clinical Excel files
- **AI Document Parsing** — Uses Claude API to intelligently extract structured data from unstructured medical documents
- **Motor Assessment** — EMG asymmetry detection, muscle coordination scoring, gait quality analysis
- **Balance Analysis** — Stability index scoring, fall risk stratification (low / medium / high)
- **Disability Quantification** — Weighted disability index mapped to severity (mild / moderate / severe / profound)
- **Rehab Recommendations** — Rule-based engine generates exercise protocols adjusted by severity and GMFCS level
- **REST API** — Full FastAPI backend with Swagger docs at `/docs`
- **Streamlit Dashboard** — Clinician-facing web UI for patient management, data import, and report generation

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.10+, FastAPI |
| Frontend | Streamlit |
| Database | SQLite (dev) / PostgreSQL (prod) via SQLAlchemy |
| AI | Anthropic Claude API |
| Data Processing | pandas, pdfplumber, openpyxl, scipy |
| Visualization | Plotly |
| Auth | JWT (python-jose), bcrypt |

---

## Architecture

```
NCCR_AI_Rehab_Platform/
├── main.py                  # FastAPI entry point
├── app_streamlit.py         # Streamlit dashboard entry point
├── api/                     # REST API route handlers
│   ├── patients.py
│   ├── assessments.py
│   ├── recommendations.py
│   ├── data_import.py
│   └── clinical_documents.py
├── analytics/               # Assessment algorithms
│   └── motor_assessment.py  # Motor, balance, disability, cognitive analyzers
├── recommendations/         # Rehab protocol engine
│   └── rehab_engine.py
├── data_ingestion/          # PDF and Excel parsers
│   ├── emg_parser.py        # Noraxon EMG PDF parser
│   ├── balance_parser.py    # TecnoBody balance PDF parser
│   └── excel_parser.py      # Clinical Excel parser
├── database/                # SQLAlchemy models and connection
│   ├── models.py
│   └── connection.py
├── utils/
│   ├── claude_ai.py         # Claude API integration
│   └── validators.py
├── config/
│   └── settings.py          # Pydantic settings (loaded from .env)
└── static/                  # Web UI assets
```

---

## Supported Data Formats

| Format | Source | Data Extracted |
|--------|--------|----------------|
| Noraxon EMG PDF | EMG machine reports | Muscle activation (min/max/mean per muscle) |
| TecnoBody Balance PDF | Balance sensor reports | Stability index, trunk sway, fall risk |
| Clinical Excel | Perturbation project data | 6MWT, 10MWT, TUG, GMFCS, GMFM, WHO-QOL |
| Clinical Documents PDF | Hospital discharge summaries | Diagnoses (ICD), Barthel Index, therapy sessions |

---

## Database Schema

9 tables: `Patient`, `EMGSession`, `EMGData`, `BalanceTest`, `ClinicalTest`, `Assessment`, `RehabRecommendation`, `ClinicalDocument`, `User`

Assessment scores are computed from:
- Motor function — 35%
- Balance — 30%
- Functional capacity (6MWT/10MWT/TUG) — 25%
- GMFCS classification — 10%

---

## Getting Started

### Prerequisites

- Python 3.10+
- A Claude API key from [console.anthropic.com](https://console.anthropic.com)

### Installation

```bash
# 1. Clone the repository
git clone https://github.com/your-username/NCCR_AI_Rehab_Platform.git
cd NCCR_AI_Rehab_Platform

# 2. Create and activate virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env
# Open .env and add your CLAUDE_API_KEY
```

### Configuration

Edit `.env` and set your API key:

```env
CLAUDE_API_KEY=your-claude-api-key-here
```

All other defaults work out of the box for local development.

### Run

```bash
# Initialize the database
python scripts/init_database.py

# Start the FastAPI backend
python main.py
# API available at http://localhost:8000
# Swagger docs at http://localhost:8000/docs

# In a separate terminal, start the Streamlit dashboard
streamlit run app_streamlit.py
```

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/health` | Health check |
| GET | `/api/stats` | System statistics |
| POST | `/api/patients/` | Create patient |
| GET | `/api/patients/` | List patients |
| GET | `/api/patients/{id}` | Get patient |
| POST | `/api/assessments/{id}/generate` | Generate AI assessment |
| POST | `/api/recommendations/{id}/generate` | Generate rehab plan |
| POST | `/api/import/emg/pdf` | Import Noraxon EMG PDF |
| POST | `/api/import/balance/pdf` | Import TecnoBody balance PDF |
| POST | `/api/import/clinical/excel` | Import clinical Excel |
| POST | `/api/import/clinical-documents` | Import clinical document PDF |

Full interactive docs at `http://localhost:8000/docs`

---

## License

Proprietary — National Center for Children's Rehabilitation, Astana, Kazakhstan.
