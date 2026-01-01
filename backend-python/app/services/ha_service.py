"""Home Assistant API service."""
import httpx
import logging
from typing import List, Dict, Any, Optional
from app.config import settings

logger = logging.getLogger(__name__)


class HomeAssistantService:
    """Service for interacting with Home Assistant REST API."""
    
    def __init__(self):
        self.base_url = settings.ha_url
        self.headers = {"Authorization": f"Bearer {settings.ha_token}"}
    
    async def get_entities(self) -> List[Dict[str, Any]]:
        """Fetch all entities from Home Assistant."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/api/states",
                    headers=self.headers,
                    timeout=10.0
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"Failed to fetch entities from Home Assistant: {e}")
            return []
    
    async def get_enhanced_entities(
        self, 
        type: Optional[str] = None, 
        search: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get entities with enhanced metadata (friendly name, icon, domain)."""
        entities = await self.get_entities()
        
        # Apply type filter
        if type:
            entities = [
                e for e in entities 
                if e.get("entity_id", "").startswith(f"{type}.")
            ]
        
        # Apply search filter
        if search:
            search_lower = search.lower()
            entities = [
                e for e in entities
                if search_lower in e.get("entity_id", "").lower()
                or search_lower in e.get("attributes", {}).get("friendly_name", "").lower()
            ]
        
        # Enhance with metadata
        return [self._enhance_entity(e) for e in entities]
    
    def _enhance_entity(self, entity: Dict[str, Any]) -> Dict[str, Any]:
        """Add metadata to entity."""
        entity_id = entity.get("entity_id", "")
        attributes = entity.get("attributes", {})
        domain = entity_id.split(".")[0] if "." in entity_id else ""
        friendly_name = attributes.get("friendly_name", entity_id)
        
        return {
            "entity_id": entity_id,
            "state": entity.get("state", "unknown"),
            "friendly_name": friendly_name,
            "short_name": friendly_name,
            "icon": attributes.get("icon", self._get_default_icon(domain)),
            "domain": domain,
            "attributes": attributes
        }
    
    def _get_default_icon(self, domain: str) -> str:
        """Get default icon for a domain."""
        icons = {
            "light": "mdi:lightbulb",
            "switch": "mdi:light-switch",
            "sensor": "mdi:gauge",
            "binary_sensor": "mdi:checkbox-marked-circle",
            "cover": "mdi:window-shutter",
            "climate": "mdi:thermostat",
            "fan": "mdi:fan",
            "lock": "mdi:lock",
            "media_player": "mdi:speaker",
        }
        return icons.get(domain, "mdi:home-assistant")
    
    async def reload_pages(self):
        """Trigger openHASP page reload via Home Assistant service."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/api/services/openhasp/load_pages",
                    headers=self.headers,
                    json={},
                    timeout=10.0
                )
                response.raise_for_status()
                logger.info("Successfully triggered openHASP page reload")
        except Exception as e:
            logger.error(f"Failed to reload openHASP pages: {e}")
            raise RuntimeError(f"Failed to reload pages: {e}")
    
    async def get_entity_state(self, entity_id: str) -> dict:
        """
        Get the current state of an entity.
        
        Args:
            entity_id: Entity ID to fetch state for
        
        Returns:
            Dictionary with state, attributes, and timestamps
        
        Raises:
            Exception if entity not found or HA unavailable
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/api/states/{entity_id}",
                    headers=self.headers,
                    timeout=10.0
                )
                
                if response.status_code == 404:
                    raise Exception(f"Entity {entity_id} not found")
                
                response.raise_for_status()
                return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error fetching state for {entity_id}: {e}")
            raise
        except Exception as e:
            logger.error(f"Error fetching state for {entity_id}: {e}")
            raise
