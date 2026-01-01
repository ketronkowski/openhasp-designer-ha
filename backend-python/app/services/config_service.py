"""Config publishing service."""
import json
from pathlib import Path
from typing import List
from app.models.designer import DesignerObjectDto
from app.models.hasp import (
    HaspButton, HaspLabel, HaspSlider, HaspCheckbox, 
    HaspSwitch, HaspDropdown, HaspObject
)
from app.config import settings


class ConfigPublisherService:
    """Service for publishing openHASP configurations."""
    
    def __init__(self):
        self.config_path = Path(settings.ha_config_path)
    
    def generate_jsonl(self, objects: List[HaspObject]) -> str:
        """Generate JSONL from HASP objects."""
        lines = []
        for obj in objects:
            # Convert to dict and exclude None values
            obj_dict = obj.model_dump(exclude_none=True)
            lines.append(json.dumps(obj_dict))
        return "\n".join(lines) + "\n"
    
    def publish_config(self, filename: str, dtos: List[DesignerObjectDto]):
        """Convert designer DTOs to JSONL and write to file."""
        hasp_objects = [self._dto_to_hasp_object(dto) for dto in dtos]
        jsonl = self.generate_jsonl(hasp_objects)
        
        # Ensure directory exists
        self.config_path.mkdir(parents=True, exist_ok=True)
        
        # Write JSONL file
        output_file = self.config_path / filename
        output_file.write_text(jsonl)
    
    def save_layout(self, objects: List[DesignerObjectDto]):
        """Save designer layout as JSON."""
        self.config_path.mkdir(parents=True, exist_ok=True)
        
        layout_file = self.config_path / "designer_layout.json"
        # Convert to dict for JSON serialization
        objects_data = [obj.model_dump() for obj in objects]
        layout_file.write_text(json.dumps(objects_data, indent=2))
    
    def load_layout(self) -> List[DesignerObjectDto]:
        """Load designer layout from JSON."""
        layout_file = self.config_path / "designer_layout.json"
        
        if not layout_file.exists():
            return []
        
        try:
            data = json.loads(layout_file.read_text())
            return [DesignerObjectDto(**obj) for obj in data]
        except Exception:
            return []
    
    def _dto_to_hasp_object(self, dto: DesignerObjectDto) -> HaspObject:
        """Convert DesignerObjectDto to appropriate HaspObject."""
        obj_type = dto.type
        
        if obj_type == "btn":
            return HaspButton(
                page=dto.page,
                id=dto.id,
                x=dto.x,
                y=dto.y,
                w=dto.width,
                h=dto.height,
                text=dto.text or "",
                entity=dto.entity_id
            )
        elif obj_type == "label":
            return HaspLabel(
                page=dto.page,
                id=dto.id,
                x=dto.x,
                y=dto.y,
                text=dto.text or ""
            )
        elif obj_type == "slider":
            return HaspSlider(
                page=dto.page,
                id=dto.id,
                x=dto.x,
                y=dto.y,
                w=dto.width,
                h=dto.height,
                min=dto.min or 0,
                max=dto.max or 100,
                entity=dto.entity_id
            )
        elif obj_type == "checkbox":
            return HaspCheckbox(
                page=dto.page,
                id=dto.id,
                x=dto.x,
                y=dto.y,
                text=dto.text or "",
                entity=dto.entity_id
            )
        elif obj_type == "sw":
            return HaspSwitch(
                page=dto.page,
                id=dto.id,
                x=dto.x,
                y=dto.y,
                w=dto.width,
                h=dto.height,
                entity=dto.entity_id
            )
        elif obj_type == "dropdown":
            return HaspDropdown(
                page=dto.page,
                id=dto.id,
                x=dto.x,
                y=dto.y,
                w=dto.width,
                h=dto.height,
                options=dto.options or "",
                entity=dto.entity_id
            )
        else:
            # Default to button for unknown types
            return HaspButton(
                page=dto.page,
                id=dto.id,
                x=dto.x,
                y=dto.y,
                w=dto.width,
                h=dto.height,
                text=dto.text or "",
                entity=dto.entity_id
            )
