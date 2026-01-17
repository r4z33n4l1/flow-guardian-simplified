"""Tests for /status endpoint."""
import pytest


def test_status_success(api_client, mock_memory, mock_restore):
    """Test successful status check."""
    response = api_client.get("/status")

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["user"] == "test-user"
    assert data["sessions_count"] == 5
    assert data["personal_learnings"] == 10
    assert data["team_learnings"] == 3


def test_status_with_last_session(api_client, mock_memory, mock_restore):
    """Test status shows last session info."""
    response = api_client.get("/status")

    assert response.status_code == 200
    data = response.json()
    assert data["last_save"] is not None
    assert data["working_on"] == "Working on auth"


def test_status_backboard_connected(api_client, mock_memory, mock_restore):
    """Test status shows Backboard connection."""
    response = api_client.get("/status")

    assert response.status_code == 200
    data = response.json()
    assert data["backboard_connected"] is True
    assert data["team_configured"] is True


def test_status_no_backboard(api_client, mock_config_no_backboard, mock_memory, mock_restore):
    """Test status without Backboard configured."""
    from api.server import app

    app.state.config = mock_config_no_backboard

    response = api_client.get("/status")

    assert response.status_code == 200
    data = response.json()
    assert data["backboard_connected"] is False
    assert data["storage"] == "local"


def test_health_check(api_client):
    """Test health check endpoint."""
    response = api_client.get("/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["version"] == "0.1.0"
