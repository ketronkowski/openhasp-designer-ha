"""Validation service for openHASP configurations."""
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from app.services.ha_service import HomeAssistantService
from app.services.device_service import DeviceService
from app.models.device import get_device_resolution, validate_coordinates
import logging

logger = logging.getLogger(__name__)


class ValidationError(BaseModel):
    """Validation error details."""
    type: str  # 'entity', 'coordinate', 'object_id', 'device'
    message: str
    object_id: Optional[int] = None
    entity_id: Optional[str] = None
    page_id: Optional[int] = None


class ValidationWarning(BaseModel):
    """Validation warning details."""
    type: str
    message: str
    object_id: Optional[int] = None
    entity_id: Optional[str] = None


class ValidationResult(BaseModel):
    """Result of configuration validation."""
    passed: bool
    errors: List[ValidationError]
    warnings: List[ValidationWarning]
    
    @property
    def has_errors(self) -> bool:
        return len(self.errors) > 0
    
    @property
    def has_warnings(self) -> bool:
        return len(self.warnings) > 0


class ValidationOptions(BaseModel):
    """Options for validation."""
    validate_entities: bool = True
    check_bounds: bool = True
    verify_device: bool = True
    check_object_ids: bool = True
    check_overlaps: bool = False  # NEW: Check for overlapping objects
    skip_warnings: bool = False


class ValidationService:
    """Service for validating openHASP configurations."""
    
    def __init__(self, ha_service: HomeAssistantService, device_service: DeviceService):
        self.ha_service = ha_service
        self.device_service = device_service
    
    async def validate_configuration(
        self,
        config: List[Dict[str, Any]],
        device_id: str,
        options: ValidationOptions = ValidationOptions()
    ) -> ValidationResult:
        """
        Validate entire configuration.
        
        Args:
            config: List of page/object configurations
            device_id: Target device ID
            options: Validation options
        
        Returns:
            ValidationResult with errors and warnings
        """
        errors: List[ValidationError] = []
        warnings: List[ValidationWarning] = []
        
        # Validate device
        if options.verify_device:
            device_error = await self.validate_device(device_id)
            if device_error:
                errors.append(device_error)
                # If device is invalid, skip other validations
                return ValidationResult(passed=False, errors=errors, warnings=warnings)
        
        # Get device resolution for coordinate validation
        device_resolution = None
        if options.check_bounds:
            # Try to get device model from HA
            devices = await self.device_service.get_openhasp_devices()
            device = next((d for d in devices if d.get('device_id') == device_id), None)
            if device and device.get('model_key'):
                device_resolution = get_device_resolution(device['model_key'])
        
        # Validate object IDs
        if options.check_object_ids:
            id_errors = self.validate_object_ids(config)
            errors.extend(id_errors)
        
        # Validate entities
        if options.validate_entities:
            entity_errors, entity_warnings = await self.validate_entities(config)
            errors.extend(entity_errors)
            warnings.extend(entity_warnings)
        
        # Validate coordinates
        if options.check_bounds and device_resolution:
            coord_errors = self.validate_object_coordinates(config, device_resolution)
            errors.extend(coord_errors)
        
        # Check for overlaps (warnings, not errors)
        if options.check_overlaps:
            overlap_warnings = self.detect_overlaps(config)
            warnings.extend(overlap_warnings)
        
        passed = len(errors) == 0
        return ValidationResult(passed=passed, errors=errors, warnings=warnings)
    
    async def validate_entities(
        self,
        config: List[Dict[str, Any]]
    ) -> tuple[List[ValidationError], List[ValidationWarning]]:
        """
        Validate all entity IDs in configuration.
        
        Args:
            config: List of page/object configurations
        
        Returns:
            Tuple of (errors, warnings)
        """
        errors: List[ValidationError] = []
        warnings: List[ValidationWarning] = []
        
        # Extract all entity IDs from config
        entity_ids = set()
        entity_map = {}  # entity_id -> list of object_ids
        
        for item in config:
            entity_id = item.get('entity_id')
            if entity_id:
                entity_ids.add(entity_id)
                if entity_id not in entity_map:
                    entity_map[entity_id] = []
                entity_map[entity_id].append(item.get('id'))
        
        # Validate each entity
        for entity_id in entity_ids:
            exists, error_msg = await self.device_service.validate_entity_exists(entity_id)
            
            if not exists:
                # Entity doesn't exist - this is an error
                for obj_id in entity_map[entity_id]:
                    errors.append(ValidationError(
                        type='entity',
                        message=f"Entity '{entity_id}' does not exist in Home Assistant",
                        object_id=obj_id,
                        entity_id=entity_id
                    ))
            else:
                # Entity exists, check if it's available
                # This would require fetching entity state, which we can add later
                # For now, just log a warning if we can't verify state
                pass
        
        return errors, warnings
    
    def validate_object_coordinates(
        self,
        config: List[Dict[str, Any]],
        device_resolution
    ) -> List[ValidationError]:
        """
        Validate object coordinates against device screen size.
        
        Args:
            config: List of page/object configurations
            device_resolution: Device resolution info
        
        Returns:
            List of validation errors
        """
        errors: List[ValidationError] = []
        
        for item in config:
            # Skip pages (they don't have coordinates)
            if item.get('obj') == 'page':
                continue
            
            x = item.get('x', 0)
            y = item.get('y', 0)
            w = item.get('w', 0)
            h = item.get('h', 0)
            obj_id = item.get('id')
            
            # Validate coordinates
            is_valid, error_msg = validate_coordinates(
                x, y, w, h,
                device_resolution.width,
                device_resolution.height
            )
            
            if not is_valid:
                errors.append(ValidationError(
                    type='coordinate',
                    message=error_msg,
                    object_id=obj_id
                ))
        
        return errors
    
    def validate_object_ids(
        self,
        config: List[Dict[str, Any]]
    ) -> List[ValidationError]:
        """
        Check for duplicate object IDs.
        
        Args:
            config: List of page/object configurations
        
        Returns:
            List of validation errors
        """
        errors: List[ValidationError] = []
        seen_ids = set()
        
        for item in config:
            obj_id = item.get('id')
            if obj_id is None:
                continue
            
            if obj_id in seen_ids:
                errors.append(ValidationError(
                    type='object_id',
                    message=f"Duplicate object ID: {obj_id}",
                    object_id=obj_id
                ))
            else:
                seen_ids.add(obj_id)
        
        return errors
    
    async def validate_device(self, device_id: str) -> Optional[ValidationError]:
        """
        Verify device exists and is online.
        
        Args:
            device_id: Device ID to validate
        
        Returns:
            ValidationError if device is invalid, None otherwise
        """
        try:
            devices = await self.device_service.get_openhasp_devices()
            device = next((d for d in devices if d.get('device_id') == device_id), None)
            
            if not device:
                return ValidationError(
                    type='device',
                    message=f"Device '{device_id}' not found in Home Assistant"
                )
            
            # Check if device is online
            if not device.get('online', False):
                return ValidationError(
                    type='device',
                    message=f"Device '{device.get('name', device_id)}' is offline"
                )
            
            return None
            
        except Exception as e:
            logger.error(f"Error validating device {device_id}: {e}")
            return ValidationError(
                type='device',
                message=f"Failed to validate device: {str(e)}"
            )
    
    def detect_overlaps(
        self,
        config: List[Dict[str, Any]]
    ) -> List[ValidationWarning]:
        """
        Detect overlapping objects on the same page.
        
        Args:
            config: List of page/object configurations
        
        Returns:
            List of validation warnings for overlaps
        """
        warnings: List[ValidationWarning] = []
        
        # Group objects by page
        by_page: Dict[int, List[Dict]] = {}
        for item in config:
            if item.get('obj') == 'page':
                continue
            
            page = item.get('page', 0)
            if page not in by_page:
                by_page[page] = []
            by_page[page].append(item)
        
        # Check each page for overlaps
        for page, objects in by_page.items():
            for i, obj1 in enumerate(objects):
                for obj2 in objects[i+1:]:
                    if self._rectangles_overlap(obj1, obj2):
                        warnings.append(ValidationWarning(
                            type='overlap',
                            message=f"Objects {obj1.get('id')} and {obj2.get('id')} overlap on page {page}",
                            object_id=obj1.get('id')
                        ))
        
        return warnings
    
    def _rectangles_overlap(self, obj1: Dict, obj2: Dict) -> bool:
        """
        Check if two rectangular objects overlap.
        
        Args:
            obj1: First object with x, y, w, h
            obj2: Second object with x, y, w, h
        
        Returns:
            True if rectangles overlap
        """
        x1, y1 = obj1.get('x', 0), obj1.get('y', 0)
        w1, h1 = obj1.get('w', 0), obj1.get('h', 0)
        x2, y2 = obj2.get('x', 0), obj2.get('y', 0)
        w2, h2 = obj2.get('w', 0), obj2.get('h', 0)
        
        # Check if rectangles do NOT overlap, then negate
        return not (
            x1 + w1 <= x2 or  # obj1 is completely left of obj2
            x2 + w2 <= x1 or  # obj1 is completely right of obj2
            y1 + h1 <= y2 or  # obj1 is completely above obj2
            y2 + h2 <= y1     # obj1 is completely below obj2
        )
