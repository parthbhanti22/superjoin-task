"""
Relationship engine — cross-document fact comparison using Groq.

Compares facts across documents to identify:
  - Corroborations: Two sources agree on the same claim
  - Contradictions: Two sources make incompatible claims
  - Contextual differences: Apparent contradictions explained by context
  - Extraction failures: Flags where extraction or reasoning may be wrong
"""

import json
import logging

from groq import Groq

from config import GROQ_API_KEY, GROQ_MODEL
from schemas import RelationshipAnalysisResponse, RelationshipExtraction

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
# Relationship analysis prompt
# ---------------------------------------------------------------------------
RELATIONSHIP_SYSTEM_PROMPT = """You are a rigorous fact-comparison engine. Given a set of facts extracted from different documents, you must identify relationships between facts that discuss the same or closely related subjects.

RELATIONSHIP TYPES (use exactly these labels):
1. "corroboration" — Two facts from different documents agree on the same claim or support each other.
2. "contradiction" — Two facts from different documents make genuinely incompatible claims about the same subject and time period.
3. "contextual_difference" — Two facts APPEAR to contradict each other but the difference is explained by a difference in time period, geographic scope, methodology, units of measurement, or data vintage. You MUST fill in `context_detail` explaining what context resolves the apparent contradiction.
4. "extraction_failure" — One or both facts appear to be incorrectly extracted, misquoted, or compared inappropriately. Flag this when you suspect the comparison itself is flawed.

RULES:
1. Only compare facts from DIFFERENT documents (never the same document).
2. Only create relationships where there is a meaningful connection — don't force comparisons.
3. For each relationship, provide a clear `explanation` of why you classified it that way.
4. For "contextual_difference", the `context_detail` must specifically identify what differs (time, scope, units, etc.).
5. For "extraction_failure", explain what seems wrong and why.
6. Use the exact `fact_id_a` and `fact_id_b` values provided — do not invent new IDs.
7. Aim for quality over quantity. 8-20 relationships is typical for a good analysis.
8. You MUST find at least one example of each relationship type if the data supports it.

You MUST respond with ONLY a valid JSON object (no markdown, no explanation) matching this schema:
{
  "relationships": [
    {
      "fact_id_a": "string",
      "fact_id_b": "string",
      "rel_type": "corroboration | contradiction | contextual_difference | extraction_failure",
      "explanation": "string",
      "context_detail": "string or null"
    }
  ]
}"""


def analyze_relationships(
    facts_by_document: dict[str, list[dict]],
) -> list[RelationshipExtraction]:
    """
    Analyze facts across documents to identify relationships.

    Args:
        facts_by_document: Dict mapping document filename to list of fact dicts.
            Each fact dict must have keys: id, claim, value, unit, subject,
            time_context, page_number, source_quote, confidence.

    Returns:
        List of RelationshipExtraction objects.

    Raises:
        RuntimeError: If fewer than 2 documents or API call fails.
    """
    if len(facts_by_document) < 2:
        raise RuntimeError(
            "Need facts from at least 2 documents to analyze relationships"
        )

    client = _get_client()

    # Build the fact listing for the prompt
    fact_sections = []
    for filename, facts in facts_by_document.items():
        lines = [f"\n=== DOCUMENT: {filename} ==="]
        for f in facts:
            lines.append(
                f"  [ID: {f['id']}]\n"
                f"  Claim: {f['claim']}\n"
                f"  Value: {f.get('value', 'N/A')} {f.get('unit', '')}\n"
                f"  Subject: {f.get('subject', 'N/A')}\n"
                f"  Time: {f.get('time_context', 'N/A')}\n"
                f"  Page: {f.get('page_number', 'N/A')}\n"
                f"  Source quote: \"{f['source_quote']}\"\n"
                f"  Confidence: {f.get('confidence', 1.0)}"
            )
        fact_sections.append("\n".join(lines))

    user_prompt = (
        "Analyze the following facts extracted from different documents. "
        "Identify corroborations, contradictions, contextual differences, "
        "and potential extraction failures.\n\n"
        + "\n".join(fact_sections)
    )

    logger.info(
        "Sending relationship analysis request to Groq (%d documents, %d total facts)",
        len(facts_by_document),
        sum(len(f) for f in facts_by_document.values()),
    )

    try:
        response = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {"role": "system", "content": RELATIONSHIP_SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.2,
            response_format={"type": "json_object"},
            max_tokens=8000,
        )
    except Exception as e:
        logger.error("Groq API error during relationship analysis: %s", e)
        raise RuntimeError(f"Groq API call failed: {e}") from e

    # Parse response
    raw_text = response.choices[0].message.content
    if not raw_text:
        logger.warning("Empty response from Groq for relationship analysis")
        return []

    try:
        raw = json.loads(raw_text)
        result = RelationshipAnalysisResponse(**raw)
        logger.info("Identified %d relationships", len(result.relationships))
        return result.relationships
    except (json.JSONDecodeError, ValueError) as e:
        logger.error("Failed to parse Groq relationship response: %s", e)
        logger.debug("Raw response: %s", raw_text[:500])
        raise RuntimeError(f"Failed to parse relationship response: {e}") from e

