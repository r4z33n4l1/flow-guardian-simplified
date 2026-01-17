"""Tests for the cerebras_client.py module."""
import json
from unittest import mock

import pytest

import cerebras_client


class TestExceptions:
    """Tests for exception classes."""

    def test_cerebras_error_hierarchy(self):
        """CerebrasError should be base for all errors."""
        assert issubclass(cerebras_client.CerebrasAuthError, cerebras_client.CerebrasError)
        assert issubclass(cerebras_client.CerebrasRateLimitError, cerebras_client.CerebrasError)

    def test_cerebras_error_message(self):
        """Exceptions should preserve error messages."""
        error = cerebras_client.CerebrasError("Test error")
        assert str(error) == "Test error"


class TestGetClient:
    """Tests for _get_client function."""

    def test_raises_auth_error_without_key(self, monkeypatch):
        """_get_client should raise CerebrasAuthError without API key."""
        monkeypatch.delenv("CEREBRAS_API_KEY", raising=False)

        with pytest.raises(cerebras_client.CerebrasAuthError) as exc_info:
            cerebras_client._get_client()

        assert "CEREBRAS_API_KEY" in str(exc_info.value)

    def test_creates_client_with_key(self, monkeypatch):
        """_get_client should create client when API key is set."""
        monkeypatch.setenv("CEREBRAS_API_KEY", "test-api-key")

        with mock.patch('cerebras_client.Cerebras') as mock_cerebras:
            mock_cerebras.return_value = mock.MagicMock()

            client = cerebras_client._get_client()

            mock_cerebras.assert_called_once_with(api_key="test-api-key")


class TestComplete:
    """Tests for complete function."""

    def test_complete_basic(self, monkeypatch):
        """complete should return model response."""
        monkeypatch.setenv("CEREBRAS_API_KEY", "test-key")

        mock_response = mock.MagicMock()
        mock_response.choices = [
            mock.MagicMock(message=mock.MagicMock(content="Test response"))
        ]

        with mock.patch('cerebras_client.Cerebras') as mock_cerebras:
            mock_client = mock.MagicMock()
            mock_client.chat.completions.create.return_value = mock_response
            mock_cerebras.return_value = mock_client

            result = cerebras_client.complete("Test prompt")

            assert result == "Test response"

    def test_complete_with_system_message(self, monkeypatch):
        """complete should include system message when provided."""
        monkeypatch.setenv("CEREBRAS_API_KEY", "test-key")

        mock_response = mock.MagicMock()
        mock_response.choices = [
            mock.MagicMock(message=mock.MagicMock(content="Response"))
        ]

        with mock.patch('cerebras_client.Cerebras') as mock_cerebras:
            mock_client = mock.MagicMock()
            mock_client.chat.completions.create.return_value = mock_response
            mock_cerebras.return_value = mock_client

            cerebras_client.complete("Prompt", system="System message")

            call_args = mock_client.chat.completions.create.call_args
            messages = call_args.kwargs.get('messages', [])
            assert any(m.get('role') == 'system' for m in messages)

    def test_complete_json_mode(self, monkeypatch):
        """complete should set response_format for json_mode."""
        monkeypatch.setenv("CEREBRAS_API_KEY", "test-key")

        mock_response = mock.MagicMock()
        mock_response.choices = [
            mock.MagicMock(message=mock.MagicMock(content='{"key": "value"}'))
        ]

        with mock.patch('cerebras_client.Cerebras') as mock_cerebras:
            mock_client = mock.MagicMock()
            mock_client.chat.completions.create.return_value = mock_response
            mock_cerebras.return_value = mock_client

            result = cerebras_client.complete("Prompt", json_mode=True)

            call_args = mock_client.chat.completions.create.call_args
            response_format = call_args.kwargs.get('response_format')
            assert response_format == {"type": "json_object"}

    def test_complete_handles_auth_error(self, monkeypatch):
        """complete should raise CerebrasAuthError on 401."""
        monkeypatch.setenv("CEREBRAS_API_KEY", "invalid-key")

        with mock.patch('cerebras_client.Cerebras') as mock_cerebras:
            mock_client = mock.MagicMock()
            mock_client.chat.completions.create.side_effect = Exception("401 Unauthorized")
            mock_cerebras.return_value = mock_client

            with pytest.raises(cerebras_client.CerebrasAuthError):
                cerebras_client.complete("Test prompt")

    def test_complete_handles_rate_limit(self, monkeypatch):
        """complete should raise CerebrasRateLimitError on 429."""
        monkeypatch.setenv("CEREBRAS_API_KEY", "test-key")

        with mock.patch('cerebras_client.Cerebras') as mock_cerebras:
            mock_client = mock.MagicMock()
            mock_client.chat.completions.create.side_effect = Exception("429 rate limit exceeded")
            mock_cerebras.return_value = mock_client

            with pytest.raises(cerebras_client.CerebrasRateLimitError):
                cerebras_client.complete("Test prompt")

    def test_complete_handles_generic_error(self, monkeypatch):
        """complete should raise CerebrasError on other errors."""
        monkeypatch.setenv("CEREBRAS_API_KEY", "test-key")

        with mock.patch('cerebras_client.Cerebras') as mock_cerebras:
            mock_client = mock.MagicMock()
            mock_client.chat.completions.create.side_effect = Exception("Server error")
            mock_cerebras.return_value = mock_client

            with pytest.raises(cerebras_client.CerebrasError):
                cerebras_client.complete("Test prompt")


class TestAnalyzeSessionContext:
    """Tests for analyze_session_context function."""

    def test_analyze_session_context_success(self, monkeypatch):
        """analyze_session_context should return structured context."""
        monkeypatch.setenv("CEREBRAS_API_KEY", "test-key")

        mock_json_response = json.dumps({
            "summary": "Working on auth",
            "hypothesis": "JWT is best",
            "next_steps": ["Add tokens"],
            "decisions": ["Use JWT"],
            "learnings": ["JWT is fast"]
        })

        with mock.patch.object(cerebras_client, 'complete', return_value=mock_json_response):
            result = cerebras_client.analyze_session_context(
                branch="feature/auth",
                files=["auth.py"],
                diff_summary="Added authentication",
                user_message="Working on login"
            )

            assert result["summary"] == "Working on auth"
            assert result["hypothesis"] == "JWT is best"
            assert result["next_steps"] == ["Add tokens"]
            assert result["decisions"] == ["Use JWT"]
            assert result["learnings"] == ["JWT is fast"]

    def test_analyze_session_context_handles_invalid_json(self, monkeypatch):
        """analyze_session_context should handle invalid JSON gracefully."""
        monkeypatch.setenv("CEREBRAS_API_KEY", "test-key")

        with mock.patch.object(cerebras_client, 'complete', return_value="not valid json"):
            result = cerebras_client.analyze_session_context(
                branch="main",
                files=[],
                diff_summary="",
                user_message="Test message"
            )

            # Should return fallback
            assert result["summary"] == "Test message"
            assert result["hypothesis"] is None
            assert result["next_steps"] == []

    def test_analyze_session_context_default_summary(self, monkeypatch):
        """analyze_session_context should provide default summary."""
        monkeypatch.setenv("CEREBRAS_API_KEY", "test-key")

        mock_json_response = json.dumps({
            "summary": None,
            "hypothesis": None,
            "next_steps": [],
            "decisions": [],
            "learnings": []
        })

        with mock.patch.object(cerebras_client, 'complete', return_value=mock_json_response):
            result = cerebras_client.analyze_session_context(
                branch="main",
                files=[],
                diff_summary=""
            )

            assert result["summary"] == "Working on code changes"


class TestGenerateRestorationMessage:
    """Tests for generate_restoration_message function."""

    def test_generate_restoration_message_success(self, monkeypatch):
        """generate_restoration_message should return message from Cerebras."""
        monkeypatch.setenv("CEREBRAS_API_KEY", "test-key")

        expected_message = "Welcome back! You were working on auth feature."

        with mock.patch.object(cerebras_client, 'complete', return_value=expected_message):
            result = cerebras_client.generate_restoration_message(
                context={
                    "summary": "Working on auth",
                    "hypothesis": "JWT approach",
                    "files": ["auth.py"],
                    "branch": "feature",
                    "learnings": []
                },
                changes={
                    "elapsed": "2h",
                    "commits": [],
                    "files_changed": []
                }
            )

            assert result == expected_message

    def test_generate_restoration_message_fallback(self, monkeypatch):
        """generate_restoration_message should fallback on error."""
        monkeypatch.setenv("CEREBRAS_API_KEY", "test-key")

        with mock.patch.object(
            cerebras_client, 'complete',
            side_effect=cerebras_client.CerebrasError("API down")
        ):
            result = cerebras_client.generate_restoration_message(
                context={
                    "summary": "Working on feature",
                    "hypothesis": None,
                    "files": [],
                    "branch": "main",
                    "learnings": []
                },
                changes={
                    "elapsed": "3h",
                    "commits": [],
                    "files_changed": []
                }
            )

            assert "Welcome back" in result
            assert "Working on feature" in result
            assert "3h" in result
