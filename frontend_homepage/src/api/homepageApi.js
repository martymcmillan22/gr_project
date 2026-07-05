function getCookie(name) {
  const value = `; ${document.cookie}`;
  const parts = value.split(`; ${name}=`);
  if (parts.length === 2) {
    return parts.pop().split(";").shift();
  }
  return "";
}

const HEADERS = {
  "Content-Type": "application/json",
};

export async function fetchOverview() {
  const response = await fetch("/homepage/api/overview/", {
    credentials: "include",
  });
  if (!response.ok) {
    throw new Error("Unable to load overview");
  }
  return response.json();
}

export async function postAction(label) {
  const response = await fetch("/homepage/api/actions/", {
    method: "POST",
    credentials: "include",
    headers: {
      ...HEADERS,
      "X-CSRFToken": getCookie("csrftoken"),
    },
    body: JSON.stringify({ label }),
  });
  if (!response.ok) {
    throw new Error("Unable to write action");
  }
  return response.json();
}

export async function savePreferences(payload) {
  const listRes = await fetch("/homepage/api/preferences/", { credentials: "include" });
  if (!listRes.ok) {
    throw new Error("Unable to read preferences");
  }
  const list = await listRes.json();
  const item = list.results?.[0];

  if (!item) {
    const createRes = await fetch("/homepage/api/preferences/", {
      method: "POST",
      credentials: "include",
      headers: {
        ...HEADERS,
        "X-CSRFToken": getCookie("csrftoken"),
      },
      body: JSON.stringify(payload),
    });
    if (!createRes.ok) {
      throw new Error("Unable to create preferences");
    }
    return createRes.json();
  }

  const patchRes = await fetch(`/homepage/api/preferences/${item.id}/`, {
    method: "PATCH",
    credentials: "include",
    headers: {
      ...HEADERS,
      "X-CSRFToken": getCookie("csrftoken"),
    },
    body: JSON.stringify(payload),
  });
  if (!patchRes.ok) {
    throw new Error("Unable to update preferences");
  }
  return patchRes.json();
}

export async function fetchPresentationSlides() {
  const response = await fetch("/homepage/api/presentation-slides/", {
    credentials: "include",
  });
  if (!response.ok) {
    throw new Error("Unable to load presentation slide manifest");
  }
  return response.json();
}

export async function fetchResolvedSlide(slideId) {
  const response = await fetch(`/contracts/slides/${slideId}/`, {
    credentials: "include",
  });
  if (!response.ok) {
    throw new Error(`Unable to load resolved slide ${slideId}`);
  }
  return response.json();
}

export async function applyPresetToSlide(slideId, payload) {
  const response = await fetch(`/contracts/slides/${slideId}/apply-preset/`, {
    method: "POST",
    credentials: "include",
    headers: {
      ...HEADERS,
      "X-CSRFToken": getCookie("csrftoken"),
    },
    body: JSON.stringify(payload || {}),
  });

  let data = null;
  try {
    data = await response.json();
  } catch (_error) {
    data = null;
  }

  if (!response.ok) {
    const detail = data?.detail || "Unable to apply preset";
    throw new Error(detail);
  }

  return data;
}

export async function fetchSemanticPresets() {
  const response = await fetch("/contracts/presets/", {
    credentials: "include",
  });
  if (!response.ok) {
    throw new Error("Unable to load semantic presets");
  }
  return response.json();
}

export async function fetchPresetBundles() {
  const response = await fetch("/contracts/preset-bundles/", {
    credentials: "include",
  });
  if (!response.ok) {
    throw new Error("Unable to load preset bundles");
  }
  return response.json();
}

export async function savePresetBundle(payload) {
  const response = await fetch("/contracts/preset-bundles/create/", {
    method: "POST",
    credentials: "include",
    headers: {
      ...HEADERS,
      "X-CSRFToken": getCookie("csrftoken"),
    },
    body: JSON.stringify(payload || {}),
  });

  let data = null;
  try {
    data = await response.json();
  } catch (_error) {
    data = null;
  }

  if (!response.ok) {
    throw new Error(data?.detail || "Unable to save preset bundle");
  }

  return data;
}

export async function deletePresetBundle(bundleName) {
  const response = await fetch(`/contracts/preset-bundles/${bundleName}/delete/`, {
    method: "DELETE",
    credentials: "include",
    headers: {
      "X-CSRFToken": getCookie("csrftoken"),
    },
  });

  let data = null;
  try {
    data = await response.json();
  } catch (_error) {
    data = null;
  }

  if (!response.ok) {
    throw new Error(data?.detail || "Unable to delete preset bundle");
  }

  return data;
}

export async function comparePresetBundle(bundleName, fromRevision, toRevision) {
  const params = new URLSearchParams({
    from: String(fromRevision),
    to: String(toRevision),
  });
  const response = await fetch(`/contracts/preset-bundles/${bundleName}/compare/?${params.toString()}`, {
    credentials: "include",
  });

  let data = null;
  try {
    data = await response.json();
  } catch (_error) {
    data = null;
  }

  if (!response.ok) {
    throw new Error(data?.detail || "Unable to compare bundle revisions");
  }

  return data;
}

export async function fetchPresetBundleHistory(bundleName) {
  const response = await fetch(`/contracts/preset-bundles/${bundleName}/history/`, {
    credentials: "include",
  });

  let data = null;
  try {
    data = await response.json();
  } catch (_error) {
    data = null;
  }

  if (!response.ok) {
    throw new Error(data?.detail || "Unable to load bundle history");
  }

  return data;
}

export async function rollbackPresetBundle(bundleName, revisionNumber) {
  const response = await fetch(`/contracts/preset-bundles/${bundleName}/rollback/`, {
    method: "POST",
    credentials: "include",
    headers: {
      ...HEADERS,
      "X-CSRFToken": getCookie("csrftoken"),
    },
    body: JSON.stringify({ revision_number: revisionNumber }),
  });

  let data = null;
  try {
    data = await response.json();
  } catch (_error) {
    data = null;
  }

  if (!response.ok) {
    throw new Error(data?.detail || "Unable to rollback bundle revision");
  }

  return data;
}

export async function fetchPresetBundleShares(bundleName) {
  const response = await fetch(`/contracts/preset-bundles/${bundleName}/shares/`, {
    credentials: "include",
  });

  let data = null;
  try {
    data = await response.json();
  } catch (_error) {
    data = null;
  }

  if (!response.ok) {
    throw new Error(data?.detail || "Unable to load bundle shares");
  }

  return data;
}

export async function savePresetBundleShare(bundleName, payload) {
  const response = await fetch(`/contracts/preset-bundles/${bundleName}/shares/`, {
    method: "POST",
    credentials: "include",
    headers: {
      ...HEADERS,
      "X-CSRFToken": getCookie("csrftoken"),
    },
    body: JSON.stringify(payload || {}),
  });

  let data = null;
  try {
    data = await response.json();
  } catch (_error) {
    data = null;
  }

  if (!response.ok) {
    throw new Error(data?.detail || "Unable to save bundle share");
  }

  return data;
}

export async function fetchPresetBundleTags(bundleName) {
  const response = await fetch(`/contracts/preset-bundles/${bundleName}/tags/`, {
    credentials: "include",
  });

  let data = null;
  try {
    data = await response.json();
  } catch (_error) {
    data = null;
  }

  if (!response.ok) {
    throw new Error(data?.detail || "Unable to load bundle tags");
  }

  return data;
}

export async function savePresetBundleTag(bundleName, payload) {
  const response = await fetch(`/contracts/preset-bundles/${bundleName}/tags/`, {
    method: "POST",
    credentials: "include",
    headers: {
      ...HEADERS,
      "X-CSRFToken": getCookie("csrftoken"),
    },
    body: JSON.stringify(payload || {}),
  });

  let data = null;
  try {
    data = await response.json();
  } catch (_error) {
    data = null;
  }

  if (!response.ok) {
    throw new Error(data?.detail || "Unable to save bundle tag");
  }

  return data;
}

export async function generateSlideBundle(slideId, payload) {
  const response = await fetch(`/contracts/slides/${slideId}/generate-bundle/`, {
    method: "POST",
    credentials: "include",
    headers: {
      ...HEADERS,
      "X-CSRFToken": getCookie("csrftoken"),
    },
    body: JSON.stringify(payload || {}),
  });

  let data = null;
  try {
    data = await response.json();
  } catch (_error) {
    data = null;
  }

  if (!response.ok) {
    throw new Error(data?.detail || "Unable to generate slide bundle");
  }

  return data;
}

export async function btpeGenerateTier(payload) {
  const response = await fetch("/baseture-engine/api/generate/", {
    method: "POST",
    credentials: "include",
    headers: {
      ...HEADERS,
      "X-CSRFToken": getCookie("csrftoken"),
    },
    body: JSON.stringify(payload || {}),
  });

  let data = null;
  try {
    data = await response.json();
  } catch (_error) {
    data = null;
  }

  if (!response.ok) {
    throw new Error(data?.error || "Unable to generate BTPE tier");
  }

  return data;
}

export async function btpeGenerateSvem(generatedTierId) {
  const response = await fetch("/baseture-engine/api/hierarchy/generate-svem/", {
    method: "POST",
    credentials: "include",
    headers: {
      ...HEADERS,
      "X-CSRFToken": getCookie("csrftoken"),
    },
    body: JSON.stringify({ generated_tier_id: generatedTierId }),
  });

  const data = await response.json();
  if (!response.ok) {
    throw new Error(data?.error || "Unable to generate SVEM branches");
  }
  return data;
}

export async function btpeGenerateCccp(svemTierId) {
  const response = await fetch("/baseture-engine/api/hierarchy/generate-cccp/", {
    method: "POST",
    credentials: "include",
    headers: {
      ...HEADERS,
      "X-CSRFToken": getCookie("csrftoken"),
    },
    body: JSON.stringify({ svem_tier_id: svemTierId }),
  });

  const data = await response.json();
  if (!response.ok) {
    throw new Error(data?.error || "Unable to generate CCCP compartments");
  }
  return data;
}

export async function btpeGenerateDchd(cccpTierId) {
  const response = await fetch("/baseture-engine/api/hierarchy/generate-dchd/", {
    method: "POST",
    credentials: "include",
    headers: {
      ...HEADERS,
      "X-CSRFToken": getCookie("csrftoken"),
    },
    body: JSON.stringify({ cccp_tier_id: cccpTierId }),
  });

  const data = await response.json();
  if (!response.ok) {
    throw new Error(data?.error || "Unable to generate DCHD subcells");
  }
  return data;
}

export async function btpeGetHierarchyTree(rootId) {
  const response = await fetch(`/baseture-engine/api/hierarchy/tree/${rootId}/`, {
    credentials: "include",
  });

  const data = await response.json();
  if (!response.ok) {
    throw new Error(data?.error || "Unable to load hierarchy tree");
  }
  return data;
}

export async function btpeGetExpansionStatus(rootId) {
  const response = await fetch(`/baseture-engine/api/hierarchy/status/${rootId}/`, {
    credentials: "include",
  });

  const data = await response.json();
  if (!response.ok) {
    throw new Error(data?.error || "Unable to load hierarchy status");
  }
  return data;
}

export async function btpeApproveGeneratedTier(rootId) {
  const response = await fetch(`/baseture-engine/api/approve/${rootId}/`, {
    method: "POST",
    credentials: "include",
    headers: {
      ...HEADERS,
      "X-CSRFToken": getCookie("csrftoken"),
    },
    body: JSON.stringify({}),
  });

  const data = await response.json();
  if (!response.ok) {
    throw new Error(data?.error || "Unable to approve generated tier");
  }
  return data;
}

export async function btpeGetStoryScaffolds(rootId) {
  const response = await fetch(`/baseture-engine/api/scaffolds/${rootId}/`, {
    credentials: "include",
  });

  const data = await response.json();
  if (!response.ok) {
    throw new Error(data?.error || "Unable to load story scaffolds");
  }
  return data;
}

export async function btpeUpsertStoryScaffold(payload) {
  const response = await fetch("/baseture-engine/api/scaffolds/upsert/", {
    method: "POST",
    credentials: "include",
    headers: {
      ...HEADERS,
      "X-CSRFToken": getCookie("csrftoken"),
    },
    body: JSON.stringify(payload || {}),
  });

  const data = await response.json();
  if (!response.ok) {
    throw new Error(data?.error || "Unable to save story scaffold");
  }
  return data;
}

export async function fetchStorytellingStories() {
  const response = await fetch("/storytelling-dashboard/api/stories/", {
    credentials: "include",
  });

  const data = await response.json();
  if (!response.ok) {
    throw new Error(data?.error || "Unable to load storytelling entries");
  }
  return data;
}

export async function saveStorytellingEntry(entryId, payload) {
  const response = await fetch(`/storytelling-dashboard/api/story/${entryId}/save/`, {
    method: "POST",
    credentials: "include",
    headers: {
      ...HEADERS,
      "X-CSRFToken": getCookie("csrftoken"),
    },
    body: JSON.stringify(payload || {}),
  });

  const data = await response.json();
  if (!response.ok) {
    throw new Error(data?.error || "Unable to save storytelling entry");
  }
  return data;
}

export async function fetchSemanticStorySearch(filters = {}) {
  const params = new URLSearchParams();
  Object.entries(filters || {}).forEach(([key, value]) => {
    if (value !== undefined && value !== null && String(value).trim() !== "") {
      params.set(key, String(value));
    }
  });

  const url = params.toString()
    ? `/storytelling-dashboard/api/semantic/search/?${params.toString()}`
    : "/storytelling-dashboard/api/semantic/search/";

  const response = await fetch(url, {
    credentials: "include",
  });

  const data = await response.json();
  if (!response.ok) {
    throw new Error(data?.error || "Unable to run semantic search");
  }
  return data;
}

export async function fetchSemanticStoryClusters(clusterBy = "mlas") {
  const params = new URLSearchParams({ by: String(clusterBy || "mlas") });
  const response = await fetch(`/storytelling-dashboard/api/semantic/clusters/?${params.toString()}`, {
    credentials: "include",
  });

  const data = await response.json();
  if (!response.ok) {
    throw new Error(data?.error || "Unable to load semantic clusters");
  }
  return data;
}

export async function fetchSemanticStoryDiff(sourceId, targetId) {
  const params = new URLSearchParams({
    source_id: String(sourceId || ""),
    target_id: String(targetId || ""),
  });

  const response = await fetch(`/storytelling-dashboard/api/semantic/diff/?${params.toString()}`, {
    credentials: "include",
  });

  const data = await response.json();
  if (!response.ok) {
    throw new Error(data?.error || "Unable to compute semantic diff");
  }
  return data;
}

export async function fetchSemanticPresetsStore() {
  const response = await fetch("/storytelling-dashboard/api/semantic/presets/", {
    credentials: "include",
  });

  const data = await response.json();
  if (!response.ok) {
    throw new Error(data?.error || "Unable to load semantic presets");
  }
  return data;
}

export async function saveSemanticPresetStore(payload) {
  const response = await fetch("/storytelling-dashboard/api/semantic/presets/", {
    method: "POST",
    credentials: "include",
    headers: {
      ...HEADERS,
      "X-CSRFToken": getCookie("csrftoken"),
    },
    body: JSON.stringify(payload || {}),
  });

  const data = await response.json();
  if (!response.ok) {
    throw new Error(data?.error || "Unable to save semantic preset");
  }
  return data;
}

export async function deleteSemanticPresetStore(presetId) {
  const response = await fetch(`/storytelling-dashboard/api/semantic/presets/${presetId}/`, {
    method: "DELETE",
    credentials: "include",
    headers: {
      "X-CSRFToken": getCookie("csrftoken"),
    },
  });

  const data = await response.json();
  if (!response.ok) {
    throw new Error(data?.error || "Unable to delete semantic preset");
  }
  return data;
}
