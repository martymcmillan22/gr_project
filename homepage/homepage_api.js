const API_BASE = "/homepage/api";

function getCsrfToken() {
  const token = document.cookie
    .split(";")
    .map((part) => part.trim())
    .find((part) => part.startsWith("csrftoken="));
  return token ? token.split("=")[1] : "";
}

export async function getHomepageOverview() {
  const response = await fetch(`${API_BASE}/overview/`, {
    credentials: "include",
  });

  if (!response.ok) {
    throw new Error("Unable to load homepage overview");
  }

  return response.json();
}

export async function createHomepageAction(label) {
  const response = await fetch(`${API_BASE}/actions/`, {
    method: "POST",
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
      "X-CSRFToken": getCsrfToken(),
    },
    body: JSON.stringify({ label }),
  });

  if (!response.ok) {
    throw new Error("Unable to create homepage action");
  }

  return response.json();
}

export async function updateHomepagePreferences(settings) {
  const list = await fetch(`${API_BASE}/preferences/`, {
    credentials: "include",
  });
  if (!list.ok) {
    throw new Error("Unable to fetch preferences");
  }

  const payload = await list.json();
  const first = Array.isArray(payload.results) && payload.results.length ? payload.results[0] : null;

  if (!first) {
    const createResponse = await fetch(`${API_BASE}/preferences/`, {
      method: "POST",
      credentials: "include",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": getCsrfToken(),
      },
      body: JSON.stringify(settings),
    });
    if (!createResponse.ok) {
      throw new Error("Unable to create preferences");
    }
    return createResponse.json();
  }

  const patchResponse = await fetch(`${API_BASE}/preferences/${first.id}/`, {
    method: "PATCH",
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
      "X-CSRFToken": getCsrfToken(),
    },
    body: JSON.stringify(settings),
  });

  if (!patchResponse.ok) {
    throw new Error("Unable to update preferences");
  }

  return patchResponse.json();
}
