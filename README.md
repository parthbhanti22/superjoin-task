# Fact Knowledge Layer

A full-stack system that ingests PDF documents, extracts semantically grounded facts, and cross-references them across documents to surface **corroborations**, **contradictions**, **contextually reconciled differences**, and **extraction failures**.

---

## Setup and Run Instructions

### Prerequisites

- **Python 3.11+** with `pip`
- **Node.js 18+** with `npm`
- **Groq API key** (free, no credit card) — get one at [console.groq.com](https://console.groq.com)

### 1. Clone & Enter the Project

```bash
git clone https://github.com/parthbhanti22/superjoin-task
cd superjoin-fact-layer
```

### 2. Backend Setup

```bash
# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
pip install -r backend/requirements.txt

# Configure your API key
cp backend/.env.example backend/.env
# Edit backend/.env and set GROQ_API_KEY=your_key_here

# Start the backend server
cd backend
uvicorn main:app --reload --port 8000
```

The API docs are available at [http://localhost:8000/docs](http://localhost:8000/docs).

### 3. Frontend Setup

```bash
# In a new terminal, from the project root:
cd frontend

# Install Node dependencies
npm install

# Start the dev server
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

### 4. Usage

1. **Upload** one or more PDF documents via the drag-and-drop upload panel.
2. **Extract Facts** — click "Extract Facts" on each document to trigger LLM-powered fact extraction.
3. **Analyze Relationships** — once 2+ documents are processed, navigate to the Relationships tab and click "Analyze Relationships" to compare facts across documents.

---

## Video Demo

[🎬 Watch the demo video here](YOUR_VIDEO_LINK_HERE)

---

## Approach

### Architecture

The system is split into a **FastAPI (Python) backend** and a **Next.js (TypeScript) frontend**, connected via a REST API.

```
Frontend (Next.js)  →  API Proxy  →  Backend (FastAPI)
                                         ├── PyMuPDF (PDF parsing)
                                         ├── Groq / Llama 3.3 70B (LLM)
                                         └── SQLite (persistence)
```

### Why This Stack?

| Component | Choice | Rationale |
|-----------|--------|-----------|
| LLM | Groq (Llama 3.3 70B) | Extremely fast inference (tokens/sec). Free tier with no credit card. JSON mode for structured output. High quality 70B parameter model. |
| PDF Parsing | PyMuPDF | Page-level text extraction with metadata. No system dependencies (Poppler, Tesseract). Fast and reliable. |
| Database | SQLite + SQLAlchemy | Zero-config persistence. ORM gives clean models. Easy migration path to Postgres. |
| Backend | FastAPI | Async-first, Pydantic validation, auto-generated OpenAPI docs. |
| Frontend | Next.js + Tailwind | App Router, TypeScript, server-side rendering capability. |

### Processing Pipeline

1. **PDF Ingestion**: PyMuPDF extracts text page-by-page, preserving page numbers as evidence anchors.

2. **Fact Extraction**: The document text (with `--- PAGE N ---` markers) is chunked and sent to Groq's Llama 3.3 70B model with a structured extraction prompt using JSON mode. Each fact includes:
   - The factual claim
   - Numeric value and unit (if applicable)
   - Subject category
   - Time context
   - **Exact verbatim source quote** from the document
   - Extraction confidence score

3. **Relationship Analysis**: Facts from all processed documents are sent to the LLM with a comparison prompt. The model classifies fact pairs into four relationship types:
   - **Corroboration**: Two sources agree
   - **Contradiction**: Sources genuinely disagree
   - **Contextual Difference**: Apparent contradiction explained by time, scope, methodology, or units
   - **Extraction Failure**: The system flags potential extraction or reasoning errors

### Design Decisions

- **No LangChain/LlamaIndex**: Direct Groq API calls with JSON mode give full control over extraction prompts — no hidden chunking or retrieval heuristics.
- **No hardcoded schemas**: The system processes any PDF dynamically. Extraction prompts are domain-agnostic.
- **Source grounding**: Every fact requires a verbatim `source_quote` from the document, making results auditable.
- **Intelligent chunking**: Large documents are split on page boundaries to stay within rate limits while preserving context.
- **Synchronous processing**: For simplicity in this assignment scope. A production system would use a job queue (Celery, etc.).

---

## Limitations and Next Steps

### Current Limitations

- **Synchronous processing**: Long PDFs may cause request timeouts. A production system would use async job queues.
- **Text-only extraction**: PyMuPDF extracts text; tables, charts, and images are not parsed. OCR would be needed for scanned documents.
- **LLM reliability**: Extraction quality depends on the model's output. Source quotes may occasionally be paraphrased rather than verbatim.
- **Groq rate limits**: The free tier has rate limits (~30 requests/minute). Large batch processing may need throttling.
- **No authentication**: The API is open. A production system would add auth.
- **SQLite concurrency**: SQLite is single-writer; concurrent uploads may queue.

### Next Steps

- **Async processing** with Celery + Redis for non-blocking fact extraction.
- **Table extraction** using Camelot or Tabula for structured data in PDFs.
- **Vector embeddings** for semantic similarity search when grouping facts.
- **Incremental analysis** — only re-analyze new documents instead of re-running on all.
- **User authentication** and multi-tenant support.
- **Confidence calibration** — validate extraction accuracy against ground truth.
- **Export** — CSV/JSON export of facts and relationships.

---

## Additional Notes

- **API Documentation**: FastAPI auto-generates interactive API docs at `/docs` (Swagger UI) and `/redoc` (ReDoc).
- **Environment Variables**: All secrets are loaded from `backend/.env` (git-ignored). See `backend/.env.example` for the template.
- **Starter Datasets**: Two curated PDF datasets are provided in the parent directory (`india-macroeconomy/` and `delhivery/`) for testing.
- **LLM Model**: Defaults to `llama-3.3-70b-versatile`. Set `GROQ_MODEL` in `.env` to switch (e.g., `llama-3.1-8b-instant` for faster but lower quality).
- **Database**: SQLite database is created at `backend/fact_layer.db` on first run. Delete it to reset all data.
