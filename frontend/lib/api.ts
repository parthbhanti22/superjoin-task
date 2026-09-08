/**
 * API client for the Fact Knowledge Layer backend.
 *
 * All API calls go through the Next.js rewrite proxy (/api/* -> localhost:8000/api/*),
 * so we never hardcode the backend URL in the browser.
 */

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------
export interface DocumentInfo {
  id: string;
  filename: string;
  upload_time: string;
  page_count: number | null;
  status: "uploaded" | "processing" | "processed" | "error";
  error_message: string | null;
  fact_count: number;
}

export interface FactInfo {
  id: string;
  document_id: string;
  claim: string;
  value: string | null;
  unit: string | null;
  subject: string | null;
  time_context: string | null;
  page_number: number | null;
  source_quote: string;
  confidence: number;
  document_filename: string | null;
}

export interface RelationshipInfo {
  id: string;
  fact_a: FactInfo;
  fact_b: FactInfo;
  rel_type:
    | "corroboration"
    | "contradiction"
    | "contextual_difference"
    | "extraction_failure";
  explanation: string;
  context_detail: string | null;
}

export interface ProcessingStatus {
  document_id: string;
  status: string;
  message: string;
  fact_count: number;
}

// ---------------------------------------------------------------------------
// API functions
// ---------------------------------------------------------------------------

const API_BASE = "/api";

/**
 * Upload a PDF file.
 */
export async function uploadDocument(file: File): Promise<DocumentInfo> {
  const formData = new FormData();
  formData.append("file", file);
  const res = await fetch(`${API_BASE}/documents/upload`, {
    method: "POST",
    body: formData,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || "Upload failed");
  }
  return res.json();
}

/**
 * List all documents.
 */
export async function listDocuments(): Promise<DocumentInfo[]> {
  const res = await fetch(`${API_BASE}/documents`);
  if (!res.ok) throw new Error("Failed to list documents");
  return res.json();
}

/**
 * Trigger fact extraction on a document.
 */
export async function processDocument(
  documentId: string
): Promise<ProcessingStatus> {
  const res = await fetch(`${API_BASE}/documents/${documentId}/process`, {
    method: "POST",
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || "Processing failed");
  }
  return res.json();
}

/**
 * Get extracted facts for a specific document.
 */
export async function getDocumentFacts(
  documentId: string
): Promise<FactInfo[]> {
  const res = await fetch(`${API_BASE}/documents/${documentId}/facts`);
  if (!res.ok) throw new Error("Failed to fetch facts");
  return res.json();
}

/**
 * Get all facts across all documents.
 */
export async function getAllFacts(): Promise<FactInfo[]> {
  const res = await fetch(`${API_BASE}/facts`);
  if (!res.ok) throw new Error("Failed to fetch facts");
  return res.json();
}

/**
 * Trigger cross-document relationship analysis.
 */
export async function analyzeRelationships(): Promise<RelationshipInfo[]> {
  const res = await fetch(`${API_BASE}/relationships/analyze`, {
    method: "POST",
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || "Analysis failed");
  }
  return res.json();
}

/**
 * Get previously computed relationships.
 */
export async function getRelationships(): Promise<RelationshipInfo[]> {
  const res = await fetch(`${API_BASE}/relationships`);
  if (!res.ok) throw new Error("Failed to fetch relationships");
  return res.json();
}

/**
 * Delete a document.
 */
export async function deleteDocument(
  documentId: string
): Promise<{ message: string }> {
  const res = await fetch(`${API_BASE}/documents/${documentId}`, {
    method: "DELETE",
  });
  if (!res.ok) throw new Error("Failed to delete document");
  return res.json();
}
