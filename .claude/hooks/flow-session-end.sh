#!/bin/bash
# Flow Guardian SessionEnd Hook
# Saves session state when user ends the session

SCRIPT_DIR="$(cd "$(dirname "$0")/../.." && pwd)"

if [ -d "$SCRIPT_DIR/.flow-guardian" ]; then
    [ -f "$SCRIPT_DIR/.env" ] && export $(grep -v '^#' "$SCRIPT_DIR/.env" | xargs)
    "$SCRIPT_DIR/.venv/bin/python" "$SCRIPT_DIR/flow_cli.py" save --quiet 2>/dev/null
fi
