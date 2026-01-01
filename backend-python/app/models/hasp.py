"""HASP object models for JSONL output."""
from pydantic import BaseModel
from typing import Optional


class HaspObject(BaseModel):
    """Base HASP object."""
    
    page: int
    id: int
    obj: str
    x: Optional[int] = None
    y: Optional[int] = None
    w: Optional[int] = None
    h: Optional[int] = None
    text: Optional[str] = None
    entity: Optional[str] = None
    action: Optional[str] = None
    color: Optional[str] = None
    bg_color: Optional[str] = None
    font_size: Optional[int] = None
    vis: Optional[bool] = None
    enabled: Optional[bool] = None
    
    class Config:
        # Exclude None values when serializing to JSON
        exclude_none = True


class HaspButton(HaspObject):
    """HASP button object."""
    
    def __init__(self, page: int, id: int, x: int, y: int, w: int, h: int, 
                 text: str, entity: Optional[str] = None, **kwargs):
        super().__init__(
            page=page, id=id, obj="btn", x=x, y=y, w=w, h=h,
            text=text, entity=entity, **kwargs
        )


class HaspLabel(HaspObject):
    """HASP label object."""
    
    def __init__(self, page: int, id: int, x: int, y: int, text: str, **kwargs):
        super().__init__(
            page=page, id=id, obj="label", x=x, y=y, text=text, **kwargs
        )


class HaspSlider(HaspObject):
    """HASP slider object."""
    
    min: Optional[int] = 0
    max: Optional[int] = 100
    val: Optional[int] = 0
    
    def __init__(self, page: int, id: int, x: int, y: int, w: int, h: int,
                 min: int = 0, max: int = 100, val: int = 0,
                 entity: Optional[str] = None, **kwargs):
        super().__init__(
            page=page, id=id, obj="slider", x=x, y=y, w=w, h=h,
            entity=entity, **kwargs
        )
        self.min = min
        self.max = max
        self.val = val


class HaspCheckbox(HaspObject):
    """HASP checkbox object."""
    
    value: Optional[bool] = False
    
    def __init__(self, page: int, id: int, x: int, y: int, text: str,
                 value: bool = False, entity: Optional[str] = None, **kwargs):
        super().__init__(
            page=page, id=id, obj="checkbox", x=x, y=y, text=text,
            entity=entity, **kwargs
        )
        self.value = value


class HaspSwitch(HaspObject):
    """HASP switch object."""
    
    value: Optional[bool] = False
    
    def __init__(self, page: int, id: int, x: int, y: int, w: int, h: int,
                 value: bool = False, entity: Optional[str] = None, **kwargs):
        super().__init__(
            page=page, id=id, obj="sw", x=x, y=y, w=w, h=h,
            entity=entity, **kwargs
        )
        self.value = value


class HaspDropdown(HaspObject):
    """HASP dropdown object."""
    
    options: Optional[str] = ""
    
    def __init__(self, page: int, id: int, x: int, y: int, w: int, h: int,
                 options: str = "", entity: Optional[str] = None, **kwargs):
        super().__init__(
            page=page, id=id, obj="dropdown", x=x, y=y, w=w, h=h,
            entity=entity, **kwargs
        )
        self.options = options
