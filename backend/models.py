"""
SQLAlchemy ORM models for the Fact Knowledge Layer.

Three tables:
  - documents: uploaded PDF metadata and processing status
  - facts: extracted factual claims, each grounded to source evidence
  - relationships: cross-document fact comparisons
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base


def _generate_uuid() -> str:
    return str(uuid.uuid4())


class Document(Base):
    """An uploaded PDF document."""

    __tablename__ = "documents"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=_generate_uuid
    )
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    upload_time: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
    page_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    status: Mapped[str] = mapped_column(
        String(20), default="uploaded"
    )  # uploaded | processing | processed | error
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    facts: Mapped[list["Fact"]] = relationship(
        back_populates="document", cascade="all, delete-orphan"
    )


class Fact(Base):
    """A single factual claim extracted from a document, with source evidence."""

    __tablename__ = "facts"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=_generate_uuid
    )
    document_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("documents.id"), nullable=False
    )
    claim: Mapped[str] = mapped_column(Text, nullable=False)
    value: Mapped[str | None] = mapped_column(String(100), nullable=True)
    unit: Mapped[str | None] = mapped_column(String(50), nullable=True)
    subject: Mapped[str | None] = mapped_column(String(255), nullable=True)
    time_context: Mapped[str | None] = mapped_column(String(100), nullable=True)
    page_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    source_quote: Mapped[str] = mapped_column(Text, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, default=1.0)

    # Relationships
    document: Mapped["Document"] = relationship(back_populates="facts")


class Relationship(Base):
    """A cross-document relationship between two facts."""

    __tablename__ = "relationships"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=_generate_uuid
    )
    fact_id_a: Mapped[str] = mapped_column(
        String(36), ForeignKey("facts.id"), nullable=False
    )
    fact_id_b: Mapped[str] = mapped_column(
        String(36), ForeignKey("facts.id"), nullable=False
    )
    rel_type: Mapped[str] = mapped_column(
        String(30), nullable=False
    )  # corroboration | contradiction | contextual_difference | extraction_failure
    explanation: Mapped[str] = mapped_column(Text, nullable=False)
    context_detail: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Eager-load both facts for display
    fact_a: Mapped["Fact"] = relationship(foreign_keys=[fact_id_a])
    fact_b: Mapped["Fact"] = relationship(foreign_keys=[fact_id_b])
