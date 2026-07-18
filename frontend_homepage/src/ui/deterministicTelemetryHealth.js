function isObject(value) {
  return value !== null && typeof value === "object" && !Array.isArray(value);
}

export function validateDeterministicTelemetryShape(store) {
  if (!isObject(store)) {
    return false;
  }

  if (!Number.isInteger(store.sequence) || store.sequence < 0) {
    return false;
  }

  if (!Array.isArray(store.events)) {
    return false;
  }

  if (!isObject(store.metrics)) {
    return false;
  }

  if (!isObject(store.metrics.counts)) {
    return false;
  }

  if (!isObject(store.metrics.durations)) {
    return false;
  }

  return true;
}

export function getDeterministicTelemetryHealthSample() {
  return {
    sequence: 0,
    events: [],
    metrics: {
      counts: {},
      durations: {},
    },
  };
}