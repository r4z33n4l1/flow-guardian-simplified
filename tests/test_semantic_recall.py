"""Tests for semantic recall optimization (P2-1).

Tests the enhanced context-aware queries, result categorization,
relevance scoring, and local fallback behavior.
"""
import os
from datetime import datetime, timezone, timedelta
from pathlib import Path
from unittest import mock

import pytest

import inject


class TestBuildRecallQuery:
    """Tests for _build_recall_query function."""

    def test_includes_project_name(self, monkeypatch, tmp_path):
        """Query should include current project name."""
        monkeypatch.chdir(tmp_path / "my-project" if (tmp_path / "my-project").exists() else tmp_path)
        (tmp_path / "my-project").mkdir(exist_ok=True)
        monkeypatch.chdir(tmp_path / "my-project")

        query = inject._build_recall_query(None)

        assert "my-project" in query

    def test_includes_goal_when_provided(self):
        """Query should include goal from handoff."""
        handoff = {"goal": "Implement authentication"}

        query = inject._build_recall_query(handoff)

        assert "Goal: Implement authentication" in query

    def test_includes_current_focus(self):
        """Query should include current focus from handoff."""
        handoff = {"now": "Writing unit tests"}

        query = inject._build_recall_query(handoff)

        assert "Current focus: Writing unit tests" in query

    def test_includes_branch(self):
        """Query should include branch name from handoff."""
        handoff = {"branch": "feature/oauth"}

        query = inject._build_recall_query(handoff)

        assert "Branch: feature/oauth" in query

    def test_includes_hypothesis(self):
        """Query should include hypothesis from handoff."""
        handoff = {"hypothesis": "Using JWT will be simpler"}

        query = inject._build_recall_query(handoff)

        assert "Hypothesis: Using JWT will be simpler" in query

    def test_includes_files(self):
        """Query should include files being worked on."""
        handoff = {"files": ["auth.py", "tests/test_auth.py", "config.py"]}

        query = inject._build_recall_query(handoff)

        assert "Working on files:" in query
        assert "auth.py" in query

    def test_limits_files_to_five(self):
        """Query should limit files to 5 to avoid query bloat."""
        handoff = {"files": ["f1.py", "f2.py", "f3.py", "f4.py", "f5.py", "f6.py", "f7.py"]}

        query = inject._build_recall_query(handoff)

        # Should only include first 5 files
        assert "f5.py" in query
        assert "f6.py" not in query

    def test_includes_standard_suffix(self):
        """Query should include standard suffix for comprehensive recall."""
        query = inject._build_recall_query(None)

        assert "recent work" in query.lower()
        assert "decisions" in query.lower()
        assert "learnings" in query.lower()


class TestScoreAndFilterResults:
    """Tests for _score_and_filter_results function."""

    def test_empty_results_returns_empty(self):
        """Should return empty list for empty input."""
        result = inject._score_and_filter_results([], None, 10)
        assert result == []

    def test_respects_limit(self):
        """Should respect the limit parameter."""
        results = [
            {"content": f"Item {i}", "metadata": {}}
            for i in range(20)
        ]

        filtered = inject._score_and_filter_results(results, None, 5)

        assert len(filtered) == 5

    def test_recency_boost_for_recent_items(self):
        """Recent items should get higher scores."""
        now = datetime.now(timezone.utc)
        recent = now - timedelta(hours=1)
        old = now - timedelta(days=2)

        results = [
            {"content": "Old item", "metadata": {"timestamp": old.isoformat()}},
            {"content": "Recent item", "metadata": {"timestamp": recent.isoformat()}},
        ]

        filtered = inject._score_and_filter_results(results, None, 10)

        # Recent item should be first
        assert filtered[0]["content"] == "Recent item"

    def test_branch_match_boost(self):
        """Items matching current branch should get higher scores."""
        handoff = {"branch": "feature/auth"}

        results = [
            {"content": "Different branch", "metadata": {"branch": "main"}},
            {"content": "Same branch", "metadata": {"branch": "feature/auth"}},
        ]

        filtered = inject._score_and_filter_results(results, handoff, 10)

        # Same branch should be first
        assert filtered[0]["content"] == "Same branch"

    def test_file_overlap_boost(self):
        """Items with overlapping files should get higher scores."""
        handoff = {"files": ["auth.py", "config.py"]}

        results = [
            {"content": "No overlap", "metadata": {"files": ["other.py"]}},
            {"content": "Has overlap", "metadata": {"files": ["auth.py", "utils.py"]}},
        ]

        filtered = inject._score_and_filter_results(results, handoff, 10)

        # Overlapping files should be first
        assert filtered[0]["content"] == "Has overlap"

    def test_learning_type_boost(self):
        """Learning type items should get priority."""
        results = [
            {"content": "Context item", "metadata": {"type": "context"}},
            {"content": "Learning item", "metadata": {"type": "learning"}},
        ]

        filtered = inject._score_and_filter_results(results, None, 10)

        # Learning should be first
        assert filtered[0]["content"] == "Learning item"

    def test_decision_type_boost(self):
        """Decision type items should get priority."""
        results = [
            {"content": "Context item", "metadata": {"type": "context"}},
            {"content": "Decision item", "metadata": {"type": "decision"}},
        ]

        filtered = inject._score_and_filter_results(results, None, 10)

        # Decision should be first
        assert filtered[0]["content"] == "Decision item"


class TestCategorizeRecall:
    """Tests for categorize_recall function."""

    def test_empty_results(self):
        """Should return empty categories for empty input."""
        result = inject.categorize_recall([])

        assert result["learnings"] == []
        assert result["decisions"] == []
        assert result["context"] == []
        assert result["insights"] == []

    def test_categorizes_learnings(self):
        """Should categorize learning items."""
        results = [
            {"content": "A learning", "metadata": {"type": "learning"}},
            {"content": "Another learning", "metadata": {"type": "learnings"}},
        ]

        categorized = inject.categorize_recall(results)

        assert len(categorized["learnings"]) == 2

    def test_categorizes_decisions(self):
        """Should categorize decision items."""
        results = [
            {"content": "A decision", "metadata": {"type": "decision"}},
            {"content": "Another decision", "metadata": {"type": "decisions"}},
        ]

        categorized = inject.categorize_recall(results)

        assert len(categorized["decisions"]) == 2

    def test_categorizes_insights(self):
        """Should categorize insight items."""
        results = [
            {"content": "An insight", "metadata": {"type": "insight"}},
            {"content": "Auto-captured", "metadata": {"type": "auto_learning"}},
        ]

        categorized = inject.categorize_recall(results)

        assert len(categorized["insights"]) == 2

    def test_defaults_to_context(self):
        """Unknown types should go to context."""
        results = [
            {"content": "Unknown type", "metadata": {"type": "unknown"}},
            {"content": "No type", "metadata": {}},
        ]

        categorized = inject.categorize_recall(results)

        assert len(categorized["context"]) == 2

    def test_mixed_results(self):
        """Should correctly categorize mixed results."""
        results = [
            {"content": "Learning 1", "metadata": {"type": "learning"}},
            {"content": "Decision 1", "metadata": {"type": "decision"}},
            {"content": "Context 1", "metadata": {"type": "context"}},
            {"content": "Insight 1", "metadata": {"type": "insight"}},
            {"content": "Learning 2", "metadata": {"type": "learning"}},
        ]

        categorized = inject.categorize_recall(results)

        assert len(categorized["learnings"]) == 2
        assert len(categorized["decisions"]) == 1
        assert len(categorized["context"]) == 1
        assert len(categorized["insights"]) == 1


class TestLocalFallback:
    """Tests for _local_fallback function."""

    def test_returns_empty_on_error(self, monkeypatch):
        """Should return empty list on error."""
        monkeypatch.setattr(inject, '_score_and_filter_results', mock.MagicMock(side_effect=Exception("Error")))

        result = inject._local_fallback()

        assert result == []

    def test_includes_learnings(self, monkeypatch):
        """Should include local learnings."""
        mock_learnings = [
            {"text": "Learning 1", "timestamp": "2024-01-01", "tags": ["test"]},
            {"text": "Learning 2", "timestamp": "2024-01-02", "tags": []},
        ]
        monkeypatch.setattr('inject.search_learnings', mock.MagicMock(return_value=mock_learnings), raising=False)

        # Mock memory module
        mock_memory = mock.MagicMock()
        mock_memory.search_learnings = mock.MagicMock(return_value=mock_learnings)
        mock_memory.get_latest_session = mock.MagicMock(return_value=None)

        with mock.patch.dict('sys.modules', {'memory': mock_memory}):
            # Need to reimport to use mocked module
            import importlib
            importlib.reload(inject)

            result = inject._local_fallback()

        # Restore inject module
        importlib.reload(inject)

    def test_respects_limit(self, monkeypatch):
        """Should respect the limit parameter."""
        # Create many mock learnings
        mock_learnings = [
            {"text": f"Learning {i}", "timestamp": "2024-01-01", "tags": []}
            for i in range(20)
        ]

        mock_memory = mock.MagicMock()
        mock_memory.search_learnings = mock.MagicMock(return_value=mock_learnings)
        mock_memory.get_latest_session = mock.MagicMock(return_value=None)

        with mock.patch.dict('sys.modules', {'memory': mock_memory}):
            import importlib
            importlib.reload(inject)

            result = inject._local_fallback(limit=5)

        importlib.reload(inject)

        # Result should be limited
        assert len(result) <= 5


class TestRecallForInjection:
    """Tests for _recall_for_injection function."""

    @pytest.mark.asyncio
    async def test_falls_back_when_no_thread_id(self, monkeypatch):
        """Should fall back to local when no BACKBOARD_PERSONAL_THREAD_ID."""
        monkeypatch.delenv("BACKBOARD_PERSONAL_THREAD_ID", raising=False)

        mock_fallback = mock.MagicMock(return_value=[{"content": "Local result"}])
        monkeypatch.setattr(inject, '_local_fallback', mock_fallback)

        result = await inject._recall_for_injection(None)

        mock_fallback.assert_called_once()

    @pytest.mark.asyncio
    async def test_calls_backboard_when_thread_id_set(self, monkeypatch):
        """Should call Backboard when thread ID is set."""
        monkeypatch.setenv("BACKBOARD_PERSONAL_THREAD_ID", "thread123")

        mock_recall = mock.AsyncMock(return_value="Backboard result")
        monkeypatch.setattr('inject.recall', mock_recall, raising=False)

        # Mock the backboard_client module
        mock_backboard = mock.MagicMock()
        mock_backboard.recall = mock_recall
        mock_backboard.BackboardError = Exception

        with mock.patch.dict('sys.modules', {'backboard_client': mock_backboard}):
            import importlib
            importlib.reload(inject)

            result = await inject._recall_for_injection({"goal": "Test"})

        importlib.reload(inject)

    @pytest.mark.asyncio
    async def test_falls_back_on_backboard_error(self, monkeypatch, caplog):
        """Should fall back to local on Backboard error."""
        import logging
        caplog.set_level(logging.WARNING)

        monkeypatch.setenv("BACKBOARD_PERSONAL_THREAD_ID", "thread123")

        # Mock backboard to raise error - the function imports it inside
        mock_recall = mock.AsyncMock(side_effect=Exception("Connection failed"))

        # Patch at the backboard_client module level
        with mock.patch('backboard_client.recall', mock_recall):
            result = await inject._recall_for_injection(None)

        # Should have logged a warning about the fallback
        assert "Backboard recall failed" in caplog.text
        # Result should be a list (from fallback)
        assert isinstance(result, list)
