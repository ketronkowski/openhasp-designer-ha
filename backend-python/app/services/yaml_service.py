"""YAML configuration generation service for openHASP."""
import yaml
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)


class YAMLConfigService:
    """Service for generating Home Assistant YAML configurations."""
    
    def generate_yaml(self, objects: List[Dict[str, Any]], device_id: str) -> str:
        """
        Generate YAML configuration for openHASP device.
        
        Args:
            objects: List of page/object configurations
            device_id: Target device ID
        
        Returns:
            YAML string with openHASP configuration
        """
        config = {
            'openhasp': {
                device_id: {
                    'objects': []
                }
            }
        }
        
        for obj in objects:
            # Skip page objects
            if obj.get('obj') == 'page':
                continue
            
            yaml_obj = self._generate_object_config(obj, device_id)
            if yaml_obj:
                config['openhasp'][device_id]['objects'].append(yaml_obj)
        
        return yaml.dump(config, default_flow_style=False, sort_keys=False)
    
    def _generate_object_config(self, obj: Dict[str, Any], device_id: str) -> Dict[str, Any]:
        """
        Generate YAML config for a single object.
        
        Args:
            obj: Object configuration
            device_id: Device ID
        
        Returns:
            YAML object configuration
        """
        page = obj.get('page', 0)
        obj_id = obj.get('id')
        obj_type = obj.get('obj')
        entity_id = obj.get('entity_id')
        
        # Create object identifier (e.g., "p0b1" for page 0, button 1)
        obj_name = f"p{page}b{obj_id}"
        
        config = {
            'obj': obj_name,
            'properties': {}
        }
        
        # Add text property if present
        if obj.get('text'):
            config['properties']['text'] = obj['text']
        
        # Add event handlers for interactive objects
        if obj_type in ['btn', 'switch', 'checkbox'] and entity_id:
            config['event'] = self._generate_event_handlers(entity_id, obj_type)
        
        # Add state updates for objects with entities
        if entity_id:
            config['state'] = self._generate_state_updates(entity_id, obj_type, obj_name, device_id)
        
        return config
    
    def _generate_event_handlers(self, entity_id: str, obj_type: str) -> Dict[str, Any]:
        """
        Generate event handlers for interactive objects.
        
        Args:
            entity_id: Entity to control
            obj_type: Object type (btn, switch, etc.)
        
        Returns:
            Event handler configuration
        """
        domain = entity_id.split('.')[0] if '.' in entity_id else 'homeassistant'
        
        # Determine service based on entity domain
        service_map = {
            'light': 'light.toggle',
            'switch': 'switch.toggle',
            'cover': 'cover.toggle',
            'fan': 'fan.toggle',
            'climate': 'climate.toggle',
            'lock': 'lock.toggle',
            'media_player': 'media_player.toggle',
        }
        
        service = service_map.get(domain, 'homeassistant.toggle')
        
        return {
            'down': [{
                'service': service,
                'target': {
                    'entity_id': entity_id
                }
            }]
        }
    
    def _generate_state_updates(
        self, 
        entity_id: str, 
        obj_type: str, 
        obj_name: str, 
        device_id: str
    ) -> List[Dict[str, Any]]:
        """
        Generate state update automations.
        
        Args:
            entity_id: Entity to monitor
            obj_type: Object type
            obj_name: Object identifier (e.g., "p0b1")
            device_id: Device ID
        
        Returns:
            List of state update configurations
        """
        domain = entity_id.split('.')[0] if '.' in entity_id else 'sensor'
        
        # Different update logic based on entity type
        if domain == 'light':
            return self._generate_light_state_update(entity_id, obj_name, device_id)
        elif domain == 'sensor':
            return self._generate_sensor_state_update(entity_id, obj_name, device_id)
        elif domain == 'binary_sensor':
            return self._generate_binary_sensor_state_update(entity_id, obj_name, device_id)
        elif domain in ['switch', 'cover', 'fan']:
            return self._generate_toggle_state_update(entity_id, obj_name, device_id)
        else:
            return self._generate_generic_state_update(entity_id, obj_name, device_id)
    
    def _generate_light_state_update(
        self, 
        entity_id: str, 
        obj_name: str, 
        device_id: str
    ) -> List[Dict[str, Any]]:
        """Generate state update for light entities."""
        return [{
            'service': 'openhasp.update_object',
            'target': {
                'entity_id': f'openhasp.{device_id}'
            },
            'data': {
                'obj': obj_name,
                'text': "{{ 'ON' if is_state('" + entity_id + "', 'on') else 'OFF' }}",
                'bg_color': "{{ '#00FF00' if is_state('" + entity_id + "', 'on') else '#FF0000' }}"
            }
        }]
    
    def _generate_sensor_state_update(
        self, 
        entity_id: str, 
        obj_name: str, 
        device_id: str
    ) -> List[Dict[str, Any]]:
        """Generate state update for sensor entities."""
        return [{
            'service': 'openhasp.update_object',
            'target': {
                'entity_id': f'openhasp.{device_id}'
            },
            'data': {
                'obj': obj_name,
                'text': "{{ states('" + entity_id + "') }}{{ state_attr('" + entity_id + "', 'unit_of_measurement') }}"
            }
        }]
    
    def _generate_binary_sensor_state_update(
        self, 
        entity_id: str, 
        obj_name: str, 
        device_id: str
    ) -> List[Dict[str, Any]]:
        """Generate state update for binary sensor entities."""
        return [{
            'service': 'openhasp.update_object',
            'target': {
                'entity_id': f'openhasp.{device_id}'
            },
            'data': {
                'obj': obj_name,
                'text': "{{ 'ON' if is_state('" + entity_id + "', 'on') else 'OFF' }}"
            }
        }]
    
    def _generate_toggle_state_update(
        self, 
        entity_id: str, 
        obj_name: str, 
        device_id: str
    ) -> List[Dict[str, Any]]:
        """Generate state update for toggle entities (switch, cover, fan)."""
        return [{
            'service': 'openhasp.update_object',
            'target': {
                'entity_id': f'openhasp.{device_id}'
            },
            'data': {
                'obj': obj_name,
                'text': "{{ 'ON' if is_state('" + entity_id + "', 'on') else 'OFF' }}",
                'val': "{{ 1 if is_state('" + entity_id + "', 'on') else 0 }}"
            }
        }]
    
    def _generate_generic_state_update(
        self, 
        entity_id: str, 
        obj_name: str, 
        device_id: str
    ) -> List[Dict[str, Any]]:
        """Generate generic state update."""
        return [{
            'service': 'openhasp.update_object',
            'target': {
                'entity_id': f'openhasp.{device_id}'
            },
            'data': {
                'obj': obj_name,
                'text': "{{ states('" + entity_id + "') }}"
            }
        }]
