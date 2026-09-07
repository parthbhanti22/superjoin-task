"""
FastAPI application entry point.

Configures CORS, includes all routers, and initializes the database.
"""

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database import init_db
from routers import documents, facts, relationships

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
)

# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------
app = FastAPI(
    title="Fact Knowledge Layer API",
    description=(
        "Backend for the Fact Knowledge Layer — ingests PDFs, extracts "
        "grounded facts, and cross-references them across documents."
    ),
    version="1.0.0",
)

# ---------------------------------------------------------------------------
# CORS — allow the Next.js dev server
# ---------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------
app.include_router(documents.router)
app.include_router(facts.router)
app.include_router(relationships.router)


# ---------------------------------------------------------------------------
# Startup event
# ---------------------------------------------------------------------------
@app.on_event("startup")
def on_startup():
    """Initialize database tables on application start."""
    init_db()
    logging.getLogger(__name__).info("Database initialized. Server ready.")


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------
@app.get("/api/health")
def health_check():
    """Simple health check endpoint."""
    return {"status": "ok", "service": "fact-knowledge-layer"}
