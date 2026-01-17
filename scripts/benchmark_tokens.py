#!/usr/bin/env python3
"""
Benchmark: Token savings with Flow Guardian TLDR

Compares tokens required for:
1. Reading raw source files (like CC-v3 does)
2. Using TLDR compressed context at different levels

Usage:
    cd flow-guardian && .venv/bin/python scripts/benchmark_tokens.py
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
PROJECT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_DIR))

# Load environment
from dotenv import load_dotenv
load_dotenv()

import subprocess

# Try to import tiktoken for accurate token counting
try:
    import tiktoken
    enc = tiktoken.get_encoding("cl100k_base")  # Claude's encoding
    def count_tokens(text: str) -> int:
        if not text:
            return 0
        return len(enc.encode(text))
except ImportError:
    print("Installing tiktoken...")
    subprocess.run([sys.executable, "-m", "pip", "install", "tiktoken", "-q"])
    import tiktoken
    enc = tiktoken.get_encoding("cl100k_base")
    def count_tokens(text: str) -> int:
        if not text:
            return 0
        return len(enc.encode(text))

from tldr import summarize_handoff, summarize_recall, summarize_context
from handoff import load_handoff
import backboard_client


def read_raw_files(files: list[Path]) -> tuple[str, int]:
    """Read files raw and count tokens."""
    content = ""
    for f in files:
        if f.exists():
            content += f"=== {f.name} ===\n"
            content += f.read_text()
            content += "\n\n"
    return content, count_tokens(content)


def get_raw_recall_results(query: str) -> tuple[str, int]:
    """Get raw recall results from Backboard."""
    thread_id = os.environ.get("BACKBOARD_PERSONAL_THREAD_ID")
    if not thread_id:
        return "No thread ID configured", 0

    try:
        import asyncio
        results = asyncio.run(backboard_client.recall(thread_id, query))
        raw_content = str(results)
        return raw_content, count_tokens(raw_content)
    except Exception as e:
        return str(e), 0


def get_tldr_recall(query: str, level: str) -> tuple[str, int]:
    """Get TLDR summarized recall results."""
    thread_id = os.environ.get("BACKBOARD_PERSONAL_THREAD_ID")
    if not thread_id:
        return "No thread ID configured", 0

    try:
        import asyncio
        results = asyncio.run(backboard_client.recall(thread_id, query))

        # Convert to list format expected by summarize_recall
        if isinstance(results, dict):
            results_list = [results]
        elif isinstance(results, str):
            results_list = [{"content": results}]
        else:
            results_list = results if isinstance(results, list) else []

        tldr_content = summarize_recall(results_list, level)
        return tldr_content, count_tokens(tldr_content)
    except Exception as e:
        return str(e), 0


def main():
    print("=" * 70)
    print("TOKEN SAVINGS BENCHMARK: Raw Files vs Flow Guardian TLDR")
    print("=" * 70)
    print(f"Project: {PROJECT_DIR}")
    print(f"Encoder: cl100k_base (Claude)")
    print()

    results = []

    # =========================================================================
    # Scenario 1: Single file analysis (like CC-v3)
    # =========================================================================
    print("─" * 70)
    print("SCENARIO 1: Single File Analysis (flow_cli.py)")
    print("─" * 70)

    cli_file = PROJECT_DIR / "flow_cli.py"
    raw_content, raw_tokens = read_raw_files([cli_file])

    # TLDR would summarize this
    tldr_content = summarize_context(raw_content, "L1", max_tokens=500)
    tldr_tokens = count_tokens(tldr_content)
    savings = (1 - tldr_tokens / raw_tokens) * 100 if raw_tokens > 0 else 0

    print(f"  Raw file:     {raw_tokens:,} tokens")
    print(f"  TLDR L1:      {tldr_tokens:,} tokens")
    print(f"  Savings:      {savings:.0f}%")
    print()

    results.append(("Single file", raw_tokens, tldr_tokens, savings))

    # =========================================================================
    # Scenario 2: Core module analysis (3 files)
    # =========================================================================
    print("─" * 70)
    print("SCENARIO 2: Core Modules (3 files: handoff, tldr, inject)")
    print("─" * 70)

    core_files = [
        PROJECT_DIR / "handoff.py",
        PROJECT_DIR / "tldr.py",
        PROJECT_DIR / "inject.py",
    ]
    raw_content, raw_tokens = read_raw_files(core_files)

    tldr_content = summarize_context(raw_content, "L1", max_tokens=800)
    tldr_tokens = count_tokens(tldr_content)
    savings = (1 - tldr_tokens / raw_tokens) * 100 if raw_tokens > 0 else 0

    print(f"  Raw files (3): {raw_tokens:,} tokens")
    print(f"  TLDR L1:       {tldr_tokens:,} tokens")
    print(f"  Savings:       {savings:.0f}%")
    print()

    results.append(("Core modules", raw_tokens, tldr_tokens, savings))

    # =========================================================================
    # Scenario 3: Full codebase overview (all .py files)
    # =========================================================================
    print("─" * 70)
    print("SCENARIO 3: Full Codebase (all Python files)")
    print("─" * 70)

    py_files = list(PROJECT_DIR.glob("*.py"))
    raw_content, raw_tokens = read_raw_files(py_files)

    tldr_content = summarize_context(raw_content, "L1", max_tokens=1500)
    tldr_tokens = count_tokens(tldr_content)
    savings = (1 - tldr_tokens / raw_tokens) * 100 if raw_tokens > 0 else 0

    print(f"  Raw files ({len(py_files)}): {raw_tokens:,} tokens")
    print(f"  TLDR L1:        {tldr_tokens:,} tokens")
    print(f"  Savings:        {savings:.0f}%")
    print()

    results.append(("Full codebase", raw_tokens, tldr_tokens, savings))

    # =========================================================================
    # Scenario 4: Semantic recall from memory
    # =========================================================================
    print("─" * 70)
    print("SCENARIO 4: Semantic Recall (query: 'project architecture')")
    print("─" * 70)

    query = "project architecture, key decisions, and implementation details"

    raw_content, raw_tokens = get_raw_recall_results(query)
    print(f"  Raw recall:   {raw_tokens:,} tokens")

    tldr_content, tldr_tokens = get_tldr_recall(query, "L1")
    savings = (1 - tldr_tokens / raw_tokens) * 100 if raw_tokens > 0 else 0
    print(f"  TLDR L1:      {tldr_tokens:,} tokens")
    print(f"  Savings:      {savings:.0f}%")
    print()

    results.append(("Semantic recall", raw_tokens, tldr_tokens, savings))

    # =========================================================================
    # Scenario 5: Context injection (handoff + recall)
    # =========================================================================
    print("─" * 70)
    print("SCENARIO 5: Full Context Injection")
    print("─" * 70)

    # Raw: handoff + recall + some codebase context
    handoff = load_handoff() or {}
    raw_parts = [
        f"Handoff: {handoff}",
        f"Recall: {raw_content}",
    ]
    full_raw = "\n".join(raw_parts)
    raw_tokens = count_tokens(full_raw)

    print(f"  Raw injection: {raw_tokens:,} tokens")

    # Get actual injection output
    try:
        result = subprocess.run(
            [".venv/bin/python", "flow_cli.py", "inject", "--quiet", "--level", "L1"],
            capture_output=True,
            text=True,
            timeout=30,
            cwd=str(PROJECT_DIR),
        )
        inject_content = result.stdout
        inject_tokens = count_tokens(inject_content)
        savings = (1 - inject_tokens / raw_tokens) * 100 if raw_tokens > 0 else 0
        print(f"  Inject L1:     {inject_tokens:,} tokens")
        print(f"  Savings:       {savings:.0f}%")
        results.append(("Context injection", raw_tokens, inject_tokens, savings))
    except Exception as e:
        print(f"  Error: {e}")

    print()

    # =========================================================================
    # Summary
    # =========================================================================
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print()
    print(f"{'Scenario':<22} {'Raw':>12} {'TLDR':>12} {'Savings':>10}")
    print("-" * 56)

    total_raw = 0
    total_tldr = 0

    for name, raw, tldr, sav in results:
        if raw > 0:
            print(f"{name:<22} {raw:>12,} {tldr:>12,} {sav:>9.0f}%")
            total_raw += raw
            total_tldr += tldr

    print("-" * 56)
    total_savings = (1 - total_tldr / total_raw) * 100 if total_raw > 0 else 0
    print(f"{'TOTAL':<22} {total_raw:>12,} {total_tldr:>12,} {total_savings:>9.0f}%")
    print()

    # =========================================================================
    # Tweet-ready stats
    # =========================================================================
    if total_raw > 0:
        saved_tokens = total_raw - total_tldr

        print("=" * 70)
        print("📊 BENCHMARK RESULTS")
        print("=" * 70)
        print()
        print(f"🎯 Flow Guardian TLDR saves {total_savings:.0f}% of tokens")
        print()
        print(f"   Raw context:  {total_raw:,} tokens")
        print(f"   TLDR context: {total_tldr:,} tokens")
        print(f"   Saved:        {saved_tokens:,} tokens")
        print()

        # Cost savings estimate
        # Claude pricing: ~$3/M input for Sonnet, ~$15/M for Opus
        sonnet_saved = (saved_tokens / 1_000_000) * 3
        opus_saved = (saved_tokens / 1_000_000) * 15

        print("   💰 Cost savings per 1000 context injections:")
        print(f"   • Sonnet ($3/M):  ${sonnet_saved * 1000:.2f}")
        print(f"   • Opus ($15/M):   ${opus_saved * 1000:.2f}")
        print()


if __name__ == "__main__":
    main()
