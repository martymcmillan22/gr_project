const TELEMETRY_STORE_KEY = "__btDeterministicTelemetry";

function getStore() {
  if (typeof window === "undefined") {
    return null;
  }
  if (!window[TELEMETRY_STORE_KEY]) {
    window[TELEMETRY_STORE_KEY] = {
      sequence: 0,
      events: [],
      metrics: {
        counts: {},
      },
    };
  }
  return window[TELEMETRY_STORE_KEY];
}

function clonePayload(payload) {
  if (!payload || typeof payload !== "object") {
    return {};
  }
  const entries = Object.entries(payload).sort(([a], [b]) => a.localeCompare(b));
  const clone = {};
  for (const [key, value] of entries) {
    clone[key] = value;
  }
  return clone;
}

export function emitDeterministicTelemetry({ eventName, tier, surface, payload = {} }) {
  if (!eventName || !tier || !surface) {
    return null;
  }

  const normalizedPayload = clonePayload(payload);
  const record = {
    namespace: "bt.semantic.telemetry",
    event: eventName,
    tier,
    surface,
    payload: normalizedPayload,
  };

  const store = getStore();
  if (store) {
    store.sequence += 1;
    record.sequence = store.sequence;
    store.events.push(record);

    const counterKey = `${eventName}:${tier}:${surface}`;
    store.metrics.counts[counterKey] = (store.metrics.counts[counterKey] || 0) + 1;

    window.dispatchEvent(
      new CustomEvent("bt:deterministic-telemetry", {
        detail: record,
      }),
    );
  }

  return record;
}

export function incrementDeterministicMetric(metricName, tags = {}) {
  const store = getStore();
  if (!store || !metricName) {
    return;
  }

  const normalizedTags = clonePayload(tags);
  const tagKey = Object.entries(normalizedTags)
    .map(([key, value]) => `${key}=${String(value)}`)
    .join("|");
  const counterKey = tagKey ? `${metricName}|${tagKey}` : metricName;
  store.metrics.counts[counterKey] = (store.metrics.counts[counterKey] || 0) + 1;
}

export function readDeterministicTelemetryStore() {
  const store = getStore();
  if (!store) {
    return {
      sequence: 0,
      events: [],
      metrics: { counts: {} },
    };
  }
  return {
    sequence: store.sequence,
    events: [...store.events],
    metrics: {
      counts: { ...store.metrics.counts },
    },
  };
}
