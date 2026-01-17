"""Tests for /learn endpoint."""
import pytest


def test_learn_personal(api_client, mock_backboard_client, mock_memory):
    """Test storing a personal learning."""
    response = api_client.post(
        "/learn",
        json={
            "insight": "JWT tokens use UTC timestamps",
            "tags": ["auth", "jwt"],
            "share_with_team": False,
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["scope"] == "personal"
    assert data["insight"] == "JWT tokens use UTC timestamps"
    assert "auth" in data["tags"]


def test_learn_team(api_client, mock_backboard_client, mock_memory):
    """Test sharing a learning with team."""
    response = api_client.post(
        "/learn",
        json={
            "insight": "Use refresh token rotation",
            "tags": ["security"],
            "share_with_team": True,
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["scope"] == "team"


def test_learn_minimal(api_client, mock_backboard_client, mock_memory):
    """Test learning with only insight."""
    response = api_client.post("/learn", json={"insight": "Simple insight"})

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["tags"] == []
    assert data["scope"] == "personal"


def test_learn_validation_error(api_client):
    """Test learning with missing insight."""
    response = api_client.post("/learn", json={})

    assert response.status_code == 422


def test_learn_stores_to_backboard(api_client, mock_backboard_client, mock_memory):
    """Test that learning is stored to Backboard."""
    response = api_client.post(
        "/learn", json={"insight": "Test insight", "tags": ["test"]}
    )

    assert response.status_code == 200
    assert response.json()["stored_backboard"] is True
