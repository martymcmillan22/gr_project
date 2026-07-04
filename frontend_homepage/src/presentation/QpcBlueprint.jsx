export default function QpcBlueprint({
  qpcLabel = "Quantum Processor Circuit (QPC)",
  processorLabel = "Quantum Series Circuit Processor (QPU)",
  relays = [],
  profileFilter = "all",
  compareMode = false,
  compareSelection = [],
  selectedRelayId = null,
  onRelaySelected,
}) {
  return (
    <section className="qpc-blueprint" aria-label="QPC blueprint built from four relays">
      <header className="qpc-header">
        <h4>{qpcLabel}</h4>
        <p>{processorLabel}</p>
      </header>

      <div className="qpc-stage">
        <div className="qpc-core">
          <strong>QPC Core</strong>
          <span>{relays.length} relays connected</span>
        </div>

        <div className="qpc-relays-grid">
          {relays.map((relay) => (
            <button
              key={relay.id}
              type="button"
              className={`qpc-relay-card ${selectedRelayId === relay.id ? "active" : ""} ${profileFilter !== "all" && relay.profileKind !== profileFilter ? "qpc-relay-muted" : ""} ${compareMode && compareSelection.includes(relay.id) ? "qpc-relay-compare-target" : ""} ${compareMode && !relay.compareApproved ? "qpc-relay-compare-locked" : ""}`}
              onClick={() => onRelaySelected?.(relay)}
              title={`${relay.name}: ${relay.subject}${compareMode && !relay.compareApproved ? " (not approved for compare)" : ""}`}
            >
              <h5>{relay.name}</h5>
              <p>{relay.subject}</p>
              {compareMode ? (
                <p className={`qpc-relay-compare-pill ${relay.compareApproved ? "approved" : "locked"}`}>
                  {relay.compareApproved ? "compare approved" : "compare blocked"}
                </p>
              ) : null}
              <div className="qpc-relay-counts">
                <span>1</span>
                <span>{relay.counts?.[0] ?? 0}</span>
                <span>{relay.counts?.[1] ?? 0}</span>
                <span>{relay.counts?.[2] ?? 0}</span>
              </div>
            </button>
          ))}
        </div>
      </div>
    </section>
  );
}
