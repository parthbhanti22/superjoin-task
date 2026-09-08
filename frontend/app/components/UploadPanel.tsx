"use client";

/**
 * UploadPanel — drag-and-drop PDF upload with visual feedback.
 *
 * Supports both click-to-browse and drag-and-drop interactions.
 * Shows upload progress and error states.
 */

import { useCallback, useRef, useState } from "react";
import { uploadDocument, type DocumentInfo } from "@/lib/api";

interface UploadPanelProps {
  onUploadComplete: (doc: DocumentInfo) => void;
}

export default function UploadPanel({ onUploadComplete }: UploadPanelProps) {
  const [isDragOver, setIsDragOver] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFile = useCallback(
    async (file: File) => {
      if (!file.name.toLowerCase().endsWith(".pdf")) {
        setError("Only PDF files are accepted");
        return;
      }

      setError(null);
      setIsUploading(true);

      try {
        const doc = await uploadDocument(file);
        onUploadComplete(doc);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Upload failed");
      } finally {
        setIsUploading(false);
      }
    },
    [onUploadComplete]
  );

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setIsDragOver(false);

      const file = e.dataTransfer.files[0];
      if (file) handleFile(file);
    },
    [handleFile]
  );

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(true);
  }, []);

  const handleDragLeave = useCallback(() => {
    setIsDragOver(false);
  }, []);

  const handleClick = useCallback(() => {
    fileInputRef.current?.click();
  }, []);

  const handleInputChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0];
      if (file) handleFile(file);
      // Reset so the same file can be re-uploaded
      e.target.value = "";
    },
    [handleFile]
  );

  return (
    <div className="animate-fade-in">
      <div
        className={`drop-zone ${isDragOver ? "drag-over" : ""}`}
        onDrop={handleDrop}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onClick={handleClick}
        role="button"
        tabIndex={0}
        aria-label="Upload PDF"
      >
        <input
          ref={fileInputRef}
          type="file"
          accept=".pdf"
          className="hidden"
          onChange={handleInputChange}
        />

        {isUploading ? (
          <div className="flex flex-col items-center gap-3">
            {/* Spinner */}
            <svg
              className="animate-spin-slow"
              width="40"
              height="40"
              viewBox="0 0 24 24"
              fill="none"
              stroke="var(--accent-blue)"
              strokeWidth="2"
            >
              <path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83" />
            </svg>
            <p style={{ color: "var(--text-secondary)" }}>Uploading...</p>
          </div>
        ) : (
          <div className="flex flex-col items-center gap-3">
            {/* Upload icon */}
            <svg
              width="48"
              height="48"
              viewBox="0 0 24 24"
              fill="none"
              stroke={isDragOver ? "var(--accent-blue)" : "var(--text-tertiary)"}
              strokeWidth="1.5"
              style={{ transition: "stroke 0.2s ease" }}
            >
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
              <polyline points="17 8 12 3 7 8" />
              <line x1="12" y1="3" x2="12" y2="15" />
            </svg>
            <div>
              <p style={{ color: "var(--text-primary)", fontWeight: 500 }}>
                Drop a PDF here or click to browse
              </p>
              <p
                style={{
                  color: "var(--text-tertiary)",
                  fontSize: "0.8rem",
                  marginTop: 4,
                }}
              >
                Maximum file size: 50 MB
              </p>
            </div>
          </div>
        )}
      </div>

      {error && (
        <div
          className="animate-fade-in"
          style={{
            marginTop: 12,
            padding: "10px 16px",
            borderRadius: "var(--radius-md)",
            background: "var(--color-contradiction-dim)",
            color: "var(--color-contradiction)",
            fontSize: "0.85rem",
          }}
        >
          {error}
        </div>
      )}
    </div>
  );
}
