"""Tests for the report_generator.py module."""
import os
from datetime import datetime
from unittest import mock

import pytest

import report_generator


class TestGenerateBugReport:
    """Tests for generate_bug_report function."""

    @pytest.mark.asyncio
    async def test_generates_report_with_issues(self):
        """generate_bug_report should create markdown report with issues."""
        mock_issues = [
            {
                "identifier": "BUG-1",
                "title": "Login fails",
                "state": {"name": "In Progress", "type": "started"},
                "priorityLabel": "Urgent",
                "assignee": {"name": "John Doe"},
                "createdAt": "2026-01-15T10:00:00",
                "labels": {"nodes": [{"name": "bug"}, {"name": "auth"}]},
                "description": "Users cannot login with valid credentials"
            },
            {
                "identifier": "BUG-2",
                "title": "Crash on upload",
                "state": {"name": "Done", "type": "completed"},
                "priorityLabel": "High",
                "assignee": None,
                "createdAt": "2026-01-10T10:00:00",
                "labels": {"nodes": []},
                "description": "App crashes when uploading large files"
            }
        ]

        with mock.patch.object(report_generator.linear_client, 'get_all_issues') as mock_issues_fn:
            mock_issues_fn.return_value = mock_issues

            result = await report_generator.generate_bug_report(days=30)

            assert "# Bug & Issue Report" in result
            assert "BUG-1" in result
            assert "Login fails" in result
            assert "In Progress" in result
            assert "John Doe" in result
            assert "BUG-2" in result

    @pytest.mark.asyncio
    async def test_handles_empty_issues(self):
        """generate_bug_report should handle empty issue list."""
        with mock.patch.object(report_generator.linear_client, 'get_all_issues') as mock_issues_fn:
            mock_issues_fn.return_value = []

            result = await report_generator.generate_bug_report(days=30)

            assert "# Bug & Issue Report" in result
            assert "Total Issues: 0" in result

    @pytest.mark.asyncio
    async def test_groups_by_state(self):
        """generate_bug_report should group issues by state."""
        mock_issues = [
            {"identifier": "A-1", "title": "Issue A", "state": {"name": "Done"}},
            {"identifier": "A-2", "title": "Issue B", "state": {"name": "In Progress"}},
            {"identifier": "A-3", "title": "Issue C", "state": {"name": "Done"}},
        ]

        with mock.patch.object(report_generator.linear_client, 'get_all_issues') as mock_issues_fn:
            mock_issues_fn.return_value = mock_issues

            result = await report_generator.generate_bug_report()

            assert "## Done" in result
            assert "## In Progress" in result
            # Done should have 2 issues
            assert result.count("Done") >= 2


class TestGenerateFaqFromSolved:
    """Tests for generate_faq_from_solved function."""

    @pytest.mark.asyncio
    async def test_generates_faq_with_issues_and_learnings(self):
        """generate_faq_from_solved should include solved issues and learnings."""
        mock_issues = [
            {
                "identifier": "SOLVED-1",
                "title": "How to fix timeout?",
                "state": {"type": "completed"},
                "description": "Connection times out after 30s",
                "comments": {"nodes": [{"body": "Increase timeout to 60s in config"}]}
            }
        ]

        mock_learnings = [
            {
                "insight": "Use retry logic for API calls",
                "tags": ["api", "reliability"],
                "source": "session"
            }
        ]

        with mock.patch.object(report_generator.linear_client, 'get_all_issues') as mock_issues_fn:
            mock_issues_fn.return_value = mock_issues

            with mock.patch.object(report_generator.memory, 'get_all_learnings') as mock_learnings_fn:
                mock_learnings_fn.return_value = mock_learnings

                result = await report_generator.generate_faq_from_solved()

                assert "# FAQ" in result
                assert "How to fix timeout?" in result
                assert "Increase timeout to 60s" in result
                assert "retry logic" in result

    @pytest.mark.asyncio
    async def test_handles_no_solved_issues(self):
        """generate_faq_from_solved should handle no solved issues."""
        mock_issues = [
            {"state": {"type": "started"}, "title": "In progress issue"}
        ]

        with mock.patch.object(report_generator.linear_client, 'get_all_issues') as mock_issues_fn:
            mock_issues_fn.return_value = mock_issues

            with mock.patch.object(report_generator.memory, 'get_all_learnings') as mock_learnings_fn:
                mock_learnings_fn.return_value = []

                result = await report_generator.generate_faq_from_solved()

                assert "# FAQ" in result
                assert "0 resolved issues" in result

    @pytest.mark.asyncio
    async def test_handles_text_field_in_learnings(self):
        """generate_faq_from_solved should handle 'text' field as fallback."""
        mock_learnings = [
            {"text": "Old learning format", "tags": ["legacy"]}
        ]

        with mock.patch.object(report_generator.linear_client, 'get_all_issues') as mock_issues_fn:
            mock_issues_fn.return_value = []

            with mock.patch.object(report_generator.memory, 'get_all_learnings') as mock_learnings_fn:
                mock_learnings_fn.return_value = mock_learnings

                result = await report_generator.generate_faq_from_solved()

                assert "Old learning format" in result


class TestGenerateWeeklySummary:
    """Tests for generate_weekly_summary function."""

    @pytest.mark.asyncio
    async def test_generates_weekly_summary(self):
        """generate_weekly_summary should create comprehensive summary."""
        mock_issues = [
            {"identifier": "ENG-1", "title": "New feature", "state": {"name": "Done"}},
            {"identifier": "ENG-2", "title": "Bug fix", "state": {"name": "In Progress"}}
        ]

        mock_sessions = [
            {"summary": "Worked on auth", "timestamp": "2026-01-17T10:00:00", "branch": "main"},
            {"summary": "Fixed tests", "timestamp": "2026-01-16T10:00:00", "branch": "fix-tests"}
        ]

        mock_learnings = [
            {"insight": "Always write tests first", "tags": ["tdd"]}
        ]

        with mock.patch.object(report_generator.linear_client, 'get_all_issues') as mock_issues_fn:
            mock_issues_fn.return_value = mock_issues

            with mock.patch.object(report_generator.memory, 'list_sessions') as mock_sessions_fn:
                mock_sessions_fn.return_value = mock_sessions

                with mock.patch.object(report_generator.memory, 'get_all_learnings') as mock_learnings_fn:
                    mock_learnings_fn.return_value = mock_learnings

                    result = await report_generator.generate_weekly_summary()

                    assert "# Weekly Summary Report" in result
                    assert "Last 7 days" in result
                    assert "Linear Issues**: 2" in result
                    assert "Coding Sessions**: 2" in result
                    assert "ENG-1" in result
                    assert "Worked on auth" in result
                    assert "Always write tests first" in result

    @pytest.mark.asyncio
    async def test_handles_empty_data(self):
        """generate_weekly_summary should handle empty data gracefully."""
        with mock.patch.object(report_generator.linear_client, 'get_all_issues') as mock_issues_fn:
            mock_issues_fn.return_value = []

            with mock.patch.object(report_generator.memory, 'list_sessions') as mock_sessions_fn:
                mock_sessions_fn.return_value = []

                with mock.patch.object(report_generator.memory, 'get_all_learnings') as mock_learnings_fn:
                    mock_learnings_fn.return_value = []

                    result = await report_generator.generate_weekly_summary()

                    assert "# Weekly Summary Report" in result
                    assert "Linear Issues**: 0" in result


class TestSaveReport:
    """Tests for save_report function."""

    @pytest.mark.asyncio
    async def test_saves_report_to_file(self, tmp_path, monkeypatch):
        """save_report should write content to file."""
        # Mock the reports directory
        reports_dir = str(tmp_path / "reports")
        monkeypatch.setattr(os.path, 'expanduser', lambda x: str(tmp_path) if "~" in x else x)

        with mock.patch('os.makedirs') as mock_makedirs:
            with mock.patch('builtins.open', mock.mock_open()) as mock_file:
                result = await report_generator.save_report("# Test Report", "test.md")

                assert "test.md" in result
                mock_file.assert_called_once()

    @pytest.mark.asyncio
    async def test_creates_directory_if_not_exists(self, tmp_path, monkeypatch):
        """save_report should create reports directory."""
        reports_dir = str(tmp_path / "reports")

        with mock.patch('os.makedirs') as mock_makedirs:
            with mock.patch('builtins.open', mock.mock_open()):
                await report_generator.save_report("# Test", "test.md")

                mock_makedirs.assert_called()


class TestReportContent:
    """Tests for report content formatting."""

    @pytest.mark.asyncio
    async def test_bug_report_truncates_long_descriptions(self):
        """generate_bug_report should truncate long descriptions."""
        long_desc = "A" * 300  # 300 character description
        mock_issues = [
            {
                "identifier": "LONG-1",
                "title": "Issue with long desc",
                "state": {"name": "Open"},
                "description": long_desc
            }
        ]

        with mock.patch.object(report_generator.linear_client, 'get_all_issues') as mock_fn:
            mock_fn.return_value = mock_issues

            result = await report_generator.generate_bug_report()

            # Description should be truncated with "..."
            assert "..." in result
            # Full description shouldn't be in output
            assert long_desc not in result

    @pytest.mark.asyncio
    async def test_faq_limits_items(self):
        """generate_faq_from_solved should limit items to prevent huge reports."""
        # Create 30 learnings
        mock_learnings = [
            {"insight": f"Learning {i}", "tags": []}
            for i in range(30)
        ]

        with mock.patch.object(report_generator.linear_client, 'get_all_issues') as mock_issues_fn:
            mock_issues_fn.return_value = []

            with mock.patch.object(report_generator.memory, 'get_all_learnings') as mock_learnings_fn:
                mock_learnings_fn.return_value = mock_learnings

                result = await report_generator.generate_faq_from_solved()

                # Should only include first 20 learnings
                assert "Learning 0" in result
                assert "Learning 19" in result
                # Learning 25 should not be in output
                assert "Learning 25" not in result


class TestEdgeCases:
    """Tests for edge cases and error handling."""

    @pytest.mark.asyncio
    async def test_handles_missing_fields(self):
        """Reports should handle issues with missing optional fields."""
        mock_issues = [
            {
                "identifier": "MINIMAL-1",
                "title": "Minimal issue",
                "state": {"name": "Open"}
                # No description, assignee, labels, etc.
            }
        ]

        with mock.patch.object(report_generator.linear_client, 'get_all_issues') as mock_fn:
            mock_fn.return_value = mock_issues

            result = await report_generator.generate_bug_report()

            assert "MINIMAL-1" in result
            assert "Minimal issue" in result
            # Should show "Unassigned" for missing assignee
            assert "Unassigned" in result

    @pytest.mark.asyncio
    async def test_handles_none_values(self):
        """Reports should handle None values gracefully."""
        # Sessions with None values but valid structure
        mock_sessions = [
            {"summary": "Test session", "timestamp": "2026-01-17T10:00:00", "branch": "main"}
        ]

        with mock.patch.object(report_generator.linear_client, 'get_all_issues') as mock_issues_fn:
            mock_issues_fn.return_value = []

            with mock.patch.object(report_generator.memory, 'list_sessions') as mock_sessions_fn:
                mock_sessions_fn.return_value = mock_sessions

                with mock.patch.object(report_generator.memory, 'get_all_learnings') as mock_learnings_fn:
                    # Learnings with None insight (edge case)
                    mock_learnings_fn.return_value = [
                        {"insight": None, "text": None, "tags": []}
                    ]

                    # Should not raise exception
                    result = await report_generator.generate_weekly_summary()

                    assert "# Weekly Summary Report" in result
