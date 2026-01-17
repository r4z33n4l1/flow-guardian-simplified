"""Tests for the backboard_client.py module."""
from datetime import datetime
from unittest import mock

import httpx
import pytest

import backboard_client


class TestExceptions:
    """Tests for exception classes."""

    def test_exception_hierarchy(self):
        """All exceptions should inherit from BackboardError."""
        assert issubclass(backboard_client.BackboardAuthError, backboard_client.BackboardError)
        assert issubclass(backboard_client.BackboardConnectionError, backboard_client.BackboardError)
        assert issubclass(backboard_client.BackboardRateLimitError, backboard_client.BackboardError)

    def test_exception_message(self):
        """Exceptions should preserve error messages."""
        error = backboard_client.BackboardError("Test error")
        assert str(error) == "Test error"


class TestHeaders:
    """Tests for _headers function."""

    def test_raises_auth_error_without_key(self, monkeypatch):
        """_headers should raise BackboardAuthError without API key."""
        monkeypatch.setattr(backboard_client, 'API_KEY', None)

        with pytest.raises(backboard_client.BackboardAuthError) as exc_info:
            backboard_client._headers()

        assert "BACKBOARD_API_KEY" in str(exc_info.value)

    def test_returns_headers_with_key(self, monkeypatch):
        """_headers should return valid headers when API key is set."""
        monkeypatch.setattr(backboard_client, 'API_KEY', "test-api-key")

        headers = backboard_client._headers()

        assert headers["X-API-Key"] == "test-api-key"
        assert headers["Content-Type"] == "application/json"


class TestRequestWithRetry:
    """Tests for _request_with_retry function."""

    @pytest.mark.asyncio
    async def test_successful_request(self, monkeypatch):
        """_request_with_retry should return response on success."""
        monkeypatch.setattr(backboard_client, 'API_KEY', "test-key")

        mock_response = mock.MagicMock()
        mock_response.status_code = 200

        with mock.patch('httpx.AsyncClient') as mock_client_class:
            mock_client = mock.AsyncMock()
            mock_client.get = mock.AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = mock.AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = mock.AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client

            result = await backboard_client._request_with_retry(
                "get",
                "https://api.example.com/test",
                headers=backboard_client._headers()
            )

            assert result.status_code == 200

    @pytest.mark.asyncio
    async def test_auth_error_on_401(self, monkeypatch):
        """_request_with_retry should raise BackboardAuthError on 401."""
        monkeypatch.setattr(backboard_client, 'API_KEY', "invalid-key")

        mock_response = mock.MagicMock()
        mock_response.status_code = 401

        with mock.patch('httpx.AsyncClient') as mock_client_class:
            mock_client = mock.AsyncMock()
            mock_client.get = mock.AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = mock.AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = mock.AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client

            with pytest.raises(backboard_client.BackboardAuthError):
                await backboard_client._request_with_retry(
                    "get",
                    "https://api.example.com/test",
                    headers=backboard_client._headers()
                )

    @pytest.mark.asyncio
    async def test_rate_limit_error_on_429(self, monkeypatch):
        """_request_with_retry should raise BackboardRateLimitError on 429."""
        monkeypatch.setattr(backboard_client, 'API_KEY', "test-key")

        mock_response = mock.MagicMock()
        mock_response.status_code = 429

        with mock.patch('httpx.AsyncClient') as mock_client_class:
            mock_client = mock.AsyncMock()
            mock_client.get = mock.AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = mock.AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = mock.AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client

            with pytest.raises(backboard_client.BackboardRateLimitError):
                await backboard_client._request_with_retry(
                    "get",
                    "https://api.example.com/test",
                    headers=backboard_client._headers()
                )

    @pytest.mark.asyncio
    async def test_connection_error_handling(self, monkeypatch):
        """_request_with_retry should handle connection errors."""
        monkeypatch.setattr(backboard_client, 'API_KEY', "test-key")
        monkeypatch.setattr(backboard_client, 'MAX_RETRIES', 1)  # Speed up test

        with mock.patch('httpx.AsyncClient') as mock_client_class:
            mock_client = mock.AsyncMock()
            mock_client.get = mock.AsyncMock(side_effect=httpx.ConnectError("Connection failed"))
            mock_client.__aenter__ = mock.AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = mock.AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client

            with pytest.raises(backboard_client.BackboardConnectionError):
                await backboard_client._request_with_retry(
                    "get",
                    "https://api.example.com/test",
                    headers=backboard_client._headers()
                )


class TestHealthCheck:
    """Tests for health_check function."""

    @pytest.mark.asyncio
    async def test_health_check_success(self, monkeypatch):
        """health_check should return True when service is available."""
        monkeypatch.setattr(backboard_client, 'API_KEY', "test-key")

        mock_response = mock.MagicMock()
        mock_response.status_code = 200

        with mock.patch('httpx.AsyncClient') as mock_client_class:
            mock_client = mock.AsyncMock()
            mock_client.get = mock.AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = mock.AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = mock.AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client

            result = await backboard_client.health_check()

            assert result is True

    @pytest.mark.asyncio
    async def test_health_check_failure(self, monkeypatch):
        """health_check should return False when service is unavailable."""
        monkeypatch.setattr(backboard_client, 'API_KEY', "test-key")

        with mock.patch('httpx.AsyncClient') as mock_client_class:
            mock_client = mock.AsyncMock()
            mock_client.get = mock.AsyncMock(side_effect=Exception("Connection failed"))
            mock_client.__aenter__ = mock.AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = mock.AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client

            result = await backboard_client.health_check()

            assert result is False


class TestStoreFunctions:
    """Tests for store functions."""

    @pytest.mark.asyncio
    async def test_store_message(self, monkeypatch):
        """store_message should post message to API."""
        monkeypatch.setattr(backboard_client, 'API_KEY', "test-key")

        mock_response = mock.MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"id": "msg_123"}

        with mock.patch.object(
            backboard_client, '_request_with_retry',
            return_value=mock_response
        ) as mock_request:
            result = await backboard_client.store_message(
                thread_id="thread_123",
                content="Test message",
                metadata={"type": "test"}
            )

            mock_request.assert_called_once()
            call_args = mock_request.call_args
            # Implementation uses data= for form data, not json=
            assert call_args.kwargs["data"]["content"] == "Test message"
            assert call_args.kwargs["data"]["send_to_llm"] == "false"
            assert result == {"id": "msg_123"}

    @pytest.mark.asyncio
    async def test_store_session(self, monkeypatch):
        """store_session should format and store session data."""
        monkeypatch.setattr(backboard_client, 'API_KEY', "test-key")

        mock_response = mock.MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"id": "msg_123"}

        session = {
            "id": "session_123",
            "timestamp": "2024-01-01T12:00:00",
            "context": {
                "summary": "Working on feature",
                "hypothesis": "Test approach",
                "files": ["test.py"],
                "next_steps": ["Write tests"]
            },
            "git": {"branch": "main"},
            "metadata": {"tags": ["test"]}
        }

        with mock.patch.object(backboard_client, 'store_message', return_value=mock_response.json.return_value) as mock_store:
            result = await backboard_client.store_session(
                thread_id="thread_123",
                session=session
            )

            mock_store.assert_called_once()
            call_args = mock_store.call_args
            # store_message is called with positional args: (thread_id, content, metadata)
            content = call_args.args[1]
            assert "Working on feature" in content
            assert "Test approach" in content

    @pytest.mark.asyncio
    async def test_store_learning(self, monkeypatch):
        """store_learning should format and store learning."""
        monkeypatch.setattr(backboard_client, 'API_KEY', "test-key")

        mock_response = {"id": "msg_123"}

        with mock.patch.object(backboard_client, 'store_message', return_value=mock_response) as mock_store:
            result = await backboard_client.store_learning(
                thread_id="thread_123",
                text="Important learning",
                tags=["auth", "jwt"],
                author="testuser"
            )

            mock_store.assert_called_once()
            call_args = mock_store.call_args
            # store_message is called with positional args: (thread_id, content, metadata)
            content = call_args.args[1]
            assert "Important learning" in content
            metadata = call_args.args[2]
            assert metadata["type"] == "learning"
            assert metadata["tags"] == ["auth", "jwt"]
            assert metadata["author"] == "testuser"


class TestRecallFunctions:
    """Tests for recall functions."""

    @pytest.mark.asyncio
    async def test_recall(self, monkeypatch):
        """recall should query with memory=auto."""
        monkeypatch.setattr(backboard_client, 'API_KEY', "test-key")

        mock_response = mock.MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"content": "Search results"}

        with mock.patch.object(
            backboard_client, '_request_with_retry',
            return_value=mock_response
        ) as mock_request:
            result = await backboard_client.recall(
                thread_id="thread_123",
                query="authentication"
            )

            mock_request.assert_called_once()
            call_args = mock_request.call_args
            # Implementation uses data= for form data, not json=
            assert call_args.kwargs["data"]["memory"] == "auto"
            assert call_args.kwargs["data"]["send_to_llm"] == "true"
            assert result == "Search results"

    @pytest.mark.asyncio
    async def test_get_restoration_context(self, monkeypatch):
        """get_restoration_context should call recall with formatted query."""
        monkeypatch.setattr(backboard_client, 'API_KEY', "test-key")

        with mock.patch.object(backboard_client, 'recall', return_value="Welcome back!") as mock_recall:
            result = await backboard_client.get_restoration_context(
                thread_id="thread_123",
                changes_summary="2 new commits"
            )

            mock_recall.assert_called_once()
            call_args = mock_recall.call_args
            query = call_args.args[1] if len(call_args.args) > 1 else call_args.kwargs.get('query')
            assert "2 new commits" in query
            assert result == "Welcome back!"


class TestTeamMemory:
    """Tests for team memory functions."""

    @pytest.mark.asyncio
    async def test_store_team_learning(self, monkeypatch):
        """store_team_learning should include author attribution."""
        monkeypatch.setattr(backboard_client, 'API_KEY', "test-key")

        mock_response = {"id": "msg_123"}

        with mock.patch.object(backboard_client, 'store_message', return_value=mock_response) as mock_store:
            result = await backboard_client.store_team_learning(
                team_thread_id="team_thread_123",
                learning="Team insight",
                author="alice",
                tags=["team"]
            )

            mock_store.assert_called_once()
            call_args = mock_store.call_args
            # store_message is called with positional args: (thread_id, content, metadata)
            content = call_args.args[1]
            assert "Team insight" in content
            assert "alice" in content
            metadata = call_args.args[2]
            assert metadata["type"] == "team_learning"
            assert metadata["author"] == "alice"

    @pytest.mark.asyncio
    async def test_query_team_memory(self, monkeypatch):
        """query_team_memory should search team learnings."""
        monkeypatch.setattr(backboard_client, 'API_KEY', "test-key")

        with mock.patch.object(backboard_client, 'recall', return_value="Team results") as mock_recall:
            result = await backboard_client.query_team_memory(
                team_thread_id="team_thread_123",
                query="database tips"
            )

            mock_recall.assert_called_once()
            assert result == "Team results"


class TestSetupFunctions:
    """Tests for setup functions (create_assistant, create_thread)."""

    @pytest.mark.asyncio
    async def test_create_assistant(self, monkeypatch):
        """create_assistant should create assistant and return ID."""
        monkeypatch.setattr(backboard_client, 'API_KEY', "test-key")

        mock_response = mock.MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"assistant_id": "assistant_123"}

        with mock.patch.object(
            backboard_client, '_request_with_retry',
            return_value=mock_response
        ) as mock_request:
            result = await backboard_client.create_assistant(
                name="test-assistant",
                llm_provider="cerebras"
            )

            mock_request.assert_called_once()
            call_args = mock_request.call_args
            assert call_args.args[0] == "post"
            assert "/assistants" in call_args.args[1]
            assert call_args.kwargs["json"]["name"] == "test-assistant"
            assert call_args.kwargs["json"]["llm_provider"] == "cerebras"
            assert result == "assistant_123"

    @pytest.mark.asyncio
    async def test_create_assistant_default_provider(self, monkeypatch):
        """create_assistant should use cerebras as default provider."""
        monkeypatch.setattr(backboard_client, 'API_KEY', "test-key")

        mock_response = mock.MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"assistant_id": "assistant_456"}

        with mock.patch.object(
            backboard_client, '_request_with_retry',
            return_value=mock_response
        ) as mock_request:
            result = await backboard_client.create_assistant(name="my-assistant")

            call_args = mock_request.call_args
            assert call_args.kwargs["json"]["llm_provider"] == "cerebras"
            assert result == "assistant_456"

    @pytest.mark.asyncio
    async def test_create_thread(self, monkeypatch):
        """create_thread should create thread and return ID."""
        monkeypatch.setattr(backboard_client, 'API_KEY', "test-key")

        mock_response = mock.MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"thread_id": "thread_789"}

        with mock.patch.object(
            backboard_client, '_request_with_retry',
            return_value=mock_response
        ) as mock_request:
            result = await backboard_client.create_thread(assistant_id="assistant_123")

            mock_request.assert_called_once()
            call_args = mock_request.call_args
            assert call_args.args[0] == "post"
            assert "/assistants/assistant_123/threads" in call_args.args[1]
            assert result == "thread_789"

    @pytest.mark.asyncio
    async def test_create_assistant_auth_error(self, monkeypatch):
        """create_assistant should raise BackboardAuthError on 401."""
        monkeypatch.setattr(backboard_client, 'API_KEY', "invalid-key")

        with mock.patch.object(
            backboard_client, '_request_with_retry',
            side_effect=backboard_client.BackboardAuthError("Invalid API key")
        ):
            with pytest.raises(backboard_client.BackboardAuthError):
                await backboard_client.create_assistant(name="test-assistant")

    @pytest.mark.asyncio
    async def test_create_thread_auth_error(self, monkeypatch):
        """create_thread should raise BackboardAuthError on 401."""
        monkeypatch.setattr(backboard_client, 'API_KEY', "invalid-key")

        with mock.patch.object(
            backboard_client, '_request_with_retry',
            side_effect=backboard_client.BackboardAuthError("Invalid API key")
        ):
            with pytest.raises(backboard_client.BackboardAuthError):
                await backboard_client.create_thread(assistant_id="assistant_123")


class TestRunAsync:
    """Tests for run_async helper."""

    def test_run_async_from_sync(self, monkeypatch):
        """run_async should execute async function from sync context."""
        async def async_func():
            return "async result"

        result = backboard_client.run_async(async_func())

        assert result == "async result"
