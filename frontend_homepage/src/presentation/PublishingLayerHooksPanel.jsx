import { useState } from "react";

import { buildDriftReflection, buildOptimizationReflection, dispatchSemanticNavigation, executeSemanticAction, normalizeBreadcrumbs, normalizeSemanticFeedbackLoop, SEMANTIC_ACTIONS } from "./semanticOsHelpers";

function gatherColorSubjects(rrDashboard) {
  const lanes = Array.isArray(rrDashboard?.lanes) ? rrDashboard.lanes : [];
  return lanes
    .filter((lane) => Number(lane.node_count || 0) > 0)
    .slice(0, 6)
    .map((lane) => {
      const anchor = lane.display_anchor_band || { r: [80], g: [80], b: [80] };
      return {
        subject: lane.subject,
        color: `rgb(${anchor.r?.[0] ?? 80}, ${anchor.g?.[0] ?? 80}, ${anchor.b?.[0] ?? 80})`,
      };
    });
}

export default function PublishingLayerHooksPanel({ panelId = "publishing-layer-panel", operatingStack, rrDashboard, semanticIntelligence, semanticActionFeedback }) {
  const publishing = operatingStack?.tracks?.publishing_layer || {};
  const investor = publishing.investor_ebook || {};
  const product = publishing.product_usage_ebook || {};
  const pipeline = publishing.sop_to_ebook_pipeline || {};
  const subjectChips = gatherColorSubjects(rrDashboard);
  const semanticPublishing = semanticIntelligence?.publishing_intelligence || {};
  const chapterAssembly = semanticPublishing.chapter_assembly || [];
  const semanticDiagram = semanticPublishing.semantic_diagram || {};
  const semanticHealth = semanticIntelligence?.semantic_os_health || {};
  const driftReflection = buildDriftReflection(
    normalizeSemanticFeedbackLoop(semanticActionFeedback || semanticIntelligence?.semantic_feedback_loop || {}),
  );
  const optimizationReflection = buildOptimizationReflection(
    normalizeSemanticFeedbackLoop(semanticActionFeedback || semanticIntelligence?.semantic_feedback_loop || {}),
  );
  const [previewMode, setPreviewMode] = useState("investor");
  const [activeChainStep, setActiveChainStep] = useState("");
  const [actionStatus, setActionStatus] = useState("");

  const previewSections = previewMode === "investor" ? investor.sections || [] : product.sections || [];

  const executeChapterAssembly = async (item) => {
    const request = {
      business_id: item?.assembly_chain?.[0]?.navigation?.business_id,
      compartment_id: item?.assembly_chain?.[0]?.navigation?.compartment_id,
    };
    try {
      const result = await executeSemanticAction({
        action: SEMANTIC_ACTIONS.PREPARE_PUBLISHING_CHAPTER,
        request,
        source: "publishing_layer",
        semanticHealth,
      });
      setActionStatus(result?.status === "executed" ? `Prepared ${item.subject}` : result?.detail || "Semantic action was not executed");
    } catch (err) {
      setActionStatus(err?.message || "Unable to execute semantic action");
    }
    dispatchSemanticNavigation({ surface: "publishing_layer", ...request }, "publishing-layer");
  };

  const executePublishingStabilization = async (recommendation = {}) => {
    const reference = chapterAssembly[0] || {};
    const request = {
      business_id: reference?.assembly_chain?.[0]?.navigation?.business_id,
      compartment_id: reference?.assembly_chain?.[0]?.navigation?.compartment_id,
    };
    if (!recommendation?.action || !request.business_id || !request.compartment_id) {
      setActionStatus("Publishing stabilization action is missing context.");
      return;
    }

    try {
      const result = await executeSemanticAction({
        action: recommendation.action,
        request,
        source: "publishing_layer",
        semanticHealth,
      });
      setActionStatus(result?.status === "executed" ? `Executed ${recommendation.label || recommendation.action}` : result?.detail || "Publishing stabilization action was not executed");
    } catch (err) {
      setActionStatus(err?.message || "Unable to execute publishing stabilization action");
    }
    dispatchSemanticNavigation({ surface: "publishing_layer", ...request }, "publishing-layer");
  };

  const executePublishingOptimization = async (recommendation = {}) => {
    const reference = chapterAssembly[0] || {};
    const request = {
      business_id: reference?.assembly_chain?.[0]?.navigation?.business_id,
      compartment_id: reference?.assembly_chain?.[0]?.navigation?.compartment_id,
    };
    if (!recommendation?.action || !request.business_id || !request.compartment_id) {
      setActionStatus("Publishing optimization action is missing context.");
      return;
    }

    try {
      const result = await executeSemanticAction({
        action: recommendation.action,
        request,
        source: "publishing_layer",
        semanticHealth,
      });
      setActionStatus(result?.status === "executed" ? `Executed ${recommendation.label || recommendation.action}` : result?.detail || "Publishing optimization action was not executed");
    } catch (err) {
      setActionStatus(err?.message || "Unable to execute publishing optimization action");
    }
    dispatchSemanticNavigation({ surface: "publishing_layer", ...request }, "publishing-layer");
  };

  return (
    <section id={panelId} className="panel semantic-stack-panel">
      <div className="semantic-stack-head">
        <div>
          <p className="eyebrow">Publishing Layer Hooks</p>
          <h2>Investor + Product E-book Assembly</h2>
        </div>
      </div>

      <div className="publishing-grid">
        <article>
          <h3>Investor E-book Structure</h3>
          <ul>
            {(investor.sections || []).map((item) => <li key={item}>{item}</li>)}
          </ul>
          <p className="status-line">{investor.color_rule || "No color rule defined."}</p>
          <button type="button" onClick={() => setPreviewMode("investor")}>Preview investor assembly</button>
        </article>
        <article>
          <h3>Product Usage E-book Structure</h3>
          <ul>
            {(product.sections || []).map((item) => <li key={item}>{item}</li>)}
          </ul>
          <p className="status-line">{product.color_rule || "No color rule defined."}</p>
          <button type="button" onClick={() => setPreviewMode("product")}>Preview product assembly</button>
        </article>
      </div>

      <section className="rr-node-detail-panel">
        <h3>Generation Preview Hooks</h3>
        <p className="status-line">Active mode: {previewMode}</p>
        <ul>
          {previewSections.map((item) => (
            <li key={`${previewMode}-${item}`}>{item}</li>
          ))}
        </ul>
      </section>

      <section className="publishing-pipeline">
        <h3>SOP to Chapter Assembly Pipeline</h3>
        <div className="rr-node-chip-row">
          {(semanticHealth.checks || []).filter((item) => item.surface === "publishing" || item.surface === "semantic_os").map((item) => (
            <span key={`${item.surface}-${item.status}`}>{item.surface}: {item.status}</span>
          ))}
        </div>
        <div className="rr-node-chip-row">
          <span>Drift {driftReflection.severity}</span>
          <span>Score {driftReflection.score}</span>
          <span>Stabilization {driftReflection.stabilization?.status || "monitor"}</span>
          <span>Pending corrections {driftReflection.stabilization?.progress?.pending_corrections || 0}</span>
        </div>
        <div className="rr-node-chip-row">
          <span>Optimization {optimizationReflection.status}</span>
          <span>Pressure {optimizationReflection.optimizationPressure}</span>
          <span>Publishing readiness {optimizationReflection.publishingReadinessScore}</span>
          <span>Pending optimizations {optimizationReflection.progress.pendingOptimizations}</span>
        </div>
        <div className="rr-node-chip-row">
          {(driftReflection.subjectChips || []).slice(0, 3).map((chip, index) => (
            <span key={`publishing-drift-chip-${index}`}>{chip.subject} {chip.phase} · {chip.severity}</span>
          ))}
        </div>
        <div className="publishing-chain">
          {(pipeline.chain || []).map((item) => (
            <button
              key={item}
              type="button"
              className={activeChainStep === item ? "is-active" : ""}
              onClick={() => setActiveChainStep(item)}
            >
              {item}
            </button>
          ))}
        </div>
        <p className="status-line">
          Required inputs: {(pipeline.required_inputs || []).join(", ") || "not specified"}
        </p>
        {activeChainStep ? <p className="status-line">Transition focus: {activeChainStep}</p> : null}
        <div className="publishing-chain">
          {(driftReflection.stabilization?.recommendations || []).slice(0, 3).map((item, index) => (
            <button key={`publishing-stabilization-${item.action || index}`} type="button" onClick={() => executePublishingStabilization(item)}>
              {item.label || item.action}
            </button>
          ))}
        </div>
        <div className="publishing-chain">
          {(optimizationReflection.recommendations || []).slice(0, 3).map((item, index) => (
            <button key={`publishing-optimization-${item.action || index}`} type="button" onClick={() => executePublishingOptimization(item)}>
              {item.label || item.action}
            </button>
          ))}
        </div>
      </section>

      <section className="publishing-colors">
        <h3>Color-aware Subject Diagram</h3>
        <div className="publishing-chip-row">
          {subjectChips.length > 0 ? subjectChips.map((item) => (
            <span key={item.subject} style={{ borderColor: item.color, color: item.color }}>
              {item.subject}
            </span>
          )) : <span>No RR subjects available yet.</span>}
        </div>
        <div className="publishing-chip-row">
          {(semanticDiagram.subjects || []).map((item, index) => (
            <span key={`${item}-${index}`}>{item}</span>
          ))}
        </div>
      </section>

      <section className="rr-node-detail-panel">
        <h3>Timeline-driven Chapter Assembly</h3>
        <div className="publishing-chain">
          {chapterAssembly.length > 0 ? chapterAssembly.map((item) => (
            <button key={item.chapter_id} type="button" onClick={() => {
              setActiveChainStep(item.chapter_id);
              executeChapterAssembly(item);
            }}>
              {item.subject}
            </button>
          )) : <span>No chapter assembly timeline yet.</span>}
        </div>
        {actionStatus ? <p className="status-line">{actionStatus}</p> : null}
        {chapterAssembly.length > 0 ? (
          <div className="rr-node-chip-row">
            {chapterAssembly.slice(0, 3).map((item) => (
              <span key={item.chapter_id}>{normalizeBreadcrumbs(item.assembly_chain || []).slice(0, 2).join(" → ") || item.adaptive_reason || item.subject}</span>
            ))}
          </div>
        ) : null}
      </section>
    </section>
  );
}
