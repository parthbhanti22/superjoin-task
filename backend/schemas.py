"""
Pydantic schemas for API request validation and response serialization.
"""

from datetime import datetime

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Document schemas
# ---------------------------------------------------------------------------
class DocumentOut(BaseModel):
    """Response schema for a document record."""

    id: str
    filename: str
    upload_time: datetime
    page_count: int | None = None
    status: str
    error_message: str | None = None
    fact_count: int = 0

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Fact schemas
# ---------------------------------------------------------------------------
class FactOut(BaseModel):
    """Response schema for an extracted fact."""

    id: str
    document_id: str
    claim: str
    value: str | None = None
    unit: str | None = None
    subject: str | None = None
    time_context: str | None = None
    page_number: int | None = None
    source_quote: str
    confidence: float = 1.0
    document_filename: str | None = None  # Populated in the router

    model_config = {"from_attributes": True}


class FactExtraction(BaseModel):
    """Schema for a single fact extracted by the LLM."""

    claim: str = Field(description="The factual claim being stated")
    value: str | None = Field(
        None, description="Numeric or quantitative value, if applicable"
    )
    unit: str | None = Field(None, description="Unit of the value (e.g., %, USD, kg)")
    subject: str = Field(description="What the fact is about")
    time_context: str | None = Field(
        None, description="Time period or date the fact refers to"
    )
    page_number: int | None = Field(
        None, description="Page number in the source document"
    )
    source_quote: str = Field(
        description="Exact verbatim quote from the source text supporting this fact"
    )
    confidence: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Confidence in the accuracy of this extraction",
    )


class FactExtractionResponse(BaseModel):
    """Wrapper for the LLM's fact extraction output."""

    facts: list[FactExtraction]


# ---------------------------------------------------------------------------
# Relationship schemas
# ---------------------------------------------------------------------------
class RelationshipOut(BaseModel):
    """Response schema for a cross-document relationship."""

    id: str
    fact_a: FactOut
    fact_b: FactOut
    rel_type: str
    explanation: str
    context_detail: str | None = None

    model_config = {"from_attributes": True}


class RelationshipExtraction(BaseModel):
    """Schema for a single relationship identified by the LLM."""

    fact_id_a: str = Field(description="ID of the first fact")
    fact_id_b: str = Field(description="ID of the second fact")
    rel_type: str = Field(
        description=(
            "Type of relationship: corroboration, contradiction, "
            "contextual_difference, or extraction_failure"
        )
    )
    explanation: str = Field(description="Why this relationship was identified")
    context_detail: str | None = Field(
        None,
        description="For contextual_difference: what context resolves the difference",
    )


class RelationshipAnalysisResponse(BaseModel):
    """Wrapper for the LLM's relationship analysis output."""

    relationships: list[RelationshipExtraction]


# ---------------------------------------------------------------------------
# Processing status
# ---------------------------------------------------------------------------
class ProcessingStatus(BaseModel):
    """Status of an async processing job."""

    document_id: str
    status: str
    message: str = ""
    fact_count: int = 0
