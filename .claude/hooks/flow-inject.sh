#!/bin/bash
# Flow Guardian SessionStart Hook
# Injects project context at session start

if [ -d ".flow-guardian" ]; then
    [ -f ".env" ] && export $(grep -v '^#' .env | xargs)
    flow inject --quiet 2>/dev/null
fi
