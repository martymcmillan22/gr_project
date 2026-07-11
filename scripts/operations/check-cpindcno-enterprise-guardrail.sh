#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/../.." && pwd)"
CPINDCNO_DIR="$ROOT_DIR/docs/CPINDCNO"
ENTERPRISE_DIR="$ROOT_DIR/docs/CPINDCNO-Enterprise"

if [[ ! -d "$CPINDCNO_DIR" ]]; then
  echo "FAIL: Missing directory: $CPINDCNO_DIR"
  exit 1
fi

if [[ ! -d "$ENTERPRISE_DIR" ]]; then
  echo "FAIL: Missing directory: $ENTERPRISE_DIR"
  exit 1
fi

# Rule 1: No CPINDCNO file may reference CPINDCNO-Enterprise paths,
# except the guardrail policy document that defines this rule.

if command -v rg >/dev/null 2>&1; then
  if rg -n --no-heading \
    -g '!enterprise-separation-guardrail.md' \
    "CPINDCNO-Enterprise|docs/CPINDCNO-Enterprise" \
    "$CPINDCNO_DIR" >/tmp/cpindcno_guardrail_refs.txt; then
    echo "FAIL: CPINDCNO files reference CPINDCNO-Enterprise."
    cat /tmp/cpindcno_guardrail_refs.txt
    exit 1
  fi
else
  if grep -RInE \
    --exclude='enterprise-separation-guardrail.md' \
    "CPINDCNO-Enterprise|docs/CPINDCNO-Enterprise" \
    "$CPINDCNO_DIR" >/tmp/cpindcno_guardrail_refs.txt; then
    echo "FAIL: CPINDCNO files reference CPINDCNO-Enterprise."
    cat /tmp/cpindcno_guardrail_refs.txt
    exit 1
  fi
fi

# Rule 2: No misplaced Enterprise blueprint file under CPINDCNO namespace.
if find "$CPINDCNO_DIR" -type f -iname "*enterprise-tier-blueprint*" | grep -q .; then
  echo "FAIL: Misplaced enterprise-tier-blueprint file found under docs/CPINDCNO."
  find "$CPINDCNO_DIR" -type f -iname "*enterprise-tier-blueprint*"
  exit 1
fi

# Rule 3: No CPINDCNO-Enterprise markdown file should be duplicated under CPINDCNO.
while IFS= read -r enterprise_file; do
  rel_path="${enterprise_file#"$ENTERPRISE_DIR/"}"
  if [[ -f "$CPINDCNO_DIR/$rel_path" ]]; then
    echo "FAIL: Duplicate enterprise file found in CPINDCNO namespace: docs/CPINDCNO/$rel_path"
    exit 1
  fi
done < <(find "$ENTERPRISE_DIR" -type f -name "*.md")

echo "PASS: CPINDCNO enterprise separation guardrail checks passed."
