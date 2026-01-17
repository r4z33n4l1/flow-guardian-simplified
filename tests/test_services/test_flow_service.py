"""Tests for FlowService business logic."""
import pytest
from services.flow_service import FlowService
from services.models import CaptureRequest, RecallRequest, LearnRequest, TeamQueryRequest


@pytest.mark.asyncio
async def test_capture_context_full(
    mock_config, mock_backboard_client, mock_memory, mock_capture
):
    """Test full capture workflow."""
    service = FlowService(mock_config)

    request = CaptureRequest(
        summary="Test capture",
        decisions=["Decision 1"],
        next_steps=["Step 1"],
        blockers=["Blocker 1"],
        tags=["test"],
    )

    result = await service.capture_context(request)

    assert result.success is True
    assert result.session_id is not None
    assert result.stored_local is True


@pytest.mark.asyncio
async def test_capture_stores_to_backboard(
    mock_config, mock_backboard_client, mock_memory, mock_capture
):
    """Test capture stores to Backboard when configured."""
    service = FlowService(mock_config)

    request = CaptureRequest(summary="Test")
    result = await service.capture_context(request)

    assert result.stored_backboard is True
    mock_backboard_client.store_session.assert_called_once()


@pytest.mark.asyncio
async def test_capture_without_backboard(
    mock_config_no_backboard, mock_memory, mock_capture
):
    """Test capture works without Backboard."""
    service = FlowService(mock_config_no_backboard)

    request = CaptureRequest(summary="Local only")
    result = await service.capture_context(request)

    assert result.success is True
    assert result.stored_backboard is False
    assert result.stored_local is True


@pytest.mark.asyncio
async def test_recall_uses_backboard_first(
    mock_config, mock_backboard_client, mock_memory
):
    """Test that recall prefers Backboard.io when available."""
    service = FlowService(mock_config)

    request = RecallRequest(query="auth")
    result = await service.recall_context(request)

    assert result.source == "backboard"
    mock_backboard_client.recall.assert_called_once()


@pytest.mark.asyncio
async def test_recall_falls_back_to_local(mock_config_no_backboard, mock_memory):
    """Test that recall falls back to local search."""
    service = FlowService(mock_config_no_backboard)

    request = RecallRequest(query="auth")
    result = await service.recall_context(request)

    assert result.source == "local"
    mock_memory.search_learnings.assert_called_once()


@pytest.mark.asyncio
async def test_store_personal_learning(
    mock_config, mock_backboard_client, mock_memory
):
    """Test storing personal learning."""
    service = FlowService(mock_config)

    request = LearnRequest(
        insight="Test insight", tags=["test"], share_with_team=False
    )

    result = await service.store_learning(request)

    assert result.scope == "personal"
    mock_backboard_client.store_learning.assert_called_once()


@pytest.mark.asyncio
async def test_store_team_learning(mock_config, mock_backboard_client, mock_memory):
    """Test storing team learning."""
    service = FlowService(mock_config)

    request = LearnRequest(
        insight="Team insight", tags=["team"], share_with_team=True
    )

    result = await service.store_learning(request)

    assert result.scope == "team"
    mock_backboard_client.store_team_learning.assert_called_once()


@pytest.mark.asyncio
async def test_query_team_success(mock_config, mock_backboard_client):
    """Test successful team query."""
    service = FlowService(mock_config)

    request = TeamQueryRequest(query="caching")
    result = await service.query_team(request)

    assert result.success is True
    assert result.team_configured is True
    mock_backboard_client.query_team_memory.assert_called_once()


@pytest.mark.asyncio
async def test_query_team_not_configured(mock_config_no_team):
    """Test team query when team not configured."""
    service = FlowService(mock_config_no_team)

    request = TeamQueryRequest(query="test")
    result = await service.query_team(request)

    assert result.success is False
    assert result.team_configured is False


@pytest.mark.asyncio
async def test_get_status(mock_config, mock_memory, mock_restore):
    """Test status retrieval."""
    service = FlowService(mock_config)

    result = await service.get_status()

    assert result.success is True
    assert result.user == "test-user"
    assert result.sessions_count == 5
    assert result.backboard_connected is True
