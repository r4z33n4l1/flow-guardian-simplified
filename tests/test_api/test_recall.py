"""Tests for /recall endpoint."""
import pytest


def test_recall_success(api_client, mock_backboard_client, mock_memory):
    """Test successful recall from Backboard."""
    response = api_client.post("/recall", json={"query": "authentication"})

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["query"] == "authentication"
    assert data["source"] == "backboard"
    assert len(data["results"]) > 0


def test_recall_fallback_to_local(api_client, mock_memory, mock_config_no_backboard):
    """Test recall falls back to local when Backboard unavailable."""
    from api.server import app

    app.state.config = mock_config_no_backboard

    response = api_client.post("/recall", json={"query": "auth"})

    assert response.status_code == 200
    data = response.json()
    assert data["source"] == "local"


def test_recall_with_tags(api_client, mock_backboard_client, mock_memory):
    """Test recall with tag filtering."""
    response = api_client.post(
        "/recall", json={"query": "auth", "tags": ["jwt"], "limit": 5}
    )

    assert response.status_code == 200
    assert response.json()["success"] is True


def test_recall_with_limit(api_client, mock_backboard_client, mock_memory):
    """Test recall with custom limit."""
    response = api_client.post("/recall", json={"query": "test", "limit": 20})

    assert response.status_code == 200


def test_recall_validation_error(api_client):
    """Test recall with missing query."""
    response = api_client.post("/recall", json={})

    assert response.status_code == 422
