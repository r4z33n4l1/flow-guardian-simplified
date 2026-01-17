"""Tests for tldr.py module.

Tests cover:
- estimate_tokens: Token count estimation
- summarize_context: Content summarization at different levels
- summarize_handoff: Handoff data to TLDR string
- summarize_recall: Recall results summarization
- auto_summarize: Automatic level selection
- Fallback behavior when Cerebras unavailable
"""
import pytest
from unittest.mock import patch, MagicMock

from tldr import (
    estimate_tokens,
    summarize_context,
    summarize_handoff,
    summarize_recall,
    auto_summarize,
    THRESHOLD_NO_TLDR,
    THRESHOLD_L1,
    THRESHOLD_L2,
)
from cerebras_client import CerebrasError


# ============ estimate_tokens TESTS ============

class TestEstimateTokens:
    """Tests for estimate_tokens function."""

    def test_empty_string_returns_zero(self):
        """Empty string returns 0 tokens."""
        assert estimate_tokens("") == 0

    def test_none_returns_zero(self):
        """None input returns 0 tokens."""
        assert estimate_tokens(None) == 0

    def test_short_text(self):
        """Short text estimation (~4 chars per token)."""
        text = "Hello world"  # 11 chars
        result = estimate_tokens(text)
        assert result == 2  # 11 // 4 = 2

    def test_longer_text(self):
        """Longer text estimation."""
        text = "This is a longer piece of text for testing"  # 43 chars
        result = estimate_tokens(text)
        assert result == 10  # 43 // 4 = 10

    def test_multiline_text(self):
        """Multiline text estimation."""
        text = "Line 1\nLine 2\nLine 3\n"  # 21 chars
        result = estimate_tokens(text)
        assert result == 5  # 21 // 4 = 5

    def test_reasonably_accurate(self):
        """Token estimation is reasonably accurate for typical code."""
        # Typical code snippet
        code = """
def hello_world():
    print("Hello, world!")
    return True
"""
        tokens = estimate_tokens(code)
        # Should be roughly 15-20 tokens for this code
        assert 10 <= tokens <= 25


# ============ summarize_context TESTS ============

class TestSummarizeContext:
    """Tests for summarize_context function."""

    def test_empty_content_returns_empty(self):
        """Empty content returns empty string."""
        assert summarize_context("") == ""
        assert summarize_context("   ") == ""

    def test_small_content_returned_as_is(self):
        """Small content (< 500 tokens) returned as-is for L1-L3."""
        small_content = "Working on authentication feature."
        result = summarize_context(small_content, "L1")
        assert result == small_content

    def test_l0_always_summarizes(self):
        """L0 always summarizes to file paths."""
        content = "Working on src/auth.py and tests/test_auth.py"
        with patch('tldr.complete') as mock_complete:
            mock_complete.return_value = "src/auth.py\ntests/test_auth.py"
            result = summarize_context(content, "L0")
            assert mock_complete.called
            assert "auth.py" in result

    def test_invalid_level_defaults_to_l1(self):
        """Invalid level defaults to L1."""
        content = "Some content"
        with patch('tldr.logger') as mock_logger:
            summarize_context(content, "INVALID")
            mock_logger.warning.assert_called()

    @patch('tldr.complete')
    def test_large_content_gets_tldr(self, mock_complete):
        """Large content gets TLDR via Cerebras."""
        mock_complete.return_value = "Summarized content here."
        # Create content that exceeds threshold
        large_content = "x" * (THRESHOLD_NO_TLDR * 5)  # > 500 tokens

        result = summarize_context(large_content, "L1")

        mock_complete.assert_called_once()
        assert result == "Summarized content here."

    @patch('tldr.complete')
    def test_l2_prompt_is_detailed(self, mock_complete):
        """L2 prompts for detailed summary."""
        mock_complete.return_value = "Detailed summary."
        large_content = "x" * (THRESHOLD_NO_TLDR * 5)

        summarize_context(large_content, "L2")

        # Check that prompt mentions bullet points (L2 characteristic)
        call_args = mock_complete.call_args
        prompt = call_args.kwargs.get('prompt') or call_args[0][0]
        assert "bullet points" in prompt.lower()

    def test_cerebras_fallback(self):
        """Falls back gracefully when Cerebras unavailable."""
        large_content = "x" * (THRESHOLD_NO_TLDR * 5)

        with patch('tldr.complete') as mock_complete:
            mock_complete.side_effect = CerebrasError("API unavailable")
            result = summarize_context(large_content, "L1")

            # Should return truncated content
            assert len(result) <= len(large_content)
            assert "truncated" in result or result.startswith("x")


# ============ summarize_handoff TESTS ============

class TestSummarizeHandoff:
    """Tests for summarize_handoff function."""

    def test_empty_handoff_returns_empty(self):
        """Empty handoff returns empty string."""
        assert summarize_handoff({}) == ""
        assert summarize_handoff(None) == ""

    def test_l0_returns_files_only(self):
        """L0 returns only file paths."""
        handoff = {
            "goal": "Build authentication",
            "now": "Testing JWT",
            "files": ["src/auth.py", "tests/test_auth.py"],
            "branch": "feature/auth",
        }
        result = summarize_handoff(handoff, "L0")
        assert "src/auth.py" in result
        assert "tests/test_auth.py" in result
        assert "Build authentication" not in result

    def test_l0_empty_files(self):
        """L0 with no files returns empty."""
        handoff = {"goal": "Work", "now": "Testing"}
        result = summarize_handoff(handoff, "L0")
        assert result == ""

    def test_l1_includes_goal_and_focus(self):
        """L1 includes goal, focus, files, branch."""
        handoff = {
            "goal": "Implement JWT auth",
            "now": "Debugging token expiry",
            "files": ["auth.py"],
            "branch": "fix/jwt",
        }
        result = summarize_handoff(handoff, "L1")

        assert "Implement JWT auth" in result
        assert "Debugging token expiry" in result
        assert "auth.py" in result
        assert "fix/jwt" in result

    def test_l1_excludes_hypothesis(self):
        """L1 excludes hypothesis details."""
        handoff = {
            "goal": "Work",
            "now": "Testing",
            "hypothesis": "Secret hypothesis",
        }
        result = summarize_handoff(handoff, "L1")
        assert "Secret hypothesis" not in result

    def test_l2_includes_hypothesis(self):
        """L2 includes hypothesis."""
        handoff = {
            "goal": "Work",
            "now": "Testing",
            "hypothesis": "Token format issue",
        }
        result = summarize_handoff(handoff, "L2")
        assert "Token format issue" in result

    def test_l2_includes_outcome(self):
        """L2 includes outcome."""
        handoff = {
            "goal": "Work",
            "now": "Testing",
            "outcome": "Fixed the bug",
        }
        result = summarize_handoff(handoff, "L2")
        assert "Fixed the bug" in result

    def test_l1_truncates_many_files(self):
        """L1 truncates file list when > 5 files."""
        handoff = {
            "goal": "Refactoring",
            "now": "Updating imports",
            "files": ["a.py", "b.py", "c.py", "d.py", "e.py", "f.py", "g.py"],
        }
        result = summarize_handoff(handoff, "L1")
        assert "(+2 more)" in result

    def test_l2_shows_all_files(self):
        """L2 shows all files."""
        handoff = {
            "goal": "Refactoring",
            "now": "Updating",
            "files": ["a.py", "b.py", "c.py", "d.py", "e.py", "f.py", "g.py"],
        }
        result = summarize_handoff(handoff, "L2")
        assert "g.py" in result
        assert "(+2 more)" not in result


# ============ summarize_recall TESTS ============

class TestSummarizeRecall:
    """Tests for summarize_recall function."""

    def test_empty_results_returns_empty(self):
        """Empty results returns empty string."""
        assert summarize_recall([]) == ""

    def test_l0_returns_counts(self):
        """L0 returns item counts by category."""
        results = [
            {"content": "Learning 1", "metadata": {"type": "learnings"}},
            {"content": "Learning 2", "metadata": {"type": "learnings"}},
            {"content": "Decision 1", "metadata": {"type": "decisions"}},
        ]
        result = summarize_recall(results, "L0")
        assert "2 learnings" in result
        assert "1 decisions" in result

    def test_l1_returns_snippets(self):
        """L1 returns snippets with counts."""
        results = [
            {"content": "Important learning about tokens", "metadata": {"type": "learnings"}},
            {"content": "Another learning", "metadata": {"type": "learnings"}},
        ]
        result = summarize_recall(results, "L1")
        assert "Important learning" in result
        assert "(+1 more)" in result

    def test_handles_text_field(self):
        """Handles 'text' field as alternative to 'content'."""
        results = [
            {"text": "Learning from text field", "metadata": {"type": "learnings"}},
        ]
        result = summarize_recall(results, "L1")
        assert "Learning from text field" in result

    def test_categorizes_by_type(self):
        """Categories results by type."""
        results = [
            {"content": "Learning A", "metadata": {"type": "learnings"}},
            {"content": "Decision B", "metadata": {"type": "decisions"}},
            {"content": "Context C", "metadata": {"type": "context"}},
        ]
        result = summarize_recall(results, "L2")
        assert "Learnings" in result
        assert "Decisions" in result
        assert "Context" in result

    def test_unknown_type_goes_to_context(self):
        """Unknown types go to context category."""
        results = [
            {"content": "Mystery item", "metadata": {"type": "unknown_type"}},
        ]
        result = summarize_recall(results, "L1")
        assert "Context" in result

    def test_missing_metadata_goes_to_context(self):
        """Missing metadata defaults to context."""
        results = [
            {"content": "No metadata item"},
        ]
        result = summarize_recall(results, "L1")
        assert "No metadata item" in result


# ============ auto_summarize TESTS ============

class TestAutoSummarize:
    """Tests for auto_summarize function."""

    def test_empty_returns_empty(self):
        """Empty content returns empty."""
        assert auto_summarize("") == ""

    def test_small_content_returned_as_is(self):
        """Small content returned as-is."""
        small = "Just a small piece of text."
        assert auto_summarize(small) == small

    @patch('tldr.complete')
    def test_medium_content_uses_l1(self, mock_complete):
        """Medium content uses L1 summarization."""
        mock_complete.return_value = "L1 summary"
        # Create medium content (500-2000 tokens = 2000-8000 chars)
        medium = "word " * 600  # ~3000 chars = ~750 tokens

        result = auto_summarize(medium)

        mock_complete.assert_called_once()
        assert result == "L1 summary"

    @patch('tldr.complete')
    def test_large_content_uses_l2(self, mock_complete):
        """Large content uses L2 summarization."""
        mock_complete.return_value = "L2 summary"
        # Create large content (> 5000 tokens = > 20000 chars)
        large = "word " * 5000  # ~25000 chars = ~6250 tokens

        result = auto_summarize(large)

        mock_complete.assert_called_once()
        # Check that L2 prompt characteristics were used
        call_args = mock_complete.call_args
        prompt = call_args.kwargs.get('prompt') or call_args[0][0]
        assert "bullet points" in prompt.lower()


# ============ INTEGRATION TESTS ============

class TestTLDRIntegration:
    """Integration tests for TLDR system."""

    def test_handoff_to_recall_workflow(self):
        """Tests summarizing handoff and recall together."""
        handoff = {
            "goal": "Build auth system",
            "now": "Testing JWT validation",
            "branch": "feature/auth",
            "files": ["auth.py", "jwt.py"],
        }

        recall = [
            {"content": "JWT tokens need iat and exp claims", "metadata": {"type": "learnings"}},
            {"content": "Using HS256 for simplicity", "metadata": {"type": "decisions"}},
        ]

        handoff_summary = summarize_handoff(handoff, "L1")
        recall_summary = summarize_recall(recall, "L1")

        assert "auth system" in handoff_summary.lower()
        assert "jwt" in handoff_summary.lower()
        assert "iat" in recall_summary or "Learnings" in recall_summary

    def test_all_levels_produce_output(self):
        """All levels produce valid output."""
        content = "Working on authentication with JWT tokens in auth.py"

        for level in ["L0", "L1", "L2", "L3"]:
            result = summarize_context(content, level)
            # All levels should produce some output for non-empty content
            assert isinstance(result, str)
