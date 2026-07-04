import { useMemo } from "react";

const TIER_CONFIG = [
  { key: "branches", prefix: "B", label: "Branches" },
  { key: "terms", prefix: "T", label: "Terms" },
  { key: "meta_terms", prefix: "M", label: "Meta-Terms" },
  { key: "tier4", prefix: "X", label: "Tier 4" },
];

export default function RepositoryRelayBlueprint({
  imageLabel = "Repository Relay",
  processorLabel = "Quantum Series Circuit Processor (QPU)",
  subjectLabel = "Subject",
  tierCounts = [4, 16, 64, 256],
  onNodeSelected,
}) {
  const tiers = useMemo(() => {
    return TIER_CONFIG.map((config, index) => {
      const rawCount = Number(Array.isArray(tierCounts) ? tierCounts[index] : 0);
      const count = Number.isFinite(rawCount) ? Math.max(0, Math.min(256, Math.floor(rawCount))) : 0;
      const nodes = Array.from({ length: count }, (_, nodeIndex) => ({
        id: `${config.key}-${nodeIndex + 1}`,
        label: `${config.prefix}${nodeIndex + 1}`,
      }));
      return {
        ...config,
        count,
        nodes,
      };
    });
  }, [tierCounts]);

  return (
    <section className="relay-blueprint" aria-label="Repository Relay blueprint">
      <header className="relay-header">
        <h4>{imageLabel || "Repository Relay"}</h4>
        <p>{processorLabel || "Quantum Series Circuit Processor (QPU)"}</p>
      </header>

      <div className="relay-stage" role="img" aria-label="Concentric relay blueprint">
        {tiers.map((tier, tierIndex) => {
          if (!tier.count) {
            return null;
          }
          return (
            <ul
              key={tier.key}
              className={`relay-ring relay-ring-${tierIndex + 1}`}
              style={{ "--relay-count": tier.count }}
              aria-label={`${tier.label} ring with ${tier.count} nodes`}
            >
              {tier.nodes.map((node, nodeIndex) => (
                <li
                  key={node.id}
                  style={{ "--relay-index": nodeIndex }}
                  title={`${tier.label}: ${node.label}`}
                >
                  <button
                    type="button"
                    onClick={() => onNodeSelected?.({ tier: tier.label, label: node.label, index: nodeIndex + 1 })}
                  >
                    {node.label}
                  </button>
                </li>
              ))}
            </ul>
          );
        })}

        <div className="relay-core">
          <h5>{subjectLabel || "Subject"}</h5>
          <span>1 Subject</span>
        </div>
      </div>

      <div className="relay-counts">
        <span>1 Subject</span>
        <span>{tiers[0].count} Branches</span>
        <span>{tiers[1].count} Terms</span>
        <span>{tiers[2].count} Meta-Terms</span>
        <span>{tiers[3].count} Tier 4</span>
      </div>
    </section>
  );
}
