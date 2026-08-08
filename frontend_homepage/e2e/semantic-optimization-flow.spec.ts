import { expect, test } from "@playwright/test";
import type { Page } from "@playwright/test";

type ActionLogEntry = {
  recorded_at: string;
  action: string;
  status: string;
  source_surface: string;
  business_id: number;
  compartment_id: number;
  subject: string;
  phase: string;
  breadcrumbs: string[];
  timeline_entry: {
    event_type: string;
    surface: string;
  };
  provenance_update: {
    depth: number;
  };
  publishing_signal: {
    status: string;
  };
  workflow_step_result: {
    status: string;
  };
};

function buildFeedbackLoop(executedOptimizations: number, actionLog: ActionLogEntry[]) {
  const pendingOptimizations = Math.max(0, 4 - executedOptimizations);
  return {
    adaptive_hints: [
      {
        type: "next_action",
        message: "If workflow actions cluster in one subject, route next action through VA guidance before publishing.",
      },
      {
        type: "timeline_alignment",
        message: "Timeline currently has 2 subject-phase clusters; align next action to top cluster.",
      },
    ],
    stability_signals: {
      recent_failures: 0,
      recent_blocked: 0,
      repeated_action_pattern: executedOptimizations >= 3,
      drift_detected: executedOptimizations >= 1,
    },
    drift_alerts: [],
    drift_detection: {
      severity: "low",
      score: executedOptimizations > 0 ? 2 : 0,
      workflow_stalled: false,
      subject_imbalance: executedOptimizations >= 3,
      provenance_gaps: 0,
      timeline_cluster_pressure: 2,
      publishing_gap: false,
      subject_drift_chips: executedOptimizations >= 3
        ? [{ subject: "Language", phase: "Primary", severity: "warn", reason: "Repeated actions", count: executedOptimizations }]
        : [{ subject: "Language", phase: "Primary", severity: "monitor", reason: "Nominal", count: executedOptimizations }],
    },
    stabilization_loop: {
      status: executedOptimizations > 0 ? "active" : "monitor",
      progress: {
        total_recommendations: 1,
        executed_corrections: 0,
        pending_corrections: executedOptimizations > 0 ? 1 : 0,
      },
      recommendations: [{ action: "rebalance_subject_mix", label: "Rebalance subject mix", reason: "Drift pressure" }],
    },
    optimization_loop: {
      status: executedOptimizations > 0 ? "active" : "monitor",
      signals: {
        subject_mix_score: 34,
        workflow_efficiency_score: 100,
        publishing_readiness_score: 60 + executedOptimizations * 4,
        optimization_pressure: Math.max(0, 36 - executedOptimizations * 2),
        trend: executedOptimizations > 0 ? "improving" : "monitor",
        dominant_subject: "Language",
        provenance_depth_ready: true,
      },
      progress: {
        total_recommendations: 4,
        executed_optimizations: executedOptimizations,
        pending_optimizations: pendingOptimizations,
        improvement_cycles: 0,
      },
      auto_balancing: {
        required: true,
        target_subject: "Language",
        target_compartment_id: 1,
        message: "Auto balancing active",
      },
      recommendations: [
        { action: "rebalance_subject_load", label: "Rebalance subject load", reason: "Subject concentration" },
        { action: "improve_subject_balance", label: "Improve subject balance", reason: "Publishing coherence" },
        { action: "improve_publishing_readiness", label: "Improve publishing readiness", reason: "Readiness score" },
      ],
    },
    grouped_actions: [],
    recent_failures: 0,
    recent_blocked: 0,
    drift_detected: executedOptimizations > 0,
    action_log: actionLog,
  };
}

function buildSemanticIntelligence(actionLog: ActionLogEntry[]) {
  const executedOptimizations = actionLog.length;
  const feedbackLoop = buildFeedbackLoop(executedOptimizations, actionLog);
  return {
    mode: "semantic_intelligence",
    rr_semantic_analytics: {
      lane_count: 16,
      active_lane_count: 1,
      status_bands: { Idea: 0, Seed: 0, Project: 1, Archived: 0 },
      integrity_strip: { ok: 1, mismatch: 0, unavailable: 0 },
      subject_mix: {
        total_nodes: 1,
        subjects: [{ compartment_id: 1, subject: "Language", phase: "Primary", node_count: 1, node_share: 1 }],
      },
    },
    recommendation_engine: {
      recommendations: [
        {
          type: "rr_node_focus",
          message: "Focus RR nodes in Language to stabilize Primary throughput.",
          compartment_id: 1,
          subject: "Language",
          phase: "Primary",
          navigation: { surface: "rr_dashboard", compartment_id: 1, business_id: 1 },
        },
      ],
      timeline_aware_recommendations: [
        {
          type: "timeline_cluster",
          message: "Timeline has 4 cross-surface events ready for drill-down.",
          navigation: { surface: "rr_dashboard", compartment_id: 1, business_id: 1 },
        },
      ],
    },
    workflow_intelligence: {
      bottlenecks: [],
      provenance_chains: [
        {
          compartment_id: 1,
          subject: "Language",
          phase: "Primary",
          business_id: 1,
          breadcrumbs: ["workflow", "rr-sop-1"],
          chain: ["rr", "workflow", "publishing"],
          depth: 5,
        },
      ],
    },
    va_action_engine: {
      timeline_actions: [],
      semantic_coaching: [],
    },
    publishing_intelligence: {
      chapter_previews: [
        {
          chapter_id: "chapter-1",
          title: "Language Chapter Preview",
          subject: "Language",
          phase: "Primary",
          compartment_id: 1,
          color: { r: [0, 63], g: [0, 63], b: [192, 255] },
        },
      ],
      chapter_assembly: [],
      semantic_diagram: { subjects: ["Language"] },
    },
    unified_timeline: [],
    timeline_groups: [
      {
        subject: "Language",
        phase: "Primary",
        count: 2,
        items: [],
        navigation_targets: ["rr_dashboard", "publishing_layer"],
      },
    ],
    semantic_os_health: {
      ready: true,
      checks: [
        { surface: "rr", status: "pass" },
        { surface: "workflow", status: "pass" },
        { surface: "va", status: "pass" },
        { surface: "publishing", status: "pass" },
        { surface: "timeline", status: "pass" },
        { surface: "provenance_depth", status: "pass" },
        { surface: "action_log", status: "pass" },
        { surface: "workflow_stability", status: "pass" },
        { surface: "semantic_drift", status: "pass" },
        { surface: "stabilization_loop", status: executedOptimizations > 0 ? "warn" : "pass" },
        { surface: "resilience_consistency", status: "pass" },
        { surface: "optimization_loop", status: "pass" },
        { surface: "improvement_loop_consistency", status: "pass" },
      ],
      optimization: {
        status: feedbackLoop.optimization_loop.status,
        subject_mix_score: feedbackLoop.optimization_loop.signals.subject_mix_score,
        workflow_efficiency_score: feedbackLoop.optimization_loop.signals.workflow_efficiency_score,
        publishing_readiness_score: feedbackLoop.optimization_loop.signals.publishing_readiness_score,
        executed_optimizations: feedbackLoop.optimization_loop.progress.executed_optimizations,
        pending_optimizations: feedbackLoop.optimization_loop.progress.pending_optimizations,
        ready: true,
      },
    },
    semantic_action_engine: {
      action_vocabulary: [
        { action: "optimize_workflow_path" },
        { action: "improve_publishing_readiness" },
        { action: "rebalance_subject_load" },
      ],
      action_bundles: [
        {
          bundle_id: "optimization-workflow-efficiency-bundle",
          title: "Workflow Efficiency Optimization Bundle",
          actions: ["optimize_workflow_path"],
          default_request: { surface: "workflow_swimlanes", business_id: 1, compartment_id: 1, workflow_step: "optimize" },
        },
        {
          bundle_id: "optimization-publishing-readiness-bundle",
          title: "Publishing Readiness Optimization Bundle",
          actions: ["improve_publishing_readiness"],
          default_request: { surface: "publishing_layer", business_id: 1, compartment_id: 1 },
        },
        {
          bundle_id: "optimization-subject-balance-bundle",
          title: "Subject Balance Optimization Bundle",
          actions: ["rebalance_subject_load"],
          default_request: { surface: "rr_dashboard", business_id: 1, compartment_id: 1, workflow_step: "optimize" },
        },
      ],
      stabilization_recommendations: [{ action: "rebalance_subject_mix", label: "Rebalance subject mix" }],
      optimization_recommendations: feedbackLoop.optimization_loop.recommendations,
    },
    semantic_action_log: {
      entries: actionLog,
    },
    semantic_feedback_loop: feedbackLoop,
    semantic_optimization: feedbackLoop.optimization_loop,
    semantic_os_unification: {
      consistency_checks: [
        { surface: "rr", status: "pass" },
        { surface: "middle_layer", status: "pass" },
        { surface: "va", status: "pass" },
        { surface: "workflow", status: "warn" },
        { surface: "publishing", status: "pass" },
        { surface: "semantic_os", status: "pass" },
        { surface: "drift_detection", status: "pass" },
        { surface: "stabilization", status: executedOptimizations > 0 ? "warn" : "pass" },
        { surface: "optimization", status: "pass" },
        { surface: "optimization_reflection", status: "pass" },
      ],
      timeline_breadcrumbs: [
        ["engine-truth", "rr", "Language", "Primary"],
      ],
    },
  };
}

function buildDashboardPayload() {
  return {
    mode: "rr_dashboard",
    lane_count: 16,
    status_bands: { Idea: 0, Seed: 0, Project: 1, Archived: 0 },
    integrity_strip: { ok: 1, mismatch: 0, unavailable: 0 },
    lanes: [
      {
        compartment_id: 1,
        subject: "Language",
        phase: "Primary",
        label: "Blue",
        display_anchor_band: { r: [0, 63], g: [0, 63], b: [192, 255] },
        node_count: 1,
        integrity: { ok: 1, mismatch: 0, unavailable: 0 },
        phase_distribution: { Idea: 0, Seed: 0, Project: 1, Archived: 0 },
        cards: [
          {
            business_id: 1,
            seed_id: 1,
            title: "Phase40 Validation Node",
            subject: "Language",
            phase: "Project",
            industry_path: ["Primary (Create Phase)", "Language", "Software", "Enterprise Operating System Architecture"],
            sector: "Primary (Create Phase)",
            industry: "Software",
            subindustry: "Enterprise Operating System Architecture",
            display_rgb: { r: 0, g: 0, b: 192 },
            card_color_spec: {
              compartment_tag: { compartment_id: 1 },
              integrity_indicator: { ok: "#16a34a", mismatch: "#f97316", unavailable: "#64748b" },
            },
            integrity_state: "ok",
            provenance: { workflow_refs: [{ workflow_id: "wf-1" }], sop_refs: [{ sop_id: "rr-sop-1" }] },
          },
        ],
      },
    ],
  };
}

async function stubSemanticIspeApis(page: Page) {
  const dashboardPayload = buildDashboardPayload();
  const cardSpecPayload = {
    mode: "rr_card_color_spec",
    cards: [{ compartment_id: 1, subject: "Language", phase: "Primary", spec: { accent_rgb: { r: 0, g: 0, b: 192 }, integrity_indicator: { ok: "#16a34a", mismatch: "#f97316", unavailable: "#64748b" } }, layout_modes: ["compact", "expanded"] }],
  };
  const industryMapPayload = {
    mode: "rr_industry_map",
    rows: [
      {
        sector_id: 1,
        phase: "Primary",
        cells: [
          {
            compartment_id: 1,
            group_id: 2,
            subject: "Language",
            anchor_band: { r: [0, 63], g: [0, 63], b: [192, 255] },
            rr_node_count: 1,
            integrity_mismatch_count: 0,
            intensity: 1,
            phase_distribution: { Idea: 0, Seed: 0, Project: 1, Archived: 0 },
            drilldown: {
              sector: "Primary (Create Phase)",
              subject: "Language",
              industries: [{ industry: "Software", subindustries: ["Enterprise Operating System Architecture"] }],
            },
            nodes: dashboardPayload.lanes[0].cards,
          },
        ],
      },
    ],
  };
  const vaGuidancePayload = {
    mode: "va_semantic_color_guidance",
    signals: {
      dominant_compartments: [{ compartment_id: 1, subject: "Language", node_count: 1 }],
      sector_distribution: { Primary: 1 },
      integrity_mismatch_hotspots: [],
    },
    recommendations: [],
  };
  const operatingStackPayload = {
    version: "phase-31",
    tracks: {
      operational_architecture: { workflow_schema: { macro: ["workflow_id"], micro: ["step_id"], provenance: ["business_id"] } },
      publishing_layer: {
        investor_ebook: { sections: ["Narrative"], color_rule: "subject colors reinforce semantic map" },
        product_usage_ebook: { sections: ["Onboarding"], color_rule: "all diagrams inherit display_rgb" },
        sop_to_ebook_pipeline: { chain: ["SOPs", "Workflows", "Usage Logs", "Insights", "Chapter Assembly"], required_inputs: ["sop_definitions"] },
      },
    },
  };
  const middleLayerPayload = {
    rr_color_context: {
      lane_count: 16,
      status_bands: { Idea: 0, Seed: 0, Project: 1, Archived: 0 },
      integrity_strip: { ok: 1, mismatch: 0, unavailable: 0 },
      dominant_lanes: [
        {
          compartment_id: 1,
          subject: "Language",
          phase: "Primary",
          node_count: 1,
          integrity: { ok: 1, mismatch: 0, unavailable: 0 },
          display_anchor_band: { r: [0, 63], g: [0, 63], b: [192, 255] },
        },
      ],
    },
  };

  const nodeDetailPayload = {
    mode: "rr_node_detail",
    node: {
      business_id: 1,
      seed_id: 1,
      title: "Phase40 Validation Node",
      subject: "Language",
      phase: "Project",
      industry_path: ["Primary (Create Phase)", "Language", "Software", "Enterprise Operating System Architecture"],
      display_rgb: { r: 0, g: 0, b: 192 },
      integrity_state: "ok",
      card_color_spec: { compartment_tag: { compartment_id: 1 }, integrity_indicator: { ok: "#16a34a", mismatch: "#f97316", unavailable: "#64748b" } },
      provenance: { workflow_refs: [{ workflow_id: "wf-1" }], sop_refs: [{ sop_id: "rr-sop-1" }] },
    },
    integrity_history: [{ event: "integrity_checked", detail: "Integrity state is ok", timestamp: new Date().toISOString() }],
    provenance_chain: [],
    multi_hop_provenance: { depth: 5, chain: [] },
    semantic_breadcrumbs: ["engine-truth", "Language", "Primary"],
    semantic_actions: [],
    publishing_ready_signals: [{ signal: "publishing_ready", status: "ready" }],
  };

  const preferencesPayload = { count: 1, results: [{ id: 1, notifications: true, dark_mode: false, view_state: {} }] };

  const actionLog: ActionLogEntry[] = [];

  await page.route("**/homepage/api/overview/**", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        welcome: "stub overview",
        flow: { status: "active", progress: 1, message: "stub" },
        tasks: [],
        settings: { notifications: true, dark_mode: false, view_state: {} },
      }),
    });
  });

  await page.route("**/homepage/api/preferences/**", async (route) => {
    const req = route.request();
    if (req.method() === "GET") {
      await route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(preferencesPayload) });
      return;
    }
    if (req.method() === "PATCH") {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ id: 1, notifications: true, dark_mode: false, view_state: JSON.parse(req.postData() || "{}") }),
      });
      return;
    }
    if (req.method() === "POST") {
      await route.fulfill({
        status: 201,
        contentType: "application/json",
        body: JSON.stringify({ id: 1, notifications: true, dark_mode: false, view_state: JSON.parse(req.postData() || "{}") }),
      });
      return;
    }
    await route.fallback();
  });

  await page.route("**/homepage/api/presentation-slides/**", async (route) => {
    await route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify({ count: 0, results: [] }) });
  });

  await page.route("**/seeds/api/rr/dashboard/**", async (route) => {
    await route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(dashboardPayload) });
  });

  await page.route("**/seeds/api/rr/industry-map/**", async (route) => {
    await route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(industryMapPayload) });
  });

  await page.route("**/seeds/api/rr/card-spec/**", async (route) => {
    await route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(cardSpecPayload) });
  });

  await page.route("**/seeds/api/rr/va-guidance/**", async (route) => {
    await route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(vaGuidancePayload) });
  });

  await page.route("**/seeds/api/rr/operating-stack/**", async (route) => {
    await route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(operatingStackPayload) });
  });

  await page.route("**/project-middle-layer/activation/**", async (route) => {
    await route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(middleLayerPayload) });
  });

  await page.route("**/seeds/api/rr/nodes/**", async (route) => {
    await route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(nodeDetailPayload) });
  });

  await page.route("**/seeds/api/rr/semantic-intelligence/**", async (route) => {
    await route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(buildSemanticIntelligence(actionLog)) });
  });

  await page.route("**/seeds/api/rr/semantic-actions/execute/", async (route) => {
    const req = route.request();
    if (req.method() === "GET") {
      const payload = buildSemanticIntelligence(actionLog);
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          mode: "semantic_action_engine",
          semantic_action_engine: payload.semantic_action_engine,
          semantic_os_health: payload.semantic_os_health,
          semantic_action_log: payload.semantic_action_log,
          semantic_feedback_loop: payload.semantic_feedback_loop,
        }),
      });
      return;
    }

    const body = JSON.parse(req.postData() || "{}");
    const action = String(body.action || "");
    const sourceSurface = String(body.surface || "semantic_os");
    const now = new Date().toISOString();
    const publishingStatus = action === "improve_publishing_readiness" ? "optimizing" : "monitor";

    const entry: ActionLogEntry = {
      recorded_at: now,
      action,
      status: "executed",
      source_surface: sourceSurface,
      business_id: Number(body.business_id || 1),
      compartment_id: Number(body.compartment_id || 1),
      subject: "Language",
      phase: "Primary",
      breadcrumbs: ["engine-truth", "semantic-actions", sourceSurface, action],
      timeline_entry: {
        event_type: "semantic_optimization_executed",
        surface: sourceSurface,
      },
      provenance_update: { depth: 8 },
      publishing_signal: { status: publishingStatus },
      workflow_step_result: { status: "n/a" },
    };

    actionLog.push(entry);
    const feedbackLoop = buildFeedbackLoop(actionLog.length, actionLog);

    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        mode: "semantic_action_execution",
        status: "executed",
        action,
        source_surface: sourceSurface,
        optimization_action: true,
        stabilization_action: false,
        timeline_entry: {
          event_type: "semantic_optimization_executed",
          surface: sourceSurface,
          action,
          business_id: Number(body.business_id || 1),
          compartment_id: Number(body.compartment_id || 1),
        },
        provenance_update: {
          action,
          depth: 8,
        },
        publishing_signal: {
          signal: "publishing_ready",
          status: publishingStatus,
        },
        workflow_step_result: {
          status: "n/a",
          message: "Workflow path optimized through deterministic improvement routing.",
        },
        optimization_loop_entry: {
          event_type: "optimization_correction",
          action,
          status: "executed",
          optimization: true,
          chain: ["engine-truth", "rr", "middle_layer", "va", "workflow", "publishing", "intelligence", "timeline", "actions", "action_log", "feedback_loop", "drift", "stabilization", "optimization"],
        },
        action_log_entry: entry,
        action_log_tail: actionLog.slice(-8),
        semantic_feedback_loop: feedbackLoop,
        semantic_os_health: buildSemanticIntelligence(actionLog).semantic_os_health,
      }),
    });
  });
}

test.describe("Semantic optimization UI flow", () => {
  test("runs workflow, publishing, and subject optimization bundles with fan-out counters", async ({ page }) => {
    await stubSemanticIspeApis(page);
    await page.goto("/ispe/");

    await expect(page.getByRole("heading", { name: "Semantic Action Bundles" })).toBeVisible();
    await expect(page.getByText("History 0")).toBeVisible();

    await page.getByRole("button", { name: "Workflow Efficiency Optimization Bundle" }).click();
    await expect(page.getByText("Executed Workflow Efficiency Optimization Bundle")).toBeVisible();
    await expect(page.getByText("History 1")).toBeVisible();

    await page.getByRole("button", { name: "Publishing Readiness Optimization Bundle" }).click();
    await expect(page.getByText("Executed Publishing Readiness Optimization Bundle")).toBeVisible();
    await expect(page.getByText("History 2")).toBeVisible();

    await page.getByRole("button", { name: "Subject Balance Optimization Bundle" }).click();
    await expect(page.getByText("Executed Subject Balance Optimization Bundle")).toBeVisible();
    await expect(page.getByText("History 3")).toBeVisible();

    await expect(page.getByText("optimize_workflow_path · executed · Language · Primary")).toBeVisible();
    await expect(page.getByText("improve_publishing_readiness · executed · Language · Primary")).toBeVisible();
    await expect(page.getByText("rebalance_subject_load · executed · Language · Primary")).toBeVisible();

    await expect(page.getByText("Executed 3")).toBeVisible();
    await expect(page.getByText("Pending optimizations 1").first()).toBeVisible();
  });
});
