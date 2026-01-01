"""Test fixtures and configuration for pytest."""
import pytest
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture
def client():
    """FastAPI test client."""
    return TestClient(app)


@pytest.fixture
def mock_ha_entities():
    """Mock Home Assistant entities for testing."""
    return [
        {
            "entity_id": "light.living_room",
            "state": "on",
            "attributes": {
                "friendly_name": "Living Room Light",
                "icon": "mdi:lightbulb"
            }
        },
        {
            "entity_id": "light.bedroom",
            "state": "off",
            "attributes": {
                "friendly_name": "Bedroom Light"
            }
        },
        {
            "entity_id": "switch.kitchen",
            "state": "on",
            "attributes": {
                "friendly_name": "Kitchen Switch"
            }
        }
    ]


@pytest.fixture
def sample_designer_objects():
    """Sample designer objects for testing."""
    from app.models.designer import DesignerObjectDto
    
    return [
        DesignerObjectDto(
            id=1,
            type="btn",
            x=10,
            y=20,
            width=100,
            height=50,
            text="Living Room",
            entity_id="light.living_room",
            page=1
        ),
        DesignerObjectDto(
            id=2,
            type="slider",
            x=10,
            y=80,
            width=200,
            height=30,
            min=0,
            max=100,
            entity_id="light.bedroom",
            page=1
        )
    ]
