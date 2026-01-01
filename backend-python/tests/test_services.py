"""Unit tests for services."""
import pytest
from app.services.ha_service import HomeAssistantService
from app.services.config_service import ConfigPublisherService
from app.models.designer import DesignerObjectDto


class TestHomeAssistantService:
    """Tests for HomeAssistantService."""
    
    def test_enhance_entity(self):
        """Test entity enhancement with metadata."""
        service = HomeAssistantService()
        entity = {
            "entity_id": "light.living_room",
            "state": "on",
            "attributes": {"friendly_name": "Living Room Light"}
        }
        
        enhanced = service._enhance_entity(entity)
        
        assert enhanced["entity_id"] == "light.living_room"
        assert enhanced["domain"] == "light"
        assert enhanced["icon"] == "mdi:lightbulb"
        assert enhanced["friendly_name"] == "Living Room Light"
    
    def test_default_icon(self):
        """Test default icon mapping."""
        service = HomeAssistantService()
        
        assert service._get_default_icon("light") == "mdi:lightbulb"
        assert service._get_default_icon("switch") == "mdi:light-switch"
        assert service._get_default_icon("unknown") == "mdi:home-assistant"


class TestConfigPublisherService:
    """Tests for ConfigPublisherService."""
    
    def test_dto_to_button(self):
        """Test converting DTO to HaspButton."""
        service = ConfigPublisherService()
        
        dto = DesignerObjectDto(
            id=1,
            type="btn",
            x=10,
            y=20,
            width=100,
            height=50,
            text="Test Button",
            entity_id="light.test",
            page=1
        )
        
        hasp_obj = service._dto_to_hasp_object(dto)
        
        assert hasp_obj.obj == "btn"
        assert hasp_obj.text == "Test Button"
        assert hasp_obj.entity == "light.test"
        assert hasp_obj.x == 10
        assert hasp_obj.y == 20
    
    def test_dto_to_slider(self):
        """Test converting DTO to HaspSlider."""
        service = ConfigPublisherService()
        
        dto = DesignerObjectDto(
            id=2,
            type="slider",
            x=10,
            y=20,
            width=200,
            height=30,
            min=0,
            max=100,
            entity_id="light.brightness",
            page=1
        )
        
        hasp_obj = service._dto_to_hasp_object(dto)
        
        assert hasp_obj.obj == "slider"
        assert hasp_obj.min == 0
        assert hasp_obj.max == 100
        assert hasp_obj.entity == "light.brightness"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
