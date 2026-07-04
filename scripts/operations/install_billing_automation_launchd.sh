#!/usr/bin/env bash
set -euo pipefail

LABEL="com.grassroots.billing-automation"
REPO_ROOT="/Users/martymcmillan/Desktop/GrassRoots"
PYTHON_BIN="$REPO_ROOT/a_gr_venv/bin/python"
MANAGE_PY="$REPO_ROOT/manage.py"
PLIST_TARGET="$HOME/Library/LaunchAgents/$LABEL.plist"
LOG_OUT="/tmp/grassroots-billing-automation.log"
LOG_ERR="/tmp/grassroots-billing-automation.err.log"

mkdir -p "$HOME/Library/LaunchAgents"

if [[ ! -x "$PYTHON_BIN" ]]; then
  echo "Missing python interpreter: $PYTHON_BIN" >&2
  exit 1
fi

if [[ ! -f "$MANAGE_PY" ]]; then
  echo "Missing manage.py: $MANAGE_PY" >&2
  exit 1
fi

cat > "$PLIST_TARGET" <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>$LABEL</string>

  <key>ProgramArguments</key>
  <array>
    <string>$PYTHON_BIN</string>
    <string>$MANAGE_PY</string>
    <string>run_billing_automation</string>
    <string>--tenant=default</string>
    <string>--client=all</string>
    <string>--limit=50</string>
  </array>

  <key>WorkingDirectory</key>
  <string>$REPO_ROOT</string>

  <key>StartInterval</key>
  <integer>3600</integer>

  <key>RunAtLoad</key>
  <true/>

  <key>StandardOutPath</key>
  <string>$LOG_OUT</string>

  <key>StandardErrorPath</key>
  <string>$LOG_ERR</string>
</dict>
</plist>
PLIST

launchctl unload "$PLIST_TARGET" 2>/dev/null || true
launchctl load "$PLIST_TARGET"
launchctl start "$LABEL"

echo "Installed and started $LABEL"
echo "Plist: $PLIST_TARGET"
echo "Logs:  $LOG_OUT and $LOG_ERR"
