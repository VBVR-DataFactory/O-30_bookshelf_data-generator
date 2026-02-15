"""Pydantic schemas for task data."""

from typing import Optional, Any, List, Dict
from pydantic import BaseModel


class TaskPair(BaseModel):
    """A task pair with initial and final states."""
    task_id: str
    domain: str
    prompt: str
    first_image: Any  # PIL Image
    final_image: Optional[Any] = None  # PIL Image
    ground_truth_video: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None  # Task metadata for deduplication and tracking  # Path to video (optional)
    insertion_indices: Optional[Dict[int, int]] = None  # Red book index -> insertion position (0-based)
    
    class Config:
        arbitrary_types_allowed = True
