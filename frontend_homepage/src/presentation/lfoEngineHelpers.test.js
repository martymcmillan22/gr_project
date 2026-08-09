import { describe, expect, it } from "vitest";

import {
  buildLfoEngineViewModel,
  buildMvpFeaturePathways,
  buildSynthesisSnapshot,
  buildTimelineSnapshot,
} from "./lfoEngineHelpers";

describe("lfoEngineHelpers", () => {
  const unifiedState = {
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

  it("builds deterministic timeline snapshot", () => {
    const snapshot = buildTimelineSnapshot(unifiedState);
    expect(snapshot.latest_slot_index).toBe(8);
    expect(snapshot.latest_phase).toBe("Seeds");
    expect(snapshot.alignment_score).toBe(0.8);
  });

  it("builds deterministic synthesis snapshot", () => {
    const snapshot = buildSynthesisSnapshot(unifiedState);
    expect(snapshot.risk_level).toBe("medium");
    expect(snapshot.drift_trend).toBe("rising");
    expect(snapshot.alignment_trajectory).toBe("improving");
  });

  it("builds deterministic project to MVP feature pathways", () => {
    const pathways = buildMvpFeaturePathways({}, unifiedState);
    expect(pathways).toEqual([
      "project_to_mvp_slot_8",
      "seeds_documentation_chain",
      "creator_presentation_scaffold",
      "consumer_gui_science_surface",
    ]);
  });

  it("builds 4-surface LFO view model from LFO envelope", () => {
    const lfoEnvelope = {
      sevm_logical_branches: Array.from({ length: 16 }).map((_, index) => ({ branch_id: `b-${index + 1}` })),
      template_summary: {
        group_template_count: 16,
        industry_template_count: 64,
      },
      group_templates: Array.from({ length: 16 }).map((_, index) => ({
        template_id: `group_lfo_${index + 1}`,
        group_metadata: { group_name: `Group ${index + 1}` },
        sevm_template: { logical_branch_count: 16, synthesis: { risk_level: "medium" } },
      })),
      industry_templates: Array.from({ length: 64 }).map((_, index) => ({ template_id: `industry_${index + 1}` })),
      feature_probability: [
        { feature: "project_to_mvp_slot_8", pipeline: { probability: 0.81 }, grade: "A" },
      ],
      math_surface: {
        mode: "sacp_probability_surface",
        feature_rows: [
          {
            feature: "project_to_mvp_slot_8",
            slot_index: 8,
            probability: 0.81,
            grade: "A",
          },
        ],
      },
      language_surface: {
        mode: "ednp_transcript_surface",
        documents: [
          {
            format: "linear",
            transcript_id: "ednp_linear_8",
            summary: "Deterministic linear transcript",
          },
        ],
      },
      arts_surface: {
        mode: "vlsm_creator_surface",
        creator_scaffolds: Array.from({ length: 16 }).map((_, index) => ({
          template_id: `group_lfo_${index + 1}`,
          group_name: `Group ${index + 1}`,
          branch_count: 16,
          mode: "creator_only",
        })),
      },
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
        ],
      },
    };

    const model = buildLfoEngineViewModel({
      timelineSignalState: {},
      unifiedIntelligenceState: unifiedState,
      lfoEnvelope,
    });

    expect(model.template_summary.group_template_count).toBe(16);
    expect(model.template_summary.industry_template_count).toBe(64);
    expect(model.template_summary.sevm_logical_branch_count).toBe(16);
    expect(model.math_surface.feature_rows[0].grade).toBe("A");
    expect(model.language_surface.document_tracks.length).toBe(1);
    expect(model.language_surface.document_tracks[0].summary).toContain("Deterministic linear transcript");
    expect(model.arts_surface.creator_scaffolds.length).toBe(16);
    expect(model.science_surface.consumer_gui.lenses.length).toBe(2);
    expect(model.science_surface.consumer_gui.lenses[0].interaction_model).toBe("deterministic_behavior");
    expect(model.science_surface.consumer_gui.latest_phase).toBe("seeds");
    expect(model.science_surface.consumer_gui.surface_phase).toBe("seeds");
    expect(model.science_surface.consumer_gui.surface_tiers.studio.unlocked).toBe(false);
    expect(model.industry_surface.template_rows.length).toBe(64);
    expect(model.industry_surface.template_rows[0].has_surface_contract).toBe(true);
    expect(model.industry_surface.template_rows[0].science_lens_count).toBe(0);
    expect(model.micro_surface.template_rows.length).toBe(256);
    expect(model.micro_surface.template_rows[0].has_surface_contract).toBe(true);
    expect(model.micro_surface.template_rows[0].science_lens_count).toBe(4);
  });

  it("derives deterministic industry fallback rows when backend templates are missing", () => {
    const model = buildLfoEngineViewModel({
      timelineSignalState: {},
      unifiedIntelligenceState: unifiedState,
      lfoEnvelope: {
        group_templates: Array.from({ length: 16 }).map((_, index) => ({
          template_id: `group_lfo_${index + 1}`,
          group_metadata: { group_id: index + 1, group_name: `Group ${index + 1}`, sector_name: `Sector ${index + 1}` },
          industries: Array.from({ length: 4 }).map((__, childIndex) => ({
            industry_name: `Industry ${index + 1}-${childIndex + 1}`,
            sub_industries: [`Sub ${index + 1}-${childIndex + 1}`],
          })),
          sevm_template: { branches: Array.from({ length: 16 }).map((__, branchIndex) => ({ branch_id: `b-${branchIndex + 1}` })) },
        })),
      },
    });

    expect(model.industry_templates.length).toBe(64);
    expect(model.industry_surface.template_rows.length).toBe(64);
    expect(model.industry_surface.template_rows[0].has_surface_contract).toBe(true);
    expect(model.industry_surface.template_rows[0].group_name).toBe("Group 1");
    expect(model.micro_templates.length).toBe(64);
    expect(model.micro_surface.template_rows.length).toBe(64);
    expect(model.micro_surface.source).toBe("derived");
  });

  it("derives Studio and Enterprise MBSP surface tiers from post-MVP readiness when backend state is absent", () => {
    const model = buildLfoEngineViewModel({
      timelineSignalState: {},
      unifiedIntelligenceState: {
        semantic_metadata: {
          drift_score: 0.12,
          stability_score: 0.84,
          alignment_score: 0.88,
        },
        slot_progression: {
          latest_slot_index: 16,
          latest_phase: "MVP",
          completion_ratio: 1,
        },
        orchestration: {
          trigger_count: 1,
          priority_queue: [],
        },
        synthesis: {
          risk_clusters: { primary: "low" },
          drift_trend: { direction: "falling" },
          alignment_trajectory: { direction: "improving" },
        },
      },
      lfoEnvelope: {
        science_surface: {
          mode: "mbsp_consumer_gui_surface",
          latest_phase: "mvp",
          completion_ratio: 1,
          trigger_count: 1,
          lenses: [],
        },
      },
    });

    expect(model.science_surface.consumer_gui.surface_phase).toBe("enterprise");
    expect(model.science_surface.consumer_gui.surface_tiers.studio.unlocked).toBe(true);
    expect(model.science_surface.consumer_gui.surface_tiers.enterprise.active).toBe(true);
  });
});
