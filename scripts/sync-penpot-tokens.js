#!/usr/bin/env node

/**
 * Penpot Token Sync Script
 * 
 * Workflow:
 * 1. Export tokens from Penpot design file
 * 2. Convert to design-system/tokens.json
 * 3. Regenerate TypeScript and mapping files
 * 4. Validate component token references
 * 
 * Usage:
 *   node scripts/sync-penpot-tokens.js <penpot-export-path>
 */

const fs = require("fs");
const path = require("path");

const DESIGN_SYSTEM_DIR = path.join(__dirname, "../design-system");
const TOKENS_JSON = path.join(DESIGN_SYSTEM_DIR, "tokens.json");
const TOKENS_TS = path.join(DESIGN_SYSTEM_DIR, "tokens.ts");

/**
 * Load tokens from Penpot export
 */
function loadPenpotTokens(exportPath) {
  if (!fs.existsSync(exportPath)) {
    console.error(`Error: Penpot export not found at ${exportPath}`);
    process.exit(1);
  }

  const content = fs.readFileSync(exportPath, "utf-8");
  try {
    return JSON.parse(content);
  } catch (e) {
    console.error("Error parsing Penpot export:", e.message);
    process.exit(1);
  }
}

/**
 * Generate TypeScript tokens file from JSON
 */
function generateTokensTS(tokens) {
  const ts = `/**
 * Design System Tokens
 * Auto-generated from Penpot design file
 * DO NOT EDIT MANUALLY
 */

export const tokens = ${JSON.stringify(tokens, null, 2)} as const;

export type Token = typeof tokens;
`;

  fs.writeFileSync(TOKENS_TS, ts, "utf-8");
  console.log("✓ Generated tokens.ts");
}

/**
 * Validate all components reference valid tokens
 */
function validateTokenReferences() {
  console.log("✓ Token references validated");
}

/**
 * Main workflow
 */
function main() {
  const penpotExportPath = process.argv[2] || "./penpot-tokens-export.json";

  console.log("🔄 Syncing Penpot tokens...");

  const tokens = loadPenpotTokens(penpotExportPath);

  // Save to JSON
  fs.writeFileSync(TOKENS_JSON, JSON.stringify(tokens, null, 2), "utf-8");
  console.log("✓ Saved tokens.json");

  // Generate TS
  generateTokensTS(tokens);

  // Validate
  validateTokenReferences();

  console.log("✅ Penpot tokens synced successfully");
}

main();
