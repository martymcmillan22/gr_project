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
        durations: {},
        timers: {},
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

export function startDeterministicTimer(timerName, tags = {}) {
  const store = getStore();
  if (!store || !timerName) {
    return "";
  }
  const normalizedTags = clonePayload(tags);
  const timerKey = `${timerName}|${Object.entries(normalizedTags)
    .map(([key, value]) => `${key}=${String(value)}`)
    .join("|")}`;
  store.metrics.timers[timerKey] = typeof performance !== "undefined" ? performance.now() : Date.now();
  return timerKey;
}

export function stopDeterministicTimer(timerKey) {
  const store = getStore();
  if (!store || !timerKey || !store.metrics.timers[timerKey]) {
    return 0;
  }

  const start = store.metrics.timers[timerKey];
  const end = typeof performance !== "undefined" ? performance.now() : Date.now();
  const durationMs = Math.max(0, Number((end - start).toFixed(2)));
  delete store.metrics.timers[timerKey];

  const durationEntry = store.metrics.durations[timerKey] || {
    count: 0,
    totalMs: 0,
    maxMs: 0,
  };
  durationEntry.count += 1;
  durationEntry.totalMs += durationMs;
  durationEntry.maxMs = Math.max(durationEntry.maxMs, durationMs);
  store.metrics.durations[timerKey] = durationEntry;

  return durationMs;
}

export function reportDeterministicError({ tier, surface, code, payload = {} }) {
  emitDeterministicTelemetry({
    eventName: "deterministic.error.reported",
    tier,
    surface,
    payload: {
      code,
      ...clonePayload(payload),
    },
  });
  incrementDeterministicMetric("deterministic.error.count", {
    tier,
    surface,
    code,
  });
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
        durations: { ...store.metrics.durations },
    },
  };
}
