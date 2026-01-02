"""Device discovery and management service."""
import logging
from typing import List, Dict, Any, Optional
import httpx
from app.config import settings
from app.models.device import get_device_resolution, DeviceResolution

logger = logging.getLogger(__name__)


class DeviceService:
    """Service for discovering and managing openHASP devices."""
    
    def __init__(self):
        self.base_url = settings.ha_url
        self.headers = {"Authorization": f"Bearer {settings.ha_token}"}
    
    async def get_openhasp_devices(self) -> List[Dict[str, Any]]:
        """
        Discover all openHASP devices from Home Assistant.
        
        Uses entity-based discovery which is more reliable than device registry.
        
        Returns list of devices with:
        - device_id
        - name
        - model
        - online_status
        - resolution (if known)
        """
        try:
            async with httpx.AsyncClient() as client:
                # Get all entities from HA
                response = await client.get(
                    f"{self.base_url}/api/states",
                    headers=self.headers,
                    timeout=10.0
                )
                response.raise_for_status()
                all_entities = response.json()
                
                # Find openHASP devices by looking for openhasp entities
                devices_map = {}
                
                for entity in all_entities:
                    entity_id = entity.get("entity_id", "")
                    
                    # Look for openhasp entities (e.g., "sensor.plate01_status")
                    if not entity_id.startswith(("sensor.", "switch.", "light.", "binary_sensor.")):
                        continue
                    
                    # Check if it's an openHASP entity
                    attributes = entity.get("attributes", {})
                    integration = attributes.get("integration", "")
                    
                    # Multiple ways to detect openHASP
                    is_openhasp = (
                        "openhasp" in entity_id.lower() or
                        "plate" in entity_id.lower() or
                        integration == "openhasp" or
                        "openhasp" in str(attributes.get("device_class", "")).lower()
                    )
                    
                    if is_openhasp:
                        # Extract device name from entity_id (e.g., "plate01" from "sensor.plate01_status")
                        parts = entity_id.split(".")
                        if len(parts) >= 2:
                            # Get the part before the first underscore
                            device_name = parts[1].split("_")[0]
                            
                            if device_name not in devices_map:
                                devices_map[device_name] = {
                                    "device_id": device_name,
                                    "name": attributes.get("friendly_name", device_name).replace(" Status", "").replace(" status", ""),
                                    "model": attributes.get("model", "Unknown"),
                                    "manufacturer": "openHASP",
                                    "online": True,
                                    "resolution": None,
                                    "entities": []
                                }
                            
                            # Track entities for this device
                            devices_map[device_name]["entities"].append(entity_id)
                            
                            # Check online status from status entity
                            if "status" in entity_id.lower():
                                state = entity.get("state", "").lower()
                                devices_map[device_name]["online"] = state in ["on", "online", "connected", "available"]
                            
                            # Try to get model info
                            if attributes.get("model"):
                                devices_map[device_name]["model"] = attributes["model"]
                
                # Convert to list and enrich with resolution info
                devices = []
                for device_id, device_info in devices_map.items():
                    # Try to determine resolution from model
                    model = device_info["model"].lower()
                    resolution = self._get_resolution_from_model(model)
                    if resolution:
                        device_info["resolution"] = resolution
                    
                    devices.append(device_info)
                
                logger.info(f"Discovered {len(devices)} openHASP devices")
                return devices
                
        except httpx.HTTPError as e:
            logger.error(f"Failed to fetch entities from HA: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error fetching devices: {e}")
            return []
    
    def _get_resolution_from_model(self, model: str) -> Optional[Dict[str, int]]:
        """Get resolution from model string."""
        model_clean = model.replace("-", "").replace("_", "").lower()
        
        # Map common model names to resolution keys
        model_mappings = {
            "lanbon": "lanbon_l8",
            "l8": "lanbon_l8",
            "wt32sc01": "wt32_sc01",
            "wt32": "wt32_sc01",
            "esp322432s028r": "esp32_2432s028r",
            "esp323248s035c": "esp32_3248s035c",
            "m5stackcore2": "m5stack_core2",
            "lilygo": "lilygo_t_display"
        }
        
        for pattern, model_key in model_mappings.items():
            if pattern in model_clean:
                res = get_device_resolution(model_key)
                if res:
                    return {"width": res.width, "height": res.height}
        
        return None
    
    async def _check_device_online(self, device_id: str) -> bool:
        """Check if device is online by checking its entities."""
        try:
            async with httpx.AsyncClient() as client:
                # Get entities for this device
                response = await client.get(
                    f"{self.base_url}/api/states",
                    headers=self.headers,
                    timeout=5.0
                )
                response.raise_for_status()
                entities = response.json()
                
                # Look for status entity
                for entity in entities:
                    entity_id = entity.get("entity_id", "")
                    if "openhasp" in entity_id and "status" in entity_id:
                        state = entity.get("state", "").lower()
                        return state in ["on", "online", "connected"]
                
                # If no status entity found, assume online
                return True
                
        except Exception as e:
            logger.warning(f"Could not check device online status: {e}")
            return True  # Assume online if we can't check
    
    async def validate_entity_exists(self, entity_id: str) -> tuple[bool, Optional[str]]:
        """
        Validate that an entity exists in Home Assistant.
        
        Returns:
            (exists, error_message)
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/api/states/{entity_id}",
                    headers=self.headers,
                    timeout=5.0
                )
                
                if response.status_code == 200:
                    return True, None
                elif response.status_code == 404:
                    return False, f"Entity '{entity_id}' not found in Home Assistant"
                else:
                    return False, f"Error checking entity: HTTP {response.status_code}"
                    
        except Exception as e:
            logger.error(f"Error validating entity {entity_id}: {e}")
            return False, f"Error validating entity: {str(e)}"
