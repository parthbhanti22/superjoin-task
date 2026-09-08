"use client";

/**
 * RelationshipCard — displays a cross-document relationship between two facts.
 *
 * Shows both facts side-by-side with color coding based on relationship type.
 * Includes explanation text and context details for contextual differences.
 */

import type { RelationshipInfo } from "@/lib/api";

interface RelationshipCardProps {
  relationship: RelationshipInfo;
}

const TYPE_CONFIG = {
  corroboration: {
    label: "Corroboration",
    color: "var(--color-corroboration)",
    dim: "var(--color-corroboration-dim)",
    icon: "✓",
    description: "Both sources agree",
  },
  contradiction: {
    label: "Contradiction",
    color: "var(--color-contradiction)",
    dim: "var(--color-contradiction-dim)",
    icon: "✗",
    description: "Sources disagree",
  },
  contextual_difference: {
    label: "Contextual Difference",
    color: "var(--color-contextual)",
    dim: "var(--color-contextual-dim)",
    icon: "◐",
    description: "Explained by context",
  },
  extraction_failure: {
    label: "Extraction Failure",
    color: "var(--color-failure)",
    dim: "var(--color-failure-dim)",
    icon: "⚠",
    description: "Possible error",
  },
};

export default function RelationshipCard({
  relationship,
}: RelationshipCardProps) {
  const config = TYPE_CONFIG[relationship.rel_type] || TYPE_CONFIG.extraction_failure;

  return (
    <div
      className="glass-card"
      style={{
        padding: 0,
        overflow: "hidden",
        borderLeft: `3px solid ${config.color}`,
      }}
    >
      {/* Header */}
      <div
        style={{
          padding: "12px 20px",
          background: config.dim,
          display: "flex",
          alignItems: "center",
          gap: 10,
          borderBottom: "1px solid var(--border-subtle)",
        }}
      >
        <span style={{ fontSize: "1.1rem" }}>{config.icon}</span>
        <div>
          <span
            style={{
              fontWeight: 600,
              fontSize: "0.85rem",
              color: config.color,
            }}
          >
            {config.label}
          </span>
          <span
            style={{
              marginLeft: 8,
              fontSize: "0.75rem",
              color: "var(--text-tertiary)",
            }}
          >
            {config.description}
          </span>
        </div>
      </div>

      {/* Facts side-by-side */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "1fr 1fr",
          gap: 0,
        }}
      >
        <FactSide fact={relationship.fact_a} label="Fact A" />
        <FactSide
          fact={relationship.fact_b}
          label="Fact B"
          borderLeft
        />
      </div>

      {/* Explanation */}
      <div
        style={{
          padding: "14px 20px",
          borderTop: "1px solid var(--border-subtle)",
        }}
      >
        <p
          style={{
            fontSize: "0.65rem",
            textTransform: "uppercase",
            letterSpacing: "0.05em",
            color: "var(--text-tertiary)",
            marginBottom: 6,
          }}
        >
          Analysis
        </p>
        <p style={{ fontSize: "0.85rem", color: "var(--text-secondary)", lineHeight: 1.6 }}>
          {relationship.explanation}
        </p>

        {/* Context detail for contextual_difference */}
        {relationship.context_detail && (
          <div
            style={{
              marginTop: 10,
              padding: "10px 14px",
              borderRadius: "var(--radius-sm)",
              background: "var(--color-contextual-dim)",
              borderLeft: "3px solid var(--color-contextual)",
            }}
          >
            <p
              style={{
                fontSize: "0.65rem",
                textTransform: "uppercase",
                letterSpacing: "0.05em",
                color: "var(--color-contextual)",
                marginBottom: 4,
              }}
            >
              Reconciling Context
            </p>
            <p style={{ fontSize: "0.8rem", color: "var(--text-secondary)" }}>
              {relationship.context_detail}
            </p>
          </div>
        )}
      </div>
    </div>
  );
}

/**
 * FactSide — one half of the side-by-side fact comparison.
 */
function FactSide({
  fact,
  label,
  borderLeft = false,
}: {
  fact: RelationshipInfo["fact_a"];
  label: string;
  borderLeft?: boolean;
}) {
  return (
    <div
      style={{
        padding: "14px 20px",
        borderLeft: borderLeft ? "1px solid var(--border-subtle)" : "none",
      }}
    >
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          marginBottom: 8,
        }}
      >
        <span
          style={{
            fontSize: "0.65rem",
            textTransform: "uppercase",
            letterSpacing: "0.05em",
            color: "var(--text-tertiary)",
          }}
        >
          {label}
        </span>
        <span
          style={{
            fontSize: "0.7rem",
            padding: "1px 6px",
            borderRadius: "var(--radius-sm)",
            background: "var(--bg-tertiary)",
            color: "var(--text-tertiary)",
          }}
        >
          p.{fact.page_number || "?"}
        </span>
      </div>

      <p
        style={{
          fontSize: "0.85rem",
          fontWeight: 500,
          color: "var(--text-primary)",
          marginBottom: 6,
          lineHeight: 1.5,
        }}
      >
        {fact.claim}
      </p>

      {fact.value && (
        <p
          style={{
            fontFamily: "var(--font-mono)",
            fontSize: "0.8rem",
            color: "var(--accent-blue)",
            marginBottom: 6,
          }}
        >
          {fact.value} {fact.unit}
        </p>
      )}

      <p
        style={{
          fontSize: "0.7rem",
          color: "var(--text-tertiary)",
          overflow: "hidden",
          textOverflow: "ellipsis",
          whiteSpace: "nowrap",
        }}
        title={fact.document_filename || undefined}
      >
        📄 {fact.document_filename || "Unknown document"}
        {fact.time_context && ` · ${fact.time_context}`}
      </p>

      {/* Source quote */}
      <div className="source-quote" style={{ marginTop: 10 }}>
        <span style={{ fontSize: "0.75rem" }}>
          &ldquo;{fact.source_quote}&rdquo;
        </span>
      </div>
    </div>
  );
}
