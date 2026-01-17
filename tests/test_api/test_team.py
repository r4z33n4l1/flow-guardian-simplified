"""Tests for /team endpoint."""
import pytest


def test_team_query_success(api_client, mock_backboard_client):
    """Test successful team query."""
    response = api_client.post("/team", json={"query": "caching strategies"})

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["query"] == "caching strategies"
    assert data["team_configured"] is True


def test_team_not_configured(api_client, mock_config_no_team):
    """Test team query when team not configured."""
    from api.server import app

    app.state.config = mock_config_no_team

    response = api_client.post("/team", json={"query": "test"})

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is False
    assert data["team_configured"] is False
    assert "not configured" in data["results"].lower()


def test_team_with_limit(api_client, mock_backboard_client):
    """Test team query with limit."""
    response = api_client.post("/team", json={"query": "test", "limit": 5})

    assert response.status_code == 200


def test_team_validation_error(api_client):
    """Test team with missing query."""
    response = api_client.post("/team", json={})

    assert response.status_code == 422
