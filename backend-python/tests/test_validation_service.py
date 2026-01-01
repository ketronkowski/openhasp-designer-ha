"""Tests for validation service."""
import pytest
from unittest.mock import AsyncMock, Mock
from app.services.validation_service import (
    ValidationService,
    ValidationOptions,
    ValidationError,
    ValidationWarning,
    ValidationResult
)
from app.services.ha_service import HomeAssistantService
from app.services.device_service import DeviceService
from app.models.device import DeviceResolution


@pytest.fixture
def mock_ha_service():
    """Mock Home Assistant service."""
    service = Mock(spec=HomeAssistantService)
    return service


@pytest.fixture
def mock_device_service():
    """Mock device service."""
    service = Mock(spec=DeviceService)
    service.validate_entity_exists = AsyncMock()
    service.get_openhasp_devices = AsyncMock()
    return service


@pytest.fixture
def validation_service(mock_ha_service, mock_device_service):
    """Create validation service with mocked dependencies."""
    return ValidationService(mock_ha_service, mock_device_service)


class TestValidateEntities:
    """Tests for entity validation."""
    
    @pytest.mark.asyncio
    async def test_validate_entities_all_valid(self, validation_service, mock_device_service):
        """Test validation with all valid entities."""
        config = [
            {'id': 1, 'entity_id': 'light.living_room'},
            {'id': 2, 'entity_id': 'switch.bedroom'}
        ]
        
        mock_device_service.validate_entity_exists.return_value = (True, None)
        
        errors, warnings = await validation_service.validate_entities(config)
        
        assert len(errors) == 0
        assert len(warnings) == 0
        assert mock_device_service.validate_entity_exists.call_count == 2
    
    @pytest.mark.asyncio
    async def test_validate_entities_invalid_entity(self, validation_service, mock_device_service):
        """Test validation with invalid entity."""
        config = [
            {'id': 1, 'entity_id': 'light.nonexistent'}
        ]
        
        mock_device_service.validate_entity_exists.return_value = (False, "Entity not found")
        
        errors, warnings = await validation_service.validate_entities(config)
        
        assert len(errors) == 1
        assert errors[0].type == 'entity'
        assert errors[0].entity_id == 'light.nonexistent'
        assert errors[0].object_id == 1
    
    @pytest.mark.asyncio
    async def test_validate_entities_no_entities(self, validation_service, mock_device_service):
        """Test validation with no entities."""
        config = [
            {'id': 1, 'obj': 'label', 'text': 'Hello'}
        ]
        
        errors, warnings = await validation_service.validate_entities(config)
        
        assert len(errors) == 0
        assert len(warnings) == 0
        assert mock_device_service.validate_entity_exists.call_count == 0
    
    @pytest.mark.asyncio
    async def test_validate_entities_duplicate_entity_ids(self, validation_service, mock_device_service):
        """Test validation with same entity used multiple times."""
        config = [
            {'id': 1, 'entity_id': 'light.living_room'},
            {'id': 2, 'entity_id': 'light.living_room'}
        ]
        
        mock_device_service.validate_entity_exists.return_value = (False, "Entity not found")
        
        errors, warnings = await validation_service.validate_entities(config)
        
        # Should have 2 errors (one for each object using the invalid entity)
        assert len(errors) == 2
        assert all(e.entity_id == 'light.living_room' for e in errors)
        # But only called validate once (entities are deduplicated)
        assert mock_device_service.validate_entity_exists.call_count == 1


class TestValidateCoordinates:
    """Tests for coordinate validation."""
    
    def test_validate_coordinates_all_valid(self, validation_service):
        """Test validation with all valid coordinates."""
        config = [
            {'id': 1, 'obj': 'btn', 'x': 10, 'y': 10, 'w': 100, 'h': 50},
            {'id': 2, 'obj': 'btn', 'x': 200, 'y': 100, 'w': 100, 'h': 50}
        ]
        
        device_resolution = DeviceResolution(width=480, height=320, model="Test")
        
        errors = validation_service.validate_object_coordinates(config, device_resolution)
        
        assert len(errors) == 0
    
    def test_validate_coordinates_exceeds_width(self, validation_service):
        """Test validation with object exceeding screen width."""
        config = [
            {'id': 1, 'obj': 'btn', 'x': 400, 'y': 10, 'w': 100, 'h': 50}
        ]
        
        device_resolution = DeviceResolution(width=480, height=320, model="Test")
        
        errors = validation_service.validate_object_coordinates(config, device_resolution)
        
        assert len(errors) == 1
        assert errors[0].type == 'coordinate'
        assert errors[0].object_id == 1
        assert 'width' in errors[0].message.lower()
    
    def test_validate_coordinates_exceeds_height(self, validation_service):
        """Test validation with object exceeding screen height."""
        config = [
            {'id': 1, 'obj': 'btn', 'x': 10, 'y': 300, 'w': 100, 'h': 50}
        ]
        
        device_resolution = DeviceResolution(width=480, height=320, model="Test")
        
        errors = validation_service.validate_object_coordinates(config, device_resolution)
        
        assert len(errors) == 1
        assert errors[0].type == 'coordinate'
        assert 'height' in errors[0].message.lower()
    
    def test_validate_coordinates_negative_x(self, validation_service):
        """Test validation with negative x coordinate."""
        config = [
            {'id': 1, 'obj': 'btn', 'x': -10, 'y': 10, 'w': 100, 'h': 50}
        ]
        
        device_resolution = DeviceResolution(width=480, height=320, model="Test")
        
        errors = validation_service.validate_object_coordinates(config, device_resolution)
        
        assert len(errors) == 1
        assert errors[0].type == 'coordinate'
        assert 'negative' in errors[0].message.lower()
    
    def test_validate_coordinates_skip_pages(self, validation_service):
        """Test that pages are skipped in coordinate validation."""
        config = [
            {'id': 1, 'obj': 'page'},
            {'id': 2, 'obj': 'btn', 'x': 10, 'y': 10, 'w': 100, 'h': 50}
        ]
        
        device_resolution = DeviceResolution(width=480, height=320, model="Test")
        
        errors = validation_service.validate_object_coordinates(config, device_resolution)
        
        assert len(errors) == 0


class TestValidateObjectIds:
    """Tests for object ID validation."""
    
    def test_validate_object_ids_all_unique(self, validation_service):
        """Test validation with all unique object IDs."""
        config = [
            {'id': 1, 'obj': 'btn'},
            {'id': 2, 'obj': 'btn'},
            {'id': 3, 'obj': 'btn'}
        ]
        
        errors = validation_service.validate_object_ids(config)
        
        assert len(errors) == 0
    
    def test_validate_object_ids_duplicate(self, validation_service):
        """Test validation with duplicate object IDs."""
        config = [
            {'id': 1, 'obj': 'btn'},
            {'id': 2, 'obj': 'btn'},
            {'id': 1, 'obj': 'btn'}  # Duplicate
        ]
        
        errors = validation_service.validate_object_ids(config)
        
        assert len(errors) == 1
        assert errors[0].type == 'object_id'
        assert errors[0].object_id == 1
        assert 'duplicate' in errors[0].message.lower()
    
    def test_validate_object_ids_missing_ids(self, validation_service):
        """Test validation with missing object IDs."""
        config = [
            {'obj': 'btn'},  # No ID
            {'id': 1, 'obj': 'btn'}
        ]
        
        errors = validation_service.validate_object_ids(config)
        
        # Should not error on missing IDs, just skip them
        assert len(errors) == 0


class TestValidateDevice:
    """Tests for device validation."""
    
    @pytest.mark.asyncio
    async def test_validate_device_exists_and_online(self, validation_service, mock_device_service):
        """Test validation with valid online device."""
        mock_device_service.get_openhasp_devices.return_value = [
            {'device_id': 'abc123', 'name': 'plate01', 'online': True}
        ]
        
        error = await validation_service.validate_device('abc123')
        
        assert error is None
    
    @pytest.mark.asyncio
    async def test_validate_device_not_found(self, validation_service, mock_device_service):
        """Test validation with non-existent device."""
        mock_device_service.get_openhasp_devices.return_value = [
            {'device_id': 'xyz789', 'name': 'plate02', 'online': True}
        ]
        
        error = await validation_service.validate_device('abc123')
        
        assert error is not None
        assert error.type == 'device'
        assert 'not found' in error.message.lower()
    
    @pytest.mark.asyncio
    async def test_validate_device_offline(self, validation_service, mock_device_service):
        """Test validation with offline device."""
        mock_device_service.get_openhasp_devices.return_value = [
            {'device_id': 'abc123', 'name': 'plate01', 'online': False}
        ]
        
        error = await validation_service.validate_device('abc123')
        
        assert error is not None
        assert error.type == 'device'
        assert 'offline' in error.message.lower()
    
    @pytest.mark.asyncio
    async def test_validate_device_service_error(self, validation_service, mock_device_service):
        """Test validation when device service throws error."""
        mock_device_service.get_openhasp_devices.side_effect = Exception("Connection error")
        
        error = await validation_service.validate_device('abc123')
        
        assert error is not None
        assert error.type == 'device'
        assert 'failed' in error.message.lower()


class TestValidateConfiguration:
    """Tests for full configuration validation."""
    
    @pytest.mark.asyncio
    async def test_validate_configuration_all_valid(self, validation_service, mock_device_service):
        """Test validation with completely valid configuration."""
        config = [
            {'id': 1, 'obj': 'page'},
            {'id': 2, 'obj': 'btn', 'x': 10, 'y': 10, 'w': 100, 'h': 50, 'entity_id': 'light.test'}
        ]
        
        mock_device_service.get_openhasp_devices.return_value = [
            {'device_id': 'abc123', 'name': 'plate01', 'online': True, 'model_key': 'lanbon_l8'}
        ]
        mock_device_service.validate_entity_exists.return_value = (True, None)
        
        result = await validation_service.validate_configuration(config, 'abc123')
        
        assert result.passed is True
        assert len(result.errors) == 0
        assert len(result.warnings) == 0
    
    @pytest.mark.asyncio
    async def test_validate_configuration_device_offline(self, validation_service, mock_device_service):
        """Test that device validation failure stops other validations."""
        config = [
            {'id': 1, 'obj': 'btn', 'entity_id': 'light.test'}
        ]
        
        mock_device_service.get_openhasp_devices.return_value = [
            {'device_id': 'abc123', 'name': 'plate01', 'online': False}
        ]
        
        result = await validation_service.validate_configuration(config, 'abc123')
        
        assert result.passed is False
        assert len(result.errors) == 1
        assert result.errors[0].type == 'device'
        # Should not have called entity validation
        assert mock_device_service.validate_entity_exists.call_count == 0
    
    @pytest.mark.asyncio
    async def test_validate_configuration_with_options(self, validation_service, mock_device_service):
        """Test validation with custom options."""
        config = [
            {'id': 1, 'obj': 'btn', 'entity_id': 'light.test'}
        ]
        
        mock_device_service.get_openhasp_devices.return_value = [
            {'device_id': 'abc123', 'name': 'plate01', 'online': True}
        ]
        
        # Disable entity validation
        options = ValidationOptions(validate_entities=False)
        
        result = await validation_service.validate_configuration(config, 'abc123', options)
        
        # Should not have validated entities
        assert mock_device_service.validate_entity_exists.call_count == 0
    
    @pytest.mark.asyncio
    async def test_validate_configuration_multiple_errors(self, validation_service, mock_device_service):
        """Test validation with multiple types of errors."""
        config = [
            {'id': 1, 'obj': 'btn', 'x': 500, 'y': 10, 'w': 100, 'h': 50, 'entity_id': 'light.invalid'},
            {'id': 1, 'obj': 'btn', 'x': 10, 'y': 10, 'w': 100, 'h': 50}  # Duplicate ID
        ]
        
        mock_device_service.get_openhasp_devices.return_value = [
            {'device_id': 'abc123', 'name': 'plate01', 'online': True, 'model_key': 'lanbon_l8'}
        ]
        mock_device_service.validate_entity_exists.return_value = (False, "Not found")
        
        result = await validation_service.validate_configuration(config, 'abc123')
        
        assert result.passed is False
        assert len(result.errors) >= 2  # At least entity and duplicate ID errors
        
        # Check we have different error types
        error_types = {e.type for e in result.errors}
        assert 'entity' in error_types
        assert 'object_id' in error_types
