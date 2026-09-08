"use client";

/**
 * FactsTable — displays extracted facts in a table with expandable source quotes.
 *
 * Each row shows claim, subject, value, time context, page, and confidence.
 * Clicking a row expands it to show the verbatim source quote.
 */

import { useState } from "react";
import type { FactInfo } from "@/lib/api";

interface FactsTableProps {
  facts: FactInfo[];
  documentFilename?: string;
}

export default function FactsTable({ facts, documentFilename }: FactsTableProps) {
  const [expandedId, setExpandedId] = useState<string | null>(null);

  if (facts.length === 0) {
    return (
      <div
        className="glass-card"
        style={{ padding: "32px 24px", textAlign: "center" }}
      >
        <p style={{ color: "var(--text-tertiary)", fontSize: "13px" }}>
          📝 No facts extracted yet.
        </p>
      </div>
    );
  }

  return (
    <div
      className="glass-card animate-fade-in"
      style={{ overflow: "hidden" }}
    >
      {documentFilename && (
        <div
          style={{
            padding: "10px 16px",
            borderBottom: "2px solid var(--border-subtle)",
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            background: "linear-gradient(180deg, #f0f0e8, #e8e8d8)",
          }}
        >
          <h3 style={{ fontSize: "13px", fontWeight: 700 }}>
            📋 {documentFilename}
          </h3>
          <span
            style={{
              fontSize: "11px",
              color: "var(--text-tertiary)",
              fontFamily: "var(--font-mono)",
            }}
          >
            {facts.length} facts
          </span>
        </div>
      )}

      <div style={{ overflowX: "auto", maxHeight: "70vh", overflowY: "auto" }}>
        <table className="facts-table">
          <thead>
            <tr>
              <th style={{ width: "35%" }}>Claim</th>
              <th>Subject</th>
              <th>Value</th>
              <th>Time</th>
              <th>Pg</th>
              <th>Conf</th>
            </tr>
          </thead>
          <tbody>
            {facts.map((fact) => (
              <>
                <tr
                  key={fact.id}
                  onClick={() =>
                    setExpandedId(expandedId === fact.id ? null : fact.id)
                  }
                  style={{ cursor: "pointer" }}
                >
                  <td style={{ color: "var(--text-primary)", fontWeight: 600 }}>
                    {fact.claim}
                  </td>
                  <td>
                    {fact.subject && (
                      <span
                        style={{
                          padding: "1px 6px",
                          borderRadius: "var(--radius-sm)",
                          background: "var(--accent-blue-dim)",
                          color: "var(--accent-blue)",
                          fontSize: "11px",
                          fontWeight: 700,
                          border: "1px solid var(--accent-blue)",
                        }}
                      >
                        {fact.subject}
                      </span>
                    )}
                  </td>
                  <td>
                    {fact.value && (
                      <span style={{ fontFamily: "var(--font-mono)", fontSize: "12px" }}>
                        {fact.value}
                        {fact.unit && (
                          <span style={{ color: "var(--text-tertiary)", marginLeft: 2 }}>
                            {fact.unit}
                          </span>
                        )}
                      </span>
                    )}
                  </td>
                  <td style={{ fontSize: "12px", whiteSpace: "nowrap" }}>
                    {fact.time_context || "—"}
                  </td>
                  <td style={{ fontFamily: "var(--font-mono)", fontSize: "12px" }}>
                    {fact.page_number || "—"}
                  </td>
                  <td>
                    <ConfidenceDot confidence={fact.confidence} />
                  </td>
                </tr>
                {expandedId === fact.id && (
                  <tr key={`${fact.id}-quote`}>
                    <td colSpan={6} style={{ padding: "0 12px 12px" }}>
                      <div className="source-quote animate-fade-in">
                        <span
                          style={{
                            fontSize: "10px",
                            textTransform: "uppercase",
                            letterSpacing: "0.04em",
                            color: "var(--text-tertiary)",
                            display: "block",
                            marginBottom: 4,
                            fontWeight: 700,
                          }}
                        >
                          📖 Source Evidence — Page {fact.page_number || "?"}
                        </span>
                        &ldquo;{fact.source_quote}&rdquo;
                      </div>
                    </td>
                  </tr>
                )}
              </>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

/**
 * ConfidenceDot — small colored indicator for extraction confidence.
 */
function ConfidenceDot({ confidence }: { confidence: number }) {
  const color =
    confidence >= 0.9
      ? "var(--color-corroboration)"
      : confidence >= 0.7
        ? "var(--color-contextual)"
        : "var(--color-contradiction)";

  return (
    <div style={{ display: "flex", alignItems: "center", gap: 4 }}>
      <span
        style={{
          width: 8,
          height: 8,
          borderRadius: "50%",
          background: color,
          display: "inline-block",
          border: "1px solid rgba(0,0,0,0.2)",
        }}
      />
      <span style={{ fontFamily: "var(--font-mono)", fontSize: "11px", fontWeight: 700 }}>
        {(confidence * 100).toFixed(0)}%
      </span>
    </div>
  );
}
