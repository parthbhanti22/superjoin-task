"""
Fact retrieval endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from models import Document, Fact
from schemas import FactOut

router = APIRouter(prefix="/api", tags=["facts"])


@router.get("/documents/{document_id}/facts", response_model=list[FactOut])
def get_document_facts(document_id: str, db: Session = Depends(get_db)):
    """Return all extracted facts for a specific document."""
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    facts = (
        db.query(Fact)
        .filter(Fact.document_id == document_id)
        .order_by(Fact.page_number, Fact.id)
        .all()
    )

    return [
        FactOut(
            id=f.id,
            document_id=f.document_id,
            claim=f.claim,
            value=f.value,
            unit=f.unit,
            subject=f.subject,
            time_context=f.time_context,
            page_number=f.page_number,
            source_quote=f.source_quote,
            confidence=f.confidence,
            document_filename=doc.filename,
        )
        for f in facts
    ]


@router.get("/facts", response_model=list[FactOut])
def get_all_facts(db: Session = Depends(get_db)):
    """Return all extracted facts across all documents."""
    facts = db.query(Fact).order_by(Fact.document_id, Fact.page_number).all()
    result = []
    # Cache doc filenames to avoid N+1
    doc_cache: dict[str, str] = {}
    for f in facts:
        if f.document_id not in doc_cache:
            doc = db.query(Document).filter(Document.id == f.document_id).first()
            doc_cache[f.document_id] = doc.filename if doc else "Unknown"
        result.append(
            FactOut(
                id=f.id,
                document_id=f.document_id,
                claim=f.claim,
                value=f.value,
                unit=f.unit,
                subject=f.subject,
                time_context=f.time_context,
                page_number=f.page_number,
                source_quote=f.source_quote,
                confidence=f.confidence,
                document_filename=doc_cache[f.document_id],
            )
        )
    return result
