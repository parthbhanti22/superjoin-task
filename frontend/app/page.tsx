"use client";

/**
 * Dashboard — main page of the Fact Knowledge Layer.
 *
 * Three-tab layout:
 *   1. Documents — upload and manage PDFs
 *   2. Facts — view extracted facts (per-document or all)
 *   3. Relationships — cross-document analysis results
 */

import { useCallback, useEffect, useState } from "react";
import {
  listDocuments,
  getDocumentFacts,
  getAllFacts,
  getRelationships,
  analyzeRelationships,
  type DocumentInfo,
  type FactInfo,
  type RelationshipInfo,
} from "@/lib/api";
import UploadPanel from "./components/UploadPanel";
import DocumentList from "./components/DocumentList";
import FactsTable from "./components/FactsTable";
import RelationshipCard from "./components/RelationshipCard";

type Tab = "documents" | "facts" | "relationships";

export default function Dashboard() {
  // ---------------------------------------------------------------------------
  // State
  // ---------------------------------------------------------------------------
  const [activeTab, setActiveTab] = useState<Tab>("documents");
  const [documents, setDocuments] = useState<DocumentInfo[]>([]);
  const [facts, setFacts] = useState<FactInfo[]>([]);
  const [relationships, setRelationships] = useState<RelationshipInfo[]>([]);
  const [selectedDoc, setSelectedDoc] = useState<DocumentInfo | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysisError, setAnalysisError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  // ---------------------------------------------------------------------------
  // Data fetching
  // ---------------------------------------------------------------------------
  const refreshDocuments = useCallback(async () => {
    try {
      const docs = await listDocuments();
      setDocuments(docs);
    } catch {
      // silently fail — API may not be ready
    }
  }, []);

  const refreshFacts = useCallback(async (docId?: string) => {
    try {
      const data = docId ? await getDocumentFacts(docId) : await getAllFacts();
      setFacts(data);
    } catch {
      setFacts([]);
    }
  }, []);

  const refreshRelationships = useCallback(async () => {
    try {
      const data = await getRelationships();
      setRelationships(data);
    } catch {
      setRelationships([]);
    }
  }, []);

  // Initial load
  useEffect(() => {
    Promise.all([refreshDocuments(), refreshRelationships()]).finally(() =>
      setLoading(false)
    );
  }, [refreshDocuments, refreshRelationships]);

  // Load facts when tab changes or document is selected
  useEffect(() => {
    if (activeTab === "facts") {
      refreshFacts(selectedDoc?.id);
    }
  }, [activeTab, selectedDoc, refreshFacts]);

  // ---------------------------------------------------------------------------
  // Polling — auto-refresh documents and facts every 3 seconds
  // ---------------------------------------------------------------------------
  useEffect(() => {
    const interval = setInterval(() => {
      refreshDocuments();
      if (activeTab === "facts") {
        refreshFacts(selectedDoc?.id);
      }
    }, 3000);
    return () => clearInterval(interval);
  }, [activeTab, selectedDoc, refreshDocuments, refreshFacts]);

  // ---------------------------------------------------------------------------
  // Handlers
  // ---------------------------------------------------------------------------
  const handleUploadComplete = useCallback(
    (doc: DocumentInfo) => {
      setDocuments((prev) => [doc, ...prev]);
    },
    []
  );

  const handleSelectDocument = useCallback(
    (doc: DocumentInfo) => {
      setSelectedDoc(doc);
      setActiveTab("facts");
      refreshFacts(doc.id);
    },
    [refreshFacts]
  );

  const handleAnalyze = useCallback(async () => {
    setIsAnalyzing(true);
    setAnalysisError(null);
    try {
      const data = await analyzeRelationships();
      setRelationships(data);
    } catch (err) {
      setAnalysisError(
        err instanceof Error ? err.message : "Analysis failed"
      );
    } finally {
      setIsAnalyzing(false);
    }
  }, []);

  // Count processed docs
  const processedCount = documents.filter(
    (d) => d.status === "processed"
  ).length;

  // Group relationships by type for display
  const relByType = {
    corroboration: relationships.filter((r) => r.rel_type === "corroboration"),
    contradiction: relationships.filter((r) => r.rel_type === "contradiction"),
    contextual_difference: relationships.filter(
      (r) => r.rel_type === "contextual_difference"
    ),
    extraction_failure: relationships.filter(
      (r) => r.rel_type === "extraction_failure"
    ),
  };

  // ---------------------------------------------------------------------------
  // Render
  // ---------------------------------------------------------------------------
  return (
    <div
      style={{
        maxWidth: 960,
        margin: "0 auto",
        padding: "24px 16px",
        width: "100%",
      }}
    >
      {/* ═══ Retro Header ═══ */}
      <header className="animate-slide-up" style={{ marginBottom: 24, textAlign: "center" }}>
        <div style={{
          background: "linear-gradient(180deg, #333366, #1a1a2e)",
          padding: "16px 24px",
          borderRadius: "var(--radius-md)",
          border: "2px outset #6666aa",
          marginBottom: 8,
        }}>
          <h1 style={{
            fontSize: "28px",
            fontFamily: "var(--font-display)",
            fontWeight: 900,
            letterSpacing: "2px",
            textTransform: "uppercase",
            margin: 0,
          }}>
            <span className="animate-rainbow">✦ Fact Knowledge Layer ✦</span>
          </h1>
          <p style={{
            color: "#ccccff",
            fontSize: "12px",
            marginTop: 6,
            fontFamily: "var(--font-sans)",
          }}>
            Upload documents · Extract grounded facts · Discover cross-document relationships
          </p>
        </div>

        {/* Retro visitor counter */}
        <div style={{
          display: "flex",
          justifyContent: "center",
          alignItems: "center",
          gap: 12,
          marginTop: 8,
          fontSize: "11px",
          color: "var(--text-tertiary)",
        }}>
          <span>📊 {documents.length} docs uploaded</span>
          <span>·</span>
          <span>📝 {facts.length} facts extracted</span>
          <span>·</span>
          <span>🔗 {relationships.length} relationships found</span>
        </div>

        <div className="retro-hr" />
      </header>

      {/* ═══ Tab Navigation — Classic early-web tab bar ═══ */}
      <nav
        style={{
          display: "flex",
          gap: 2,
          marginBottom: 20,
        }}
      >
        {(
          [
            { key: "documents" as Tab, label: "📁 Documents", count: documents.length },
            { key: "facts" as Tab, label: "📝 Facts", count: facts.length },
            { key: "relationships" as Tab, label: "🔗 Relationships", count: relationships.length },
          ] as const
        ).map((tab) => (
          <button
            key={tab.key}
            onClick={() => {
              setActiveTab(tab.key);
              if (tab.key === "facts" && !selectedDoc) refreshFacts();
              if (tab.key === "relationships") refreshRelationships();
            }}
            style={{
              padding: "8px 18px",
              fontSize: "13px",
              fontWeight: 700,
              fontFamily: "var(--font-sans)",
              border: activeTab === tab.key
                ? "2px solid var(--border-subtle)"
                : "2px outset #ccccbb",
              borderBottom: activeTab === tab.key
                ? "2px solid var(--bg-primary)"
                : "2px solid var(--border-subtle)",
              background: activeTab === tab.key
                ? "var(--bg-primary)"
                : "linear-gradient(180deg, #f0f0e8, #d8d8cc)",
              color: activeTab === tab.key
                ? "var(--accent-blue)"
                : "var(--text-tertiary)",
              cursor: "pointer",
              borderRadius: "var(--radius-sm) var(--radius-sm) 0 0",
              position: "relative",
              top: activeTab === tab.key ? 2 : 0,
            }}
          >
            {tab.label}
            {tab.count > 0 && (
              <span
                style={{
                  marginLeft: 6,
                  fontSize: "11px",
                  padding: "1px 5px",
                  borderRadius: "var(--radius-sm)",
                  background: activeTab === tab.key
                    ? "var(--accent-blue-dim)"
                    : "var(--bg-tertiary)",
                  color: activeTab === tab.key
                    ? "var(--accent-blue)"
                    : "var(--text-tertiary)",
                  border: "1px solid currentColor",
                }}
              >
                {tab.count}
              </span>
            )}
          </button>
        ))}
      </nav>

      {/* Content area with classic border */}
      <div style={{
        border: "2px solid var(--border-subtle)",
        borderTop: "none",
        borderRadius: "0 0 var(--radius-md) var(--radius-md)",
        padding: "20px",
        background: "var(--bg-primary)",
        minHeight: 300,
      }}>
        {/* Loading state */}
        {loading && (
          <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
            <div className="skeleton" style={{ height: 64, width: "100%" }} />
            <div className="skeleton" style={{ height: 64, width: "100%" }} />
            <div className="skeleton" style={{ height: 64, width: "80%" }} />
          </div>
        )}

        {/* Tab Content */}
        {!loading && (
          <>
            {/* ─── Documents Tab ─── */}
            {activeTab === "documents" && (
              <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>
                <UploadPanel onUploadComplete={handleUploadComplete} />
                <DocumentList
                  documents={documents}
                  onRefresh={refreshDocuments}
                  onSelectDocument={handleSelectDocument}
                />
              </div>
            )}

            {/* ─── Facts Tab ─── */}
            {activeTab === "facts" && (
              <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
                {/* Sub-navigation: all facts vs. specific document */}
                <div style={{ display: "flex", gap: 6, alignItems: "center", flexWrap: "wrap" }}>
                  <button
                    className={selectedDoc ? "btn-secondary" : "btn-primary"}
                    style={{ padding: "5px 12px", fontSize: "12px" }}
                    onClick={() => {
                      setSelectedDoc(null);
                      refreshFacts();
                    }}
                  >
                    All Facts
                  </button>
                  {documents
                    .filter((d) => d.status === "processed" || d.status === "processing")
                    .map((doc) => (
                      <button
                        key={doc.id}
                        className={
                          selectedDoc?.id === doc.id
                            ? "btn-primary"
                            : "btn-secondary"
                        }
                        style={{ padding: "5px 12px", fontSize: "12px" }}
                        onClick={() => {
                          setSelectedDoc(doc);
                          refreshFacts(doc.id);
                        }}
                      >
                        {doc.filename.length > 30
                          ? doc.filename.slice(0, 27) + "..."
                          : doc.filename}
                      </button>
                    ))}
                </div>

                <FactsTable
                  facts={facts}
                  documentFilename={
                    selectedDoc ? selectedDoc.filename : "All Documents"
                  }
                />
              </div>
            )}

            {/* ─── Relationships Tab ─── */}
            {activeTab === "relationships" && (
              <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
                {/* Analysis controls */}
                <div
                  className="glass-card"
                  style={{
                    padding: "14px 20px",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "space-between",
                  }}
                >
                  <div>
                    <p style={{ fontWeight: 700, fontSize: "14px" }}>
                      🔍 Cross-Document Analysis
                    </p>
                    <p
                      style={{
                        fontSize: "12px",
                        color: "var(--text-tertiary)",
                        marginTop: 2,
                      }}
                    >
                      {processedCount} processed document{processedCount !== 1 ? "s" : ""} available
                    </p>
                  </div>
                  <button
                    className="btn-primary"
                    onClick={handleAnalyze}
                    disabled={processedCount < 2 || isAnalyzing}
                  >
                    {isAnalyzing ? (
                      <>
                        <svg
                          className="animate-spin-slow"
                          width="14"
                          height="14"
                          viewBox="0 0 24 24"
                          fill="none"
                          stroke="currentColor"
                          strokeWidth="2"
                        >
                          <path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83" />
                        </svg>
                        Analyzing...
                      </>
                    ) : (
                      "⚡ Analyze Relationships"
                    )}
                  </button>
                </div>

                {analysisError && (
                  <div
                    style={{
                      padding: "10px 14px",
                      borderRadius: "var(--radius-sm)",
                      background: "var(--color-contradiction-dim)",
                      color: "var(--color-contradiction)",
                      fontSize: "13px",
                      border: "1px solid var(--color-contradiction)",
                    }}
                  >
                    ⚠️ {analysisError}
                  </div>
                )}

                {/* Summary counters */}
                {relationships.length > 0 && (
                  <div
                    style={{
                      display: "grid",
                      gridTemplateColumns: "repeat(4, 1fr)",
                      gap: 8,
                    }}
                  >
                    {(
                      [
                        {
                          type: "corroboration",
                          label: "✓ Corroborations",
                          color: "var(--color-corroboration)",
                          count: relByType.corroboration.length,
                        },
                        {
                          type: "contradiction",
                          label: "✗ Contradictions",
                          color: "var(--color-contradiction)",
                          count: relByType.contradiction.length,
                        },
                        {
                          type: "contextual_difference",
                          label: "◐ Contextual",
                          color: "var(--color-contextual)",
                          count: relByType.contextual_difference.length,
                        },
                        {
                          type: "extraction_failure",
                          label: "⚠ Failures",
                          color: "var(--color-failure)",
                          count: relByType.extraction_failure.length,
                        },
                      ] as const
                    ).map((item) => (
                      <div
                        key={item.type}
                        className="glass-card"
                        style={{
                          padding: "12px",
                          textAlign: "center",
                          borderTop: `3px solid ${item.color}`,
                        }}
                      >
                        <p
                          style={{
                            fontSize: "24px",
                            fontWeight: 900,
                            color: item.color,
                            fontFamily: "var(--font-mono)",
                          }}
                        >
                          {item.count}
                        </p>
                        <p
                          style={{
                            fontSize: "11px",
                            color: "var(--text-tertiary)",
                            marginTop: 2,
                            fontWeight: 700,
                          }}
                        >
                          {item.label}
                        </p>
                      </div>
                    ))}
                  </div>
                )}

                {/* Empty state */}
                {relationships.length === 0 && !isAnalyzing && (
                  <div
                    className="glass-card"
                    style={{
                      padding: "32px 24px",
                      textAlign: "center",
                    }}
                  >
                    <p style={{ color: "var(--text-tertiary)", fontSize: "13px" }}>
                      {processedCount < 2
                        ? "📤 Upload and process at least 2 documents, then analyze their relationships."
                        : "👆 Click 'Analyze Relationships' to start cross-document comparison."}
                    </p>
                  </div>
                )}

                <div className="stagger" style={{ display: "flex", flexDirection: "column", gap: 12 }}>
                  {relationships.map((rel) => (
                    <RelationshipCard key={rel.id} relationship={rel} />
                  ))}
                </div>
              </div>
            )}
          </>
        )}
      </div>

      {/* ═══ Retro Footer ═══ */}
      <footer style={{
        textAlign: "center",
        marginTop: 24,
        padding: "12px",
        fontSize: "11px",
        color: "var(--text-tertiary)",
        borderTop: "1px dashed var(--border-subtle)",
      }}>
        <p>
          🌐 Best viewed in Netscape Navigator 4.0+ at 1024×768 resolution
        </p>
        <p style={{ marginTop: 4 }}>
          Made with ❤️ and ☕ · Powered by <b>Groq</b> + <b>Llama 3.3</b> ·{" "}
          <span className="animate-blink" style={{ color: "var(--accent-hot-pink)" }}>NEW!</span>
        </p>
      </footer>
    </div>
  );
}
