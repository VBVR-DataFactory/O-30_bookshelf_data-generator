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
    image_size: tuple[int, int] = Field(default=(1024, 1024))
    
    # ══════════════════════════════════════════════════════════════════════════
    #  VIDEO SETTINGS
    # ══════════════════════════════════════════════════════════════════════════
    
    generate_videos: bool = Field(
        default=True,
        description="Whether to generate ground truth videos"
    )
    
    video_fps: int = Field(
        default=16,
        description="Video frame rate"
    )
    
    # ══════════════════════════════════════════════════════════════════════════
    #  TASK-SPECIFIC SETTINGS
    # ══════════════════════════════════════════════════════════════════════════
    
    num_blue_books: int = Field(
        default=16,
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
    
    # ══════════════════════════════════════════════════════════════════════════
    #  COLOR RANDOMIZATION SETTINGS (for scalable 10K+ generation)
    # ══════════════════════════════════════════════════════════════════════════
    
    randomize_colors: bool = Field(
        default=True,
        description="Whether to randomize book colors for diversity"
    )
    
    min_color_distance: float = Field(
        default=120.0,
        description="Minimum HSV distance between existing/new book colors (0-360)"
    )
    
    use_color_names: bool = Field(
        default=True,
        description="Whether to use descriptive color names in prompts"
    )
    
    randomize_book_properties: bool = Field(
        default=True,
        description="Whether to randomize additional visual properties (width, patterns)"
    )