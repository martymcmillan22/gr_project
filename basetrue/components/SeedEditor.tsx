import { useMemo, useState } from "react";
import { buildArtifactTags, formatArtifactTags } from "../logic/artifactTagging";
import { RR_LOGIC_MODES, RR_QUADRANTS, RR_SUBNODES, buildRrSelection, buildSeedRoute } from "../logic/rrRouter";
import {
  canPreviewQPUInSeed,
  canRouteRRInPipeline,
  getSeedGeometryMode,
} from "../logic/pipelineLogic";
import type {
  IdeaRecord,
  ProfileKind,
  RRLogicMode,
  RRQuadrant,
  RRSubnode,
  SeedRecord,
  TemporalGroup,
  Tier,
} from "../types";

interface SeedEditorProps {
  profile: ProfileKind;
  compartmentName: string;
  compartmentIndex: number;
  temporalGroup: TemporalGroup;
  tier: Tier;
  phaseColor: string;
  idea: IdeaRecord | null;
  existingSeed: SeedRecord | null;
  onCreate: (seed: SeedRecord) => void;
  rrQuadrant: RRQuadrant;
  rrSubnode: RRSubnode;
  rrLogicMode: RRLogicMode;
  onRrQuadrantChange: (quadrant: RRQuadrant) => void;
  onRrSubnodeChange: (subnode: RRSubnode) => void;
  onRrLogicModeChange: (logicMode: RRLogicMode) => void;
}

function parseMetadata(lines: string): Record<string, string> {
  return lines
    .split("\n")
    .map((line) => line.trim())
    .filter(Boolean)
    .reduce<Record<string, string>>((acc, line) => {
      const [key, ...rest] = line.split(":");
      const cleanKey = key?.trim();
      if (!cleanKey) {
        return acc;
      }
      acc[cleanKey] = rest.join(":").trim();
      return acc;
    }, {});
}

export default function SeedEditor({
  profile,
  compartmentName,
  compartmentIndex,
  temporalGroup,
  tier,
  phaseColor,
  idea,
  existingSeed,
  onCreate,
  rrQuadrant,
  rrSubnode,
  rrLogicMode,
  onRrQuadrantChange,
  onRrSubnodeChange,
  onRrLogicModeChange,
}: SeedEditorProps) {
  const [structure, setStructure] = useState(existingSeed?.structure || "");
  const [metadataInput, setMetadataInput] = useState(
    existingSeed ? Object.entries(existingSeed.metadata).map(([k, v]) => `${k}: ${v}`).join("\n") : "",
  );
  const [rrRoute, setRrRoute] = useState(existingSeed?.rr_route || "");

  const showRrRoute = canRouteRRInPipeline(tier);
  const showQpuPreview = canPreviewQPUInSeed(tier);
  const geometryMode = getSeedGeometryMode(tier);
  const rrSelectionEnabled = showRrRoute && Boolean(idea);

  const computedSeedRoute = useMemo(() => {
    return buildSeedRoute({
      quadrant: rrQuadrant,
      subnode: rrSubnode,
      logicMode: rrLogicMode,
      temporalGroup,
    });
  }, [rrLogicMode, rrQuadrant, rrSubnode, temporalGroup]);
  const seedTagPreview = useMemo(
    () =>
      buildArtifactTags({
        profile,
        compartmentName,
        compartmentIndex,
        phase: "create",
        temporalGroup,
        tier,
        rrRoute: computedSeedRoute,
        rrSelection: buildRrSelection({
          quadrant: rrQuadrant,
          subnode: rrSubnode,
          logicMode: rrLogicMode,
          temporalGroup,
        }),
      }),
    [
      compartmentIndex,
      compartmentName,
      computedSeedRoute,
      profile,
      rrLogicMode,
      rrQuadrant,
      rrSubnode,
      temporalGroup,
      tier,
    ],
  );

  const gateMessage = useMemo(() => {
    if (tier === "novice") {
      return "Novice cannot form seeds.";
    }
    if (tier === "intermediate") {
      return "Intermediate can form seeds with SVEM structure only.";
    }
    if (tier === "advanced") {
      return "Advanced unlocks RR routing.";
    }
    return "Studio and Enterprise unlock RR routing and QPU readiness preview.";
  }, [tier]);

  const createSeed = () => {
    if (!idea) {
      return;
    }

    const seed: SeedRecord = {
      seed_id: `seed-${Date.now()}`,
      idea_id: idea.idea_id,
      structure: structure.trim(),
      metadata: parseMetadata(metadataInput),
      temporal_group: temporalGroup,
      phase: "create",
      tier,
      seed_route: showRrRoute ? computedSeedRoute : undefined,
      rr_selection: showRrRoute
        ? buildRrSelection({
            quadrant: rrQuadrant,
            subnode: rrSubnode,
            logicMode: rrLogicMode,
            temporalGroup,
          })
        : undefined,
      rr_route: showRrRoute ? (rrRoute.trim() || computedSeedRoute) : undefined,
      ready_for_qpu: showQpuPreview,
      geometry_mode: geometryMode,
      artifact_tags: buildArtifactTags({
        profile,
        compartmentName,
        compartmentIndex,
        phase: "create",
        temporalGroup,
        tier,
        rrRoute: showRrRoute ? (rrRoute.trim() || computedSeedRoute) : undefined,
        rrSelection: showRrRoute
          ? buildRrSelection({
              quadrant: rrQuadrant,
              subnode: rrSubnode,
              logicMode: rrLogicMode,
              temporalGroup,
            })
          : undefined,
      }),
    };

    onCreate(seed);
  };

  return (
    <article className="pipeline-card" data-color={phaseColor}>
      <h3>Seed Formation</h3>
      <p>{gateMessage}</p>
      <p>Geometry mode: {geometryMode}</p>
      <p>Temporal group: {temporalGroup}</p>
      <p>Artifact tags: {formatArtifactTags(seedTagPreview)}</p>

      <label>
        SVEM Structure
        <textarea
          value={structure}
          onChange={(event) => setStructure(event.target.value)}
          placeholder="Branch map / SVEM structure"
          rows={3}
          disabled={!idea || tier === "novice"}
        />
      </label>

      <label>
        Metadata (key: value per line)
        <textarea
          value={metadataInput}
          onChange={(event) => setMetadataInput(event.target.value)}
          placeholder="intent: growth\npriority: medium"
          rows={4}
          disabled={!idea || tier === "novice"}
        />
      </label>

      <fieldset disabled={!idea || tier === "novice"}>
        <legend>RR Semantic Selection</legend>
        <p>{showRrRoute ? "Routing active (Advanced+)." : "Preview only until Advanced tier."}</p>
        <label>
          Quadrant
          <select value={rrQuadrant} onChange={(event) => onRrQuadrantChange(event.target.value as RRQuadrant)}>
            {RR_QUADRANTS.map((quadrant) => (
              <option key={quadrant} value={quadrant}>
                {quadrant}
              </option>
            ))}
          </select>
        </label>
        <label>
          Subnode
          <select value={rrSubnode} onChange={(event) => onRrSubnodeChange(event.target.value as RRSubnode)}>
            {RR_SUBNODES.map((subnode) => (
              <option key={subnode} value={subnode}>
                {subnode}
              </option>
            ))}
          </select>
        </label>
        <label>
          Logic mode
          <select value={rrLogicMode} onChange={(event) => onRrLogicModeChange(event.target.value as RRLogicMode)}>
            {RR_LOGIC_MODES.map((logicMode) => (
              <option key={logicMode} value={logicMode}>
                {logicMode}
              </option>
            ))}
          </select>
        </label>
        <p>Computed route: {computedSeedRoute}</p>
      </fieldset>

      {showRrRoute ? (
        <label>
          RR Route
          <input
            value={rrRoute}
            onChange={(event) => setRrRoute(event.target.value)}
            placeholder={computedSeedRoute}
            disabled={!rrSelectionEnabled}
          />
        </label>
      ) : null}

      <button type="button" onClick={createSeed} disabled={!idea || tier === "novice"}>
        Form Seed
      </button>
    </article>
  );
}
