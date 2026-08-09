import { useEffect, useMemo, useState } from "react";

import { fetchProjectMiddleLayerLfoEngine } from "../api/homepageApi";
import {
  buildLfoEngineViewModel,
  buildMvpFeaturePathways,
  buildSynthesisSnapshot,
  buildTimelineSnapshot,
} from "./lfoEngineHelpers";

export default function LfoExpansionPanel({
  panelId = "lfo-expansion-panel",
  timelineSignalState,
  unifiedIntelligenceState,
}) {
  const [lfoEnvelope, setLfoEnvelope] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  const timelineSnapshot = useMemo(
    () => buildTimelineSnapshot(unifiedIntelligenceState || {}),
    [unifiedIntelligenceState],
  );
  const synthesisSnapshot = useMemo(
    () => buildSynthesisSnapshot(unifiedIntelligenceState || {}),
    [unifiedIntelligenceState],
  );
  const featurePathways = useMemo(
    () => buildMvpFeaturePathways(timelineSignalState || {}, unifiedIntelligenceState || {}),
    [timelineSignalState, unifiedIntelligenceState],
  );
  const triggerCount = Number(unifiedIntelligenceState?.orchestration?.trigger_count || 0);

  useEffect(() => {
    let active = true;
    setLoading(true);
    setError("");

    fetchProjectMiddleLayerLfoEngine({
      timeline_snapshot: timelineSnapshot,
      synthesis_snapshot: synthesisSnapshot,
      trigger_count: triggerCount,
      feature_pathways: featurePathways,
    })
      .then((payload) => {
        if (!active) {
          return;
        }
        setLfoEnvelope(payload);
      })
      .catch((nextError) => {
        if (!active) {
          return;
        }
        setError(nextError?.message || "Unable to load LFO engine envelope");
      })
      .finally(() => {
        if (active) {
          setLoading(false);
        }
      });

    return () => {
      active = false;
    };
  }, [featurePathways, synthesisSnapshot, timelineSnapshot, triggerCount]);

  const viewModel = useMemo(
    () => buildLfoEngineViewModel({
      timelineSignalState: timelineSignalState || {},
      unifiedIntelligenceState: unifiedIntelligenceState || {},
      lfoEnvelope: lfoEnvelope || {},
    }),
    [lfoEnvelope, timelineSignalState, unifiedIntelligenceState],
  );

  return (
    <section id={panelId} className="panel semantic-stack-panel">
      <div className="semantic-stack-head">
        <div>
          <p className="eyebrow">Governed LFO Expansion</p>
          <h2>4-Surface LFO Engine</h2>
        </div>
      </div>

      {loading ? <p className="status-line">Loading deterministic LFO envelopes...</p> : null}
      {error ? <p className="status-line">{error}</p> : null}

      {!loading && !error ? (
        <>
          <div className="rr-node-chip-row">
            <span>SEVM logical branches {viewModel.template_summary.sevm_logical_branch_count}</span>
            <span>Industry Group templates {viewModel.template_summary.group_template_count}</span>
            <span>Industry templates {viewModel.template_summary.industry_template_count}</span>
            <span>Project-MVP pathways {viewModel.probability_rows.length}</span>
          </div>

          <article>
            <h3>{viewModel.math_surface.title}</h3>
            <ul>
              {viewModel.math_surface.feature_rows.map((row) => (
                <li key={`math-lfo-${row.feature}`}>
                  {row.feature}: slot {row.slot_index} · probability {row.probability.toFixed(3)} · grade {row.grade}
                </li>
              ))}
            </ul>
          </article>

          <article>
            <h3>{viewModel.language_surface.title}</h3>
            <ul>
              {viewModel.language_surface.document_tracks.map((track) => (
                <li key={`language-lfo-${track.format}`}>
                  {track.format}: {track.transcript_id} {track.summary ? `- ${track.summary}` : ""}
                </li>
              ))}
            </ul>
          </article>

          <article>
            <h3>{viewModel.arts_surface.title}</h3>
            <ul>
              {viewModel.arts_surface.creator_scaffolds.slice(0, 8).map((scaffold) => (
                <li key={`arts-lfo-${scaffold.template_id}`}>
                  {scaffold.group_name}: {scaffold.branch_count} branches ({scaffold.mode})
                </li>
              ))}
            </ul>
          </article>

          <article>
            <h3>{viewModel.industry_surface.title}</h3>
            <div className="rr-node-chip-row">
              <span>Industry templates {viewModel.industry_surface.template_rows.length}</span>
              <span>Fallback {viewModel.industry_surface.source}</span>
            </div>
            <ul>
              {viewModel.industry_surface.template_rows.slice(0, 8).map((template) => (
                <li key={`industry-lfo-${template.template_id}`}>
                  {template.group_name} / {template.industry_name}: branches {template.branch_count} · slot {template.latest_slot_index}
                </li>
              ))}
            </ul>
          </article>

          <article>
            <h3>{viewModel.micro_surface.title}</h3>
            <div className="rr-node-chip-row">
              <span>Micro templates {viewModel.micro_surface.template_rows.length}</span>
              <span>Fallback {viewModel.micro_surface.source}</span>
            </div>
            <ul>
              {viewModel.micro_surface.template_rows.slice(0, 8).map((template) => (
                <li key={`micro-lfo-${template.template_id}`}>
                  {template.group_name} / {template.industry_name} / {template.sub_industry_name}: lenses {template.science_lens_count} · slot {template.latest_slot_index}
                </li>
              ))}
            </ul>
          </article>

          <article>
            <h3>{viewModel.science_surface.title}</h3>
            <div className="rr-node-chip-row">
              <span>Consumer GUI risk {viewModel.science_surface.consumer_gui.risk_level}</span>
              <span>Trigger bindings {viewModel.science_surface.consumer_gui.trigger_count}</span>
              <span>Latest phase {viewModel.science_surface.consumer_gui.latest_phase || "n/a"}</span>
              <span>Surface phase {viewModel.science_surface.consumer_gui.surface_phase || "n/a"}</span>
              <span>Completion ratio {Number(viewModel.science_surface.consumer_gui.completion_ratio || 0).toFixed(3)}</span>
            </div>
            <div className="rr-node-chip-row">
              <span>
                Studio tier {viewModel.science_surface.consumer_gui.surface_tiers?.studio?.active ? "active" : viewModel.science_surface.consumer_gui.surface_tiers?.studio?.unlocked ? "unlocked" : "locked"}
              </span>
              <span>
                Studio readiness {Number(viewModel.science_surface.consumer_gui.surface_tiers?.studio?.readiness_score || 0).toFixed(3)}
              </span>
              <span>
                Enterprise tier {viewModel.science_surface.consumer_gui.surface_tiers?.enterprise?.active ? "active" : viewModel.science_surface.consumer_gui.surface_tiers?.enterprise?.unlocked ? "unlocked" : "locked"}
              </span>
              <span>
                Enterprise readiness {Number(viewModel.science_surface.consumer_gui.surface_tiers?.enterprise?.readiness_score || 0).toFixed(3)}
              </span>
            </div>
            <ul>
              {(viewModel.science_surface.consumer_gui.lenses || []).map((lens) => (
                <li key={`science-lfo-${lens.lens}`}>
                  {lens.lens}: {lens.interaction_model || "model"} · behavior {Number(lens.behavior_score || 0).toFixed(3)}
                </li>
              ))}
            </ul>
          </article>
        </>
      ) : null}
    </section>
  );
}
