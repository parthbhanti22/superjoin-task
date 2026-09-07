"""
Application configuration.

Loads settings from environment variables via a .env file.
Keeps all secrets out of source code.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent
UPLOAD_DIR = BASE_DIR / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

DB_PATH = BASE_DIR / "fact_layer.db"

# ---------------------------------------------------------------------------
# Environment
# ---------------------------------------------------------------------------
load_dotenv(BASE_DIR / ".env")

GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL: str = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

if not GROQ_API_KEY:
    print(
        "WARNING: GROQ_API_KEY is not set. "
        "Create backend/.env with GROQ_API_KEY=your_key. "
        "Get a free key at https://console.groq.com"
    )

# ---------------------------------------------------------------------------
# App settings
# ---------------------------------------------------------------------------
MAX_UPLOAD_SIZE_MB: int = 50
ALLOWED_EXTENSIONS: set[str] = {".pdf"}

