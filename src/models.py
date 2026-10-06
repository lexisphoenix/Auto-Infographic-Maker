from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime

class ReviewAction(str, Enum):
    approve = "approve"
    schedule = "schedule"
    edit_caption = "edit_caption"
    regenerate = "regenerate"
    reject = "reject"

class InfographicItem(BaseModel):
    id: Optional[str] = None
    topic_fingerprint: str
    title: str
    summary: str
    key_facts: List[str]
    novelty_score: float
    viz_score: float
    priority_score: float
    design_brief: Dict[str, Any]
    status: str = "pending"
    image_url: Optional[str] = None
    html_path: Optional[str] = None
    caption: Optional[str] = None
    hashtags: Optional[List[str]] = None
    scheduled_for: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class ResearchResult(BaseModel):
    source_url: str
    title: str
    summary: str
    key_facts: List[str]
    viz_score: float
    novelty_score: float
    priority_score: Optional[float] = 0.0

class DesignBrief(BaseModel):
    topic: str
    headline: str
    story_angle: str
    key_facts: List[str]
    visual_metaphor: str
    canvas_format: str
    design_language: str
    should_animate: bool = False

class RenderRequest(BaseModel):
    html: str
    width: int
    height: int

class RenderResponse(BaseModel):
    image_url: Optional[str] = None
    image_path: Optional[str] = None
    error: Optional[str] = None
