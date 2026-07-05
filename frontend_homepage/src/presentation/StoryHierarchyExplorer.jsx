import { useCallback, useEffect, useMemo, useState } from "react";

import {
  btpeApproveGeneratedTier,
  btpeGenerateCccp,
  btpeGenerateDchd,
  btpeGenerateSvem,
  btpeGenerateTier,
  btpeGetExpansionStatus,
  btpeGetHierarchyTree,
  btpeGetStoryScaffolds,
  btpeUpsertStoryScaffold,
  fetchStorytellingStories,
  saveStorytellingEntry,
} from "../api/homepageApi";

function normalizeMlasColorToken(token) {
  const map = {
    "green-lime": "GREEN_LIME",
  };
  const normalized = String(token || "").toLowerCase();
  return map[normalized] || normalized.toUpperCase();
}

function storageKeyFor(selection) {
  return `btpe_hierarchy_state_${selection?.latticeIndex || "default"}`;
}

function getNodeKey(node) {
  if (!node) {
    return "root";
  }
  return node.type === "root" ? "root" : `${node.type}:${node.id}`;
}

function buildDefaultScaffold(node, path, timelineSelection) {
  const nodeTitle = node?.title || "Untitled node";
  const phase = timelineSelection?.timelineLabel || "Story";
  const intent = timelineSelection?.semanticIntentId || "intent";
  const route = Array.isArray(path) ? path.join(" -> ") : "12-Grid -> MLAS";

  const dchdAtoms = [];
  const metadata = node?.metadata || {};
  if (Array.isArray(metadata?.dchd_subcells)) {
    metadata.dchd_subcells.forEach((subcell) => {
      dchdAtoms.push(`S${subcell?.subcell_number || "?"}: ${subcell?.seed_input || "seed"}`);
    });
  } else if (typeof metadata?.subcell_number === "number") {
    dchdAtoms.push(`S${metadata.subcell_number}: ${metadata?.seed_input || "seed"}`);
  }

  if (!dchdAtoms.length) {
    dchdAtoms.push(`${nodeTitle} atom: ${metadata?.seed_input || "core seed"}`);
  }

  return {
    talkingPoints: [
      `${phase} hook anchored in ${nodeTitle}`,
      `Conflict signal derived from ${intent}`,
      `Reader promise mapped to route ${route}`,
      `Escalation cue based on semantic tier depth`,
    ].join("\n"),
    coreConcept: `${nodeTitle} transforms ${phase.toLowerCase()} pressure into decisive narrative movement through ${intent}.`,
    synopsis: `In ${phase}, the story follows ${nodeTitle} through the semantic route ${route}. The narrative pressure emerges from deterministic hierarchy signals and resolves through layered intent handoffs. Each movement reframes the same seed across tier depth, letting meaning evolve without losing structural coherence.`,
    chapterStructure: [
      `Act I: Entry through ${path?.[0] || "12-Grid"}`,
      `Act II: Expansion across ${path?.slice(1).join(" / ") || "MLAS"}`,
      `Act III: Compression into decisive semantic outcome`,
      `Act IV: Reflection and forward branch setup`,
    ].join("\n"),
    dchdAtoms,
    scaffoldVersion: 1,
    scaffoldStatus: "draft",
    updatedAt: new Date().toISOString(),
  };
}

function buildScaffoldFromApi(apiScaffold) {
  return {
    talkingPoints: apiScaffold?.talking_points || "",
    coreConcept: apiScaffold?.core_concept || "",
    synopsis: apiScaffold?.synopsis || "",
    chapterStructure: apiScaffold?.chapter_structure || "",
    dchdAtoms: Array.isArray(apiScaffold?.dchd_atoms) ? apiScaffold.dchd_atoms : [],
    scaffoldVersion: Number(apiScaffold?.scaffold_version || 1),
    scaffoldStatus: apiScaffold?.decision || "draft",
    updatedAt: apiScaffold?.updated_at || new Date().toISOString(),
  };
}

function parseTalkingPoints(text) {
  return String(text || "")
    .split("\n")
    .map((line) => line.trim())
    .filter(Boolean)
    .map((line) => line.replace(/^[-*]\s*/, ""));
}

function parseChapterStructure(text) {
  const lines = String(text || "")
    .split("\n")
    .map((line) => line.trim())
    .filter(Boolean);

  return lines.map((line, index) => {
    const parts = line.split(":");
    if (parts.length > 1) {
      return {
        number: index + 1,
        title: parts[0].trim(),
        description: parts.slice(1).join(":").trim() || "Generated chapter detail",
      };
    }
    return {
      number: index + 1,
      title: `Chapter ${index + 1}`,
      description: line,
    };
  });
}

export default function StoryHierarchyExplorer({ timelineSelection }) {
  const [rootTierId, setRootTierId] = useState(null);
  const [rootRationale, setRootRationale] = useState("");
  const [tree, setTree] = useState(null);
  const [status, setStatus] = useState(null);
  const [expandedNodes, setExpandedNodes] = useState({ root: true });
  const [selectedNodeKey, setSelectedNodeKey] = useState("root");
  const [activeNodeTab, setActiveNodeTab] = useState("metadata");
  const [decisionByNode, setDecisionByNode] = useState({});
  const [scaffoldByNode, setScaffoldByNode] = useState({});
  const [scaffoldDecisionByNode, setScaffoldDecisionByNode] = useState({});
  const [storyEntries, setStoryEntries] = useState([]);
  const [targetStoryEntryId, setTargetStoryEntryId] = useState(8);
  const [syncStoryTitle, setSyncStoryTitle] = useState(false);
  const [isExportingToStory, setIsExportingToStory] = useState(false);
  const [storyExportStatus, setStoryExportStatus] = useState("");
  const [lastExportEntryId, setLastExportEntryId] = useState(null);
  const [isSavingScaffold, setIsSavingScaffold] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");

  const persistState = useCallback((partial) => {
    if (!timelineSelection) {
      return;
    }
    const key = storageKeyFor(timelineSelection);
    const next = {
      rootTierId,
      expandedNodes,
      selectedNodeKey,
      activeNodeTab,
      decisionByNode,
      scaffoldByNode,
      scaffoldDecisionByNode,
      ...partial,
    };
    window.localStorage.setItem(key, JSON.stringify(next));
  }, [activeNodeTab, decisionByNode, expandedNodes, rootTierId, scaffoldByNode, scaffoldDecisionByNode, selectedNodeKey, timelineSelection]);

  const refreshHierarchy = useCallback(async (rootId) => {
    const [treePayload, statusPayload] = await Promise.all([
      btpeGetHierarchyTree(rootId),
      btpeGetExpansionStatus(rootId),
    ]);
    setTree(treePayload?.tree || null);
    setStatus(statusPayload?.status || null);
  }, []);

  const ensureExpandedHierarchy = useCallback(async (rootId) => {
    let treePayload = await btpeGetHierarchyTree(rootId);
    let treeData = treePayload?.tree || null;

    if (!treeData?.svem_branches?.length) {
      await btpeGenerateSvem(rootId);
      treePayload = await btpeGetHierarchyTree(rootId);
      treeData = treePayload?.tree || null;
    }

    const svemBranches = Array.isArray(treeData?.svem_branches) ? treeData.svem_branches : [];
    for (const svem of svemBranches) {
      if (!Array.isArray(svem?.cccp_compartments) || svem.cccp_compartments.length === 0) {
        await btpeGenerateCccp(svem.id);
      }
    }

    treePayload = await btpeGetHierarchyTree(rootId);
    treeData = treePayload?.tree || null;

    const svemAfterCccp = Array.isArray(treeData?.svem_branches) ? treeData.svem_branches : [];
    for (const svem of svemAfterCccp) {
      for (const cccp of svem.cccp_compartments || []) {
        if (!Array.isArray(cccp?.dchd_subcells) || cccp.dchd_subcells.length === 0) {
          await btpeGenerateDchd(cccp.id);
        }
      }
    }

    await refreshHierarchy(rootId);
  }, [refreshHierarchy]);

  const loadScaffoldsFromBackend = useCallback(async (rootId) => {
    const payload = await btpeGetStoryScaffolds(rootId);
    const byNode = {};
    const decisionByNodeMap = {};

    for (const scaffold of payload?.results || []) {
      if (!scaffold?.node_key) {
        continue;
      }
      byNode[scaffold.node_key] = buildScaffoldFromApi(scaffold);
      decisionByNodeMap[scaffold.node_key] = scaffold?.decision || "draft";
    }

    return { byNode, decisionByNodeMap };
  }, []);

  const bootstrap = useCallback(async () => {
    if (!timelineSelection) {
      return;
    }

    setIsLoading(true);
    setError("");

    try {
      const key = storageKeyFor(timelineSelection);
      const persistedRaw = window.localStorage.getItem(key);
      const persisted = persistedRaw ? JSON.parse(persistedRaw) : null;

      const payload = {
        seed_input: `${timelineSelection.timelineLabel} ${timelineSelection.mlasSubject} lattice ${timelineSelection.latticeIndex}`,
        mlas_color: normalizeMlasColorToken(timelineSelection.mlasColorToken),
        industry: "SYSTEMS",
        tier_level: 1,
      };

      const generated = await btpeGenerateTier(payload);
      const nextRootId = Number(generated?.tier_id || persisted?.rootTierId || 0);

      if (!nextRootId) {
        throw new Error("Tier generated without root id. Ensure TierDefinition rows exist for this MLAS color.");
      }

      setRootTierId(nextRootId);
      setRootRationale(String(generated?.rationale || ""));

      const restoredExpandedNodes = persisted?.expandedNodes || { root: true };
      const restoredSelectedNode = persisted?.selectedNodeKey || "root";
      const restoredActiveNodeTab = persisted?.activeNodeTab || "metadata";
      const restoredDecisions = persisted?.decisionByNode || {};
      const restoredScaffoldByNode = persisted?.scaffoldByNode || {};
      const restoredScaffoldDecisions = persisted?.scaffoldDecisionByNode || {};

      setExpandedNodes(restoredExpandedNodes);
      setSelectedNodeKey(restoredSelectedNode);
      setActiveNodeTab(restoredActiveNodeTab);
      setDecisionByNode(restoredDecisions);

      await ensureExpandedHierarchy(nextRootId);

      const serverScaffolds = await loadScaffoldsFromBackend(nextRootId);
      const mergedScaffolds = {
        ...serverScaffolds.byNode,
        ...restoredScaffoldByNode,
      };
      const mergedScaffoldDecisions = {
        ...serverScaffolds.decisionByNodeMap,
        ...restoredScaffoldDecisions,
      };

      setScaffoldByNode(mergedScaffolds);
      setScaffoldDecisionByNode(mergedScaffoldDecisions);

      persistState({
        rootTierId: nextRootId,
        expandedNodes: restoredExpandedNodes,
        selectedNodeKey: restoredSelectedNode,
        activeNodeTab: restoredActiveNodeTab,
        decisionByNode: restoredDecisions,
        scaffoldByNode: mergedScaffolds,
        scaffoldDecisionByNode: mergedScaffoldDecisions,
      });
    } catch (err) {
      setError(err.message || "Could not initialize hierarchy explorer");
      setTree(null);
      setStatus(null);
    } finally {
      setIsLoading(false);
    }
  }, [ensureExpandedHierarchy, loadScaffoldsFromBackend, persistState, timelineSelection]);

  useEffect(() => {
    bootstrap();
  }, [bootstrap]);

  useEffect(() => {
    let active = true;
    const loadStoryEntries = async () => {
      try {
        const payload = await fetchStorytellingStories();
        if (!active) {
          return;
        }
        const stories = Array.isArray(payload?.stories) ? payload.stories : [];
        setStoryEntries(stories);
        if (!stories.length) {
          return;
        }

        setTargetStoryEntryId((current) => {
          const desired = Number(timelineSelection?.latticeIndex || 8);
          const hasDesired = stories.some((story) => Number(story.entry_id) === desired);
          if (hasDesired) {
            return desired;
          }
          const hasCurrent = stories.some((story) => Number(story.entry_id) === Number(current));
          return hasCurrent ? current : Number(stories[0].entry_id);
        });
      } catch (_err) {
        if (active) {
          setStoryEntries([]);
        }
      }
    };

    loadStoryEntries();
    return () => {
      active = false;
    };
  }, [timelineSelection]);

  useEffect(() => {
    persistState({});
  }, [activeNodeTab, decisionByNode, expandedNodes, persistState, rootTierId, scaffoldByNode, scaffoldDecisionByNode, selectedNodeKey]);

  const selectedNodePath = useMemo(() => {
    if (!tree) {
      return ["12-Grid", "MLAS"];
    }

    const base = ["12-Grid", "MLAS"];
    if (selectedNodeKey === "root") {
      return base;
    }

    const [type, idText] = String(selectedNodeKey || "").split(":");
    const id = Number(idText || 0);
    if (!id) {
      return base;
    }

    for (const svem of tree.svem_branches || []) {
      if (type === "svem" && svem.id === id) {
        return [...base, `SVEM B${svem.branch_number}`];
      }
      for (const cccp of svem.cccp_compartments || []) {
        if (type === "cccp" && cccp.id === id) {
          return [...base, `SVEM B${svem.branch_number}`, `CCCP C${cccp.compartment_number}`];
        }
        for (const dchd of cccp.dchd_subcells || []) {
          if (type === "dchd" && dchd.id === id) {
            return [...base, `SVEM B${svem.branch_number}`, `CCCP C${cccp.compartment_number}`, `DCHD S${dchd.subcell_number}`];
          }
        }
      }
    }

    return base;
  }, [selectedNodeKey, tree]);

  const selectedNode = useMemo(() => {
    if (!tree || selectedNodeKey === "root") {
      return tree?.root_tier
        ? {
            type: "root",
            id: tree.root_tier.id,
            title: tree.root_tier.seed_input,
            metadata: tree.root_tier,
            rationale: rootRationale || "Root tier rationale not available.",
          }
        : null;
    }

    const [type, idText] = String(selectedNodeKey || "").split(":");
    const id = Number(idText || 0);

    for (const svem of tree.svem_branches || []) {
      if (type === "svem" && svem.id === id) {
        return {
          type,
          id,
          title: `SVEM Branch ${svem.branch_number}`,
          metadata: svem,
          rationale: `Generated from root tier ${tree.root_tier.id} using branch specialization.`,
        };
      }
      for (const cccp of svem.cccp_compartments || []) {
        if (type === "cccp" && cccp.id === id) {
          return {
            type,
            id,
            title: `CCCP Compartment ${cccp.compartment_number}`,
            metadata: cccp,
            rationale: `Generated from SVEM branch ${svem.branch_number} for compartment specialization.`,
          };
        }
        for (const dchd of cccp.dchd_subcells || []) {
          if (type === "dchd" && dchd.id === id) {
            return {
              type,
              id,
              title: `DCHD Subcell ${dchd.subcell_number}`,
              metadata: dchd,
              rationale: `Generated from CCCP compartment ${cccp.compartment_number}.`,
            };
          }
        }
      }
    }

    return null;
  }, [rootRationale, selectedNodeKey, tree]);

  const toggleExpanded = useCallback((key) => {
    setExpandedNodes((current) => ({ ...current, [key]: !current[key] }));
  }, []);

  const setNodeDecision = useCallback((nodeKey, value) => {
    setDecisionByNode((current) => ({ ...current, [nodeKey]: value }));
  }, []);

  const regenerateSelectedNode = useCallback(async () => {
    if (!selectedNode || !rootTierId) {
      return;
    }
    setIsLoading(true);
    setError("");
    try {
      if (selectedNode.type === "root") {
        await btpeGenerateSvem(rootTierId);
      } else if (selectedNode.type === "svem") {
        await btpeGenerateCccp(selectedNode.id);
      } else if (selectedNode.type === "cccp") {
        await btpeGenerateDchd(selectedNode.id);
      }
      await refreshHierarchy(rootTierId);
    } catch (err) {
      setError(err.message || "Regeneration failed");
    } finally {
      setIsLoading(false);
    }
  }, [refreshHierarchy, rootTierId, selectedNode]);

  const approveSelectedNode = useCallback(async () => {
    if (!selectedNode) {
      return;
    }
    const nodeKey = selectedNode.type === "root" ? "root" : `${selectedNode.type}:${selectedNode.id}`;

    if (selectedNode.type === "root" && rootTierId) {
      try {
        await btpeApproveGeneratedTier(rootTierId);
      } catch (err) {
        setError(err.message || "Approval failed");
      }
    }

    setNodeDecision(nodeKey, "approved");
  }, [rootTierId, selectedNode, setNodeDecision]);

  const rejectSelectedNode = useCallback(() => {
    if (!selectedNode) {
      return;
    }
    const nodeKey = selectedNode.type === "root" ? "root" : `${selectedNode.type}:${selectedNode.id}`;
    setNodeDecision(nodeKey, "rejected");
  }, [selectedNode, setNodeDecision]);

  useEffect(() => {
    if (!selectedNode) {
      return;
    }
    const key = getNodeKey(selectedNode);
    setScaffoldByNode((current) => {
      if (current[key]) {
        return current;
      }
      return {
        ...current,
        [key]: buildDefaultScaffold(selectedNode, selectedNodePath, timelineSelection),
      };
    });
  }, [selectedNode, selectedNodePath, timelineSelection]);

  const selectedScaffold = selectedNode ? scaffoldByNode[getNodeKey(selectedNode)] || null : null;

  const updateScaffoldField = useCallback((field, value) => {
    if (!selectedNode) {
      return;
    }
    const key = getNodeKey(selectedNode);
    setScaffoldByNode((current) => {
      const existing = current[key] || buildDefaultScaffold(selectedNode, selectedNodePath, timelineSelection);
      return {
        ...current,
        [key]: {
          ...existing,
          [field]: value,
          updatedAt: new Date().toISOString(),
        },
      };
    });
  }, [selectedNode, selectedNodePath, timelineSelection]);

  const regenerateScaffoldSection = useCallback((field) => {
    if (!selectedNode) {
      return;
    }
    const key = getNodeKey(selectedNode);
    const fresh = buildDefaultScaffold(selectedNode, selectedNodePath, timelineSelection);
    setScaffoldByNode((current) => {
      const existing = current[key] || fresh;
      return {
        ...current,
        [key]: {
          ...existing,
          [field]: fresh[field],
          updatedAt: new Date().toISOString(),
        },
      };
    });
  }, [selectedNode, selectedNodePath, timelineSelection]);

  const saveSelectedScaffold = useCallback(async () => {
    if (!selectedNode || !rootTierId) {
      return;
    }

    const key = getNodeKey(selectedNode);
    const scaffold = scaffoldByNode[key] || buildDefaultScaffold(selectedNode, selectedNodePath, timelineSelection);
    const decision = scaffoldDecisionByNode[key] || scaffold.scaffoldStatus || "draft";

    setIsSavingScaffold(true);
    setError("");
    try {
      const result = await btpeUpsertStoryScaffold({
        root_tier_id: rootTierId,
        node_key: key,
        node_type: selectedNode.type || "root",
        node_id: selectedNode.id,
        timeline_lattice_index: timelineSelection?.latticeIndex || null,
        timeline_label: timelineSelection?.timelineLabel || "",
        semantic_intent_id: timelineSelection?.semanticIntentId || "",
        talking_points: scaffold.talkingPoints || "",
        core_concept: scaffold.coreConcept || "",
        synopsis: scaffold.synopsis || "",
        chapter_structure: scaffold.chapterStructure || "",
        dchd_atoms: Array.isArray(scaffold.dchdAtoms) ? scaffold.dchdAtoms : [],
        decision,
      });

      const savedDecision = result?.scaffold?.decision || decision;
      setScaffoldDecisionByNode((current) => ({ ...current, [key]: savedDecision }));
      setScaffoldByNode((current) => ({
        ...current,
        [key]: {
          ...(current[key] || scaffold),
          scaffoldVersion: Number(result?.scaffold?.scaffold_version || (current[key]?.scaffoldVersion || 1)),
          scaffoldStatus: savedDecision,
          updatedAt: result?.scaffold?.updated_at || new Date().toISOString(),
        },
      }));
    } catch (err) {
      setError(err.message || "Could not save scaffold");
    } finally {
      setIsSavingScaffold(false);
    }
  }, [rootTierId, scaffoldByNode, scaffoldDecisionByNode, selectedNode, selectedNodePath, timelineSelection]);

  const approveScaffoldAndSave = useCallback(async () => {
    if (!selectedNode) {
      return;
    }
    const key = getNodeKey(selectedNode);
    setScaffoldDecisionByNode((current) => ({ ...current, [key]: "approved" }));
    await saveSelectedScaffold();
  }, [saveSelectedScaffold, selectedNode]);

  const rejectScaffoldAndSave = useCallback(async () => {
    if (!selectedNode) {
      return;
    }
    const key = getNodeKey(selectedNode);
    setScaffoldDecisionByNode((current) => ({ ...current, [key]: "rejected" }));
    await saveSelectedScaffold();
  }, [saveSelectedScaffold, selectedNode]);

  const exportScaffoldToStoryEntry = useCallback(async () => {
    if (!selectedNode) {
      return;
    }

    const entryId = Number(targetStoryEntryId || 0);
    if (!entryId) {
      setError("Select a target story entry before export");
      return;
    }

    const key = getNodeKey(selectedNode);
    const scaffold = scaffoldByNode[key] || buildDefaultScaffold(selectedNode, selectedNodePath, timelineSelection);
    const talkingPoints = parseTalkingPoints(scaffold.talkingPoints);
    const chapters = parseChapterStructure(scaffold.chapterStructure);
    const exportTimestamp = new Date().toISOString();
    const semanticMetadataLines = [
      `- MLAS color: ${timelineSelection?.mlasColorToken || "unknown"}`,
      `- Timeline cell: ${timelineSelection?.latticeIndex || "unknown"} (${timelineSelection?.timelineLabel || "unlabeled"})`,
      `- Semantic path: ${selectedNodePath.join(" -> ")}`,
      `- Hierarchy node key: ${key}`,
      `- DCHD atom summary: ${(Array.isArray(scaffold.dchdAtoms) && scaffold.dchdAtoms.length) ? scaffold.dchdAtoms.join(" | ") : "none"}`,
    ].join("\n");
    const versionMetadataLines = [
      `- Scaffold version: ${Number(scaffold?.scaffoldVersion || 1)}`,
      `- Export timestamp: ${exportTimestamp}`,
      `- Node key: ${key}`,
      `- Root tier id: ${rootTierId || "unknown"}`,
    ].join("\n");

    setIsExportingToStory(true);
    setStoryExportStatus("");
    setError("");
    try {
      const payload = {
        talking_points: talkingPoints,
        core_concept: scaffold.coreConcept || "",
        synopsis: scaffold.synopsis || "",
        chapters,
        dynamic_navigation: `BTPE Route: ${selectedNodePath.join(" -> ")}`,
        semantic_metadata: semanticMetadataLines,
        version_metadata: versionMetadataLines,
        status: "in_progress",
      };

      if (syncStoryTitle) {
        payload.title = selectedNode.title || `BTPE Entry ${entryId}`;
      }

      await saveStorytellingEntry(entryId, payload);
      setLastExportEntryId(entryId);
      setStoryExportStatus(`Exported scaffold to story entry ${entryId} at ${new Date(exportTimestamp).toLocaleTimeString()}`);
    } catch (err) {
      setError(err.message || "Could not export scaffold to story entry");
    } finally {
      setIsExportingToStory(false);
    }
  }, [rootTierId, scaffoldByNode, selectedNode, selectedNodePath, syncStoryTitle, targetStoryEntryId, timelineSelection]);

  return (
    <section className="story-hierarchy-explorer" aria-label="BTPE hierarchy explorer">
      <p className="status-line story-hierarchy-breadcrumb">{selectedNodePath.join(" -> ")}</p>

      {status ? (
        <div className="story-hierarchy-summary">
          <span>SVEM: {status.svem_generated}/{status.svem_count}</span>
          <span>CCCP: {status.cccp_generated}/{status.cccp_count}</span>
          <span>DCHD: {status.dchd_generated}/{status.dchd_count}</span>
        </div>
      ) : null}

      {isLoading ? <p className="status-line">Loading hierarchy...</p> : null}
      {error ? <p className="routing-error">{error}</p> : null}

      {tree ? (
        <div className="story-hierarchy-layout">
          <div className="story-hierarchy-tree">
            <button type="button" className="story-node story-node-root" onClick={() => setSelectedNodeKey("root")}>
              MLAS Root #{tree.root_tier.id}
            </button>

            {(tree.svem_branches || []).map((svem) => {
              const svemKey = `svem:${svem.id}`;
              const isSvemOpen = Boolean(expandedNodes[svemKey]);
              return (
                <div key={svem.id} className="story-node-group">
                  <div className="story-node-row">
                    <button type="button" className="story-node story-node-svem" onClick={() => setSelectedNodeKey(svemKey)}>
                      SVEM B{svem.branch_number}
                    </button>
                    <button type="button" className="story-node-toggle" onClick={() => toggleExpanded(svemKey)}>
                      {isSvemOpen ? "Collapse" : "Expand"}
                    </button>
                  </div>

                  {isSvemOpen ? (
                    <div className="story-node-children">
                      {(svem.cccp_compartments || []).map((cccp) => {
                        const cccpKey = `cccp:${cccp.id}`;
                        const isCccpOpen = Boolean(expandedNodes[cccpKey]);
                        return (
                          <div key={cccp.id} className="story-node-group">
                            <div className="story-node-row">
                              <button type="button" className="story-node story-node-cccp" onClick={() => setSelectedNodeKey(cccpKey)}>
                                CCCP C{cccp.compartment_number}
                              </button>
                              <button type="button" className="story-node-toggle" onClick={() => toggleExpanded(cccpKey)}>
                                {isCccpOpen ? "Collapse" : "Expand"}
                              </button>
                            </div>
                            {isCccpOpen ? (
                              <div className="story-node-children">
                                {(cccp.dchd_subcells || []).map((dchd) => {
                                  const dchdKey = `dchd:${dchd.id}`;
                                  return (
                                    <button
                                      key={dchd.id}
                                      type="button"
                                      className="story-node story-node-dchd"
                                      onClick={() => setSelectedNodeKey(dchdKey)}
                                    >
                                      DCHD S{dchd.subcell_number}
                                    </button>
                                  );
                                })}
                              </div>
                            ) : null}
                          </div>
                        );
                      })}
                    </div>
                  ) : null}
                </div>
              );
            })}
          </div>

          <div className="story-hierarchy-inspector">
            <div className="story-node-actions action-grid">
              <button type="button" onClick={regenerateSelectedNode} disabled={isLoading || !selectedNode}>
                Regenerate
              </button>
              <button type="button" onClick={approveSelectedNode} disabled={!selectedNode}>
                Approve
              </button>
              <button type="button" onClick={rejectSelectedNode} disabled={!selectedNode}>
                Reject
              </button>
            </div>

            {selectedNode ? (
              <>
                <h4>{selectedNode.title}</h4>
                <p className="status-line">
                  Decision: {decisionByNode[selectedNode.type === "root" ? "root" : `${selectedNode.type}:${selectedNode.id}`] || "pending"}
                </p>

                <div className="story-node-inspector-tabs" role="tablist" aria-label="Node inspector tabs">
                  <button
                    type="button"
                    role="tab"
                    aria-selected={activeNodeTab === "metadata"}
                    className={`story-engine-tab${activeNodeTab === "metadata" ? " is-active" : ""}`}
                    onClick={() => setActiveNodeTab("metadata")}
                  >
                    Metadata
                  </button>
                  <button
                    type="button"
                    role="tab"
                    aria-selected={activeNodeTab === "rationale"}
                    className={`story-engine-tab${activeNodeTab === "rationale" ? " is-active" : ""}`}
                    onClick={() => setActiveNodeTab("rationale")}
                  >
                    Rationale
                  </button>
                  <button
                    type="button"
                    role="tab"
                    aria-selected={activeNodeTab === "scaffold"}
                    className={`story-engine-tab${activeNodeTab === "scaffold" ? " is-active" : ""}`}
                    onClick={() => setActiveNodeTab("scaffold")}
                  >
                    Scaffolding
                  </button>
                </div>

                {activeNodeTab === "metadata" ? (
                  <pre className="story-node-metadata" aria-label="Node metadata">
                    {JSON.stringify(selectedNode.metadata, null, 2)}
                  </pre>
                ) : null}

                {activeNodeTab === "rationale" ? (
                  <div className="story-node-rationale" aria-label="Node rationale">
                    {selectedNode.rationale}
                  </div>
                ) : null}

                {activeNodeTab === "scaffold" && selectedScaffold ? (
                  <div className="story-node-scaffold" aria-label="Story scaffolding editor">
                    <p className="status-line">Scaffold decision: {scaffoldDecisionByNode[getNodeKey(selectedNode)] || "pending"}</p>
                    <div className="action-grid story-scaffold-actions">
                      <button type="button" onClick={approveScaffoldAndSave} disabled={isSavingScaffold}>Approve Scaffold</button>
                      <button type="button" onClick={rejectScaffoldAndSave} disabled={isSavingScaffold}>Reject Scaffold</button>
                      <button type="button" onClick={saveSelectedScaffold} disabled={isSavingScaffold}>
                        {isSavingScaffold ? "Saving..." : "Save Scaffold"}
                      </button>
                    </div>

                    <div className="story-scaffold-export-row">
                      <label>
                        Master Entry
                        <select
                          value={targetStoryEntryId}
                          onChange={(event) => setTargetStoryEntryId(Number(event.target.value || 0))}
                        >
                          {(storyEntries || []).map((story) => (
                            <option key={story.entry_id} value={story.entry_id}>
                              {story.entry_id}: {story.title}
                            </option>
                          ))}
                        </select>
                      </label>
                      <button type="button" onClick={exportScaffoldToStoryEntry} disabled={isExportingToStory || !storyEntries.length}>
                        {isExportingToStory ? "Exporting..." : "Export To MASTER_DOCUMENT"}
                      </button>
                    </div>
                    <label className="story-scaffold-toggle">
                      <input
                        type="checkbox"
                        checked={syncStoryTitle}
                        onChange={(event) => setSyncStoryTitle(Boolean(event.target.checked))}
                      />
                      Update Story Title from Selected Node
                    </label>
                    <p className="status-line">Safe mode default is OFF to prevent accidental title overwrite.</p>
                    {storyExportStatus ? <p className="status-line">{storyExportStatus}</p> : null}
                    {lastExportEntryId ? (
                      <div className="story-scaffold-export-row">
                        <a
                          className="generated-preset-btn story-open-link"
                          href={`/storytelling-dashboard/story/${lastExportEntryId}/`}
                          target="_blank"
                          rel="noreferrer"
                        >
                          Open in Dashboard
                        </a>
                      </div>
                    ) : null}

                    <label>
                      Talking Points
                      <textarea
                        value={selectedScaffold.talkingPoints || ""}
                        onChange={(event) => updateScaffoldField("talkingPoints", event.target.value)}
                      />
                      <button type="button" className="generated-preset-btn" onClick={() => regenerateScaffoldSection("talkingPoints")}>Regenerate Section</button>
                    </label>

                    <label>
                      Core Concept
                      <textarea
                        value={selectedScaffold.coreConcept || ""}
                        onChange={(event) => updateScaffoldField("coreConcept", event.target.value)}
                      />
                      <button type="button" className="generated-preset-btn" onClick={() => regenerateScaffoldSection("coreConcept")}>Regenerate Section</button>
                    </label>

                    <label>
                      Synopsis
                      <textarea
                        value={selectedScaffold.synopsis || ""}
                        onChange={(event) => updateScaffoldField("synopsis", event.target.value)}
                      />
                      <button type="button" className="generated-preset-btn" onClick={() => regenerateScaffoldSection("synopsis")}>Regenerate Section</button>
                    </label>

                    <label>
                      Chapter Structure
                      <textarea
                        value={selectedScaffold.chapterStructure || ""}
                        onChange={(event) => updateScaffoldField("chapterStructure", event.target.value)}
                      />
                      <button type="button" className="generated-preset-btn" onClick={() => regenerateScaffoldSection("chapterStructure")}>Regenerate Section</button>
                    </label>

                    <div className="story-scaffold-atoms">
                      <strong>DCHD Atoms</strong>
                      <ul>
                        {(selectedScaffold.dchdAtoms || []).map((atom) => (
                          <li key={atom}>{atom}</li>
                        ))}
                      </ul>
                    </div>
                  </div>
                ) : null}
              </>
            ) : null}
          </div>
        </div>
      ) : null}
    </section>
  );
}
