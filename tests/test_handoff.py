"""Tests for handoff.py module.

Tests cover:
- find_project_root: Locating project root via .flow-guardian, .git, pyproject.toml
- load_handoff: Loading YAML, handling missing files, invalid YAML
- save_handoff: Validation, directory creation, atomic writes
- update_handoff: Merging updates, timestamp updates
- clear_handoff: Deleting handoff file
"""
import os
import tempfile
import pytest
from pathlib import Path
from datetime import datetime

import yaml

from handoff import (
    find_project_root,
    get_handoff_path,
    load_handoff,
    save_handoff,
    update_handoff,
    clear_handoff,
    HandoffError,
    HandoffValidationError,
    FLOW_GUARDIAN_DIR,
    HANDOFF_FILE,
)


# ============ FIXTURES ============

@pytest.fixture
def temp_project(tmp_path):
    """Create a temporary project directory."""
    return tmp_path


@pytest.fixture
def project_with_git(temp_project):
    """Create a project with .git directory."""
    git_dir = temp_project / ".git"
    git_dir.mkdir()
    return temp_project


@pytest.fixture
def project_with_flow_guardian(temp_project):
    """Create a project with .flow-guardian directory."""
    fg_dir = temp_project / FLOW_GUARDIAN_DIR
    fg_dir.mkdir()
    return temp_project


@pytest.fixture
def valid_handoff_data():
    """Return valid handoff data with required fields."""
    return {
        "goal": "Implement user authentication",
        "status": "in_progress",
        "now": "Debugging token expiry",
        "hypothesis": "Off-by-one error in timestamp",
        "files": ["src/auth.py", "tests/test_auth.py"],
        "branch": "fix/jwt-expiry",
    }


# ============ find_project_root TESTS ============

class TestFindProjectRoot:
    """Tests for find_project_root function."""

    def test_finds_flow_guardian_directory(self, project_with_flow_guardian):
        """Finds .flow-guardian as project root marker."""
        subdir = project_with_flow_guardian / "src" / "deep" / "nested"
        subdir.mkdir(parents=True)

        result = find_project_root(str(subdir))
        assert result == project_with_flow_guardian

    def test_finds_git_directory(self, project_with_git):
        """Finds .git directory as project root."""
        subdir = project_with_git / "src" / "components"
        subdir.mkdir(parents=True)

        result = find_project_root(str(subdir))
        assert result == project_with_git

    def test_finds_pyproject_toml(self, temp_project):
        """Finds pyproject.toml as project root marker."""
        (temp_project / "pyproject.toml").write_text("[project]\nname = 'test'\n")
        subdir = temp_project / "src"
        subdir.mkdir()

        result = find_project_root(str(subdir))
        assert result == temp_project

    def test_prefers_flow_guardian_over_git(self, temp_project):
        """.flow-guardian is preferred over .git."""
        (temp_project / ".git").mkdir()
        (temp_project / FLOW_GUARDIAN_DIR).mkdir()

        result = find_project_root(str(temp_project))
        assert result == temp_project  # Both markers, returns same dir

    def test_returns_start_dir_when_no_markers(self, temp_project):
        """Returns starting directory if no markers found."""
        subdir = temp_project / "some" / "path"
        subdir.mkdir(parents=True)

        result = find_project_root(str(subdir))
        # Should return the subdir since no markers found up to root
        assert result == subdir

    def test_uses_cwd_when_no_argument(self, monkeypatch, temp_project):
        """Uses current working directory when no argument provided."""
        (temp_project / ".git").mkdir()
        monkeypatch.chdir(temp_project)

        result = find_project_root()
        assert result == temp_project


# ============ get_handoff_path TESTS ============

class TestGetHandoffPath:
    """Tests for get_handoff_path function."""

    def test_returns_correct_path(self, temp_project):
        """Returns .flow-guardian/handoff.yaml path."""
        result = get_handoff_path(temp_project)
        expected = temp_project / FLOW_GUARDIAN_DIR / HANDOFF_FILE
        assert result == expected

    def test_auto_detects_project_root(self, project_with_git, monkeypatch):
        """Auto-detects project root when not provided."""
        monkeypatch.chdir(project_with_git)
        result = get_handoff_path()
        assert result.parent.parent == project_with_git


# ============ load_handoff TESTS ============

class TestLoadHandoff:
    """Tests for load_handoff function."""

    def test_returns_none_for_missing_file(self, temp_project):
        """Returns None when handoff file doesn't exist."""
        result = load_handoff(temp_project)
        assert result is None

    def test_creates_flow_guardian_directory(self, temp_project):
        """Creates .flow-guardian/ directory if missing."""
        fg_dir = temp_project / FLOW_GUARDIAN_DIR
        assert not fg_dir.exists()

        load_handoff(temp_project)
        assert fg_dir.exists()

    def test_loads_valid_yaml(self, project_with_flow_guardian, valid_handoff_data):
        """Loads and parses valid YAML file."""
        handoff_path = project_with_flow_guardian / FLOW_GUARDIAN_DIR / HANDOFF_FILE
        with open(handoff_path, 'w') as f:
            yaml.safe_dump(valid_handoff_data, f)

        result = load_handoff(project_with_flow_guardian)
        assert result == valid_handoff_data

    def test_returns_none_for_empty_file(self, project_with_flow_guardian):
        """Returns None for empty YAML file."""
        handoff_path = project_with_flow_guardian / FLOW_GUARDIAN_DIR / HANDOFF_FILE
        handoff_path.write_text("")

        result = load_handoff(project_with_flow_guardian)
        assert result is None

    def test_returns_none_for_invalid_yaml(self, project_with_flow_guardian):
        """Returns None and logs warning for invalid YAML."""
        handoff_path = project_with_flow_guardian / FLOW_GUARDIAN_DIR / HANDOFF_FILE
        handoff_path.write_text("invalid: yaml: syntax: [")

        result = load_handoff(project_with_flow_guardian)
        assert result is None


# ============ save_handoff TESTS ============

class TestSaveHandoff:
    """Tests for save_handoff function."""

    def test_saves_valid_handoff(self, temp_project, valid_handoff_data):
        """Saves valid handoff data to file."""
        result_path = save_handoff(valid_handoff_data, temp_project)

        assert result_path.exists()
        with open(result_path) as f:
            saved_data = yaml.safe_load(f)
        assert saved_data["goal"] == valid_handoff_data["goal"]
        assert saved_data["status"] == valid_handoff_data["status"]

    def test_creates_directories(self, temp_project, valid_handoff_data):
        """Creates .flow-guardian/ directory if missing."""
        fg_dir = temp_project / FLOW_GUARDIAN_DIR
        assert not fg_dir.exists()

        save_handoff(valid_handoff_data, temp_project)
        assert fg_dir.exists()

    def test_auto_generates_timestamp(self, temp_project, valid_handoff_data):
        """Auto-generates timestamp if missing."""
        data = dict(valid_handoff_data)
        assert "timestamp" not in data

        save_handoff(data, temp_project)

        loaded = load_handoff(temp_project)
        assert "timestamp" in loaded
        # Verify it's a valid ISO timestamp
        datetime.fromisoformat(loaded["timestamp"].replace('Z', '+00:00'))

    def test_validates_required_goal(self, temp_project):
        """Raises error if goal is missing."""
        data = {"status": "in_progress", "now": "Working"}

        with pytest.raises(HandoffValidationError, match="goal"):
            save_handoff(data, temp_project)

    def test_validates_required_status(self, temp_project):
        """Raises error if status is missing."""
        data = {"goal": "Test", "now": "Working"}

        with pytest.raises(HandoffValidationError, match="status"):
            save_handoff(data, temp_project)

    def test_validates_required_now(self, temp_project):
        """Raises error if now is missing."""
        data = {"goal": "Test", "status": "in_progress"}

        with pytest.raises(HandoffValidationError, match="now"):
            save_handoff(data, temp_project)

    def test_validates_status_values(self, temp_project):
        """Raises error for invalid status values."""
        data = {"goal": "Test", "status": "invalid", "now": "Working"}

        with pytest.raises(HandoffValidationError, match="Invalid status"):
            save_handoff(data, temp_project)

    def test_accepts_valid_status_values(self, temp_project):
        """Accepts all valid status values."""
        for status in ["in_progress", "completed", "blocked"]:
            data = {"goal": "Test", "status": status, "now": "Working"}
            save_handoff(data, temp_project)

            loaded = load_handoff(temp_project)
            assert loaded["status"] == status

    def test_rejects_empty_goal(self, temp_project):
        """Rejects empty string for goal."""
        data = {"goal": "", "status": "in_progress", "now": "Working"}

        with pytest.raises(HandoffValidationError, match="goal"):
            save_handoff(data, temp_project)

    def test_rejects_empty_now(self, temp_project):
        """Rejects empty string for now."""
        data = {"goal": "Test", "status": "in_progress", "now": ""}

        with pytest.raises(HandoffValidationError, match="now"):
            save_handoff(data, temp_project)


# ============ update_handoff TESTS ============

class TestUpdateHandoff:
    """Tests for update_handoff function."""

    def test_merges_into_existing(self, temp_project, valid_handoff_data):
        """Merges updates into existing handoff."""
        save_handoff(valid_handoff_data, temp_project)

        updates = {"hypothesis": "New hypothesis", "outcome": "success"}
        result = update_handoff(updates, temp_project)

        assert result["goal"] == valid_handoff_data["goal"]
        assert result["hypothesis"] == "New hypothesis"
        assert result["outcome"] == "success"

    def test_creates_new_if_none_exists(self, temp_project):
        """Creates new handoff with defaults if none exists."""
        updates = {"hypothesis": "Just a theory"}
        result = update_handoff(updates, temp_project)

        # Should have defaults plus updates
        assert result["goal"] == "Working on project"
        assert result["status"] == "in_progress"
        assert result["hypothesis"] == "Just a theory"

    def test_always_updates_timestamp(self, temp_project, valid_handoff_data):
        """Always updates timestamp on update."""
        save_handoff(valid_handoff_data, temp_project)
        original = load_handoff(temp_project)
        original_timestamp = original["timestamp"]

        # Small delay to ensure different timestamp
        import time
        time.sleep(0.01)

        update_handoff({"hypothesis": "Updated"}, temp_project)
        updated = load_handoff(temp_project)

        assert updated["timestamp"] != original_timestamp

    def test_update_can_change_required_fields(self, temp_project, valid_handoff_data):
        """Can update required fields."""
        save_handoff(valid_handoff_data, temp_project)

        updates = {
            "goal": "New goal",
            "status": "completed",
            "now": "Finished work"
        }
        result = update_handoff(updates, temp_project)

        assert result["goal"] == "New goal"
        assert result["status"] == "completed"
        assert result["now"] == "Finished work"


# ============ clear_handoff TESTS ============

class TestClearHandoff:
    """Tests for clear_handoff function."""

    def test_deletes_existing_file(self, temp_project, valid_handoff_data):
        """Deletes handoff file when it exists."""
        save_handoff(valid_handoff_data, temp_project)
        handoff_path = get_handoff_path(temp_project)
        assert handoff_path.exists()

        result = clear_handoff(temp_project)

        assert result is True
        assert not handoff_path.exists()

    def test_returns_false_when_missing(self, temp_project):
        """Returns False when handoff doesn't exist."""
        result = clear_handoff(temp_project)
        assert result is False

    def test_preserves_flow_guardian_directory(self, temp_project, valid_handoff_data):
        """Preserves .flow-guardian/ directory after clearing."""
        save_handoff(valid_handoff_data, temp_project)
        fg_dir = temp_project / FLOW_GUARDIAN_DIR

        clear_handoff(temp_project)

        assert fg_dir.exists()


# ============ INTEGRATION TESTS ============

class TestHandoffIntegration:
    """Integration tests for handoff workflow."""

    def test_full_workflow(self, temp_project):
        """Tests complete handoff workflow: create, update, clear."""
        # Create
        initial_data = {
            "goal": "Build authentication",
            "status": "in_progress",
            "now": "Setting up JWT",
        }
        save_handoff(initial_data, temp_project)

        # Verify created
        loaded = load_handoff(temp_project)
        assert loaded["goal"] == "Build authentication"
        assert "timestamp" in loaded

        # Update
        update_handoff({
            "now": "Testing token validation",
            "hypothesis": "Token format issue"
        }, temp_project)

        loaded = load_handoff(temp_project)
        assert loaded["now"] == "Testing token validation"
        assert loaded["hypothesis"] == "Token format issue"
        assert loaded["goal"] == "Build authentication"  # Preserved

        # Complete
        update_handoff({
            "status": "completed",
            "outcome": "Authentication working"
        }, temp_project)

        loaded = load_handoff(temp_project)
        assert loaded["status"] == "completed"
        assert loaded["outcome"] == "Authentication working"

        # Clear
        assert clear_handoff(temp_project) is True
        assert load_handoff(temp_project) is None

    def test_handoff_in_nested_directory(self, temp_project):
        """Works correctly from nested subdirectory."""
        # Create .git marker at root
        (temp_project / ".git").mkdir()

        # Work from nested directory
        nested = temp_project / "src" / "components" / "auth"
        nested.mkdir(parents=True)

        # Save from nested (should find project root)
        data = {
            "goal": "Auth component",
            "status": "in_progress",
            "now": "Writing tests"
        }
        project_root = find_project_root(str(nested))
        save_handoff(data, project_root)

        # Handoff should be at project root
        assert (temp_project / FLOW_GUARDIAN_DIR / HANDOFF_FILE).exists()
        assert not (nested / FLOW_GUARDIAN_DIR / HANDOFF_FILE).exists()
