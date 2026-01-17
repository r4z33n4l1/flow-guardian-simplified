"""Tests for the session_parser.py module."""
import json
import os
import tempfile
from datetime import datetime
from pathlib import Path
from unittest import mock

import pytest

import session_parser


class TestGetProjectDir:
    """Tests for get_project_dir function."""

    def test_converts_path_to_project_name(self):
        """Should convert slashes to dashes."""
        cwd = "/Users/test/projects/myapp"
        result = session_parser.get_project_dir(cwd)
        assert result == session_parser.CLAUDE_PROJECTS_DIR / "-Users-test-projects-myapp"

    def test_handles_root_path(self):
        """Should handle root path correctly."""
        cwd = "/"
        result = session_parser.get_project_dir(cwd)
        assert result == session_parser.CLAUDE_PROJECTS_DIR / "-"


class TestGetSessionsIndex:
    """Tests for get_sessions_index function."""

    def test_returns_empty_dict_when_no_file(self, tmp_path):
        """Should return empty dict when index doesn't exist."""
        result = session_parser.get_sessions_index(tmp_path)
        assert result == {}

    def test_reads_existing_index(self, tmp_path):
        """Should read and return index contents."""
        index_data = {"session1": {"created": "2024-01-01"}}
        index_path = tmp_path / "sessions-index.json"
        index_path.write_text(json.dumps(index_data))

        result = session_parser.get_sessions_index(tmp_path)
        assert result == index_data


class TestGetActiveSession:
    """Tests for get_active_session function."""

    def test_returns_none_when_no_sessions(self, tmp_path):
        """Should return None when no jsonl files exist."""
        result = session_parser.get_active_session(tmp_path)
        assert result is None

    def test_returns_most_recent_session(self, tmp_path):
        """Should return the most recently modified session."""
        # Create two session files with different modification times
        old_session = tmp_path / "old_session.jsonl"
        new_session = tmp_path / "new_session.jsonl"

        old_session.write_text('{"type": "user"}')
        new_session.write_text('{"type": "user"}')

        # Make old_session actually older by touching new_session
        import time
        time.sleep(0.01)
        new_session.write_text('{"type": "user", "updated": true}')

        result = session_parser.get_active_session(tmp_path)
        assert result == "new_session"


class TestGetSessionPath:
    """Tests for get_session_path function."""

    def test_returns_correct_path(self, tmp_path):
        """Should return path to session JSONL file."""
        result = session_parser.get_session_path(tmp_path, "my_session")
        assert result == tmp_path / "my_session.jsonl"


class TestParseSessionMessages:
    """Tests for parse_session_messages function."""

    def test_handles_nonexistent_file(self, tmp_path):
        """Should return empty iterator for nonexistent file."""
        result = list(session_parser.parse_session_messages(tmp_path / "nonexistent.jsonl"))
        assert result == []

    def test_parses_user_messages(self, tmp_path):
        """Should parse user messages correctly."""
        session_file = tmp_path / "test.jsonl"
        session_file.write_text(json.dumps({
            "type": "user",
            "message": {"role": "user", "content": "Hello!"},
            "cwd": "/test",
            "gitBranch": "main"
        }))

        result = list(session_parser.parse_session_messages(session_file))
        assert len(result) == 1
        assert result[0]["role"] == "user"
        assert result[0]["content"] == "Hello!"
        assert result[0]["cwd"] == "/test"

    def test_parses_assistant_messages(self, tmp_path):
        """Should parse assistant messages correctly."""
        session_file = tmp_path / "test.jsonl"
        session_file.write_text(json.dumps({
            "type": "assistant",
            "message": {"role": "assistant", "content": "Hi there!"}
        }))

        result = list(session_parser.parse_session_messages(session_file))
        assert len(result) == 1
        assert result[0]["role"] == "assistant"
        assert result[0]["content"] == "Hi there!"

    def test_handles_structured_content(self, tmp_path):
        """Should handle structured content blocks."""
        session_file = tmp_path / "test.jsonl"
        session_file.write_text(json.dumps({
            "type": "assistant",
            "message": {
                "role": "assistant",
                "content": [
                    {"type": "text", "text": "Let me help."},
                    {"type": "tool_use", "name": "read_file"},
                    {"type": "text", "text": "Here's what I found."}
                ]
            }
        }))

        result = list(session_parser.parse_session_messages(session_file))
        assert len(result) == 1
        assert "Let me help." in result[0]["content"]
        assert "[Used tool: read_file]" in result[0]["content"]
        assert "Here's what I found." in result[0]["content"]

    def test_skips_lines_before_since_line(self, tmp_path):
        """Should skip lines before since_line parameter."""
        session_file = tmp_path / "test.jsonl"
        lines = [
            json.dumps({"type": "user", "message": {"role": "user", "content": "Line 0"}}),
            json.dumps({"type": "user", "message": {"role": "user", "content": "Line 1"}}),
            json.dumps({"type": "user", "message": {"role": "user", "content": "Line 2"}}),
        ]
        session_file.write_text("\n".join(lines))

        result = list(session_parser.parse_session_messages(session_file, since_line=2))
        assert len(result) == 1
        assert result[0]["content"] == "Line 2"

    def test_skips_invalid_json(self, tmp_path):
        """Should skip lines with invalid JSON."""
        session_file = tmp_path / "test.jsonl"
        lines = [
            json.dumps({"type": "user", "message": {"role": "user", "content": "Valid"}}),
            "not valid json",
            json.dumps({"type": "user", "message": {"role": "user", "content": "Also valid"}}),
        ]
        session_file.write_text("\n".join(lines))

        result = list(session_parser.parse_session_messages(session_file))
        assert len(result) == 2

    def test_skips_empty_content(self, tmp_path):
        """Should skip messages with empty content."""
        session_file = tmp_path / "test.jsonl"
        lines = [
            json.dumps({"type": "user", "message": {"role": "user", "content": ""}}),
            json.dumps({"type": "user", "message": {"role": "user", "content": "Has content"}}),
        ]
        session_file.write_text("\n".join(lines))

        result = list(session_parser.parse_session_messages(session_file))
        assert len(result) == 1
        assert result[0]["content"] == "Has content"


class TestGetConversationText:
    """Tests for get_conversation_text function."""

    def test_returns_formatted_text(self, tmp_path):
        """Should return formatted conversation text."""
        session_file = tmp_path / "test.jsonl"
        lines = [
            json.dumps({"type": "user", "message": {"role": "user", "content": "Hello"}}),
            json.dumps({"type": "assistant", "message": {"role": "assistant", "content": "Hi"}}),
        ]
        session_file.write_text("\n".join(lines))

        text, last_line = session_parser.get_conversation_text(session_file)
        assert "Human: Hello" in text
        assert "Assistant: Hi" in text
        assert last_line == 1

    def test_respects_since_line(self, tmp_path):
        """Should start from since_line."""
        session_file = tmp_path / "test.jsonl"
        lines = [
            json.dumps({"type": "user", "message": {"role": "user", "content": "First"}}),
            json.dumps({"type": "user", "message": {"role": "user", "content": "Second"}}),
        ]
        session_file.write_text("\n".join(lines))

        text, last_line = session_parser.get_conversation_text(session_file, since_line=1)
        assert "First" not in text
        assert "Second" in text

    def test_respects_max_chars(self, tmp_path):
        """Should respect max_chars limit."""
        session_file = tmp_path / "test.jsonl"
        # Create a very long message
        long_content = "A" * 1000
        lines = [
            json.dumps({"type": "user", "message": {"role": "user", "content": long_content}}),
            json.dumps({"type": "user", "message": {"role": "user", "content": "Second"}}),
        ]
        session_file.write_text("\n".join(lines))

        text, last_line = session_parser.get_conversation_text(session_file, max_chars=500)
        # Should only get first message (truncated)
        assert "Second" not in text
        assert last_line == 0


class TestFindAllSessions:
    """Tests for find_all_sessions function."""

    def test_returns_empty_list_when_no_project_dir(self, monkeypatch, tmp_path):
        """Should return empty list when project dir doesn't exist."""
        monkeypatch.setattr(session_parser, 'CLAUDE_PROJECTS_DIR', tmp_path / "nonexistent")
        result = session_parser.find_all_sessions("/test/path")
        assert result == []

    def test_returns_sorted_sessions(self, monkeypatch, tmp_path):
        """Should return sessions sorted by modification time."""
        project_dir = tmp_path / "-test-path"
        project_dir.mkdir(parents=True)
        monkeypatch.setattr(session_parser, 'CLAUDE_PROJECTS_DIR', tmp_path)

        # Create sessions
        old = project_dir / "old.jsonl"
        new = project_dir / "new.jsonl"
        old.write_text("{}")
        new.write_text("{}")

        import time
        time.sleep(0.01)
        new.write_text('{"updated": true}')

        result = session_parser.find_all_sessions("/test/path")
        assert len(result) == 2
        # Newest should be first
        assert result[0]["session_id"] == "new"
        assert result[1]["session_id"] == "old"


class TestGetCurrentSessionForCwd:
    """Tests for get_current_session_for_cwd function."""

    def test_returns_none_when_no_project_dir(self, monkeypatch, tmp_path):
        """Should return None when project dir doesn't exist."""
        monkeypatch.setattr(session_parser, 'CLAUDE_PROJECTS_DIR', tmp_path / "nonexistent")
        result = session_parser.get_current_session_for_cwd("/test/path")
        assert result is None

    def test_returns_none_when_no_sessions(self, monkeypatch, tmp_path):
        """Should return None when no sessions exist."""
        project_dir = tmp_path / "-test-path"
        project_dir.mkdir(parents=True)
        monkeypatch.setattr(session_parser, 'CLAUDE_PROJECTS_DIR', tmp_path)

        result = session_parser.get_current_session_for_cwd("/test/path")
        assert result is None

    def test_returns_session_path(self, monkeypatch, tmp_path):
        """Should return path to most recent session."""
        project_dir = tmp_path / "-test-path"
        project_dir.mkdir(parents=True)
        session_file = project_dir / "session1.jsonl"
        session_file.write_text("{}")
        monkeypatch.setattr(session_parser, 'CLAUDE_PROJECTS_DIR', tmp_path)

        result = session_parser.get_current_session_for_cwd("/test/path")
        assert result == session_file

    def test_uses_cwd_when_none_provided(self, monkeypatch, tmp_path):
        """Should use os.getcwd() when cwd is None."""
        current_dir = os.getcwd()
        project_name = current_dir.replace("/", "-")
        project_dir = tmp_path / project_name
        project_dir.mkdir(parents=True)
        session_file = project_dir / "current.jsonl"
        session_file.write_text("{}")
        monkeypatch.setattr(session_parser, 'CLAUDE_PROJECTS_DIR', tmp_path)

        result = session_parser.get_current_session_for_cwd(None)
        assert result == session_file
