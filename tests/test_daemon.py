"""Tests for the daemon.py module."""
import asyncio
import json
import os
import signal
import tempfile
from datetime import datetime
from pathlib import Path
from unittest import mock

import pytest

import daemon


class TestLogging:
    """Tests for log function."""

    def test_log_creates_directory(self, tmp_path, monkeypatch):
        """Should create daemon state directory if it doesn't exist."""
        log_dir = tmp_path / "daemon"
        monkeypatch.setattr(daemon, 'DAEMON_STATE_DIR', log_dir)
        monkeypatch.setattr(daemon, 'LOG_FILE', log_dir / "daemon.log")

        daemon.log("Test message")

        assert log_dir.exists()
        assert (log_dir / "daemon.log").exists()

    def test_log_writes_timestamp(self, tmp_path, monkeypatch):
        """Should write log with timestamp."""
        log_dir = tmp_path / "daemon"
        log_file = log_dir / "daemon.log"
        monkeypatch.setattr(daemon, 'DAEMON_STATE_DIR', log_dir)
        monkeypatch.setattr(daemon, 'LOG_FILE', log_file)

        daemon.log("Test message")

        content = log_file.read_text()
        # Should have timestamp format [YYYY-MM-DD HH:MM:SS]
        assert "[" in content
        assert "]" in content
        assert "Test message" in content


class TestStateManagement:
    """Tests for load_state and save_state functions."""

    def test_load_state_returns_default_when_no_file(self, tmp_path, monkeypatch):
        """Should return default state when state file doesn't exist."""
        monkeypatch.setattr(daemon, 'STATE_FILE', tmp_path / "nonexistent.json")

        result = daemon.load_state()

        assert result["sessions"] == {}
        assert result["started_at"] is None
        assert result["extractions_count"] == 0

    def test_load_state_reads_existing_file(self, tmp_path, monkeypatch):
        """Should read existing state file."""
        state_file = tmp_path / "state.json"
        state_data = {
            "sessions": {"sess1": {"last_line": 10}},
            "started_at": "2024-01-01T00:00:00",
            "extractions_count": 5
        }
        state_file.write_text(json.dumps(state_data))
        monkeypatch.setattr(daemon, 'STATE_FILE', state_file)

        result = daemon.load_state()

        assert result["sessions"] == {"sess1": {"last_line": 10}}
        assert result["extractions_count"] == 5

    def test_save_state_creates_directory(self, tmp_path, monkeypatch):
        """Should create state directory if it doesn't exist."""
        state_dir = tmp_path / "daemon"
        state_file = state_dir / "state.json"
        monkeypatch.setattr(daemon, 'DAEMON_STATE_DIR', state_dir)
        monkeypatch.setattr(daemon, 'STATE_FILE', state_file)

        daemon.save_state({"sessions": {}, "extractions_count": 0})

        assert state_dir.exists()
        assert state_file.exists()

    def test_save_state_writes_json(self, tmp_path, monkeypatch):
        """Should write valid JSON to state file."""
        state_dir = tmp_path / "daemon"
        state_file = state_dir / "state.json"
        monkeypatch.setattr(daemon, 'DAEMON_STATE_DIR', state_dir)
        monkeypatch.setattr(daemon, 'STATE_FILE', state_file)

        state_data = {"sessions": {"s1": {"last_line": 5}}, "extractions_count": 3}
        daemon.save_state(state_data)

        content = json.loads(state_file.read_text())
        assert content["extractions_count"] == 3


class TestExtractJsonFromResponse:
    """Tests for _extract_json_from_response function."""

    def test_extracts_direct_json_array(self):
        """Should parse direct JSON array."""
        response = '[{"category": "learning", "insight": "test"}]'
        result = daemon._extract_json_from_response(response)
        assert len(result) == 1
        assert result[0]["insight"] == "test"

    def test_extracts_from_markdown_code_block(self):
        """Should extract JSON from markdown code block."""
        response = '''Here's the analysis:
```json
[{"category": "decision", "insight": "use JWT"}]
```
That's all.'''
        result = daemon._extract_json_from_response(response)
        assert len(result) == 1
        assert result[0]["insight"] == "use JWT"

    def test_extracts_array_from_mixed_text(self):
        """Should find JSON array in mixed text."""
        response = 'The insights are: [{"category": "context", "insight": "working on auth"}] end.'
        result = daemon._extract_json_from_response(response)
        assert len(result) == 1

    def test_returns_empty_for_invalid_json(self):
        """Should return empty list for invalid JSON."""
        response = 'No valid JSON here'
        result = daemon._extract_json_from_response(response)
        assert result == []


class TestExtractInsights:
    """Tests for extract_insights function."""

    @pytest.mark.asyncio
    async def test_returns_empty_for_empty_input(self):
        """Should return empty list for empty input."""
        result = await daemon.extract_insights("")
        assert result == []

    @pytest.mark.asyncio
    async def test_returns_empty_for_whitespace_input(self):
        """Should return empty list for whitespace-only input."""
        result = await daemon.extract_insights("   \n\t  ")
        assert result == []

    @pytest.mark.asyncio
    async def test_calls_cerebras_and_parses_response(self, monkeypatch):
        """Should call Cerebras and parse response."""
        mock_complete = mock.MagicMock(return_value='[{"category": "learning", "insight": "test insight"}]')
        monkeypatch.setattr(daemon.cerebras_client, 'complete', mock_complete)

        result = await daemon.extract_insights("Human: How do I test?\nAssistant: Use pytest.")

        assert len(result) == 1
        assert result[0]["category"] == "learning"
        assert result[0]["insight"] == "test insight"
        mock_complete.assert_called_once()

    @pytest.mark.asyncio
    async def test_handles_cerebras_error(self, monkeypatch, tmp_path):
        """Should handle Cerebras errors gracefully."""
        monkeypatch.setattr(daemon, 'DAEMON_STATE_DIR', tmp_path)
        monkeypatch.setattr(daemon, 'LOG_FILE', tmp_path / "daemon.log")
        monkeypatch.setattr(daemon.cerebras_client, 'complete', mock.MagicMock(side_effect=Exception("API Error")))

        result = await daemon.extract_insights("Some conversation")

        assert result == []

    @pytest.mark.asyncio
    async def test_validates_insights_have_required_fields(self, monkeypatch):
        """Should filter out insights without required fields."""
        mock_complete = mock.MagicMock(return_value='[{"category": "learning"}, {"insight": "valid"}]')
        monkeypatch.setattr(daemon.cerebras_client, 'complete', mock_complete)

        result = await daemon.extract_insights("Some conversation")

        # Only the second one has "insight" field
        assert len(result) == 1
        assert result[0]["insight"] == "valid"


class TestStoreInsights:
    """Tests for store_insights function."""

    @pytest.mark.asyncio
    async def test_skips_when_no_thread_id(self, monkeypatch, tmp_path):
        """Should skip storage when BACKBOARD_PERSONAL_THREAD_ID is not set."""
        monkeypatch.delenv("BACKBOARD_PERSONAL_THREAD_ID", raising=False)
        monkeypatch.setattr(daemon, 'DAEMON_STATE_DIR', tmp_path)
        monkeypatch.setattr(daemon, 'LOG_FILE', tmp_path / "daemon.log")

        mock_store = mock.AsyncMock()
        monkeypatch.setattr(daemon.backboard_client, 'store_message', mock_store)

        insights = [{"category": "learning", "insight": "test"}]
        await daemon.store_insights(insights, "session1", "/test")

        mock_store.assert_not_called()

    @pytest.mark.asyncio
    async def test_stores_each_insight(self, monkeypatch, tmp_path):
        """Should store each insight to Backboard."""
        monkeypatch.setenv("BACKBOARD_PERSONAL_THREAD_ID", "thread123")
        monkeypatch.setattr(daemon, 'DAEMON_STATE_DIR', tmp_path)
        monkeypatch.setattr(daemon, 'LOG_FILE', tmp_path / "daemon.log")

        mock_store = mock.AsyncMock()
        monkeypatch.setattr(daemon.backboard_client, 'store_message', mock_store)

        insights = [
            {"category": "learning", "insight": "First insight"},
            {"category": "decision", "insight": "Second insight"},
        ]
        await daemon.store_insights(insights, "session1", "/test")

        assert mock_store.call_count == 2

    @pytest.mark.asyncio
    async def test_skips_empty_insights(self, monkeypatch, tmp_path):
        """Should skip insights with empty text."""
        monkeypatch.setenv("BACKBOARD_PERSONAL_THREAD_ID", "thread123")
        monkeypatch.setattr(daemon, 'DAEMON_STATE_DIR', tmp_path)
        monkeypatch.setattr(daemon, 'LOG_FILE', tmp_path / "daemon.log")

        mock_store = mock.AsyncMock()
        monkeypatch.setattr(daemon.backboard_client, 'store_message', mock_store)

        insights = [
            {"category": "learning", "insight": ""},
            {"category": "learning", "insight": "Valid"},
        ]
        await daemon.store_insights(insights, "session1", "/test")

        assert mock_store.call_count == 1

    @pytest.mark.asyncio
    async def test_handles_backboard_error(self, monkeypatch, tmp_path):
        """Should handle Backboard errors gracefully."""
        monkeypatch.setenv("BACKBOARD_PERSONAL_THREAD_ID", "thread123")
        monkeypatch.setattr(daemon, 'DAEMON_STATE_DIR', tmp_path)
        monkeypatch.setattr(daemon, 'LOG_FILE', tmp_path / "daemon.log")

        mock_store = mock.AsyncMock(side_effect=daemon.BackboardError("Connection failed"))
        monkeypatch.setattr(daemon.backboard_client, 'store_message', mock_store)

        insights = [{"category": "learning", "insight": "test"}]
        # Should not raise
        await daemon.store_insights(insights, "session1", "/test")


class TestIsRunning:
    """Tests for is_running function."""

    def test_returns_none_when_no_pid_file(self, tmp_path, monkeypatch):
        """Should return None when PID file doesn't exist."""
        monkeypatch.setattr(daemon, 'PID_FILE', tmp_path / "nonexistent.pid")

        result = daemon.is_running()

        assert result is None

    def test_returns_none_for_invalid_pid(self, tmp_path, monkeypatch):
        """Should return None when PID file contains invalid data."""
        pid_file = tmp_path / "daemon.pid"
        pid_file.write_text("not a number")
        monkeypatch.setattr(daemon, 'PID_FILE', pid_file)

        result = daemon.is_running()

        assert result is None
        assert not pid_file.exists()  # Should clean up invalid PID file

    def test_returns_pid_when_process_exists(self, tmp_path, monkeypatch):
        """Should return PID when process is running."""
        pid_file = tmp_path / "daemon.pid"
        current_pid = os.getpid()  # Use our own PID (guaranteed to exist)
        pid_file.write_text(str(current_pid))
        monkeypatch.setattr(daemon, 'PID_FILE', pid_file)

        result = daemon.is_running()

        assert result == current_pid


class TestDaemonStatus:
    """Tests for daemon_status function."""

    def test_returns_not_running_status(self, tmp_path, monkeypatch):
        """Should return not running status when daemon is not running."""
        monkeypatch.setattr(daemon, 'PID_FILE', tmp_path / "nonexistent.pid")
        monkeypatch.setattr(daemon, 'STATE_FILE', tmp_path / "state.json")
        monkeypatch.setattr(daemon, 'LOG_FILE', tmp_path / "daemon.log")

        status = daemon.daemon_status()

        assert status["running"] is False
        assert status["pid"] is None

    def test_returns_running_status(self, tmp_path, monkeypatch):
        """Should return running status when daemon is running."""
        pid_file = tmp_path / "daemon.pid"
        pid_file.write_text(str(os.getpid()))
        monkeypatch.setattr(daemon, 'PID_FILE', pid_file)
        monkeypatch.setattr(daemon, 'STATE_FILE', tmp_path / "state.json")
        monkeypatch.setattr(daemon, 'LOG_FILE', tmp_path / "daemon.log")

        status = daemon.daemon_status()

        assert status["running"] is True
        assert status["pid"] == os.getpid()

    def test_includes_state_info(self, tmp_path, monkeypatch):
        """Should include state information."""
        state_file = tmp_path / "state.json"
        state_file.write_text(json.dumps({
            "sessions": {"s1": {}, "s2": {}},
            "started_at": "2024-01-01T00:00:00",
            "extractions_count": 10
        }))
        monkeypatch.setattr(daemon, 'PID_FILE', tmp_path / "nonexistent.pid")
        monkeypatch.setattr(daemon, 'STATE_FILE', state_file)
        monkeypatch.setattr(daemon, 'LOG_FILE', tmp_path / "daemon.log")

        status = daemon.daemon_status()

        assert status["extractions_count"] == 10
        assert status["sessions_tracked"] == 2

    def test_includes_recent_logs(self, tmp_path, monkeypatch):
        """Should include recent log lines."""
        log_file = tmp_path / "daemon.log"
        log_file.write_text("Line 1\nLine 2\nLine 3\nLine 4\nLine 5\nLine 6\n")
        monkeypatch.setattr(daemon, 'PID_FILE', tmp_path / "nonexistent.pid")
        monkeypatch.setattr(daemon, 'STATE_FILE', tmp_path / "state.json")
        monkeypatch.setattr(daemon, 'LOG_FILE', log_file)

        status = daemon.daemon_status()

        assert "recent_logs" in status
        assert len(status["recent_logs"]) == 5


class TestProcessSession:
    """Tests for process_session function."""

    @pytest.mark.asyncio
    async def test_returns_false_when_no_new_messages(self, tmp_path, monkeypatch):
        """Should return False when there are no new messages."""
        monkeypatch.setattr(daemon, 'DAEMON_STATE_DIR', tmp_path)
        monkeypatch.setattr(daemon, 'STATE_FILE', tmp_path / "state.json")
        monkeypatch.setattr(daemon, 'LOG_FILE', tmp_path / "daemon.log")

        session_file = tmp_path / "test.jsonl"
        session_file.write_text("")

        mock_get_conv = mock.MagicMock(return_value=("", 0))
        monkeypatch.setattr(daemon.session_parser, 'get_conversation_text', mock_get_conv)

        state = {"sessions": {"test": {"last_line": 0}}}
        result = await daemon.process_session(session_file, state)

        assert result is False

    @pytest.mark.asyncio
    async def test_extracts_when_batch_threshold_met(self, tmp_path, monkeypatch):
        """Should extract insights when batch threshold is met."""
        monkeypatch.setattr(daemon, 'DAEMON_STATE_DIR', tmp_path)
        monkeypatch.setattr(daemon, 'STATE_FILE', tmp_path / "state.json")
        monkeypatch.setattr(daemon, 'LOG_FILE', tmp_path / "daemon.log")
        monkeypatch.setattr(daemon, 'MIN_MESSAGES_BATCH', 2)
        monkeypatch.delenv("BACKBOARD_PERSONAL_THREAD_ID", raising=False)

        session_file = tmp_path / "test.jsonl"
        session_file.write_text("")

        # Simulate having new messages
        mock_get_conv = mock.MagicMock(side_effect=[
            ("Human: Test\nAssistant: Response", 5),  # First call (incremental)
            ("Human: Test\nAssistant: Response", 5),  # Second call (full context)
        ])
        monkeypatch.setattr(daemon.session_parser, 'get_conversation_text', mock_get_conv)
        monkeypatch.setattr(daemon.session_parser, 'parse_session_messages', mock.MagicMock(return_value=iter([])))

        mock_extract = mock.AsyncMock(return_value=[{"category": "learning", "insight": "test"}])
        monkeypatch.setattr(daemon, 'extract_insights', mock_extract)

        state = {"sessions": {"test": {"last_line": 0, "pending_messages": 0}}, "extractions_count": 0}
        result = await daemon.process_session(session_file, state)

        assert result is True
        mock_extract.assert_called_once()
