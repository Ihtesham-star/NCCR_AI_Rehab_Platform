# NCCR AI Rehabilitation Platform

**Astana, Kazakhstan**

An AI-powered clinical platform for assessing motor and cognitive function in children with disabilities, built for the National Center for Children's Rehabilitation (NCCR). The system ingests multimodal clinical data, runs automated assessments, generates personalized rehabilitation recommendations, and supports semantic search across patient documents.

## Overview

Clinicians at NCCR collect data from multiple sources — EMG machines, balance sensors, clinical examinations, and discharge summary documents. This platform unifies all of that data into a single system that:

- Automatically extracts structured data from Noraxon EMG and TecnoBody balance PDFs, and unstructured clinical discharge summaries, using Claude AI
- Calculates motor function scores, disability severity, and fall risk
- Generates personalized weekly rehabilitation protocols per patient
- Supports semantic search over patient documents via a RAG pipeline
- Provides a clinician-facing dashboard for patient management and reporting

## Features

- **Multimodal Data Ingestion** — Parses Noraxon EMG PDFs, TecnoBody balance test PDFs, clinical Excel files, and Russian/Kazakh clinical discharge summary PDFs
- **AI Document Parsing** — Uses the Claude API to intelligently extract structured data from unstructured medical documents
- **RAG Document Search** — Semantic search across patient discharge summaries using multilingual sentence-transformer embeddings, with a LangGraph agent cross-validating extraction in shadow mode
- **Motor Assessment** — EMG asymmetry detection, muscle coordination scoring, gait quality analysis
- **Balance Analysis** — Stability index scoring, fall risk stratification (low / medium / high)
- **Disability Quantification** — Weighted disability index mapped to severity (mild / moderate / severe / profound)
- **Rehab Recommendations** — Rule-based engine generates exercise protocols adjusted by severity and GMFCS level
- **REST API** — Full FastAPI backend with Swagger docs at `/docs`
- **Streamlit Dashboard** — Clinician-facing web UI for patient management, data import, document search, and report generation

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.10+, FastAPI |
| Frontend | Streamlit |
| Database | SQLite (dev) / PostgreSQL (prod) via SQLAlchemy |
| AI | Anthropic Claude API, LangChain, LangGraph |
| RAG | sentence-transformers (`paraphrase-multilingual-MiniLM-L12-v2`), cosine similarity search |
| Data Processing | pandas, pdfplumber, openpyxl, scipy |
| Visualization | Plotly |
| Auth | JWT (python-jose), bcrypt |
| Evaluation | RAGAS |

## Architecture

```
NCCR_AI_Rehab_Platform/
├── main.py                  # FastAPI entry point
├── app_streamlit.py         # Streamlit dashboard entry point
├── api/                     # REST API route handlers
│   ├── patients.py
│   ├── assessments.py       # Assessment generation + RAG search endpoint
│   ├── recommendations.py
│   ├── data_import.py       # PDF/Excel import pipeline
│   └── clinical_documents.py
├── analytics/                # Assessment algorithms
│   └── motor_assessment.py   # Motor, balance, disability, cognitive analyzers
├── recommendations/          # Rehab protocol engine
│   └── rehab_engine.py
├── data_ingestion/           # PDF and Excel parsers
│   ├── emg_parser.py         # Noraxon EMG PDF parser
│   ├── balance_parser.py     # TecnoBody balance PDF parser
│   └── excel_parser.py       # Clinical Excel parser
├── database/                 # SQLAlchemy models and connection
│   ├── models.py
│   └── connection.py
├── utils/
│   ├── claude_ai.py          # Claude API integration
│   ├── rag_engine.py         # RAG pipeline (chunk → embed → search)
│   ├── nccr_agent.py         # LangGraph shadow-mode validation agent
│   └── validators.py
├── config/
│   └── settings.py           # Pydantic settings (loaded from .env)
└── static/                   # Web UI assets
```

## Supported Data Formats

| Format | Source | Data Extracted |
|---|---|---|
| Noraxon EMG PDF | EMG machine reports | Muscle activation (min/max/mean per muscle) |
| TecnoBody Balance PDF | Balance sensor reports | Stability index, trunk sway, fall risk |
| Clinical Excel | Perturbation project data | 6MWT, 10MWT, TUG, GMFCS, GMFM, WHO-QOL |
| Clinical Documents PDF | Hospital discharge summaries (Russian/Kazakh) | Diagnoses (ICD), Barthel Index, medications, therapy sessions, recommendations |

## Database Schema

9 tables: `Patient`, `EMGSession`, `EMGData`, `BalanceTest`, `ClinicalTest`, `Assessment`, `RehabRecommendation`, `ClinicalDocument`, `User` — plus `DocumentChunk` for RAG vector storage.

Assessment scores are computed from:
- Motor function — 35%
- Balance — 30%
- Functional capacity (6MWT/10MWT/TUG) — 25%
- GMFCS classification — 10%

## RAG Document Search

Discharge summary documents are chunked into 150-word segments with 30-word overlap, embedded using a multilingual sentence-transformer model, and stored as vectors in the database. Semantic search retrieves the top-3 relevant chunks per query, which are passed to Claude for grounded, source-cited answers via the `/assessments/{id}/search` endpoint.

The multilingual embedding model was a deliberate choice, not a default — an earlier English-centric model (`all-MiniLM-L6-v2`) gave noticeably noisier similarity scores on the Russian/Kazakh source documents. See **Engineering Notes** below for the full debugging trail.

**RAGAS Evaluation (6 patients, 30 QA pairs):**

| Metric | Score |
|--------|-------|
| Faithfulness | 0.928 |
| Answer Relevancy | 0.815 |
| Context Precision | 0.444 |
| Overall | 0.729 |

Faithfulness and Answer Relevancy stayed strong even with moderate Context Precision — indicating the generation layer (Claude) compensates well for retrieval noise, which is largely driven by the source documents' own structure (see Known Limitations).

## LangGraph Agent

A 4-node graph with conditional retry logic, run in **shadow mode**: it processes each document independently and its output is compared against Claude's primary extraction (logged as a warning on disagreement), rather than gating or driving the main pipeline. This cross-validates extraction consistency between two independent methods without adding a hard dependency to the ingestion path.

1. `extract_basic` — pull patient name/DOB/sex from the document
2. Conditional edge: if name is missing and `retry_count < 2` → `retry_extraction` (broader prompt, loops back to step 1); otherwise proceeds
3. `extract_clinical` — extract Barthel/GMFCS scores, diagnosis, therapy session data
4. `validate_clinical` — range-checks scores (Barthel 0–100, GMFCS 1–5), collects warnings without blocking
5. `generate_assessment` — compiles the final structured output

## Engineering Notes

The RAG pipeline went through several rounds of RAGAS-driven debugging rather than being tuned once and left alone:

- **API compatibility bug** — RAGAS's default Anthropic LLM wrapper sent both `temperature` and `top_p` in every request, which newer Claude models (4.5+) reject. Fixed by switching to a `LangchainLLMWrapper` configuration that sends only `temperature`.
- **Chunking bug** — the original chunker used 500-word chunks with no overlap. Most source documents only produced 2–4 chunks total, so `top_k=3` retrieval was effectively returning nearly the whole document regardless of the question. Reduced to 150 words with 30-word overlap, meaningfully improving Context Precision.
- **Embedding language mismatch** — the initial embedding model (`all-MiniLM-L6-v2`) is English-centric and gave noisy similarity scores on the Russian/Kazakh clinical text. Switched to a multilingual model (`paraphrase-multilingual-MiniLM-L12-v2`), improving both Context Precision and Answer Relevancy.
- **Data-integrity bugs** — found and fixed two issues causing orphaned/duplicate data: missing cascade-delete relationships (deleting a patient left their document chunks behind in the database), and no duplicate-upload check (re-uploading the same file created redundant chunks). Both fixed at the SQLAlchemy model / API level.
- **Section-aware chunking attempt (reverted)** — attempted a more sophisticated chunker that split documents on known section headers and collapsed repetitive therapy-log boilerplate. It worked correctly on the sample documents it was built and tested against, but regressed Context Precision on the full corpus (0.456 → 0.286) because the header patterns didn't generalize across all document templates in the dataset. Diagnosed the root cause (insufficient template coverage in the sample used to build it) and reverted to the flat chunker, which remains the best-measured configuration.
- **Excel import row truncation** — `parse_excel_intelligently` used `pd.read_excel(..., nrows=20)`, silently dropping every patient past row 20 in larger files with no warning. Fixed by reading the full sheet and processing it in batches, merging results across batches so files of any size are fully imported.
- **Missing input validation on GMFCS level** — a clinically meaningless value (e.g. outside the valid 1–5 range) could be saved via the patient API with no rejection. Added Pydantic `field_validator` constraints on `PatientCreate`/`PatientUpdate` to reject out-of-range values at the API boundary.
- **Assessment scoring evidence audit** — rather than leaving disability/motor scoring constants as unexamined heuristics, each one was checked against published pediatric rehabilitation literature:
  - **6MWT scoring** was normalized against a flat, unsourced 600m ceiling for every patient regardless of severity. Replaced with GMFCS-level-specific published reference distances (Nsenga Leunkeu et al.: GMFCS I ≈ 440m, II ≈ 387m, III ≈ 305m, typically-developing ≈ 528m).
  - **EMG asymmetry threshold** was an uncited 20%. No pediatric-CP-specific EMG threshold exists in the literature; lowered to 15%, the conservative end of the 10–15% range commonly cited in adjacent (sports/biomechanics) asymmetry research — flagged as borrowed evidence, not domain-specific.
  - **TUG and 10MWT scoring formulas** (`100 - ((time-10)*5)`, etc.) had no cited basis and, unlike adults (where a 13.5s TUG cutoff is established), no validated pediatric fall-risk cutoff exists for either test. Removed rather than replaced with a different unproven formula — raw times are now reported instead of a fabricated 0–100 score.
  - Remaining heuristics (disability index component weights, GMFCS-to-score linear conversion, EMG amplitude normalization, motor-derived cognitive scoring) were kept but are now explicitly flagged in code comments and API response fields as unvalidated, rather than presented as evidence-based. See Known Limitations.

## Known Limitations

- **Context Precision (0.444)** is limited primarily by document structure, not retrieval logic — source documents are 70–80% repetitive therapy-session log entries by word count, which caps how precisely any chunking strategy can rank relevant content.
- **`DocumentChunk` links to `Patient` only, not to a specific `ClinicalDocument`.** Fine for a corpus where each patient has one document; if a patient ever has multiple distinct documents, replacing just one requires wiping and rebuilding all of that patient's chunks.
- **Disability/motor scoring is a mix of evidence-based and unvalidated heuristics** — 6MWT scoring and the EMG asymmetry threshold are now grounded in published pediatric CP literature (see Engineering Notes). TUG/10MWT report raw times only, since no validated pediatric scoring cutoff exists for either. The disability index component weights, GMFCS-to-score linear conversion, and EMG amplitude normalization remain uncited heuristics — the clearest candidates for replacement with a supervised model trained on real outcome data. Raw EMG amplitude specifically cannot be meaningfully standardized at all without MVC (maximum voluntary contraction) calibration, which this pipeline does not currently collect — a data-collection gap, not just a scoring-formula gap.
- **Excel parser** processes all rows but performance degrades at 500+ patients without vector indexing (e.g. pgvector).

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

```
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

> **Note:** `localhost:8000` and `localhost:8501` are local-only addresses — they only work on the machine where you've run the commands above. There is no live/hosted demo of this project; you need to clone and run it yourself to access the API docs or dashboard.

## API Endpoints

> Requires the app running locally (see **Getting Started** above) — these are not live, publicly hosted endpoints.

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/health` | Health check |
| GET | `/api/stats` | System statistics |
| POST | `/api/patients/` | Create patient |
| GET | `/api/patients/` | List patients |
| GET | `/api/patients/{id}` | Get patient |
| POST | `/api/assessments/{id}/generate` | Generate AI assessment |
| POST | `/api/assessments/{id}/search` | RAG semantic search over patient documents |
| POST | `/api/recommendations/{id}/generate` | Generate rehab plan |
| POST | `/api/import/emg/pdf` | Import Noraxon EMG PDF |
| POST | `/api/import/balance/pdf` | Import TecnoBody balance PDF |
| POST | `/api/import/clinical/excel` | Import clinical Excel |
| POST | `/api/import/pdf/claude` | Import clinical document PDF (Claude AI parsing + RAG indexing) |

Full interactive docs at `http://localhost:8000/docs` once running.

## Data Privacy

Patient documents used to develop and evaluate this system are confidential clinical records. Neither raw documents nor derived training/fine-tuning data are included in this repository.

## License

Proprietary — National Center for Children's Rehabilitation, Astana, Kazakhstan.