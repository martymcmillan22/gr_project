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
