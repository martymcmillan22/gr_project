export default function RrNodeCard({
  card,
  compact = false,
  mode = "compact",
  showSemanticChips = false,
  showProvenanceChips = false,
  onOpenDetail,
  onOpenMiddleLayer,
}) {
  if (!card) {
    return null;
  }

  const rgb = card.display_rgb || { r: 90, g: 90, b: 90 };
  const integrityPalette = (card.card_color_spec && card.card_color_spec.integrity_indicator) || {
    ok: "#16a34a",
    mismatch: "#f97316",
    unavailable: "#64748b",
  };
  const integrityState = String(card.integrity_state || "unavailable");
  const integrityColor = integrityPalette[integrityState] || integrityPalette.unavailable;
  const path = Array.isArray(card.industry_path) ? card.industry_path : [];
  const semanticChips = [card.subject, card.sector, card.industry, card.subindustry].filter(Boolean);
  const workflowRefs = Array.isArray(card?.provenance?.workflow_refs) ? card.provenance.workflow_refs : [];
  const sopRefs = Array.isArray(card?.provenance?.sop_refs) ? card.provenance.sop_refs : [];

  const handleOpenDetail = () => {
    if (typeof onOpenDetail === "function" && card.business_id) {
      onOpenDetail(card.business_id);
    }
  };

  const handleOpenMiddleLayer = () => {
    if (typeof onOpenMiddleLayer === "function" && card.business_id) {
      onOpenMiddleLayer(card.business_id, card.compartment_id ?? card.card_color_spec?.compartment_tag?.compartment_id);
    }
  };

  return (
    <article className={`rr-node-card ${compact ? "is-compact" : ""} ${mode === "expanded" ? "is-expanded" : ""}`}>
      <header style={{ borderTopColor: `rgb(${rgb.r}, ${rgb.g}, ${rgb.b})` }}>
        <h4>{card.title || "Untitled RR Node"}</h4>
        <span className="rr-node-phase">{card.phase || "Unknown"}</span>
      </header>
      <div className="rr-node-meta">
        <span className="rr-node-compartment">
          {card.subject || "Unknown Subject"} · C{card.card_color_spec?.compartment_tag?.compartment_id ?? "?"}
        </span>
        <span className="rr-node-integrity" style={{ borderColor: integrityColor, color: integrityColor }}>
          Integrity {integrityState}
        </span>
      </div>
      <p className="rr-node-path">{path.length > 0 ? path.join(" -> ") : "No ontology path recorded"}</p>

      {showSemanticChips && semanticChips.length > 0 ? (
        <div className="rr-node-chip-row" aria-label="Semantic identity">
          {semanticChips.map((chip) => (
            <span key={chip}>{chip}</span>
          ))}
        </div>
      ) : null}

      {showProvenanceChips ? (
        <div className="rr-node-chip-row" aria-label="Provenance links">
          {workflowRefs.map((item) => (
            <span key={item.workflow_id || String(item.phase || "workflow")}>Workflow {item.workflow_id || item.phase || "ref"}</span>
          ))}
          {sopRefs.map((item) => (
            <span key={item.sop_id || item.title || "sop-ref"}>SOP {item.sop_id || item.title || "ref"}</span>
          ))}
          {workflowRefs.length === 0 && sopRefs.length === 0 ? <span>No provenance refs</span> : null}
        </div>
      ) : null}

      {!compact ? (
        <div className="rr-node-actions">
          <button type="button" onClick={handleOpenDetail} disabled={!card.business_id}>Open node detail</button>
          <button type="button" onClick={handleOpenMiddleLayer} disabled={!card.business_id}>Open middle layer</button>
        </div>
      ) : null}

      <footer>
        <span>Seed #{card.seed_id ?? "-"}</span>
        <span>Business #{card.business_id ?? "-"}</span>
      </footer>
    </article>
  );
}
