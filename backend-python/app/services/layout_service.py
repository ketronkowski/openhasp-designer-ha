"""Layout storage service."""
import json
import uuid
from pathlib import Path
from typing import List, Optional
from datetime import datetime
from app.models.layout import Layout, Page
from app.models.designer import DesignerObjectDto
from app.config import settings


class LayoutStorageService:
    """Service for managing saved layouts."""
    
    def __init__(self):
        self.storage_path = Path(settings.ha_config_path) / "layouts"
        self.storage_path.mkdir(parents=True, exist_ok=True)
    
    def save_quick_layout(self, objects: List[DesignerObjectDto]):
        """Save quick layout (temporary save)."""
        quick_file = self.storage_path / "quick_layout.json"
        objects_data = [obj.model_dump() for obj in objects]
        quick_file.write_text(json.dumps(objects_data, indent=2))
    
    def load_quick_layout(self) -> List[DesignerObjectDto]:
        """Load quick layout."""
        quick_file = self.storage_path / "quick_layout.json"
        
        if not quick_file.exists():
            return []
        
        try:
            data = json.loads(quick_file.read_text())
            return [DesignerObjectDto(**obj) for obj in data]
        except Exception:
            return []
    
    def list_layouts(self) -> List[Layout]:
        """List all saved layouts."""
        layouts = []
        
        for layout_file in self.storage_path.glob("layout_*.json"):
            try:
                data = json.loads(layout_file.read_text())
                layouts.append(Layout(**data))
            except Exception:
                continue
        
        return sorted(layouts, key=lambda x: x.updated_at or x.created_at or "", reverse=True)
    
    def save_layout(self, layout: Layout) -> Layout:
        """Save a named layout."""
        # Generate ID if not provided
        if not layout.id:
            layout.id = str(uuid.uuid4())
        
        # Update timestamps
        now = datetime.utcnow().isoformat()
        if not layout.created_at:
            layout.created_at = now
        layout.updated_at = now
        
        # Save to file
        layout_file = self.storage_path / f"layout_{layout.id}.json"
        layout_file.write_text(json.dumps(layout.model_dump(), indent=2))
        
        return layout
    
    def load_layout(self, layout_id: str) -> Optional[Layout]:
        """Load a specific layout by ID."""
        layout_file = self.storage_path / f"layout_{layout_id}.json"
        
        if not layout_file.exists():
            return None
        
        try:
            data = json.loads(layout_file.read_text())
            return Layout(**data)
        except Exception:
            return None
    
    def delete_layout(self, layout_id: str) -> bool:
        """Delete a layout by ID."""
        layout_file = self.storage_path / f"layout_{layout_id}.json"
        
        if layout_file.exists():
            layout_file.unlink()
            return True
        
        return False
