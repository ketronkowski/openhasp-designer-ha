"""Tests for YAML configuration generation service."""
import pytest
from app.services.yaml_service import YAMLConfigService
import yaml


@pytest.fixture
def yaml_service():
    """Create YAML service instance."""
    return YAMLConfigService()


class TestYAMLGeneration:
    """Tests for YAML configuration generation."""
    
    def test_generate_yaml_basic(self, yaml_service):
        """Test basic YAML generation."""
        objects = [
            {'page': 0, 'id': 0, 'obj': 'page'},
            {'page': 0, 'id': 1, 'obj': 'btn', 'text': 'Test Button', 'entity_id': 'light.living_room'},
        ]
        
        yaml_content = yaml_service.generate_yaml(objects, 'plate01')
        
        assert yaml_content is not None
        assert 'openhasp:' in yaml_content
        assert 'plate01:' in yaml_content
        assert 'p0b1' in yaml_content
    
    def test_skip_page_objects(self, yaml_service):
        """Test that page objects are skipped."""
        objects = [
            {'page': 0, 'id': 0, 'obj': 'page'},
            {'page': 0, 'id': 1, 'obj': 'btn', 'text': 'Button'},
        ]
        
        yaml_content = yaml_service.generate_yaml(objects, 'plate01')
        parsed = yaml.safe_load(yaml_content)
        
        # Should only have 1 object (button), not the page
        assert len(parsed['openhasp']['plate01']['objects']) == 1
    
    def test_light_entity_event_handler(self, yaml_service):
        """Test event handler generation for light entity."""
        obj = {
            'page': 0,
            'id': 1,
            'obj': 'btn',
            'text': 'Light',
            'entity_id': 'light.living_room'
        }
        
        config = yaml_service._generate_object_config(obj, 'plate01')
        
        assert 'event' in config
        assert 'down' in config['event']
        assert config['event']['down'][0]['service'] == 'light.toggle'
        assert config['event']['down'][0]['target']['entity_id'] == 'light.living_room'
    
    def test_switch_entity_event_handler(self, yaml_service):
        """Test event handler generation for switch entity."""
        obj = {
            'page': 0,
            'id': 1,
            'obj': 'switch',
            'entity_id': 'switch.fan'
        }
        
        config = yaml_service._generate_object_config(obj, 'plate01')
        
        assert 'event' in config
        assert config['event']['down'][0]['service'] == 'switch.toggle'
    
    def test_sensor_state_update(self, yaml_service):
        """Test state update generation for sensor."""
        obj = {
            'page': 0,
            'id': 2,
            'obj': 'label',
            'entity_id': 'sensor.temperature'
        }
        
        config = yaml_service._generate_object_config(obj, 'plate01')
        
        assert 'state' in config
        assert len(config['state']) > 0
        assert config['state'][0]['service'] == 'openhasp.update_object'
        assert config['state'][0]['target']['entity_id'] == 'openhasp.plate01'
        assert 'sensor.temperature' in config['state'][0]['data']['text']
    
    def test_light_state_update(self, yaml_service):
        """Test state update generation for light."""
        obj = {
            'page': 0,
            'id': 1,
            'obj': 'btn',
            'entity_id': 'light.bedroom'
        }
        
        config = yaml_service._generate_object_config(obj, 'plate01')
        
        assert 'state' in config
        assert 'light.bedroom' in config['state'][0]['data']['text']
        assert 'bg_color' in config['state'][0]['data']
    
    def test_binary_sensor_state_update(self, yaml_service):
        """Test state update generation for binary sensor."""
        obj = {
            'page': 0,
            'id': 3,
            'obj': 'label',
            'entity_id': 'binary_sensor.motion'
        }
        
        config = yaml_service._generate_object_config(obj, 'plate01')
        
        assert 'state' in config
        assert 'binary_sensor.motion' in config['state'][0]['data']['text']
    
    def test_multiple_objects(self, yaml_service):
        """Test YAML generation with multiple objects."""
        objects = [
            {'page': 0, 'id': 0, 'obj': 'page'},
            {'page': 0, 'id': 1, 'obj': 'btn', 'text': 'Light', 'entity_id': 'light.living_room'},
            {'page': 0, 'id': 2, 'obj': 'label', 'text': 'Temp', 'entity_id': 'sensor.temperature'},
            {'page': 1, 'id': 0, 'obj': 'page'},
            {'page': 1, 'id': 3, 'obj': 'switch', 'entity_id': 'switch.fan'},
        ]
        
        yaml_content = yaml_service.generate_yaml(objects, 'plate01')
        parsed = yaml.safe_load(yaml_content)
        
        # Should have 3 objects (excluding pages)
        assert len(parsed['openhasp']['plate01']['objects']) == 3
        
        # Check object identifiers
        obj_names = [obj['obj'] for obj in parsed['openhasp']['plate01']['objects']]
        assert 'p0b1' in obj_names
        assert 'p0b2' in obj_names
        assert 'p1b3' in obj_names
    
    def test_object_without_entity(self, yaml_service):
        """Test object without entity_id."""
        obj = {
            'page': 0,
            'id': 1,
            'obj': 'label',
            'text': 'Static Label'
        }
        
        config = yaml_service._generate_object_config(obj, 'plate01')
        
        # Should have properties but no event or state
        assert 'properties' in config
        assert 'event' not in config
        assert 'state' not in config
    
    def test_yaml_syntax_valid(self, yaml_service):
        """Test that generated YAML is syntactically valid."""
        objects = [
            {'page': 0, 'id': 1, 'obj': 'btn', 'text': 'Test', 'entity_id': 'light.test'},
        ]
        
        yaml_content = yaml_service.generate_yaml(objects, 'plate01')
        
        # Should parse without errors
        parsed = yaml.safe_load(yaml_content)
        assert parsed is not None
        assert 'openhasp' in parsed
