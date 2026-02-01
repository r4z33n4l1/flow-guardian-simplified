"""Tests for /capture endpoint."""
import pytest


def test_capture_success(api_client, mock_memory, mock_capture):
    """Test successful context capture."""
    response = api_client.post(
        "/capture",
        json={
            "summary": "Implementing auth feature",
            "decisions": ["Use JWT tokens"],
            "next_steps": ["Add refresh tokens"],
            "tags": ["auth"],
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "session_id" in data
    assert data["stored_local"] is True


def test_capture_minimal_request(api_client, mock_memory, mock_capture):
    """Test capture with only required fields."""
    response = api_client.post("/capture", json={"summary": "Minimal capture"})

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "session_id" in data


def test_capture_validation_error(api_client):
    """Test capture with missing required field."""
    response = api_client.post("/capture", json={})

    assert response.status_code == 422  # Validation error


def test_capture_with_blockers(api_client, mock_memory, mock_capture):
    """Test capture with blockers."""
    response = api_client.post(
        "/capture",
        json={
            "summary": "Working on feature",
            "blockers": ["Need API key", "Waiting for review"],
        },
    )

    assert response.status_code == 200
    assert response.json()["success"] is True
