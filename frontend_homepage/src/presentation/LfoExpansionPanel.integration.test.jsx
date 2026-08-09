// @vitest-environment jsdom
import { act } from "react";
import { createRoot } from "react-dom/client";
import { afterEach, describe, expect, it, vi } from "vitest";

import { fetchProjectMiddleLayerLfoEngine } from "../api/homepageApi";
import LfoExpansionPanel from "./LfoExpansionPanel";

globalThis.IS_REACT_ACT_ENVIRONMENT = true;

vi.mock("../api/homepageApi", () => ({
  fetchProjectMiddleLayerLfoEngine: vi.fn(),
}));

describe("LfoExpansionPanel integration", () => {
  let container;
  let root;

  afterEach(async () => {
    vi.clearAllMocks();
    if (root) {
      await act(async () => {
        root.unmount();
      });
    }
    root = null;
    if (container?.parentNode) {
      container.parentNode.removeChild(container);
    }
    container = null;
  });

  it("requests deterministic envelope and renders all four LFO surfaces", async () => {
    fetchProjectMiddleLayerLfoEngine.mockResolvedValue({
      sevm_logical_branches: Array.from({ length: 16 }).map((_, index) => ({
        branch_id: `branch_${index + 1}`,
      })),
      template_summary: {
        group_template_count: 16,
        industry_template_count: 64,
      },
      group_templates: Array.from({ length: 16 }).map((_, index) => ({
        template_id: `group_${index + 1}`,
        group_metadata: { group_name: `Group ${index + 1}` },
        sevm_template: {
          logical_branch_count: 16,
          synthesis: { risk_level: "medium" },
        },
      })),
      industry_templates: Array.from({ length: 64 }).map((_, index) => ({
        template_id: `industry_lfo_${String(Math.floor(index / 4) + 1).padStart(2, "0")}_${String((index % 4) + 1).padStart(2, "0")}`,
        group_name: `Group ${Math.floor(index / 4) + 1}`,
        industry_name: `Industry ${index + 1}`,
        branch_ids: Array.from({ length: 16 }).map((__, branchIndex) => `branch-${branchIndex + 1}`),
        timeline_binding: {
          latest_slot_index: 8,
          latest_phase: "Seeds",
        },
        surface_contract: {
          math: { mode: "sacp_probability_surface" },
          language: { mode: "ednp_transcript_surface" },
          arts: { mode: "vlsm_creator_surface" },
          science: { mode: "mbsp_consumer_gui_surface", lenses: [] },
        },
      })),
      micro_templates: Array.from({ length: 256 }).map((_, index) => ({
        template_id: `micro_lfo_${String(Math.floor(index / 16) + 1).padStart(2, "0")}_${String((index % 16) + 1).padStart(2, "0")}`,
        inherits_from: `industry_lfo_${String(Math.floor(index / 4) + 1).padStart(2, "0")}_${String((index % 4) + 1).padStart(2, "0")}`,
        group_name: `Group ${Math.floor(index / 16) + 1}`,
        industry_name: `Industry ${Math.floor(index / 4) + 1}`,
        sub_industry_name: `Sub Industry ${index + 1}`,
        branch_ids: Array.from({ length: 16 }).map((__, branchIndex) => `branch-${branchIndex + 1}`),
        timeline_binding: {
          latest_slot_index: 8,
          latest_phase: "Seeds",
        },
        surface_contract: {
          math: { mode: "sacp_probability_surface", feature_rows: [{ feature: `micro_${index + 1}` }] },
          language: { mode: "ednp_transcript_surface", documents: [{ format: "linear" }, { format: "2x_linear" }, { format: "12_point" }, { format: "perpetual" }] },
          arts: { mode: "vlsm_creator_surface", creator_scaffolds: [{ template_id: `micro_${index + 1}` }] },
          science: { mode: "mbsp_consumer_gui_surface", lenses: [{}, {}, {}, {}] },
        },
        inheritance: { override_allowed: false },
      })),
      feature_probability: [
        {
          feature: "project_to_mvp_slot_8",
          grade: "A",
          pipeline: { probability: 0.812 },
        },
      ],
      language_surface: {
        mode: "ednp_transcript_surface",
        documents: [
          {
            format: "linear",
            transcript_id: "ednp_linear_8",
            summary: "Deterministic linear transcript for seeds slot 8.",
          },
        ],
      },
      science_surface: {
        mode: "mbsp_consumer_gui_surface",
        latest_phase: "seeds",
        surface_phase: "seeds",
        surface_tiers: {
          studio: { phase: "studio", unlocked: false, active: false, readiness_score: 0.61 },
          enterprise: { phase: "enterprise", unlocked: false, active: false, readiness_score: 0.55 },
        },
        completion_ratio: 0.5,
        trigger_count: 3,
        lenses: [
          { lens: "math_logic", behavior_score: 0.77, interaction_model: "deterministic_behavior" },
          { lens: "biology", behavior_score: 0.74, interaction_model: "organic_interaction_flow" },
          { lens: "social", behavior_score: 0.7, interaction_model: "collaborative_community_patterns" },
          { lens: "physical", behavior_score: 0.71, interaction_model: "deployment_visual_physics" },
        ],
      },
    });

    const timelineSignalState = {
      latest_event: {
        slot_index: 8,
        phase: "Seeds",
      },
    };

    const unifiedIntelligenceState = {
      semantic_metadata: {
        drift_score: 0.2,
        stability_score: 0.85,
        alignment_score: 0.8,
      },
      slot_progression: {
        latest_slot_index: 8,
        latest_phase: "Seeds",
        completion_ratio: 0.5,
      },
      orchestration: {
        trigger_count: 3,
        priority_queue: [{ id: "drift_spike", priority: "critical" }],
      },
      synthesis: {
        risk_clusters: { primary: "medium" },
        drift_trend: { direction: "rising" },
        alignment_trajectory: { direction: "improving" },
      },
    };

    container = document.createElement("div");
    document.body.appendChild(container);
    root = createRoot(container);

    await act(async () => {
      root.render(
        <LfoExpansionPanel
          timelineSignalState={timelineSignalState}
          unifiedIntelligenceState={unifiedIntelligenceState}
        />,
      );
    });

    await act(async () => {
      await Promise.resolve();
    });

    expect(fetchProjectMiddleLayerLfoEngine).toHaveBeenCalledTimes(1);
    expect(fetchProjectMiddleLayerLfoEngine).toHaveBeenCalledWith({
      timeline_snapshot: {
        latest_slot_index: 8,
        latest_phase: "Seeds",
        drift_score: 0.2,
        stability_score: 0.85,
        alignment_score: 0.8,
        completion_ratio: 0.5,
      },
      synthesis_snapshot: {
        risk_level: "medium",
        drift_trend: "rising",
        alignment_trajectory: "improving",
      },
      trigger_count: 3,
      feature_pathways: [
        "project_to_mvp_slot_8",
        "seeds_documentation_chain",
        "creator_presentation_scaffold",
        "consumer_gui_science_surface",
      ],
    });

    const text = container.textContent || "";
    expect(text).toContain("4-Surface LFO Engine");
    expect(text).toContain("SEVM logical branches 16");
    expect(text).toContain("Industry Group templates 16");
    expect(text).toContain("Industry templates 64");
    expect(text).toContain("Math (SACP)");
    expect(text).toContain("Language (EDNP)");
    expect(text).toContain("Arts (VLSM)");
    expect(text).toContain("Industry Templates");
    expect(text).toContain("Fallback backend");
    expect(text).toContain("Micro Templates");
    expect(text).toContain("Micro templates 256");
    expect(text).toContain("Science (MBSP)");
    expect(text).toContain("linear: ednp_linear_8 - Deterministic linear transcript for seeds slot 8.");
    expect(text).toContain("Latest phase seeds");
    expect(text).toContain("Surface phase seeds");
    expect(text).toContain("Studio tier locked");
    expect(text).toContain("Enterprise tier locked");
    expect(text).toContain("math_logic: deterministic_behavior");
  });

  it("falls back to derived industry templates when backend templates are absent", async () => {
    fetchProjectMiddleLayerLfoEngine.mockResolvedValue({
      sevm_logical_branches: Array.from({ length: 16 }).map((_, index) => ({
        branch_id: `branch_${index + 1}`,
      })),
      template_summary: {
        group_template_count: 16,
        industry_template_count: 64,
      },
      group_templates: Array.from({ length: 16 }).map((_, index) => ({
        template_id: `group_${index + 1}`,
        group_metadata: { group_id: index + 1, group_name: `Group ${index + 1}`, sector_name: `Sector ${index + 1}` },
        industries: Array.from({ length: 4 }).map((__, childIndex) => ({
          industry_name: `Industry ${index + 1}-${childIndex + 1}`,
          sub_industries: [`Sub ${index + 1}-${childIndex + 1}`],
        })),
        sevm_template: {
          logical_branch_count: 16,
          synthesis: { risk_level: "medium" },
          branches: Array.from({ length: 16 }).map((__, branchIndex) => ({ branch_id: `branch-${branchIndex + 1}` })),
        },
      })),
      feature_probability: [],
      math_surface: { mode: "sacp_probability_surface", feature_rows: [] },
      language_surface: { mode: "ednp_transcript_surface", documents: [] },
      arts_surface: { mode: "vlsm_creator_surface", creator_scaffolds: [] },
      science_surface: {
        mode: "mbsp_consumer_gui_surface",
        latest_phase: "ideas",
        completion_ratio: 0.25,
        trigger_count: 0,
        lenses: [],
      },
      micro_templates: Array.from({ length: 256 }).map((_, index) => ({
        template_id: `micro_lfo_${String(Math.floor(index / 16) + 1).padStart(2, "0")}_${String((index % 16) + 1).padStart(2, "0")}`,
        inherits_from: `industry_lfo_${String(Math.floor(index / 4) + 1).padStart(2, "0")}_${String((index % 4) + 1).padStart(2, "0")}`,
        group_name: `Group ${Math.floor(index / 16) + 1}`,
        industry_name: `Industry ${Math.floor(index / 4) + 1}`,
        sub_industry_name: `Sub Industry ${index + 1}`,
        branch_ids: Array.from({ length: 16 }).map((__, branchIndex) => `branch-${branchIndex + 1}`),
        timeline_binding: {
          latest_slot_index: 1,
          latest_phase: "Ideas",
        },
        surface_contract: {
          math: { mode: "sacp_probability_surface", feature_rows: [{ feature: `micro_${index + 1}` }] },
          language: { mode: "ednp_transcript_surface", documents: [{ format: "linear" }, { format: "2x_linear" }, { format: "12_point" }, { format: "perpetual" }] },
          arts: { mode: "vlsm_creator_surface", creator_scaffolds: [{ template_id: `micro_${index + 1}` }] },
          science: { mode: "mbsp_consumer_gui_surface", lenses: [{}, {}, {}, {}] },
        },
        inheritance: { override_allowed: false },
      })),
    });

    const timelineSignalState = {};
    const unifiedIntelligenceState = {
      semantic_metadata: { drift_score: 0.2, stability_score: 0.8, alignment_score: 0.8 },
      slot_progression: { latest_slot_index: 1, latest_phase: "Ideas", completion_ratio: 0.25 },
      orchestration: { trigger_count: 0, priority_queue: [] },
      synthesis: {
        risk_clusters: { primary: "low" },
        drift_trend: { direction: "stable" },
        alignment_trajectory: { direction: "stable" },
      },
    };

    container = document.createElement("div");
    document.body.appendChild(container);
    root = createRoot(container);

    await act(async () => {
      root.render(
        <LfoExpansionPanel
          timelineSignalState={timelineSignalState}
          unifiedIntelligenceState={unifiedIntelligenceState}
        />,
      );
    });

    await act(async () => {
      await Promise.resolve();
    });

    const text = container.textContent || "";
    expect(text).toContain("Industry Templates");
    expect(text).toContain("Fallback derived");
    expect(text).toContain("Industry templates 64");
    expect(text).toContain("Micro Templates");
    expect(text).toContain("Micro templates 256");
  });
});
