import { execSync } from "node:child_process";
import { DETERMINISTIC_RELEASE_GATES } from "../src/config/deterministicReleaseGates.js";
import {
  getDeterministicTelemetryHealthSample,
  validateDeterministicTelemetryShape,
} from "../src/ui/deterministicTelemetryHealth.js";

function runCommand(command) {
  execSync(command, {
    stdio: "inherit",
  });
}

function readCommand(command) {
  return execSync(command, {
    stdio: ["ignore", "pipe", "pipe"],
    encoding: "utf-8",
  });
}

function assertNoSnapshotOrCssDrift() {
  const output = readCommand("git status --short");
  const lines = output
    .split("\n")
    .map((line) => line.trim())
    .filter(Boolean);

  const driftLines = lines.filter((line) =>
    /__snapshots__|\.snap$|\.(png|jpg|jpeg|webp)$|src\/styles\.css$/.test(line),
  );

  if (driftLines.length > 0) {
    throw new Error(`Preflight failed: snapshot or CSS drift detected:\n${driftLines.join("\n")}`);
  }
}

function assertTelemetryHealth() {
  const sample = getDeterministicTelemetryHealthSample();
  if (!validateDeterministicTelemetryShape(sample)) {
    throw new Error("Preflight failed: deterministic telemetry health check is invalid.");
  }
}

function runPreflight() {
  for (const gate of DETERMINISTIC_RELEASE_GATES) {
    if (!gate.required) {
      continue;
    }

    if (gate.id === "telemetry-health") {
      assertTelemetryHealth();
      continue;
    }

    if (gate.id === "snapshot-drift") {
      assertNoSnapshotOrCssDrift();
      continue;
    }

    runCommand(gate.command);
  }
}

runPreflight();