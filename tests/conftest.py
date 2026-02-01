"""Shared pytest fixtures and mocks for Flow Guardian tests."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from services.config import FlowConfig
from services.flow_service import FlowService


@pytest.fixture
def mock_config():
    """Mock configuration for local-only mode."""
    return FlowConfig(
        cerebras_api_key="test-cerebras-key",
        user="test-user",
    )


@pytest.fixture
def mock_service(mock_config):
    """FlowService with mocked configuration."""
    return FlowService(mock_config)




@pytest.fixture
def mock_memory():
    """Mock memory module."""
    with patch("services.flow_service.memory") as mock:
        mock.save_session = MagicMock(return_value="session_2026-01-16_12-00-00")
        mock.save_learning = MagicMock(return_value="learning_2026-01-16_12-00-00")
        mock.search_learnings = MagicMock(
            return_value=[
                {
                    "text": "JWT tokens expire",
                    "tags": ["auth"],
                    "timestamp": "2026-01-15T10:00:00",
                }
            ]
        )
        mock.get_latest_session = MagicMock(
            return_value={
                "timestamp": "2026-01-16T10:00:00",
                "context": {"summary": "Working on auth", "files": ["auth.py"]},
                "git": {"branch": "main"},
            }
        )
        mock.get_stats = MagicMock(
            return_value={
                "sessions_count": 5,
                "personal_learnings": 10,
                "team_learnings": 3,
            }
        )
        yield mock


@pytest.fixture
def mock_capture():
    """Mock capture module."""
    with patch("services.flow_service.capture") as mock:
        mock.build_session = MagicMock(
            return_value={
                "id": "session_2026-01-16_12-00-00",
                "timestamp": "2026-01-16T12:00:00",
                "context": {
                    "summary": "Test session",
                    "files": ["test.py"],
                    "next_steps": [],
                },
                "git": {"branch": "main"},
                "decisions": [],
                "learnings": [],
                "metadata": {"tags": []},
            }
        )
        yield mock


@pytest.fixture
def mock_restore():
    """Mock restore module."""
    with patch("services.flow_service.restore") as mock:
        mock.get_current_branch = MagicMock(return_value="main")
        mock.calculate_time_elapsed = MagicMock(return_value="2h 30m")
        yield mock


@pytest.fixture
def api_client(mock_config):
    """FastAPI TestClient with mocked config."""
    from fastapi.testclient import TestClient
    from api.server import app

    app.state.config = mock_config
    return TestClient(app)
