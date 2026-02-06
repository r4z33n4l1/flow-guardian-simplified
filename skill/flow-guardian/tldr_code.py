#!/usr/bin/env python3
"""Code-aware TLDR using AST parsing.

Unlike narrative LLM summarization, this extracts actual code structure:
- Function signatures (exact names, parameters, return types)
- Class definitions (names, methods, attributes)
- Constants and imports
- Docstrings (brief)

This preserves the symbols an agent needs to actually USE the code.

Levels:
- L1: AST (signatures only)
- L2: AST + brief docstrings
- L3: AST + docstrings + call graph hints

Usage:
    python3 tldr_code.py --file src/server.py --level L2
    python3 tldr_code.py --file src/server.py                # defaults to L1
    cat file.py | python3 tldr_code.py --level L1             # read from stdin
"""
import argparse
import ast
import re
import sys
from pathlib import Path


def extract_python_structure(content: str, filename: str = "file.py", level: str = "L1") -> str:
    """
    Extract code structure using AST parsing.

    Args:
        content: Python source code
        filename: Name for header
        level: L1 (signatures), L2 (+docstrings), L3 (+details)

    Returns:
        Structured summary preserving exact symbols
    """
    try:
        tree = ast.parse(content)
    except SyntaxError as e:
        return f"## {filename}\n[Syntax error: {e}]\n"

    lines = []
    lines.append(f"## {filename}")
    lines.append("")

    # Extract imports
    imports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            for alias in node.names:
                imports.append(f"{module}.{alias.name}")

    if imports:
        lines.append(f"**Imports:** {', '.join(imports[:10])}")
        if len(imports) > 10:
            lines.append(f"  (+{len(imports) - 10} more)")
        lines.append("")

    # Extract top-level constants
    constants = []
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id.isupper():
                    constants.append(target.id)

    if constants:
        lines.append(f"**Constants:** {', '.join(constants)}")
        lines.append("")

    # Extract classes
    classes = [node for node in ast.iter_child_nodes(tree) if isinstance(node, ast.ClassDef)]
    if classes:
        lines.append("**Classes:**")
        for cls in classes:
            bases = [_get_name(base) for base in cls.bases]
            base_str = f"({', '.join(bases)})" if bases else ""
            lines.append(f"- `{cls.name}{base_str}`")

            if level in ("L2", "L3"):
                docstring = ast.get_docstring(cls)
                if docstring:
                    first_line = docstring.split('\n')[0][:80]
                    lines.append(f"  {first_line}")

            methods = [n for n in cls.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
            if methods:
                method_sigs = []
                for method in methods[:10]:
                    sig = _format_function_signature(method, include_types=level != "L1")
                    method_sigs.append(sig)
                lines.append(f"  Methods: {', '.join(method_sigs)}")
                if len(methods) > 10:
                    lines.append(f"  (+{len(methods) - 10} more methods)")
        lines.append("")

    # Extract top-level functions
    functions = [node for node in ast.iter_child_nodes(tree)
                 if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))]

    if functions:
        lines.append("**Functions:**")
        for func in functions:
            sig = _format_function_signature(func, include_types=True)
            lines.append(f"- `{sig}`")

            if level in ("L2", "L3"):
                docstring = ast.get_docstring(func)
                if docstring:
                    first_line = docstring.split('\n')[0][:80]
                    lines.append(f"  {first_line}")
        lines.append("")

    # For L3, add call graph hints and complexity metrics
    if level == "L3":
        calls = _extract_function_calls(tree)
        if calls:
            lines.append("**Internal Calls:**")
            for caller, callees in list(calls.items())[:5]:
                lines.append(f"- {caller} -> {', '.join(callees[:5])}")
            lines.append("")

        # Complexity metrics per function
        all_funcs = [node for node in ast.walk(tree)
                     if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))]
        complex_funcs = []
        for func in all_funcs:
            cc = _compute_complexity(func)
            if cc > 3:  # Only show non-trivial complexity
                complex_funcs.append((func.name, cc))
        if complex_funcs:
            complex_funcs.sort(key=lambda x: x[1], reverse=True)
            lines.append("**Complexity (cyclomatic):**")
            for name, cc in complex_funcs[:8]:
                label = "⚠️ high" if cc > 10 else ""
                lines.append(f"- {name}: {cc} {label}".rstrip())
            lines.append("")

        # File-level metrics
        metrics = _compute_file_metrics(content, tree)
        lines.append(f"**Metrics:** {metrics['sloc']} SLOC, {metrics['num_functions']} functions, "
                     f"{metrics['num_classes']} classes, avg complexity {metrics['avg_complexity']}")
        lines.append("")

    return '\n'.join(lines)


def _format_function_signature(node, include_types: bool = True) -> str:
    """Format a function signature from AST node."""
    name = node.name
    args = []

    for arg in node.args.args:
        arg_str = arg.arg
        if include_types and arg.annotation:
            arg_str += f": {_get_annotation(arg.annotation)}"
        args.append(arg_str)

    if node.args.vararg:
        args.append(f"*{node.args.vararg.arg}")
    if node.args.kwarg:
        args.append(f"**{node.args.kwarg.arg}")

    return_str = ""
    if include_types and node.returns:
        return_str = f" -> {_get_annotation(node.returns)}"

    prefix = "async " if isinstance(node, ast.AsyncFunctionDef) else ""
    return f"{prefix}{name}({', '.join(args)}){return_str}"


def _get_annotation(node) -> str:
    """Get string representation of a type annotation."""
    if isinstance(node, ast.Name):
        return node.id
    elif isinstance(node, ast.Constant):
        return repr(node.value)
    elif isinstance(node, ast.Subscript):
        value = _get_annotation(node.value)
        slice_val = _get_annotation(node.slice)
        return f"{value}[{slice_val}]"
    elif isinstance(node, ast.Tuple):
        elements = [_get_annotation(e) for e in node.elts]
        return ', '.join(elements)
    elif isinstance(node, ast.Attribute):
        return f"{_get_annotation(node.value)}.{node.attr}"
    elif isinstance(node, ast.BinOp) and isinstance(node.op, ast.BitOr):
        left = _get_annotation(node.left)
        right = _get_annotation(node.right)
        return f"{left} | {right}"
    else:
        return "..."


def _get_name(node) -> str:
    """Get name from various AST nodes."""
    if isinstance(node, ast.Name):
        return node.id
    elif isinstance(node, ast.Attribute):
        return f"{_get_name(node.value)}.{node.attr}"
    elif isinstance(node, ast.Subscript):
        return f"{_get_name(node.value)}[...]"
    return "?"


def _extract_function_calls(tree) -> dict:
    """Extract function call graph (caller -> callees)."""
    calls = {}
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            caller = node.name
            callees = set()
            for child in ast.walk(node):
                if isinstance(child, ast.Call):
                    if isinstance(child.func, ast.Name):
                        callees.add(child.func.id)
                    elif isinstance(child.func, ast.Attribute):
                        callees.add(child.func.attr)
            if callees:
                calls[caller] = list(callees)
    return calls


def _compute_complexity(node) -> int:
    """
    Compute cyclomatic complexity for a function node.

    Counts decision points: if, elif, for, while, except, with, assert,
    boolean operators (and, or), ternary (IfExp).

    Args:
        node: AST function node

    Returns:
        Cyclomatic complexity score (1 = linear)
    """
    complexity = 1  # Base complexity
    for child in ast.walk(node):
        if isinstance(child, (ast.If, ast.IfExp)):
            complexity += 1
        elif isinstance(child, (ast.For, ast.AsyncFor, ast.While)):
            complexity += 1
        elif isinstance(child, ast.ExceptHandler):
            complexity += 1
        elif isinstance(child, (ast.With, ast.AsyncWith)):
            complexity += 1
        elif isinstance(child, ast.Assert):
            complexity += 1
        elif isinstance(child, ast.BoolOp):
            # and/or add branches
            complexity += len(child.values) - 1
    return complexity


def _compute_file_metrics(content: str, tree) -> dict:
    """
    Compute file-level metrics.

    Args:
        content: Source code text
        tree: Parsed AST

    Returns:
        Dictionary with loc, sloc, num_functions, num_classes, avg_complexity
    """
    lines = content.split('\n')
    loc = len(lines)
    sloc = sum(1 for line in lines if line.strip() and not line.strip().startswith('#'))

    functions = [n for n in ast.walk(tree)
                 if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
    classes = [n for n in ast.iter_child_nodes(tree) if isinstance(n, ast.ClassDef)]

    complexities = [_compute_complexity(f) for f in functions]
    avg_complexity = sum(complexities) / len(complexities) if complexities else 0

    return {
        "loc": loc,
        "sloc": sloc,
        "num_functions": len(functions),
        "num_classes": len(classes),
        "avg_complexity": round(avg_complexity, 1),
    }


def generate_code_tldr(content: str, filename: str, level: str = "L1") -> str:
    """
    Generate TLDR for code files using AST parsing.

    Args:
        content: File content
        filename: Filename (used to detect language)
        level: L1 (signatures), L2 (+docstrings), L3 (+call graph + complexity)

    Returns:
        Structured code summary
    """
    ext = Path(filename).suffix.lower()

    if ext == ".py":
        return extract_python_structure(content, filename, level)
    elif ext in (".js", ".ts", ".jsx", ".tsx"):
        return _extract_js_structure(content, filename, level)
    else:
        return _extract_generic_structure(content, filename, level)


def _extract_js_structure(content: str, filename: str, level: str) -> str:
    """Extract structure from JavaScript/TypeScript using regex."""
    lines = [f"## {filename}", ""]

    imports = re.findall(r"import\s+(?:{[^}]+}|\w+)\s+from\s+['\"]([^'\"]+)['\"]", content)
    if imports:
        lines.append(f"**Imports:** {', '.join(imports[:8])}")
        lines.append("")

    exports = re.findall(r"export\s+(?:default\s+)?(?:const|let|var|function|class|interface|type)\s+(\w+)", content)
    if exports:
        lines.append(f"**Exports:** {', '.join(exports)}")
        lines.append("")

    functions = re.findall(
        r"(?:export\s+)?(?:async\s+)?function\s+(\w+)\s*\(([^)]*)\)",
        content
    )
    arrow_functions = re.findall(
        r"(?:export\s+)?(?:const|let)\s+(\w+)\s*=\s*(?:async\s+)?\([^)]*\)\s*(?::\s*\w+)?\s*=>",
        content
    )

    all_funcs = [(name, params) for name, params in functions]
    all_funcs.extend([(name, "") for name in arrow_functions])

    if all_funcs:
        lines.append("**Functions:**")
        for name, params in all_funcs[:15]:
            params_short = params[:50] + "..." if len(params) > 50 else params
            lines.append(f"- `{name}({params_short})`")
        lines.append("")

    classes = re.findall(r"(?:export\s+)?(?:class|interface)\s+(\w+)", content)
    if classes:
        lines.append(f"**Classes/Interfaces:** {', '.join(classes)}")
        lines.append("")

    types = re.findall(r"(?:export\s+)?type\s+(\w+)\s*=", content)
    if types:
        lines.append(f"**Types:** {', '.join(types)}")
        lines.append("")

    return '\n'.join(lines)


def _extract_generic_structure(content: str, filename: str, level: str) -> str:
    """Fallback: Extract structure using regex patterns."""
    lines = [f"## {filename}", ""]

    func_patterns = [
        r"def\s+(\w+)\s*\(",
        r"func\s+(\w+)\s*\(",
        r"fn\s+(\w+)\s*\(",
        r"function\s+(\w+)\s*\(",
        r"public\s+\w+\s+(\w+)\s*\(",
        r"private\s+\w+\s+(\w+)\s*\(",
    ]

    functions = []
    for pattern in func_patterns:
        functions.extend(re.findall(pattern, content))

    if functions:
        unique_funcs = list(dict.fromkeys(functions))[:15]
        lines.append(f"**Functions:** {', '.join(unique_funcs)}")
        lines.append("")

    class_patterns = [
        r"class\s+(\w+)",
        r"struct\s+(\w+)",
        r"interface\s+(\w+)",
        r"trait\s+(\w+)",
    ]

    classes = []
    for pattern in class_patterns:
        classes.extend(re.findall(pattern, content))

    if classes:
        lines.append(f"**Classes/Structs:** {', '.join(dict.fromkeys(classes))}")
        lines.append("")

    return '\n'.join(lines)


def _estimate_tokens(text: str) -> int:
    """Rough token estimate (~4 chars per token for code)."""
    return len(text) // 4


def format_stats(raw_content: str, tldr_result: str, filename: str, level: str) -> str:
    """Format token count comparison between raw and compressed."""
    raw_tokens = _estimate_tokens(raw_content)
    compressed_tokens = _estimate_tokens(tldr_result)
    raw_lines = len(raw_content.splitlines())
    compressed_lines = len(tldr_result.splitlines())

    if raw_tokens > 0:
        ratio = compressed_tokens / raw_tokens
        savings = (1 - ratio) * 100
    else:
        ratio = 0
        savings = 0

    lines = [
        f"📊 TLDR Stats for {filename} (level {level}):",
        f"   Raw:        {raw_tokens:,} tokens ({raw_lines} lines)",
        f"   Compressed: {compressed_tokens:,} tokens ({compressed_lines} lines)",
        f"   Savings:    {savings:.0f}% reduction ({ratio:.2f}x ratio)",
    ]
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Code-aware TLDR using AST parsing. Extracts code structure without LLM calls."
    )
    parser.add_argument(
        "--file", "-f",
        help="Path to file to analyze. If omitted, reads from stdin."
    )
    parser.add_argument(
        "--level", "-l",
        choices=["L1", "L2", "L3"],
        default="L1",
        help="Detail level: L1=signatures, L2=+docstrings, L3=+call graph (default: L1)"
    )
    parser.add_argument(
        "--stats", "-s",
        action="store_true",
        help="Show token count comparison (raw vs compressed)"
    )

    args = parser.parse_args()

    if args.file:
        filepath = Path(args.file)
        if not filepath.exists():
            print(f"Error: File not found: {args.file}", file=sys.stderr)
            sys.exit(1)
        content = filepath.read_text(encoding="utf-8")
        filename = filepath.name
    else:
        content = sys.stdin.read()
        filename = "stdin.py"

    result = generate_code_tldr(content, filename, args.level)
    print(result)

    if args.stats:
        print()
        print(format_stats(content, result, filename, args.level))


if __name__ == "__main__":
    main()
