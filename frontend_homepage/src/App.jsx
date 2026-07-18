import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import {
  applyPresetToSlide,
  comparePresetBundle,
  deletePresetBundle,
  fetchPresetBundleHistory,
  fetchPresetBundleShares,
  fetchPresetBundleTags,
  fetchPresetBundles,
  fetchSemanticPresets,
  fetchOverview,
  fetchPresentationSlides,
  fetchResolvedSlide,
  generateSlideBundle,
  postAction,
  rollbackPresetBundle,
  savePresetBundleShare,
  savePresetBundleTag,
  savePresetBundle,
  savePreferences,
} from "./api/homepageApi";
import QpcBlueprint from "./presentation/QpcBlueprint";
import RoutingLayoutPreview from "./presentation/RoutingLayoutPreview";
import SquareRootTimelineGrid from "./presentation/SquareRootTimelineGrid";
import StoryHierarchyExplorer from "./presentation/StoryHierarchyExplorer";
import SemanticOperationsPanel from "./presentation/SemanticOperationsPanel";
import { SQUARE_ROOT_TIMELINE_CELLS } from "./presentation/squareRootTimelineModel";
import DashboardCard from "./ui/DashboardCard";
import FlowPanel from "./ui/FlowPanel";
import QuickActions from "./ui/QuickActions";
import SettingsPanel from "./ui/SettingsPanel";
import Taskboard from "./ui/Taskboard";
import BaseTrueWheelDemo from "./presentation/BaseTrueWheelDemo";
import { DeterministicErrorBoundary, DeterministicGuardedSurface } from "./ui/DeterministicBoundary";
import { getDeterministicReleaseMetadata } from "./config/deterministicRelease";
import { getTierDeploymentRules } from "./config/tierDeploymentRules";
import { DETERMINISTIC_RELEASE_GATES } from "./config/deterministicReleaseGates";
import { getDeterministicRollbackPolicy } from "./config/releaseRollbackPolicy";
import { buildDeterministicReleaseReport } from "./config/deterministicReleaseReport";
import {
  emitDeterministicTelemetry,
  incrementDeterministicMetric,
  reportDeterministicError,
  startDeterministicTimer,
  stopDeterministicTimer,
} from "./ui/deterministicTelemetry";
import { TemplateGroupInspectorPanel } from "../../ui/diagnostics/TemplateGroupInspectorPanel";
import CompartmentPage from "../../basetrue/components/CompartmentPage";
import EnterpriseWorkspace from "../../basetrue/workspaces/EnterpriseWorkspace";
import StudioWorkspace from "../../basetrue/workspaces/StudioWorkspace";
import { canUseGovernedApplyMode } from "../../basetrue/logic/pipelineLogic";
import btAnchor from "../../basetrue/anchors/bt_anchor.json";

const fallbackFlow = { status: "active", progress: 42, message: "In progress" };
const fallbackTasks = [
  { id: 1, title: "Review Notes", description: "Check today's flow" },
  { id: 2, title: "Update Settings", description: "Adjust preferences" },
];
const fallbackSettings = { notifications: true, dark_mode: false };
const PRESET_STORAGE_KEY = "mdx_registry_custom_presets_v1";
const TIMELINE_SELECTION_STORAGE_KEY = "btpe_timeline_selection_v1";
const QUICK_PRESET_IDS = ["operations_view", "customer_view", "delivery_view", "executive_view"];
const ROUTE_PHASES = ["create", "post", "work"];
const QPC_COUNT_PRESETS = [
  { label: "Base 4/16/64", counts: [4, 16, 64] },
  { label: "Growth 4/20/64", counts: [4, 20, 64] },
  { label: "Wide 8/24/64", counts: [8, 24, 64] },
  { label: "Compact 2/8/32", counts: [2, 8, 32] },
];

function slugifyCompartmentName(name = "") {
  return String(name)
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/(^-|-$)/g, "");
}

function parseBaseTrueCompartmentRoute(pathname) {
  const segments = String(pathname || "")
    .split("/")
    .filter(Boolean);

  if (segments[0] !== "basetrue") {
    return null;
  }

  if (segments.length === 1) {
    return {
      error:
        "Missing route segments. Use /basetrue/<public|personal>/<compartment>/<1-12>/<tier>",
    };
  }

  const profile = segments[1];
  if (profile !== "public" && profile !== "personal") {
    return {
      error: "Profile must be public or personal.",
    };
  }

  const compartmentSegment = decodeURIComponent(segments[2] || "");
  const index = Number(segments[3]);
  const tier = String(segments[4] || "novice").toLowerCase();

  const validTiers = Object.keys(btAnchor.tiers || {});
  if (!validTiers.includes(tier)) {
    return {
      error: `Invalid tier. Use one of: ${validTiers.join(", ")}`,
    };
  }

  if (!Number.isInteger(index) || index < 1 || index > 12) {
    return {
      error: "Compartment index must be an integer from 1 to 12.",
    };
  }

  const names = Array.isArray(btAnchor.compartments?.[profile]) ? btAnchor.compartments[profile] : [];
  const bySlug = new Map(names.map((name) => [slugifyCompartmentName(name), name]));
  const compartmentName = bySlug.get(slugifyCompartmentName(compartmentSegment));

  if (!compartmentName) {
    return {
      error: `Unknown compartment for ${profile}.`,
    };
  }

  return {
    profile,
    name: compartmentName,
    index,
    tier,
  };
}

function buildBaseTruePath(profile, compartmentSlug, index, tier) {
  return `/basetrue/${profile}/${compartmentSlug}/${index}/${tier}`;
}

const BASETRUE_ROUTE_PRESETS = [
  {
    id: "novice_start",
    label: "Novice Start",
    profile: "public",
    compartmentSlug: "bos",
    index: 1,
    tier: "novice",
  },
  {
    id: "rr_start",
    label: "RR Start",
    profile: "public",
    compartmentSlug: "boe",
    index: 3,
    tier: "intermediate",
  },
  {
    id: "qpu_start",
    label: "QPU Start",
    profile: "public",
    compartmentSlug: "bop",
    index: 4,
    tier: "studio",
  },
  {
    id: "tower_start",
    label: "Tower Start",
    profile: "public",
    compartmentSlug: "library",
    index: 5,
    tier: "enterprise",
  },
];

function detectQpcPresetLabel(profile = []) {
  for (const preset of QPC_COUNT_PRESETS) {
    const isMatch = preset.counts.every((value, index) => Number(profile?.[index] || 0) === Number(value || 0));
    if (isMatch) {
      return preset.label;
    }
  }
  return "custom";
}

function resolveTimelineCellByIndex(index) {
  return SQUARE_ROOT_TIMELINE_CELLS.find((cell) => Number(cell.latticeIndex || 0) === Number(index || 0)) || null;
}

export default function App() {
  const releaseMetadata = useMemo(() => getDeterministicReleaseMetadata(), []);
  const tierDeploymentRules = useMemo(() => getTierDeploymentRules(), []);
  const rollbackPolicy = useMemo(() => getDeterministicRollbackPolicy(), []);
  const deterministicReleaseReport = useMemo(
    () =>
      buildDeterministicReleaseReport({
        releaseMetadata,
        tierDeploymentRules,
        releaseGates: DETERMINISTIC_RELEASE_GATES,
        rollbackPolicy,
      }),
    [releaseMetadata, rollbackPolicy, tierDeploymentRules],
  );
  const noticeTimerRef = useRef(null);
  const presetInitRef = useRef(false);
  const qpcPanelRef = useRef(null);
  const routeLoadingTimerRef = useRef("");
  const pathname = window.location.pathname === "/" ? "/" : window.location.pathname.replace(/\/+$/, "");
  const isDiagnosticsRoute = pathname === "/diagnostics";
  const isBaseTrueWheelRoute = pathname === "/base-true-wheel";
  const isStudioWorkspaceRoute = pathname === "/basetrue/studio";
  const isEnterpriseWorkspaceRoute = pathname === "/basetrue/enterprise" || pathname === "/basetrue/tower";
  const studioTierParam = new URLSearchParams(window.location.search).get("tier");
  const enterpriseRouteAllowed = canUseGovernedApplyMode("enterprise");
  const baseTrueCompartmentRoute =
    isStudioWorkspaceRoute || isEnterpriseWorkspaceRoute ? null : parseBaseTrueCompartmentRoute(pathname);
  const activeRouteTier = isStudioWorkspaceRoute
    ? "studio"
    : isEnterpriseWorkspaceRoute
      ? "enterprise"
      : baseTrueCompartmentRoute?.tier || "novice";
  const activeDeploymentPolicy = tierDeploymentRules.byTier?.[activeRouteTier] || null;

  if (isStudioWorkspaceRoute && studioTierParam === "enterprise") {
    throw new Error("Tier/profile mismatch: Studio route cannot request enterprise tier");
  }
  const [overview, setOverview] = useState({
    welcome: "Your daily overview",
    flow: fallbackFlow,
    tasks: [],
    settings: fallbackSettings,
  });
  const [notice, setNotice] = useState(null);
  const [presentationSlides, setPresentationSlides] = useState([]);
  const [presentationSummary, setPresentationSummary] = useState(null);
  const [isPresentationLoading, setIsPresentationLoading] = useState(true);
  const [slideSearch, setSlideSearch] = useState("");
  const [slideTagFilter, setSlideTagFilter] = useState("all");
  const [slideTagCountFilter, setSlideTagCountFilter] = useState("all");
  const [slideCategoryFilter, setSlideCategoryFilter] = useState("all");
  const [slideComponentFilter, setSlideComponentFilter] = useState("all");
  const [slidePageFilter, setSlidePageFilter] = useState("all");
  const [slideSort, setSlideSort] = useState("title_asc");
  const [slideGroupBy, setSlideGroupBy] = useState("none");
  const [activePresetId, setActivePresetId] = useState("custom_live");
  const [customPresets, setCustomPresets] = useState([]);
  const [customPresetName, setCustomPresetName] = useState("");
  const [routeSlideId, setRouteSlideId] = useState("1");
  const [routeSlide, setRouteSlide] = useState(null);
  const [routeError, setRouteError] = useState("");
  const [isRouteLoading, setIsRouteLoading] = useState(false);
  const [semanticPresets, setSemanticPresets] = useState([]);
  const [presetBundles, setPresetBundles] = useState([]);
  const [presetInput, setPresetInput] = useState("post.purple.statistics");
  const [isPresetApplying, setIsPresetApplying] = useState(false);
  const [bundleInput, setBundleInput] = useState("bundle.foundation.triad");
  const [bundleInversionMode, setBundleInversionMode] = useState("none");
  const [isBundleGenerating, setIsBundleGenerating] = useState(false);
  const [bundlePreview, setBundlePreview] = useState(null);
  const [bundleDraftName, setBundleDraftName] = useState("");
  const [bundleDraftFamily, setBundleDraftFamily] = useState("custom.user");
  const [bundleDraftDescription, setBundleDraftDescription] = useState("");
  const [bundleDraftStep, setBundleDraftStep] = useState("");
  const [bundleDraftSequence, setBundleDraftSequence] = useState([]);
  const [editingBundleName, setEditingBundleName] = useState("");
  const [persistGeneratedSlides, setPersistGeneratedSlides] = useState(false);
  const [bundleCompareFromRevision, setBundleCompareFromRevision] = useState(1);
  const [bundleCompareToRevision, setBundleCompareToRevision] = useState(1);
  const [isBundleComparing, setIsBundleComparing] = useState(false);
  const [isBundleRollingBack, setIsBundleRollingBack] = useState(false);
  const [bundleCompareResult, setBundleCompareResult] = useState(null);
  const [bundleShares, setBundleShares] = useState([]);
  const [isBundleSharesLoading, setIsBundleSharesLoading] = useState(false);
  const [isBundleShareSaving, setIsBundleShareSaving] = useState(false);
  const [shareUsernameInput, setShareUsernameInput] = useState("");
  const [sharePermissionInput, setSharePermissionInput] = useState("view");
  const [shareIsActiveInput, setShareIsActiveInput] = useState(true);
  const [bundleTags, setBundleTags] = useState([]);
  const [isBundleTagsLoading, setIsBundleTagsLoading] = useState(false);
  const [isBundleTagSaving, setIsBundleTagSaving] = useState(false);
  const [tagNameInput, setTagNameInput] = useState("");
  const [tagRevisionInput, setTagRevisionInput] = useState(1);
  const [tagNoteInput, setTagNoteInput] = useState("");
  const [bundleTimelineRows, setBundleTimelineRows] = useState([]);
  const [bundleTimelineShareEvents, setBundleTimelineShareEvents] = useState([]);
  const [isBundleTimelineLoading, setIsBundleTimelineLoading] = useState(false);
  const [bundleCatalogTagFilter, setBundleCatalogTagFilter] = useState("all");
  const [bundleTimelinePage, setBundleTimelinePage] = useState(1);
  const [bundleTimelinePageSize, setBundleTimelinePageSize] = useState(8);
  const [bundleTimelineTagFilter, setBundleTimelineTagFilter] = useState("all");
  const [bundleTimelineActorFilter, setBundleTimelineActorFilter] = useState("all");
  const [bundleTimelineSeverityFilter, setBundleTimelineSeverityFilter] = useState("all");
  const [relayImageLabel, setRelayImageLabel] = useState("Repository Relay");
  const [relayProcessorLabel, setRelayProcessorLabel] = useState("Quantum Series Circuit Processor (QPU)");
  const [relaySubjectLabel, setRelaySubjectLabel] = useState("Subject");
  const [relayBranchCount, setRelayBranchCount] = useState(4);
  const [relayTermCount, setRelayTermCount] = useState(16);
  const [relayMetaTermCount, setRelayMetaTermCount] = useState(64);
  const [relayTier4Count, setRelayTier4Count] = useState(0);
  const [relaySelectedNode, setRelaySelectedNode] = useState(null);
  const [timelineSelection, setTimelineSelection] = useState(() => {
    if (typeof window === "undefined") {
      return null;
    }
    try {
      const raw = window.localStorage.getItem(TIMELINE_SELECTION_STORAGE_KEY);
      if (!raw) {
        return null;
      }
      const parsed = JSON.parse(raw);
      return resolveTimelineCellByIndex(parsed?.latticeIndex || 0);
    } catch (_error) {
      return null;
    }
  });
  const [storyEnginePanelTab, setStoryEnginePanelTab] = useState("timeline");
  const [qpcLabel, setQpcLabel] = useState("Quantum Processor Circuit (QPC)");
  const [qpcRelayNames, setQpcRelayNames] = useState(["Relay A", "Relay B", "Relay C", "Relay D"]);
  const [qpcRelaySubjects, setQpcRelaySubjects] = useState(["Subject 1", "Subject 2", "Subject 3", "Subject 4"]);
  const [qpcRelayCountProfiles, setQpcRelayCountProfiles] = useState([
    [4, 16, 64],
    [4, 16, 64],
    [4, 16, 64],
    [4, 16, 64],
  ]);
  const [qpcRelayCompareApproved, setQpcRelayCompareApproved] = useState([false, false, false, false]);
  const [qpcProfileFilter, setQpcProfileFilter] = useState("all");
  const [qpcSelectedRelay, setQpcSelectedRelay] = useState(null);
  const [isQpcHotkeysArmed, setIsQpcHotkeysArmed] = useState(false);
  const [qpcCompareEnabled, setQpcCompareEnabled] = useState(false);
  const [qpcCompareMode, setQpcCompareMode] = useState(false);
  const [qpcCompareSelection, setQpcCompareSelection] = useState([]);
  const [btRouteProfile, setBtRouteProfile] = useState("public");
  const [btRouteCompartmentSlug, setBtRouteCompartmentSlug] = useState("bos");
  const [btRouteIndex, setBtRouteIndex] = useState(1);
  const [btRouteTier, setBtRouteTier] = useState("novice");

  const showNotice = useCallback((type, text) => {
    if (noticeTimerRef.current) {
      clearTimeout(noticeTimerRef.current);
    }
    setNotice({ type, text });
    noticeTimerRef.current = setTimeout(() => {
      setNotice(null);
    }, 2200);
  }, []);

  useEffect(() => {
    let active = true;
    fetchOverview()
      .then((payload) => {
        if (!active) {
          return;
        }
        setOverview((prev) => ({
          ...prev,
          ...payload,
          flow: payload.flow || fallbackFlow,
          settings: payload.settings || fallbackSettings,
        }));
      })
      .catch(() => {
        reportDeterministicError({
          tier: "novice",
          surface: "workspace",
          code: "overview_fetch_failed",
        });
      });

    fetchPresentationSlides()
      .then((payload) => {
        if (!active) {
          return;
        }
        setPresentationSlides(payload.slides || []);
        setPresentationSummary(payload.summary || null);
      })
      .catch(() => {
        if (!active) {
          return;
        }
        setPresentationSlides([]);
        setPresentationSummary(null);
        reportDeterministicError({
          tier: "novice",
          surface: "pipeline",
          code: "presentation_manifest_failed",
        });
      })
      .finally(() => {
        if (!active) {
          return;
        }
        setIsPresentationLoading(false);
      });

    return () => {
      active = false;
      if (noticeTimerRef.current) {
        clearTimeout(noticeTimerRef.current);
      }
    };
  }, []);

  useEffect(() => {
    try {
      const raw = window.localStorage.getItem(PRESET_STORAGE_KEY);
      if (!raw) {
        return;
      }
      const parsed = JSON.parse(raw);
      if (Array.isArray(parsed)) {
        setCustomPresets(parsed);
      }
    } catch (_error) {
      setCustomPresets([]);
    }
  }, []);

  useEffect(() => {
    const darkModeEnabled = Boolean(overview.settings?.dark_mode);
    document.body.classList.toggle("dark-mode", darkModeEnabled);
  }, [overview.settings?.dark_mode]);

  useEffect(() => {
    if (typeof window === "undefined") {
      return;
    }
    if (!timelineSelection) {
      window.localStorage.removeItem(TIMELINE_SELECTION_STORAGE_KEY);
      return;
    }
    window.localStorage.setItem(
      TIMELINE_SELECTION_STORAGE_KEY,
      JSON.stringify({ latticeIndex: timelineSelection.latticeIndex }),
    );
  }, [timelineSelection]);

  useEffect(() => {
    if (isRouteLoading && !routeLoadingTimerRef.current) {
      routeLoadingTimerRef.current = startDeterministicTimer("app.route.preview.loading", {
        surface: "pipeline",
        tier: "novice",
      });
      emitDeterministicTelemetry({
        eventName: "app.route.preview.loading.started",
        tier: "novice",
        surface: "pipeline",
      });
    }

    if (!isRouteLoading && routeLoadingTimerRef.current) {
      const durationMs = stopDeterministicTimer(routeLoadingTimerRef.current);
      routeLoadingTimerRef.current = "";
      emitDeterministicTelemetry({
        eventName: "app.route.preview.loading.completed",
        tier: "novice",
        surface: "pipeline",
        payload: { durationMs },
      });
      incrementDeterministicMetric("app.route.preview.loading.completed", {
        tier: "novice",
      });
    }
  }, [isRouteLoading]);

  useEffect(() => {
    if (!routeError) {
      return;
    }
    reportDeterministicError({
      tier: "novice",
      surface: "pipeline",
      code: "route_preview_error",
      payload: {
        message: routeError,
      },
    });
  }, [routeError]);

  useEffect(() => {
    const onUnhandledError = () => {
      reportDeterministicError({
        tier: "novice",
        surface: "workspace",
        code: "window_error",
      });
    };
    const onUnhandledRejection = () => {
      reportDeterministicError({
        tier: "novice",
        surface: "workspace",
        code: "window_unhandled_rejection",
      });
    };

    window.addEventListener("error", onUnhandledError);
    window.addEventListener("unhandledrejection", onUnhandledRejection);
    return () => {
      window.removeEventListener("error", onUnhandledError);
      window.removeEventListener("unhandledrejection", onUnhandledRejection);
    };
  }, []);

  useEffect(() => {
    emitDeterministicTelemetry({
      eventName: "app.release.metadata.loaded",
      tier: "novice",
      surface: "workspace",
      payload: {
        semanticVersion: releaseMetadata.semanticVersion,
        buildId: releaseMetadata.buildId,
        channel: releaseMetadata.channel,
      },
    });
  }, [releaseMetadata]);

  useEffect(() => {
    emitDeterministicTelemetry({
      eventName: "app.release.rollback.metadata.loaded",
      tier: activeRouteTier,
      surface: "workspace",
      payload: {
        rollbackAllowed: Boolean(rollbackPolicy.rollbackAllowed),
        previousBuildId: rollbackPolicy.previousBuildId,
      },
    });
  }, [activeRouteTier, rollbackPolicy]);

  useEffect(() => {
    emitDeterministicTelemetry({
      eventName: "app.release.report.generated",
      tier: activeRouteTier,
      surface: "workspace",
      payload: {
        semanticVersion: deterministicReleaseReport.semanticVersion,
        buildId: deterministicReleaseReport.buildId,
        requiredGateCount: deterministicReleaseReport.requiredGateIds.length,
      },
    });
    window.__btDeterministicReleaseReport = deterministicReleaseReport;
  }, [activeRouteTier, deterministicReleaseReport]);

  useEffect(() => {
    emitDeterministicTelemetry({
      eventName: "app.release.deployment.rule.loaded",
      tier: activeRouteTier,
      surface: "workspace",
      payload: {
        deployEnabled: Boolean(activeDeploymentPolicy?.enabled),
        defaultChannel: activeDeploymentPolicy?.defaultChannel || "",
      },
    });
  }, [activeDeploymentPolicy, activeRouteTier]);

  useEffect(() => {
    emitDeterministicTelemetry({
      eventName: "app.route.context.loaded",
      tier: "novice",
      surface: "workspace",
      payload: {
        pathname,
        releaseVersion: releaseMetadata.semanticVersion,
        releaseBuildId: releaseMetadata.buildId,
        routeTier: activeRouteTier,
        deployEnabled: Boolean(activeDeploymentPolicy?.enabled),
      },
    });
  }, [activeDeploymentPolicy, activeRouteTier, pathname, releaseMetadata]);

  useEffect(() => {
    const onKeyDown = (event) => {
      if (event.metaKey || event.ctrlKey || event.altKey) {
        return;
      }

      const panelElement = qpcPanelRef.current;
      const activeElement = document.activeElement;
      const isPanelFocused = Boolean(panelElement && activeElement && panelElement.contains(activeElement));
      if (!isQpcHotkeysArmed && !isPanelFocused) {
        return;
      }

      const target = event.target;
      const tagName = String(target?.tagName || "").toLowerCase();
      const isEditable = Boolean(target?.isContentEditable) || ["input", "textarea", "select"].includes(tagName);
      if (isEditable) {
        return;
      }

      const key = String(event.key || "").toLowerCase();
      if (key === "a") {
        setQpcProfileFilter("all");
      } else if (key === "p") {
        setQpcProfileFilter("preset");
      } else if (key === "c") {
        setQpcProfileFilter("custom");
      }
    };

    window.addEventListener("keydown", onKeyDown);
    return () => {
      window.removeEventListener("keydown", onKeyDown);
    };
  }, [isQpcHotkeysArmed]);

  const onSettingChange = useCallback((key, value) => {
    setOverview((current) => {
      const next = {
        ...current,
        settings: {
          ...(current.settings || {}),
          [key]: value,
        },
      };
      savePreferences(next.settings)
        .then(() => showNotice("success", "Settings saved"))
        .catch(() => showNotice("error", "Could not save settings"));
      return next;
    });
  }, [showNotice]);

  const baseTrueTierOptions = useMemo(() => Object.keys(btAnchor.tiers || {}), []);

  const baseTrueCompartmentsForProfile = useMemo(() => {
    const list = Array.isArray(btAnchor.compartments?.[btRouteProfile]) ? btAnchor.compartments[btRouteProfile] : [];
    return list.map((name) => ({ name, slug: slugifyCompartmentName(name) }));
  }, [btRouteProfile]);

  useEffect(() => {
    if (baseTrueCompartmentsForProfile.length === 0) {
      setBtRouteCompartmentSlug("");
      return;
    }

    const exists = baseTrueCompartmentsForProfile.some((item) => item.slug === btRouteCompartmentSlug);
    if (!exists) {
      setBtRouteCompartmentSlug(baseTrueCompartmentsForProfile[0].slug);
    }
  }, [baseTrueCompartmentsForProfile, btRouteCompartmentSlug]);

  const baseTrueRoutePath = useMemo(
    () => buildBaseTruePath(btRouteProfile, btRouteCompartmentSlug || "", btRouteIndex, btRouteTier),
    [btRouteCompartmentSlug, btRouteIndex, btRouteProfile, btRouteTier],
  );

  const openBaseTrueRoute = useCallback(() => {
    window.location.href = baseTrueRoutePath;
  }, [baseTrueRoutePath]);

  const applyBaseTrueRoutePreset = useCallback((preset) => {
    if (!preset) {
      return;
    }
    setBtRouteProfile(preset.profile);
    setBtRouteCompartmentSlug(preset.compartmentSlug);
    setBtRouteIndex(preset.index);
    setBtRouteTier(preset.tier);
  }, []);

  const loadResolvedRoute = useCallback((slideId) => {
    const normalized = String(slideId || "").trim();
    if (!normalized) {
      setRouteError("Enter a slide id to load a resolved route.");
      return;
    }

    setIsRouteLoading(true);
    setRouteError("");
    fetchResolvedSlide(normalized)
      .then((payload) => {
        setRouteSlide(payload);
      })
      .catch(() => {
        setRouteSlide(null);
        setRouteError(`Could not load resolved route for slide ${normalized}.`);
      })
      .finally(() => {
        setIsRouteLoading(false);
      });
  }, []);

  useEffect(() => {
    loadResolvedRoute(routeSlideId);
  }, [loadResolvedRoute, routeSlideId]);

  useEffect(() => {
    let active = true;
    fetchSemanticPresets()
      .then((payload) => {
        if (!active) {
          return;
        }
        const list = Array.isArray(payload?.presets) ? payload.presets : [];
        setSemanticPresets(list);
      })
      .catch(() => {
        if (!active) {
          return;
        }
        setSemanticPresets([]);
      });
    return () => {
      active = false;
    };
  }, []);

  const refreshPresetBundles = useCallback(() => {
    return fetchPresetBundles()
      .then((payload) => {
        const list = Array.isArray(payload?.bundles) ? payload.bundles : [];
        setPresetBundles(list);
        if (list.length > 0) {
          setBundleInput((current) => current || list[0].name);
        }
      })
      .catch(() => {
        setPresetBundles([]);
      });
  }, []);

  useEffect(() => {
    refreshPresetBundles();
  }, [refreshPresetBundles]);

  const phaseByPresetName = useMemo(() => {
    const map = new Map();
    semanticPresets.forEach((item) => {
      if (item?.name && item?.phase) {
        map.set(item.name, item.phase);
      }
    });
    return map;
  }, [semanticPresets]);

  const decorateBundle = useCallback((bundle) => {
    const sequence = Array.isArray(bundle?.sequence) ? bundle.sequence.filter(Boolean) : [];
    const phaseDistribution = {};
    const layoutDistribution = {};
    sequence.forEach((presetName) => {
      const phase = phaseByPresetName.get(presetName) || "unknown";
      const layout = phase === "create" ? "matrix" : phase === "post" ? "journey" : phase === "work" ? "pipeline" : "matrix";
      phaseDistribution[phase] = (phaseDistribution[phase] || 0) + 1;
      layoutDistribution[layout] = (layoutDistribution[layout] || 0) + 1;
    });

    return {
      ...bundle,
      slide_count: bundle?.slide_count ?? sequence.length,
      phase_distribution: bundle?.phase_distribution || phaseDistribution,
      layout_distribution: bundle?.layout_distribution || layoutDistribution,
      supports_inversion: bundle?.supports_inversion ?? true,
      sequence,
      kind: bundle?.kind || "custom",
    };
  }, [phaseByPresetName]);

  const allBundleCatalog = useMemo(() => {
    const map = new Map();
    presetBundles.forEach((bundle) => {
      if (bundle?.name) {
        map.set(bundle.name, decorateBundle(bundle));
      }
    });
    return Array.from(map.values()).sort((a, b) => (a.family || "").localeCompare(b.family || "") || a.name.localeCompare(b.name));
  }, [presetBundles, decorateBundle]);

  const allBundleCatalogTags = useMemo(() => {
    const tagNames = new Set();
    allBundleCatalog.forEach((bundle) => {
      (bundle?.tags || []).forEach((tag) => {
        const name = String(tag?.name || "").trim();
        if (name) {
          tagNames.add(name);
        }
      });
    });
    return Array.from(tagNames).sort((a, b) => a.localeCompare(b));
  }, [allBundleCatalog]);

  const filteredBundleCatalog = useMemo(() => {
    if (bundleCatalogTagFilter === "all") {
      return allBundleCatalog;
    }
    return allBundleCatalog.filter((bundle) =>
      (bundle?.tags || []).some((tag) => String(tag?.name || "") === bundleCatalogTagFilter),
    );
  }, [allBundleCatalog, bundleCatalogTagFilter]);

  const addBundleDraftStep = useCallback(() => {
    if (!bundleDraftStep) {
      return;
    }
    setBundleDraftSequence((current) => [...current, bundleDraftStep]);
    setBundleDraftStep("");
  }, [bundleDraftStep]);

  const moveBundleDraftStep = useCallback((index, delta) => {
    setBundleDraftSequence((current) => {
      const next = [...current];
      const target = index + delta;
      if (target < 0 || target >= next.length) {
        return current;
      }
      const [item] = next.splice(index, 1);
      next.splice(target, 0, item);
      return next;
    });
  }, []);

  const removeBundleDraftStep = useCallback((index) => {
    setBundleDraftSequence((current) => current.filter((_, stepIndex) => stepIndex !== index));
  }, []);

  const loadBundleIntoEditor = useCallback((bundle, mode = "edit") => {
    if (!bundle) {
      return;
    }
    const isDuplicate = mode === "duplicate";
    setEditingBundleName(isDuplicate ? "" : (bundle.kind === "custom" ? bundle.name : ""));
    setBundleDraftName(isDuplicate ? `${bundle.label || bundle.name} Copy` : (bundle.label || ""));
    setBundleDraftFamily(bundle.family || "custom.user");
    setBundleDraftDescription(bundle.description || "");
    setBundleDraftSequence(Array.isArray(bundle.sequence) ? bundle.sequence : []);
  }, []);

  const hasUnsavedBundleChanges = useMemo(() => {
    const trimmedName = bundleDraftName.trim();
    const trimmedFamily = bundleDraftFamily.trim() || "custom.user";
    const trimmedDescription = bundleDraftDescription.trim();
    const sequenceKey = JSON.stringify(bundleDraftSequence);

    if (editingBundleName) {
      const source = allBundleCatalog.find((item) => item.name === editingBundleName);
      if (!source) {
        return Boolean(trimmedName || trimmedDescription || bundleDraftSequence.length);
      }
      return (
        trimmedName !== (source.label || "") ||
        trimmedFamily !== (source.family || "custom.user") ||
        trimmedDescription !== (source.description || "") ||
        sequenceKey !== JSON.stringify(source.sequence || [])
      );
    }

    return Boolean(trimmedName || trimmedDescription || bundleDraftSequence.length || trimmedFamily !== "custom.user");
  }, [allBundleCatalog, bundleDraftDescription, bundleDraftFamily, bundleDraftName, bundleDraftSequence, editingBundleName]);

  const saveCustomBundle = useCallback(() => {
    const trimmedName = bundleDraftName.trim();
    const isUpdating = Boolean(editingBundleName);
    if (!trimmedName || bundleDraftSequence.length === 0) {
      setRouteError("Custom bundles require a name and at least one preset step.");
      return;
    }
    const slug = trimmedName.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/(^-|-$)/g, "") || "bundle";
    const bundle = {
      name: editingBundleName || `custom.bundle.${slug}`,
      label: trimmedName,
      family: bundleDraftFamily.trim() || "custom.user",
      description: bundleDraftDescription.trim(),
      sequence: bundleDraftSequence,
    };
    savePresetBundle(bundle)
      .then((payload) => {
        setPresetBundles((current) => {
          const nextBundle = payload.bundle;
          const filtered = current.filter((item) => item.name !== nextBundle.name);
          return [...filtered, nextBundle].sort((a, b) => (a.family || "").localeCompare(b.family || "") || a.name.localeCompare(b.name));
        });
        setBundleInput(bundle.name);
        setEditingBundleName(bundle.name);
        setBundleDraftName("");
        setBundleDraftDescription("");
        setBundleDraftFamily("custom.user");
        setBundleDraftSequence([]);
        setEditingBundleName("");
        showNotice("success", `${isUpdating ? "Updated" : "Saved"} custom bundle: ${bundle.label}`);
      })
      .catch((error) => {
        setRouteError(error.message || "Could not save custom bundle.");
        showNotice("error", "Could not save custom bundle");
      });
  }, [bundleDraftName, bundleDraftSequence, bundleDraftFamily, bundleDraftDescription, editingBundleName, showNotice]);

  const deleteCustomBundle = useCallback((bundleName) => {
    deletePresetBundle(bundleName)
      .then(() => {
        setPresetBundles((current) => current.filter((item) => item.name !== bundleName));
        if (bundleInput === bundleName) {
          setBundleInput("");
        }
        showNotice("success", `Deleted custom bundle: ${bundleName}`);
      })
      .catch((error) => {
        setRouteError(error.message || "Could not delete custom bundle.");
        showNotice("error", "Could not delete custom bundle");
      });
  }, [bundleInput, showNotice]);

  const applyPresetForRoute = useCallback((presetName) => {
    const normalizedSlideId = String(routeSlideId || "").trim();
    const normalizedPreset = String(presetName || "").trim();

    if (!normalizedSlideId) {
      setRouteError("Enter a slide id before applying a preset.");
      return;
    }
    if (!normalizedPreset) {
      setRouteError("Enter a preset name before applying.");
      return;
    }

    setIsPresetApplying(true);
    setRouteError("");
    applyPresetToSlide(normalizedSlideId, { preset: normalizedPreset })
      .then((payload) => {
        setRouteSlide(payload);
        setPresetInput(normalizedPreset);
        showNotice("success", `Preset applied: ${normalizedPreset}`);
      })
      .catch((error) => {
        setRouteError(error.message || "Preset apply failed.");
        showNotice("error", "Preset apply failed");
      })
      .finally(() => {
        setIsPresetApplying(false);
      });
  }, [routeSlideId, showNotice]);

  const routePhasePresetShortcuts = useMemo(() => {
    const byPhase = new Map();
    semanticPresets.forEach((item) => {
      const phase = String(item?.phase || "").toLowerCase();
      const name = String(item?.name || "");
      if (!ROUTE_PHASES.includes(phase) || !name) {
        return;
      }
      if (!byPhase.has(phase)) {
        byPhase.set(phase, name);
      }
    });

    return ROUTE_PHASES
      .filter((phase) => byPhase.has(phase))
      .map((phase) => ({
        phase,
        label: `${phase.charAt(0).toUpperCase()}${phase.slice(1)} Layout`,
        preset: byPhase.get(phase),
      }));
  }, [semanticPresets]);

  const selectedBundle = useMemo(() => {
    return allBundleCatalog.find((item) => item.name === bundleInput) || null;
  }, [allBundleCatalog, bundleInput]);

  const applyTagCompareShortcut = useCallback((bundleName, revisionNumber) => {
    const revision = Number(revisionNumber || 1);
    setBundleInput(bundleName);
    setBundleCompareToRevision(Math.max(1, revision));
    setBundleCompareFromRevision(Math.max(1, revision - 1));
  }, []);

  useEffect(() => {
    const revisionCount = selectedBundle?.revision_count || 0;
    if (!selectedBundle || revisionCount <= 1) {
      setBundleCompareFromRevision(1);
      setBundleCompareToRevision(Math.max(1, revisionCount || 1));
      setBundleCompareResult(null);
      return;
    }
    setBundleCompareFromRevision(Math.max(1, revisionCount - 1));
    setBundleCompareToRevision(revisionCount);
    setBundleCompareResult(null);
    setTagRevisionInput(revisionCount || 1);
    setBundleTimelinePage(1);
    setBundleTimelineTagFilter("all");
    setBundleTimelineActorFilter("all");
    setBundleTimelineSeverityFilter("all");
  }, [selectedBundle?.name, selectedBundle?.revision_count]);

  useEffect(() => {
    setBundleTimelinePage(1);
  }, [bundleTimelinePageSize]);

  const bundleTimelineTagOptions = useMemo(() => {
    const tags = new Set();
    bundleTimelineRows.forEach((entry) => {
      (entry.tags || []).forEach((tag) => {
        const name = String(tag?.name || "").trim();
        if (name) {
          tags.add(name);
        }
      });
    });
    return Array.from(tags).sort((a, b) => a.localeCompare(b));
  }, [bundleTimelineRows]);

  const bundleTimelineActorOptions = useMemo(() => {
    const actors = new Set();
    bundleTimelineRows.forEach((entry) => {
      const username = String(entry?.createdBy?.username || "").trim();
      if (username) {
        actors.add(username);
      }
    });
    return Array.from(actors).sort((a, b) => a.localeCompare(b));
  }, [bundleTimelineRows]);

  const tagActorFilteredBundleTimelineRows = useMemo(() => {
    return bundleTimelineRows.filter((entry) => {
      if (bundleTimelineTagFilter !== "all") {
        const hasTag = (entry.tags || []).some((tag) => String(tag?.name || "") === bundleTimelineTagFilter);
        if (!hasTag) {
          return false;
        }
      }
      if (bundleTimelineActorFilter !== "all") {
        const actor = String(entry?.createdBy?.username || "");
        if (actor !== bundleTimelineActorFilter) {
          return false;
        }
      }
      return true;
    });
  }, [bundleTimelineActorFilter, bundleTimelineRows, bundleTimelineTagFilter]);

  const bundleTimelineSeverityCounts = useMemo(() => {
    const counts = { high: 0, medium: 0, low: 0 };
    tagActorFilteredBundleTimelineRows.forEach((entry) => {
      const level = String(entry?.severityLevel || "low");
      if (Object.prototype.hasOwnProperty.call(counts, level)) {
        counts[level] += 1;
      }
    });
    return counts;
  }, [tagActorFilteredBundleTimelineRows]);

  const filteredBundleTimelineRows = useMemo(() => {
    if (bundleTimelineSeverityFilter === "all") {
      return tagActorFilteredBundleTimelineRows;
    }
    return tagActorFilteredBundleTimelineRows.filter((entry) => String(entry?.severityLevel || "") === bundleTimelineSeverityFilter);
  }, [bundleTimelineSeverityFilter, tagActorFilteredBundleTimelineRows]);

  const isTimelineFilterResetDisabled = useMemo(() => {
    return (
      bundleTimelineTagFilter === "all" &&
      bundleTimelineActorFilter === "all" &&
      bundleTimelineSeverityFilter === "all" &&
      bundleTimelinePage === 1
    );
  }, [bundleTimelineActorFilter, bundleTimelinePage, bundleTimelineSeverityFilter, bundleTimelineTagFilter]);

  const timelineFilterResetTitle = isTimelineFilterResetDisabled
    ? "Timeline filters are already at defaults"
    : "Reset tag, actor, severity filters and return to page 1";

  const paginatedBundleTimelineRows = useMemo(() => {
    if (!filteredBundleTimelineRows.length) {
      return [];
    }
    const start = (bundleTimelinePage - 1) * bundleTimelinePageSize;
    return filteredBundleTimelineRows.slice(start, start + bundleTimelinePageSize);
  }, [bundleTimelinePage, bundleTimelinePageSize, filteredBundleTimelineRows]);

  const bundleTimelinePageCount = useMemo(() => {
    if (!filteredBundleTimelineRows.length) {
      return 1;
    }
    return Math.max(1, Math.ceil(filteredBundleTimelineRows.length / bundleTimelinePageSize));
  }, [bundleTimelinePageSize, filteredBundleTimelineRows.length]);

  useEffect(() => {
    setBundleTimelinePage((current) => Math.min(current, bundleTimelinePageCount));
  }, [bundleTimelinePageCount]);

  const loadSelectedBundleTags = useCallback((bundleName) => {
    if (!bundleName) {
      setBundleTags([]);
      return Promise.resolve();
    }
    setIsBundleTagsLoading(true);
    return fetchPresetBundleTags(bundleName)
      .then((payload) => {
        setBundleTags(Array.isArray(payload?.tags) ? payload.tags : []);
      })
      .catch((error) => {
        setBundleTags([]);
        setRouteError(error.message || "Could not load revision tags.");
      })
      .finally(() => {
        setIsBundleTagsLoading(false);
      });
  }, []);

  const loadBundleTimeline = useCallback((bundleName, includeShareChanges = false) => {
    if (!bundleName) {
      setBundleTimelineRows([]);
      setBundleTimelineShareEvents([]);
      return Promise.resolve();
    }
    setIsBundleTimelineLoading(true);
    const historyPromise = fetchPresetBundleHistory(bundleName);
    const sharesPromise = includeShareChanges
      ? fetchPresetBundleShares(bundleName).catch(() => ({ shares: [] }))
      : Promise.resolve({ shares: [] });

    return Promise.all([historyPromise, sharesPromise])
      .then(async ([historyPayload, sharesPayload]) => {
        const historyRows = Array.isArray(historyPayload?.history) ? historyPayload.history : [];
        const tags = Array.isArray(historyPayload?.tags) ? historyPayload.tags : [];

        const tagsByRevision = new Map();
        tags.forEach((tag) => {
          const revisionNumber = Number(tag?.revision_number || 0);
          if (!revisionNumber) {
            return;
          }
          if (!tagsByRevision.has(revisionNumber)) {
            tagsByRevision.set(revisionNumber, []);
          }
          tagsByRevision.get(revisionNumber).push(tag);
        });

        const compareRequests = [];
        for (let index = 0; index < historyRows.length - 1; index += 1) {
          const newerRevision = Number(historyRows[index]?.revision_number || 0);
          const olderRevision = Number(historyRows[index + 1]?.revision_number || 0);
          if (!newerRevision || !olderRevision) {
            continue;
          }
          compareRequests.push(
            comparePresetBundle(bundleName, olderRevision, newerRevision)
              .then((payload) => ({ revisionNumber: newerRevision, compare: payload?.compare || null }))
              .catch(() => null),
          );
        }
        const compareResults = await Promise.all(compareRequests);
        const compareByRevision = new Map();
        compareResults.forEach((entry) => {
          if (entry?.revisionNumber) {
            compareByRevision.set(entry.revisionNumber, entry.compare);
          }
        });

        const signatureByIndex = historyRows.map((row) => JSON.stringify({
          label: row?.label || "",
          family: row?.family || "",
          description: row?.description || "",
          sequence: Array.isArray(row?.sequence) ? row.sequence : [],
        }));

        const timelineRows = historyRows.map((row, index) => {
          const revisionNumber = Number(row?.revision_number || 0);
          const previous = historyRows[index + 1] || null;
          const previousRevisionNumber = Number(previous?.revision_number || 0) || null;

          let rollbackToRevision = null;
          for (let olderIndex = index + 1; olderIndex < signatureByIndex.length; olderIndex += 1) {
            if (signatureByIndex[index] === signatureByIndex[olderIndex]) {
              rollbackToRevision = Number(historyRows[olderIndex]?.revision_number || 0) || null;
              break;
            }
          }

          const compare = compareByRevision.get(revisionNumber);
          const delta = compare
            ? {
                added: (compare?.sequence?.added || []).length,
                removed: (compare?.sequence?.removed || []).length,
                reordered: (compare?.sequence?.reordered || []).length,
                labelChanged: Boolean(compare?.changes?.label_changed),
                familyChanged: Boolean(compare?.changes?.family_changed),
                descriptionChanged: Boolean(compare?.changes?.description_changed),
              }
            : null;

          let severityScore = 0;
          if (delta) {
            severityScore += delta.added + delta.removed + delta.reordered;
            if (delta.labelChanged) {
              severityScore += 1;
            }
            if (delta.familyChanged) {
              severityScore += 1;
            }
            if (delta.descriptionChanged) {
              severityScore += 1;
            }
          }
          if (rollbackToRevision) {
            severityScore += 2;
          }

          let severityLevel = "low";
          if (severityScore >= 6) {
            severityLevel = "high";
          } else if (severityScore >= 3) {
            severityLevel = "medium";
          }

          const currentEditor = row?.created_by?.username || "unknown";
          const previousEditor = previous?.created_by?.username || "";

          return {
            revisionNumber,
            previousRevisionNumber,
            createdAt: row?.created_at || null,
            createdBy: row?.created_by || null,
            tags: tagsByRevision.get(revisionNumber) || [],
            rollbackToRevision,
            delta,
            severityLevel,
            ownerChangedFrom: previous && currentEditor !== previousEditor ? previousEditor : null,
          };
        });

        const shareEvents = (Array.isArray(sharesPayload?.shares) ? sharesPayload.shares : [])
          .map((share) => ({
            username: share?.username || "",
            permission: share?.permission || "view",
            isActive: Boolean(share?.is_active),
            updatedAt: share?.updated_at || null,
          }))
          .sort((a, b) => (b.updatedAt || "").localeCompare(a.updatedAt || ""));

        setBundleTimelineRows(timelineRows);
        setBundleTimelineShareEvents(shareEvents);
      })
      .catch((error) => {
        setBundleTimelineRows([]);
        setBundleTimelineShareEvents([]);
        setRouteError(error.message || "Could not load revision timeline.");
      })
      .finally(() => {
        setIsBundleTimelineLoading(false);
      });
  }, []);

  useEffect(() => {
    if (!selectedBundle || selectedBundle.kind !== "custom") {
      setBundleTags([]);
      return;
    }
    loadSelectedBundleTags(selectedBundle.name);
  }, [loadSelectedBundleTags, selectedBundle]);

  useEffect(() => {
    if (!selectedBundle || selectedBundle.kind !== "custom") {
      setBundleTimelineRows([]);
      setBundleTimelineShareEvents([]);
      return;
    }
    loadBundleTimeline(selectedBundle.name, selectedBundle.access_role === "owner");
  }, [loadBundleTimeline, selectedBundle?.access_role, selectedBundle?.kind, selectedBundle?.name]);

  const saveSelectedBundleTag = useCallback(() => {
    const normalizedName = tagNameInput.trim();
    if (!selectedBundle?.name || !normalizedName) {
      setRouteError("Tag name is required.");
      return;
    }
    setIsBundleTagSaving(true);
    setRouteError("");
    savePresetBundleTag(selectedBundle.name, {
      name: normalizedName,
      revision_number: tagRevisionInput,
      note: tagNoteInput.trim(),
    })
      .then(() => loadSelectedBundleTags(selectedBundle.name))
      .then(() => loadBundleTimeline(selectedBundle.name, selectedBundle.access_role === "owner"))
      .then(() => {
        setTagNameInput("");
        setTagNoteInput("");
        showNotice("success", `Tag saved: ${normalizedName}`);
      })
      .catch((error) => {
        setRouteError(error.message || "Could not save revision tag.");
        showNotice("error", "Could not save revision tag");
      })
      .finally(() => {
        setIsBundleTagSaving(false);
      });
  }, [loadBundleTimeline, loadSelectedBundleTags, selectedBundle?.access_role, selectedBundle?.name, showNotice, tagNameInput, tagNoteInput, tagRevisionInput]);

  const loadSelectedBundleShares = useCallback((bundleName) => {
    if (!bundleName) {
      setBundleShares([]);
      return Promise.resolve();
    }
    setIsBundleSharesLoading(true);
    return fetchPresetBundleShares(bundleName)
      .then((payload) => {
        setBundleShares(Array.isArray(payload?.shares) ? payload.shares : []);
      })
      .catch((error) => {
        setBundleShares([]);
        setRouteError(error.message || "Could not load share grants.");
      })
      .finally(() => {
        setIsBundleSharesLoading(false);
      });
  }, []);

  useEffect(() => {
    if (!selectedBundle || selectedBundle.kind !== "custom" || selectedBundle.access_role !== "owner") {
      setBundleShares([]);
      return;
    }
    loadSelectedBundleShares(selectedBundle.name);
  }, [loadSelectedBundleShares, selectedBundle]);

  const saveSelectedBundleShare = useCallback(() => {
    const normalizedUsername = shareUsernameInput.trim();
    if (!selectedBundle?.name || !normalizedUsername) {
      setRouteError("Share username is required.");
      return;
    }
    setIsBundleShareSaving(true);
    setRouteError("");
    savePresetBundleShare(selectedBundle.name, {
      username: normalizedUsername,
      permission: sharePermissionInput,
      is_active: shareIsActiveInput,
    })
      .then(() => loadSelectedBundleShares(selectedBundle.name))
      .then(() => loadBundleTimeline(selectedBundle.name, true))
      .then(() => {
        setShareUsernameInput("");
        setSharePermissionInput("view");
        setShareIsActiveInput(true);
        showNotice("success", `Share grant saved for ${normalizedUsername}`);
      })
      .catch((error) => {
        setRouteError(error.message || "Could not save share grant.");
        showNotice("error", "Could not save share grant");
      })
      .finally(() => {
        setIsBundleShareSaving(false);
      });
  }, [loadBundleTimeline, loadSelectedBundleShares, selectedBundle?.name, shareIsActiveInput, sharePermissionInput, shareUsernameInput, showNotice]);

  const compareSelectedBundle = useCallback(() => {
    if (!selectedBundle?.name) {
      return;
    }
    setIsBundleComparing(true);
    setRouteError("");
    comparePresetBundle(selectedBundle.name, bundleCompareFromRevision, bundleCompareToRevision)
      .then((payload) => {
        setBundleCompareResult(payload?.compare || null);
        showNotice("success", `Compared revisions ${bundleCompareFromRevision} → ${bundleCompareToRevision}`);
      })
      .catch((error) => {
        setBundleCompareResult(null);
        setRouteError(error.message || "Bundle compare failed.");
        showNotice("error", "Bundle compare failed");
      })
      .finally(() => {
        setIsBundleComparing(false);
      });
  }, [bundleCompareFromRevision, bundleCompareToRevision, selectedBundle?.name, showNotice]);

  const rollbackSelectedBundle = useCallback(() => {
    if (!selectedBundle?.name) {
      return;
    }
    setIsBundleRollingBack(true);
    setRouteError("");
    rollbackPresetBundle(selectedBundle.name, bundleCompareFromRevision)
      .then(() => refreshPresetBundles())
      .then(() => loadBundleTimeline(selectedBundle.name, selectedBundle.access_role === "owner"))
      .then(() => {
        setBundleCompareResult(null);
        showNotice("success", `Rolled back to revision ${bundleCompareFromRevision}`);
      })
      .catch((error) => {
        setRouteError(error.message || "Bundle rollback failed.");
        showNotice("error", "Bundle rollback failed");
      })
      .finally(() => {
        setIsBundleRollingBack(false);
      });
  }, [bundleCompareFromRevision, loadBundleTimeline, refreshPresetBundles, selectedBundle?.access_role, selectedBundle?.name, showNotice]);

  const generateBundleForRoute = useCallback((bundleName) => {
    const normalizedSlideId = String(routeSlideId || "").trim();
    const normalizedBundle = String(bundleName || "").trim();

    if (!normalizedSlideId) {
      setRouteError("Enter a slide id before generating a bundle.");
      return;
    }
    if (!normalizedBundle) {
      setRouteError("Select a bundle before generating.");
      return;
    }

    setIsBundleGenerating(true);
    setRouteError("");
    const selectedBundle = allBundleCatalog.find((item) => item.name === normalizedBundle);
    const requestPayload = selectedBundle?.kind === "custom"
      ? {
          name: selectedBundle.name,
          label: selectedBundle.label,
          family: selectedBundle.family,
          description: selectedBundle.description,
          sequence: selectedBundle.sequence,
          inversion: bundleInversionMode,
          persist_generated: persistGeneratedSlides,
        }
      : {
          bundle: normalizedBundle,
          inversion: bundleInversionMode,
          persist_generated: persistGeneratedSlides,
        };

    generateSlideBundle(normalizedSlideId, requestPayload)
      .then((payload) => {
        setBundlePreview(payload);
        if (Array.isArray(payload?.generated) && payload.generated.length > 0) {
          setRouteSlide(payload.generated[0].slide);
        }
        showNotice("success", `Bundle generated: ${normalizedBundle}`);
      })
      .catch((error) => {
        setBundlePreview(null);
        setRouteError(error.message || "Bundle generation failed.");
        showNotice("error", "Bundle generation failed");
      })
      .finally(() => {
        setIsBundleGenerating(false);
      });
  }, [allBundleCatalog, bundleInversionMode, routeSlideId, showNotice]);

  const actions = useMemo(
    () => [
      {
        id: 1,
        label: "Start Flow",
        onClick: () => {
          postAction("Start Flow")
            .then(() => {
              setOverview((current) => ({
                ...current,
                flow: {
                  ...(current.flow || fallbackFlow),
                  status: "active",
                  message: "Flow started",
                },
              }));
              showNotice("success", "Quick action logged: Start Flow");
            })
            .catch(() => showNotice("error", "Could not log action"));
        },
      },
      {
        id: 2,
        label: "Open Taskboard",
        onClick: () => {
          postAction("Open Taskboard")
            .then(() => showNotice("success", "Quick action logged: Open Taskboard"))
            .catch(() => showNotice("error", "Could not log action"));
        },
      },
      {
        id: 3,
        label: "Open Diagnostics",
        onClick: () => {
          window.location.assign("/diagnostics");
        },
      },
    ],
    [showNotice]
  );

  const tasks = overview.tasks?.length
    ? overview.tasks.map((task) => ({
        id: task.id,
        title: task.title,
        description: task.description,
      }))
    : fallbackTasks;

  const availableTagTypes = useMemo(() => {
    const tags = presentationSummary?.tags_by_type || {};
    return Object.keys(tags).sort();
  }, [presentationSummary]);

  const availableCategories = useMemo(() => {
    const categories = presentationSummary?.categories || {};
    return Object.keys(categories).sort();
  }, [presentationSummary]);

  const availableComponents = useMemo(() => {
    return Array.from(new Set(presentationSlides.map((slide) => slide.component_name).filter(Boolean))).sort();
  }, [presentationSlides]);

  const availablePages = useMemo(() => {
    return Array.from(new Set(presentationSlides.map((slide) => slide.page_name).filter(Boolean))).sort();
  }, [presentationSlides]);

  const registryPresets = useMemo(() => {
    return Array.isArray(presentationSummary?.presets) ? presentationSummary.presets : [];
  }, [presentationSummary]);

  const allPresets = useMemo(() => {
    const map = new Map();
    [...registryPresets, ...customPresets].forEach((preset) => {
      if (preset?.id) {
        map.set(preset.id, preset);
      }
    });
    return Array.from(map.values());
  }, [registryPresets, customPresets]);

  const quickPresets = useMemo(() => {
    return QUICK_PRESET_IDS.map((id) => allPresets.find((preset) => preset.id === id)).filter(Boolean);
  }, [allPresets]);

  const additionalPresets = useMemo(() => {
    const quickSet = new Set(quickPresets.map((preset) => preset.id));
    return allPresets.filter((preset) => !quickSet.has(preset.id));
  }, [allPresets, quickPresets]);

  const isPresetApplied = useCallback((preset) => {
    if (!preset) {
      return false;
    }
    const filters = preset.filters || {};
    return (
      (filters.tag_type || "all") === slideTagFilter &&
      (filters.tag_count_band || "all") === slideTagCountFilter &&
      (filters.category || "all") === slideCategoryFilter &&
      (filters.component_name || "all") === slideComponentFilter &&
      (filters.page_name || "all") === slidePageFilter &&
      (preset.sort_order || "title_asc") === slideSort &&
      (preset.grouping_mode || "none") === slideGroupBy &&
      (preset.search_query || "") === slideSearch
    );
  }, [
    slideTagFilter,
    slideTagCountFilter,
    slideCategoryFilter,
    slideComponentFilter,
    slidePageFilter,
    slideSort,
    slideGroupBy,
    slideSearch,
  ]);

  const applyPreset = useCallback((preset) => {
    if (!preset) {
      return;
    }
    const filters = preset.filters || {};
    setSlideTagFilter(filters.tag_type || "all");
    setSlideTagCountFilter(filters.tag_count_band || "all");
    setSlideCategoryFilter(filters.category || "all");
    setSlideComponentFilter(filters.component_name || "all");
    setSlidePageFilter(filters.page_name || "all");
    setSlideSort(preset.sort_order || "title_asc");
    setSlideGroupBy(preset.grouping_mode || "none");
    setSlideSearch(preset.search_query || "");
    setActivePresetId(preset.id || "custom_live");
  }, []);

  useEffect(() => {
    if (presetInitRef.current) {
      return;
    }
    if (!allPresets.length) {
      return;
    }
    const defaultPreset = allPresets.find((preset) => preset.id === "executive_view") || allPresets[0];
    applyPreset(defaultPreset);
    presetInitRef.current = true;
  }, [allPresets, applyPreset]);

  useEffect(() => {
    if (activePresetId === "custom_live") {
      return;
    }
    const activePreset = allPresets.find((preset) => preset.id === activePresetId);
    if (!activePreset) {
      setActivePresetId("custom_live");
      return;
    }
    if (!isPresetApplied(activePreset)) {
      setActivePresetId("custom_live");
    }
  }, [activePresetId, allPresets, isPresetApplied]);

  const persistCustomPresets = useCallback((nextPresets) => {
    setCustomPresets(nextPresets);
    window.localStorage.setItem(PRESET_STORAGE_KEY, JSON.stringify(nextPresets));
  }, []);

  const saveCurrentAsPreset = useCallback(() => {
    const trimmedName = customPresetName.trim();
    if (!trimmedName) {
      return;
    }
    const slug = trimmedName.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/(^-|-$)/g, "") || "preset";
    const preset = {
      id: `custom_${slug}_${Date.now()}`,
      name: trimmedName,
      quick_switch: false,
      filters: {
        tag_type: slideTagFilter,
        tag_count_band: slideTagCountFilter,
        category: slideCategoryFilter,
        component_name: slideComponentFilter,
        page_name: slidePageFilter,
      },
      sort_order: slideSort,
      grouping_mode: slideGroupBy,
      search_query: slideSearch,
    };
    const next = [...customPresets, preset];
    persistCustomPresets(next);
    setActivePresetId(preset.id);
    setCustomPresetName("");
  }, [
    customPresetName,
    slideTagFilter,
    slideTagCountFilter,
    slideCategoryFilter,
    slideComponentFilter,
    slidePageFilter,
    slideSort,
    slideGroupBy,
    slideSearch,
    customPresets,
    persistCustomPresets,
  ]);

  const removeActiveCustomPreset = useCallback(() => {
    if (!activePresetId.startsWith("custom_")) {
      return;
    }
    const next = customPresets.filter((preset) => preset.id !== activePresetId);
    persistCustomPresets(next);
    setActivePresetId("custom_live");
  }, [activePresetId, customPresets, persistCustomPresets]);

  const activePreset = useMemo(() => {
    return allPresets.find((preset) => preset.id === activePresetId) || null;
  }, [allPresets, activePresetId]);

  const canDeleteActiveCustomPreset = useMemo(() => {
    if (!activePresetId.startsWith("custom_")) {
      return false;
    }
    return customPresets.some((preset) => preset.id === activePresetId);
  }, [activePresetId, customPresets]);

  const activePresetLabel = useMemo(() => {
    if (activePreset && isPresetApplied(activePreset)) {
      return activePreset.name;
    }
    return "Current Filters";
  }, [activePreset, isPresetApplied]);

  const filteredSlides = useMemo(() => {
    const needle = slideSearch.trim().toLowerCase();
    return presentationSlides.filter((slide) => {
      const tagMatch =
        slideTagFilter === "all" ||
        Boolean(slide.tags_by_type && Object.prototype.hasOwnProperty.call(slide.tags_by_type, slideTagFilter));

      if (!tagMatch) {
        return false;
      }

      const tagCount = Number(slide.tag_count || 0);
      const tagCountMatch =
        slideTagCountFilter === "all" ||
        (slideTagCountFilter === "0-10" && tagCount >= 0 && tagCount <= 10) ||
        (slideTagCountFilter === "11-14" && tagCount >= 11 && tagCount <= 14) ||
        (slideTagCountFilter === "15+" && tagCount >= 15);
      if (!tagCountMatch) {
        return false;
      }

      const categoryMatch = slideCategoryFilter === "all" || slide.category === slideCategoryFilter;
      if (!categoryMatch) {
        return false;
      }

      const componentMatch = slideComponentFilter === "all" || slide.component_name === slideComponentFilter;
      if (!componentMatch) {
        return false;
      }

      const pageMatch = slidePageFilter === "all" || slide.page_name === slidePageFilter;
      if (!pageMatch) {
        return false;
      }

      if (!needle) {
        return true;
      }

      const haystack = [
        slide.title,
        slide.source_file,
        slide.route,
        slide.component_name,
        slide.page_name,
        ...(slide.preview_components || []),
      ]
        .filter(Boolean)
        .join(" ")
        .toLowerCase();

      return haystack.includes(needle);
    });
  }, [
    presentationSlides,
    slideSearch,
    slideTagFilter,
    slideTagCountFilter,
    slideCategoryFilter,
    slideComponentFilter,
    slidePageFilter,
  ]);

  const sortedSlides = useMemo(() => {
    const items = [...filteredSlides];
    items.sort((a, b) => {
      if (slideSort === "tag_desc") {
        return Number(b.tag_count || 0) - Number(a.tag_count || 0);
      }
      if (slideSort === "tag_asc") {
        return Number(a.tag_count || 0) - Number(b.tag_count || 0);
      }
      if (slideSort === "category_asc") {
        return (a.category || "").localeCompare(b.category || "") || (a.title || "").localeCompare(b.title || "");
      }
      if (slideSort === "title_desc") {
        return (b.title || "").localeCompare(a.title || "");
      }
      return (a.title || "").localeCompare(b.title || "");
    });
    return items;
  }, [filteredSlides, slideSort]);

  const groupedSlides = useMemo(() => {
    if (slideGroupBy === "none") {
      return [{ key: "All Slides", slides: sortedSlides }];
    }

    const bucketMap = new Map();
    sortedSlides.forEach((slide) => {
      let key = "Other";
      if (slideGroupBy === "category") {
        key = slide.category || "uncategorized";
      }
      if (slideGroupBy === "tag_type") {
        const tagKeys = Object.keys(slide.tags_by_type || {});
        key = tagKeys.length ? tagKeys.join(" + ") : "untagged";
      }
      if (!bucketMap.has(key)) {
        bucketMap.set(key, []);
      }
      bucketMap.get(key).push(slide);
    });

    return Array.from(bucketMap.entries())
      .sort((a, b) => a[0].localeCompare(b[0]))
      .map(([key, slides]) => ({ key, slides }));
  }, [sortedSlides, slideGroupBy]);

  const relayTierCounts = useMemo(() => {
    return [relayBranchCount, relayTermCount, relayMetaTermCount].map((count) => {
      const normalized = Number(count || 0);
      if (!Number.isFinite(normalized)) {
        return 0;
      }
      return Math.max(0, Math.min(256, Math.floor(normalized)));
    });
  }, [relayBranchCount, relayMetaTermCount, relayTermCount]);

  const qpcRelayPresetMatches = useMemo(() => {
    return qpcRelayCountProfiles.map((profile) => detectQpcPresetLabel(profile));
  }, [qpcRelayCountProfiles]);

  const qpcRelays = useMemo(() => {
    return qpcRelayNames.map((name, index) => ({
      id: index + 1,
      name: String(name || `Relay ${index + 1}`),
      subject: String(qpcRelaySubjects[index] || `Subject ${index + 1}`),
      profileLabel: qpcRelayPresetMatches[index],
      profileKind: qpcRelayPresetMatches[index] === "custom" ? "custom" : "preset",
      compareApproved: Boolean(qpcRelayCompareApproved[index]),
      counts: (qpcRelayCountProfiles[index] || [0, 0, 0]).map((count) => {
        const normalized = Number(count || 0);
        if (!Number.isFinite(normalized)) {
          return 0;
        }
        return Math.max(0, Math.min(256, Math.floor(normalized)));
      }),
    }));
  }, [qpcRelayCompareApproved, qpcRelayCountProfiles, qpcRelayNames, qpcRelayPresetMatches, qpcRelaySubjects]);

  const qpcGlobalPresetMatch = useMemo(() => {
    for (const preset of QPC_COUNT_PRESETS) {
      const isMatch = qpcRelayCountProfiles.every((profile) =>
        preset.counts.every((value, index) => Number(profile?.[index] || 0) === Number(value || 0)),
      );
      if (isMatch) {
        return preset.label;
      }
    }
    return "custom";
  }, [qpcRelayCountProfiles]);

  const qpcApprovedRelayCount = useMemo(() => {
    return qpcRelays.filter((relay) => relay.compareApproved).length;
  }, [qpcRelays]);

  const qpcAggregateMetaTerms = useMemo(() => {
    return qpcRelays.reduce((total, relay) => total + Number(relay.counts?.[2] || 0), 0);
  }, [qpcRelays]);

  const qpcCompareAllowed = qpcCompareEnabled && qpcApprovedRelayCount >= 2;

  useEffect(() => {
    if (!qpcCompareAllowed) {
      setQpcCompareMode(false);
      setQpcCompareSelection([]);
    }
  }, [qpcCompareAllowed]);

  const qpcCompareRelays = useMemo(() => {
    if (qpcCompareSelection.length !== 2) {
      return [];
    }
    const first = qpcRelays.find((relay) => relay.id === qpcCompareSelection[0]);
    const second = qpcRelays.find((relay) => relay.id === qpcCompareSelection[1]);
    return [first, second].filter(Boolean);
  }, [qpcCompareSelection, qpcRelays]);

  const qpcCompareSummary = useMemo(() => {
    if (qpcCompareRelays.length !== 2) {
      return null;
    }
    const [left, right] = qpcCompareRelays;
    const deltas = [0, 1, 2].map((index) => Number(right.counts[index] || 0) - Number(left.counts[index] || 0));
    const changedLevels = deltas.reduce((total, value) => total + (value !== 0 ? 1 : 0), 0);
    return {
      left,
      right,
      subjectChanged: left.subject !== right.subject,
      profileChanged: left.profileLabel !== right.profileLabel,
      changedLevels,
      deltas,
    };
  }, [qpcCompareRelays]);

  const loadQpcRelayIntoBlueprint = useCallback((relay) => {
    if (!relay) {
      return;
    }
    if (qpcCompareMode) {
      if (!qpcCompareAllowed) {
        showNotice("error", "Compare mode requires compare approval on at least 2 relays");
        return;
      }
      if (!relay.compareApproved) {
        showNotice("error", `${relay.name} is not approved for compare`);
        return;
      }
      setQpcCompareSelection((current) => {
        if (current.includes(relay.id)) {
          return current.filter((id) => id !== relay.id);
        }
        if (current.length < 2) {
          return [...current, relay.id];
        }
        return [current[1], relay.id];
      });
      return;
    }
    setQpcSelectedRelay(relay);
    setRelaySubjectLabel(String(relay.subject || "Subject"));
    setRelayBranchCount(Number(relay.counts?.[0] || 0));
    setRelayTermCount(Number(relay.counts?.[1] || 0));
    setRelayMetaTermCount(Number(relay.counts?.[2] || 0));
    setRelayTier4Count(0);
    showNotice("success", `Loaded ${relay.name} into Repository Relay panel`);
  }, [qpcCompareAllowed, qpcCompareMode, showNotice]);

  const handleTimelineCellSelect = useCallback((cell) => {
    if (!cell) {
      return;
    }

    setTimelineSelection(cell);
    setPresetInput(cell.presetId || "");
    setRelaySubjectLabel(String(cell.mlasSubject || "Subject"));
    setRelayBranchCount(4);
    setRelayTermCount(16);
    setRelayMetaTermCount(64);
    setRelayTier4Count(0);
    setRelaySelectedNode({
      tier: "SVEM -> CCCP -> DCHD",
      label: `${cell.links?.svemId || "svem"} / ${cell.links?.cccpId || "cccp"} / ${cell.links?.dchdId || "dchd"}`,
      index: Number(cell.latticeIndex || 0),
    });
    setStoryEnginePanelTab("timeline");
  }, []);

  if (isBaseTrueWheelRoute) {
    return (
      <main className="homepage-wrap basetrue-route">
        <section className="panel basetrue-route-hero">
          <p className="eyebrow">Demo Route</p>
          <h1>BaseTrue Wheel</h1>
          <p className="status-line">
            A dedicated route for the interactive BaseTrue quadrant wheel. Click a quadrant to see the selection state.
          </p>
          <a href="/" className="action-btn basetrue-route-back">
            Back to dashboard
          </a>
        </section>
        <BaseTrueWheelDemo />
      </main>
    );
  }

  if (baseTrueCompartmentRoute) {
    return (
      <main className="homepage-wrap basetrue-route">
        <section className="panel basetrue-route-hero">
          <p className="eyebrow">BaseTrue Route</p>
          <h1>Compartment Lens</h1>
          <p className="status-line">
            Anchor-driven compartment page using BaseTrue temporal, tier, and phase rules.
          </p>
          <a href="/" className="action-btn basetrue-route-back">
            Back to dashboard
          </a>
        </section>

        <section className="panel basetrue-route-builder">
          <p className="eyebrow">Route Builder</p>
          <h2>Generate BaseTrue URL</h2>
          <p className="status-line">Pick values and open a valid anchor-driven compartment route.</p>
          <div className="action-grid">
            {BASETRUE_ROUTE_PRESETS.map((preset) => (
              <button
                key={preset.id}
                type="button"
                className="action-btn"
                onClick={() => applyBaseTrueRoutePreset(preset)}
              >
                {preset.label}
              </button>
            ))}
          </div>
          <div className="routing-controls">
            <label>
              Profile
              <select value={btRouteProfile} onChange={(event) => setBtRouteProfile(event.target.value)}>
                <option value="public">public</option>
                <option value="personal">personal</option>
              </select>
            </label>
            <label>
              Compartment
              <select
                value={btRouteCompartmentSlug}
                onChange={(event) => setBtRouteCompartmentSlug(event.target.value)}
              >
                {baseTrueCompartmentsForProfile.map((item) => (
                  <option key={`${btRouteProfile}-${item.slug}`} value={item.slug}>
                    {item.name}
                  </option>
                ))}
              </select>
            </label>
            <label>
              Index
              <input
                type="number"
                min="1"
                max="12"
                value={btRouteIndex}
                onChange={(event) => {
                  const next = Number(event.target.value || 1);
                  const bounded = Math.min(12, Math.max(1, Number.isNaN(next) ? 1 : next));
                  setBtRouteIndex(bounded);
                }}
              />
            </label>
            <label>
              Tier
              <select value={btRouteTier} onChange={(event) => setBtRouteTier(event.target.value)}>
                {baseTrueTierOptions.map((tier) => (
                  <option key={tier} value={tier}>
                    {tier}
                  </option>
                ))}
              </select>
            </label>
            <button type="button" className="action-btn" onClick={openBaseTrueRoute}>
              Open Route
            </button>
          </div>
          <p className="status-line">{baseTrueRoutePath}</p>
        </section>

        {baseTrueCompartmentRoute.error ? (
          <DeterministicGuardedSurface
            tier="novice"
            surface="route-error"
            shellClassName="det-surface-stable det-surface-stable--novice"
            loading={false}
            releaseMetadata={releaseMetadata}
            deploymentPolicy={tierDeploymentRules.byTier?.novice}
            rollbackPolicy={rollbackPolicy}
          >
            <section className="panel">
              <h2>Invalid BaseTrue Route</h2>
              <p className="status-line">{baseTrueCompartmentRoute.error}</p>
              <p className="status-line">Example: /basetrue/public/bos/1/novice</p>
            </section>
          </DeterministicGuardedSurface>
        ) : (
          <DeterministicErrorBoundary
            tier={baseTrueCompartmentRoute.tier}
            surface="compartment-pipeline"
            shellClassName={`det-surface-stable det-surface-stable--${baseTrueCompartmentRoute.tier}`}
            releaseMetadata={releaseMetadata}
            deploymentPolicy={tierDeploymentRules.byTier?.[baseTrueCompartmentRoute.tier]}
            rollbackPolicy={rollbackPolicy}
            fallbackTitle="Compartment Route Recovery"
            fallbackMessage="Compartment fallback surface is active. Deterministic route, tier, and gating constraints are preserved."
            fallbackDetails="Fallback coverage: compartment panel, pipeline surface, and phase section render boundaries."
          >
            <CompartmentPage
              profile={baseTrueCompartmentRoute.profile}
              name={baseTrueCompartmentRoute.name}
              index={baseTrueCompartmentRoute.index}
              tier={baseTrueCompartmentRoute.tier}
            />
          </DeterministicErrorBoundary>
        )}
      </main>
    );
  }

  if (isStudioWorkspaceRoute) {
    return (
      <main className="homepage-wrap basetrue-route">
        <section className="panel basetrue-route-hero">
          <p className="eyebrow">BaseTrue Route</p>
          <h1>Studio Workspace</h1>
          <p className="status-line">Dedicated Studio environment with scaled QPU and no enterprise tower floors.</p>
          <p className="status-line">Governed apply mode and release workflows are disabled on Studio route.</p>
          <a href="/" className="action-btn basetrue-route-back">
            Back to dashboard
          </a>
        </section>
        <DeterministicErrorBoundary
          tier="studio"
          surface="workspace-panel"
          shellClassName="det-surface-stable det-surface-stable--studio"
          releaseMetadata={releaseMetadata}
          deploymentPolicy={tierDeploymentRules.byTier?.studio}
          rollbackPolicy={rollbackPolicy}
          fallbackTitle="Studio Workspace Recovery"
          fallbackMessage="Studio workspace fallback surface is active. Deterministic routing and governance constraints are preserved."
          fallbackDetails="Fallback coverage: workspace panels, compartments, pipelines, and QPU presentation surfaces."
        >
          <StudioWorkspace initialTier="studio" />
        </DeterministicErrorBoundary>
      </main>
    );
  }

  if (isEnterpriseWorkspaceRoute) {
    if (!enterpriseRouteAllowed) {
      return (
        <main className="homepage-wrap basetrue-route">
          <DeterministicGuardedSurface
            tier="enterprise"
            surface="route-gate"
            shellClassName="det-surface-stable det-surface-stable--enterprise"
            loading={false}
            releaseMetadata={releaseMetadata}
            deploymentPolicy={tierDeploymentRules.byTier?.enterprise}
            rollbackPolicy={rollbackPolicy}
          >
            <section className="panel basetrue-route-hero">
              <p className="eyebrow">BaseTrue Route</p>
              <h1>Enterprise Tower Workspace</h1>
              <p className="status-line">Enterprise route is disabled because governed apply mode is not available.</p>
              <a href="/" className="action-btn basetrue-route-back">
                Back to dashboard
              </a>
            </section>
          </DeterministicGuardedSurface>
        </main>
      );
    }

    return (
      <main className="homepage-wrap basetrue-route">
        <section className="panel basetrue-route-hero">
          <p className="eyebrow">BaseTrue Route</p>
          <h1>Enterprise Tower Workspace</h1>
          <p className="status-line">Full-power tower orchestration environment for enterprise projects only.</p>
          <a href="/" className="action-btn basetrue-route-back">
            Back to dashboard
          </a>
        </section>
        <DeterministicErrorBoundary
          tier="enterprise"
          surface="tower-workspace"
          shellClassName="det-surface-stable det-surface-stable--enterprise"
          releaseMetadata={releaseMetadata}
          deploymentPolicy={tierDeploymentRules.byTier?.enterprise}
          rollbackPolicy={rollbackPolicy}
          fallbackTitle="Enterprise Workspace Recovery"
          fallbackMessage="Enterprise tower fallback surface is active. Deterministic routing, gating, and governance constraints are preserved."
          fallbackDetails="Fallback coverage: tower, zone rail, guided chain, floor slice, and workspace panel surfaces."
        >
          <EnterpriseWorkspace accessTier="enterprise" />
        </DeterministicErrorBoundary>
      </main>
    );
  }

  if (isDiagnosticsRoute) {
    return (
      <main className="homepage-wrap diagnostics-route">
        <section className="panel diagnostics-route-hero">
          <h1>Diagnostics</h1>
          <p className="status-line">Tier-aware diagnostics for template group routing and mappings.</p>
        </section>
        <TemplateGroupInspectorPanel profile="enterprise" />
      </main>
    );
  }

  return (
    <main className="homepage-wrap">
      {notice ? <div className={`toast toast-${notice.type}`}>{notice.text}</div> : null}
      <DashboardCard title="Welcome" value={overview.welcome || "Your daily overview"} />
      <QuickActions actions={actions} />
      <FlowPanel flow={overview.flow || fallbackFlow} />
      <SquareRootTimelineGrid
        onCellSelect={handleTimelineCellSelect}
        initialLatticeIndex={timelineSelection?.latticeIndex || 1}
      />
      <Taskboard tasks={tasks} />
      <SettingsPanel settings={overview.settings || fallbackSettings} onChange={onSettingChange} />

      <section className="routing-integration panel">
        <p className="eyebrow">UI Integration</p>
        <h2>Resolved Route Layout Engine</h2>
        <p className="status-line">
          Create renders matrix, Post renders journey, and Work renders pipeline from the resolved routing payload.
        </p>
        <div className="routing-controls">
          <label>
            Slide ID
            <input
              type="number"
              min="1"
              step="1"
              value={routeSlideId}
              onChange={(event) => setRouteSlideId(event.target.value)}
            />
          </label>
          <button type="button" className="action-btn" onClick={() => loadResolvedRoute(routeSlideId)}>
            Load Route
          </button>
        </div>

        {timelineSelection ? (
          <div className="timeline-handoff panel story-engine-panel">
            <p className="eyebrow">Timeline Handoff</p>
            <p className="status-line">
              Lattice {timelineSelection.latticeIndex} {"->"} {timelineSelection.timelineLabel} / {timelineSelection.cpwState} / preset {timelineSelection.presetId}
            </p>

            <div className="story-engine-tabs" role="tablist" aria-label="Story Engine timeline tabs">
              <button
                type="button"
                role="tab"
                aria-selected={storyEnginePanelTab === "timeline"}
                className={`story-engine-tab${storyEnginePanelTab === "timeline" ? " is-active" : ""}`}
                onClick={() => setStoryEnginePanelTab("timeline")}
              >
                Timeline Context
              </button>
              <button
                type="button"
                role="tab"
                aria-selected={storyEnginePanelTab === "hierarchy"}
                className={`story-engine-tab${storyEnginePanelTab === "hierarchy" ? " is-active" : ""}`}
                onClick={() => setStoryEnginePanelTab("hierarchy")}
              >
                Hierarchy Links
              </button>
              <button
                type="button"
                role="tab"
                aria-selected={storyEnginePanelTab === "semantic"}
                className={`story-engine-tab${storyEnginePanelTab === "semantic" ? " is-active" : ""}`}
                onClick={() => setStoryEnginePanelTab("semantic")}
              >
                Semantic Ops
              </button>
            </div>

            {storyEnginePanelTab === "timeline" ? (
              <div className="story-engine-content" role="tabpanel" aria-label="Timeline context panel">
                <ul>
                  <li>Preset: {timelineSelection.presetId}</li>
                  <li>MLAS Subject: {timelineSelection.mlasSubject}</li>
                  <li>Color Token: {timelineSelection.mlasColorToken}</li>
                  <li>Semantic Intent: {timelineSelection.semanticIntentId}</li>
                </ul>
                <div className="action-grid">
                  <button type="button" onClick={() => applyPresetForRoute(timelineSelection.presetId)} disabled={isPresetApplying}>
                    {isPresetApplying ? "Applying..." : "Apply Timeline Preset"}
                  </button>
                  <button type="button" onClick={() => loadResolvedRoute(routeSlideId)} disabled={isRouteLoading}>
                    {isRouteLoading ? "Loading..." : "Refresh Route Preview"}
                  </button>
                </div>
              </div>
            ) : null}

            {storyEnginePanelTab === "hierarchy" ? (
              <div className="story-engine-content" role="tabpanel" aria-label="Hierarchy links panel">
                <ul>
                  <li>SVEM: {timelineSelection.links?.svemId}</li>
                  <li>CCCP: {timelineSelection.links?.cccpId}</li>
                  <li>DCHD: {timelineSelection.links?.dchdId}</li>
                </ul>
                <StoryHierarchyExplorer timelineSelection={timelineSelection} />
              </div>
            ) : null}

            {storyEnginePanelTab === "semantic" ? (
              <div className="story-engine-content" role="tabpanel" aria-label="Semantic operations panel">
                <SemanticOperationsPanel timelineSelection={timelineSelection} />
              </div>
            ) : null}
          </div>
        ) : null}

        <div className="routing-presets">
          <label>
            Preset Name
            <input
              type="text"
              value={presetInput}
              onChange={(event) => setPresetInput(event.target.value)}
              placeholder="post.purple.statistics"
              list="semantic-preset-catalog"
            />
            <datalist id="semantic-preset-catalog">
              {semanticPresets.map((item) => (
                <option key={item.name} value={item.name} />
              ))}
            </datalist>
          </label>
          <button
            type="button"
            className="action-btn"
            onClick={() => applyPresetForRoute(presetInput)}
            disabled={isPresetApplying}
          >
            {isPresetApplying ? "Applying..." : "Apply Preset"}
          </button>
        </div>

        <div className="routing-phase-shortcuts">
          {routePhasePresetShortcuts.map((shortcut) => (
            <button
              key={shortcut.preset}
              type="button"
              className="generated-preset-btn"
              onClick={() => applyPresetForRoute(shortcut.preset)}
              disabled={isPresetApplying}
              title={`Apply ${shortcut.preset}`}
            >
              {shortcut.label}
            </button>
          ))}
        </div>

        <div className="routing-presets">
          <label>
            Bundle Name
            <input
              type="text"
              value={bundleInput}
              onChange={(event) => setBundleInput(event.target.value)}
              placeholder="bundle.foundation.triad"
              list="semantic-bundle-catalog"
            />
            <datalist id="semantic-bundle-catalog">
              {presetBundles.map((item) => (
                <option key={item.name} value={item.name} />
              ))}
            </datalist>
          </label>
          <label>
            Inversion
            <select value={bundleInversionMode} onChange={(event) => setBundleInversionMode(event.target.value)}>
              <option value="none">none</option>
              <option value="executive">executive</option>
            </select>
          </label>
          <label>
            Persist Generated
            <select value={persistGeneratedSlides ? "yes" : "no"} onChange={(event) => setPersistGeneratedSlides(event.target.value === "yes")}>
              <option value="no">preview only</option>
              <option value="yes">save slides</option>
            </select>
          </label>
          <button
            type="button"
            className="action-btn"
            onClick={() => generateBundleForRoute(bundleInput)}
            disabled={isBundleGenerating}
          >
            {isBundleGenerating ? "Generating..." : "Generate Bundle"}
          </button>
        </div>

        {selectedBundle ? (
          <div className="routing-bundle-preview">
            <h3>{selectedBundle.label || selectedBundle.name}</h3>
            <p className="status-line">{selectedBundle.description || "No bundle description provided."}</p>
            <div className="routing-chip-row">
              <span>family: {selectedBundle.family}</span>
              <span>slides: {selectedBundle.slide_count}</span>
              <span>inversion: {selectedBundle.supports_inversion ? "supported" : "none"}</span>
              <span>owner: {selectedBundle.owner?.username || "system"}</span>
              <span>revision: {selectedBundle.current_revision?.revision_number || 0}</span>
              <span>history: {selectedBundle.revision_count || 0}</span>
            </div>
            <div className="routing-chip-row">
              {Object.entries(selectedBundle.phase_distribution || {}).map(([phase, count]) => (
                <span key={`phase-${phase}`}>{phase}:{count}</span>
              ))}
              {Object.entries(selectedBundle.layout_distribution || {}).map(([layout, count]) => (
                <span key={`layout-${layout}`}>{layout}:{count}</span>
              ))}
            </div>

            {selectedBundle.kind === "custom" && (selectedBundle.revision_count || 0) > 1 ? (
              <div className="routing-bundle-compare-panel">
                <h4>Revision Compare + Rollback</h4>
                <div className="routing-presets">
                  <label>
                    From Revision
                    <select value={String(bundleCompareFromRevision)} onChange={(event) => setBundleCompareFromRevision(Number(event.target.value))}>
                      {Array.from({ length: selectedBundle.revision_count || 0 }, (_, index) => index + 1).map((revision) => (
                        <option key={`from-${revision}`} value={String(revision)}>{revision}</option>
                      ))}
                    </select>
                  </label>
                  <label>
                    To Revision
                    <select value={String(bundleCompareToRevision)} onChange={(event) => setBundleCompareToRevision(Number(event.target.value))}>
                      {Array.from({ length: selectedBundle.revision_count || 0 }, (_, index) => index + 1).map((revision) => (
                        <option key={`to-${revision}`} value={String(revision)}>{revision}</option>
                      ))}
                    </select>
                  </label>
                  <button type="button" className="generated-preset-btn" onClick={compareSelectedBundle} disabled={isBundleComparing}>
                    {isBundleComparing ? "Comparing..." : "Compare Revisions"}
                  </button>
                  {selectedBundle.access_role === "owner" || selectedBundle.access_role === "edit" ? (
                    <button type="button" className="generated-preset-btn generated-preset-btn-danger" onClick={rollbackSelectedBundle} disabled={isBundleRollingBack}>
                      {isBundleRollingBack ? "Rolling Back..." : `Rollback To ${bundleCompareFromRevision}`}
                    </button>
                  ) : null}
                </div>

                {bundleCompareResult ? (
                  <div className="routing-bundle-compare-result">
                    <div className="routing-chip-row">
                      <span>label: {bundleCompareResult.changes?.label_changed ? "changed" : "same"}</span>
                      <span>family: {bundleCompareResult.changes?.family_changed ? "changed" : "same"}</span>
                      <span>description: {bundleCompareResult.changes?.description_changed ? "changed" : "same"}</span>
                      <span>sequence: {bundleCompareResult.changes?.sequence_changed ? "changed" : "same"}</span>
                      <span>executive impact: {bundleCompareResult.executive_projection?.changed_count || 0}</span>
                    </div>
                    <ul>
                      <li>
                        <strong>Added</strong>
                        <span>{(bundleCompareResult.sequence?.added || []).join(", ") || "none"}</span>
                      </li>
                      <li>
                        <strong>Removed</strong>
                        <span>{(bundleCompareResult.sequence?.removed || []).join(", ") || "none"}</span>
                      </li>
                      <li>
                        <strong>Reordered</strong>
                        <span>{(bundleCompareResult.sequence?.reordered || []).join(", ") || "none"}</span>
                      </li>
                    </ul>
                  </div>
                ) : null}
              </div>
            ) : null}

            {selectedBundle.kind === "custom" && selectedBundle.access_role === "owner" ? (
              <div className="routing-bundle-share-panel">
                <h4>Share Access</h4>
                <div className="routing-presets">
                  <label>
                    Username
                    <input
                      type="text"
                      value={shareUsernameInput}
                      onChange={(event) => setShareUsernameInput(event.target.value)}
                      placeholder="collaborator_username"
                    />
                  </label>
                  <label>
                    Permission
                    <select value={sharePermissionInput} onChange={(event) => setSharePermissionInput(event.target.value)}>
                      <option value="view">view</option>
                      <option value="edit">edit</option>
                    </select>
                  </label>
                  <label>
                    Status
                    <select value={shareIsActiveInput ? "active" : "inactive"} onChange={(event) => setShareIsActiveInput(event.target.value === "active")}>
                      <option value="active">active</option>
                      <option value="inactive">inactive</option>
                    </select>
                  </label>
                  <button type="button" className="generated-preset-btn" onClick={saveSelectedBundleShare} disabled={isBundleShareSaving}>
                    {isBundleShareSaving ? "Saving..." : "Save Share Grant"}
                  </button>
                </div>

                {isBundleSharesLoading ? <p className="status-line">Loading share grants...</p> : null}
                {!isBundleSharesLoading && bundleShares.length === 0 ? <p className="status-line">No share grants yet.</p> : null}
                {bundleShares.length > 0 ? (
                  <ul className="routing-share-list">
                    {bundleShares.map((share) => (
                      <li key={share.username}>
                        <strong>{share.username}</strong>
                        <span>
                          permission: {share.permission} | status: {share.is_active ? "active" : "inactive"}
                        </span>
                        <div className="routing-sequence-actions">
                          <button
                            type="button"
                            className="generated-preset-btn"
                            onClick={() => {
                              setShareUsernameInput(share.username || "");
                              setSharePermissionInput(share.permission || "view");
                              setShareIsActiveInput(Boolean(share.is_active));
                            }}
                          >
                            Edit Grant
                          </button>
                        </div>
                      </li>
                    ))}
                  </ul>
                ) : null}
              </div>
            ) : null}

            {selectedBundle.kind === "custom" ? (
              <div className="routing-bundle-tag-panel">
                <h4>Revision Tags</h4>
                {(selectedBundle.access_role === "owner" || selectedBundle.access_role === "edit") ? (
                  <div className="routing-presets">
                    <label>
                      Tag Name
                      <input
                        type="text"
                        value={tagNameInput}
                        onChange={(event) => setTagNameInput(event.target.value)}
                        placeholder="stable"
                      />
                    </label>
                    <label>
                      Revision
                      <select value={String(tagRevisionInput)} onChange={(event) => setTagRevisionInput(Number(event.target.value))}>
                        {Array.from({ length: selectedBundle.revision_count || 1 }, (_, index) => index + 1).map((revision) => (
                          <option key={`tag-rev-${revision}`} value={String(revision)}>{revision}</option>
                        ))}
                      </select>
                    </label>
                    <label>
                      Note
                      <input
                        type="text"
                        value={tagNoteInput}
                        onChange={(event) => setTagNoteInput(event.target.value)}
                        placeholder="release checkpoint"
                      />
                    </label>
                    <button type="button" className="generated-preset-btn" onClick={saveSelectedBundleTag} disabled={isBundleTagSaving}>
                      {isBundleTagSaving ? "Saving..." : "Save Tag"}
                    </button>
                  </div>
                ) : null}

                {isBundleTagsLoading ? <p className="status-line">Loading tags...</p> : null}
                {!isBundleTagsLoading && bundleTags.length === 0 ? <p className="status-line">No tags created yet.</p> : null}
                {bundleTags.length > 0 ? (
                  <ul className="routing-tag-list">
                    {bundleTags.map((tag) => (
                      <li key={`${tag.name}-${tag.revision_number}`}>
                        <strong>{tag.name}</strong>
                        <span>
                          rev: {tag.revision_number}{tag.note ? ` | ${tag.note}` : ""}
                        </span>
                        <div className="routing-sequence-actions">
                          <button
                            type="button"
                            className="generated-preset-btn"
                            onClick={() => {
                              applyTagCompareShortcut(selectedBundle.name, tag.revision_number || 1);
                            }}
                          >
                            Jump To Revision
                          </button>
                          {(selectedBundle.access_role === "owner" || selectedBundle.access_role === "edit") ? (
                            <button
                              type="button"
                              className="generated-preset-btn"
                              onClick={() => {
                                setTagNameInput(tag.name || "");
                                setTagRevisionInput(tag.revision_number || 1);
                                setTagNoteInput(tag.note || "");
                              }}
                            >
                              Edit Tag
                            </button>
                          ) : null}
                        </div>
                      </li>
                    ))}
                  </ul>
                ) : null}
              </div>
            ) : null}
          </div>
        ) : null}

        <div className="routing-presets">
          <label>
            Catalog Tag Filter
            <select value={bundleCatalogTagFilter} onChange={(event) => setBundleCatalogTagFilter(event.target.value)}>
              <option value="all">all tags</option>
              {allBundleCatalogTags.map((tagName) => (
                <option key={`catalog-tag-${tagName}`} value={tagName}>{tagName}</option>
              ))}
            </select>
          </label>
        </div>

        <div className="routing-bundle-catalog">
          {filteredBundleCatalog.map((bundle) => (
            <div className="routing-bundle-catalog-item" key={bundle.name}>
              <button
                type="button"
                className={`generated-preset-btn ${bundleInput === bundle.name ? "active" : ""}`}
                onClick={() => setBundleInput(bundle.name)}
                title={bundle.description || bundle.name}
              >
                {bundle.label || bundle.name}
              </button>
              {Array.isArray(bundle?.tags) && bundle.tags.length > 0 ? (
                <div className="routing-tag-shortcuts">
                  {bundle.tags.slice(0, 2).map((tag) => (
                    <button
                      key={`catalog-tag-shortcut-${bundle.name}-${tag.name}`}
                      type="button"
                      className="generated-preset-btn"
                      onClick={() => applyTagCompareShortcut(bundle.name, tag.revision_number || 1)}
                      title={`Compare from tag ${tag.name}`}
                    >
                      cmp:{tag.name}
                    </button>
                  ))}
                </div>
              ) : null}
            </div>
          ))}
          {selectedBundle ? (
            <>
              <button type="button" className="generated-preset-btn" onClick={() => loadBundleIntoEditor(selectedBundle, "edit")}>
                Load Into Editor
              </button>
              <button type="button" className="generated-preset-btn" onClick={() => loadBundleIntoEditor(selectedBundle, "duplicate")}>
                Duplicate To Editor
              </button>
            </>
          ) : null}
        </div>

        <div className="routing-bundle-editor">
          <h3>Custom Bundle Editor</h3>
          <div className="routing-presets">
            <label>
              Bundle Label
              <input type="text" value={bundleDraftName} onChange={(event) => setBundleDraftName(event.target.value)} placeholder="Quarterly Review Arc" />
            </label>
            <label>
              Family
              <input type="text" value={bundleDraftFamily} onChange={(event) => setBundleDraftFamily(event.target.value)} placeholder="executive.custom" />
            </label>
          </div>
          <div className="routing-presets">
            <label>
              Description
              <input type="text" value={bundleDraftDescription} onChange={(event) => setBundleDraftDescription(event.target.value)} placeholder="Short explanation for preview cards" />
            </label>
          </div>
          <div className="routing-presets">
            <label>
              Add Preset Step
              <input type="text" value={bundleDraftStep} onChange={(event) => setBundleDraftStep(event.target.value)} list="semantic-preset-catalog" placeholder="executive.summary" />
            </label>
            <button type="button" className="generated-preset-btn" onClick={addBundleDraftStep}>Add Step</button>
            <button type="button" className="generated-preset-btn" onClick={saveCustomBundle}>Save Custom Bundle</button>
            {bundleInput.startsWith("custom.bundle.") ? (
              <button type="button" className="generated-preset-btn generated-preset-btn-danger" onClick={() => deleteCustomBundle(bundleInput)}>
                Delete Selected Custom
              </button>
            ) : null}
          </div>
          {editingBundleName ? <p className="status-line">Editing saved bundle: {editingBundleName}</p> : null}
          {hasUnsavedBundleChanges ? <p className="routing-dirty-indicator">Unsaved bundle changes</p> : null}
          {bundleDraftSequence.length > 0 ? (
            <ul className="routing-bundle-sequence-editor">
              {bundleDraftSequence.map((step, index) => (
                <li key={`${step}-${index}`}>
                  <strong>{index + 1}. {step}</strong>
                  <div className="routing-sequence-actions">
                    <button type="button" className="generated-preset-btn" onClick={() => moveBundleDraftStep(index, -1)}>Up</button>
                    <button type="button" className="generated-preset-btn" onClick={() => moveBundleDraftStep(index, 1)}>Down</button>
                    <button type="button" className="generated-preset-btn generated-preset-btn-danger" onClick={() => removeBundleDraftStep(index)}>Remove</button>
                  </div>
                </li>
              ))}
            </ul>
          ) : null}
        </div>

        {selectedBundle?.kind === "custom" ? (
          <div className="routing-bundle-timeline-panel">
            <h3>Bundle Version Timeline</h3>
            <p className="status-line">
              Unified revision log with tags, compare shortcuts, rollback targeting, owner metadata, and share metadata.
            </p>

            <div className="routing-presets">
              <label>
                Tag Filter
                <select value={bundleTimelineTagFilter} onChange={(event) => setBundleTimelineTagFilter(event.target.value)}>
                  <option value="all">all tags</option>
                  {bundleTimelineTagOptions.map((tagName) => (
                    <option key={`timeline-filter-tag-${tagName}`} value={tagName}>{tagName}</option>
                  ))}
                </select>
              </label>
              <label>
                Actor Filter
                <select value={bundleTimelineActorFilter} onChange={(event) => setBundleTimelineActorFilter(event.target.value)}>
                  <option value="all">all editors</option>
                  {bundleTimelineActorOptions.map((username) => (
                    <option key={`timeline-filter-actor-${username}`} value={username}>{username}</option>
                  ))}
                </select>
              </label>
              <label>
                Severity Filter
                <select value={bundleTimelineSeverityFilter} onChange={(event) => setBundleTimelineSeverityFilter(event.target.value)}>
                  <option value="all">all severities</option>
                  <option value="high">high ({bundleTimelineSeverityCounts.high})</option>
                  <option value="medium">medium ({bundleTimelineSeverityCounts.medium})</option>
                  <option value="low">low ({bundleTimelineSeverityCounts.low})</option>
                </select>
              </label>
              <button
                type="button"
                className="generated-preset-btn"
                disabled={isTimelineFilterResetDisabled}
                title={timelineFilterResetTitle}
                aria-label={timelineFilterResetTitle}
                onClick={() => {
                  setBundleTimelineTagFilter("all");
                  setBundleTimelineActorFilter("all");
                  setBundleTimelineSeverityFilter("all");
                  setBundleTimelinePage(1);
                }}
              >
                Clear Filters
              </button>
            </div>

            {isBundleTimelineLoading ? <p className="status-line">Loading timeline...</p> : null}
            {!isBundleTimelineLoading && filteredBundleTimelineRows.length === 0 ? <p className="status-line">No timeline entries for current filters.</p> : null}

            {filteredBundleTimelineRows.length > 0 ? (
              <div className="routing-timeline-pagination">
                <span>page {bundleTimelinePage} / {bundleTimelinePageCount}</span>
                <span>{filteredBundleTimelineRows.length} matching rows</span>
                <label>
                  Rows
                  <select value={String(bundleTimelinePageSize)} onChange={(event) => setBundleTimelinePageSize(Number(event.target.value))}>
                    <option value="5">5</option>
                    <option value="8">8</option>
                    <option value="12">12</option>
                  </select>
                </label>
                <button
                  type="button"
                  className="generated-preset-btn"
                  onClick={() => setBundleTimelinePage((current) => Math.max(1, current - 1))}
                  disabled={bundleTimelinePage <= 1}
                >
                  Newer
                </button>
                <button
                  type="button"
                  className="generated-preset-btn"
                  onClick={() => setBundleTimelinePage((current) => Math.min(bundleTimelinePageCount, current + 1))}
                  disabled={bundleTimelinePage >= bundleTimelinePageCount}
                >
                  Older
                </button>
              </div>
            ) : null}

            {paginatedBundleTimelineRows.length > 0 ? (
              <ul className="routing-timeline-list">
                {paginatedBundleTimelineRows.map((entry) => (
                  <li key={`timeline-${entry.revisionNumber}`}>
                    <div className="routing-chip-row">
                      <span>rev {entry.revisionNumber}</span>
                      <span className={`routing-severity-badge routing-severity-${entry.severityLevel}`}>severity: {entry.severityLevel}</span>
                      <span>editor: {entry.createdBy?.username || "unknown"}</span>
                      {entry.createdAt ? <span>{new Date(entry.createdAt).toLocaleString()}</span> : null}
                      {entry.ownerChangedFrom ? <span>owner change: {entry.ownerChangedFrom} → {entry.createdBy?.username || "unknown"}</span> : null}
                      {entry.rollbackToRevision ? <span>rollback point: rev {entry.rollbackToRevision}</span> : null}
                    </div>
                    {entry.delta ? (
                      <div className="routing-chip-row">
                        <span>delta +{entry.delta.added}</span>
                        <span>delta -{entry.delta.removed}</span>
                        <span>reordered: {entry.delta.reordered}</span>
                        <span>label: {entry.delta.labelChanged ? "changed" : "same"}</span>
                        <span>family: {entry.delta.familyChanged ? "changed" : "same"}</span>
                      </div>
                    ) : null}
                    {entry.tags?.length > 0 ? (
                      <div className="routing-chip-row">
                        {entry.tags.map((tag) => (
                          <button
                            key={`timeline-tag-${entry.revisionNumber}-${tag.name}`}
                            type="button"
                            className="generated-preset-btn"
                            onClick={() => {
                              applyTagCompareShortcut(selectedBundle.name, entry.revisionNumber || 1);
                              setTagNameInput(tag.name || "");
                              setTagRevisionInput(entry.revisionNumber || 1);
                              setTagNoteInput(tag.note || "");
                            }}
                          >
                            tag:{tag.name}
                          </button>
                        ))}
                      </div>
                    ) : null}
                    <div className="routing-sequence-actions">
                      <button
                        type="button"
                        className="generated-preset-btn"
                        onClick={() => {
                          setBundleCompareToRevision(entry.revisionNumber || 1);
                          setBundleCompareFromRevision(Math.max(1, entry.previousRevisionNumber || entry.revisionNumber || 1));
                        }}
                      >
                        Compare From Here
                      </button>
                      {(selectedBundle.access_role === "owner" || selectedBundle.access_role === "edit") ? (
                        <button
                          type="button"
                          className="generated-preset-btn generated-preset-btn-danger"
                          onClick={() => {
                            setBundleCompareFromRevision(entry.revisionNumber || 1);
                          }}
                        >
                          Set Rollback Target
                        </button>
                      ) : null}
                    </div>
                  </li>
                ))}
              </ul>
            ) : null}

            <h4>Share Metadata</h4>
            {selectedBundle.access_role !== "owner" ? (
              <p className="status-line">Share metadata is visible to owners only.</p>
            ) : null}
            {selectedBundle.access_role === "owner" && bundleTimelineShareEvents.length === 0 ? (
              <p className="status-line">No share changes captured yet.</p>
            ) : null}
            {selectedBundle.access_role === "owner" && bundleTimelineShareEvents.length > 0 ? (
              <ul className="routing-share-event-list">
                {bundleTimelineShareEvents.map((event) => (
                  <li key={`share-event-${event.username}-${event.updatedAt}`}>
                    <strong>{event.username}</strong>
                    <span>
                      {event.permission} | {event.isActive ? "active" : "inactive"} | {event.updatedAt ? new Date(event.updatedAt).toLocaleString() : "timestamp unavailable"}
                    </span>
                  </li>
                ))}
              </ul>
            ) : null}
          </div>
        ) : null}

        {bundlePreview ? (
          <div className="routing-bundle-preview">
            <h3>{bundlePreview.label || bundlePreview.bundle}</h3>
            <p className="status-line">
              Generated {bundlePreview.generated?.length || 0} slides from source #{bundlePreview.source_slide_id} with inversion {bundlePreview.inversion}
            </p>
            <ul>
              {(bundlePreview.generated || []).map((entry) => (
                <li key={`${entry.sequence}-${entry.slide?.id}`}>
                  <strong>{entry.sequence}. {entry.bundle_preset}</strong>
                  <span>
                    phase: {entry.slide?.phase_resolved} | layout: {entry.slide?.ui?.layout_archetype} | pack: {entry.slide?.ui?.component_pack} | effective: {entry.effective_preset}
                  </span>
                </li>
              ))}
            </ul>
          </div>
        ) : null}

        {isRouteLoading ? (
          <DeterministicGuardedSurface
            tier="novice"
            surface="pipeline-loading"
            shellClassName="det-surface-stable det-surface-stable--novice"
            loading={true}
            loadingTitle="Resolved Route Loading"
            loadingMessage="Deterministic route preview is loading while preserving pipeline surface stability."
          />
        ) : null}
        {routeError ? <p className="routing-error">{routeError}</p> : null}
        {routeSlide ? <RoutingLayoutPreview slide={routeSlide} /> : null}

        <div
          ref={qpcPanelRef}
          className="qpc-panel panel"
          onMouseEnter={() => setIsQpcHotkeysArmed(true)}
          onMouseLeave={() => setIsQpcHotkeysArmed(false)}
          onFocusCapture={() => setIsQpcHotkeysArmed(true)}
          onBlurCapture={(event) => {
            const nextTarget = event.relatedTarget;
            if (!qpcPanelRef.current?.contains(nextTarget)) {
              setIsQpcHotkeysArmed(false);
            }
          }}
        >
          <p className="eyebrow">Composite Blueprint</p>
          <h3>QPC From 4 Relays</h3>
          <p className="status-line">
            QPU(RR,RR,RR,RR): four relay instances using RR(1,4,16,64); aggregate meta-terms across QPU = 256.
          </p>
          <p className="qpc-formula-badge">4 relays × 64 meta-terms = 256 aggregate</p>
          <p className="status-line">aggregate meta-terms across QPC: {qpcAggregateMetaTerms}</p>

          <div className="routing-presets">
            <label>
              QPC Label
              <input type="text" value={qpcLabel} onChange={(event) => setQpcLabel(event.target.value)} />
            </label>
            {qpcRelayNames.map((name, index) => (
              <label key={`qpc-relay-name-${index}`}>
                Relay {index + 1}
                <input
                  type="text"
                  value={name}
                  onChange={(event) => {
                    const next = [...qpcRelayNames];
                    next[index] = event.target.value;
                    setQpcRelayNames(next);
                  }}
                />
              </label>
            ))}
            {qpcRelaySubjects.map((subjectName, index) => (
              <label key={`qpc-relay-subject-${index}`}>
                Relay {index + 1} Subject
                <input
                  type="text"
                  value={subjectName}
                  onChange={(event) => {
                    const next = [...qpcRelaySubjects];
                    next[index] = event.target.value;
                    setQpcRelaySubjects(next);
                  }}
                />
              </label>
            ))}
          </div>

          <div className="routing-sequence-actions">
            {QPC_COUNT_PRESETS.map((preset) => (
              <button
                key={`qpc-all-relays-preset-${preset.label}`}
                type="button"
                className={`generated-preset-btn ${qpcGlobalPresetMatch === preset.label ? "active" : ""}`}
                onClick={() => {
                  setQpcRelayCountProfiles([
                    [...preset.counts],
                    [...preset.counts],
                    [...preset.counts],
                    [...preset.counts],
                  ]);
                  showNotice("success", `Applied ${preset.label} to all relays`);
                }}
              >
                Apply To All: {preset.label}
              </button>
            ))}
          </div>
          <p className={`status-line qpc-profile-badge ${qpcGlobalPresetMatch === "custom" ? "qpc-profile-custom" : "qpc-profile-preset"}`}>
            global profile: {qpcGlobalPresetMatch}
          </p>
          <div className="qpc-profile-legend" aria-label="QPC profile color legend">
            <button
              type="button"
              className={`generated-preset-btn qpc-profile-badge ${qpcProfileFilter === "all" ? "active" : ""}`}
              onClick={() => setQpcProfileFilter("all")}
            >
              all profiles
            </button>
            <button
              type="button"
              className={`generated-preset-btn qpc-profile-badge qpc-profile-preset ${qpcProfileFilter === "preset" ? "active" : ""}`}
              onClick={() => setQpcProfileFilter((current) => (current === "preset" ? "all" : "preset"))}
            >
              preset profile
            </button>
            <button
              type="button"
              className={`generated-preset-btn qpc-profile-badge qpc-profile-custom ${qpcProfileFilter === "custom" ? "active" : ""}`}
              onClick={() => setQpcProfileFilter((current) => (current === "custom" ? "all" : "custom"))}
            >
              custom profile
            </button>
          </div>
          <p className="status-line qpc-key-hint">
            shortcuts: A = all, P = preset, C = custom
            <span className={`qpc-hotkeys-state ${isQpcHotkeysArmed ? "active" : "inactive"}`}>
              hotkeys {isQpcHotkeysArmed ? "active" : "inactive"}
            </span>
          </p>
          <p className="status-line">legend filter: {qpcProfileFilter}</p>
          <div className="qpc-compare-controls" aria-label="QPC compare controls">
            <label className="qpc-compare-toggle">
              <input
                type="checkbox"
                checked={qpcCompareEnabled}
                onChange={(event) => {
                  const next = Boolean(event.target.checked);
                  setQpcCompareEnabled(next);
                  if (!next) {
                    setQpcCompareMode(false);
                    setQpcCompareSelection([]);
                  }
                }}
              />
              compare enabled
            </label>
            <button
              type="button"
              className={`generated-preset-btn ${qpcCompareMode ? "active" : ""}`}
              disabled={!qpcCompareAllowed}
              title={!qpcCompareAllowed ? "Approve at least two relays to enable compare mode" : "Toggle compare mode"}
              onClick={() => {
                setQpcCompareMode((current) => !current);
                setQpcCompareSelection([]);
              }}
            >
              compare mode
            </button>
            <button
              type="button"
              className="generated-preset-btn"
              disabled={qpcCompareSelection.length === 0}
              onClick={() => setQpcCompareSelection([])}
            >
              clear compare targets
            </button>
          </div>
          <p className="status-line">compare approvals: {qpcApprovedRelayCount} of {qpcRelays.length} relays</p>
          {qpcCompareMode ? (
            <p className="status-line qpc-compare-mode-note">
              compare mode active: click approved relays to select up to two targets
            </p>
          ) : null}

          <div className="routing-presets">
            {qpcRelayCountProfiles.map((counts, relayIndex) => (
              <label key={`qpc-relay-counts-${relayIndex}`}>
                Relay {relayIndex + 1} Counts (L1/L2/L3)
                <span className={`status-line qpc-profile-badge ${qpcRelayPresetMatches[relayIndex] === "custom" ? "qpc-profile-custom" : "qpc-profile-preset"}`}>
                  profile: {qpcRelayPresetMatches[relayIndex]}
                </span>
                <div className="qpc-compare-toggle qpc-compare-approval">
                  <input
                    type="checkbox"
                    checked={Boolean(qpcRelayCompareApproved[relayIndex])}
                    onChange={(event) => {
                      const nextApprovals = [...qpcRelayCompareApproved];
                      nextApprovals[relayIndex] = Boolean(event.target.checked);
                      setQpcRelayCompareApproved(nextApprovals);
                    }}
                  />
                  <span>approved for compare</span>
                </div>
                <div className="routing-sequence-actions">
                  {[0, 1, 2].map((countIndex) => (
                    <input
                      key={`qpc-relay-${relayIndex}-count-${countIndex}`}
                      type="number"
                      min="0"
                      max="256"
                      value={String(counts[countIndex] ?? 0)}
                      onChange={(event) => {
                        const nextProfiles = qpcRelayCountProfiles.map((profile) => [...profile]);
                        nextProfiles[relayIndex][countIndex] = Number(event.target.value || 0);
                        setQpcRelayCountProfiles(nextProfiles);
                      }}
                    />
                  ))}
                </div>
                <div className="routing-sequence-actions">
                  {QPC_COUNT_PRESETS.map((preset) => (
                    <button
                      key={`qpc-relay-${relayIndex}-preset-${preset.label}`}
                      type="button"
                      className="generated-preset-btn"
                      onClick={() => {
                        const nextProfiles = qpcRelayCountProfiles.map((profile) => [...profile]);
                        nextProfiles[relayIndex] = [...preset.counts];
                        setQpcRelayCountProfiles(nextProfiles);
                      }}
                    >
                      {preset.label}
                    </button>
                  ))}
                </div>
              </label>
            ))}
          </div>

          <QpcBlueprint
            qpcLabel={qpcLabel}
            processorLabel={relayProcessorLabel}
            relays={qpcRelays}
            profileFilter={qpcProfileFilter}
            compareMode={qpcCompareMode}
            compareSelection={qpcCompareSelection}
            selectedRelayId={qpcSelectedRelay?.id || null}
            onRelaySelected={loadQpcRelayIntoBlueprint}
          />

          {qpcCompareSummary ? (
            <div className="qpc-compare-panel" role="status" aria-live="polite">
              <h4>Relay Compare</h4>
              <p>
                {qpcCompareSummary.left.name} vs {qpcCompareSummary.right.name}
              </p>
              <div className="qpc-compare-grid">
                <span>subject</span>
                <span>{qpcCompareSummary.left.subject}</span>
                <span>{qpcCompareSummary.right.subject}</span>

                <span>profile</span>
                <span>{qpcCompareSummary.left.profileLabel}</span>
                <span>{qpcCompareSummary.right.profileLabel}</span>

                <span>L1 delta</span>
                <span>{qpcCompareSummary.left.counts[0]}</span>
                <span>{qpcCompareSummary.deltas[0] >= 0 ? `+${qpcCompareSummary.deltas[0]}` : qpcCompareSummary.deltas[0]}</span>

                <span>L2 delta</span>
                <span>{qpcCompareSummary.left.counts[1]}</span>
                <span>{qpcCompareSummary.deltas[1] >= 0 ? `+${qpcCompareSummary.deltas[1]}` : qpcCompareSummary.deltas[1]}</span>

                <span>L3 delta</span>
                <span>{qpcCompareSummary.left.counts[2]}</span>
                <span>{qpcCompareSummary.deltas[2] >= 0 ? `+${qpcCompareSummary.deltas[2]}` : qpcCompareSummary.deltas[2]}</span>
              </div>
              <p className="status-line">
                changed levels: {qpcCompareSummary.changedLevels} | subject changed: {qpcCompareSummary.subjectChanged ? "yes" : "no"} | profile changed: {qpcCompareSummary.profileChanged ? "yes" : "no"}
              </p>
            </div>
          ) : null}

          {qpcSelectedRelay ? (
            <p className="status-line">
              selected relay: {qpcSelectedRelay.name} | counts: 1 / {qpcSelectedRelay.counts?.[0] ?? 0} / {qpcSelectedRelay.counts?.[1] ?? 0} / {qpcSelectedRelay.counts?.[2] ?? 0}
            </p>
          ) : null}
        </div>
      </section>
    </main>
  );
}
