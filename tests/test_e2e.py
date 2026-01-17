"""End-to-end tests for the seamless context system.

Tests the full flow: save → close → reopen → context restored.
"""
import json
import os
import tempfile
from datetime import datetime
from pathlib import Path
from unittest import mock

import pytest

import handoff
import inject
import backboard_client
import memory


class TestSaveAndRestoreFlow:
    """End-to-end tests for save and restore flow."""

    @pytest.fixture
    def mock_project(self, tmp_path, monkeypatch):
        """Create a mock project directory with git."""
        project_dir = tmp_path / "test-project"
        project_dir.mkdir()
        flow_guardian_dir = project_dir / ".flow-guardian"
        flow_guardian_dir.mkdir()

        # Mock find_project_root to return our test directory
        monkeypatch.setattr(handoff, 'find_project_root', lambda cwd=None: project_dir)
        monkeypatch.setattr(inject, 'find_project_root', lambda cwd=None: project_dir)

        return project_dir

    def test_save_creates_handoff_file(self, mock_project):
        """Saving state should create handoff.yaml."""
        handoff_path = mock_project / ".flow-guardian" / "handoff.yaml"

        # Initially no handoff
        assert not handoff_path.exists()

        # Save handoff
        data = {
            "goal": "Implement feature X",
            "status": "in_progress",
            "now": "Writing tests",
            "branch": "feature/x",
            "files": ["src/feature.py", "tests/test_feature.py"],
        }
        handoff.save_handoff(data, project_root=mock_project)

        # Now handoff exists
        assert handoff_path.exists()
        loaded = handoff.load_handoff(project_root=mock_project)
        assert loaded["goal"] == "Implement feature X"
        assert loaded["now"] == "Writing tests"
        assert loaded["branch"] == "feature/x"

    def test_load_restores_saved_state(self, mock_project):
        """Loading should return the previously saved state."""
        # Save initial state
        initial_data = {
            "goal": "Fix bug #123",
            "status": "in_progress",
            "now": "Debugging auth module",
            "hypothesis": "Token expiration issue",
            "files": ["src/auth.py"],
            "branch": "fix/auth-bug",
        }
        handoff.save_handoff(initial_data, project_root=mock_project)

        # Load and verify
        loaded = handoff.load_handoff(project_root=mock_project)
        assert loaded["goal"] == initial_data["goal"]
        assert loaded["now"] == initial_data["now"]
        assert loaded["hypothesis"] == initial_data["hypothesis"]
        assert loaded["files"] == initial_data["files"]

    def test_update_merges_with_existing(self, mock_project):
        """Update should merge with existing handoff data."""
        # Save initial state
        initial_data = {
            "goal": "Build API",
            "status": "in_progress",
            "now": "Designing endpoints",
            "branch": "main",
        }
        handoff.save_handoff(initial_data, project_root=mock_project)

        # Update with new progress
        handoff.update_handoff(
            {"now": "Implementing authentication", "files": ["api/auth.py"]},
            project_root=mock_project
        )

        # Verify merge
        loaded = handoff.load_handoff(project_root=mock_project)
        assert loaded["goal"] == "Build API"  # Unchanged
        assert loaded["now"] == "Implementing authentication"  # Updated
        assert loaded["files"] == ["api/auth.py"]  # Added

    @pytest.mark.asyncio
    async def test_full_save_restore_cycle(self, mock_project, monkeypatch):
        """Test full cycle: save state, simulate restart, inject context."""
        # Skip Backboard calls
        monkeypatch.delenv("BACKBOARD_PERSONAL_THREAD_ID", raising=False)
        monkeypatch.setattr(backboard_client, 'API_KEY', None)

        # Mock git functions to avoid actual git calls
        monkeypatch.setattr(inject, 'get_current_branch', lambda: "feature/test")
        monkeypatch.setattr(inject, 'get_uncommitted_files', lambda: ["file1.py", "file2.py"])

        # === PHASE 1: Save state before closing ===
        # Simulate user saving their work state
        save_data = {
            "goal": "Implement user dashboard",
            "status": "in_progress",
            "now": "Building chart components",
            "hypothesis": "D3.js will be faster than Chart.js",
            "files": ["components/Chart.tsx", "utils/data.ts"],
            "branch": "feature/dashboard",
        }
        handoff.save_handoff(save_data, project_root=mock_project)

        # === PHASE 2: Simulate session close (clear any in-memory state) ===
        # In real scenario, Claude Code session ends here
        # The handoff.yaml file persists on disk

        # === PHASE 3: Restore context on new session ===
        # Load handoff (simulates SessionStart hook)
        loaded = handoff.load_handoff(project_root=mock_project)

        # Verify all context is preserved
        assert loaded is not None
        assert loaded["goal"] == "Implement user dashboard"
        assert loaded["now"] == "Building chart components"
        assert loaded["hypothesis"] == "D3.js will be faster than Chart.js"
        assert loaded["files"] == ["components/Chart.tsx", "utils/data.ts"]
        assert loaded["branch"] == "feature/dashboard"

    @pytest.mark.asyncio
    async def test_inject_generates_context_string(self, mock_project, monkeypatch):
        """Test that inject generates proper context string."""
        # Skip Backboard
        monkeypatch.delenv("BACKBOARD_PERSONAL_THREAD_ID", raising=False)
        monkeypatch.setattr(backboard_client, 'API_KEY', None)

        # Mock local memory to return empty (no stored learnings)
        monkeypatch.setattr(memory, 'search_learnings', lambda **kwargs: [])

        # Save handoff data
        save_data = {
            "goal": "Refactor database layer",
            "status": "in_progress",
            "now": "Migrating to async",
            "branch": "feature/async-db",
        }
        handoff.save_handoff(save_data, project_root=mock_project)

        # Generate injection
        context = await inject.generate_injection(
            level="L1",
            quiet=False,
            project_root=mock_project
        )

        # Verify output contains key information
        assert "flow-guardian-context" in context
        assert "Refactor database layer" in context or "refactor database layer" in context.lower()
        assert "async" in context.lower()

    def test_format_injection_quiet_mode(self, mock_project):
        """Test that quiet mode produces plain output without wrapper tags."""
        handoff_data = {
            "goal": "Test feature",
            "status": "in_progress",
            "now": "Running tests",
            "branch": "main",
        }

        # Quiet mode - no wrapper tags
        quiet_output = inject.format_injection(
            handoff=handoff_data,
            memory=[],
            level="L1",
            quiet=True
        )

        # Quiet mode should NOT have wrapper tags
        assert "<flow-guardian-context>" not in quiet_output
        # But should still have content
        assert "Goal:" in quiet_output or "goal" in quiet_output.lower()
        assert "Test feature" in quiet_output

        # Non-quiet mode should have wrapper tags
        non_quiet_output = inject.format_injection(
            handoff=handoff_data,
            memory=[],
            level="L1",
            quiet=False
        )
        assert "<flow-guardian-context>" in non_quiet_output

    def test_format_injection_with_memory(self, mock_project):
        """Test that injection includes memory results."""
        handoff_data = {
            "goal": "Fix performance",
            "status": "in_progress",
            "now": "Profiling",
            "branch": "perf",
        }

        memory_results = [
            {"content": "Use connection pooling for DB", "metadata": {"type": "learning"}},
            {"content": "Decided to use Redis for caching", "metadata": {"type": "decision"}},
        ]

        output = inject.format_injection(
            handoff=handoff_data,
            memory=memory_results,
            level="L1",
            quiet=True
        )

        # Should include memory
        assert "connection pooling" in output or "Memory" in output

    @pytest.mark.asyncio
    async def test_save_current_state_captures_git_info(self, mock_project, monkeypatch):
        """Test that save_current_state captures git state."""
        # Mock git functions
        monkeypatch.setattr(inject, 'get_current_branch', lambda: "feature/test-branch")
        monkeypatch.setattr(inject, 'get_uncommitted_files', lambda: ["modified.py", "new.py"])

        # Create initial handoff
        initial = {
            "goal": "Test git capture",
            "status": "in_progress",
            "now": "Initial state",
        }
        handoff.save_handoff(initial, project_root=mock_project)

        # Save current state
        result = await inject.save_current_state(project_root=mock_project)

        # Verify git info was captured
        assert result["branch"] == "feature/test-branch"
        assert result["files"] == ["modified.py", "new.py"]


class TestContextPersistence:
    """Tests for context persistence across simulated restarts."""

    @pytest.fixture
    def persistent_storage(self, tmp_path, monkeypatch):
        """Set up persistent storage for testing."""
        project_dir = tmp_path / "persistent-project"
        project_dir.mkdir()
        (project_dir / ".flow-guardian").mkdir()

        monkeypatch.setattr(handoff, 'find_project_root', lambda cwd=None: project_dir)
        monkeypatch.setattr(inject, 'find_project_root', lambda cwd=None: project_dir)

        return project_dir

    def test_context_survives_multiple_updates(self, persistent_storage):
        """Context should persist across multiple updates."""
        # Initial save
        handoff.save_handoff({
            "goal": "Build feature",
            "status": "in_progress",
            "now": "Step 1",
        }, project_root=persistent_storage)

        # Multiple updates
        handoff.update_handoff({"now": "Step 2"}, project_root=persistent_storage)
        handoff.update_handoff({"now": "Step 3", "files": ["a.py"]}, project_root=persistent_storage)
        handoff.update_handoff({"hypothesis": "This should work"}, project_root=persistent_storage)

        # Final state should have all updates
        final = handoff.load_handoff(project_root=persistent_storage)
        assert final["goal"] == "Build feature"
        assert final["now"] == "Step 3"
        assert final["files"] == ["a.py"]
        assert final["hypothesis"] == "This should work"

    def test_status_transitions(self, persistent_storage):
        """Test status field transitions."""
        # Start in_progress
        handoff.save_handoff({
            "goal": "Complete task",
            "status": "in_progress",
            "now": "Working",
        }, project_root=persistent_storage)

        # Transition to blocked
        handoff.update_handoff({"status": "blocked", "now": "Waiting for review"}, project_root=persistent_storage)
        assert handoff.load_handoff(project_root=persistent_storage)["status"] == "blocked"

        # Transition to completed
        handoff.update_handoff({"status": "completed", "now": "Done!"}, project_root=persistent_storage)
        assert handoff.load_handoff(project_root=persistent_storage)["status"] == "completed"


class TestInjectLevels:
    """Test different TLDR levels for injection."""

    @pytest.fixture
    def setup_handoff(self, tmp_path, monkeypatch):
        """Set up handoff for level tests."""
        project_dir = tmp_path / "level-test"
        project_dir.mkdir()
        (project_dir / ".flow-guardian").mkdir()

        monkeypatch.setattr(handoff, 'find_project_root', lambda cwd=None: project_dir)

        # Save detailed handoff
        handoff.save_handoff({
            "goal": "Implement authentication system with OAuth2",
            "status": "in_progress",
            "now": "Configuring OAuth providers",
            "hypothesis": "Using passport.js will simplify OAuth integration",
            "files": ["auth/oauth.ts", "auth/providers/google.ts", "auth/providers/github.ts"],
            "branch": "feature/oauth",
        }, project_root=project_dir)

        return project_dir

    def test_l0_minimal_output(self, setup_handoff):
        """L0 level should produce minimal output (just paths)."""
        output = inject.format_injection(
            handoff=handoff.load_handoff(project_root=setup_handoff),
            memory=[],
            level="L0",
            quiet=True
        )
        # L0 should be concise
        assert len(output) < 2000

    def test_l1_balanced_output(self, setup_handoff):
        """L1 level should include descriptions."""
        output = inject.format_injection(
            handoff=handoff.load_handoff(project_root=setup_handoff),
            memory=[],
            level="L1",
            quiet=True
        )
        # L1 should include goal and current focus
        assert "authentication" in output.lower() or "oauth" in output.lower()

    def test_l2_detailed_output(self, setup_handoff):
        """L2 level should include more logic details."""
        output = inject.format_injection(
            handoff=handoff.load_handoff(project_root=setup_handoff),
            memory=[],
            level="L2",
            quiet=True
        )
        # L2 should be more detailed
        assert len(output) >= len(inject.format_injection(
            handoff=handoff.load_handoff(project_root=setup_handoff),
            memory=[],
            level="L0",
            quiet=True
        ))
