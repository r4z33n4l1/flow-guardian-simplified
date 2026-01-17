"""Tests for the flow.py CLI module."""
from unittest import mock

import pytest
from click.testing import CliRunner

import flow
import flow_cli


@pytest.fixture
def cli_runner():
    """Create a Click CLI test runner."""
    return CliRunner()


class TestCLIBasics:
    """Tests for basic CLI functionality."""

    def test_help_command(self, cli_runner):
        """CLI should display help message."""
        result = cli_runner.invoke(flow.cli, ['--help'])

        assert result.exit_code == 0
        assert "Flow Guardian" in result.output
        assert "save" in result.output
        assert "resume" in result.output
        assert "learn" in result.output
        assert "recall" in result.output
        assert "team" in result.output
        assert "status" in result.output
        assert "history" in result.output

    def test_version_command(self, cli_runner):
        """CLI should display version."""
        result = cli_runner.invoke(flow.cli, ['--version'])

        assert result.exit_code == 0
        assert "0.1.0" in result.output


class TestSaveCommand:
    """Tests for the save command."""

    def test_save_help(self, cli_runner):
        """save command should display help."""
        result = cli_runner.invoke(flow.cli, ['save', '--help'])

        assert result.exit_code == 0
        assert "--message" in result.output or "-m" in result.output
        assert "--tag" in result.output or "-t" in result.output
        assert "--quiet" in result.output or "-q" in result.output

    def test_save_basic(self, cli_runner, tmp_path):
        """save command should save session."""
        with mock.patch('flow_cli.capture') as mock_capture, \
             mock.patch('flow_cli.memory') as mock_memory, \
             mock.patch('flow_cli.backboard_client') as mock_backboard:

            mock_capture.build_session.return_value = {
                "id": "session_test",
                "timestamp": "2024-01-01T12:00:00",
                "context": {"summary": "Test session"},
                "git": {"branch": "main"},
                "metadata": {"tags": []}
            }
            mock_memory.save_session.return_value = "session_test"
            mock_backboard.run_async.return_value = None

            result = cli_runner.invoke(flow.cli, ['save'])

            assert result.exit_code == 0
            mock_capture.build_session.assert_called_once()
            mock_memory.save_session.assert_called_once()

    def test_save_with_message(self, cli_runner):
        """save command should accept message."""
        with mock.patch('flow_cli.capture') as mock_capture, \
             mock.patch('flow_cli.memory') as mock_memory, \
             mock.patch('flow_cli.backboard_client'):

            mock_capture.build_session.return_value = {
                "id": "session_test",
                "timestamp": "2024-01-01T12:00:00",
                "context": {"summary": "Test"},
                "git": {"branch": "main"},
                "metadata": {"tags": []}
            }
            mock_memory.save_session.return_value = "session_test"

            result = cli_runner.invoke(flow.cli, ['save', '-m', 'Test message'])

            assert result.exit_code == 0
            call_args = mock_capture.build_session.call_args
            assert call_args.kwargs.get('user_message') == 'Test message'

    def test_save_with_tags(self, cli_runner):
        """save command should accept multiple tags."""
        with mock.patch('flow_cli.capture') as mock_capture, \
             mock.patch('flow_cli.memory') as mock_memory, \
             mock.patch('flow_cli.backboard_client'):

            mock_capture.build_session.return_value = {
                "id": "session_test",
                "timestamp": "2024-01-01T12:00:00",
                "context": {"summary": "Test"},
                "git": {"branch": "main"},
                "metadata": {"tags": ["auth", "jwt"]}
            }
            mock_memory.save_session.return_value = "session_test"

            result = cli_runner.invoke(flow.cli, ['save', '-t', 'auth', '-t', 'jwt'])

            assert result.exit_code == 0
            call_args = mock_capture.build_session.call_args
            assert 'auth' in call_args.kwargs.get('tags', [])
            assert 'jwt' in call_args.kwargs.get('tags', [])


class TestResumeCommand:
    """Tests for the resume command."""

    def test_resume_help(self, cli_runner):
        """resume command should display help."""
        result = cli_runner.invoke(flow.cli, ['resume', '--help'])

        assert result.exit_code == 0
        assert "--session" in result.output or "-s" in result.output
        assert "--pick" in result.output or "-p" in result.output
        assert "--raw" in result.output
        assert "--copy" in result.output

    def test_resume_no_sessions(self, cli_runner):
        """resume command should handle no sessions gracefully."""
        with mock.patch('flow_cli.memory') as mock_memory:
            mock_memory.get_latest_session.return_value = None

            result = cli_runner.invoke(flow.cli, ['resume'])

            assert result.exit_code == 0
            assert "No saved sessions" in result.output or "no sessions" in result.output.lower()

    def test_resume_with_session(self, cli_runner):
        """resume command should restore session context."""
        with mock.patch('flow_cli.memory') as mock_memory, \
             mock.patch('flow_cli.restore') as mock_restore:

            mock_memory.get_latest_session.return_value = {
                "id": "session_test",
                "timestamp": "2024-01-01T12:00:00",
                "context": {
                    "summary": "Working on feature",
                    "hypothesis": "Test approach",
                    "files": ["test.py"],
                    "next_steps": ["Write tests"]
                },
                "git": {"branch": "main"},
                "learnings": []
            }
            mock_restore.get_changes_since.return_value = {
                "elapsed": "2h",
                "commits": [],
                "files_changed": [],
                "is_stale": False
            }
            mock_restore.detect_conflicts.return_value = []
            mock_restore.generate_restoration_message.return_value = "Welcome back!"

            result = cli_runner.invoke(flow.cli, ['resume'])

            assert result.exit_code == 0
            mock_memory.get_latest_session.assert_called_once()


class TestLearnCommand:
    """Tests for the learn command."""

    def test_learn_help(self, cli_runner):
        """learn command should display help."""
        result = cli_runner.invoke(flow.cli, ['learn', '--help'])

        assert result.exit_code == 0
        assert "--tag" in result.output or "-t" in result.output
        assert "--team" in result.output

    def test_learn_basic(self, cli_runner):
        """learn command should store learning."""
        with mock.patch('flow_cli.memory') as mock_memory, \
             mock.patch('flow_cli.backboard_client'):

            mock_memory.save_learning.return_value = "learning_test"
            mock_memory.get_config.return_value = {"user": "testuser"}

            result = cli_runner.invoke(flow.cli, ['learn', 'Test learning'])

            assert result.exit_code == 0
            mock_memory.save_learning.assert_called_once()

    def test_learn_with_tags(self, cli_runner):
        """learn command should accept tags."""
        with mock.patch('flow_cli.memory') as mock_memory, \
             mock.patch('flow_cli.backboard_client'):

            mock_memory.save_learning.return_value = "learning_test"
            mock_memory.get_config.return_value = {"user": "testuser"}

            result = cli_runner.invoke(flow.cli, ['learn', 'Auth insight', '-t', 'auth', '-t', 'security'])

            assert result.exit_code == 0
            call_args = mock_memory.save_learning.call_args
            learning = call_args.args[0] if call_args.args else call_args.kwargs.get('learning')
            if isinstance(learning, dict):
                assert 'auth' in learning.get('tags', [])


class TestRecallCommand:
    """Tests for the recall command."""

    def test_recall_help(self, cli_runner):
        """recall command should display help."""
        result = cli_runner.invoke(flow.cli, ['recall', '--help'])

        assert result.exit_code == 0
        assert "--tag" in result.output or "-t" in result.output
        assert "--limit" in result.output

    def test_recall_basic(self, cli_runner, monkeypatch):
        """recall command should search learnings."""
        # Clear Backboard env vars to use local search
        monkeypatch.delenv("BACKBOARD_PERSONAL_THREAD_ID", raising=False)

        with mock.patch('flow_cli.memory') as mock_memory, \
             mock.patch('flow_cli.restore') as mock_restore:

            mock_memory.search_learnings.return_value = [
                {"text": "Auth learning", "tags": ["auth"], "timestamp": "2024-01-01T12:00:00"}
            ]
            mock_restore.calculate_time_elapsed.return_value = "1h"

            result = cli_runner.invoke(flow.cli, ['recall', 'authentication'])

            assert result.exit_code == 0


class TestTeamCommand:
    """Tests for the team command."""

    def test_team_help(self, cli_runner):
        """team command should display help."""
        result = cli_runner.invoke(flow.cli, ['team', '--help'])

        assert result.exit_code == 0
        assert "--tag" in result.output or "-t" in result.output
        assert "--limit" in result.output

    def test_team_no_config(self, cli_runner):
        """team command should handle missing team config."""
        with mock.patch('flow_cli.memory') as mock_memory:
            mock_memory.get_config.return_value = {"backboard": {}}

            result = cli_runner.invoke(flow.cli, ['team', 'query'])

            # Should exit gracefully with info about team setup
            assert result.exit_code == 0 or "team" in result.output.lower()


class TestStatusCommand:
    """Tests for the status command."""

    def test_status_help(self, cli_runner):
        """status command should display help."""
        result = cli_runner.invoke(flow.cli, ['status', '--help'])

        assert result.exit_code == 0

    def test_status_basic(self, cli_runner):
        """status command should show status information."""
        with mock.patch('flow_cli.memory') as mock_memory, \
             mock.patch('flow_cli.capture') as mock_capture, \
             mock.patch('flow_cli.backboard_client') as mock_backboard:

            mock_memory.get_stats.return_value = {
                "sessions_count": 5,
                "personal_learnings": 10,
                "team_learnings": 3,
                "total_learnings": 13
            }
            mock_memory.get_latest_session.return_value = {
                "id": "session_test",
                "timestamp": "2024-01-01T12:00:00",
                "context": {"summary": "Working on feature"},
                "git": {"branch": "main"}
            }
            mock_memory.get_config.return_value = {}
            mock_capture.capture_git_state.return_value = {
                "is_git": True,
                "branch": "main",
                "uncommitted_files": []
            }
            mock_backboard.run_async.return_value = True

            result = cli_runner.invoke(flow.cli, ['status'])

            assert result.exit_code == 0


class TestHistoryCommand:
    """Tests for the history command."""

    def test_history_help(self, cli_runner):
        """history command should display help."""
        result = cli_runner.invoke(flow.cli, ['history', '--help'])

        assert result.exit_code == 0
        assert "--limit" in result.output or "-n" in result.output
        assert "--all" in result.output
        assert "--branch" in result.output

    def test_history_basic(self, cli_runner):
        """history command should list sessions."""
        with mock.patch('flow_cli.memory') as mock_memory:
            mock_memory.list_sessions.return_value = [
                {
                    "id": "session_1",
                    "timestamp": "2024-01-01T12:00:00",
                    "branch": "main",
                    "summary": "First session"
                },
                {
                    "id": "session_2",
                    "timestamp": "2024-01-01T13:00:00",
                    "branch": "feature",
                    "summary": "Second session"
                }
            ]

            result = cli_runner.invoke(flow.cli, ['history'])

            assert result.exit_code == 0
            mock_memory.list_sessions.assert_called_once()

    def test_history_with_limit(self, cli_runner):
        """history command should respect limit."""
        with mock.patch('flow_cli.memory') as mock_memory:
            mock_memory.list_sessions.return_value = []

            result = cli_runner.invoke(flow.cli, ['history', '-n', '5'])

            assert result.exit_code == 0
            call_args = mock_memory.list_sessions.call_args
            assert call_args.kwargs.get('limit') == 5

    def test_history_filter_by_branch(self, cli_runner):
        """history command should filter by branch."""
        with mock.patch('flow_cli.memory') as mock_memory:
            mock_memory.list_sessions.return_value = []

            result = cli_runner.invoke(flow.cli, ['history', '--branch', 'main'])

            assert result.exit_code == 0
            call_args = mock_memory.list_sessions.call_args
            assert call_args.kwargs.get('branch') == 'main'

    def test_history_empty(self, cli_runner):
        """history command should handle no sessions."""
        with mock.patch('flow_cli.memory') as mock_memory:
            mock_memory.list_sessions.return_value = []

            result = cli_runner.invoke(flow.cli, ['history'])

            assert result.exit_code == 0
            assert "No sessions" in result.output or "no saved sessions" in result.output.lower()


class TestInjectCommand:
    """Tests for the inject command."""

    def test_inject_help(self, cli_runner):
        """inject command should display help."""
        result = cli_runner.invoke(flow.cli, ['inject', '--help'])

        assert result.exit_code == 0
        assert "--quiet" in result.output or "-q" in result.output
        assert "--level" in result.output or "-l" in result.output
        assert "--save-state" in result.output

    def test_inject_quiet_mode(self, cli_runner, tmp_path, monkeypatch):
        """inject command in quiet mode outputs plain text."""
        monkeypatch.chdir(tmp_path)
        monkeypatch.delenv("BACKBOARD_PERSONAL_THREAD_ID", raising=False)

        # Create .git marker
        (tmp_path / ".git").mkdir()

        # Patch at the inject module level
        with mock.patch('inject.generate_injection_sync') as mock_gen:
            mock_gen.return_value = "Plain text output"

            result = cli_runner.invoke(flow.cli, ['inject', '--quiet'])

            assert result.exit_code == 0
            assert "Plain text output" in result.output

    def test_inject_save_state(self, cli_runner, tmp_path, monkeypatch):
        """inject --save-state saves current state."""
        monkeypatch.chdir(tmp_path)

        # Create .git marker
        (tmp_path / ".git").mkdir()

        with mock.patch('inject.save_current_state_sync') as mock_save:
            mock_save.return_value = {
                "goal": "Saved goal",
                "status": "in_progress",
                "now": "Working",
            }

            result = cli_runner.invoke(flow.cli, ['inject', '--save-state'])

            assert result.exit_code == 0
            mock_save.assert_called_once()

    def test_inject_level_options(self, cli_runner):
        """inject command should accept level options."""
        result = cli_runner.invoke(flow.cli, ['inject', '--help'])

        # Level should be documented
        assert "L0" in result.output or "L1" in result.output


class TestSetupCommand:
    """Tests for the setup command."""

    def test_setup_help(self, cli_runner):
        """setup command should display help."""
        result = cli_runner.invoke(flow.cli, ['setup', '--help'])

        assert result.exit_code == 0
        assert "--global" in result.output or "-g" in result.output
        assert "--check" in result.output or "-c" in result.output
        assert "--force" in result.output or "-f" in result.output

    def test_setup_creates_directories(self, cli_runner, tmp_path, monkeypatch):
        """setup command should create required directories."""
        monkeypatch.chdir(tmp_path)

        # Create .git marker so project is detected
        (tmp_path / ".git").mkdir()

        result = cli_runner.invoke(flow.cli, ['setup'])

        assert result.exit_code == 0

        # Check directories were created
        assert (tmp_path / ".flow-guardian").exists()
        assert (tmp_path / ".flow-guardian" / "handoff.yaml").exists()
        assert (tmp_path / ".flow-guardian" / "config.yaml").exists()
        assert (tmp_path / ".claude" / "hooks").exists()
        assert (tmp_path / ".claude" / "hooks" / "flow-inject.sh").exists()
        assert (tmp_path / ".claude" / "hooks" / "flow-precompact.sh").exists()
        assert (tmp_path / ".claude" / "settings.json").exists()

    def test_setup_check_mode(self, cli_runner, tmp_path, monkeypatch):
        """setup --check should report status without modifying."""
        monkeypatch.chdir(tmp_path)

        result = cli_runner.invoke(flow.cli, ['setup', '--check'])

        assert result.exit_code == 0
        assert "Status" in result.output

        # Should not create directories in check mode
        assert not (tmp_path / ".flow-guardian").exists()

    def test_setup_force_overwrites(self, cli_runner, tmp_path, monkeypatch):
        """setup --force should overwrite existing files."""
        monkeypatch.chdir(tmp_path)

        # Create existing files
        fg_dir = tmp_path / ".flow-guardian"
        fg_dir.mkdir()
        (fg_dir / "handoff.yaml").write_text("old content")

        result = cli_runner.invoke(flow.cli, ['setup', '--force'])

        assert result.exit_code == 0

        # File should be overwritten
        content = (fg_dir / "handoff.yaml").read_text()
        assert "old content" not in content
        assert "Flow Guardian" in content or "goal" in content

    def test_setup_global_mode(self, cli_runner, tmp_path, monkeypatch):
        """setup --global should install hooks to home directory only."""
        monkeypatch.chdir(tmp_path)
        home_dir = tmp_path / "fakehome"
        home_dir.mkdir()
        monkeypatch.setattr("pathlib.Path.home", lambda: home_dir)

        result = cli_runner.invoke(flow.cli, ['setup', '--global'])

        assert result.exit_code == 0

        # Global mode should NOT create .flow-guardian/
        assert not (home_dir / ".flow-guardian").exists()

        # Should create hooks in home .claude directory
        assert (home_dir / ".claude" / "hooks").exists()
        assert (home_dir / ".claude" / "hooks" / "flow-inject.sh").exists()
        assert (home_dir / ".claude" / "hooks" / "flow-precompact.sh").exists()
        assert (home_dir / ".claude" / "settings.json").exists()

    def test_setup_hook_scripts_executable(self, cli_runner, tmp_path, monkeypatch):
        """setup should create hook scripts with executable permissions."""
        import stat
        monkeypatch.chdir(tmp_path)
        (tmp_path / ".git").mkdir()

        result = cli_runner.invoke(flow.cli, ['setup'])

        assert result.exit_code == 0

        # Check scripts have executable permission
        inject_hook = tmp_path / ".claude" / "hooks" / "flow-inject.sh"
        precompact_hook = tmp_path / ".claude" / "hooks" / "flow-precompact.sh"

        assert inject_hook.exists()
        assert precompact_hook.exists()

        # Check that executable bit is set (owner, group, or other)
        inject_mode = inject_hook.stat().st_mode
        precompact_mode = precompact_hook.stat().st_mode

        assert inject_mode & (stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
        assert precompact_mode & (stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

    def test_setup_hook_script_contents(self, cli_runner, tmp_path, monkeypatch):
        """setup should create hook scripts with correct contents."""
        monkeypatch.chdir(tmp_path)
        (tmp_path / ".git").mkdir()

        result = cli_runner.invoke(flow.cli, ['setup'])

        assert result.exit_code == 0

        # Check inject hook content
        inject_content = (tmp_path / ".claude" / "hooks" / "flow-inject.sh").read_text()
        assert "#!/bin/bash" in inject_content
        assert ".flow-guardian" in inject_content
        assert "flow inject" in inject_content
        assert "--quiet" in inject_content

        # Check precompact hook content
        precompact_content = (tmp_path / ".claude" / "hooks" / "flow-precompact.sh").read_text()
        assert "#!/bin/bash" in precompact_content
        assert ".flow-guardian" in precompact_content
        assert "flow inject --save-state" in precompact_content

    def test_setup_environment_variable_warnings(self, cli_runner, tmp_path, monkeypatch):
        """setup should warn about missing environment variables."""
        monkeypatch.chdir(tmp_path)
        (tmp_path / ".git").mkdir()

        # Clear environment variables
        monkeypatch.delenv("CEREBRAS_API_KEY", raising=False)
        monkeypatch.delenv("BACKBOARD_API_KEY", raising=False)
        monkeypatch.delenv("BACKBOARD_PERSONAL_THREAD_ID", raising=False)

        result = cli_runner.invoke(flow.cli, ['setup'])

        assert result.exit_code == 0
        # Output should indicate missing env vars
        assert "not set" in result.output or "missing" in result.output.lower()

    def test_setup_environment_variables_set(self, cli_runner, tmp_path, monkeypatch):
        """setup should show success when environment variables are set."""
        monkeypatch.chdir(tmp_path)
        (tmp_path / ".git").mkdir()

        # Set environment variables
        monkeypatch.setenv("CEREBRAS_API_KEY", "test-key")
        monkeypatch.setenv("BACKBOARD_API_KEY", "test-key")
        monkeypatch.setenv("BACKBOARD_PERSONAL_THREAD_ID", "test-thread")

        result = cli_runner.invoke(flow.cli, ['setup'])

        assert result.exit_code == 0
        # Should show checkmarks for set vars
        assert "CEREBRAS_API_KEY" in result.output
        assert "BACKBOARD_API_KEY" in result.output

    def test_setup_settings_json_merge(self, cli_runner, tmp_path, monkeypatch):
        """setup should merge hooks into existing settings.json without hooks."""
        import json
        monkeypatch.chdir(tmp_path)
        (tmp_path / ".git").mkdir()

        # Create existing settings without hooks
        claude_dir = tmp_path / ".claude"
        claude_dir.mkdir()
        existing_settings = {"other_setting": "value", "another": True}
        (claude_dir / "settings.json").write_text(json.dumps(existing_settings))

        result = cli_runner.invoke(flow.cli, ['setup'])

        assert result.exit_code == 0

        # Check settings were merged
        settings = json.loads((claude_dir / "settings.json").read_text())
        assert "hooks" in settings
        assert "other_setting" in settings
        assert settings["other_setting"] == "value"

    def test_setup_settings_json_existing_hooks(self, cli_runner, tmp_path, monkeypatch):
        """setup should warn when settings.json already has hooks."""
        import json
        monkeypatch.chdir(tmp_path)
        (tmp_path / ".git").mkdir()

        # Create existing settings with hooks
        claude_dir = tmp_path / ".claude"
        claude_dir.mkdir()
        existing_settings = {"hooks": {"other_hook": []}}
        (claude_dir / "settings.json").write_text(json.dumps(existing_settings))

        result = cli_runner.invoke(flow.cli, ['setup'])

        assert result.exit_code == 0
        # Should warn about manual merge
        assert "manual merge" in result.output.lower() or "exists" in result.output.lower()

    def test_setup_existing_files_without_force(self, cli_runner, tmp_path, monkeypatch):
        """setup should skip existing files without --force."""
        monkeypatch.chdir(tmp_path)
        (tmp_path / ".git").mkdir()

        # Create existing files
        fg_dir = tmp_path / ".flow-guardian"
        fg_dir.mkdir()
        original_content = "original handoff content"
        (fg_dir / "handoff.yaml").write_text(original_content)

        result = cli_runner.invoke(flow.cli, ['setup'])

        assert result.exit_code == 0
        # File should NOT be overwritten
        content = (fg_dir / "handoff.yaml").read_text()
        assert content == original_content

    def test_setup_handoff_yaml_contents(self, cli_runner, tmp_path, monkeypatch):
        """setup should create handoff.yaml with correct initial structure."""
        monkeypatch.chdir(tmp_path)
        (tmp_path / ".git").mkdir()

        result = cli_runner.invoke(flow.cli, ['setup'])

        assert result.exit_code == 0

        content = (tmp_path / ".flow-guardian" / "handoff.yaml").read_text()
        assert "goal:" in content
        assert "status:" in content
        assert "now:" in content
        assert "timestamp:" in content

    def test_setup_config_yaml_contents(self, cli_runner, tmp_path, monkeypatch):
        """setup should create config.yaml with correct defaults."""
        monkeypatch.chdir(tmp_path)
        (tmp_path / ".git").mkdir()

        result = cli_runner.invoke(flow.cli, ['setup'])

        assert result.exit_code == 0

        content = (tmp_path / ".flow-guardian" / "config.yaml").read_text()
        assert "tldr_level: L1" in content
        assert "include_files: true" in content
        assert "auto_inject: true" in content

    def test_setup_settings_json_structure(self, cli_runner, tmp_path, monkeypatch):
        """setup should create settings.json with correct hook structure."""
        import json
        monkeypatch.chdir(tmp_path)
        (tmp_path / ".git").mkdir()

        result = cli_runner.invoke(flow.cli, ['setup'])

        assert result.exit_code == 0

        settings = json.loads((tmp_path / ".claude" / "settings.json").read_text())
        assert "hooks" in settings
        assert "SessionStart" in settings["hooks"]
        assert "PreCompact" in settings["hooks"]

    def test_setup_check_mode_with_env_vars(self, cli_runner, tmp_path, monkeypatch):
        """setup --check should display environment variable status."""
        monkeypatch.chdir(tmp_path)
        monkeypatch.setenv("CEREBRAS_API_KEY", "test-key")
        monkeypatch.delenv("BACKBOARD_API_KEY", raising=False)

        result = cli_runner.invoke(flow.cli, ['setup', '--check'])

        assert result.exit_code == 0
        # Should show status of env vars
        assert "CEREBRAS_API_KEY" in result.output
        assert "BACKBOARD_API_KEY" in result.output

    def test_setup_check_mode_with_existing_setup(self, cli_runner, tmp_path, monkeypatch):
        """setup --check should show existing setup status."""
        monkeypatch.chdir(tmp_path)

        # Create existing setup
        (tmp_path / ".flow-guardian").mkdir()
        (tmp_path / ".flow-guardian" / "handoff.yaml").write_text("test")
        (tmp_path / ".claude" / "hooks").mkdir(parents=True)
        (tmp_path / ".claude" / "settings.json").write_text("{}")

        result = cli_runner.invoke(flow.cli, ['setup', '--check'])

        assert result.exit_code == 0
        assert "exists" in result.output.lower() or "✓" in result.output

    def test_setup_global_check_mode(self, cli_runner, tmp_path, monkeypatch):
        """setup --global --check should check global setup."""
        monkeypatch.chdir(tmp_path)
        home_dir = tmp_path / "fakehome"
        home_dir.mkdir()
        monkeypatch.setattr("pathlib.Path.home", lambda: home_dir)

        result = cli_runner.invoke(flow.cli, ['setup', '--global', '--check'])

        assert result.exit_code == 0
        assert "Global" in result.output or "~/.claude" in result.output

    def test_setup_idempotent(self, cli_runner, tmp_path, monkeypatch):
        """setup should be idempotent - running twice should not error."""
        monkeypatch.chdir(tmp_path)
        (tmp_path / ".git").mkdir()

        # Run setup twice
        result1 = cli_runner.invoke(flow.cli, ['setup'])
        result2 = cli_runner.invoke(flow.cli, ['setup'])

        assert result1.exit_code == 0
        assert result2.exit_code == 0

        # Files should still exist
        assert (tmp_path / ".flow-guardian" / "handoff.yaml").exists()
        assert (tmp_path / ".claude" / "hooks" / "flow-inject.sh").exists()
