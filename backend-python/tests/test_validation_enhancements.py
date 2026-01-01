"""Tests for Phase 4 validation enhancements."""
import pytest
from app.services.validation_service import ValidationService, ValidationOptions, ValidationWarning
from app.services.ha_service import HomeAssistantService
from app.services.device_service import DeviceService


@pytest.fixture
def validation_service():
    """Create validation service instance."""
    ha_service = HomeAssistantService()
    device_service = DeviceService()
    return ValidationService(ha_service, device_service)


class TestOverlapDetection:
    """Tests for overlap detection."""
    
    def test_no_overlaps(self, validation_service):
        """Test configuration with no overlapping objects."""
        config = [
            {'page': 0, 'id': 0, 'obj': 'page'},
            {'page': 0, 'id': 1, 'obj': 'btn', 'x': 0, 'y': 0, 'w': 100, 'h': 50},
            {'page': 0, 'id': 2, 'obj': 'btn', 'x': 110, 'y': 0, 'w': 100, 'h': 50},
        ]
        
        warnings = validation_service.detect_overlaps(config)
        
        assert len(warnings) == 0
    
    def test_complete_overlap(self, validation_service):
        """Test objects that completely overlap."""
        config = [
            {'page': 0, 'id': 1, 'obj': 'btn', 'x': 0, 'y': 0, 'w': 100, 'h': 50},
            {'page': 0, 'id': 2, 'obj': 'btn', 'x': 0, 'y': 0, 'w': 100, 'h': 50},
        ]
        
        warnings = validation_service.detect_overlaps(config)
        
        assert len(warnings) == 1
        assert warnings[0].type == 'overlap'
        assert '1' in warnings[0].message and '2' in warnings[0].message
    
    def test_partial_overlap(self, validation_service):
        """Test objects that partially overlap."""
        config = [
            {'page': 0, 'id': 1, 'obj': 'btn', 'x': 0, 'y': 0, 'w': 100, 'h': 50},
            {'page': 0, 'id': 2, 'obj': 'btn', 'x': 50, 'y': 25, 'w': 100, 'h': 50},
        ]
        
        warnings = validation_service.detect_overlaps(config)
        
        assert len(warnings) == 1
        assert warnings[0].type == 'overlap'
    
    def test_edge_touching_not_overlap(self, validation_service):
        """Test objects touching at edges (not overlapping)."""
        config = [
            {'page': 0, 'id': 1, 'obj': 'btn', 'x': 0, 'y': 0, 'w': 100, 'h': 50},
            {'page': 0, 'id': 2, 'obj': 'btn', 'x': 100, 'y': 0, 'w': 100, 'h': 50},
        ]
        
        warnings = validation_service.detect_overlaps(config)
        
        assert len(warnings) == 0
    
    def test_different_pages_no_overlap(self, validation_service):
        """Test objects on different pages don't trigger overlap."""
        config = [
            {'page': 0, 'id': 1, 'obj': 'btn', 'x': 0, 'y': 0, 'w': 100, 'h': 50},
            {'page': 1, 'id': 2, 'obj': 'btn', 'x': 0, 'y': 0, 'w': 100, 'h': 50},
        ]
        
        warnings = validation_service.detect_overlaps(config)
        
        assert len(warnings) == 0
    
    def test_multiple_overlaps(self, validation_service):
        """Test multiple overlapping objects."""
        config = [
            {'page': 0, 'id': 1, 'obj': 'btn', 'x': 0, 'y': 0, 'w': 100, 'h': 50},
            {'page': 0, 'id': 2, 'obj': 'btn', 'x': 50, 'y': 25, 'w': 100, 'h': 50},
            {'page': 0, 'id': 3, 'obj': 'btn', 'x': 75, 'y': 40, 'w': 100, 'h': 50},
        ]
        
        warnings = validation_service.detect_overlaps(config)
        
        # Should detect 3 overlaps: 1-2, 1-3, 2-3
        assert len(warnings) == 3
    
    def test_skip_page_objects(self, validation_service):
        """Test that page objects are skipped."""
        config = [
            {'page': 0, 'id': 0, 'obj': 'page', 'x': 0, 'y': 0, 'w': 480, 'h': 320},
            {'page': 0, 'id': 1, 'obj': 'btn', 'x': 0, 'y': 0, 'w': 100, 'h': 50},
        ]
        
        warnings = validation_service.detect_overlaps(config)
        
        assert len(warnings) == 0


class TestRectangleOverlap:
    """Tests for rectangle overlap algorithm."""
    
    def test_rectangles_overlap_helper(self, validation_service):
        """Test the _rectangles_overlap helper method."""
        # Overlapping
        obj1 = {'x': 0, 'y': 0, 'w': 100, 'h': 50}
        obj2 = {'x': 50, 'y': 25, 'w': 100, 'h': 50}
        assert validation_service._rectangles_overlap(obj1, obj2) == True
        
        # Not overlapping (separated horizontally)
        obj1 = {'x': 0, 'y': 0, 'w': 100, 'h': 50}
        obj2 = {'x': 110, 'y': 0, 'w': 100, 'h': 50}
        assert validation_service._rectangles_overlap(obj1, obj2) == False
        
        # Not overlapping (separated vertically)
        obj1 = {'x': 0, 'y': 0, 'w': 100, 'h': 50}
        obj2 = {'x': 0, 'y': 60, 'w': 100, 'h': 50}
        assert validation_service._rectangles_overlap(obj1, obj2) == False
        
        # Edge touching (not overlapping)
        obj1 = {'x': 0, 'y': 0, 'w': 100, 'h': 50}
        obj2 = {'x': 100, 'y': 0, 'w': 100, 'h': 50}
        assert validation_service._rectangles_overlap(obj1, obj2) == False
        
        # One inside another
        obj1 = {'x': 0, 'y': 0, 'w': 200, 'h': 200}
        obj2 = {'x': 50, 'y': 50, 'w': 50, 'h': 50}
        assert validation_service._rectangles_overlap(obj1, obj2) == True
