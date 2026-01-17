"""Tests for inject.py module.

Tests cover:
- generate_injection: Context generation with handoff and memory
- format_injection: Output formatting for Claude
- save_current_state: State preservation for PreCompact
- Fallback behavior when Backboard unavailable
"""
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from pathlib import Path

from inject import (
    generate_injection,
    format_injection,
    save_current_state,
    generate_injection_sync,
    save_current_state_sync,
    INJECTION_HEADER,
    INJECTION_FOOTER,
)


# ============ FIXTURES ============

@pytest.fixture
def temp_project(tmp_path):
    """Create a temporary project directory with .git marker."""
    (tmp_path / ".git").mkdir()
    return tmp_path


@pytest.fixture
def sample_handoff():
    """Return sample handoff data."""
    return {
        "goal": "Implement user authentication",
        "status": "in_progress",
        "now": "Debugging token expiry",
        "hypothesis": "Off-by-one error in timestamp",
        "branch": "fix/jwt-expiry",
        "files": ["src/auth.py", "tests/test_auth.py"],
    }


@pytest.fixture
def sample_memory():
    """Return sample memory/recall results."""
    return [
        {
            "content": "JWT tokens need both iat and exp claims",
            "metadata": {"type": "learnings"}
        },
        {
            "content": "Using HS256 for simplicity",
            "metadata": {"type": "decisions"}
        },
    ]


# ============ format_injection TESTS ============

class TestFormatInjection:
    """Tests for format_injection function."""

    def test_empty_handoff_and_memory(self, monkeypatch, temp_project):
        """Shows new session message when no context."""
        monkeypatch.chdir(temp_project)
        result = format_injection(None, [])

        assert INJECTION_HEADER in result
        assert INJECTION_FOOTER in result
        assert "New Session" in result
        assert "No previous context" in result

    def test_includes_handoff_state(self, sample_handoff):
        """Includes handoff fields in output."""
        result = format_injection(sample_handoff, [])

        assert "Implement user authentication" in result
        assert "in_progress" in result
        assert "Debugging token expiry" in result
        assert "fix/jwt-expiry" in result

    def test_includes_hypothesis(self, sample_handoff):
        """Includes hypothesis in output."""
        result = format_injection(sample_handoff, [])
        assert "Off-by-one error" in result

    def test_includes_files(self, sample_handoff):
        """Includes file list in output."""
        result = format_injection(sample_handoff, [])
        assert "src/auth.py" in result
        assert "tests/test_auth.py" in result

    def test_includes_memory(self, sample_handoff, sample_memory):
        """Includes memory results in output."""
        result = format_injection(sample_handoff, sample_memory)

        assert "Relevant Memory" in result
        # Memory content or categories should appear
        assert "JWT" in result or "Learnings" in result

    def test_quiet_mode_no_tags(self, sample_handoff):
        """Quiet mode omits XML wrapper tags."""
        result = format_injection(sample_handoff, [], quiet=True)

        assert INJECTION_HEADER not in result
        assert INJECTION_FOOTER not in result

    def test_quiet_mode_includes_content(self, sample_handoff):
        """Quiet mode still includes content."""
        result = format_injection(sample_handoff, [], quiet=True)
        assert "Implement user authentication" in result

    def test_l0_truncates_files(self):
        """L0 shows all files but briefly."""
        handoff = {
            "goal": "Work",
            "status": "in_progress",
            "now": "Testing",
            "files": ["a.py", "b.py", "c.py", "d.py", "e.py", "f.py", "g.py"],
        }
        result = format_injection(handoff, [], level="L0")
        # All files should be listed
        assert "g.py" in result

    def test_l1_truncates_many_files(self):
        """L1 truncates file list when > 5 files."""
        handoff = {
            "goal": "Work",
            "status": "in_progress",
            "now": "Testing",
            "files": ["a.py", "b.py", "c.py", "d.py", "e.py", "f.py", "g.py"],
        }
        result = format_injection(handoff, [], level="L1")
        assert "(+2 more)" in result


# ============ generate_injection TESTS ============

class TestGenerateInjection:
    """Tests for generate_injection function."""

    @pytest.mark.asyncio
    async def test_loads_handoff(self, temp_project, sample_handoff, monkeypatch):
        """Loads handoff from project."""
        monkeypatch.chdir(temp_project)

        with patch('inject.load_handoff', return_value=sample_handoff):
            with patch('inject._recall_for_injection', new_callable=AsyncMock, return_value=[]):
                result = await generate_injection(project_root=temp_project)

        assert "Implement user authentication" in result

    @pytest.mark.asyncio
    async def test_queries_backboard(self, temp_project, monkeypatch):
        """Queries Backboard for memory."""
        monkeypatch.chdir(temp_project)
        monkeypatch.setenv("BACKBOARD_PERSONAL_THREAD_ID", "test-thread")

        with patch('inject.load_handoff', return_value=None):
            with patch('inject._recall_for_injection', new_callable=AsyncMock) as mock_recall_inject:
                mock_recall_inject.return_value = [{"content": "Memory from Backboard", "metadata": {}}]
                result = await generate_injection(project_root=temp_project)

        assert "Memory from Backboard" in result or "Memory" in result

    @pytest.mark.asyncio
    async def test_handles_missing_thread_id(self, temp_project, monkeypatch):
        """Gracefully handles missing thread ID."""
        monkeypatch.chdir(temp_project)
        monkeypatch.delenv("BACKBOARD_PERSONAL_THREAD_ID", raising=False)

        with patch('inject.load_handoff', return_value=None):
            result = await generate_injection(project_root=temp_project)

        # Should still produce output (new session message)
        assert "New Session" in result or INJECTION_HEADER in result

    @pytest.mark.asyncio
    async def test_respects_level_parameter(self, temp_project, sample_handoff, monkeypatch):
        """Respects TLDR level parameter."""
        monkeypatch.chdir(temp_project)

        with patch('inject.load_handoff', return_value=sample_handoff):
            with patch('inject._recall_for_injection', new_callable=AsyncMock, return_value=[]):
                result_l0 = await generate_injection(level="L0", project_root=temp_project)
                result_l2 = await generate_injection(level="L2", project_root=temp_project)

        # Both should have content
        assert "auth" in result_l0.lower() or "authentication" in result_l0.lower()
        assert "auth" in result_l2.lower() or "authentication" in result_l2.lower()


# ============ save_current_state TESTS ============

class TestSaveCurrentState:
    """Tests for save_current_state function."""

    @pytest.mark.asyncio
    async def test_creates_handoff_if_missing(self, temp_project, monkeypatch):
        """Creates handoff if none exists."""
        monkeypatch.chdir(temp_project)

        with patch('inject.get_current_branch', return_value="main"):
            with patch('inject.get_uncommitted_files', return_value=["test.py"]):
                result = await save_current_state(temp_project)

        assert result["status"] == "in_progress"
        assert result["branch"] == "main"
        assert "test.py" in result["files"]

    @pytest.mark.asyncio
    async def test_updates_existing_handoff(self, temp_project, sample_handoff, monkeypatch):
        """Updates existing handoff with new info."""
        monkeypatch.chdir(temp_project)

        with patch('inject.load_handoff', return_value=sample_handoff):
            with patch('inject.get_current_branch', return_value="new-branch"):
                with patch('inject.get_uncommitted_files', return_value=["new.py"]):
                    with patch('inject.update_handoff') as mock_update:
                        mock_update.return_value = {**sample_handoff, "branch": "new-branch"}
                        result = await save_current_state(temp_project)

        assert result["goal"] == "Implement user authentication"

    @pytest.mark.asyncio
    async def test_handles_git_errors(self, temp_project, monkeypatch):
        """Handles git command errors gracefully."""
        monkeypatch.chdir(temp_project)

        with patch('inject.load_handoff', return_value=None):
            with patch('inject.get_current_branch', side_effect=Exception("Git error")):
                with patch('inject.get_uncommitted_files', side_effect=Exception("Git error")):
                    result = await save_current_state(temp_project)

        # Should still create handoff without git info
        assert result["status"] == "in_progress"


# ============ SYNC WRAPPERS TESTS ============

class TestSyncWrappers:
    """Tests for synchronous wrapper functions."""

    def test_generate_injection_sync(self, temp_project, sample_handoff, monkeypatch):
        """Sync wrapper works correctly."""
        monkeypatch.chdir(temp_project)

        with patch('inject.load_handoff', return_value=sample_handoff):
            with patch('inject._recall_for_injection', new_callable=AsyncMock, return_value=[]):
                result = generate_injection_sync(project_root=temp_project)

        assert "Implement user authentication" in result

    def test_save_current_state_sync(self, temp_project, monkeypatch):
        """Sync wrapper for save_current_state works."""
        monkeypatch.chdir(temp_project)

        with patch('inject.load_handoff', return_value=None):
            with patch('inject.get_current_branch', return_value="main"):
                with patch('inject.get_uncommitted_files', return_value=[]):
                    result = save_current_state_sync(temp_project)

        assert result["status"] == "in_progress"


# ============ INTEGRATION TESTS ============

class TestInjectIntegration:
    """Integration tests for inject module."""

    @pytest.mark.asyncio
    async def test_full_injection_workflow(self, temp_project, monkeypatch):
        """Tests complete injection workflow."""
        monkeypatch.chdir(temp_project)

        # Set up handoff
        handoff = {
            "goal": "Build API endpoint",
            "status": "in_progress",
            "now": "Writing tests",
            "branch": "feature/api",
            "files": ["api.py", "test_api.py"],
        }

        # Set up memory
        memory = [
            {"content": "API should return JSON", "metadata": {"type": "decisions"}},
        ]

        with patch('inject.load_handoff', return_value=handoff):
            with patch('inject._recall_for_injection', new_callable=AsyncMock, return_value=memory):
                result = await generate_injection(project_root=temp_project)

        # Should include handoff info
        assert "Build API endpoint" in result
        assert "Writing tests" in result
        assert "feature/api" in result

        # Should include memory
        assert "Memory" in result or "Decisions" in result

        # Should have proper structure
        assert INJECTION_HEADER in result
        assert INJECTION_FOOTER in result
