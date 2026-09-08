"""
Document management endpoints — upload, list, and process PDFs.
"""

import logging
import uuid
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, UploadFile
from sqlalchemy.orm import Session

from config import ALLOWED_EXTENSIONS, MAX_UPLOAD_SIZE_MB, UPLOAD_DIR
from database import get_db, SessionLocal
from models import Document, Fact
from schemas import DocumentOut, ProcessingStatus
from services.fact_extractor import extract_facts
from services.pdf_parser import build_extraction_context, extract_text_from_pdf

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/documents", tags=["documents"])


# ---------------------------------------------------------------------------
# Upload a PDF
# ---------------------------------------------------------------------------
@router.post("/upload", response_model=DocumentOut)
async def upload_document(file: UploadFile, db: Session = Depends(get_db)):
    """
    Upload a PDF file for processing.

    The file is saved to disk and a document record is created.
    Processing is NOT triggered automatically — call /process separately.
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")

    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Only PDF files are accepted. Got: {ext}",
        )

    content = await file.read()
    size_mb = len(content) / (1024 * 1024)
    if size_mb > MAX_UPLOAD_SIZE_MB:
        raise HTTPException(
            status_code=400,
            detail=f"File too large ({size_mb:.1f} MB). Max: {MAX_UPLOAD_SIZE_MB} MB",
        )

    doc_id = str(uuid.uuid4())
    safe_filename = f"{doc_id}_{file.filename}"
    filepath = UPLOAD_DIR / safe_filename

    with open(filepath, "wb") as f:
        f.write(content)

    logger.info("Saved uploaded file: %s (%s MB)", safe_filename, f"{size_mb:.1f}")

    doc = Document(
        id=doc_id,
        filename=file.filename,
        status="uploaded",
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    return DocumentOut(
        id=doc.id,
        filename=doc.filename,
        upload_time=doc.upload_time,
        page_count=doc.page_count,
        status=doc.status,
        fact_count=0,
    )


# ---------------------------------------------------------------------------
# List all documents
# ---------------------------------------------------------------------------
@router.get("", response_model=list[DocumentOut])
def list_documents(db: Session = Depends(get_db)):
    """Return all uploaded documents with their processing status."""
    docs = db.query(Document).order_by(Document.upload_time.desc()).all()
    result = []
    for doc in docs:
        fact_count = db.query(Fact).filter(Fact.document_id == doc.id).count()
        result.append(
            DocumentOut(
                id=doc.id,
                filename=doc.filename,
                upload_time=doc.upload_time,
                page_count=doc.page_count,
                status=doc.status,
                error_message=doc.error_message,
                fact_count=fact_count,
            )
        )
    return result


# ---------------------------------------------------------------------------
# Background processing task
# ---------------------------------------------------------------------------
def _process_document_bg(document_id: str, filepath: Path, filename: str):
    """Background task: extract facts chunk-by-chunk and commit them incrementally."""
    db = SessionLocal()
    try:
        doc = db.query(Document).filter(Document.id == document_id).first()
        if not doc:
            return

        logger.info("Parsing PDF: %s", filepath.name)
        parsed = extract_text_from_pdf(filepath)
        doc.page_count = parsed.page_count
        db.commit()

        context_text = build_extraction_context(parsed)

        logger.info("Extracting facts via Groq for: %s", doc.filename)
        fact_generator = extract_facts(context_text, doc.filename)

        total_extracted = 0
        for chunk_facts in fact_generator:
            if not chunk_facts:
                continue

            for ef in chunk_facts:
                fact = Fact(
                    document_id=document_id,
                    claim=ef.claim,
                    value=ef.value,
                    unit=ef.unit,
                    subject=ef.subject,
                    time_context=ef.time_context,
                    page_number=ef.page_number,
                    source_quote=ef.source_quote,
                    confidence=ef.confidence,
                )
                db.add(fact)

            db.commit()
            total_extracted += len(chunk_facts)
            logger.info(
                "Committed %d facts (total: %d) for '%s'",
                len(chunk_facts), total_extracted, filename,
            )

        doc.status = "processed"
        db.commit()
        logger.info(
            "Finished processing %s. Total facts: %d",
            doc.filename, total_extracted,
        )

    except Exception as e:
        logger.error("Processing failed for %s: %s", filename, e)
        doc = db.query(Document).filter(Document.id == document_id).first()
        if doc:
            doc.status = "error"
            doc.error_message = str(e)
            db.commit()
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Process a document (extract facts) — runs in background
# ---------------------------------------------------------------------------
@router.post("/{document_id}/process", response_model=ProcessingStatus)
def process_document(
    document_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """
    Trigger fact extraction on an uploaded document.
    Returns immediately — extraction runs in the background.
    """
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    if doc.status == "processing":
        raise HTTPException(status_code=409, detail="Document is already being processed")

    matching_files = list(UPLOAD_DIR.glob(f"{document_id}_*"))
    if not matching_files:
        raise HTTPException(status_code=404, detail="PDF file not found on disk")
    filepath = matching_files[0]

    doc.status = "processing"
    doc.error_message = None
    db.query(Fact).filter(Fact.document_id == document_id).delete()
    db.commit()

    background_tasks.add_task(_process_document_bg, document_id, filepath, doc.filename)

    return ProcessingStatus(
        document_id=document_id,
        status="processing",
        message="Fact extraction started in background",
        fact_count=0,
    )


# ---------------------------------------------------------------------------
# Delete a document
# ---------------------------------------------------------------------------
@router.delete("/{document_id}")
def delete_document(document_id: str, db: Session = Depends(get_db)):
    """Delete a document and all its associated facts."""
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    matching_files = list(UPLOAD_DIR.glob(f"{document_id}_*"))
    for f in matching_files:
        f.unlink(missing_ok=True)

    db.delete(doc)
    db.commit()

    return {"message": f"Document '{doc.filename}' deleted"}
