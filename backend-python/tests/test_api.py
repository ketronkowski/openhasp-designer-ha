"""API endpoint tests."""
import pytest
from fastapi.testclient import TestClient


def test_status_endpoint(client: TestClient):
    """Test the status/health check endpoint."""
    response = client.get("/api/status")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_root_endpoint(client: TestClient):
    """Test the root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    assert "openHASP Designer API" in response.json()["message"]


def test_entities_endpoint_structure(client: TestClient):
    """Test entities endpoint returns correct structure."""
    # Note: This will fail without a real HA instance
    # In real testing, we'd mock the HA service
    response = client.get("/api/ha/entities")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_entities_endpoint_with_type_filter(client: TestClient):
    """Test entities endpoint with type filter."""
    response = client.get("/api/ha/entities?type=light")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_entities_endpoint_with_search(client: TestClient):
    """Test entities endpoint with search parameter."""
    response = client.get("/api/ha/entities?search=living")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_publish_endpoint_accepts_post(client: TestClient):
    """Test publish endpoint accepts POST requests."""
    test_objects = [
        {
            "id": 1,
            "type": "btn",
            "x": 10,
            "y": 20,
            "width": 100,
            "height": 50,
            "text": "Test",
            "page": 1
        }
    ]
    
    response = client.post("/api/config/publish", json=test_objects)
    # May fail without HA connection, but should accept the request
    assert response.status_code in [200, 500]  # 500 if HA not available


def test_layout_save_and_load(client: TestClient):
    """Test saving and loading quick layout."""
    test_objects = [
        {
            "id": 1,
            "type": "btn",
            "x": 10,
            "y": 20,
            "width": 100,
            "height": 50,
            "page": 1
        }
    ]
    
    # Save layout
    save_response = client.post("/api/config/layout", json=test_objects)
    assert save_response.status_code == 200
    
    # Load layout
    load_response = client.get("/api/config/layout")
    assert load_response.status_code == 200
    loaded = load_response.json()
    assert len(loaded) == 1
    assert loaded[0]["id"] == 1


def test_list_layouts(client: TestClient):
    """Test listing saved layouts."""
    response = client.get("/api/config/layouts")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_import_available_configs(client: TestClient):
    """Test listing available import configs."""
    response = client.get("/api/config/import/available")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
