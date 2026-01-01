"""Model validation tests."""
import pytest
from pydantic import ValidationError
from app.models.designer import DesignerObjectDto
from app.models.hasp import HaspButton, HaspSlider
from app.models.layout import Layout, Page


def test_designer_object_dto_valid():
    """Test DesignerObjectDto with valid data."""
    obj = DesignerObjectDto(
        id=1,
        type="btn",
        x=10,
        y=20,
        width=100,
        height=50,
        page=1
    )
    assert obj.id == 1
    assert obj.type == "btn"
    assert obj.page == 1


def test_designer_object_dto_with_entity():
    """Test DesignerObjectDto with entity_id."""
    obj = DesignerObjectDto(
        id=1,
        type="btn",
        x=10,
        y=20,
        width=100,
        height=50,
        entity_id="light.living_room",
        page=1
    )
    assert obj.entity_id == "light.living_room"


def test_designer_object_dto_camel_case_alias():
    """Test DesignerObjectDto accepts camelCase from frontend."""
    obj = DesignerObjectDto(
        id=1,
        type="btn",
        x=10,
        y=20,
        width=100,
        height=50,
        entityId="light.test",  # camelCase
        backgroundColor="#ff0000",  # camelCase
        page=1
    )
    assert obj.entity_id == "light.test"
    assert obj.background_color == "#ff0000"


def test_hasp_button_creation():
    """Test HaspButton model creation."""
    btn = HaspButton(
        page=1,
        id=2,
        x=10,
        y=20,
        w=100,
        h=50,
        text="Test Button",
        entity="light.test"
    )
    assert btn.obj == "btn"
    assert btn.text == "Test Button"
    assert btn.entity == "light.test"


def test_hasp_slider_creation():
    """Test HaspSlider model creation."""
    slider = HaspSlider(
        page=1,
        id=3,
        x=10,
        y=80,
        w=200,
        h=30,
        min=0,
        max=100,
        val=50,
        entity="light.brightness"
    )
    assert slider.obj == "slider"
    assert slider.min == 0
    assert slider.max == 100
    assert slider.val == 50


def test_hasp_object_exclude_none():
    """Test that None values are excluded from serialization."""
    btn = HaspButton(
        page=1,
        id=2,
        x=10,
        y=20,
        w=100,
        h=50,
        text="Test"
    )
    data = btn.model_dump(exclude_none=True)
    assert "entity" not in data  # Should be excluded since it's None
    assert "text" in data


def test_layout_creation():
    """Test Layout model creation."""
    layout = Layout(
        id="test-layout",
        name="Test Layout",
        description="A test layout",
        pages=[]
    )
    assert layout.id == "test-layout"
    assert layout.name == "Test Layout"


def test_page_with_objects():
    """Test Page model with designer objects."""
    obj = DesignerObjectDto(
        id=1,
        type="btn",
        x=10,
        y=20,
        width=100,
        height=50,
        page=1
    )
    
    page = Page(page_id=1, objects=[obj])
    assert page.page_id == 1
    assert len(page.objects) == 1
    assert page.objects[0].id == 1
