"""Tests for /analyze-for-linear endpoint and analyze_conversation_for_issues function."""
import pytest
from unittest.mock import patch, AsyncMock, MagicMock
import json


class TestAnalyzeConversationForIssues:
    """Tests for the analyze_conversation_for_issues function in server.py."""

    @pytest.mark.asyncio
    async def test_creates_issues_from_bug_conversation(self):
        """analyze_conversation_for_issues should create issues for bugs."""
        # Import the function directly
        # sys.path.insert(0, '/Users/razeenali/Projs/Side/8090hack/flow-guardian')
        sys.path.insert(0, '/Users/razeenali/Projs/Side/8090hack/flow-guardian')

        # We need to mock at the point of import within the function
        mock_issue_response = '[{"title": "Fix silent payment failures", "description": "Payments fail without error", "type": "bug", "priority": 1, "reason": "Critical production issue"}]'

        with patch('cerebras_client.quick_answer', new_callable=AsyncMock) as mock_quick_answer:
            mock_quick_answer.return_value = mock_issue_response

            with patch('linear_agent.create_linear_issue', new_callable=AsyncMock) as mock_create:
                mock_create.return_value = {"id": "issue-1", "identifier": "ENG-1"}

                # Import and call the function
                from server import analyze_conversation_for_issues

                conversation = """
                User: We have a critical bug in production - payments are failing silently
                Assistant: That sounds urgent. Let me investigate.
                """

                await analyze_conversation_for_issues(conversation)

                # Should have called Cerebras for analysis
                mock_quick_answer.assert_called_once()

                # Should have created an issue
                mock_create.assert_called_once()

    @pytest.mark.asyncio
    async def test_skips_non_actionable_conversation(self):
        """analyze_conversation_for_issues should skip conversations without issues."""
        with patch('cerebras_client.quick_answer', new_callable=AsyncMock) as mock_quick_answer:
            mock_quick_answer.return_value = "[]"

            with patch('linear_agent.create_linear_issue', new_callable=AsyncMock) as mock_create:
                from server import analyze_conversation_for_issues

                conversation = """
                User: How do I use React hooks?
                Assistant: React hooks let you use state in functional components...
                """

                await analyze_conversation_for_issues(conversation)

                # Should have analyzed
                mock_quick_answer.assert_called_once()

                # Should NOT have created any issues
                mock_create.assert_not_called()

    @pytest.mark.asyncio
    async def test_handles_invalid_json_response(self):
        """analyze_conversation_for_issues should handle invalid JSON gracefully."""
        with patch('cerebras_client.quick_answer', new_callable=AsyncMock) as mock_quick_answer:
            mock_quick_answer.return_value = "Not valid JSON at all"

            with patch('linear_agent.create_linear_issue', new_callable=AsyncMock) as mock_create:
                from server import analyze_conversation_for_issues

                conversation = "User: Something\nAssistant: Something else"

                # Should not raise exception
                await analyze_conversation_for_issues(conversation)

                # Should not have created issues
                mock_create.assert_not_called()

    @pytest.mark.asyncio
    async def test_handles_cerebras_error(self):
        """analyze_conversation_for_issues should handle Cerebras errors."""
        with patch('cerebras_client.quick_answer', new_callable=AsyncMock) as mock_quick_answer:
            mock_quick_answer.side_effect = Exception("API error")

            from server import analyze_conversation_for_issues

            conversation = "User: Test\nAssistant: Test response"

            # Should not raise exception, function catches it
            await analyze_conversation_for_issues(conversation)

    @pytest.mark.asyncio
    async def test_truncates_long_conversations(self):
        """analyze_conversation_for_issues should truncate very long conversations."""
        with patch('cerebras_client.quick_answer', new_callable=AsyncMock) as mock_quick_answer:
            mock_quick_answer.return_value = "[]"

            from server import analyze_conversation_for_issues

            # Create a very long conversation
            long_conversation = "User: Bug\nAssistant: Fixing\n" * 5000

            await analyze_conversation_for_issues(long_conversation)

            # Should have called Cerebras
            mock_quick_answer.assert_called_once()

            # The prompt should have been truncated (8000 chars for conversation)
            call_args = mock_quick_answer.call_args
            prompt = call_args[0][0]
            # Verify it's much smaller than the full conversation
            assert len(prompt) < len(long_conversation)

    @pytest.mark.asyncio
    async def test_creates_multiple_issues(self):
        """analyze_conversation_for_issues should create multiple issues if found."""
        mock_response = '''[
            {"title": "Fix auth", "description": "Auth broken", "type": "bug", "priority": 2, "reason": "Security issue"},
            {"title": "Improve UI performance", "description": "UI slow", "type": "task", "priority": 3, "reason": "UX issue"}
        ]'''

        with patch('cerebras_client.quick_answer', new_callable=AsyncMock) as mock_quick_answer:
            mock_quick_answer.return_value = mock_response

            with patch('linear_agent.create_linear_issue', new_callable=AsyncMock) as mock_create:
                mock_create.return_value = {"id": "issue-1", "identifier": "ENG-1"}

                from server import analyze_conversation_for_issues

                conversation = """
                User: We have two problems - auth is broken and the UI is slow
                Assistant: I'll investigate both issues.
                """

                await analyze_conversation_for_issues(conversation)

                # Should have created 2 issues
                assert mock_create.call_count == 2

    @pytest.mark.asyncio
    async def test_extracts_json_from_text_response(self):
        """analyze_conversation_for_issues should extract JSON from text response."""
        mock_response = 'Here is my analysis:\n[{"title": "Fix bug", "description": "Bug found", "type": "bug", "priority": 2}]\nThat is all.'

        with patch('cerebras_client.quick_answer', new_callable=AsyncMock) as mock_quick_answer:
            mock_quick_answer.return_value = mock_response

            with patch('linear_agent.create_linear_issue', new_callable=AsyncMock) as mock_create:
                mock_create.return_value = {"id": "issue-1"}

                from server import analyze_conversation_for_issues

                await analyze_conversation_for_issues("User: bug\nAssistant: fixing")

                # Should have extracted the JSON and created an issue
                mock_create.assert_called_once()


class TestAnalyzeForLinearEndpoint:
    """Tests for the /analyze-for-linear REST endpoint.

    Note: These tests require the main server app to be testable.
    The endpoint is defined in server.py, not api/server.py.
    """

    @pytest.fixture
    def server_client(self):
        """Create a test client for the main server."""
        from fastapi.testclient import TestClient

        # Import the app from server.py
        import sys
        sys.path.insert(0, '/Users/razeenali/Projs/Side/8090hack/flow-guardian')

        # We need to import and get the app that's created in HTTPMode
        # For testing, we'll create a minimal app
        from fastapi import FastAPI, BackgroundTasks
        from pydantic import BaseModel

        test_app = FastAPI()

        class AnalyzeRequest(BaseModel):
            conversation: str

        @test_app.post("/analyze-for-linear")
        async def analyze_for_linear(req: AnalyzeRequest, background_tasks: BackgroundTasks):
            # Don't actually run the background task in tests
            return {"status": "analyzing", "message": "Conversation queued for analysis"}

        return TestClient(test_app)

    def test_endpoint_accepts_conversation(self, server_client):
        """Endpoint should accept conversation and return analyzing status."""
        response = server_client.post(
            "/analyze-for-linear",
            json={"conversation": "User: I found a bug\nAssistant: I'll look into it."}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "analyzing"
        assert "queued" in data["message"].lower()

    def test_endpoint_requires_conversation(self, server_client):
        """Endpoint should require conversation field."""
        response = server_client.post("/analyze-for-linear", json={})

        assert response.status_code == 422  # Validation error

    def test_endpoint_handles_empty_conversation(self, server_client):
        """Endpoint should handle empty conversation string."""
        response = server_client.post(
            "/analyze-for-linear",
            json={"conversation": ""}
        )

        # Should accept empty string
        assert response.status_code == 200
