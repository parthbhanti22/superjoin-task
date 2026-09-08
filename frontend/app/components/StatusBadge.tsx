"use client";

/**
 * StatusBadge — visual indicator for document processing status.
 *
 * Renders a color-coded pill badge based on the document's current
 * processing state (uploaded, processing, processed, error).
 */

interface StatusBadgeProps {
  status: "uploaded" | "processing" | "processed" | "error";
}

const STATUS_CONFIG = {
  uploaded: {
    label: "Uploaded",
    bg: "var(--color-uploaded)",
    dim: "rgba(96, 165, 250, 0.12)",
  },
  processing: {
    label: "Processing",
    bg: "var(--color-processing)",
    dim: "rgba(251, 191, 36, 0.12)",
  },
  processed: {
    label: "Processed",
    bg: "var(--color-processed)",
    dim: "rgba(52, 211, 153, 0.12)",
  },
  error: {
    label: "Error",
    bg: "var(--color-error)",
    dim: "rgba(248, 113, 113, 0.12)",
  },
};

export default function StatusBadge({ status }: StatusBadgeProps) {
  const config = STATUS_CONFIG[status] || STATUS_CONFIG.uploaded;

  return (
    <span
      className="badge"
      style={{
        background: config.dim,
        color: config.bg,
      }}
    >
      {/* Animated dot for processing state */}
      {status === "processing" && (
        <span
          className="animate-pulse-soft"
          style={{
            width: 6,
            height: 6,
            borderRadius: "50%",
            background: config.bg,
          }}
        />
      )}
      {config.label}
    </span>
  );
}
