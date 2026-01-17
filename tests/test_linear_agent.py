"""Tests for the linear_agent.py module."""
import json
from unittest import mock

import pytest

import linear_agent


class TestAnalyzeForIssues:
    """Tests for analyze_for_issues function."""

    @pytest.mark.asyncio
    async def test_returns_issues_from_valid_response(self):
        """analyze_for_issues should parse JSON array from Cerebras response."""
        mock_issues = [
            {"title": "Fix bug", "description": "Bug desc", "type": "bug", "priority": 2}
        ]

        with mock.patch.object(linear_agent.cerebras_client, 'quick_answer') as mock_answer:
            mock_answer.return_value = json.dumps(mock_issues)

            result = await linear_agent.analyze_for_issues("Session with bug")

            assert len(result) == 1
            assert result[0]["title"] == "Fix bug"
            assert result[0]["type"] == "bug"

    @pytest.mark.asyncio
    async def test_handles_json_in_text_response(self):
        """analyze_for_issues should extract JSON from text response."""
        response = 'Here are the issues:\n[{"title": "Task", "description": "Do something", "type": "task", "priority": 3}]\nEnd.'

        with mock.patch.object(linear_agent.cerebras_client, 'quick_answer') as mock_answer:
            mock_answer.return_value = response

            result = await linear_agent.analyze_for_issues("Session content")

            assert len(result) == 1
            assert result[0]["title"] == "Task"

    @pytest.mark.asyncio
    async def test_returns_empty_list_on_no_issues(self):
        """analyze_for_issues should return empty list when no issues found."""
        with mock.patch.object(linear_agent.cerebras_client, 'quick_answer') as mock_answer:
            mock_answer.return_value = "[]"

            result = await linear_agent.analyze_for_issues("Normal session")

            assert result == []

    @pytest.mark.asyncio
    async def test_returns_empty_list_on_invalid_json(self):
        """analyze_for_issues should return empty list on invalid JSON."""
        with mock.patch.object(linear_agent.cerebras_client, 'quick_answer') as mock_answer:
            mock_answer.return_value = "Not valid JSON at all"

            result = await linear_agent.analyze_for_issues("Some content")

            assert result == []

    @pytest.mark.asyncio
    async def test_returns_empty_list_on_exception(self):
        """analyze_for_issues should return empty list on exception."""
        with mock.patch.object(linear_agent.cerebras_client, 'quick_answer') as mock_answer:
            mock_answer.side_effect = Exception("API error")

            result = await linear_agent.analyze_for_issues("Some content")

            assert result == []


class TestCreateLinearIssue:
    """Tests for create_linear_issue function."""

    @pytest.mark.asyncio
    async def test_creates_issue_successfully(self):
        """create_linear_issue should create and return issue."""
        mock_team_info = {
            "teams": {"nodes": [{"id": "team-123", "name": "Eng"}]}
        }
        mock_issue = {
            "id": "issue-123",
            "identifier": "ENG-1",
            "title": "Test Issue",
            "url": "https://linear.app/eng-1"
        }

        with mock.patch.object(linear_agent.linear_client, 'get_team_info') as mock_info:
            mock_info.return_value = mock_team_info

            with mock.patch.object(linear_agent.linear_client, 'linear_query') as mock_query:
                mock_query.return_value = {
                    "data": {"issueCreate": {"success": True, "issue": mock_issue}}
                }

                result = await linear_agent.create_linear_issue(
                    title="Test Issue",
                    description="Test description",
                    issue_type="bug",
                    priority=2
                )

                assert result == mock_issue
                assert result["identifier"] == "ENG-1"

    @pytest.mark.asyncio
    async def test_returns_none_when_no_teams(self):
        """create_linear_issue should return None when no teams exist."""
        with mock.patch.object(linear_agent.linear_client, 'get_team_info') as mock_info:
            mock_info.return_value = {"teams": {"nodes": []}}

            result = await linear_agent.create_linear_issue(
                title="Test Issue",
                description="Test description"
            )

            assert result is None

    @pytest.mark.asyncio
    async def test_returns_none_on_failure(self):
        """create_linear_issue should return None when creation fails."""
        mock_team_info = {
            "teams": {"nodes": [{"id": "team-123", "name": "Eng"}]}
        }

        with mock.patch.object(linear_agent.linear_client, 'get_team_info') as mock_info:
            mock_info.return_value = mock_team_info

            with mock.patch.object(linear_agent.linear_client, 'linear_query') as mock_query:
                mock_query.return_value = {
                    "data": {"issueCreate": {"success": False, "issue": None}}
                }

                result = await linear_agent.create_linear_issue(
                    title="Test Issue",
                    description="Test description"
                )

                assert result is None

    @pytest.mark.asyncio
    async def test_handles_exception(self):
        """create_linear_issue should return None on exception."""
        mock_team_info = {
            "teams": {"nodes": [{"id": "team-123", "name": "Eng"}]}
        }

        with mock.patch.object(linear_agent.linear_client, 'get_team_info') as mock_info:
            mock_info.return_value = mock_team_info

            with mock.patch.object(linear_agent.linear_client, 'linear_query') as mock_query:
                # Simulate exception during issue creation
                mock_query.side_effect = Exception("API error")

                result = await linear_agent.create_linear_issue(
                    title="Test Issue",
                    description="Test description"
                )

                assert result is None

    @pytest.mark.asyncio
    async def test_clamps_priority(self):
        """create_linear_issue should clamp priority to 1-4 range."""
        mock_team_info = {
            "teams": {"nodes": [{"id": "team-123", "name": "Eng"}]}
        }

        with mock.patch.object(linear_agent.linear_client, 'get_team_info') as mock_info:
            mock_info.return_value = mock_team_info

            with mock.patch.object(linear_agent.linear_client, 'linear_query') as mock_query:
                mock_query.return_value = {
                    "data": {"issueCreate": {"success": True, "issue": {"id": "issue-1"}}}
                }

                # Test priority > 4
                await linear_agent.create_linear_issue(
                    title="Test",
                    description="Test",
                    priority=10
                )

                call_args = mock_query.call_args
                variables = call_args[1]["variables"] if "variables" in call_args[1] else call_args[0][1]
                assert variables["input"]["priority"] == 4


class TestProcessSession:
    """Tests for process_session function."""

    @pytest.mark.asyncio
    async def test_creates_issues_from_blockers(self):
        """process_session should create issues from session blockers."""
        session = {
            "summary": "Working on auth",
            "context": {
                "blockers": ["Redis not configured", "API key missing"]
            }
        }

        mock_issues = [
            {"title": "Configure Redis", "description": "Set up Redis", "type": "blocker", "priority": 2}
        ]

        with mock.patch.object(linear_agent, 'analyze_for_issues') as mock_analyze:
            mock_analyze.return_value = mock_issues

            with mock.patch.object(linear_agent, 'create_linear_issue') as mock_create:
                mock_create.return_value = {"id": "issue-1", "identifier": "ENG-1"}

                result = await linear_agent.process_session(session)

                assert len(result) == 1
                mock_analyze.assert_called_once()
                mock_create.assert_called_once()

    @pytest.mark.asyncio
    async def test_returns_empty_list_for_empty_session(self):
        """process_session should return empty list for session without content."""
        session = {}

        result = await linear_agent.process_session(session)

        assert result == []

    @pytest.mark.asyncio
    async def test_handles_session_with_metadata_blockers(self):
        """process_session should handle blockers in metadata field."""
        session = {
            "summary": "Working on feature",
            "metadata": {
                "blockers": ["Waiting for design"]
            }
        }

        with mock.patch.object(linear_agent, 'analyze_for_issues') as mock_analyze:
            mock_analyze.return_value = []

            await linear_agent.process_session(session)

            # Should have called analyze with blocker content
            call_args = mock_analyze.call_args[0][0]
            assert "Waiting for design" in call_args


class TestProcessLearning:
    """Tests for process_learning function."""

    @pytest.mark.asyncio
    async def test_creates_issue_for_bug_learning(self):
        """process_learning should create issue for bug-related learning."""
        learning = {
            "insight": "Found a bug in authentication",
            "tags": ["bug", "auth"]
        }

        mock_issues = [
            {"title": "Auth Bug", "description": "Bug in auth", "type": "bug", "priority": 2}
        ]

        with mock.patch.object(linear_agent, 'analyze_for_issues') as mock_analyze:
            mock_analyze.return_value = mock_issues

            with mock.patch.object(linear_agent, 'create_linear_issue') as mock_create:
                mock_create.return_value = {"id": "issue-1"}

                result = await linear_agent.process_learning(learning)

                assert result is not None
                mock_create.assert_called_once()

    @pytest.mark.asyncio
    async def test_skips_non_bug_learning(self):
        """process_learning should skip learning without bug indicators."""
        learning = {
            "insight": "Learned about React hooks",
            "tags": ["react", "learning"]
        }

        # Should not even call analyze for non-bug content
        with mock.patch.object(linear_agent, 'analyze_for_issues') as mock_analyze:
            result = await linear_agent.process_learning(learning)

            assert result is None
            mock_analyze.assert_not_called()

    @pytest.mark.asyncio
    async def test_handles_text_field_instead_of_insight(self):
        """process_learning should handle 'text' field as fallback."""
        learning = {
            "text": "Error in production deployment",
            "tags": ["error"]
        }

        with mock.patch.object(linear_agent, 'analyze_for_issues') as mock_analyze:
            mock_analyze.return_value = []

            await linear_agent.process_learning(learning)

            # Should have tried to analyze
            mock_analyze.assert_called_once()

    @pytest.mark.asyncio
    async def test_returns_none_when_no_issues_detected(self):
        """process_learning should return None when analysis finds no issues."""
        learning = {
            "insight": "Fix needed for edge case",
            "tags": ["fix"]
        }

        with mock.patch.object(linear_agent, 'analyze_for_issues') as mock_analyze:
            mock_analyze.return_value = []

            result = await linear_agent.process_learning(learning)

            assert result is None


class TestIssueDetection:
    """Tests for issue detection patterns."""

    @pytest.mark.parametrize("content,should_process", [
        ("Found a bug in login", True),
        ("Error handling needs improvement", True),
        ("Need to fix the timeout issue", True),
        ("Problem with caching", True),
        ("Something failed to load", True),  # 'fail' is in indicators
        ("Learned about Python decorators", False),
        ("Implemented new feature", False),
        ("Refactored the code", False),
    ])
    @pytest.mark.asyncio
    async def test_bug_indicator_detection(self, content, should_process):
        """process_learning should detect bug indicators correctly."""
        learning = {"insight": content, "tags": []}

        with mock.patch.object(linear_agent, 'analyze_for_issues') as mock_analyze:
            mock_analyze.return_value = []

            await linear_agent.process_learning(learning)

            if should_process:
                mock_analyze.assert_called_once()
            else:
                mock_analyze.assert_not_called()

    @pytest.mark.parametrize("tags,should_process", [
        (["bug"], True),
        (["error"], True),
        (["fix"], True),
        (["issue"], True),
        (["feature"], False),
        (["docs"], False),
        (["learning"], False),
    ])
    @pytest.mark.asyncio
    async def test_tag_based_detection(self, tags, should_process):
        """process_learning should detect issues based on tags."""
        learning = {"insight": "Some neutral content", "tags": tags}

        with mock.patch.object(linear_agent, 'analyze_for_issues') as mock_analyze:
            mock_analyze.return_value = []

            await linear_agent.process_learning(learning)

            if should_process:
                mock_analyze.assert_called_once()
            else:
                mock_analyze.assert_not_called()
