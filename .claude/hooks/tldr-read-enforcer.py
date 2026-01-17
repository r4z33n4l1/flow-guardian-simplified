#!/Users/mihajlomicic/Desktop/flow-guardian/.venv/bin/python3
"""
TLDR Read Enforcer Hook

Intercepts Read tool calls and returns TLDR summaries instead of raw files.
Saves 95% of tokens on code file reads.

Input (stdin JSON):
    {
        "session_id": "...",
        "tool_name": "Read",
        "tool_input": {"file_path": "/path/to/file.py"},
        "cwd": "/project/root"
    }

Output (stdout JSON):
    {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": "TLDR summary provided instead of raw file",
            "additionalContext": "<tldr content>"
        }
    }

Bypass conditions (allows raw read):
    - Config files (.json, .yaml, .toml, .ini, .env, etc.)
    - Small files (<100 lines)
    - Test files (test_*.py, *_test.py)
    - Hook/skill files (.claude/*)
    - Non-code files (images, binaries)
    - Explicit bypass in tool_input
"""

import json
import os
import sys
from pathlib import Path

# Add parent directories to path for imports
SCRIPT_DIR = Path(__file__).parent.parent.parent  # flow-guardian root
sys.path.insert(0, str(SCRIPT_DIR))

from dotenv import load_dotenv
load_dotenv(SCRIPT_DIR / ".env")

# File extensions to TLDR (code files)
CODE_EXTENSIONS = {
    '.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.go', '.rs', '.rb',
    '.c', '.cpp', '.h', '.hpp', '.cs', '.swift', '.kt', '.scala',
    '.php', '.pl', '.pm', '.sh', '.bash', '.zsh', '.fish',
    '.sql', '.graphql', '.proto',
}

# File extensions to bypass (config/data files - read raw)
BYPASS_EXTENSIONS = {
    '.json', '.yaml', '.yml', '.toml', '.ini', '.env', '.cfg', '.conf',
    '.md', '.txt', '.rst', '.csv', '.xml', '.html', '.css', '.scss',
    '.lock', '.sum', '.mod',
    '.png', '.jpg', '.jpeg', '.gif', '.svg', '.ico',
    '.pdf', '.doc', '.docx',
}

# Paths to always bypass
BYPASS_PATHS = {
    '.claude/',
    '.flow-guardian/',
    'node_modules/',
    '.git/',
    '__pycache__/',
    '.venv/',
    'venv/',
}

# Max lines for small file bypass
SMALL_FILE_THRESHOLD = 100


def should_bypass(file_path: str, cwd: str) -> tuple[bool, str]:
    """
    Determine if file should bypass TLDR and be read raw.

    Returns:
        (should_bypass, reason)
    """
    path = Path(file_path)

    # Check extension bypass
    ext = path.suffix.lower()
    if ext in BYPASS_EXTENSIONS:
        return True, f"Config/data file ({ext})"

    # Check if it's a code file we should TLDR
    if ext not in CODE_EXTENSIONS:
        return True, f"Non-code file ({ext or 'no extension'})"

    # Check path bypass patterns
    file_str = str(file_path)
    for bypass_path in BYPASS_PATHS:
        if bypass_path in file_str:
            return True, f"Bypass path ({bypass_path})"

    # Check if test file
    name = path.name.lower()
    if name.startswith('test_') or name.endswith('_test.py') or '/tests/' in file_str:
        return True, "Test file"

    # Check file size (small files don't need TLDR)
    try:
        if path.exists():
            line_count = sum(1 for _ in open(path, 'r', errors='ignore'))
            if line_count < SMALL_FILE_THRESHOLD:
                return True, f"Small file ({line_count} lines)"
    except Exception:
        pass  # If we can't read it, let the Read tool handle the error

    return False, ""


def get_tldr(file_path: str, level: str = "L2") -> str:
    """
    Get TLDR summary of a file using AST-based extraction.

    Uses AST parsing for code files to preserve exact symbols (function names,
    class names, signatures) - unlike LLM summarization which loses these.
    """
    try:
        from tldr_code import generate_code_tldr

        path = Path(file_path)
        if not path.exists():
            return ""

        content = path.read_text(errors='ignore')
        if not content.strip():
            return ""

        original_lines = len(content.split('\n'))

        # Use AST-based extraction for code files (preserves symbols)
        summary = generate_code_tldr(content, path.name, level=level)

        if summary and len(summary.strip()) > 50:
            summary_lines = len(summary.split('\n'))
            savings = round((1 - summary_lines / original_lines) * 100)

            # Obvious header and footer so Claude knows AND mentions it's a TLDR
            header = f"""╔══════════════════════════════════════════════════════════════════╗
║  📋 TLDR SUMMARY (Flow Guardian)                                  ║
║  Original: {path.name} ({original_lines} lines → {summary_lines} lines, {savings}% savings)
╚══════════════════════════════════════════════════════════════════╝

"""
            footer = f"""

---
📋 **Note:** You are viewing a TLDR summary of `{path.name}`, not the full file.
When responding, briefly mention you're working from a TLDR summary ({savings}% smaller).
If the user needs specific implementation details not shown above, offer to read the full file."""

            return header + summary + footer
        else:
            # Fallback: return first 50 lines
            lines = content.split('\n')[:50]
            return f"=== {path.name} (first 50 lines) ===\n" + '\n'.join(lines)

    except Exception as e:
        # On error, let the Read tool handle it normally
        sys.stderr.write(f"[tldr-read-enforcer] Error: {e}\n")
        return ""


def main():
    try:
        # Read input from stdin
        input_data = json.loads(sys.stdin.read())

        tool_name = input_data.get('tool_name', '')
        tool_input = input_data.get('tool_input', {})
        cwd = input_data.get('cwd', os.getcwd())

        # Only intercept Read tool
        if tool_name != 'Read':
            print('{}')
            return

        file_path = tool_input.get('file_path', '')
        if not file_path:
            print('{}')
            return

        # Make path absolute if relative
        if not Path(file_path).is_absolute():
            file_path = str(Path(cwd) / file_path)

        # Check bypass conditions
        should_skip, reason = should_bypass(file_path, cwd)
        if should_skip:
            sys.stderr.write(f"[tldr-read-enforcer] Bypass: {reason} - {file_path}\n")
            print('{}')  # Allow normal read
            return

        # Get TLDR summary
        tldr_content = get_tldr(file_path)

        if not tldr_content:
            # TLDR failed, allow normal read
            sys.stderr.write(f"[tldr-read-enforcer] TLDR failed, allowing raw read: {file_path}\n")
            print('{}')
            return

        # Write TLDR to temp file and redirect Read to it
        # This makes the UX cleaner - shows as successful read, not "blocking error"
        import tempfile

        # Create obvious TLDR filename that shows in Claude Code UI
        original_name = Path(file_path).name
        temp_dir = Path(tempfile.gettempdir()) / "flow-guardian-tldr"
        temp_dir.mkdir(exist_ok=True)
        temp_file = temp_dir / f"TLDR__{original_name}.md"

        # Write TLDR content to temp file
        temp_file.write_text(tldr_content)

        # Return allow with modified input pointing to temp file
        output = {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "allow",
                "updatedInput": {
                    "file_path": str(temp_file)
                }
            }
        }

        sys.stderr.write(f"[tldr-read-enforcer] TLDR: {file_path} -> {temp_file}\n")
        print(json.dumps(output))

    except json.JSONDecodeError as e:
        sys.stderr.write(f"[tldr-read-enforcer] JSON error: {e}\n")
        print('{}')
    except Exception as e:
        sys.stderr.write(f"[tldr-read-enforcer] Error: {e}\n")
        print('{}')


if __name__ == '__main__':
    main()
