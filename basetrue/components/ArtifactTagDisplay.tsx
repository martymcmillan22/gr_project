import { formatArtifactTags } from "../logic/artifactTagging";
import type { ArtifactTags, WorkspaceMode } from "../types";

interface ArtifactTagDisplayProps {
  label: string;
  tags?: ArtifactTags | null;
  emptyText?: string;
  semanticMix?: string[];
  executionState?: "planned" | "in_progress" | "completed";
  workspaceMode?: WorkspaceMode;
}

export default function ArtifactTagDisplay({
  label,
  tags,
  emptyText = "none",
  semanticMix,
  executionState,
  workspaceMode,
}: ArtifactTagDisplayProps) {
  return (
    <div
      className="artifact-tag-display"
      role="note"
      aria-label={`${label} artifact tags`}
      style={{ display: "grid", gap: "6px", padding: "6px 0" }}
    >
      <div>
        <strong>{label}:</strong> {tags ? formatArtifactTags(tags) : emptyText}
      </div>
      {tags || semanticMix?.length || executionState || workspaceMode ? (
        <div style={{ display: "flex", flexWrap: "wrap", gap: "6px" }}>
          {typeof tags?.floor === "number" ? (
            <span
              style={{
                border: "1px solid #587090",
                borderRadius: "999px",
                padding: "2px 8px",
                fontSize: "12px",
              }}
            >
              floor {tags.floor}
            </span>
          ) : null}
          {workspaceMode ? (
            <span
              style={{
                border: "1px solid #587090",
                borderRadius: "999px",
                padding: "2px 8px",
                fontSize: "12px",
              }}
            >
              workspace {workspaceMode}
            </span>
          ) : null}
          {executionState ? (
            <span
              style={{
                border: "1px solid #587090",
                borderRadius: "999px",
                padding: "2px 8px",
                fontSize: "12px",
              }}
            >
              state {executionState}
            </span>
          ) : null}
          {(semanticMix || []).map((mix) => (
            <span
              key={`${label}-${mix}`}
              style={{
                border: "1px solid #587090",
                borderRadius: "999px",
                padding: "2px 8px",
                fontSize: "12px",
              }}
            >
              semantic {mix}
            </span>
          ))}
        </div>
      ) : null}
    </div>
  );
}
