"""Config import service."""
import json
import logging
from pathlib import Path
from typing import List, Optional, Tuple, Dict
from app.models.layout import Layout, Page
from app.models.designer import DesignerObjectDto
from app.config import settings

logger = logging.getLogger(__name__)


class ConfigImportService:
    """Service for importing existing openHASP configurations."""
    
    def __init__(self):
        self.config_path = Path(settings.ha_config_path)
    
    def list_available_configs(self) -> List[str]:
        """List available JSONL config files."""
        if not self.config_path.exists():
            return []
        
        return [f.name for f in self.config_path.glob("*.jsonl")]
    
    def import_from_ha_config(self, filename: str) -> Optional[Layout]:
        """Import JSONL config and convert to Layout."""
        config_file = self.config_path / filename
        
        if not config_file.exists():
            return None
        
        try:
            # Read JSONL file
            lines = config_file.read_text().strip().split("\n")
            hasp_objects = [json.loads(line) for line in lines if line.strip()]
            
            # Group objects by page
            pages_dict = {}
            for obj in hasp_objects:
                page_num = obj.get("page", 1)
                if page_num not in pages_dict:
                    pages_dict[page_num] = []
                
                # Convert HASP object to DesignerObjectDto
                dto = self._hasp_to_dto(obj)
                if dto:
                    pages_dict[page_num].append(dto)
            
            # Create Page objects
            pages = [
                Page(page_id=page_num, objects=objects)
                for page_num, objects in sorted(pages_dict.items())
            ]
            
            # Create Layout
            layout = Layout(
                id=filename.replace(".jsonl", ""),
                name=f"Imported from {filename}",
                description=f"Imported configuration from {filename}",
                pages=pages
            )
            
            return layout
            
        except Exception as e:
            logger.error(f"Error importing config: {e}")
            return None
    
    def _hasp_to_dto(self, hasp_obj: dict) -> Optional[DesignerObjectDto]:
        """Convert HASP object to DesignerObjectDto."""
        try:
            obj_type = hasp_obj.get("obj", "")
            
            # Map HASP obj type to designer type
            type_mapping = {
                "btn": "btn",
                "label": "label",
                "slider": "slider",
                "checkbox": "checkbox",
                "sw": "sw",
                "dropdown": "dropdown",
            }
            
            designer_type = type_mapping.get(obj_type, obj_type)
            
            return DesignerObjectDto(
                id=hasp_obj.get("id", 0),
                type=designer_type,
                x=hasp_obj.get("x", 0),
                y=hasp_obj.get("y", 0),
                width=hasp_obj.get("w", 100),
                height=hasp_obj.get("h", 50),
                text=hasp_obj.get("text"),
                entity_id=hasp_obj.get("entity"),
                page=hasp_obj.get("page", 1),
                color=hasp_obj.get("color"),
                background_color=hasp_obj.get("bg_color"),
                font_size=hasp_obj.get("font_size"),
                options=hasp_obj.get("options"),
                min=hasp_obj.get("min"),
                max=hasp_obj.get("max")
            )
        except Exception:
            return None
    
    # ========== Phase 3: New Methods ==========
    
    def parse_jsonl(self, content: str) -> List[Dict]:
        """
        Parse JSONL content into list of objects.
        
        Args:
            content: JSONL string content
            
        Returns:
            List of parsed objects
            
        Skips:
            - Empty lines
            - Comment lines (starting with #)
            - Invalid JSON lines (logs warning)
        """
        objects = []
        for line_num, line in enumerate(content.split('\n'), 1):
            line = line.strip()
            
            # Skip empty lines and comments
            if not line or line.startswith('#'):
                continue
            
            try:
                obj = json.loads(line)
                objects.append(obj)
            except json.JSONDecodeError as e:
                logger.warning(f"Skipping invalid JSON at line {line_num}: {line[:50]}... Error: {e}")
                continue
        
        logger.info(f"Parsed {len(objects)} objects from JSONL")
        return objects
    
    def extract_metadata(self, objects: List[Dict]) -> Dict:
        """
        Extract project metadata from configuration.
        
        Looks for the first object with 'comment' and 'project_name' fields.
        
        Args:
            objects: List of configuration objects
            
        Returns:
            Dictionary with project_name and page_size
        """
        for obj in objects:
            if 'comment' in obj and 'project_name' in obj:
                return {
                    'project_name': obj.get('project_name', 'Imported Config'),
                    'page_size': obj.get('page_size', 'large_portrait'),
                }
        
        # Default metadata if not found
        return {
            'project_name': 'Imported Config',
            'page_size': 'large_portrait'
        }
    
    def merge_configurations(
        self, 
        existing: List[Dict], 
        imported: List[Dict]
    ) -> Tuple[List[Dict], Dict[int, int]]:
        """
        Merge imported configuration with existing, avoiding ID conflicts.
        
        Args:
            existing: Current configuration objects
            imported: Imported configuration objects
            
        Returns:
            Tuple of (merged_objects, id_mapping)
            - merged_objects: Combined list with remapped IDs
            - id_mapping: Dict mapping old IDs to new IDs
        """
        # Get max ID from existing objects
        max_id = 0
        for obj in existing:
            obj_id = obj.get('id', 0)
            if isinstance(obj_id, int) and obj_id > max_id:
                max_id = obj_id
        
        # Remap imported object IDs to avoid conflicts
        id_mapping = {}
        remapped_imported = []
        
        for obj in imported:
            # Skip metadata/comment objects
            if 'comment' in obj:
                continue
            
            obj_copy = obj.copy()
            old_id = obj.get('id')
            
            if old_id is not None:
                max_id += 1
                id_mapping[old_id] = max_id
                obj_copy['id'] = max_id
            
            remapped_imported.append(obj_copy)
        
        # Combine existing and remapped imported
        merged = existing + remapped_imported
        
        logger.info(f"Merged {len(existing)} existing + {len(remapped_imported)} imported = {len(merged)} total objects")
        logger.info(f"ID mapping: {id_mapping}")
        
        return merged, id_mapping
    
    def calculate_stats(self, objects: List[Dict]) -> Dict:
        """
        Calculate statistics about a configuration.
        
        Args:
            objects: List of configuration objects
            
        Returns:
            Dictionary with pages, objects, and entities counts
        """
        pages = sum(1 for obj in objects if obj.get('obj') == 'page')
        total_objects = len(objects)
        
        # Count unique entities
        entities = set()
        for obj in objects:
            entity_id = obj.get('entity_id')
            if entity_id:
                entities.add(entity_id)
        
        return {
            'pages': pages,
            'objects': total_objects - pages,  # Exclude pages from object count
            'entities': len(entities)
        }
