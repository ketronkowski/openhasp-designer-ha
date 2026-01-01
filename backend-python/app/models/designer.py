"""Designer data models."""
from pydantic import BaseModel, Field
from typing import Optional


class DesignerObjectDto(BaseModel):
    """Designer object representation from frontend."""
    
    id: int
    type: str
    x: int
    y: int
    width: int
    height: int
    text: Optional[str] = None
    entity_id: Optional[str] = Field(None, alias="entityId")
    page: int = 1
    color: Optional[str] = None
    background_color: Optional[str] = Field(None, alias="backgroundColor")
    font_size: Optional[int] = Field(None, alias="fontSize")
    options: Optional[str] = None
    min: Optional[int] = None
    max: Optional[int] = None
    
    class Config:
        populate_by_name = True  # Allow both snake_case and camelCase
