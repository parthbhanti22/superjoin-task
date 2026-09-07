"""
Relationship analysis endpoints — trigger cross-document comparison and retrieve results.
"""

import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from models import Document, Fact, Relationship
from schemas import FactOut, RelationshipOut
from services.relationship_engine import analyze_relationships

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/relationships", tags=["relationships"])


@router.post("/analyze", response_model=list[RelationshipOut])
def trigger_analysis(db: Session = Depends(get_db)):
    """
    Trigger cross-document relationship analysis.

    Compares facts across ALL processed documents. Clears any
    previously computed relationships before re-analyzing.
    """
    # Gather facts grouped by document
    processed_docs = (
        db.query(Document).filter(Document.status == "processed").all()
    )

    if len(processed_docs) < 2:
        raise HTTPException(
            status_code=400,
            detail="Need at least 2 processed documents to analyze relationships",
        )

    facts_by_doc: dict[str, list[dict]] = {}
    for doc in processed_docs:
        facts = db.query(Fact).filter(Fact.document_id == doc.id).all()
        facts_by_doc[doc.filename] = [
            {
                "id": f.id,
                "claim": f.claim,
                "value": f.value,
                "unit": f.unit,
                "subject": f.subject,
                "time_context": f.time_context,
                "page_number": f.page_number,
                "source_quote": f.source_quote,
                "confidence": f.confidence,
            }
            for f in facts
        ]

    # Collect all valid fact IDs so we can validate the LLM response
    all_fact_ids = set()
    for facts in facts_by_doc.values():
        for f in facts:
            all_fact_ids.add(f["id"])

    try:
        # Run relationship analysis via Gemini
        extracted_rels = analyze_relationships(facts_by_doc)

        # Clear existing relationships
        db.query(Relationship).delete()

        # Store new relationships (only those referencing valid fact IDs)
        stored = []
        for rel in extracted_rels:
            if rel.fact_id_a not in all_fact_ids or rel.fact_id_b not in all_fact_ids:
                logger.warning(
                    "Skipping relationship with invalid fact IDs: %s, %s",
                    rel.fact_id_a,
                    rel.fact_id_b,
                )
                continue

            db_rel = Relationship(
                fact_id_a=rel.fact_id_a,
                fact_id_b=rel.fact_id_b,
                rel_type=rel.rel_type,
                explanation=rel.explanation,
                context_detail=rel.context_detail,
            )
            db.add(db_rel)
            stored.append(db_rel)

        db.commit()

        # Refresh and build response
        return _build_relationship_response(stored, db)

    except Exception as e:
        logger.error("Relationship analysis failed: %s", e)
        raise HTTPException(
            status_code=500, detail=f"Relationship analysis failed: {e}"
        )


@router.get("", response_model=list[RelationshipOut])
def get_relationships(db: Session = Depends(get_db)):
    """Return all previously computed relationships."""
    rels = db.query(Relationship).all()
    return _build_relationship_response(rels, db)


def _build_relationship_response(
    rels: list[Relationship], db: Session
) -> list[RelationshipOut]:
    """Helper to convert Relationship ORM objects to response schemas."""
    result = []
    # Cache document filenames
    doc_cache: dict[str, str] = {}

    for rel in rels:
        fact_a = db.query(Fact).filter(Fact.id == rel.fact_id_a).first()
        fact_b = db.query(Fact).filter(Fact.id == rel.fact_id_b).first()
        if not fact_a or not fact_b:
            continue

        for fact in (fact_a, fact_b):
            if fact.document_id not in doc_cache:
                doc = (
                    db.query(Document)
                    .filter(Document.id == fact.document_id)
                    .first()
                )
                doc_cache[fact.document_id] = doc.filename if doc else "Unknown"

        result.append(
            RelationshipOut(
                id=rel.id,
                fact_a=FactOut(
                    id=fact_a.id,
                    document_id=fact_a.document_id,
                    claim=fact_a.claim,
                    value=fact_a.value,
                    unit=fact_a.unit,
                    subject=fact_a.subject,
                    time_context=fact_a.time_context,
                    page_number=fact_a.page_number,
                    source_quote=fact_a.source_quote,
                    confidence=fact_a.confidence,
                    document_filename=doc_cache[fact_a.document_id],
                ),
                fact_b=FactOut(
                    id=fact_b.id,
                    document_id=fact_b.document_id,
                    claim=fact_b.claim,
                    value=fact_b.value,
                    unit=fact_b.unit,
                    subject=fact_b.subject,
                    time_context=fact_b.time_context,
                    page_number=fact_b.page_number,
                    source_quote=fact_b.source_quote,
                    confidence=fact_b.confidence,
                    document_filename=doc_cache[fact_b.document_id],
                ),
                rel_type=rel.rel_type,
                explanation=rel.explanation,
                context_detail=rel.context_detail,
            )
        )
    return result
