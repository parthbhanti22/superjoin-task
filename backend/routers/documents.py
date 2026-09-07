"""
Document management endpoints — upload, list, and process PDFs.
"""

import logging
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile
from sqlalchemy.orm import Session

from config import ALLOWED_EXTENSIONS, MAX_UPLOAD_SIZE_MB, UPLOAD_DIR
from database import get_db
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
    # Validate file type
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")

    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Only PDF files are accepted. Got: {ext}",
        )

    # Read and validate file size
    content = await file.read()
    size_mb = len(content) / (1024 * 1024)
    if size_mb > MAX_UPLOAD_SIZE_MB:
        raise HTTPException(
            status_code=400,
            detail=f"File too large ({size_mb:.1f} MB). Max: {MAX_UPLOAD_SIZE_MB} MB",
        )

    # Save to uploads directory with a unique name to avoid collisions
    doc_id = str(uuid.uuid4())
    safe_filename = f"{doc_id}_{file.filename}"
    filepath = UPLOAD_DIR / safe_filename

    with open(filepath, "wb") as f:
        f.write(content)

    logger.info("Saved uploaded file: %s (%s MB)", safe_filename, f"{size_mb:.1f}")

    # Create database record
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
# Process a document (extract facts)
# ---------------------------------------------------------------------------
@router.post("/{document_id}/process", response_model=ProcessingStatus)
def process_document(document_id: str, db: Session = Depends(get_db)):
    """
    Trigger fact extraction on an uploaded document.

    This is a synchronous endpoint — it blocks until extraction is complete.
    For production, this would be an async job queue.
    """
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    if doc.status == "processing":
        raise HTTPException(status_code=409, detail="Document is already being processed")

    # Find the file on disk
    matching_files = list(UPLOAD_DIR.glob(f"{document_id}_*"))
    if not matching_files:
        raise HTTPException(status_code=404, detail="PDF file not found on disk")
    filepath = matching_files[0]

    # Update status to processing
    doc.status = "processing"
    doc.error_message = None
    db.commit()

    try:
        # Step 1: Extract text from PDF
        logger.info("Parsing PDF: %s", filepath.name)
        parsed = extract_text_from_pdf(filepath)
        doc.page_count = parsed.page_count

        # Step 2: Build text context for LLM
        context_text = build_extraction_context(parsed)

        # Step 3: Send to Groq for fact extraction
        logger.info("Extracting facts via Groq for: %s", doc.filename)
        extracted_facts = extract_facts(context_text, doc.filename)

        # Step 4: Clear any existing facts (re-processing)
        db.query(Fact).filter(Fact.document_id == document_id).delete()

        # Step 5: Store extracted facts
        for ef in extracted_facts:
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

        doc.status = "processed"
        db.commit()

        fact_count = db.query(Fact).filter(Fact.document_id == document_id).count()
        logger.info("Successfully extracted %d facts from %s", fact_count, doc.filename)

        return ProcessingStatus(
            document_id=document_id,
            status="processed",
            message=f"Successfully extracted {fact_count} facts",
            fact_count=fact_count,
        )

    except Exception as e:
        logger.error("Processing failed for %s: %s", doc.filename, e)
        doc.status = "error"
        doc.error_message = str(e)
        db.commit()
        raise HTTPException(status_code=500, detail=f"Processing failed: {e}")


# ---------------------------------------------------------------------------
# Delete a document
# ---------------------------------------------------------------------------
@router.delete("/{document_id}")
def delete_document(document_id: str, db: Session = Depends(get_db)):
    """Delete a document and all its associated facts."""
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    # Delete file from disk
    matching_files = list(UPLOAD_DIR.glob(f"{document_id}_*"))
    for f in matching_files:
        f.unlink(missing_ok=True)

    # Cascade delete removes facts
    db.delete(doc)
    db.commit()

    return {"message": f"Document '{doc.filename}' deleted"}
