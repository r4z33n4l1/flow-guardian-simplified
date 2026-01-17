#!/bin/bash
# Flow Guardian PreCompact Hook
# Saves state before context compaction

if [ -d ".flow-guardian" ]; then
    [ -f ".env" ] && export $(grep -v '^#' .env | xargs)
    flow inject --quiet --save-state 2>/dev/null
fi
