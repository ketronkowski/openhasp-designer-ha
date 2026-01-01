"""FastAPI application for openHASP Designer backend."""
import logging
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from typing import List, Optional, Dict
from pydantic import BaseModel

from app.models.designer import DesignerObjectDto
from app.models.layout import Layout, Page
from app.models.device import get_all_device_models, get_device_resolution, validate_coordinates
from app.services.ha_service import HomeAssistantService
from app.services.config_service import ConfigPublisherService
from app.services.layout_service import LayoutStorageService
from app.services.import_service import ConfigImportService
from app.services.device_service import DeviceService
from app.services.yaml_service import YAMLConfigService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="openHASP Designer API",
    description="Backend API for openHASP Designer with Home Assistant integration",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
ha_service = HomeAssistantService()
config_service = ConfigPublisherService()
layout_service = LayoutStorageService()
import_service = ConfigImportService()
device_service = DeviceService()
yaml_service = YAMLConfigService()


# ============================================================================
# Home Assistant API Routes
# ============================================================================

@app.get("/api/ha/entities")
async def get_entities(
    type: Optional[str] = Query(None, description="Filter by entity domain (e.g., 'light', 'switch')"),
    search: Optional[str] = Query(None, description="Search query for entity_id or friendly_name")
):
    """Get Home Assistant entities with optional filtering."""
    return await ha_service.get_enhanced_entities(type=type, search=search)


@app.post("/api/ha/reload")
async def reload_pages():
    """Trigger openHASP page reload in Home Assistant."""
    try:
        await ha_service.reload_pages()
        return {"status": "Pages reloaded"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Phase 1: Device Discovery & Validation
# ============================================================================

@app.get("/api/ha/devices/openhasp")
async def get_openhasp_devices():
    """
    Discover all openHASP devices from Home Assistant.
    
    Returns devices with resolution info and online status.
    """
    try:
        devices = await device_service.get_openhasp_devices()
        return devices
    except Exception as e:
        logger.error(f"Failed to get openHASP devices: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/ha/devices/resolutions")
async def get_device_resolutions():
    """Get all known device models and their screen resolutions."""
    models = get_all_device_models()
    return {
        key: {
            "width": res.width,
            "height": res.height,
            "model": res.model,
            "description": res.description
        }
        for key, res in models.items()
    }


@app.get("/api/ha/devices/resolution/{model_key}")
async def get_resolution_for_model(model_key: str):
    """Get screen resolution for a specific device model."""
    resolution = get_device_resolution(model_key)
    if not resolution:
        raise HTTPException(status_code=404, detail=f"Unknown device model: {model_key}")
    return {
        "width": resolution.width,
        "height": resolution.height,
        "model": resolution.model,
        "description": resolution.description
    }


@app.post("/api/ha/validate/entity")
async def validate_entity(entity_id: str = Query(..., description="Entity ID to validate")):
    """Validate that an entity exists in Home Assistant."""
    exists, error = await device_service.validate_entity_exists(entity_id)
    if not exists:
        return {"valid": False, "error": error}
    return {"valid": True}


@app.post("/api/ha/validate/coordinates")
async def validate_object_coordinates(
    x: int = Query(..., description="X coordinate"),
    y: int = Query(..., description="Y coordinate"),
    width: int = Query(..., description="Object width"),
    height: int = Query(..., description="Object height"),
    device_width: int = Query(..., description="Device screen width"),
    device_height: int = Query(..., description="Device screen height")
):
    """Validate object coordinates against device screen size."""
    is_valid, error = validate_coordinates(x, y, width, height, device_width, device_height)
    if not is_valid:
        return {"valid": False, "error": error}
    return {"valid": True}


@app.get("/api/entities/{entity_id}/state")
async def get_entity_state(entity_id: str):
    """
    Get current state of a single entity.
    
    Returns:
        Entity state with attributes
    """
    try:
        state = await ha_service.get_entity_state(entity_id)
        return {
            "entity_id": entity_id,
            "state": state.get("state"),
            "attributes": state.get("attributes", {}),
            "last_updated": state.get("last_updated"),
            "last_changed": state.get("last_changed")
        }
    except Exception as e:
        logger.error(f"Failed to get state for {entity_id}: {e}")
        raise HTTPException(status_code=404, detail=f"Entity {entity_id} not found or unavailable")


class EntityStatesRequest(BaseModel):
    """Request model for batch entity states."""
    entity_ids: List[str]


@app.post("/api/entities/states")
async def get_multiple_entity_states(request: EntityStatesRequest):
    """
    Get states for multiple entities at once.
    
    Args:
        request: List of entity IDs
    
    Returns:
        Dictionary mapping entity_id to state info
    """
    states = {}
    
    for entity_id in request.entity_ids:
        try:
            state = await ha_service.get_entity_state(entity_id)
            states[entity_id] = {
                "state": state.get("state"),
                "attributes": state.get("attributes", {}),
                "available": True
            }
        except Exception as e:
            logger.debug(f"Entity {entity_id} unavailable: {e}")
            states[entity_id] = {
                "state": "unavailable",
                "attributes": {},
                "available": False
            }
    
    return states


# ============================================================================
# Config API Routes
# ============================================================================

class PublishRequest(BaseModel):
    """Request model for publishing configuration."""
    objects: List[DesignerObjectDto]
    device_id: str
    validate: bool = True
    dry_run: bool = False


class DeploymentResult(BaseModel):
    """Result of configuration deployment."""
    success: bool
    device_id: str
    device_name: Optional[str] = None
    pages_deployed: int = 0
    objects_deployed: int = 0
    validation: dict
    deployment_time: Optional[str] = None
    error: Optional[str] = None


@app.post("/api/config/publish", response_model=DeploymentResult)
async def publish_config(request: PublishRequest):
    """
    Publish designer configuration to Home Assistant device.
    
    Args:
        request: PublishRequest with objects, device_id, and options
    
    Returns:
        DeploymentResult with status and validation details
    """
    from app.services.validation_service import ValidationService, ValidationOptions
    from datetime import datetime
    
    try:
        # Initialize validation service
        validation_service = ValidationService(ha_service, device_service)
        
        # Convert objects to config format
        config = [obj.dict() for obj in request.objects]
        
        # Run validation if enabled
        validation_result = None
        if request.validate:
            validation_options = ValidationOptions(
                validate_entities=True,
                check_bounds=True,
                verify_device=True,
                check_object_ids=True
            )
            
            validation_result = await validation_service.validate_configuration(
                config,
                request.device_id,
                validation_options
            )
            
            # If validation failed and not dry-run, return error
            if not validation_result.passed and not request.dry_run:
                return DeploymentResult(
                    success=False,
                    device_id=request.device_id,
                    validation={
                        "passed": False,
                        "errors": [e.dict() for e in validation_result.errors],
                        "warnings": [w.dict() for w in validation_result.warnings]
                    },
                    error="Validation failed. Please fix errors before deploying."
                )
        
        # If dry-run, return validation results without deploying
        if request.dry_run:
            return DeploymentResult(
                success=validation_result.passed if validation_result else True,
                device_id=request.device_id,
                validation={
                    "passed": validation_result.passed if validation_result else True,
                    "errors": [e.dict() for e in validation_result.errors] if validation_result else [],
                    "warnings": [w.dict() for w in validation_result.warnings] if validation_result else []
                }
            )
        
        # Deploy configuration
        config_service.publish_config("pages.jsonl", request.objects)
        await ha_service.reload_pages()
        
        # Count pages and objects
        pages = sum(1 for obj in request.objects if obj.obj == "page")
        objects = len(request.objects) - pages
        
        # Get device name
        devices = await device_service.get_openhasp_devices()
        device = next((d for d in devices if d.get('device_id') == request.device_id), None)
        device_name = device.get('name') if device else None
        
        return DeploymentResult(
            success=True,
            device_id=request.device_id,
            device_name=device_name,
            pages_deployed=pages,
            objects_deployed=objects,
            validation={
                "passed": validation_result.passed if validation_result else True,
                "errors": [],
                "warnings": [w.dict() for w in validation_result.warnings] if validation_result and validation_result.warnings else []
            },
            deployment_time=datetime.utcnow().isoformat() + "Z"
        )
        
    except Exception as e:
        logger.error(f"Failed to publish config: {e}")
        return DeploymentResult(
            success=False,
            device_id=request.device_id,
            validation={"passed": False, "errors": [], "warnings": []},
            error=str(e)
        )


@app.post("/api/config/layout")
async def save_quick_layout(objects: List[DesignerObjectDto]):
    """Save quick layout (temporary save)."""
    try:
        layout_service.save_quick_layout(objects)
        return {"status": "Layout saved"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/config/layout")
async def load_quick_layout():
    """Load quick layout."""
    return layout_service.load_quick_layout()


@app.get("/api/config/layouts")
async def list_layouts():
    """List all saved layouts."""
    return layout_service.list_layouts()


@app.post("/api/config/layouts")
async def create_layout(layout: Layout):
    """Create or update a named layout."""
    try:
        saved_layout = layout_service.save_layout(layout)
        return saved_layout
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/config/layouts/{layout_id}")
async def get_layout(layout_id: str):
    """Get a specific layout by ID."""
    layout = layout_service.load_layout(layout_id)
    if not layout:
        raise HTTPException(status_code=404, detail="Layout not found")
    return layout


@app.delete("/api/config/layouts/{layout_id}")
async def delete_layout(layout_id: str):
    """Delete a layout by ID."""
    deleted = layout_service.delete_layout(layout_id)
    return {"deleted": deleted}


# ============================================================================
# Import API Routes
# ============================================================================

@app.get("/api/config/import/available")
async def list_available_configs():
    """List available JSONL config files."""
    return import_service.list_available_configs()


class ImportRequest(BaseModel):
    """Request model for importing configuration."""
    source: str = 'file'  # 'file' or 'device'
    content: Optional[str] = None  # JSONL content if source='file'
    device_id: Optional[str] = None  # Device ID if source='device'
    validate_entities: bool = False
    mode: str = 'replace'  # 'replace' or 'merge'


class ImportResult(BaseModel):
    """Result model for import operation."""
    success: bool
    objects: List[Dict]
    metadata: Dict
    validation: Optional[Dict] = None
    warnings: List[str] = []


@app.post("/api/config/import", response_model=ImportResult)
async def import_config_enhanced(request: ImportRequest):
    """
    Import JSONL configuration from content or device.
    
    Supports:
    - File content import (source='file', content=<jsonl>)
    - Device import (source='device', device_id=<id>) - not yet implemented
    - Entity validation
    - Merge/replace modes
    """
    try:
        # Parse JSONL content
        if request.source == 'file' and request.content:
            objects = import_service.parse_jsonl(request.content)
        elif request.source == 'device' and request.device_id:
            # Device import not yet implemented
            raise HTTPException(
                status_code=501,
                detail="Device import not yet implemented. Please use file upload."
            )
        else:
            raise HTTPException(
                status_code=400,
                detail="Must provide either 'content' (for file) or 'device_id' (for device)"
            )
        
        # Extract metadata
        metadata = import_service.extract_metadata(objects)
        
        # Validate entities if requested
        validation_result = None
        if request.validate_entities:
            try:
                # Use validation service
                validation_result = await validation_service.validate_configuration(
                    objects,
                    request.device_id or "unknown"
                )
                validation_dict = {
                    "passed": validation_result.passed,
                    "errors": [
                        {
                            "type": err.type,
                            "message": err.message,
                            "entity_id": err.entity_id,
                            "object_id": err.object_id
                        }
                        for err in validation_result.errors
                    ],
                    "warnings": [
                        {
                            "type": warn.type,
                            "message": warn.message
                        }
                        for warn in validation_result.warnings
                    ]
                }
            except Exception as e:
                logger.warning(f"Validation failed: {e}")
                validation_dict = {
                    "passed": True,  # Don't block import on validation failure
                    "errors": [],
                    "warnings": [{"type": "validation_error", "message": f"Validation service unavailable: {str(e)}"}]
                }
        else:
            validation_dict = {"passed": True, "errors": [], "warnings": []}
        
        return ImportResult(
            success=True,
            objects=objects,
            metadata=metadata,
            validation=validation_dict,
            warnings=[]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Import failed: {e}")
        raise HTTPException(status_code=500, detail=f"Import failed: {str(e)}")


@app.get("/api/config/import/device/{device_id}")
async def import_config_from_device(device_id: str):
    """
    Import JSONL configuration directly from a device.
    
    Automatically finds the JSONL file for the specified device
    and returns parsed configuration.
    
    Args:
        device_id: Device ID to import from
    
    Returns:
        Parsed configuration objects
    """
    try:
        # Try common filename patterns
        possible_filenames = [
            f"{device_id}.jsonl",
            f"pages_{device_id}.jsonl",
            "pages.jsonl"  # fallback
        ]
        
        layout = None
        for filename in possible_filenames:
            layout = import_service.import_from_ha_config(filename)
            if layout:
                logger.info(f"Found config for {device_id} in {filename}")
                break
        
        if not layout:
            raise HTTPException(
                status_code=404,
                detail=f"No configuration found for device {device_id}"
            )
        
        # Convert to objects format
        objects = []
        for page in layout.pages:
            for obj in page.objects:
                objects.append(obj.dict())
        
        return {
            "success": True,
            "device_id": device_id,
            "objects": objects,
            "metadata": {
                "project_name": layout.name or device_id,
                "page_size": "medium_portrait"  # default
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Device import failed for {device_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Device import failed: {str(e)}")


@app.get("/api/config/import")
async def import_config_for_designer():
    """Import JSONL config and return pages for designer (legacy endpoint)."""
    layout = import_service.import_from_ha_config("pages.jsonl")
    if not layout:
        return []
    return layout.pages


class YAMLGenerationRequest(BaseModel):
    """Request model for YAML generation."""
    objects: List[Dict]
    device_id: str


@app.post("/api/config/yaml")
async def generate_yaml_config(request: YAMLGenerationRequest):
    """
    Generate Home Assistant YAML configuration for openHASP.
    
    Creates YAML with:
    - Event handlers for interactive objects
    - State update automations
    - Entity bindings
    
    Args:
        request: Configuration objects and device ID
    
    Returns:
        YAML configuration string
    """
    try:
        yaml_content = yaml_service.generate_yaml(
            request.objects,
            request.device_id
        )
        
        return {
            "success": True,
            "yaml": yaml_content,
            "device_id": request.device_id,
            "suggested_path": f"/config/packages/openhasp_{request.device_id}.yaml"
        }
    except Exception as e:
        logger.error(f"YAML generation failed: {e}")
        raise HTTPException(status_code=500, detail=f"YAML generation failed: {str(e)}")



# ============================================================================
# Status/Health Routes
# ============================================================================

@app.get("/api/status")
async def get_status():
    """Health check endpoint."""
    return {
        "status": "ok",
        "service": "openHASP Designer Backend",
        "version": "1.0.0"
    }


@app.get("/")
async def root():
    """Root endpoint - redirect to API docs."""
    return {
        "message": "openHASP Designer API",
        "docs": "/docs",
        "health": "/api/status"
    }


# Mount static files (Vue frontend) if available
# This will be populated by the Docker build
try:
    app.mount("/", StaticFiles(directory="static", html=True), name="static")
except RuntimeError:
    # Static directory doesn't exist (development mode)
    logger.warning("Static directory not found - running in API-only mode")
