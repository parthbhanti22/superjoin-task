"""
PDF text extraction service using PyMuPDF.

Extracts text page-by-page from uploaded PDFs, preserving page numbers
for evidence grounding. Returns structured page data that the fact
extractor can use.
"""

from dataclasses import dataclass
from pathlib import Path

import fitz  # PyMuPDF


@dataclass
class PageText:
    """Text content from a single PDF page."""

    page_number: int  # 1-indexed
    text: str


@dataclass
class ParsedDocument:
    """Complete extraction result for a PDF."""

    filename: str
    page_count: int
    pages: list[PageText]


def extract_text_from_pdf(filepath: Path) -> ParsedDocument:
    """
    Extract text from every page of a PDF file.

    Args:
        filepath: Path to the PDF file on disk.

    Returns:
        ParsedDocument with page-by-page text and metadata.

    Raises:
        FileNotFoundError: If the PDF doesn't exist.
        fitz.FileDataError: If the file is not a valid PDF.
    """
    if not filepath.exists():
        raise FileNotFoundError(f"PDF not found: {filepath}")

    doc = fitz.open(str(filepath))
    pages: list[PageText] = []

    for page_num in range(len(doc)):
        page = doc[page_num]
        text = page.get_text("text")  # Plain text extraction

        # Skip pages with no meaningful text (e.g., blank or image-only)
        if text.strip():
            pages.append(
                PageText(
                    page_number=page_num + 1,  # 1-indexed for human readability
                    text=text.strip(),
                )
            )

    result = ParsedDocument(
        filename=filepath.name,
        page_count=len(doc),
        pages=pages,
    )

    doc.close()
    return result


def build_extraction_context(parsed: ParsedDocument) -> str:
    """
    Build a single text blob from parsed pages, with page markers.

    This format is sent to the LLM so it can reference page numbers
    in its source_quote fields.

    Args:
        parsed: The parsed document result.

    Returns:
        A formatted string with page delimiters.
    """
    sections = []
    for page in parsed.pages:
        sections.append(f"--- PAGE {page.page_number} ---\n{page.text}")
    return "\n\n".join(sections)
