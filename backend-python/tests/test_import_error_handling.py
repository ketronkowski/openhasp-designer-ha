"""Additional tests for Phase 3 error handling and edge cases."""
import pytest
from app.services.import_service import ConfigImportService
from pathlib import Path
import json


@pytest.fixture
def import_service():
    """Create import service instance."""
    return ConfigImportService()


class TestErrorHandling:
    """Tests for error handling in import service."""
    
    def test_parse_jsonl_with_missing_file(self, import_service):
        """Test handling of missing JSONL file."""
        result = import_service.import_from_ha_config("nonexistent.jsonl")
        assert result is None
    
    def test_parse_jsonl_with_empty_content(self, import_service):
        """Test parsing empty JSONL content."""
        objects = import_service.parse_jsonl("")
        assert objects == []
    
    def test_parse_jsonl_with_only_whitespace(self, import_service):
        """Test parsing JSONL with only whitespace."""
        objects = import_service.parse_jsonl("   \n\n   \n")
        assert objects == []
    
    def test_parse_jsonl_with_all_invalid_lines(self, import_service):
        """Test parsing JSONL where all lines are invalid."""
        content = "{invalid json\n{also invalid\n{still invalid"
        objects = import_service.parse_jsonl(content)
        assert objects == []
    
    def test_parse_jsonl_with_mixed_valid_invalid(self, import_service):
        """Test parsing JSONL with mix of valid and invalid lines."""
        content = '''{"valid": 1}
{invalid json}
{"valid": 2}
{also invalid
{"valid": 3}'''
        objects = import_service.parse_jsonl(content)
        assert len(objects) == 3
        assert objects[0]["valid"] == 1
        assert objects[1]["valid"] == 2
        assert objects[2]["valid"] == 3
    
    def test_extract_metadata_with_missing_fields(self, import_service):
        """Test metadata extraction when fields are missing."""
        objects = [
            {"page": 0, "id": 1, "obj": "btn"}
        ]
        metadata = import_service.extract_metadata(objects)
        assert "project_name" in metadata
        assert "page_size" in metadata
        # Should have defaults
        assert metadata["project_name"] == "Imported Config"
        assert metadata["page_size"] == "large_portrait"
    
    def test_extract_metadata_with_partial_fields(self, import_service):
        """Test metadata extraction with only some fields present."""
        objects = [
            {"comment": "Test Project"},
            {"page": 0, "id": 1, "obj": "btn"}
        ]
        metadata = import_service.extract_metadata(objects)
        # Should extract project name from comment or use default
        assert metadata["project_name"] == "Imported Config"
    
    def test_merge_with_empty_existing(self, import_service):
        """Test merging when existing config is empty."""
        existing = []
        imported = [
            {"page": 0, "id": 1, "obj": "btn"}
        ]
        merged, id_map = import_service.merge_configurations(existing, imported)
        assert len(merged) == 1
        assert merged[0]["id"] == 1
        assert id_map == {1: 1}
    
    def test_merge_with_empty_imported(self, import_service):
        """Test merging when imported config is empty."""
        existing = [
            {"page": 0, "id": 1, "obj": "btn"}
        ]
        imported = []
        merged, id_map = import_service.merge_configurations(existing, imported)
        assert len(merged) == 1
        assert merged[0]["id"] == 1
        assert id_map == {}
    
    def test_merge_with_both_empty(self, import_service):
        """Test merging when both configs are empty."""
        merged, id_map = import_service.merge_configurations([], [])
        assert merged == []
        assert id_map == {}
    
    def test_calculate_stats_with_empty_config(self, import_service):
        """Test stats calculation with empty config."""
        stats = import_service.calculate_stats([])
        assert stats["pages"] == 0
        assert stats["objects"] == 0
        assert stats["entities"] == 0
    
    def test_calculate_stats_with_no_entities(self, import_service):
        """Test stats calculation when no entities are present."""
        objects = [
            {"page": 0, "id": 0, "obj": "page"},
            {"page": 0, "id": 1, "obj": "label", "text": "Static Text"}
        ]
        stats = import_service.calculate_stats(objects)
        assert stats["pages"] == 1
        assert stats["objects"] == 1
        assert stats["entities"] == 0
    
    def test_calculate_stats_with_duplicate_entities(self, import_service):
        """Test stats calculation with duplicate entity references."""
        objects = [
            {"page": 0, "id": 1, "obj": "btn", "entity_id": "light.living_room"},
            {"page": 0, "id": 2, "obj": "btn", "entity_id": "light.living_room"},
            {"page": 0, "id": 3, "obj": "btn", "entity_id": "light.bedroom"}
        ]
        stats = import_service.calculate_stats(objects)
        assert stats["objects"] == 3
        assert stats["entities"] == 2  # Only unique entities
    
    def test_parse_jsonl_with_unicode_content(self, import_service):
        """Test parsing JSONL with unicode characters."""
        content = '{"text": "Hello 世界 🌍", "obj": "label"}'
        objects = import_service.parse_jsonl(content)
        assert len(objects) == 1
        assert objects[0]["text"] == "Hello 世界 🌍"
    
    def test_parse_jsonl_with_very_long_lines(self, import_service):
        """Test parsing JSONL with very long lines."""
        long_text = "A" * 10000
        content = f'{{"text": "{long_text}", "obj": "label"}}'
        objects = import_service.parse_jsonl(content)
        assert len(objects) == 1
        assert len(objects[0]["text"]) == 10000
    
    def test_merge_preserves_object_properties(self, import_service):
        """Test that merge preserves all object properties."""
        existing = [
            {"page": 0, "id": 1, "obj": "btn", "x": 10, "y": 20, "w": 100, "h": 50}
        ]
        imported = [
            {"page": 0, "id": 1, "obj": "label", "x": 30, "y": 40, "w": 200, "h": 30, "text": "Test"}
        ]
        merged, id_map = import_service.merge_configurations(existing, imported)
        
        # Check that imported object has new ID
        imported_obj = merged[1]
        assert imported_obj["id"] != 1
        assert imported_obj["x"] == 30
        assert imported_obj["y"] == 40
        assert imported_obj["text"] == "Test"
    
    def test_parse_jsonl_with_nested_objects(self, import_service):
        """Test parsing JSONL with nested object structures."""
        content = '{"obj": "btn", "options": {"key1": "value1", "key2": {"nested": true}}}'
        objects = import_service.parse_jsonl(content)
        assert len(objects) == 1
        assert objects[0]["options"]["key2"]["nested"] is True


class TestInvalidEntityReferences:
    """Tests for handling invalid entity references."""
    
    def test_calculate_stats_with_null_entity_id(self, import_service):
        """Test stats with null entity_id."""
        objects = [
            {"page": 0, "id": 1, "obj": "btn", "entity_id": None}
        ]
        stats = import_service.calculate_stats(objects)
        assert stats["entities"] == 0
    
    def test_calculate_stats_with_empty_entity_id(self, import_service):
        """Test stats with empty string entity_id."""
        objects = [
            {"page": 0, "id": 1, "obj": "btn", "entity_id": ""}
        ]
        stats = import_service.calculate_stats(objects)
        assert stats["entities"] == 0
    
    def test_calculate_stats_with_malformed_entity_id(self, import_service):
        """Test stats with malformed entity_id."""
        objects = [
            {"page": 0, "id": 1, "obj": "btn", "entity_id": "not.a.valid.entity.id.format"}
        ]
        stats = import_service.calculate_stats(objects)
        # Should still count it as an entity
        assert stats["entities"] == 1
