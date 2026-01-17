"""Tests for the setup_assistants.py module."""
from unittest import mock
import pytest

import setup_assistants
import backboard_client


class TestSetupPersonalAssistant:
    """Tests for setup_personal_assistant function."""

    @pytest.mark.asyncio
    async def test_setup_personal_assistant_success(self, monkeypatch):
        """setup_personal_assistant should create assistant and thread."""
        monkeypatch.setattr(backboard_client, 'API_KEY', "test-key")

        with mock.patch.object(
            backboard_client, 'create_assistant',
            return_value="assistant_123"
        ) as mock_create_assistant:
            with mock.patch.object(
                backboard_client, 'create_thread',
                return_value="thread_456"
            ) as mock_create_thread:
                assistant_id, thread_id = await setup_assistants.setup_personal_assistant("testuser")

                mock_create_assistant.assert_called_once_with("flow-guardian-personal-testuser")
                mock_create_thread.assert_called_once_with("assistant_123")
                assert assistant_id == "assistant_123"
                assert thread_id == "thread_456"

    @pytest.mark.asyncio
    async def test_setup_personal_assistant_naming(self, monkeypatch):
        """setup_personal_assistant should use correct naming convention."""
        monkeypatch.setattr(backboard_client, 'API_KEY', "test-key")

        with mock.patch.object(
            backboard_client, 'create_assistant',
            return_value="asst_xyz"
        ):
            with mock.patch.object(
                backboard_client, 'create_thread',
                return_value="thread_xyz"
            ):
                await setup_assistants.setup_personal_assistant("alice")

                backboard_client.create_assistant.assert_called_with("flow-guardian-personal-alice")

    @pytest.mark.asyncio
    async def test_setup_personal_assistant_auth_error(self, monkeypatch):
        """setup_personal_assistant should propagate auth errors."""
        monkeypatch.setattr(backboard_client, 'API_KEY', "invalid-key")

        with mock.patch.object(
            backboard_client, 'create_assistant',
            side_effect=backboard_client.BackboardAuthError("Invalid API key")
        ):
            with pytest.raises(backboard_client.BackboardAuthError):
                await setup_assistants.setup_personal_assistant("testuser")


class TestSetupTeamAssistant:
    """Tests for setup_team_assistant function."""

    @pytest.mark.asyncio
    async def test_setup_team_assistant_success(self, monkeypatch):
        """setup_team_assistant should create assistant and thread."""
        monkeypatch.setattr(backboard_client, 'API_KEY', "test-key")

        with mock.patch.object(
            backboard_client, 'create_assistant',
            return_value="team_assistant_123"
        ) as mock_create_assistant:
            with mock.patch.object(
                backboard_client, 'create_thread',
                return_value="team_thread_456"
            ) as mock_create_thread:
                assistant_id, thread_id = await setup_assistants.setup_team_assistant("myteam")

                mock_create_assistant.assert_called_once_with("flow-guardian-team-myteam")
                mock_create_thread.assert_called_once_with("team_assistant_123")
                assert assistant_id == "team_assistant_123"
                assert thread_id == "team_thread_456"

    @pytest.mark.asyncio
    async def test_setup_team_assistant_naming(self, monkeypatch):
        """setup_team_assistant should use correct naming convention."""
        monkeypatch.setattr(backboard_client, 'API_KEY', "test-key")

        with mock.patch.object(
            backboard_client, 'create_assistant',
            return_value="asst_team"
        ):
            with mock.patch.object(
                backboard_client, 'create_thread',
                return_value="thread_team"
            ):
                await setup_assistants.setup_team_assistant("engineering")

                backboard_client.create_assistant.assert_called_with("flow-guardian-team-engineering")

    @pytest.mark.asyncio
    async def test_setup_team_assistant_auth_error(self, monkeypatch):
        """setup_team_assistant should propagate auth errors."""
        monkeypatch.setattr(backboard_client, 'API_KEY', "invalid-key")

        with mock.patch.object(
            backboard_client, 'create_assistant',
            side_effect=backboard_client.BackboardAuthError("Invalid API key")
        ):
            with pytest.raises(backboard_client.BackboardAuthError):
                await setup_assistants.setup_team_assistant("myteam")

    @pytest.mark.asyncio
    async def test_setup_team_assistant_connection_error(self, monkeypatch):
        """setup_team_assistant should propagate connection errors."""
        monkeypatch.setattr(backboard_client, 'API_KEY', "test-key")

        with mock.patch.object(
            backboard_client, 'create_assistant',
            side_effect=backboard_client.BackboardConnectionError("Network error")
        ):
            with pytest.raises(backboard_client.BackboardConnectionError):
                await setup_assistants.setup_team_assistant("myteam")
