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
        
        Returns list of devices with:
        - device_id
        - name
        - model
        - online_status
        - resolution (if known)
        """
        try:
            async with httpx.AsyncClient() as client:
                # Get all devices from HA
                response = await client.get(
                    f"{self.base_url}/api/config/device_registry/list",
                    headers=self.headers,
                    timeout=10.0
                )
                response.raise_for_status()
                all_devices = response.json()
                
                # Filter for openHASP devices
                openhasp_devices = []
                for device in all_devices:
                    # Check if device is openHASP (via integration)
                    if self._is_openhasp_device(device):
                        device_info = await self._enrich_device_info(device)
                        openhasp_devices.append(device_info)
                
                return openhasp_devices
                
        except httpx.HTTPError as e:
            logger.error(f"Failed to fetch devices from HA: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error fetching devices: {e}")
            return []
    
    def _is_openhasp_device(self, device: Dict[str, Any]) -> bool:
        """Check if device is an openHASP device."""
        # Check for openHASP integration
        config_entries = device.get("config_entries", [])
        identifiers = device.get("identifiers", [])
        
        # Look for openhasp in config entries or identifiers
        for entry in config_entries:
            if "openhasp" in str(entry).lower():
                return True
        
        for identifier in identifiers:
            if isinstance(identifier, (list, tuple)) and len(identifier) > 0:
                if "openhasp" in str(identifier[0]).lower():
                    return True
        
        return False
    
    async def _enrich_device_info(self, device: Dict[str, Any]) -> Dict[str, Any]:
        """Enrich device info with resolution and online status."""
        device_id = device.get("id")
        name = device.get("name_by_user") or device.get("name", "Unknown")
        model = device.get("model", "").lower()
        manufacturer = device.get("manufacturer", "")
        
        # Try to get resolution from model
        resolution = None
        for model_key in ["lanbon_l8", "wt32_sc01", "esp32_2432s028r", "esp32_3248s035c"]:
            if model_key.replace("_", "") in model.replace("-", "").replace("_", ""):
                res = get_device_resolution(model_key)
                if res:
                    resolution = {"width": res.width, "height": res.height}
                    break
        
        # Get online status from entities
        online = await self._check_device_online(device_id)
        
        return {
            "device_id": device_id,
            "name": name,
            "model": model or "Unknown",
            "manufacturer": manufacturer,
            "resolution": resolution,
            "online": online,
            "identifiers": device.get("identifiers", [])
        }
    
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
