"use client";

/**
 * DocumentList — displays uploaded documents with their processing status.
 *
 * Each document row shows filename, page count, fact count, status badge,
 * and action buttons (process / delete).
 */

import { useState } from "react";
import {
  processDocument,
  deleteDocument,
  type DocumentInfo,
} from "@/lib/api";
import StatusBadge from "./StatusBadge";

interface DocumentListProps {
  documents: DocumentInfo[];
  onRefresh: () => void;
  onSelectDocument: (doc: DocumentInfo) => void;
}

export default function DocumentList({
  documents,
  onRefresh,
  onSelectDocument,
}: DocumentListProps) {
  const [processingId, setProcessingId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleProcess = async (docId: string) => {
    setProcessingId(docId);
    setError(null);
    try {
      await processDocument(docId);
      onRefresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Processing failed");
    } finally {
      setProcessingId(null);
    }
  };

  const handleDelete = async (docId: string) => {
    try {
      await deleteDocument(docId);
      onRefresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Delete failed");
    }
  };

  if (documents.length === 0) {
    return (
      <div
        className="glass-card animate-fade-in"
        style={{
          padding: "32px 24px",
          textAlign: "center",
        }}
      >
        <p style={{ color: "var(--text-tertiary)", fontSize: "13px" }}>
          📂 No documents uploaded yet. Upload a PDF to get started!
        </p>
      </div>
    );
  }

  return (
    <div className="animate-fade-in">
      {error && (
        <div
          style={{
            marginBottom: 10,
            padding: "8px 14px",
            borderRadius: "var(--radius-sm)",
            background: "var(--color-contradiction-dim)",
            color: "var(--color-contradiction)",
            fontSize: "13px",
            border: "1px solid var(--color-contradiction)",
          }}
        >
          ⚠️ {error}
        </div>
      )}

      <div className="stagger" style={{ display: "flex", flexDirection: "column", gap: 6 }}>
        {documents.map((doc) => (
          <div
            key={doc.id}
            className="glass-card"
            style={{
              padding: "12px 16px",
              display: "flex",
              alignItems: "center",
              gap: 12,
              cursor: doc.status === "processed" ? "pointer" : "default",
            }}
            onClick={() => {
              if (doc.status === "processed") onSelectDocument(doc);
            }}
          >
            {/* PDF Icon */}
            <div
              style={{
                width: 36,
                height: 36,
                borderRadius: "var(--radius-sm)",
                background: "var(--accent-blue-dim)",
                border: "1px solid var(--accent-blue)",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                flexShrink: 0,
                fontSize: "16px",
              }}
            >
              📄
            </div>

            {/* File info */}
            <div style={{ flex: 1, minWidth: 0 }}>
              <p
                style={{
                  fontWeight: 700,
                  fontSize: "13px",
                  overflow: "hidden",
                  textOverflow: "ellipsis",
                  whiteSpace: "nowrap",
                  color: "var(--accent-blue)",
                }}
              >
                {doc.filename}
              </p>
              <div
                style={{
                  display: "flex",
                  gap: 12,
                  marginTop: 3,
                  fontSize: "11px",
                  color: "var(--text-tertiary)",
                }}
              >
                {doc.page_count && <span>📃 {doc.page_count} pages</span>}
                {doc.fact_count > 0 && <span>📝 {doc.fact_count} facts</span>}
              </div>
            </div>

            {/* Status */}
            <StatusBadge status={doc.status} />

            {/* Actions */}
            <div
              style={{ display: "flex", gap: 6 }}
              onClick={(e) => e.stopPropagation()}
            >
              {(doc.status === "uploaded" || doc.status === "error") && (
                <button
                  className="btn-primary"
                  style={{ padding: "5px 12px", fontSize: "11px" }}
                  onClick={() => handleProcess(doc.id)}
                  disabled={processingId === doc.id}
                >
                  {processingId === doc.id ? (
                    <>
                      <svg
                        className="animate-spin-slow"
                        width="12"
                        height="12"
                        viewBox="0 0 24 24"
                        fill="none"
                        stroke="currentColor"
                        strokeWidth="2"
                      >
                        <path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83" />
                      </svg>
                      Extracting...
                    </>
                  ) : (
                    "⚡ Extract Facts"
                  )}
                </button>
              )}
              <button
                className="btn-danger"
                onClick={() => handleDelete(doc.id)}
                title="Delete document"
              >
                🗑️
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
