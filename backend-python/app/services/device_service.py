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
                    
                    # Special handling for openhasp.{device_id} entities (main device entity)
                    if entity_id.startswith("openhasp."):
                        device_name = entity_id.split(".")[1]
                        if device_name not in devices_map:
                            attributes = entity.get("attributes", {})
                            devices_map[device_name] = {
                                "device_id": device_name,
                                "name": "",  # Will be set later
                                "model": attributes.get("tftDriver", "Unknown"),
                                "manufacturer": "openHASP",
                                "online": True,
                                "resolution": {
                                    "width": attributes.get("tftWidth"),
                                    "height": attributes.get("tftHeight")
                                } if attributes.get("tftWidth") and attributes.get("tftHeight") else None,
                                "entities": [entity_id],
                                "entity_id": device_name,
                                "friendly_names": [],
                                "ip": attributes.get("ip"),
                                "version": attributes.get("version")
                            }
                        continue
                    
                    # Look for openhasp entities (e.g., "sensor.plate01_status")
                    if not entity_id.startswith(("sensor.", "switch.", "light.", "binary_sensor.", "button.", "number.")):
                        continue
                    
                    # Check if it's an openHASP entity
                    attributes = entity.get("attributes", {})
                    integration = attributes.get("integration", "")
                    
                    # Multiple ways to detect openHASP
                    is_openhasp = (
                        "openhasp" in entity_id.lower() or
                        "plate" in entity_id.lower() or
                        integration == "openhasp"
                    )
                    
                    # Skip the integration itself (e.g., "switch.openhasp_pre_release")
                    if "pre_release" in entity_id.lower() or "prerelease" in entity_id.lower():
                        continue
                    
                    if is_openhasp:
                        # Extract device name from entity_id (e.g., "kevin_plate" from "light.plate_kevin_backlight")
                        parts = entity_id.split(".")
                        if len(parts) >= 2:
                            # Get the part before common suffixes
                            entity_base = parts[1]
                            
                            # Try to extract device name by removing common suffixes
                            for suffix in ["_backlight", "_antiburn", "_moodlight", "_status", "_light", "_restart", "_page_number"]:
                                if suffix in entity_base:
                                    entity_base = entity_base.replace(suffix, "")
                                    break
                            
                            # Remove trailing numbers (e.g., "_12", "_14")
                            import re
                            entity_base = re.sub(r'_\d+$', '', entity_base)
                            
                            # Use this as device_id
                            device_id = entity_base
                            
                            if device_id not in devices_map:
                                devices_map[device_id] = {
                                    "device_id": device_id,
                                    "name": "",  # Will be set after collecting all entities
                                    "model": attributes.get("model", "Unknown"),
                                    "manufacturer": "openHASP",
                                    "online": True,
                                    "resolution": None,
                                    "entities": [],
                                    "entity_id": device_id,
                                    "friendly_names": []  # Collect all friendly names
                                }
                            
                            # Track entities for this device
                            devices_map[device_id]["entities"].append(entity_id)
                            
                            # Collect friendly names
                            friendly_name = attributes.get("friendly_name", "")
                            if friendly_name:
                                devices_map[device_id]["friendly_names"].append(friendly_name)
                            
                            # Check online status from status entity
                            if "status" in entity_id.lower():
                                state = entity.get("state", "").lower()
                                devices_map[device_id]["online"] = state in ["on", "online", "connected", "available"]
                            
                            # Try to get model info
                            if attributes.get("model"):
                                devices_map[device_id]["model"] = attributes["model"]
                
                # Convert to list and enrich with resolution info
                devices = []
                for device_id, device_info in devices_map.items():
                    # Only include devices with multiple entities (real devices, not integration)
                    if len(device_info["entities"]) > 1:
                        # Try multiple strategies to get device name
                        device_name = await self._get_device_name_from_registry(device_info["entities"][0])
                        
                        if not device_name:
                            # Fallback to extracting from friendly names
                            device_name = self._extract_device_name(device_info["friendly_names"])
                        
                        device_info["name"] = device_name or device_id.replace("_", " ").title()
                        
                        # Remove temporary friendly_names list
                        if "friendly_names" in device_info:
                            del device_info["friendly_names"]
                        
                        # Try to determine resolution from model if not already set
                        if not device_info.get("resolution"):
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
    
    async def _get_device_name_from_registry(self, entity_id: str) -> Optional[str]:
        """
        Get device name from device registry using an entity ID.
        
        This fetches the actual device name set in HA (e.g., "Kevin's Office Plate").
        """
        try:
            async with httpx.AsyncClient() as client:
                # Get entity registry to find device_id
                logger.debug(f"Fetching entity registry for {entity_id}")
                response = await client.get(
                    f"{self.base_url}/api/config/entity_registry/list",
                    headers=self.headers,
                    timeout=5.0
                )
                
                logger.debug(f"Entity registry response status: {response.status_code}")
                
                if response.status_code != 200:
                    logger.warning(f"Entity registry API returned {response.status_code}: {response.text[:200]}")
                    return None
                
                entities = response.json()
                logger.debug(f"Found {len(entities)} entities in registry")
                
                # Find our entity and get its device_id
                ha_device_id = None
                for entity in entities:
                    if entity.get("entity_id") == entity_id:
                        ha_device_id = entity.get("device_id")
                        logger.debug(f"Found device_id for {entity_id}: {ha_device_id}")
                        break
                
                if not ha_device_id:
                    logger.debug(f"No device_id found for entity {entity_id}")
                    return None
                
                # Now get device info from device registry
                logger.debug(f"Fetching device registry for device_id: {ha_device_id}")
                response = await client.get(
                    f"{self.base_url}/api/config/device_registry/list",
                    headers=self.headers,
                    timeout=5.0
                )
                
                logger.debug(f"Device registry response status: {response.status_code}")
                
                if response.status_code != 200:
                    logger.warning(f"Device registry API returned {response.status_code}: {response.text[:200]}")
                    return None
                
                devices = response.json()
                logger.debug(f"Found {len(devices)} devices in registry")
                
                # Find our device and get its name
                for device in devices:
                    if device.get("id") == ha_device_id:
                        device_name = device.get("name_by_user") or device.get("name")
                        logger.info(f"Found device name from registry: {device_name}")
                        return device_name
                
                logger.debug(f"Device {ha_device_id} not found in device registry")
                return None
                
        except Exception as e:
            logger.warning(f"Could not fetch device name from registry: {e}")
            return None
    
    def _extract_device_name(self, friendly_names: List[str]) -> str:
        """
        Extract device name from list of entity friendly names.
        
        Finds common prefix among all friendly names, which typically
        represents the device name (e.g., "Kevin's Office Plate" from
        ["Kevin's Office Plate Backlight", "Kevin's Office Plate Moodlight"]).
        """
        if not friendly_names:
            return ""
        
        if len(friendly_names) == 1:
            # Single entity, remove common suffixes
            name = friendly_names[0]
            for suffix in [" Backlight", " Antiburn", " Moodlight", " Status", " Light"]:
                if name.endswith(suffix):
                    name = name[:-len(suffix)]
                    break
            return name.strip()
        
        # Find common prefix among all friendly names
        # Sort to make comparison easier
        sorted_names = sorted(friendly_names)
        first = sorted_names[0]
        last = sorted_names[-1]
        
        # Find common prefix
        common_prefix = ""
        for i in range(min(len(first), len(last))):
            if first[i] == last[i]:
                common_prefix += first[i]
            else:
                break
        
        # Clean up the prefix (remove trailing spaces and common suffixes)
        common_prefix = common_prefix.strip()
        
        # Remove common trailing words that aren't part of device name
        for suffix in [" Backlight", " Antiburn", " Moodlight", " Status", " Light"]:
            if common_prefix.endswith(suffix):
                common_prefix = common_prefix[:-len(suffix)]
        
        return common_prefix.strip()
    
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
