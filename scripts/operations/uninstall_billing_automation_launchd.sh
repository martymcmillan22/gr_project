#!/usr/bin/env bash
set -euo pipefail

LABEL="com.grassroots.billing-automation"
PLIST_TARGET="$HOME/Library/LaunchAgents/$LABEL.plist"

if [[ -f "$PLIST_TARGET" ]]; then
  launchctl unload "$PLIST_TARGET" 2>/dev/null || true
  rm -f "$PLIST_TARGET"
fi

echo "Uninstalled $LABEL"
