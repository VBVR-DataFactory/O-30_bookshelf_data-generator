"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                           BOOKSHELF INSERTION CONFIGURATION                   ║
║                                                                               ║
║  Configuration for Bookshelf Book Insertion Task.                            ║
║  Inherits common settings from core.GenerationConfig                          ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

from typing import Optional
from pydantic import Field
from core import GenerationConfig


class TaskConfig(GenerationConfig):
    """
    Bookshelf Insertion task configuration.
    
    Task: Insert red books into gaps between blue books based on height clustering.
    
    Inherited from GenerationConfig:
        - num_samples: int          # Number of samples to generate
        - domain: str               # Task domain name
        - difficulty: Optional[str] # Difficulty level
        - random_seed: Optional[int] # For reproducibility
        - output_dir: Path          # Where to save outputs
        - image_size: tuple[int, int] # Image dimensions
    """
    
    # ══════════════════════════════════════════════════════════════════════════
    #  OVERRIDE DEFAULTS
    # ══════════════════════════════════════════════════════════════════════════
    
    domain: str = Field(default="bookshelf")
    image_size: tuple[int, int] = Field(default=(800, 400))
    
    # ══════════════════════════════════════════════════════════════════════════
    #  VIDEO SETTINGS
    # ══════════════════════════════════════════════════════════════════════════
    
    generate_videos: bool = Field(
        default=True,
        description="Whether to generate ground truth videos"
    )
    
    video_fps: int = Field(
        default=10,
        description="Video frame rate"
    )
    
    # ══════════════════════════════════════════════════════════════════════════
    #  TASK-SPECIFIC SETTINGS
    # ══════════════════════════════════════════════════════════════════════════
    
    num_blue_books: int = Field(
        default=10,
        description="Number of blue books (existing books on shelf)"
    )
    
    num_red_books: int = Field(
        default=3,
        description="Number of red books (books to insert)"
    )
    
    eps: Optional[float] = Field(
        default=None,
        description="Clustering threshold. If None, uses 0.05 * median(blue_heights)"
    )
    
    min_book_height: float = Field(
        default=50.0,
        description="Minimum book height"
    )
    
    max_book_height: float = Field(
        default=200.0,
        description="Maximum book height"
    )
