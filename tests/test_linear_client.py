"""Tests for the linear_client.py module."""
from datetime import datetime, timedelta
from unittest import mock

import httpx
import pytest

import linear_client


class TestGetApiKey:
    """Tests for get_api_key function."""

    def test_returns_key_when_set(self, monkeypatch):
        """get_api_key should return API key from environment."""
        monkeypatch.setenv("LINEAR_API_KEY", "lin_test_key")
        assert linear_client.get_api_key() == "lin_test_key"

    def test_returns_none_when_not_set(self, monkeypatch):
        """get_api_key should return None when not set."""
        monkeypatch.delenv("LINEAR_API_KEY", raising=False)
        assert linear_client.get_api_key() is None


class TestLinearQuery:
    """Tests for linear_query function."""

    @pytest.mark.asyncio
    async def test_raises_error_without_api_key(self, monkeypatch):
        """linear_query should raise ValueError without API key."""
        monkeypatch.delenv("LINEAR_API_KEY", raising=False)

        with pytest.raises(ValueError) as exc_info:
            await linear_client.linear_query("query { viewer { id } }")

        assert "LINEAR_API_KEY" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_successful_query(self, monkeypatch):
        """linear_query should return data on success."""
        monkeypatch.setenv("LINEAR_API_KEY", "lin_test_key")

        mock_response = mock.MagicMock()
        mock_response.json.return_value = {"data": {"viewer": {"id": "user-123"}}}
        mock_response.raise_for_status = mock.MagicMock()

        with mock.patch('httpx.AsyncClient') as mock_client_class:
            mock_client = mock.AsyncMock()
            mock_client.post = mock.AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = mock.AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = mock.AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client

            result = await linear_client.linear_query("query { viewer { id } }")

            assert result == {"data": {"viewer": {"id": "user-123"}}}
            mock_client.post.assert_called_once()

    @pytest.mark.asyncio
    async def test_query_with_variables(self, monkeypatch):
        """linear_query should include variables in payload."""
        monkeypatch.setenv("LINEAR_API_KEY", "lin_test_key")

        mock_response = mock.MagicMock()
        mock_response.json.return_value = {"data": {"issues": {"nodes": []}}}
        mock_response.raise_for_status = mock.MagicMock()

        with mock.patch('httpx.AsyncClient') as mock_client_class:
            mock_client = mock.AsyncMock()
            mock_client.post = mock.AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = mock.AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = mock.AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client

            await linear_client.linear_query(
                "query Issues($first: Int!) { issues(first: $first) { nodes { id } } }",
                variables={"first": 10}
            )

            call_args = mock_client.post.call_args
            payload = call_args[1]["json"]
            assert "variables" in payload
            assert payload["variables"] == {"first": 10}


class TestGetAllIssues:
    """Tests for get_all_issues function."""

    @pytest.mark.asyncio
    async def test_returns_issues_list(self, monkeypatch):
        """get_all_issues should return list of issues."""
        monkeypatch.setenv("LINEAR_API_KEY", "lin_test_key")

        mock_issues = [
            {"id": "issue-1", "title": "Bug fix", "identifier": "TEST-1"},
            {"id": "issue-2", "title": "Feature", "identifier": "TEST-2"},
        ]

        with mock.patch.object(linear_client, 'linear_query') as mock_query:
            mock_query.return_value = {"data": {"issues": {"nodes": mock_issues}}}

            result = await linear_client.get_all_issues(days=30, limit=50)

            assert result == mock_issues
            mock_query.assert_called_once()


class TestGetRecentBugs:
    """Tests for get_recent_bugs function."""

    @pytest.mark.asyncio
    async def test_filters_by_bug_label(self, monkeypatch):
        """get_recent_bugs should filter issues with bug label."""
        monkeypatch.setenv("LINEAR_API_KEY", "lin_test_key")

        mock_bugs = [
            {"id": "bug-1", "title": "Critical bug", "identifier": "BUG-1"},
        ]

        with mock.patch.object(linear_client, 'linear_query') as mock_query:
            mock_query.return_value = {"data": {"issues": {"nodes": mock_bugs}}}

            result = await linear_client.get_recent_bugs(days=30)

            assert result == mock_bugs
            # Verify filter includes bug label
            call_args = mock_query.call_args
            variables = call_args[1]["variables"] if "variables" in call_args[1] else call_args[0][1]
            assert "filter" in variables
            assert "labels" in variables["filter"]


class TestGetSolvedBugs:
    """Tests for get_solved_bugs function."""

    @pytest.mark.asyncio
    async def test_filters_completed_issues(self, monkeypatch):
        """get_solved_bugs should filter completed issues."""
        monkeypatch.setenv("LINEAR_API_KEY", "lin_test_key")

        mock_solved = [
            {"id": "solved-1", "title": "Fixed bug", "completedAt": "2026-01-15T10:00:00"},
        ]

        with mock.patch.object(linear_client, 'linear_query') as mock_query:
            mock_query.return_value = {"data": {"issues": {"nodes": mock_solved}}}

            result = await linear_client.get_solved_bugs(days=90)

            assert result == mock_solved


class TestTeamInfo:
    """Tests for team info functions."""

    @pytest.mark.asyncio
    async def test_get_team_info(self, monkeypatch):
        """get_team_info should return viewer and teams data."""
        monkeypatch.setenv("LINEAR_API_KEY", "lin_test_key")

        mock_data = {
            "viewer": {"id": "user-1", "name": "Test User", "email": "test@example.com"},
            "teams": {"nodes": [{"id": "team-1", "name": "Engineering", "key": "ENG", "issueCount": 100}]}
        }

        with mock.patch.object(linear_client, 'linear_query') as mock_query:
            mock_query.return_value = {"data": mock_data}

            result = await linear_client.get_team_info()

            assert result == mock_data

    @pytest.mark.asyncio
    async def test_test_connection_success(self, monkeypatch):
        """test_connection should return connected=True on success."""
        monkeypatch.setenv("LINEAR_API_KEY", "lin_test_key")

        mock_data = {
            "viewer": {"name": "Test User", "email": "test@example.com"},
            "teams": {"nodes": [{"name": "Eng", "key": "ENG", "issueCount": 50}]}
        }

        with mock.patch.object(linear_client, 'linear_query') as mock_query:
            mock_query.return_value = {"data": mock_data}

            result = await linear_client.test_connection()

            assert result["connected"] is True
            assert result["user"] == "Test User"
            assert len(result["teams"]) == 1

    @pytest.mark.asyncio
    async def test_test_connection_failure(self, monkeypatch):
        """test_connection should return connected=False on error."""
        monkeypatch.setenv("LINEAR_API_KEY", "lin_test_key")

        with mock.patch.object(linear_client, 'linear_query') as mock_query:
            mock_query.side_effect = Exception("API error")

            result = await linear_client.test_connection()

            assert result["connected"] is False
            assert "error" in result


class TestDocuments:
    """Tests for document-related functions."""

    @pytest.mark.asyncio
    async def test_get_default_team_id(self, monkeypatch):
        """get_default_team_id should return first team's ID."""
        monkeypatch.setenv("LINEAR_API_KEY", "lin_test_key")

        with mock.patch.object(linear_client, 'get_team_info') as mock_info:
            mock_info.return_value = {
                "teams": {"nodes": [{"id": "team-123", "name": "Eng"}]}
            }

            result = await linear_client.get_default_team_id()

            assert result == "team-123"

    @pytest.mark.asyncio
    async def test_get_default_project_id_from_env(self, monkeypatch):
        """get_default_project_id should use LINEAR_PROJECT_ID env var."""
        monkeypatch.setenv("LINEAR_API_KEY", "lin_test_key")
        monkeypatch.setenv("LINEAR_PROJECT_ID", "proj-from-env")

        result = await linear_client.get_default_project_id()

        assert result == "proj-from-env"

    @pytest.mark.asyncio
    async def test_get_default_project_id_fallback(self, monkeypatch):
        """get_default_project_id should query for first project if no env var."""
        monkeypatch.setenv("LINEAR_API_KEY", "lin_test_key")
        monkeypatch.delenv("LINEAR_PROJECT_ID", raising=False)

        with mock.patch.object(linear_client, 'linear_query') as mock_query:
            mock_query.return_value = {
                "data": {"projects": {"nodes": [{"id": "proj-123"}]}}
            }

            result = await linear_client.get_default_project_id()

            assert result == "proj-123"

    @pytest.mark.asyncio
    async def test_create_document_success(self, monkeypatch):
        """create_document should create and return document data."""
        monkeypatch.setenv("LINEAR_API_KEY", "lin_test_key")
        monkeypatch.setenv("LINEAR_PROJECT_ID", "proj-123")

        mock_doc = {
            "id": "doc-123",
            "title": "Test Doc",
            "url": "https://linear.app/test/doc-123",
            "createdAt": "2026-01-17T10:00:00"
        }

        with mock.patch.object(linear_client, 'linear_query') as mock_query:
            mock_query.return_value = {
                "data": {"documentCreate": {"success": True, "document": mock_doc}}
            }

            result = await linear_client.create_document("Test Doc", "# Content")

            assert result == mock_doc

    @pytest.mark.asyncio
    async def test_create_document_failure(self, monkeypatch):
        """create_document should return None on failure."""
        monkeypatch.setenv("LINEAR_API_KEY", "lin_test_key")
        monkeypatch.setenv("LINEAR_PROJECT_ID", "proj-123")

        with mock.patch.object(linear_client, 'linear_query') as mock_query:
            mock_query.return_value = {
                "data": {"documentCreate": {"success": False, "document": None}}
            }

            result = await linear_client.create_document("Test Doc", "# Content")

            assert result is None

    @pytest.mark.asyncio
    async def test_update_document_success(self, monkeypatch):
        """update_document should return True on success."""
        monkeypatch.setenv("LINEAR_API_KEY", "lin_test_key")

        with mock.patch.object(linear_client, 'linear_query') as mock_query:
            mock_query.return_value = {
                "data": {"documentUpdate": {"success": True}}
            }

            result = await linear_client.update_document("doc-123", "# Updated")

            assert result is True

    @pytest.mark.asyncio
    async def test_find_document_by_title(self, monkeypatch):
        """find_document_by_title should return matching document."""
        monkeypatch.setenv("LINEAR_API_KEY", "lin_test_key")

        mock_doc = {"id": "doc-123", "title": "FAQ", "url": "https://linear.app/doc"}

        with mock.patch.object(linear_client, 'linear_query') as mock_query:
            mock_query.return_value = {
                "data": {"documents": {"nodes": [mock_doc]}}
            }

            result = await linear_client.find_document_by_title("FAQ")

            assert result == mock_doc

    @pytest.mark.asyncio
    async def test_find_document_not_found(self, monkeypatch):
        """find_document_by_title should return None if not found."""
        monkeypatch.setenv("LINEAR_API_KEY", "lin_test_key")

        with mock.patch.object(linear_client, 'linear_query') as mock_query:
            mock_query.return_value = {
                "data": {"documents": {"nodes": []}}
            }

            result = await linear_client.find_document_by_title("Missing Doc")

            assert result is None

    @pytest.mark.asyncio
    async def test_create_or_update_document_creates_new(self, monkeypatch):
        """create_or_update_document should create new doc if not exists."""
        monkeypatch.setenv("LINEAR_API_KEY", "lin_test_key")
        monkeypatch.setenv("LINEAR_PROJECT_ID", "proj-123")

        mock_doc = {"id": "new-doc", "title": "New FAQ", "url": "https://linear.app/new"}

        with mock.patch.object(linear_client, 'find_document_by_title') as mock_find:
            mock_find.return_value = None

            with mock.patch.object(linear_client, 'create_document') as mock_create:
                mock_create.return_value = mock_doc

                result = await linear_client.create_or_update_document("New FAQ", "# Content")

                assert result == mock_doc
                mock_create.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_or_update_document_updates_existing(self, monkeypatch):
        """create_or_update_document should update existing doc."""
        monkeypatch.setenv("LINEAR_API_KEY", "lin_test_key")
        monkeypatch.setenv("LINEAR_PROJECT_ID", "proj-123")

        existing_doc = {"id": "existing-doc", "title": "FAQ", "url": "https://linear.app/existing"}

        with mock.patch.object(linear_client, 'find_document_by_title') as mock_find:
            mock_find.return_value = existing_doc

            with mock.patch.object(linear_client, 'update_document') as mock_update:
                mock_update.return_value = True

                result = await linear_client.create_or_update_document("FAQ", "# Updated")

                assert result == existing_doc
                mock_update.assert_called_once_with("existing-doc", "# Updated")
