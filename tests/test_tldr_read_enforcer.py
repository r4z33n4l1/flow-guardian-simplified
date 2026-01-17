"""Tests for TLDR Read Enforcer hook."""

import json
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

# Add hook directory to path
HOOK_PATH = Path(__file__).parent.parent / ".claude" / "hooks" / "tldr-read-enforcer.py"
PROJECT_ROOT = Path(__file__).parent.parent

# Import the hook module
sys.path.insert(0, str(HOOK_PATH.parent.parent.parent))
sys.path.insert(0, str(HOOK_PATH.parent))

# We need to import the functions from the hook
# Since it's a script, we'll test by running it as subprocess and also by importing

class TestShouldBypass:
    """Test bypass logic for different file types."""

    @pytest.fixture
    def hook_module(self):
        """Import hook module for testing."""
        import importlib.util
        spec = importlib.util.spec_from_file_location("tldr_read_enforcer", HOOK_PATH)
        module = importlib.util.module_from_spec(spec)

        # Mock the imports that require env setup
        with patch.dict('sys.modules', {'tldr': MagicMock()}):
            spec.loader.exec_module(module)
        return module

    def test_bypass_json_files(self, hook_module):
        """JSON config files should be read raw."""
        should_bypass, reason = hook_module.should_bypass("/path/to/config.json", "/project")
        assert should_bypass is True
        assert ".json" in reason

    def test_bypass_yaml_files(self, hook_module):
        """YAML config files should be read raw."""
        should_bypass, reason = hook_module.should_bypass("/path/to/config.yaml", "/project")
        assert should_bypass is True
        assert ".yaml" in reason

    def test_bypass_env_files(self, hook_module):
        """Env files should be read raw."""
        should_bypass, reason = hook_module.should_bypass("/path/to/.env", "/project")
        assert should_bypass is True
        # .env has no extension, so bypassed as non-code file

    def test_bypass_markdown_files(self, hook_module):
        """Markdown files should be read raw."""
        should_bypass, reason = hook_module.should_bypass("/path/to/README.md", "/project")
        assert should_bypass is True
        assert ".md" in reason

    def test_bypass_test_files_prefix(self, hook_module):
        """Test files with test_ prefix should be read raw."""
        should_bypass, reason = hook_module.should_bypass("/path/to/test_main.py", "/project")
        assert should_bypass is True
        assert "Test file" in reason

    def test_bypass_test_files_suffix(self, hook_module):
        """Test files with _test suffix should be read raw."""
        should_bypass, reason = hook_module.should_bypass("/path/to/main_test.py", "/project")
        assert should_bypass is True
        assert "Test file" in reason

    def test_bypass_tests_directory(self, hook_module):
        """Files in tests/ directory should be read raw."""
        should_bypass, reason = hook_module.should_bypass("/project/tests/conftest.py", "/project")
        assert should_bypass is True
        assert "Test file" in reason

    def test_bypass_claude_directory(self, hook_module):
        """Files in .claude/ should be read raw."""
        should_bypass, reason = hook_module.should_bypass("/project/.claude/hooks/hook.py", "/project")
        assert should_bypass is True
        assert ".claude/" in reason

    def test_bypass_flow_guardian_directory(self, hook_module):
        """Files in .flow-guardian/ should be read raw."""
        should_bypass, reason = hook_module.should_bypass("/project/.flow-guardian/config.yaml", "/project")
        assert should_bypass is True
        # Bypassed either for path or extension

    def test_bypass_node_modules(self, hook_module):
        """Files in node_modules/ should be read raw."""
        should_bypass, reason = hook_module.should_bypass("/project/node_modules/pkg/index.js", "/project")
        assert should_bypass is True
        assert "node_modules/" in reason

    def test_bypass_git_directory(self, hook_module):
        """Files in .git/ should be read raw."""
        should_bypass, reason = hook_module.should_bypass("/project/.git/config", "/project")
        assert should_bypass is True
        # Bypassed either for path or no extension

    def test_bypass_image_files(self, hook_module):
        """Image files should be read raw (let Read tool handle them)."""
        should_bypass, reason = hook_module.should_bypass("/path/to/image.png", "/project")
        assert should_bypass is True
        assert ".png" in reason

    def test_bypass_no_extension(self, hook_module):
        """Files with no extension should be read raw."""
        should_bypass, reason = hook_module.should_bypass("/path/to/Makefile", "/project")
        assert should_bypass is True
        assert "no extension" in reason

    def test_no_bypass_python_files(self, hook_module, tmp_path):
        """Python code files should get TLDR treatment."""
        # Create a file with enough lines
        py_file = tmp_path / "main.py"
        py_file.write_text("\n".join([f"line {i}" for i in range(150)]))

        should_bypass, reason = hook_module.should_bypass(str(py_file), str(tmp_path))
        assert should_bypass is False
        assert reason == ""

    def test_no_bypass_javascript_files(self, hook_module, tmp_path):
        """JavaScript code files should get TLDR treatment."""
        js_file = tmp_path / "app.js"
        js_file.write_text("\n".join([f"// line {i}" for i in range(150)]))

        should_bypass, reason = hook_module.should_bypass(str(js_file), str(tmp_path))
        assert should_bypass is False

    def test_no_bypass_typescript_files(self, hook_module, tmp_path):
        """TypeScript code files should get TLDR treatment."""
        ts_file = tmp_path / "app.ts"
        ts_file.write_text("\n".join([f"// line {i}" for i in range(150)]))

        should_bypass, reason = hook_module.should_bypass(str(ts_file), str(tmp_path))
        assert should_bypass is False

    def test_bypass_small_python_files(self, hook_module, tmp_path):
        """Small Python files (<100 lines) should be read raw."""
        py_file = tmp_path / "small.py"
        py_file.write_text("\n".join([f"line {i}" for i in range(50)]))

        should_bypass, reason = hook_module.should_bypass(str(py_file), str(tmp_path))
        assert should_bypass is True
        assert "Small file" in reason


class TestHookExecution:
    """Test hook execution via subprocess."""

    def test_hook_is_executable(self):
        """Hook script should be executable."""
        assert HOOK_PATH.exists()
        # Check it's a valid Python script
        result = subprocess.run(
            [sys.executable, "-m", "py_compile", str(HOOK_PATH)],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, f"Syntax error: {result.stderr}"

    def test_hook_empty_input(self):
        """Hook should handle empty/invalid input gracefully."""
        result = subprocess.run(
            [sys.executable, str(HOOK_PATH)],
            input="{}",
            capture_output=True,
            text=True,
            timeout=10
        )
        # Should return empty JSON (allow read)
        assert result.returncode == 0
        assert result.stdout.strip() == "{}"

    def test_hook_non_read_tool(self):
        """Hook should ignore non-Read tools."""
        input_data = {
            "session_id": "test",
            "tool_name": "Bash",
            "tool_input": {"command": "ls"},
            "cwd": "/tmp"
        }
        result = subprocess.run(
            [sys.executable, str(HOOK_PATH)],
            input=json.dumps(input_data),
            capture_output=True,
            text=True,
            timeout=10
        )
        assert result.returncode == 0
        assert result.stdout.strip() == "{}"

    def test_hook_config_file_bypass(self):
        """Hook should allow raw read for config files."""
        input_data = {
            "session_id": "test",
            "tool_name": "Read",
            "tool_input": {"file_path": "/path/to/config.json"},
            "cwd": "/tmp"
        }
        result = subprocess.run(
            [sys.executable, str(HOOK_PATH)],
            input=json.dumps(input_data),
            capture_output=True,
            text=True,
            timeout=10
        )
        assert result.returncode == 0
        assert result.stdout.strip() == "{}"
        assert "Bypass" in result.stderr

    def test_hook_test_file_bypass(self):
        """Hook should allow raw read for test files."""
        input_data = {
            "session_id": "test",
            "tool_name": "Read",
            "tool_input": {"file_path": "/path/to/test_main.py"},
            "cwd": "/tmp"
        }
        result = subprocess.run(
            [sys.executable, str(HOOK_PATH)],
            input=json.dumps(input_data),
            capture_output=True,
            text=True,
            timeout=10
        )
        assert result.returncode == 0
        assert result.stdout.strip() == "{}"

    def test_hook_code_file_tldr(self, tmp_path):
        """Hook should return TLDR for code files."""
        # Create a large Python file
        code_file = tmp_path / "large_module.py"
        code_content = '''"""A large module for testing."""

def function_one():
    """Does something important."""
    x = 1
    y = 2
    return x + y

def function_two():
    """Does something else."""
    for i in range(100):
        print(i)

class MyClass:
    """A test class."""

    def __init__(self):
        self.value = 42

    def method(self):
        return self.value * 2

''' + "\n".join([f"# Comment line {i}" for i in range(100)])

        code_file.write_text(code_content)

        input_data = {
            "session_id": "test",
            "tool_name": "Read",
            "tool_input": {"file_path": str(code_file)},
            "cwd": str(tmp_path)
        }

        result = subprocess.run(
            [sys.executable, str(HOOK_PATH)],
            input=json.dumps(input_data),
            capture_output=True,
            text=True,
            timeout=30,
            env={**subprocess.os.environ, "PYTHONPATH": str(PROJECT_ROOT)}
        )

        assert result.returncode == 0

        # Should either deny with TLDR or allow (if TLDR fails due to missing API key)
        output = json.loads(result.stdout.strip())

        if output:
            # TLDR was applied
            assert "hookSpecificOutput" in output
            assert output["hookSpecificOutput"]["permissionDecision"] == "deny"
            assert "additionalContext" in output["hookSpecificOutput"]
            assert "TLDR" in result.stderr
        else:
            # TLDR failed, allowed raw read
            assert "{}" == result.stdout.strip() or "failed" in result.stderr.lower()

    def test_hook_invalid_json(self):
        """Hook should handle invalid JSON gracefully."""
        result = subprocess.run(
            [sys.executable, str(HOOK_PATH)],
            input="not valid json",
            capture_output=True,
            text=True,
            timeout=10
        )
        assert result.returncode == 0
        assert result.stdout.strip() == "{}"
        assert "JSON error" in result.stderr

    def test_hook_missing_file_path(self):
        """Hook should handle missing file_path gracefully."""
        input_data = {
            "session_id": "test",
            "tool_name": "Read",
            "tool_input": {},
            "cwd": "/tmp"
        }
        result = subprocess.run(
            [sys.executable, str(HOOK_PATH)],
            input=json.dumps(input_data),
            capture_output=True,
            text=True,
            timeout=10
        )
        assert result.returncode == 0
        assert result.stdout.strip() == "{}"


class TestHookIntegration:
    """Integration tests with actual project files."""

    def test_hook_on_flow_cli(self):
        """Test hook on our own flow_cli.py (should TLDR it)."""
        flow_cli_path = PROJECT_ROOT / "flow_cli.py"
        if not flow_cli_path.exists():
            pytest.skip("flow_cli.py not found")

        input_data = {
            "session_id": "test",
            "tool_name": "Read",
            "tool_input": {"file_path": str(flow_cli_path)},
            "cwd": str(PROJECT_ROOT)
        }

        result = subprocess.run(
            [sys.executable, str(HOOK_PATH)],
            input=json.dumps(input_data),
            capture_output=True,
            text=True,
            timeout=30,
            env={**subprocess.os.environ, "PYTHONPATH": str(PROJECT_ROOT)}
        )

        assert result.returncode == 0
        # flow_cli.py is large, should get TLDR treatment (or fail gracefully)

    def test_hook_on_settings_json(self):
        """Test hook on .claude/settings.json (should bypass)."""
        settings_path = PROJECT_ROOT / ".claude" / "settings.json"
        if not settings_path.exists():
            pytest.skip("settings.json not found")

        input_data = {
            "session_id": "test",
            "tool_name": "Read",
            "tool_input": {"file_path": str(settings_path)},
            "cwd": str(PROJECT_ROOT)
        }

        result = subprocess.run(
            [sys.executable, str(HOOK_PATH)],
            input=json.dumps(input_data),
            capture_output=True,
            text=True,
            timeout=10
        )

        assert result.returncode == 0
        assert result.stdout.strip() == "{}"  # Should bypass
        assert "Bypass" in result.stderr


class TestBypassExtensions:
    """Test that all expected extensions are in bypass lists."""

    @pytest.fixture
    def hook_module(self):
        """Import hook module for testing."""
        import importlib.util
        spec = importlib.util.spec_from_file_location("tldr_read_enforcer", HOOK_PATH)
        module = importlib.util.module_from_spec(spec)

        with patch.dict('sys.modules', {'tldr': MagicMock()}):
            spec.loader.exec_module(module)
        return module

    def test_code_extensions_defined(self, hook_module):
        """Verify code extensions are defined."""
        assert '.py' in hook_module.CODE_EXTENSIONS
        assert '.js' in hook_module.CODE_EXTENSIONS
        assert '.ts' in hook_module.CODE_EXTENSIONS
        assert '.go' in hook_module.CODE_EXTENSIONS
        assert '.rs' in hook_module.CODE_EXTENSIONS

    def test_bypass_extensions_defined(self, hook_module):
        """Verify bypass extensions are defined."""
        assert '.json' in hook_module.BYPASS_EXTENSIONS
        assert '.yaml' in hook_module.BYPASS_EXTENSIONS
        assert '.md' in hook_module.BYPASS_EXTENSIONS
        assert '.txt' in hook_module.BYPASS_EXTENSIONS

    def test_bypass_paths_defined(self, hook_module):
        """Verify bypass paths are defined."""
        assert '.claude/' in hook_module.BYPASS_PATHS
        assert '.flow-guardian/' in hook_module.BYPASS_PATHS
        assert 'node_modules/' in hook_module.BYPASS_PATHS
        assert '.git/' in hook_module.BYPASS_PATHS
