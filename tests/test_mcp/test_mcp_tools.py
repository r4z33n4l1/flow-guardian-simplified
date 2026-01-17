"""Tests for MCP server tools."""
import pytest
from unittest.mock import patch, AsyncMock, MagicMock


@pytest.fixture
def mock_all_services():
    """Mock all service dependencies for MCP tests."""
    with patch("mcp_server.FlowConfig") as mock_config_cls, \
         patch("mcp_server.FlowService") as mock_service_cls:

        # Setup mock config
        mock_config = MagicMock()
        mock_config.backboard_available = True
        mock_config.team_available = True
        mock_config.user = "test-user"
        mock_config_cls.from_env.return_value = mock_config

        # Setup mock service
        mock_service = MagicMock()
        mock_service_cls.return_value = mock_service

        yield mock_config, mock_service


@pytest.mark.asyncio
async def test_flow_recall_tool(mock_all_services):
    """Test flow_recall MCP tool."""
    mock_config, mock_service = mock_all_services

    # Setup mock response
    from services.models import RecallResponse
    mock_service.recall_context = AsyncMock(
        return_value=RecallResponse(
            success=True,
            query="auth work",
            results=[{"content": "Working on JWT auth"}],
            source="backboard"
        )
    )

    from mcp_server import handle_call_tool
    result = await handle_call_tool("flow_recall", {"query": "auth work"})

    assert len(result) == 1
    assert result[0].type == "text"
    assert "Retrieved Context" in result[0].text


@pytest.mark.asyncio
async def test_flow_capture_tool(mock_all_services):
    """Test flow_capture MCP tool."""
    mock_config, mock_service = mock_all_services

    from services.models import CaptureResponse
    mock_service.capture_context = AsyncMock(
        return_value=CaptureResponse(
            success=True,
            session_id="session_123",
            timestamp="2026-01-16T12:00:00",
            branch="main",
            files=["auth.py"],
            summary="Working on auth",
            stored_backboard=True,
            stored_local=True
        )
    )

    from mcp_server import handle_call_tool
    result = await handle_call_tool("flow_capture", {
        "summary": "Working on auth",
        "decisions": ["Use JWT"],
        "next_steps": ["Add tests"]
    })

    assert len(result) == 1
    assert "Context Captured" in result[0].text
    assert "Working on auth" in result[0].text


@pytest.mark.asyncio
async def test_flow_learn_tool(mock_all_services):
    """Test flow_learn MCP tool."""
    mock_config, mock_service = mock_all_services

    from services.models import LearnResponse
    mock_service.store_learning = AsyncMock(
        return_value=LearnResponse(
            success=True,
            learning_id="learning_123",
            insight="JWT uses UTC",
            tags=["auth"],
            scope="personal",
            stored_backboard=True
        )
    )

    from mcp_server import handle_call_tool
    result = await handle_call_tool("flow_learn", {
        "insight": "JWT uses UTC",
        "tags": ["auth"],
        "share_with_team": False
    })

    assert len(result) == 1
    assert "Learning Saved" in result[0].text


@pytest.mark.asyncio
async def test_flow_learn_team_tool(mock_all_services):
    """Test flow_learn with team sharing."""
    mock_config, mock_service = mock_all_services

    from services.models import LearnResponse
    mock_service.store_learning = AsyncMock(
        return_value=LearnResponse(
            success=True,
            learning_id="learning_123",
            insight="Team insight",
            tags=["team"],
            scope="team",
            stored_backboard=True
        )
    )

    from mcp_server import handle_call_tool
    result = await handle_call_tool("flow_learn", {
        "insight": "Team insight",
        "share_with_team": True
    })

    assert "Shared with Team" in result[0].text


@pytest.mark.asyncio
async def test_flow_team_tool(mock_all_services):
    """Test flow_team MCP tool."""
    mock_config, mock_service = mock_all_services

    from services.models import TeamQueryResponse
    mock_service.query_team = AsyncMock(
        return_value=TeamQueryResponse(
            success=True,
            query="caching",
            results="Team learned: use Redis",
            team_configured=True
        )
    )

    from mcp_server import handle_call_tool
    result = await handle_call_tool("flow_team", {"query": "caching"})

    assert len(result) == 1
    assert "Team Knowledge" in result[0].text


@pytest.mark.asyncio
async def test_flow_status_tool(mock_all_services):
    """Test flow_status MCP tool."""
    mock_config, mock_service = mock_all_services

    from services.models import StatusResponse
    mock_service.get_status = AsyncMock(
        return_value=StatusResponse(
            success=True,
            user="test-user",
            last_save="2h ago",
            branch="main",
            working_on="Auth feature",
            sessions_count=5,
            personal_learnings=10,
            team_learnings=3,
            storage="backboard+local",
            backboard_connected=True,
            team_configured=True
        )
    )

    from mcp_server import handle_call_tool
    result = await handle_call_tool("flow_status", {})

    assert len(result) == 1
    assert "Flow Guardian Status" in result[0].text
    assert "test-user" in result[0].text


@pytest.mark.asyncio
async def test_unknown_tool():
    """Test handling of unknown tool names."""
    from mcp_server import handle_call_tool

    with patch("mcp_server.FlowConfig"), patch("mcp_server.FlowService"):
        result = await handle_call_tool("unknown_tool", {})

    assert len(result) == 1
    assert "Unknown tool" in result[0].text


@pytest.mark.asyncio
async def test_tool_error_handling(mock_all_services):
    """Test error handling in tool calls."""
    mock_config, mock_service = mock_all_services

    mock_service.recall_context = AsyncMock(side_effect=Exception("Test error"))

    from mcp_server import handle_call_tool
    result = await handle_call_tool("flow_recall", {"query": "test"})

    assert len(result) == 1
    assert "Error" in result[0].text
