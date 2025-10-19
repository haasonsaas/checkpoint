import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
import tempfile
import os
from server import app
from database import Base, engine


@pytest.fixture
def client():
    """Create a test client"""
    return TestClient(app)


@pytest.fixture(autouse=True)
def setup_test_db():
    """Setup test database before each test"""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


def test_root_endpoint(client):
    """Test the root endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "name" in data
    assert data["name"] == "The Checkpoint"


def test_list_checkpoints_empty(client):
    """Test listing checkpoints when none exist"""
    response = client.get("/checkpoints")
    assert response.status_code == 200
    assert response.json() == []


def test_create_checkpoint(client):
    """Test creating a new checkpoint"""
    response = client.post("/checkpoints", json={
        "version": "0.1",
        "description": "Test checkpoint",
        "config": {"test": "value"},
        "metadata": {}
    })
    
    assert response.status_code == 200
    data = response.json()
    assert data["version"] == "0.1"
    assert data["description"] == "Test checkpoint"


def test_create_duplicate_checkpoint(client):
    """Test creating a duplicate checkpoint fails"""
    client.post("/checkpoints", json={
        "version": "0.1",
        "description": "First",
        "config": {},
        "metadata": {}
    })
    
    response = client.post("/checkpoints", json={
        "version": "0.1",
        "description": "Second",
        "config": {},
        "metadata": {}
    })
    
    assert response.status_code == 400


def test_get_checkpoint(client):
    """Test getting a specific checkpoint"""
    client.post("/checkpoints", json={
        "version": "0.1",
        "description": "Test",
        "config": {},
        "metadata": {}
    })
    
    response = client.get("/checkpoints/0.1")
    assert response.status_code == 200
    data = response.json()
    assert data["version"] == "0.1"


def test_get_nonexistent_checkpoint(client):
    """Test getting a checkpoint that doesn't exist"""
    response = client.get("/checkpoints/0.999")
    assert response.status_code == 404


def test_activate_checkpoint(client):
    """Test activating a checkpoint"""
    client.post("/checkpoints", json={
        "version": "0.1",
        "description": "Test",
        "config": {},
        "metadata": {}
    })
    
    response = client.post("/checkpoints/0.1/activate")
    assert response.status_code == 200
    assert "active" in response.json()["message"]


def test_delete_checkpoint(client):
    """Test deleting a checkpoint"""
    client.post("/checkpoints", json={
        "version": "0.1",
        "description": "Test",
        "config": {},
        "metadata": {}
    })
    
    response = client.delete("/checkpoints/0.1")
    assert response.status_code == 200
    
    # Verify it's gone
    response = client.get("/checkpoints/0.1")
    assert response.status_code == 404


@patch('server.ghost_engine.generate_response')
def test_chat_endpoint(mock_generate, client):
    """Test the chat endpoint"""
    # Setup
    client.post("/checkpoints", json={
        "version": "0.1",
        "description": "Test",
        "config": {},
        "metadata": {}
    })
    client.post("/checkpoints/0.1/activate")
    
    # Mock response
    mock_generate.return_value = {
        "response": "Test response",
        "sources": []
    }
    
    response = client.post("/chat", json={
        "message": "Hello",
        "checkpoint_version": "0.1"
    })
    
    assert response.status_code == 200
    data = response.json()
    assert data["response"] == "Test response"
    assert data["checkpoint_version"] == "0.1"


def test_chat_without_active_checkpoint(client):
    """Test chat endpoint without active checkpoint"""
    response = client.post("/chat", json={
        "message": "Hello"
    })
    
    assert response.status_code == 400
    assert "No active checkpoint" in response.json()["detail"]


def test_get_stats(client):
    """Test getting checkpoint statistics"""
    client.post("/checkpoints", json={
        "version": "0.1",
        "description": "Test",
        "config": {},
        "metadata": {}
    })
    
    response = client.get("/stats/0.1")
    assert response.status_code == 200
    data = response.json()
    assert "checkpoint_version" in data
    assert "total_messages" in data
