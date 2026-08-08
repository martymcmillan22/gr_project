import { useState } from "react";

function buildSopBlocksFromDashboard(rrDashboard) {
  const lanes = Array.isArray(rrDashboard?.lanes) ? rrDashboard.lanes : [];
  const blocks = [];

  lanes.forEach((lane) => {
    const cards = Array.isArray(lane.cards) ? lane.cards : [];
    cards.slice(0, 2).forEach((card) => {
      blocks.push({
        sop_id: `sop-${card.business_id}`,
        title: card.title,
        purpose: `Advance ${card.subject} ${card.phase} operations with integrity ${card.integrity_state}.`,
        subject: card.subject,
        compartment_id: lane.compartment_id,
        phase: card.phase,
        display_rgb: card.display_rgb,
        provenance: {
          business_id: card.business_id,
          seed_id: card.seed_id,
          workflow_refs: card.provenance?.workflow_refs || [],
          sop_refs: card.provenance?.sop_refs || [],
        },
      });
    });
  });

  return blocks.slice(0, 12);
}
import { buildDriftReflection, buildOptimizationReflection, dispatchSemanticNavigation, executeSemanticAction, normalizeBreadcrumbs, normalizeSemanticFeedbackLoop, SEMANTIC_ACTIONS } from "./semanticOsHelpers";

export default function SopWorkflowScaffoldPanel({ panelId = "sop-workflow-panel", rrDashboard, operatingStack, semanticIntelligence, semanticActionFeedback }) {
  const sopBlocks = buildSopBlocksFromDashboard(rrDashboard);
  const workflowContract = operatingStack?.tracks?.operational_architecture?.workflow_schema || {};
  const [selectedSopId, setSelectedSopId] = useState(null);
  const semanticBreadcrumbs = semanticIntelligence?.semantic_os_unification?.timeline_breadcrumbs || [];
  const semanticHealth = semanticIntelligence?.semantic_os_health || {};
  const provenanceChains = semanticIntelligence?.workflow_intelligence?.provenance_chains || [];
  const driftReflection = buildDriftReflection(
    normalizeSemanticFeedbackLoop(semanticActionFeedback || semanticIntelligence?.semantic_feedback_loop || {}),
  );
  const optimizationReflection = buildOptimizationReflection(
    normalizeSemanticFeedbackLoop(semanticActionFeedback || semanticIntelligence?.semantic_feedback_loop || {}),
  );
  const [actionStatus, setActionStatus] = useState("");

  const selectedSop = sopBlocks.find((item) => item.sop_id === selectedSopId) || sopBlocks[0] || null;
  const timeline = selectedSop
    ? [
        { id: `${selectedSop.sop_id}-capture`, label: "Capture", business_id: selectedSop.provenance.business_id },
        { id: `${selectedSop.sop_id}-activate`, label: "Activate", business_id: selectedSop.provenance.business_id },
        { id: `${selectedSop.sop_id}-publish`, label: "Publish", business_id: selectedSop.provenance.business_id },
      ]
    : [];

  const openNode = (businessId) => {
    dispatchSemanticNavigation({ surface: "rr_dashboard", business_id: businessId }, "sop-workflow");
  };

  const executeTimelineStep = async (step) => {
    try {
      const result = await executeSemanticAction({
        action: SEMANTIC_ACTIONS.ADVANCE_WORKFLOW_STEP,
        request: {
          business_id: step.business_id,
          compartment_id: selectedSop?.compartment_id,
          workflow_step: step.label.toLowerCase(),
        },
        source: "workflow_swimlanes",
        semanticHealth,
      });
      setActionStatus(result?.status === "executed" ? `Executed ${step.label}` : result?.detail || "Semantic action was not executed");
    } catch (err) {
      setActionStatus(err?.message || "Unable to execute semantic action");
    }
    openNode(step.business_id);
  };

  const executeStabilizationAction = async (recommendation = {}) => {
    const businessId = selectedSop?.provenance?.business_id;
    const compartmentId = selectedSop?.compartment_id;
    if (!recommendation?.action || !businessId || !compartmentId) {
      setActionStatus("Stabilization recommendation missing context.");
      return;
    }

    try {
      const result = await executeSemanticAction({
        action: recommendation.action,
        request: {
          business_id: businessId,
          compartment_id: compartmentId,
        },
        source: "workflow_swimlanes",
        semanticHealth,
      });
      setActionStatus(result?.status === "executed" ? `Executed ${recommendation.label || recommendation.action}` : result?.detail || "Stabilization action was not executed");
    } catch (err) {
      setActionStatus(err?.message || "Unable to execute stabilization action");
    }
    openNode(businessId);
  };

  const executeOptimizationAction = async (recommendation = {}) => {
    const businessId = selectedSop?.provenance?.business_id;
    const compartmentId = selectedSop?.compartment_id;
    if (!recommendation?.action || !businessId || !compartmentId) {
      setActionStatus("Optimization recommendation missing context.");
      return;
    }

    try {
      const result = await executeSemanticAction({
        action: recommendation.action,
        request: {
          business_id: businessId,
          compartment_id: compartmentId,
          workflow_step: "optimize",
        },
        source: "workflow_swimlanes",
        semanticHealth,
      });
      setActionStatus(result?.status === "executed" ? `Executed ${recommendation.label || recommendation.action}` : result?.detail || "Optimization action was not executed");
    } catch (err) {
      setActionStatus(err?.message || "Unable to execute optimization action");
    }
    openNode(businessId);
  };

  return (
    <section id={panelId} className="panel semantic-stack-panel">
      <div className="semantic-stack-head">
        <div>
          <p className="eyebrow">SOP / Workflow Scaffolding</p>
          <h2>Modular Blocks + Color Swimlanes</h2>
        </div>
      </div>

      <div className="sop-grid">
        {sopBlocks.length > 0 ? sopBlocks.map((block) => {
          const rgb = block.display_rgb || { r: 90, g: 90, b: 90 };
          return (
            <article
              key={block.sop_id}
              className={selectedSop?.sop_id === block.sop_id ? "is-selected" : ""}
              style={{ borderLeftColor: `rgb(${rgb.r}, ${rgb.g}, ${rgb.b})` }}
            >
              <h3>{block.title}</h3>
              <p>{block.purpose}</p>
              <p>{block.subject} · C{block.compartment_id} · {block.phase}</p>
              <p>
                Provenance: RR business #{block.provenance.business_id}, seed #{block.provenance.seed_id}
              </p>
              <div className="rr-node-actions">
                <button type="button" onClick={() => setSelectedSopId(block.sop_id)}>Open SOP detail</button>
                <button type="button" onClick={() => openNode(block.provenance.business_id)}>Open RR node</button>
              </div>
            </article>
          );
        }) : <p className="status-line">No RR-backed SOP blocks yet.</p>}
      </div>

      {selectedSop ? (
        <section className="rr-node-detail-panel">
          <h3>SOP Detail</h3>
          <p className="status-line">{selectedSop.title}</p>
          <p className="status-line">{selectedSop.purpose}</p>
          <div className="rr-node-chip-row">
            {normalizeBreadcrumbs(semanticBreadcrumbs).slice(0, 3).map((crumb, index) => (
              <span key={`crumb-${index}`}>{crumb}</span>
            ))}
            {(selectedSop.provenance.workflow_refs || []).map((item) => (
              <span key={item.workflow_id || item.phase || "wf"}>Workflow {item.workflow_id || item.phase}</span>
            ))}
            {(selectedSop.provenance.sop_refs || []).map((item) => (
              <span key={item.sop_id || item.title || "sop"}>SOP {item.sop_id || item.title}</span>
            ))}
          </div>
        </section>
      ) : null}

      <section className="workflow-swimlanes">
        <h3>Workflow Swimlane Contract</h3>
        <p className="status-line">
          Macro fields: {(workflowContract.macro || []).join(", ") || "not available"}
        </p>
        <p className="status-line">
          Micro fields: {(workflowContract.micro || []).join(", ") || "not available"}
        </p>
        <p className="status-line">
          Provenance fields: {(workflowContract.provenance || []).join(", ") || "not available"}
        </p>
        <div className="publishing-chain">
          {timeline.map((step) => (
            <button key={step.id} type="button" onClick={() => executeTimelineStep(step)}>
              {step.label}
            </button>
          ))}
        </div>
        {actionStatus ? <p className="status-line">{actionStatus}</p> : null}
        <div className="rr-node-chip-row">
          {(semanticHealth.checks || []).filter((item) => item.surface === "workflow" || item.surface === "semantic_os").map((item) => (
            <span key={`${item.surface}-${item.status}`}>{item.surface}: {item.status}</span>
          ))}
        </div>
        <div className="rr-node-chip-row">
          <span>Drift {driftReflection.severity}</span>
          <span>Score {driftReflection.score}</span>
          <span>Workflow stalled {driftReflection.stabilization?.status === "active" ? "monitor" : "clear"}</span>
        </div>
        <div className="rr-node-chip-row">
          <span>Optimization {optimizationReflection.status}</span>
          <span>Pressure {optimizationReflection.optimizationPressure}</span>
          <span>Workflow efficiency {optimizationReflection.workflowEfficiencyScore}</span>
          <span>Pending {optimizationReflection.progress.pendingOptimizations}</span>
        </div>
        <div className="rr-node-chip-row">
          {(driftReflection.subjectChips || []).slice(0, 3).map((chip, index) => (
            <span key={`workflow-drift-chip-${index}`}>{chip.subject} {chip.phase} · {chip.severity}</span>
          ))}
        </div>
        <div className="rr-node-chip-row">
          {provenanceChains.slice(0, 3).map((item) => (
            <button key={`${item.compartment_id}-${item.subject}`} type="button" onClick={() => dispatchSemanticNavigation({ surface: "rr_detail", business_id: item.business_id, compartment_id: item.compartment_id }, "sop-workflow")}>
              {item.subject} chain
            </button>
          ))}
        </div>
        <div className="publishing-chain">
          {(driftReflection.stabilization?.recommendations || []).slice(0, 3).map((item, index) => (
            <button
              key={`workflow-stab-${item.action || index}`}
              type="button"
              onClick={() => executeStabilizationAction(item)}
            >
              {item.label || item.action}
            </button>
          ))}
        </div>
        <div className="publishing-chain">
          {(optimizationReflection.recommendations || []).slice(0, 3).map((item, index) => (
            <button
              key={`workflow-opt-${item.action || index}`}
              type="button"
              onClick={() => executeOptimizationAction(item)}
            >
              {item.label || item.action}
            </button>
          ))}
        </div>
      </section>
    </section>
  );
}
