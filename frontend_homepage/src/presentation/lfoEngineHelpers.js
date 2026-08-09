export const LFO_DOCUMENT_FORMATS = ["linear", "2x_linear", "12_point", "perpetual"];

function normalizeArray(value) {
  return Array.isArray(value) ? value : [];
}

function resolveScienceSurfaceTierState({ scienceSurface = {}, timelineSnapshot = {}, unifiedIntelligenceState = {} } = {}) {
  const riskLevel = String(
    scienceSurface?.risk_level
      || unifiedIntelligenceState?.synthesis?.risk_clusters?.primary
      || "low",
  );
  const alignmentScore = Number(scienceSurface?.alignment_score ?? timelineSnapshot?.alignment_score ?? 0);
  const stabilityScore = Number(scienceSurface?.stability_score ?? timelineSnapshot?.stability_score ?? 0);
  const completionRatio = Number(scienceSurface?.completion_ratio ?? timelineSnapshot?.completion_ratio ?? 0);
  const triggerCount = Number(scienceSurface?.trigger_count || unifiedIntelligenceState?.orchestration?.trigger_count || 0);
  const latestPhase = String(scienceSurface?.latest_phase || timelineSnapshot?.latest_phase || "").toLowerCase();

  const studioReadyScore = Number(((0.4 * completionRatio) + (0.35 * alignmentScore) + (0.25 * stabilityScore)).toFixed(3));
  const enterpriseReadyScore = Number(((0.45 * alignmentScore) + (0.35 * stabilityScore) + (0.2 * completionRatio) - (0.03 * triggerCount)).toFixed(3));
  const unlocked = completionRatio >= 1 || latestPhase === "studio" || latestPhase === "enterprise";
  const enterpriseUnlocked = completionRatio >= 1 || latestPhase === "enterprise";

  let surfacePhase = String(scienceSurface?.surface_phase || "").toLowerCase();
  if (!surfacePhase) {
    if (latestPhase === "studio" || latestPhase === "enterprise") {
      surfacePhase = latestPhase;
    } else if (completionRatio >= 1) {
      surfacePhase = alignmentScore >= 0.78 && stabilityScore >= 0.72 && riskLevel !== "high" && triggerCount <= 3
        ? "enterprise"
        : "studio";
    } else {
      surfacePhase = latestPhase || "ideas";
    }
  }

  return {
    surface_phase: surfacePhase,
    surface_tiers: scienceSurface?.surface_tiers || {
      studio: {
        phase: "studio",
        label: "creator_publisher_tier",
        unlocked,
        active: surfacePhase === "studio",
        readiness_score: studioReadyScore,
      },
      enterprise: {
        phase: "enterprise",
        label: "operational_organizational_tier",
        unlocked: enterpriseUnlocked,
        active: surfacePhase === "enterprise",
        readiness_score: enterpriseReadyScore,
      },
    },
  };
}

function buildFallbackIndustryRows(groupTemplates = [], latestPhase = "", latestSlotIndex = 0) {
  return normalizeArray(groupTemplates).flatMap((template) => {
    const groupName = template?.group_metadata?.group_name || "Unknown";
    const groupId = Number(template?.group_metadata?.group_id || 0);
    const groupIndustry = normalizeArray(template?.industries).map((industry, index) => ({
      template_id: `industry_lfo_${String(groupId).padStart(2, "0")}_${String(index + 1).padStart(2, "0")}`,
      inherits_from: template?.template_id || "",
      group_id: groupId,
      group_name: groupName,
      sector_name: template?.group_metadata?.sector_name || "",
      industry_name: industry?.industry_name || "",
      sub_industries: normalizeArray(industry?.sub_industries),
      branch_ids: normalizeArray(template?.sevm_template?.branches).map((branch) => branch?.branch_id).filter(Boolean),
      timeline_binding: {
        latest_slot_index: latestSlotIndex,
        latest_phase: latestPhase,
      },
      surface_contract: {
        math: { mode: "sacp_probability_surface", feature_rows: [] },
        language: { mode: "ednp_transcript_surface", documents: [] },
        arts: { mode: "vlsm_creator_surface", creator_scaffolds: [] },
        science: { mode: "mbsp_consumer_gui_surface", lenses: [] },
      },
    }));
    return groupIndustry;
  });
}

function buildFallbackMicroRows(industryTemplates = [], latestPhase = "", latestSlotIndex = 0) {
  return normalizeArray(industryTemplates).flatMap((template) => {
    const industryName = template?.industry_name || template?.group_name || "Unknown Industry";
    const groupName = template?.group_name || template?.group_metadata?.group_name || "Unknown Group";
    const groupId = Number(template?.group_id || template?.group_metadata?.group_id || 0);
    const subIndustries = normalizeArray(template?.sub_industries);
    const resolvedSubIndustries = subIndustries.length > 0 ? subIndustries : [industryName];
    const branchIds = normalizeArray(template?.branch_ids);
    return resolvedSubIndustries.map((subIndustryName, index) => ({
      template_id: `micro_lfo_${String(groupId).padStart(2, "0")}_${String(index + 1).padStart(2, "0")}`,
      inherits_from: template?.template_id || "",
      group_id: groupId,
      group_name: groupName,
      industry_name: industryName,
      sub_industry_name: subIndustryName,
      branch_ids: branchIds,
      timeline_binding: {
        latest_slot_index: Number(template?.timeline_binding?.latest_slot_index || latestSlotIndex || 0),
        latest_phase: String(template?.timeline_binding?.latest_phase || latestPhase || ""),
      },
      surface_contract: {
        math: { mode: "sacp_probability_surface", feature_rows: [] },
        language: { mode: "ednp_transcript_surface", documents: [] },
        arts: { mode: "vlsm_creator_surface", creator_scaffolds: [] },
        science: { mode: "mbsp_consumer_gui_surface", lenses: [] },
      },
    }));
  });
}

export function buildTimelineSnapshot(unifiedIntelligenceState = {}) {
  const semantic = unifiedIntelligenceState?.semantic_metadata || {};
  const progression = unifiedIntelligenceState?.slot_progression || {};
  return {
    latest_slot_index: Number(progression.latest_slot_index || 0),
    latest_phase: String(progression.latest_phase || ""),
    drift_score: Number(semantic.drift_score || 0),
    stability_score: Number(semantic.stability_score || 0),
    alignment_score: Number(semantic.alignment_score || 0),
    completion_ratio: Number(progression.completion_ratio || 0),
  };
}

export function buildSynthesisSnapshot(unifiedIntelligenceState = {}) {
  const synthesis = unifiedIntelligenceState?.synthesis || {};
  const riskCluster = synthesis?.risk_clusters?.primary || "low";
  return {
    risk_level: String(riskCluster || "low"),
    drift_trend: String(synthesis?.drift_trend?.direction || "stable"),
    alignment_trajectory: String(synthesis?.alignment_trajectory?.direction || "stable"),
  };
}

export function buildMvpFeaturePathways(timelineSignalState = {}, unifiedIntelligenceState = {}) {
  const latestSlot = Number(unifiedIntelligenceState?.slot_progression?.latest_slot_index || timelineSignalState?.latest_event?.slot_index || 0);
  const latestPhase = String(unifiedIntelligenceState?.slot_progression?.latest_phase || timelineSignalState?.latest_event?.phase || "timeline").toLowerCase();
  return [
    `project_to_mvp_slot_${latestSlot || 1}`,
    `${latestPhase || "timeline"}_documentation_chain`,
    "creator_presentation_scaffold",
    "consumer_gui_science_surface",
  ];
}

export function buildLfoEngineViewModel({
  timelineSignalState = {},
  unifiedIntelligenceState = {},
  lfoEnvelope = {},
} = {}) {
  const timelineSnapshot = buildTimelineSnapshot(unifiedIntelligenceState);
  const priorityQueue = normalizeArray(unifiedIntelligenceState?.orchestration?.priority_queue);
  const features = normalizeArray(lfoEnvelope?.feature_probability);
  const backendMathRows = normalizeArray(lfoEnvelope?.math_surface?.feature_rows);
  const backendLanguageDocuments = normalizeArray(lfoEnvelope?.language_surface?.documents);
  const backendArtsScaffolds = normalizeArray(lfoEnvelope?.arts_surface?.creator_scaffolds);
  const backendScienceLenses = normalizeArray(lfoEnvelope?.science_surface?.lenses);
  const scienceSurfaceTierState = resolveScienceSurfaceTierState({
    scienceSurface: lfoEnvelope?.science_surface || {},
    timelineSnapshot,
    unifiedIntelligenceState,
  });
  const backendIndustryTemplates = normalizeArray(lfoEnvelope?.industry_templates);
  const backendMicroTemplates = normalizeArray(lfoEnvelope?.micro_templates);
  const fallbackIndustryTemplates = buildFallbackIndustryRows(
    normalizeArray(lfoEnvelope?.group_templates),
    timelineSnapshot.latest_phase,
    timelineSnapshot.latest_slot_index,
  );
  const resolvedIndustryTemplates = backendIndustryTemplates.length > 0 ? backendIndustryTemplates : fallbackIndustryTemplates;
  const industryTemplateSource = backendIndustryTemplates.length > 0 ? "backend" : "derived";
  const fallbackMicroTemplates = buildFallbackMicroRows(
    resolvedIndustryTemplates,
    timelineSnapshot.latest_phase,
    timelineSnapshot.latest_slot_index,
  );
  const resolvedMicroTemplates = backendMicroTemplates.length > 0 ? backendMicroTemplates : fallbackMicroTemplates;
  const microTemplateSource = backendMicroTemplates.length > 0 ? "backend" : "derived";

  const mathSurface = {
    title: "Math (SACP)",
    feature_rows: (backendMathRows.length > 0 ? backendMathRows : features).map((item) => ({
      feature: item.feature,
      slot_index: Number(item?.slot_index || timelineSnapshot.latest_slot_index),
      probability: Number((item?.probability ?? item?.pipeline?.probability) || 0),
      grade: String(item?.grade || "C"),
    })),
  };

  const languageSurface = {
    title: "Language (EDNP)",
    document_tracks: (backendLanguageDocuments.length > 0
      ? backendLanguageDocuments
      : LFO_DOCUMENT_FORMATS.map((formatName) => ({
          format: formatName,
          transcript_id: `ednp_${formatName}_${timelineSnapshot.latest_slot_index || 1}`,
          summary: `Deterministic ${formatName} transcript bound to slot ${timelineSnapshot.latest_slot_index || 1}.`,
        }))),
  };

  const artsSurface = {
    title: "Arts (VLSM)",
    creator_scaffolds: (backendArtsScaffolds.length > 0
      ? backendArtsScaffolds
      : normalizeArray(lfoEnvelope?.group_templates).slice(0, 16).map((template) => ({
      template_id: template.template_id,
      group_name: template?.group_metadata?.group_name || "Unknown",
      branch_count: Number(template?.sevm_template?.logical_branch_count || 0),
      mode: "creator_only",
      }))),
  };

  const scienceSurface = {
    title: "Science (MBSP)",
    consumer_gui: {
      lenses: backendScienceLenses,
      trigger_count: Number(lfoEnvelope?.science_surface?.trigger_count || priorityQueue.length),
      risk_level: String(lfoEnvelope?.group_templates?.[0]?.sevm_template?.synthesis?.risk_level || unifiedIntelligenceState?.synthesis?.risk_clusters?.primary || "low"),
      latest_phase: String(lfoEnvelope?.science_surface?.latest_phase || timelineSnapshot.latest_phase || ""),
      surface_phase: String(scienceSurfaceTierState.surface_phase || ""),
      surface_tiers: scienceSurfaceTierState.surface_tiers,
      completion_ratio: Number(lfoEnvelope?.science_surface?.completion_ratio || timelineSnapshot.completion_ratio || 0),
    },
  };

  const industrySurface = {
    title: "Industry Templates",
    source: industryTemplateSource,
    template_rows: resolvedIndustryTemplates.map((template) => ({
      template_id: template.template_id,
      group_name: template.group_name || template?.group_metadata?.group_name || "Unknown",
      industry_name: template.industry_name || template?.industry_name || "",
      branch_count: Number(template?.branch_ids?.length || template?.surface_contract?.arts?.creator_scaffolds?.[0]?.branch_count || 0),
      latest_slot_index: Number(template?.timeline_binding?.latest_slot_index || timelineSnapshot.latest_slot_index || 0),
      latest_phase: String(template?.timeline_binding?.latest_phase || timelineSnapshot.latest_phase || ""),
      has_surface_contract: Boolean(template?.surface_contract),
      science_lens_count: normalizeArray(template?.surface_contract?.science?.lenses).length,
    })),
  };

  const microSurface = {
    title: "Micro Templates",
    source: microTemplateSource,
    template_rows: resolvedMicroTemplates.map((template) => ({
      template_id: template.template_id,
      group_name: template.group_name || "Unknown",
      industry_name: template.industry_name || "",
      sub_industry_name: template.sub_industry_name || "",
      branch_count: Number(template?.branch_ids?.length || 0),
      latest_slot_index: Number(template?.timeline_binding?.latest_slot_index || timelineSnapshot.latest_slot_index || 0),
      latest_phase: String(template?.timeline_binding?.latest_phase || timelineSnapshot.latest_phase || ""),
      has_surface_contract: Boolean(template?.surface_contract),
      science_lens_count: normalizeArray(template?.surface_contract?.science?.lenses).length,
    })),
  };

  return {
    template_summary: {
      group_template_count: Number(lfoEnvelope?.template_summary?.group_template_count || 0),
      industry_template_count: Number(lfoEnvelope?.template_summary?.industry_template_count || 0),
      sevm_logical_branch_count: normalizeArray(lfoEnvelope?.sevm_logical_branches).length,
    },
    math_surface: mathSurface,
    language_surface: languageSurface,
    arts_surface: artsSurface,
    science_surface: scienceSurface,
    industry_surface: industrySurface,
    micro_surface: microSurface,
    sevm_group_templates: normalizeArray(lfoEnvelope?.group_templates),
    industry_templates: resolvedIndustryTemplates,
    micro_templates: resolvedMicroTemplates,
    probability_rows: features,
  };
}
