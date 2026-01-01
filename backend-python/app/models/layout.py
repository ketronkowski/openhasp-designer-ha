"""Layout storage models."""
from pydantic import BaseModel
from typing import List, Optional
from app.models.designer import DesignerObjectDto


class Page(BaseModel):
    """Page containing designer objects."""
    
    page_id: int
    objects: List[DesignerObjectDto]


class Layout(BaseModel):
    """Saved layout with metadata."""
    
    id: str
    name: str
    description: Optional[str] = None
    pages: List[Page]
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
