import { useEffect, useMemo, useState } from "react";

import {
  activateProject,
  fetchIspeActivation,
  fetchPhase4Activation,
  fetchPhase4Orchestration,
  fetchRrOperatingStack,
  fetchRrSemanticIntelligence,
  fetchPreferences,
  saveViewState,
  promoteSeed,
} from "../api/homepageApi";
import MiddleLayerColorContextPanel from "./MiddleLayerColorContextPanel";
import PublishingLayerHooksPanel from "./PublishingLayerHooksPanel";
import RrCardSpecPanel from "./RrCardSpecPanel";
import RrDashboardPanel from "./RrDashboardPanel";
import RrDetailPanel from "./RrDetailPanel";
import RrIndustryMapPanel from "./RrIndustryMapPanel";
import SemanticActionLogPanel from "./SemanticActionLogPanel";
import SemanticIntelligencePanel from "./SemanticIntelligencePanel";
import SopWorkflowScaffoldPanel from "./SopWorkflowScaffoldPanel";
import VaSemanticGuidancePanel from "./VaSemanticGuidancePanel";
import { buildDriftReflection, buildOptimizationReflection, mergeSemanticActionHistory, normalizeSemanticFeedbackLoop } from "./semanticOsHelpers";

const PHASE_OPTIONS = [
  {
    key: "idea",
    label: "Idea",
    headline: "Project Genesis",
    description: "Capture the first intent, audience, and direction.",
    suggestedFields: ["Purpose", "Industry classification", "Audience", "Early narrative intent"],
  },
  {
    key: "seed",
    label: "Seed",
    headline: "Structure Formation",
    description: "Shape the Idea into a formal Seed with identity and constraints.",
    suggestedFields: ["Seed name", "BTIF identity", "Structure", "Release cadence"],
  },
  {
    key: "project",
    label: "Project",
    headline: "Delivery Workspace",
    description: "Unlock PIP, Polish, Task Manager, and VA orchestration.",
    suggestedFields: ["Project scope", "PIP access", "Polish scope", "Task manager scope"],
  },
];

const DEFAULT_FORM = {
  purpose: "Basetrue Newsletter",
  industry: "Media / Publishing",
  audience: "Readers, contributors, and newsletter operators",
  narrative:
    "A deterministic editorial project that can move from Idea into Seed with annual planning, identity, and guided orchestration.",
  notes: "Annual plan demo flow for ISPE + orchestration.",
  identityName: "Basetrue Newsletter",
  identityType: "Editorial Identity",
  identityPurpose: "Create a guided editorial identity for the annual newsletter plan.",
  identityStructure: "Sections, themes, recurring elements, and core narrative pillars.",
  deliverables: "Monthly newsletter issues, annual summary, editorial calendar",
  annualPlan: "Editorial calendar, theme tracking, issue rhythm, annual review checkpoints",
  quarterlyObjectives: "Q1 launch, Q2 consistency, Q3 refinement, Q4 annual recap",
  deliverableStructure: "Lead story, recurring sections, audience signals, annual planning checkpoints",
  deliverableCadence: "Monthly",
  taskArchetypes: "Linear, 2xLinear, 12-Point, Perpetual",
  governanceTiers: "PIP, Polish, Task Manager",
};

const SEMANTIC_PANELS = [
  { id: "rr_intelligence", label: "Intelligence", panelId: "rr-intelligence-panel" },
  { id: "rr_dashboard", label: "RR Dashboard", panelId: "rr-dashboard-panel" },
  { id: "rr_card_spec", label: "RR Card Spec", panelId: "rr-card-spec-panel" },
  { id: "rr_industry_map", label: "RR Map", panelId: "rr-industry-map-panel" },
  { id: "rr_detail", label: "RR Detail", panelId: "rr-detail-panel" },
  { id: "middle_layer", label: "Middle Layer", panelId: "middle-layer-panel" },
  { id: "rr_va", label: "VA Guidance", panelId: "va-guidance-panel" },
  { id: "rr_workflows", label: "Workflows", panelId: "sop-workflow-panel" },
  { id: "rr_publishing", label: "Publishing", panelId: "publishing-layer-panel" },
  { id: "semantic_action_log", label: "Action Log", panelId: "semantic-action-log-panel" },
];

function renderReadableList(items = []) {
  return Array.isArray(items) ? items.filter(Boolean) : [];
}

function statusLabel(go) {
  return go ? "GO" : "NO-GO";
}

export default function IspeIdeaScreen() {
  const [phase, setPhase] = useState("idea");
  const [vaEnabled, setVaEnabled] = useState(true);
  const [activation, setActivation] = useState(null);
  const [orchestration, setOrchestration] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [draftSaved, setDraftSaved] = useState(false);
  const [submissionMessage, setSubmissionMessage] = useState("");
  const [promotingSeed, setPromotingSeed] = useState(false);
  const [currentSeedId, setCurrentSeedId] = useState(null);
  const [activatingProject, setActivatingProject] = useState(false);
  const [rrDashboardPayload, setRrDashboardPayload] = useState(null);
  const [operatingStackPayload, setOperatingStackPayload] = useState(null);
  const [semanticIntelligencePayload, setSemanticIntelligencePayload] = useState(null);
  const [semanticIntelligenceLoading, setSemanticIntelligenceLoading] = useState(true);
  const [semanticActionHistory, setSemanticActionHistory] = useState([]);
  const [semanticActionFeedback, setSemanticActionFeedback] = useState({});
  const [activeSemanticPanel, setActiveSemanticPanel] = useState("rr_dashboard");
  const [semanticViewHydrated, setSemanticViewHydrated] = useState(false);
  const [form, setForm] = useState(DEFAULT_FORM);

  const selectedPhase = useMemo(() => PHASE_OPTIONS.find((item) => item.key === phase) || PHASE_OPTIONS[0], [phase]);
  const requestContext = activation?.request_context || {};
  const activationReady = Boolean(activation?.ispe_ready);
  const decisionGo = Boolean(orchestration?.decision?.go);
  const recommendedActions = renderReadableList(orchestration?.recommended_next_actions);
  const blockers = renderReadableList(orchestration?.blocking_capabilities);
  const softBlockers = renderReadableList(orchestration?.soft_blocking_capabilities);
  const activationSequence = renderReadableList(orchestration?.activation_sequence);
  const vaHints = orchestration?.orchestration_hints?.va || {};
  const uiHints = orchestration?.orchestration_hints?.ui || {};
  const phaseGuidance = activation?.phase_guidance || {};
  const semanticReadiness = activation?.activation_contract?.semantic_readiness || {};
  const semanticCatalogs = semanticReadiness.semantic_catalogs || {};
  const referenceTruth = semanticReadiness.reference_truth || {};
  const classificationTruth = semanticReadiness.classification_truth || {};
  const semanticHostHealth = semanticIntelligencePayload?.semantic_os_health || {};
  const semanticHostDrift = buildDriftReflection(semanticActionFeedback);
  const semanticHostOptimization = buildOptimizationReflection(semanticActionFeedback);
  const semanticHostReady = Boolean(semanticHostHealth.ready) && !semanticIntelligenceLoading && Boolean(operatingStackPayload);
  const isSeedPhase = phase === "seed";
  const isProjectPhase = phase === "project";
  const isIdeaPhase = phase === "idea";

  const fetchWorkspaceState = (phaseName, includeVa) =>
    Promise.all([
      fetchIspeActivation({ mode: "assistive", include_va: includeVa ? 1 : 0, phase: phaseName }),
      fetchPhase4Activation({ mode: "assistive", include_va: includeVa ? 1 : 0 }),
      fetchPhase4Orchestration({ mode: "assistive", include_va: includeVa ? 1 : 0 }),
    ]);

  const applyWorkspaceState = ([ispePayload, activationPayload, orchestrationPayload]) => {
    setActivation({
      ...ispePayload,
      activation_contract: activationPayload,
    });
    setOrchestration(orchestrationPayload);
    setDraftSaved(false);
  };

  const reloadWorkspace = async (phaseName, includeVa = vaEnabled) => {
    const payloads = await fetchWorkspaceState(phaseName, includeVa);
    applyWorkspaceState(payloads);
  };

  useEffect(() => {
    let active = true;
    setLoading(true);
    setError("");

    fetchWorkspaceState(phase, vaEnabled)
      .then((payloads) => {
        if (!active) {
          return;
        }
        applyWorkspaceState(payloads);
      })
      .catch((fetchError) => {
        if (!active) {
          return;
        }
        setError(fetchError instanceof Error ? fetchError.message : "Unable to load ISPE activation state");
      })
      .finally(() => {
        if (active) {
          setLoading(false);
        }
      });

    return () => {
      active = false;
    };
  }, [phase]);

  useEffect(() => {
    if (!activation || !activation.request_context) {
      return;
    }
    const apiIncludeVa = Boolean(activation.request_context.include_va);
    if (apiIncludeVa !== vaEnabled) {
      setVaEnabled(apiIncludeVa);
    }
  }, [activation, vaEnabled]);

  useEffect(() => {
    let active = true;
    fetchRrOperatingStack()
      .then((payload) => {
        if (!active) {
          return;
        }
        setOperatingStackPayload(payload);
      })
      .catch(() => {
        if (!active) {
          return;
        }
        setOperatingStackPayload(null);
      });
    return () => {
      active = false;
    };
  }, []);

  useEffect(() => {
    let active = true;
    setSemanticIntelligenceLoading(true);

    fetchRrSemanticIntelligence()
      .then((payload) => {
        if (!active) {
          return;
        }
        setSemanticIntelligencePayload(payload);
        const seededHistory = mergeSemanticActionHistory([], payload?.semantic_action_log?.entries || []);
        setSemanticActionHistory(seededHistory);
        setSemanticActionFeedback(
          normalizeSemanticFeedbackLoop(
            payload?.semantic_feedback_loop || {},
            {
              actionLog: seededHistory,
              semanticHealth: payload?.semantic_os_health || {},
            },
          ),
        );
      })
      .catch(() => {
        if (!active) {
          return;
        }
        setSemanticIntelligencePayload(null);
      })
      .finally(() => {
        if (active) {
          setSemanticIntelligenceLoading(false);
        }
      });

    return () => {
      active = false;
    };
  }, []);

  useEffect(() => {
    const handleSemanticActionResult = (event) => {
      const detail = event?.detail || {};
      const incomingEntries = Array.isArray(detail?.action_log_tail)
        ? detail.action_log_tail
        : detail?.action_log_entry
          ? [detail.action_log_entry]
          : [detail];

      setSemanticActionHistory((previous) => {
        const merged = mergeSemanticActionHistory(previous, incomingEntries);
        setSemanticActionFeedback((existing) => normalizeSemanticFeedbackLoop(
          detail?.semantic_feedback_loop || existing,
          {
            actionLog: merged,
            semanticHealth: detail?.semantic_os_health || semanticIntelligencePayload?.semantic_os_health || {},
          },
        ));
        return merged;
      });

      setSemanticIntelligencePayload((previous) => {
        if (!previous) {
          return previous;
        }
        const mergedEntries = mergeSemanticActionHistory(previous?.semantic_action_log?.entries || [], incomingEntries);
        return {
          ...previous,
          semantic_feedback_loop: detail?.semantic_feedback_loop || previous.semantic_feedback_loop,
          semantic_os_health: detail?.semantic_os_health || previous.semantic_os_health,
          semantic_action_log: {
            ...(previous.semantic_action_log || {}),
            entries: mergedEntries,
          },
        };
      });
    };

    window.addEventListener("grassroots:semantic-action-result", handleSemanticActionResult);
    return () => {
      window.removeEventListener("grassroots:semantic-action-result", handleSemanticActionResult);
    };
  }, [semanticIntelligencePayload]);

  useEffect(() => {
    const persistedRaw = window.localStorage.getItem("grassroots.semantic-stack.view-state.v1");
    if (persistedRaw) {
      try {
        const persisted = JSON.parse(persistedRaw);
        const nextPanel = persisted?.semantic_stack?.active_panel;
        if (typeof nextPanel === "string" && nextPanel) {
          setActiveSemanticPanel(nextPanel);
        }
      } catch (_error) {
        // Ignore malformed local view state.
      }
    }

    fetchPreferences()
      .then((payload) => {
        const preference = Array.isArray(payload?.results) ? payload.results[0] : null;
        const nextPanel = preference?.view_state?.semantic_stack?.active_panel;
        if (typeof nextPanel === "string" && nextPanel) {
          setActiveSemanticPanel(nextPanel);
        }
      })
      .catch(() => {
        // Server sync is additive; localStorage remains available.
      })
      .finally(() => {
        setSemanticViewHydrated(true);
      });
  }, []);

  useEffect(() => {
    if (!semanticViewHydrated) {
      return;
    }
    const nextState = {
      semantic_stack: {
        active_panel: activeSemanticPanel,
      },
    };
    window.localStorage.setItem("grassroots.semantic-stack.view-state.v1", JSON.stringify(nextState));
    saveViewState(nextState).catch(() => {
      // Local state remains available if server sync fails.
    });
  }, [activeSemanticPanel, semanticViewHydrated]);

  useEffect(() => {
    const handlePanelSelect = (event) => {
      const panelId = String(event?.detail?.panelId || "");
      if (panelId) {
        setActiveSemanticPanel(panelId);
      }
    };

    window.addEventListener("grassroots:semantic-panel-select", handlePanelSelect);
    return () => {
      window.removeEventListener("grassroots:semantic-panel-select", handlePanelSelect);
    };
  }, []);

  useEffect(() => {
    const target = SEMANTIC_PANELS.find((item) => item.id === activeSemanticPanel);
    if (!target) {
      return;
    }
    const element = document.getElementById(target.panelId);
    if (element) {
      element.scrollIntoView({ behavior: "smooth", block: "start" });
    }
  }, [activeSemanticPanel]);

  const handleToggleVa = async () => {
    if (!isProjectPhase) {
      setSubmissionMessage("VA mode is locked during Idea and Seed phases. Activate Project to toggle VA.");
      return;
    }

    const nextVaEnabled = !vaEnabled;
    setVaEnabled(nextVaEnabled);
    setLoading(true);
    setError("");
    try {
      await reloadWorkspace(phase, nextVaEnabled);
      setSubmissionMessage(`VA ${nextVaEnabled ? "enabled" : "disabled"} for ISPE orchestration.`);
    } catch (toggleError) {
      setError(toggleError instanceof Error ? toggleError.message : "Unable to toggle VA mode");
    } finally {
      setLoading(false);
    }
  };

  const updateField = (field) => (event) => {
    setForm((previous) => ({
      ...previous,
      [field]: event.target.value,
    }));
    setSubmissionMessage("");
  };

  const handleSaveDraft = () => {
    try {
      window.localStorage.setItem("ispe_idea_draft_v1", JSON.stringify({ phase, form }));
      setDraftSaved(true);
      setSubmissionMessage("Draft saved locally. Re-open this screen to continue the Idea.");
    } catch (_error) {
      setSubmissionMessage("Draft could not be stored locally in this browser.");
    }
  };

  const handleCreateIdea = () => {
    if (!decisionGo) {
      setSubmissionMessage("Resolve the orchestration blockers before creating the Idea.");
      return;
    }
    setPhase("seed");
    setSubmissionMessage("Idea created successfully. Transitioning into Seed formation.");
  };

  const handlePromoteToSeed = async () => {
    if (!decisionGo) {
      setSubmissionMessage("Resolve the orchestration blockers before promoting the Seed.");
      return;
    }

    setPromotingSeed(true);
    setSubmissionMessage("Promoting Seed through backend orchestration...");

    try {
      const result = await promoteSeed({
        purpose: form.purpose,
        industry: form.industry,
        audience: form.audience,
        narrative: form.narrative,
        notes: form.notes,
        identity_name: form.identityName,
        identity_type: form.identityType,
        identity_purpose: form.identityPurpose,
        identity_structure: form.identityStructure,
        deliverables: form.deliverables,
        deliverable_structure: form.deliverableStructure,
        deliverable_cadence: form.deliverableCadence,
        metadata: {
          phase,
          requested_by: "ispe",
        },
      });

      setCurrentSeedId(result?.seed?.id || null);
      setPhase(result?.next_phase || "project");
      setSubmissionMessage(`Seed #${result?.seed?.id || "created"} promoted. Transitioning into Project formation.`);
    } catch (promotionError) {
      setSubmissionMessage(promotionError instanceof Error ? promotionError.message : "Unable to promote Seed.");
    } finally {
      setPromotingSeed(false);
    }
  };

  const handleActivateProject = async () => {
    if (!decisionGo) {
      setSubmissionMessage("Resolve the orchestration blockers before activating the Project.");
      return;
    }

    if (!currentSeedId) {
      setSubmissionMessage("Promote the Seed first so the Project activation endpoint has a Seed id.");
      return;
    }

    setActivatingProject(true);
    setSubmissionMessage("Activating Project through backend orchestration...");

    try {
      const result = await activateProject({
        seed_id: currentSeedId,
        project_name: form.identityName,
        market_status: "live",
        project_notes: {
          btif_narrative: {
            identity_name: form.identityName,
            identity_purpose: form.identityPurpose,
            narrative_pillars: form.identityStructure,
            editorial_voice: form.identityType,
            audience_narrative: form.audience,
            core_themes: form.annualPlan,
          },
          pip: {
            annual_plan: form.annualPlan,
            quarterly_objectives: form.quarterlyObjectives,
            monthly_deliverables: form.deliverables,
            task_archetypes: form.taskArchetypes.split(",").map((item) => item.trim()).filter(Boolean),
            governance_tiers: form.governanceTiers.split(",").map((item) => item.trim()).filter(Boolean),
          },
          polish: {
            refinement_notes: form.notes,
            editorial_adjustments: form.deliverableStructure,
            narrative_improvements: form.narrative,
            identity_strengthening: form.identityPurpose,
            semantic_drift_corrections: form.identityStructure,
          },
          task_manager: {
            task_list: form.deliverables.split(",").map((item) => item.trim()).filter(Boolean),
            assignments: ["Editorial planning", "Narrative review", "Deliverable routing"],
            deadlines: ["Monthly", "Quarterly", "Annual"],
            status_tracking: ["Draft", "Review", "Live"],
            deliverable_routing: ["PIP", "Polish", "Task Manager"],
          },
          semantic_alignment: {
            reference_truth,
            classification_truth,
            semantic_catalogs,
            quadrant_ready: Boolean(activation?.activation_contract?.quadrant_readiness?.deterministic_ready),
            middle_layer_ready: Boolean(activation?.activation_contract?.project_middle_layer_readiness?.deterministic_ready),
          },
          va_guidance: {
            narrative: "This Project appears ready for full editorial governance.",
            annual_outcome: "A governed newsletter system with annual, quarterly, and monthly structure.",
          },
        },
        metadata: {
          phase,
          requested_by: "ispe",
        },
      });

      await reloadWorkspace("project");
      setSubmissionMessage(
        `Project activated successfully. ${result?.business?.brand_name || form.identityName} is now governed and ready for annual operations.`,
      );
    } catch (activationError) {
      setSubmissionMessage(activationError instanceof Error ? activationError.message : "Unable to activate Project.");
    } finally {
      setActivatingProject(false);
    }
  };

  return (
    <main className="homepage-wrap ispe-route">
      <section className="panel ispe-hero-panel">
        <div>
          <p className="eyebrow">ISPE</p>
          <h1>{selectedPhase.headline}</h1>
          <p className="status-line">
            {selectedPhase.description}
          </p>
        </div>
        <div className="ispe-status-row">
          <span className={`ispe-chip ${activationReady ? "ispe-chip-ready" : "ispe-chip-warm"}`}>
            Platform spine {activationReady ? "ready" : "warming"}
          </span>
          <span className={`ispe-chip ${decisionGo ? "ispe-chip-go" : "ispe-chip-blocked"}`}>
            Decision {statusLabel(decisionGo)}
          </span>
          <span className={`ispe-chip ${semanticHostReady ? "ispe-chip-ready" : "ispe-chip-warm"}`}>
            Semantic OS {semanticHostReady ? "ready" : "hydrating"}
          </span>
          <span className="ispe-chip">Mode {requestContext.mode || "assistive"}</span>
          <span className="ispe-chip">VA {requestContext.include_va ? "on" : "off"}</span>
          <span className="ispe-chip">Phase {selectedPhase.label}</span>
          <button
            type="button"
            className="action-btn"
            onClick={handleToggleVa}
            aria-pressed={vaEnabled}
            disabled={!isProjectPhase}
            title={isProjectPhase ? "Toggle VA mode" : "VA toggles unlock at Project phase"}
          >
            Turn VA {vaEnabled ? "Off" : "On"}
          </button>
        </div>
      </section>

      {error ? (
        <section className="panel ispe-alert-panel">
          <p className="eyebrow">Loading error</p>
          <h2>ISPE could not load its heartbeat</h2>
          <p className="status-line">{error}</p>
        </section>
      ) : null}

      <section className="ispe-layout">
        <div className="ispe-stack">
          <section className="panel ispe-decision-panel">
            <p className="eyebrow">Orchestration Summary</p>
            <h2>{decisionGo ? "Decision: GO" : "Decision: NO-GO"}</h2>
            <p className="status-line">
              {decisionGo
                ? isIdeaPhase
                  ? "Your platform is ready for Idea creation."
                  : isSeedPhase
                    ? "Your Idea can be promoted into a Seed."
                    : "Your Seed is ready to unlock Project operations."
                : "Critical blockers must be cleared before this phase can proceed."}
            </p>
            <div className="ispe-summary-grid">
              <div>
                <strong>Blocking capabilities</strong>
                <ul>
                  {blockers.length > 0 ? blockers.map((item) => <li key={item.capability}>{item.capability}</li>) : <li>None</li>}
                </ul>
              </div>
              <div>
                <strong>Soft blockers</strong>
                <ul>
                  {softBlockers.length > 0 ? softBlockers.map((item) => <li key={item.capability}>{item.capability}</li>) : <li>None</li>}
                </ul>
              </div>
              <div>
                <strong>Next actions</strong>
                <ul>
                  {recommendedActions.length > 0 ? recommendedActions.map((item) => <li key={item}>{item}</li>) : <li>No inferred actions</li>}
                </ul>
              </div>
            </div>
            <p className="ispe-phase-summary">
              {isIdeaPhase
                ? "Suggested next steps: define purpose, select industry, add early narrative intent, and capture audience context."
                : isSeedPhase
                  ? "Suggested next steps: define BTIF identity, establish structural outline, add semantic classification, and frame early deliverables."
                  : "Suggested next steps: activate PIP, define deliverables, and begin Project formation."}
            </p>
          </section>

          <section className="panel ispe-form-panel">
            <div className="ispe-section-heading">
              <div>
                <p className="eyebrow">{isIdeaPhase ? "Idea Creation" : isSeedPhase ? "Seed Formation" : "Project Formation"}</p>
                <h2>
                  {isIdeaPhase
                    ? "Basetrue Newsletter - Annual Plan"
                    : isSeedPhase
                      ? "BTIF Identity Builder"
                      : "Project Delivery Setup"}
                </h2>
              </div>
              <div className="ispe-phase-switcher" role="tablist" aria-label="ISPE phase switcher">
                {PHASE_OPTIONS.map((item) => (
                  <button
                    key={item.key}
                    type="button"
                    className={`story-engine-tab ${phase === item.key ? "is-active" : ""}`}
                    onClick={() => setPhase(item.key)}
                    aria-pressed={phase === item.key}
                  >
                    {item.label}
                  </button>
                ))}
              </div>
            </div>

            {isIdeaPhase ? (
              <div className="ispe-form-grid">
                <label>
                  Purpose
                  <input
                    type="text"
                    value={form.purpose}
                    onChange={updateField("purpose")}
                    placeholder="Describe what this project aims to achieve"
                  />
                  <span className="ispe-field-hint">{phaseGuidance.subheadline || "Describe the project purpose in one sentence."}</span>
                </label>
                <label>
                  Industry Classification
                  <input
                    type="text"
                    value={form.industry}
                    onChange={updateField("industry")}
                    placeholder="Select industry, GICS, NAICS, or semantic category"
                  />
                  <span className="ispe-field-hint">
                    Use canonical reference truth for classification, then let the semantic preview resolve the category.
                  </span>
                </label>
                <label>
                  Audience
                  <input
                    type="text"
                    value={form.audience}
                    onChange={updateField("audience")}
                    placeholder="Who is this project for?"
                  />
                  <span className="ispe-field-hint">VA hint: define the audience before expanding the structure.</span>
                </label>
                <label className="ispe-textarea-field">
                  Early Narrative Intent
                  <textarea
                    value={form.narrative}
                    onChange={updateField("narrative")}
                    placeholder="Write 2-3 sentences describing the direction of the project"
                  />
                  <span className="ispe-field-hint">
                    {vaHints.semantic_bridge_ready
                      ? "This Idea can be translated into Seed identity and structure after creation."
                      : "Narrative intent helps the orchestration brain shape the first Seed."}
                  </span>
                </label>
                <label className="ispe-textarea-field">
                  Optional Notes / Attachments
                  <textarea value={form.notes} onChange={updateField("notes")} placeholder="Capture extra context, links, or reference notes" />
                </label>
              </div>
            ) : null}

            {isSeedPhase ? (
              <div className="ispe-form-grid ispe-form-grid--seed">
                <label>
                  Identity Name
                  <input type="text" value={form.identityName} onChange={updateField("identityName")} placeholder="Name the identity of this Seed" />
                  <span className="ispe-field-hint">VA hint: Name the identity of this Seed (e.g., Basetrue Newsletter).</span>
                </label>
                <label>
                  Identity Type
                  <input type="text" value={form.identityType} onChange={updateField("identityType")} placeholder="Editorial Identity, Narrative Identity, Product Identity" />
                  <span className="ispe-field-hint">BTIF identity types guide how the Seed will be structured.</span>
                </label>
                <label className="ispe-textarea-field">
                  Identity Purpose
                  <textarea value={form.identityPurpose} onChange={updateField("identityPurpose")} placeholder="Describe the purpose of this identity in one sentence" />
                </label>
                <label className="ispe-textarea-field">
                  Identity Structure
                  <textarea value={form.identityStructure} onChange={updateField("identityStructure")} placeholder="Sections, themes, recurring elements, and core narrative pillars" />
                </label>
              </div>
            ) : null}

            {isProjectPhase ? (
              <div className="ispe-form-grid ispe-form-grid--seed">
                <label>
                  Annual Plan
                  <input type="text" value={form.annualPlan} onChange={updateField("annualPlan")} placeholder="Annual planning and governance" />
                </label>
                <label>
                  Quarterly Objectives
                  <input type="text" value={form.quarterlyObjectives} onChange={updateField("quarterlyObjectives")} placeholder="Q1, Q2, Q3, Q4 goals" />
                </label>
                <label>
                  Deliverable List
                  <input type="text" value={form.deliverables} onChange={updateField("deliverables")} placeholder="Monthly newsletter issues, annual summary, editorial calendar" />
                </label>
                <label>
                  Deliverable Cadence
                  <input type="text" value={form.deliverableCadence} onChange={updateField("deliverableCadence")} placeholder="Monthly, quarterly, annual" />
                  <span className="ispe-field-hint">Define how this Seed becomes a Project-producing system.</span>
                </label>
                <label>
                  Task Archetypes
                  <input type="text" value={form.taskArchetypes} onChange={updateField("taskArchetypes")} placeholder="Linear, 2xLinear, 12-Point, Perpetual" />
                </label>
                <label>
                  Governance Tiers
                  <input type="text" value={form.governanceTiers} onChange={updateField("governanceTiers")} placeholder="PIP, Polish, Task Manager" />
                </label>
                <label className="ispe-textarea-field">
                  Deliverable Structure
                  <textarea value={form.deliverableStructure} onChange={updateField("deliverableStructure")} placeholder="Lead story, recurring sections, audience signals, planning checkpoints" />
                </label>
                <label className="ispe-textarea-field">
                  Project Notes
                  <textarea value={form.notes} onChange={updateField("notes")} placeholder="Capture project-level context, links, and constraints" />
                </label>
              </div>
            ) : null}

            <div className="ispe-action-bar">
              {isIdeaPhase ? (
                <button type="button" className="action-btn" onClick={handleCreateIdea} disabled={!decisionGo}>
                  Create Idea
                </button>
              ) : null}
              {isSeedPhase ? (
                <button type="button" className="action-btn" onClick={handlePromoteToSeed} disabled={!decisionGo || promotingSeed}>
                  Promote to Seed
                </button>
              ) : null}
              {isProjectPhase ? (
                <button type="button" className="action-btn" onClick={handleActivateProject} disabled={!decisionGo || activatingProject}>
                  Activate Project
                </button>
              ) : null}
              <button type="button" className="action-btn" onClick={handleSaveDraft}>
                Save {selectedPhase.label} Draft
              </button>
              <span className="status-line ispe-action-status">
                {submissionMessage || (draftSaved ? `${selectedPhase.label} draft saved locally.` : `Ready for orchestration-driven ${selectedPhase.label} work.`)}
              </span>
            </div>
          </section>
        </div>

        <aside className="ispe-side-stack">
          <section className="panel ispe-preview-panel">
            <p className="eyebrow">Semantic Preview</p>
            <h2>Canonical context</h2>
            <ul className="ispe-bullet-list">
              <li>Reference truth: GICS {referenceTruth.gics_total || 0} / NAICS {referenceTruth.naics_total || 0}</li>
              <li>Classification truth: {classificationTruth.approved_total || 0} approved records</li>
              <li>Phase catalog entries: {Object.keys(semanticCatalogs.phase || {}).length || 0}</li>
              <li>Bundle families: {Object.keys(semanticCatalogs.bundle_family || {}).length || 0}</li>
              <li>UI category resolution: {Object.keys(semanticCatalogs.ui_category_resolved || {}).length || 0}</li>
            </ul>
          </section>

          {isIdeaPhase ? (
            <section className="panel ispe-preview-panel">
              <p className="eyebrow">Fields to show next</p>
              <h2>{selectedPhase.label}</h2>
              <ul className="ispe-bullet-list">
                {selectedPhase.suggestedFields.map((field) => (
                  <li key={field}>{field}</li>
                ))}
              </ul>
              <div className="ispe-mini-grid">
                <div>
                  <strong>VA mode</strong>
                  <p>{vaHints.mode || "standby"}</p>
                </div>
                <div>
                  <strong>UI mode</strong>
                  <p>{uiHints.mode || "guided_activation"}</p>
                </div>
              </div>
            </section>
          ) : null}

          {isSeedPhase ? (
            <section className="panel ispe-preview-panel">
              <p className="eyebrow">Semantic Alignment</p>
              <h2>Canonical semantic context</h2>
              <ul className="ispe-bullet-list">
                <li>Industry: {form.industry}</li>
                <li>Sector: {referenceTruth.gics_total > 0 ? "Canonical sector available" : "Waiting for canonical sector truth"}</li>
                <li>Semantic Bundle Family: {Object.keys(semanticCatalogs.bundle_family || {}).join(", ") || "foundation"}</li>
                <li>UI Category: {Object.keys(semanticCatalogs.ui_category_resolved || {}).join(", ") || "Editorial"}</li>
                <li>MLAS Classification: {classificationTruth.approved_total || 0} approved records</li>
              </ul>
            </section>
          ) : null}

          {(isSeedPhase || isProjectPhase) ? (
            <section className="panel ispe-preview-panel">
              <p className="eyebrow">Early Deliverables</p>
              <h2>{isSeedPhase ? "Seed deliverable frame" : "Project deliverable frame"}</h2>
              <ul className="ispe-bullet-list">
                <li>{form.deliverables}</li>
                <li>{form.deliverableStructure}</li>
                <li>{form.deliverableCadence}</li>
              </ul>
              <p className="ispe-field-hint">
                {isSeedPhase
                  ? "Define the first version of what this Seed will produce once promoted to Project."
                  : "These deliverables become the first operating shape of the Project."}
              </p>
            </section>
          ) : null}

          <section className="panel ispe-preview-panel">
            <p className="eyebrow">Transition Preview</p>
            <h2>Idea to Seed</h2>
            <p className="status-line">
              {phaseGuidance.headline || "When the Idea is created, orchestration will recommend the next Seed transition."}
            </p>
            <p className="ispe-quote">
              {phaseGuidance.subheadline ||
                "When promoted to Seed, the orchestration brain will help define identity, structure, and the first-year plan."}
            </p>
          </section>

          {requestContext.include_va ? (
            <section className="panel ispe-va-panel">
              <p className="eyebrow">VA Assistive Panel</p>
              <h2>Voice of the orchestration layer</h2>
              <p className="ispe-quote">
                {isSeedPhase
                  ? "This Seed appears to be forming a structured editorial identity. When promoted to Project, I’ll help you activate PIP, Polish, and Task Manager."
                  : "This Idea looks like the beginning of a structured editorial project. When promoted to Seed, the VA can help define identity, structure, and the first-year plan."}
              </p>
              <ul className="ispe-bullet-list">
                <li>Identity suggestions</li>
                <li>Structural guidance</li>
                <li>Deliverable framing</li>
                <li>{isSeedPhase ? "Project transition preview" : "Seed transition preview"}</li>
              </ul>
            </section>
          ) : null}
        </aside>
      </section>

      <section className="panel ispe-footer-panel">
        <p className="eyebrow">Post-create transition</p>
        <p className="status-line">
          After promotion, ISPE will re-run /platform/orchestration/?mode=assistive&amp;include_va={vaEnabled ? 1 : 0} and guide the user into the next phase.
        </p>
        <div className="ispe-summary-grid ispe-summary-grid--compact">
          {activationSequence.map((step) => (
            <div key={`${step.step}-${step.surface}`} className="ispe-step-pill">
              <strong>Step {step.step}</strong>
              <span>{step.surface}</span>
              <span>{step.status}</span>
            </div>
          ))}
        </div>
      </section>

      <section className="semantic-stack-layout">
        <div className="semantic-stack-nav panel">
          {SEMANTIC_PANELS.map((item) => (
            <button
              key={item.id}
              type="button"
              className={activeSemanticPanel === item.id ? "is-active" : ""}
              onClick={() => {
                setActiveSemanticPanel(item.id);
                window.dispatchEvent(new CustomEvent("grassroots:semantic-panel-select", { detail: { panelId: item.id } }));
              }}
            >
              {item.label}
            </button>
          ))}
        </div>
        <section className="panel semantic-intelligence-panel">
          <h3>Semantic Host Health</h3>
          <p className="status-line">
            {semanticHostReady
              ? "Payload propagation is stable across RR, middle layer, VA, workflows, publishing, and timeline surfaces."
              : "One or more semantic surfaces are still hydrating; the host will keep the shared payload fan-out deterministic."}
          </p>
          <div className="rr-node-chip-row">
            {(semanticHostHealth.checks || []).map((item) => (
              <span key={`${item.surface}-${item.status}`}>{item.surface}: {item.status}</span>
            ))}
          </div>
          <div className="rr-node-chip-row">
            <span>Drift severity {semanticHostDrift.severity}</span>
            <span>Drift score {semanticHostDrift.score}</span>
            <span>Stabilization {semanticHostDrift.stabilization?.status || "monitor"}</span>
            <span>Pending corrections {semanticHostDrift.stabilization?.progress?.pending_corrections || 0}</span>
          </div>
          <div className="rr-node-chip-row">
            <span>Optimization {semanticHostOptimization.status}</span>
            <span>Subject mix {semanticHostOptimization.subjectMixScore}</span>
            <span>Workflow efficiency {semanticHostOptimization.workflowEfficiencyScore}</span>
            <span>Publishing readiness {semanticHostOptimization.publishingReadinessScore}</span>
            <span>Pending optimizations {semanticHostOptimization.progress.pendingOptimizations}</span>
          </div>
        </section>
        <SemanticIntelligencePanel
          panelId="rr-intelligence-panel"
          semanticIntelligence={semanticIntelligencePayload}
          semanticIntelligenceLoading={semanticIntelligenceLoading}
          semanticActionHistory={semanticActionHistory}
          semanticActionFeedback={semanticActionFeedback}
        />
        <RrDashboardPanel panelId="rr-dashboard-panel" onDataChange={setRrDashboardPayload} />
        <RrCardSpecPanel panelId="rr-card-spec-panel" />
        <RrIndustryMapPanel panelId="rr-industry-map-panel" />
        <RrDetailPanel panelId="rr-detail-panel" semanticIntelligence={semanticIntelligencePayload} semanticActionHistory={semanticActionHistory} semanticActionFeedback={semanticActionFeedback} />
        <MiddleLayerColorContextPanel panelId="middle-layer-panel" semanticIntelligence={semanticIntelligencePayload} semanticActionHistory={semanticActionHistory} />
        <VaSemanticGuidancePanel panelId="va-guidance-panel" semanticIntelligence={semanticIntelligencePayload} semanticActionHistory={semanticActionHistory} semanticActionFeedback={semanticActionFeedback} />
        <SopWorkflowScaffoldPanel
          panelId="sop-workflow-panel"
          rrDashboard={rrDashboardPayload}
          operatingStack={operatingStackPayload}
          semanticIntelligence={semanticIntelligencePayload}
          semanticActionHistory={semanticActionHistory}
          semanticActionFeedback={semanticActionFeedback}
        />
        <PublishingLayerHooksPanel
          panelId="publishing-layer-panel"
          rrDashboard={rrDashboardPayload}
          operatingStack={operatingStackPayload}
          semanticIntelligence={semanticIntelligencePayload}
          semanticActionHistory={semanticActionHistory}
          semanticActionFeedback={semanticActionFeedback}
        />
        <SemanticActionLogPanel
          panelId="semantic-action-log-panel"
          actionHistory={semanticActionHistory}
          feedbackLoop={semanticActionFeedback}
        />
      </section>
    </main>
  );
}
