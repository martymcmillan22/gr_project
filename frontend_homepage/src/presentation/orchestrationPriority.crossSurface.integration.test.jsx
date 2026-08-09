// @vitest-environment jsdom
import { act } from "react";
import { createRoot } from "react-dom/client";
import { afterEach, describe, expect, it, vi } from "vitest";

import PublishingLayerHooksPanel from "./PublishingLayerHooksPanel";
import SemanticIntelligencePanel from "./SemanticIntelligencePanel";
import SopWorkflowScaffoldPanel from "./SopWorkflowScaffoldPanel";
import VaSemanticGuidancePanel from "./VaSemanticGuidancePanel";
import {
  buildUnifiedPlatformIntelligenceState,
  buildTimelineOrchestrationPriorityQueue,
  createTimelineSignalState,
  reduceTimelineSlotSignal,
} from "./semanticOsHelpers";

globalThis.IS_REACT_ACT_ENVIRONMENT = true;

vi.mock("../api/homepageApi", () => ({
  executeRrSemanticAction: vi.fn(async () => ({ status: "noop" })),
  fetchRrSemanticIntelligence: vi.fn(async () => ({})),
  fetchRrVaGuidance: vi.fn(async () => ({
    signals: {
      dominant_compartments: [],
      integrity_mismatch_hotspots: [],
    },
    recommendations: [],
  })),
}));

function buildTimelineStateForPriorityValidation() {
  return reduceTimelineSlotSignal(createTimelineSignalState(), {
    event_type: "slot_completion",
    slot_index: 4,
    phase: "Ideas",
    slot_completed: true,
    gate_locked: false,
    completed_slots: [1, 2, 3, 4],
    semantic_state: {
      drift_score: 0.9,
      stability_score: 0.45,
      alignment_score: 0.3,
    },
    industry_metadata: {
      group_name: "Math",
      industry: "Software",
    },
  });
}

function buildTimelineStateForMbspSurfaceValidation() {
  return reduceTimelineSlotSignal(createTimelineSignalState(), {
    event_type: "slot_completion",
    slot_index: 16,
    phase: "MVP",
    slot_completed: true,
    gate_locked: false,
    completed_slots: Array.from({ length: 16 }, (_, index) => index + 1),
    semantic_state: {
      drift_score: 0.12,
      stability_score: 0.84,
      alignment_score: 0.88,
    },
    industry_metadata: {
      group_name: "Systemics",
      industry: "Operations",
    },
  });
}

function extractTriggerIds(container, scopeSelector) {
  const root = scopeSelector ? container.querySelector(scopeSelector) : container;
  if (!root) {
    return [];
  }
  return Array.from(root.querySelectorAll("[data-orchestration-trigger]"))
    .map((node) => node.getAttribute("data-orchestration-trigger"))
    .filter(Boolean);
}

describe("orchestration priority cross-surface integration", () => {
  let containers = [];
  let roots = [];

  afterEach(async () => {
    while (roots.length > 0) {
      const root = roots.pop();
      await act(async () => {
        root.unmount();
      });
    }
    containers.forEach((container) => {
      if (container.parentNode) {
        container.parentNode.removeChild(container);
      }
    });
    containers = [];
  });

  it("keeps identical deterministic trigger ordering across Intelligence, VA, SOP/Workflow, and Publishing surfaces", async () => {
    const timelineSignalState = buildTimelineStateForPriorityValidation();
    const unifiedIntelligenceState = buildUnifiedPlatformIntelligenceState(timelineSignalState);
    const expected = buildTimelineOrchestrationPriorityQueue(timelineSignalState).map((item) => item.id);

    const semanticIntelligencePayload = {
      semantic_os_health: { checks: [] },
      recommendation_engine: { recommendations: [], timeline_aware_recommendations: [] },
      workflow_intelligence: { bottlenecks: [], provenance_chains: [] },
      publishing_intelligence: { chapter_previews: [], chapter_assembly: [], semantic_diagram: { subjects: [] } },
      rr_semantic_analytics: { subject_mix: { subjects: [] } },
      semantic_action_engine: { action_bundles: [] },
      semantic_action_log: { entries: [] },
      semantic_feedback_loop: {},
      semantic_os_unification: { consistency_checks: [], timeline_breadcrumbs: [] },
    };

    const sopRrDashboard = {
      lanes: [
        {
          compartment_id: 1,
          cards: [
            {
              business_id: 101,
              title: "Math Workflow",
              subject: "Math",
              phase: "Ideas",
              integrity_state: "aligned",
              display_rgb: { r: 80, g: 110, b: 180 },
              provenance: { workflow_refs: [], sop_refs: [] },
              seed_id: 11,
            },
          ],
        },
      ],
    };

    const publishingStack = {
      tracks: {
        publishing_layer: {
          investor_ebook: { sections: ["intro"], color_rule: "deterministic" },
          product_usage_ebook: { sections: ["usage"], color_rule: "deterministic" },
          sop_to_ebook_pipeline: { chain: ["capture"], required_inputs: ["rr"] },
        },
        operational_architecture: {
          workflow_schema: {
            macro: ["macro"],
            micro: ["micro"],
            provenance: ["provenance"],
          },
        },
      },
    };

    const intelligenceContainer = document.createElement("div");
    const vaContainer = document.createElement("div");
    const sopContainer = document.createElement("div");
    const publishingContainer = document.createElement("div");
    [intelligenceContainer, vaContainer, sopContainer, publishingContainer].forEach((container) => {
      document.body.appendChild(container);
      containers.push(container);
    });

    const intelligenceRoot = createRoot(intelligenceContainer);
    const vaRoot = createRoot(vaContainer);
    const sopRoot = createRoot(sopContainer);
    const publishingRoot = createRoot(publishingContainer);
    roots.push(intelligenceRoot, vaRoot, sopRoot, publishingRoot);

    await act(async () => {
      intelligenceRoot.render(
        <SemanticIntelligencePanel
          semanticIntelligence={semanticIntelligencePayload}
          semanticIntelligenceLoading={false}
          semanticIntelligenceError=""
          semanticActionHistory={[]}
          semanticActionFeedback={{}}
          timelineSignalState={timelineSignalState}
          unifiedIntelligenceState={unifiedIntelligenceState}
        />,
      );
      vaRoot.render(
        <VaSemanticGuidancePanel
          semanticIntelligence={semanticIntelligencePayload}
          semanticActionFeedback={{}}
          timelineSignalState={timelineSignalState}
          unifiedIntelligenceState={unifiedIntelligenceState}
        />,
      );
      sopRoot.render(
        <SopWorkflowScaffoldPanel
          rrDashboard={sopRrDashboard}
          operatingStack={publishingStack}
          semanticIntelligence={semanticIntelligencePayload}
          semanticActionFeedback={{}}
          timelineSignalState={timelineSignalState}
          unifiedIntelligenceState={unifiedIntelligenceState}
        />,
      );
      publishingRoot.render(
        <PublishingLayerHooksPanel
          operatingStack={publishingStack}
          rrDashboard={sopRrDashboard}
          semanticIntelligence={semanticIntelligencePayload}
          semanticActionFeedback={{}}
          timelineSignalState={timelineSignalState}
          unifiedIntelligenceState={unifiedIntelligenceState}
        />,
      );
    });

    await act(async () => {
      await Promise.resolve();
    });

    const intelligenceTriggers = extractTriggerIds(intelligenceContainer);
    const vaTriggers = extractTriggerIds(vaContainer);
    const workflowTriggers = extractTriggerIds(sopContainer, ".workflow-swimlanes");
    const publishingTriggers = extractTriggerIds(publishingContainer, ".publishing-pipeline");

    const riskLabels = [
      intelligenceContainer.querySelector("[data-intelligence-risk-level]")?.textContent,
      vaContainer.querySelector("[data-intelligence-risk-level]")?.textContent,
      sopContainer.querySelector("[data-intelligence-risk-level]")?.textContent,
      publishingContainer.querySelector("[data-intelligence-risk-level]")?.textContent,
    ].filter(Boolean);

    const driftTrendLabels = [
      intelligenceContainer.querySelector("[data-intelligence-drift-trend]")?.textContent,
      vaContainer.querySelector("[data-intelligence-drift-trend]")?.textContent,
      sopContainer.querySelector("[data-intelligence-drift-trend]")?.textContent,
      publishingContainer.querySelector("[data-intelligence-drift-trend]")?.textContent,
    ].filter(Boolean);

    const alignmentTrajectoryLabels = [
      intelligenceContainer.querySelector("[data-intelligence-alignment-trajectory]")?.textContent,
      vaContainer.querySelector("[data-intelligence-alignment-trajectory]")?.textContent,
      sopContainer.querySelector("[data-intelligence-alignment-trajectory]")?.textContent,
      publishingContainer.querySelector("[data-intelligence-alignment-trajectory]")?.textContent,
    ].filter(Boolean);

    expect(intelligenceTriggers).toEqual(expected);
    expect(vaTriggers).toEqual(expected);
    expect(workflowTriggers).toEqual(expected);
    expect(publishingTriggers).toEqual(expected);
    expect(new Set(riskLabels).size).toBe(1);
    expect(new Set(driftTrendLabels).size).toBe(1);
    expect(new Set(alignmentTrajectoryLabels).size).toBe(1);
  });

  it("propagates identical MBSP Studio and Enterprise surface states across semantic panels", async () => {
    const timelineSignalState = buildTimelineStateForMbspSurfaceValidation();
    const unifiedIntelligenceState = buildUnifiedPlatformIntelligenceState(timelineSignalState);

    const semanticIntelligencePayload = {
      semantic_os_health: { checks: [] },
      recommendation_engine: { recommendations: [], timeline_aware_recommendations: [] },
      workflow_intelligence: { bottlenecks: [], provenance_chains: [] },
      publishing_intelligence: { chapter_previews: [], chapter_assembly: [], semantic_diagram: { subjects: [] } },
      rr_semantic_analytics: { subject_mix: { subjects: [] } },
      semantic_action_engine: { action_bundles: [] },
      semantic_action_log: { entries: [] },
      semantic_feedback_loop: {},
      semantic_os_unification: { consistency_checks: [], timeline_breadcrumbs: [] },
    };

    const sopRrDashboard = {
      lanes: [
        {
          compartment_id: 16,
          cards: [
            {
              business_id: 101,
              title: "Systemics Workflow",
              subject: "Systemics",
              phase: "MVP",
              integrity_state: "aligned",
              display_rgb: { r: 80, g: 110, b: 180 },
              provenance: { workflow_refs: [], sop_refs: [] },
              seed_id: 11,
            },
          ],
        },
      ],
    };

    const publishingStack = {
      tracks: {
        publishing_layer: {
          investor_ebook: { sections: ["intro"], color_rule: "deterministic" },
          product_usage_ebook: { sections: ["usage"], color_rule: "deterministic" },
          sop_to_ebook_pipeline: { chain: ["capture"], required_inputs: ["rr"] },
        },
        operational_architecture: {
          workflow_schema: {
            macro: ["macro"],
            micro: ["micro"],
            provenance: ["provenance"],
          },
        },
      },
    };

    const intelligenceContainer = document.createElement("div");
    const vaContainer = document.createElement("div");
    const sopContainer = document.createElement("div");
    const publishingContainer = document.createElement("div");
    [intelligenceContainer, vaContainer, sopContainer, publishingContainer].forEach((container) => {
      document.body.appendChild(container);
      containers.push(container);
    });

    const intelligenceRoot = createRoot(intelligenceContainer);
    const vaRoot = createRoot(vaContainer);
    const sopRoot = createRoot(sopContainer);
    const publishingRoot = createRoot(publishingContainer);
    roots.push(intelligenceRoot, vaRoot, sopRoot, publishingRoot);

    await act(async () => {
      intelligenceRoot.render(
        <SemanticIntelligencePanel
          semanticIntelligence={semanticIntelligencePayload}
          semanticIntelligenceLoading={false}
          semanticIntelligenceError=""
          semanticActionHistory={[]}
          semanticActionFeedback={{}}
          timelineSignalState={timelineSignalState}
          unifiedIntelligenceState={unifiedIntelligenceState}
        />,
      );
      vaRoot.render(
        <VaSemanticGuidancePanel
          semanticIntelligence={semanticIntelligencePayload}
          semanticActionFeedback={{}}
          timelineSignalState={timelineSignalState}
          unifiedIntelligenceState={unifiedIntelligenceState}
        />,
      );
      sopRoot.render(
        <SopWorkflowScaffoldPanel
          rrDashboard={sopRrDashboard}
          operatingStack={publishingStack}
          semanticIntelligence={semanticIntelligencePayload}
          semanticActionFeedback={{}}
          timelineSignalState={timelineSignalState}
          unifiedIntelligenceState={unifiedIntelligenceState}
        />,
      );
      publishingRoot.render(
        <PublishingLayerHooksPanel
          operatingStack={publishingStack}
          rrDashboard={sopRrDashboard}
          semanticIntelligence={semanticIntelligencePayload}
          semanticActionFeedback={{}}
          timelineSignalState={timelineSignalState}
          unifiedIntelligenceState={unifiedIntelligenceState}
        />,
      );
    });

    await act(async () => {
      await Promise.resolve();
    });

    const mbspPhases = [
      intelligenceContainer.querySelector("[data-intelligence-mbsp-phase]")?.textContent,
      vaContainer.querySelector("[data-intelligence-mbsp-phase]")?.textContent,
      sopContainer.querySelector("[data-intelligence-mbsp-phase]")?.textContent,
      publishingContainer.querySelector("[data-intelligence-mbsp-phase]")?.textContent,
    ].filter(Boolean);

    const studioStates = [
      intelligenceContainer.querySelector("[data-intelligence-mbsp-studio]")?.textContent,
      vaContainer.querySelector("[data-intelligence-mbsp-studio]")?.textContent,
      sopContainer.querySelector("[data-intelligence-mbsp-studio]")?.textContent,
      publishingContainer.querySelector("[data-intelligence-mbsp-studio]")?.textContent,
    ].filter(Boolean);

    const enterpriseStates = [
      intelligenceContainer.querySelector("[data-intelligence-mbsp-enterprise]")?.textContent,
      vaContainer.querySelector("[data-intelligence-mbsp-enterprise]")?.textContent,
      sopContainer.querySelector("[data-intelligence-mbsp-enterprise]")?.textContent,
      publishingContainer.querySelector("[data-intelligence-mbsp-enterprise]")?.textContent,
    ].filter(Boolean);

    expect(new Set(mbspPhases).size).toBe(1);
    expect(mbspPhases[0]).toContain("enterprise");
    expect(new Set(studioStates).size).toBe(1);
    expect(studioStates[0]).toContain("unlocked");
    expect(new Set(enterpriseStates).size).toBe(1);
    expect(enterpriseStates[0]).toContain("active");
  });
});
