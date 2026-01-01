"""Tests for import service."""
import pytest
from app.services.import_service import ConfigImportService


@pytest.fixture
def import_service():
    """Create import service instance."""
    return ConfigImportService()


class TestParseJSONL:
    """Tests for JSONL parsing."""
    
    def test_parse_valid_jsonl(self, import_service):
        """Test parsing valid JSONL content."""
        jsonl = '''{"id": 1, "obj": "page"}
{"id": 2, "obj": "btn", "text": "Button"}
{"id": 3, "obj": "label", "text": "Label"}'''
        
        objects = import_service.parse_jsonl(jsonl)
        
        assert len(objects) == 3
        assert objects[0]['id'] == 1
        assert objects[1]['text'] == 'Button'
        assert objects[2]['obj'] == 'label'
    
    def test_parse_with_empty_lines(self, import_service):
        """Test parsing JSONL with empty lines."""
        jsonl = '''{"id": 1, "obj": "page"}

{"id": 2, "obj": "btn"}

'''
        
        objects = import_service.parse_jsonl(jsonl)
        
        assert len(objects) == 2
    
    def test_parse_with_comments(self, import_service):
        """Test parsing JSONL with comment lines."""
        jsonl = '''# This is a comment
{"id": 1, "obj": "page"}
# Another comment
{"id": 2, "obj": "btn"}'''
        
        objects = import_service.parse_jsonl(jsonl)
        
        assert len(objects) == 2
    
    def test_parse_malformed_jsonl(self, import_service):
        """Test parsing JSONL with invalid JSON lines."""
        jsonl = '''{"id": 1, "obj": "page"}
{invalid json}
{"id": 2, "obj": "btn"}'''
        
        objects = import_service.parse_jsonl(jsonl)
        
        # Should skip invalid line and continue
        assert len(objects) == 2
        assert objects[0]['id'] == 1
        assert objects[1]['id'] == 2
    
    def test_parse_empty_content(self, import_service):
        """Test parsing empty JSONL content."""
        objects = import_service.parse_jsonl('')
        
        assert len(objects) == 0


class TestExtractMetadata:
    """Tests for metadata extraction."""
    
    def test_extract_metadata_present(self, import_service):
        """Test extracting metadata when present."""
        objects = [
            {'comment': '---- Config ----', 'project_name': 'My Project', 'page_size': 'large_landscape'},
            {'id': 1, 'obj': 'page'}
        ]
        
        metadata = import_service.extract_metadata(objects)
        
        assert metadata['project_name'] == 'My Project'
        assert metadata['page_size'] == 'large_landscape'
    
    def test_extract_metadata_missing(self, import_service):
        """Test extracting metadata when not present."""
        objects = [
            {'id': 1, 'obj': 'page'},
            {'id': 2, 'obj': 'btn'}
        ]
        
        metadata = import_service.extract_metadata(objects)
        
        assert metadata['project_name'] == 'Imported Config'
        assert metadata['page_size'] == 'large_portrait'
    
    def test_extract_metadata_partial(self, import_service):
        """Test extracting metadata with partial data."""
        objects = [
            {'comment': '---- Config ----', 'project_name': 'Test'},
            {'id': 1, 'obj': 'page'}
        ]
        
        metadata = import_service.extract_metadata(objects)
        
        assert metadata['project_name'] == 'Test'
        assert metadata['page_size'] == 'large_portrait'  # Default


class TestMergeConfigurations:
    """Tests for configuration merging."""
    
    def test_merge_empty_existing(self, import_service):
        """Test merging with empty existing configuration."""
        existing = []
        imported = [
            {'id': 1, 'obj': 'page'},
            {'id': 2, 'obj': 'btn'}
        ]
        
        merged, id_map = import_service.merge_configurations(existing, imported)
        
        assert len(merged) == 2
        assert merged[0]['id'] == 1
        assert merged[1]['id'] == 2
        assert id_map == {1: 1, 2: 2}
    
    def test_merge_with_id_conflicts(self, import_service):
        """Test merging with ID conflicts."""
        existing = [
            {'id': 1, 'obj': 'page'},
            {'id': 2, 'obj': 'btn'}
        ]
        imported = [
            {'id': 1, 'obj': 'label'},  # Conflicts with existing
            {'id': 2, 'obj': 'switch'}  # Conflicts with existing
        ]
        
        merged, id_map = import_service.merge_configurations(existing, imported)
        
        assert len(merged) == 4
        # Existing objects unchanged
        assert merged[0]['id'] == 1
        assert merged[1]['id'] == 2
        # Imported objects remapped
        assert merged[2]['id'] == 3
        assert merged[3]['id'] == 4
        assert id_map == {1: 3, 2: 4}
    
    def test_merge_skip_comments(self, import_service):
        """Test that comment objects are skipped during merge."""
        existing = [{'id': 1, 'obj': 'page'}]
        imported = [
            {'comment': '---- Config ----', 'project_name': 'Test'},
            {'id': 2, 'obj': 'btn'}
        ]
        
        merged, id_map = import_service.merge_configurations(existing, imported)
        
        # Comment should be skipped
        assert len(merged) == 2
        assert merged[1]['id'] == 2
    
    def test_merge_preserves_properties(self, import_service):
        """Test that object properties are preserved during merge."""
        existing = []
        imported = [
            {'id': 1, 'obj': 'btn', 'text': 'Click Me', 'x': 10, 'y': 20}
        ]
        
        merged, id_map = import_service.merge_configurations(existing, imported)
        
        assert merged[0]['text'] == 'Click Me'
        assert merged[0]['x'] == 10
        assert merged[0]['y'] == 20


class TestCalculateStats:
    """Tests for statistics calculation."""
    
    def test_calculate_stats_basic(self, import_service):
        """Test calculating stats for basic configuration."""
        objects = [
            {'id': 0, 'obj': 'page'},
            {'id': 1, 'obj': 'btn'},
            {'id': 2, 'obj': 'label'},
            {'id': 3, 'obj': 'btn'}
        ]
        
        stats = import_service.calculate_stats(objects)
        
        assert stats['pages'] == 1
        assert stats['objects'] == 3
        assert stats['entities'] == 0
    
    def test_calculate_stats_with_entities(self, import_service):
        """Test calculating stats with entities."""
        objects = [
            {'id': 0, 'obj': 'page'},
            {'id': 1, 'obj': 'btn', 'entity_id': 'light.living_room'},
            {'id': 2, 'obj': 'btn', 'entity_id': 'light.bedroom'},
            {'id': 3, 'obj': 'btn', 'entity_id': 'light.living_room'}  # Duplicate
        ]
        
        stats = import_service.calculate_stats(objects)
        
        assert stats['pages'] == 1
        assert stats['objects'] == 3
        assert stats['entities'] == 2  # Unique entities
    
    def test_calculate_stats_multiple_pages(self, import_service):
        """Test calculating stats with multiple pages."""
        objects = [
            {'id': 0, 'obj': 'page'},
            {'id': 1, 'obj': 'btn'},
            {'id': 0, 'obj': 'page'},
            {'id': 2, 'obj': 'label'}
        ]
        
        stats = import_service.calculate_stats(objects)
        
        assert stats['pages'] == 2
        assert stats['objects'] == 2
    
    def test_calculate_stats_empty(self, import_service):
        """Test calculating stats for empty configuration."""
        stats = import_service.calculate_stats([])
        
        assert stats['pages'] == 0
        assert stats['objects'] == 0
        assert stats['entities'] == 0
