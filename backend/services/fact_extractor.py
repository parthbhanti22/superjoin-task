"""
Fact extraction service using Groq (Llama 3.3 70B).

Sends PDF text to the Groq API with a structured extraction prompt.
Returns validated facts with source evidence grounding.

Groq's API is OpenAI-compatible, so we use its native JSON mode
for structured output.
"""

import json
from typing import Generator
import logging
import time

from groq import Groq

from config import GROQ_API_KEY, GROQ_MODEL
from schemas import FactExtraction, FactExtractionResponse

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Groq client (lazy-initialized)
# ---------------------------------------------------------------------------
_client: Groq | None = None


def _get_client() -> Groq:
    """Return a singleton Groq client."""
    global _client
    if _client is None:
        if not GROQ_API_KEY:
            raise RuntimeError(
                "GROQ_API_KEY not configured. Set it in backend/.env. "
                "Get a free key at https://console.groq.com"
            )
        _client = Groq(api_key=GROQ_API_KEY)
    return _client


# ---------------------------------------------------------------------------
# Extraction prompt
# ---------------------------------------------------------------------------
EXTRACTION_SYSTEM_PROMPT = """You are a meticulous fact extraction engine. Your job is to extract factual claims from document text and ground each one to its exact source evidence.

RULES:
1. Extract ONLY factual, verifiable claims — not opinions, recommendations, or forward-looking statements.
2. For each fact, you MUST include a `source_quote` that is an EXACT verbatim excerpt from the provided text. Do not paraphrase.
3. If a fact has a numerical value, extract the `value` and `unit` separately.
4. The `subject` should be a concise label for what the fact is about (e.g., "India GDP growth rate", "Delhivery revenue").
5. The `time_context` should capture the time period the fact refers to (e.g., "FY 2024-25", "Q4 FY24", "2022").
6. The `page_number` should be the page where the fact appears, based on the "--- PAGE N ---" markers in the text.
7. Set `confidence` to a value between 0 and 1:
   - 1.0: Clear, unambiguous fact with exact source text
   - 0.7-0.9: Fact requires minor interpretation
   - Below 0.7: Fact is uncertain or the source text is ambiguous
8. Focus on the MOST IMPORTANT facts — key metrics, financial figures, dates, percentages, and named entities.
9. Do NOT extract duplicate facts from the same document.
10. Extract ONLY 2-5 of the most important facts per chunk. DO NOT exceed 5 facts.

You MUST respond with ONLY a valid JSON object (no markdown, no explanation) matching this schema:
{
  "facts": [
    {
      "claim": "string",
      "value": "string or null",
      "unit": "string or null",
      "subject": "string",
      "time_context": "string or null",
      "page_number": integer or null,
      "source_quote": "string",
      "confidence": float
    }
  ]
}"""


def _chunk_text(text: str, max_chars: int = 4000) -> list[str]:
    """
    Split document text into chunks that fit within Groq's context window.

    Llama 3.3 70B on Groq has a ~128k token context, but we chunk at
    ~24k characters (~6k tokens) to leave room for the system prompt
    and response, and to stay within rate limits on the free tier.
    Old data, groq can't handle more than 8000 per chunk here and its going nuts dude - changed it to 4000(chunk size) and 2000 tokens per chunk

    Splits on page boundaries (--- PAGE N ---) to preserve context.
    """
    if len(text) <= max_chars:
        return [text]

    chunks: list[str] = []
    pages = text.split("--- PAGE ")

    current_chunk = ""
    for page in pages:
        page_text = f"--- PAGE {page}" if page.strip() else ""
        if len(current_chunk) + len(page_text) > max_chars and current_chunk:
            chunks.append(current_chunk)
            current_chunk = page_text
        else:
            current_chunk += page_text

    if current_chunk.strip():
        chunks.append(current_chunk)

    return chunks if chunks else [text]


def extract_facts(document_text: str, filename: str) -> Generator[list[FactExtraction], None, None]:
    """
    Extract structured facts from document text using Groq.

    Args:
        document_text: The full text of the document with page markers.
        filename: Original filename for context.

    Returns:
        List of validated FactExtraction objects.

    Raises:
        RuntimeError: If the API call fails or response is unparseable.
    """
    client = _get_client()
    chunks = _chunk_text(document_text)
    logger.info(
        "Processing '%s' in %d chunk(s) via Groq (%s)",
        filename, len(chunks), GROQ_MODEL,
    )

    for i, chunk in enumerate(chunks):
        user_prompt = (
            f"Extract factual claims from this document: '{filename}'\n"
            f"(Chunk {i + 1} of {len(chunks)})\n\n"
            f"DOCUMENT TEXT:\n{chunk}"
        )

        logger.info("Sending chunk %d/%d to Groq for '%s'", i + 1, len(chunks), filename)

        try:
            response = client.chat.completions.create(
                model=GROQ_MODEL,
                messages=[
                    {"role": "system", "content": EXTRACTION_SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.1,  # Low temperature for precise extraction
                response_format={"type": "json_object"},
                max_tokens=2000, # Old data, groq can't handle more than 8000 per chunk here and its going nuts dude - changed it to 4000(chunk size) and 2000 tokens per chunk
            )
        except Exception as e:
            logger.error("Groq API error during fact extraction (chunk %d): %s", i + 1, e)
            continue  # Skip this chunk and move to the next to avoid crashing the whole document

        # Parse the structured response
        raw_text = response.choices[0].message.content
        if not raw_text:
            logger.warning("Empty response from Groq for chunk %d", i + 1)
            continue



        try:
            raw = json.loads(raw_text)
            result = FactExtractionResponse(**raw)
            yield result.facts
            logger.info(
                "Extracted %d facts from chunk %d of '%s'",
                len(result.facts), i + 1, filename,
            )
        except (json.JSONDecodeError, ValueError) as e:
            logger.error("Failed to parse Groq response (chunk %d): %s", i + 1, e)
            logger.debug("Raw response: %s", raw_text[:500])
            # Continue with other chunks instead of failing entirely
            continue

        if i < len(chunks) - 1:
            logger.info("Pausing for 60 seconds to respect Groq rate limits...")
            time.sleep(60)

