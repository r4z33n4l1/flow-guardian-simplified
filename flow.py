#!/usr/bin/env python3
"""Flow Guardian CLI entry point.

This module re-exports the CLI and its dependencies from flow_cli.py
for backwards compatibility and as the main entry point for the 'flow' command.
"""
# Re-export CLI and dependencies for backwards compatibility with tests
from flow_cli import (
    cli,
    capture,
    memory,
    restore,
    backboard_client,
)

if __name__ == "__main__":
    cli()
