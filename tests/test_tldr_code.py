"""Tests for AST-based code TLDR (tldr_code.py)."""

import pytest
from tldr_code import (
    extract_python_structure,
    generate_code_tldr,
    measure_quality,
    _format_function_signature,
    _get_annotation,
    _extract_function_calls,
)


class TestExtractPythonStructure:
    """Tests for Python AST extraction."""

    def test_extracts_functions(self):
        code = '''
def hello(name: str) -> str:
    """Say hello."""
    return f"Hello, {name}"

def goodbye():
    pass
'''
        result = extract_python_structure(code, "test.py")
        assert "hello" in result
        assert "goodbye" in result
        assert "str" in result

    def test_extracts_classes(self):
        code = '''
class MyClass:
    """A test class."""
    def method(self):
        pass

class ChildClass(MyClass):
    pass
'''
        result = extract_python_structure(code, "test.py")
        assert "MyClass" in result
        assert "ChildClass" in result
        assert "method" in result

    def test_extracts_constants(self):
        code = '''
MAX_SIZE = 100
DEFAULT_NAME = "test"
some_var = 123
'''
        result = extract_python_structure(code, "test.py")
        assert "MAX_SIZE" in result
        assert "DEFAULT_NAME" in result
        # Lowercase not captured as constant
        assert "some_var" not in result

    def test_extracts_imports(self):
        code = '''
import os
import sys
from pathlib import Path
from typing import Optional, List
'''
        result = extract_python_structure(code, "test.py")
        assert "os" in result
        assert "sys" in result
        assert "pathlib.Path" in result or "Path" in result

    def test_handles_async_functions(self):
        code = '''
async def fetch_data(url: str) -> dict:
    """Fetch data from URL."""
    pass
'''
        result = extract_python_structure(code, "test.py")
        assert "fetch_data" in result
        assert "async" in result

    def test_handles_syntax_error(self):
        code = "def broken("
        result = extract_python_structure(code, "test.py")
        assert "Syntax error" in result

    def test_includes_docstrings_at_l2(self):
        code = '''
def documented():
    """This is a docstring."""
    pass
'''
        l1_result = extract_python_structure(code, "test.py", level="L1")
        l2_result = extract_python_structure(code, "test.py", level="L2")

        # L1 should have function name
        assert "documented" in l1_result

        # L2 should have docstring
        assert "docstring" in l2_result.lower()

    def test_includes_call_graph_at_l3(self):
        code = '''
def caller():
    callee()
    other_func()

def callee():
    pass

def other_func():
    pass
'''
        l3_result = extract_python_structure(code, "test.py", level="L3")
        assert "caller" in l3_result
        assert "Calls" in l3_result or "callee" in l3_result


class TestGenerateCodeTldr:
    """Tests for multi-language TLDR generation."""

    def test_python_files(self):
        code = "def test(): pass"
        result = generate_code_tldr(code, "test.py")
        assert "test" in result

    def test_javascript_files(self):
        code = '''
import { foo } from "bar";
export function hello() {}
const arrow = () => {};
'''
        result = generate_code_tldr(code, "test.js")
        assert "hello" in result or "arrow" in result

    def test_typescript_files(self):
        code = '''
import { Component } from "react";
export interface Props {}
export type Result = string;
export class MyComponent {}
'''
        result = generate_code_tldr(code, "test.ts")
        assert "Props" in result or "Result" in result or "MyComponent" in result

    def test_unknown_extension_uses_generic(self):
        code = '''
def python_like():
    pass
function js_like() {}
'''
        result = generate_code_tldr(code, "test.xyz")
        # Should still extract something
        assert "test.xyz" in result


class TestMeasureQuality:
    """Tests for quality measurement."""

    def test_perfect_quality(self):
        code = '''
def foo():
    pass
class Bar:
    pass
'''
        tldr = "foo Bar"
        quality = measure_quality(code, "test.py", tldr)
        assert quality["quality_score"] == 100.0

    def test_zero_quality(self):
        code = '''
def specific_function_name():
    pass
'''
        tldr = "nothing relevant here"
        quality = measure_quality(code, "test.py", tldr)
        assert quality["quality_score"] == 0.0
        assert "specific_function_name" in quality["missing"]

    def test_partial_quality(self):
        code = '''
def foo():
    pass
def bar():
    pass
'''
        tldr = "foo is a function"
        quality = measure_quality(code, "test.py", tldr)
        assert quality["quality_score"] == 50.0

    def test_handles_syntax_error(self):
        code = "def broken("
        quality = measure_quality(code, "test.py", "anything")
        assert "error" in quality


class TestFormatFunctionSignature:
    """Tests for function signature formatting."""

    def test_simple_function(self):
        import ast
        code = "def foo(): pass"
        tree = ast.parse(code)
        func = tree.body[0]
        sig = _format_function_signature(func)
        assert sig == "foo()"

    def test_function_with_args(self):
        import ast
        code = "def foo(a, b): pass"
        tree = ast.parse(code)
        func = tree.body[0]
        sig = _format_function_signature(func, include_types=False)
        assert sig == "foo(a, b)"

    def test_function_with_types(self):
        import ast
        code = "def foo(a: int, b: str) -> bool: pass"
        tree = ast.parse(code)
        func = tree.body[0]
        sig = _format_function_signature(func, include_types=True)
        assert "int" in sig
        assert "str" in sig
        assert "bool" in sig

    def test_async_function(self):
        import ast
        code = "async def foo(): pass"
        tree = ast.parse(code)
        func = tree.body[0]
        sig = _format_function_signature(func)
        assert "async" in sig


class TestExtractFunctionCalls:
    """Tests for call graph extraction."""

    def test_extracts_calls(self):
        import ast
        code = '''
def caller():
    foo()
    bar()

def foo():
    pass
'''
        tree = ast.parse(code)
        calls = _extract_function_calls(tree)
        assert "caller" in calls
        assert "foo" in calls["caller"]
        assert "bar" in calls["caller"]

    def test_extracts_method_calls(self):
        import ast
        code = '''
def process():
    obj.method()
    self.helper()
'''
        tree = ast.parse(code)
        calls = _extract_function_calls(tree)
        assert "process" in calls
        assert "method" in calls["process"]
        assert "helper" in calls["process"]


class TestRealCodeQuality:
    """Test quality on actual project files."""

    def test_handoff_quality(self):
        try:
            with open("handoff.py") as f:
                content = f.read()
            tldr = generate_code_tldr(content, "handoff.py", level="L2")
            quality = measure_quality(content, "handoff.py", tldr)

            # Should preserve most symbols
            assert quality["quality_score"] >= 90.0
        except FileNotFoundError:
            pytest.skip("handoff.py not found")

    def test_tldr_quality(self):
        try:
            with open("tldr.py") as f:
                content = f.read()
            tldr = generate_code_tldr(content, "tldr.py", level="L2")
            quality = measure_quality(content, "tldr.py", tldr)

            # Should preserve most symbols
            assert quality["quality_score"] >= 90.0
        except FileNotFoundError:
            pytest.skip("tldr.py not found")
