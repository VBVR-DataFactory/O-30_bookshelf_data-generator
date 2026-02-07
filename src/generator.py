"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                           YOUR TASK GENERATOR                                 ║
║                                                                               ║
║  CUSTOMIZE THIS FILE to implement your data generation logic.                 ║
║  Replace the example implementation with your own task.                       ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import random
import numpy as np
import tempfile
import colorsys
from pathlib import Path
from typing import List, Tuple, Dict
from PIL import Image, ImageDraw

from core import BaseGenerator, TaskPair, ImageRenderer
from core.video_utils import VideoGenerator
from .config import TaskConfig
from .prompts import get_prompt


class TaskGenerator(BaseGenerator):
    """
    Bookshelf insertion task generator.
    
    Generates tasks where red books need to be inserted into a shelf of blue books
    based on height clustering and matching.
    """
    
    def __init__(self, config: TaskConfig):
        super().__init__(config)
        self.renderer = ImageRenderer(image_size=config.image_size)
        
        # Initialize video generator if enabled
        self.video_generator = None
        if config.generate_videos and VideoGenerator.is_available():
            self.video_generator = VideoGenerator(fps=config.video_fps, output_format="mp4")
    
    # ══════════════════════════════════════════════════════════════════════════
    #  SCALABLE COLOR GENERATION SYSTEM
    # ══════════════════════════════════════════════════════════════════════════
    
    def _generate_color_scheme(self) -> Dict[str, Tuple[Tuple[int, int, int], str]]:
        """
        Generate procedural color scheme for existing and new books.
        
        For existing (left) books: any color from full spectrum
        For new (right) books: only common, simple color names
        
        Returns:
            Dict with 'existing' and 'new' keys, each containing (rgb_tuple, color_name)
        """
        if not self.config.randomize_colors:
            # Default colors
            return {
                'existing': ((70, 130, 180), "blue"),  # Steel blue
                'new': ((220, 20, 60), "red")  # Crimson red
            }
        
        # Common colors for new books (right side) - only simple, well-known color names
        COMMON_COLORS = [
            (0, "red"),       # Red
            (30, "orange"),   # Orange
            (60, "yellow"),   # Yellow
            (120, "green"),   # Green
            (210, "blue"),    # Blue
            (270, "purple"),  # Purple
            (330, "pink")     # Pink
        ]
        
        # Choose a random common color for new books
        new_hue, new_color_name = random.choice(COMMON_COLORS)
        
        # Generate existing book color (can be any hue, but must be different from new book)
        min_distance = self.config.min_color_distance
        existing_hue = new_hue
        attempts = 0
        while abs(existing_hue - new_hue) < min_distance and attempts < 10:
            existing_hue = random.uniform(0, 360)
            if abs(existing_hue - new_hue) > 360 - min_distance:
                break  # Colors are far apart (wrapping around 360)
            attempts += 1
        
        # Generate colors with good saturation and brightness for visibility
        existing_rgb = self._hsv_to_rgb(
            existing_hue / 360.0,
            random.uniform(0.6, 0.9),  # High saturation
            random.uniform(0.4, 0.8)   # Medium to high brightness
        )
        
        # New book color: use exact hue from common colors with slight variation
        new_rgb = self._hsv_to_rgb(
            new_hue / 360.0,
            random.uniform(0.7, 0.9),  # High saturation for vivid colors
            random.uniform(0.5, 0.8)   # Medium to high brightness
        )
        
        return {
            'existing': (existing_rgb, ""),  # No color name for existing books
            'new': (new_rgb, new_color_name)  # Simple color name for new books
        }
    
    def _hsv_to_rgb(self, h: float, s: float, v: float) -> Tuple[int, int, int]:
        """Convert HSV to RGB color space."""
        rgb = colorsys.hsv_to_rgb(h, s, v)
        return tuple(int(c * 255) for c in rgb)
    
    def _get_color_name(self, hue: float) -> str:
        """
        Map hue value (0-360) to descriptive color name.
        Covers entire color wheel with smooth transitions.
        """
        # Normalize hue to 0-360
        hue = hue % 360
        
        color_map = [
            (0, ["red", "crimson", "scarlet"]),
            (30, ["orange", "amber", "coral"]),
            (60, ["yellow", "gold", "lemon"]),
            (90, ["lime", "chartreuse", "spring"]),
            (120, ["green", "emerald", "forest"]),
            (150, ["teal", "mint", "seafoam"]),
            (180, ["cyan", "turquoise", "aqua"]),
            (210, ["blue", "azure", "sky"]),
            (240, ["indigo", "navy", "royal"]),
            (270, ["purple", "violet", "plum"]),
            (300, ["magenta", "fuchsia", "pink"]),
            (330, ["rose", "burgundy", "maroon"]),
            (360, ["red", "crimson", "scarlet"])  # Wrap around
        ]
        
        # Find the closest color range
        for i, (threshold, names) in enumerate(color_map[:-1]):
            next_threshold = color_map[i + 1][0]
            if threshold <= hue < next_threshold:
                return random.choice(names)
        
        # Fallback to red if something goes wrong
        return random.choice(color_map[0][1])
    
    def _generate_additional_properties(self) -> Dict[str, any]:
        """Generate additional randomized visual properties."""
        if not self.config.randomize_book_properties:
            return {
                'book_width': 26,  # Scaled from 30 for 1024x1024 (30 * 1024/800 ≈ 38)
                'shelf_color': (139, 69, 19)  # Brown
            }
        
        return {
            'book_width': random.randint(24, 34),  # Scaled from 25-40 for 1024x1024
            'shelf_color': self._hsv_to_rgb(
                random.uniform(20, 40) / 360.0,  # Brown/wood hues
                random.uniform(0.3, 0.7),
                random.uniform(0.2, 0.5)
            )
        }
    
    def generate_task_pair(self, task_id: str) -> TaskPair:
        """Generate one task pair."""
        
        # Generate procedural color scheme and visual properties
        color_scheme = self._generate_color_scheme()
        visual_props = self._generate_additional_properties()
        
        # Generate book heights
        blue_heights = self._generate_blue_heights()
        
        # Randomly determine number of red books (gaps) for variety
        # Number of gaps must equal number of red books
        num_red = random.randint(2, 5)  # Vary between 2-5 red books
        
        # Calculate slot positions and adjacent blue books
        slot_info = self._calculate_slot_info(blue_heights, num_red)
        
        # Generate red book heights from adjacent blue books, then assign to slots
        red_heights, insertion_indices = self._generate_red_heights_and_assign(
            blue_heights, slot_info, num_red
        )
        
        # Generate random queue order for red books (consistent across all renders)
        red_queue_order = list(range(len(red_heights)))
        random.shuffle(red_queue_order)
        
        # Render images with dynamic colors
        first_image = self._render_initial_state(blue_heights, red_heights, insertion_indices, red_queue_order, color_scheme, visual_props)
        final_image = self._render_final_state(blue_heights, red_heights, insertion_indices, color_scheme, visual_props)
        
        # Generate video if enabled
        video_path = None
        if self.config.generate_videos and self.video_generator:
            video_path = self._generate_video(
                blue_heights, red_heights, insertion_indices, task_id, red_queue_order, color_scheme, visual_props
            )
        
        # Get prompt with color substitution
        prompt = get_prompt("default", color_scheme)
        
        return TaskPair(
            task_id=task_id,
            domain=self.config.domain,
            prompt=prompt,
            first_image=first_image,
            final_image=final_image,
            ground_truth_video=video_path,
            insertion_indices=insertion_indices
        )
    
    # ══════════════════════════════════════════════════════════════════════════
    #  DATA GENERATION
    # ══════════════════════════════════════════════════════════════════════════
    
    def _generate_blue_heights(self) -> List[float]:
        """Generate blue book heights with clustering structure."""
        num_books = self.config.num_blue_books
        min_h = self.config.min_book_height
        max_h = self.config.max_book_height
        
        # Generate heights in groups to create natural clusters
        heights = []
        num_groups = random.randint(2, 4)  # 2-4 groups
        books_per_group = num_books // num_groups
        remainder = num_books % num_groups
        
        for group_idx in range(num_groups):
            group_size = books_per_group + (1 if group_idx < remainder else 0)
            # Each group has a base height
            base_height = min_h + (max_h - min_h) * (group_idx + 1) / (num_groups + 1)
            # Add small variations within group
            for _ in range(group_size):
                variation = random.uniform(-0.1, 0.1) * (max_h - min_h)
                heights.append(base_height + variation)
        
        # Shuffle to create more realistic distribution
        random.shuffle(heights)
        
        # Sort to create clusters naturally
        heights.sort()
        
        return heights
    
    def _calculate_slot_info(self, blue_heights: List[float], num_red: int) -> List[Tuple[int, List[float]]]:
        """
        Calculate slot positions and their adjacent blue book heights.
        
        Args:
            blue_heights: List of blue book heights
            num_red: Number of red books (gaps) - must equal number of slots
        
        Returns:
            List of (slot_position, [adjacent_blue_heights]) tuples
        """
        num_blue = len(blue_heights)
        
        slot_info = []
        
        # Slots between blue books: positions 1, 2, ..., num_blue-1
        for i in range(1, num_blue):
            # Slot at position i is between blue[i-1] and blue[i]
            adjacent_heights = [blue_heights[i - 1], blue_heights[i]]
            slot_info.append((i, adjacent_heights))
        
        # If we need more slots, add slots at the ends
        if len(slot_info) < num_red:
            # Add slot before first blue book
            slot_info.insert(0, (0, [blue_heights[0]]))
            
            if len(slot_info) < num_red:
                # Add slot after last blue book
                slot_info.append((num_blue, [blue_heights[num_blue - 1]]))
        
        # Ensure we have exactly num_red slots
        if len(slot_info) > num_red:
            # Randomly select num_red slots for more diverse gap patterns
            # This creates varied distributions instead of uniform spacing
            selected_indices = sorted(random.sample(range(len(slot_info)), num_red))
            slot_info = [slot_info[i] for i in selected_indices]
        elif len(slot_info) < num_red:
            raise ValueError(f"Cannot create {num_red} slots with {num_blue} blue books")
        
        return slot_info
    
    def _generate_red_heights_and_assign(
        self,
        blue_heights: List[float],
        slot_info: List[Tuple[int, List[float]]],
        num_red: int
    ) -> Tuple[List[float], Dict[int, int]]:
        """
        Generate red book heights from adjacent blue books and assign to slots.
        
        Each red book height is chosen from the adjacent blue books of its assigned slot.
        Uses optimal assignment based on slot target heights, then selects closest
        adjacent blue book height for each assigned slot.
        
        Args:
            blue_heights: List of blue book heights
            slot_info: List of (slot_position, [adjacent_blue_heights]) tuples
            num_red: Number of red books (must equal len(slot_info))
        
        Returns:
            Tuple of (red_heights, insertion_indices)
        """
        
        # Extract slot positions and target heights (average of adjacent blue books)
        slot_positions = [pos for pos, _ in slot_info]
        slot_targets = []
        slot_adjacent_heights = []
        
        for pos, adjacent_heights in slot_info:
            if len(adjacent_heights) == 2:
                # Slot between two blue books
                target = (adjacent_heights[0] + adjacent_heights[1]) / 2.0
            else:
                # Slot at end (only one adjacent blue book)
                target = adjacent_heights[0]
            slot_targets.append(target)
            slot_adjacent_heights.append(adjacent_heights)
        
        # Generate initial red book heights from all adjacent blue books
        # These will be used for optimal assignment
        initial_red_heights = []
        for adjacent_heights in slot_adjacent_heights:
            # Randomly choose one height from adjacent blue books
            initial_red_heights.append(random.choice(adjacent_heights))
        
        # Optimal assignment: minimize sum of |red_height - slot_target|
        assignment = self._optimal_assignment(initial_red_heights, slot_targets, slot_positions)
        
        # Now generate final red book heights based on assigned slots
        # Each red book gets a height from its assigned slot's adjacent blue books
        red_heights = [0.0] * num_red
        slot_to_red = {}  # slot_pos -> red_idx
        
        # Build mapping: slot_pos -> red_idx
        for red_idx, slot_pos in assignment.items():
            slot_to_red[slot_pos] = red_idx
        
        # Generate red book heights from their assigned slot's adjacent blue books
        for slot_pos, adjacent_heights in zip(slot_positions, slot_adjacent_heights):
            if slot_pos in slot_to_red:
                red_idx = slot_to_red[slot_pos]
                # Choose the adjacent blue book height closest to slot target
                slot_idx = slot_positions.index(slot_pos)
                target = slot_targets[slot_idx]
                
                # Find closest adjacent height to target
                closest_height = min(adjacent_heights, key=lambda h: abs(h - target))
                red_heights[red_idx] = closest_height
        
        return red_heights, assignment
    
    # ══════════════════════════════════════════════════════════════════════════
    #  CLUSTERING LOGIC
    # ══════════════════════════════════════════════════════════════════════════
    
    def _cluster_blue_books(self, blue_heights: List[float]) -> List[Tuple[int, int]]:
        """
        Cluster blue books using adjacent difference rule.
        
        Returns:
            List of (start_idx, end_idx) tuples for each cluster (inclusive).
        """
        if len(blue_heights) == 0:
            return []
        
        # Calculate eps
        if self.config.eps is not None:
            eps = self.config.eps
        else:
            median_height = np.median(blue_heights)
            eps = 0.05 * median_height
        
        clusters = []
        cluster_start = 0
        
        for i in range(len(blue_heights) - 1):
            height_diff = abs(blue_heights[i + 1] - blue_heights[i])
            if height_diff > eps:
                # Start new cluster
                clusters.append((cluster_start, i))
                cluster_start = i + 1
        
        # Add final cluster
        clusters.append((cluster_start, len(blue_heights) - 1))
        
        return clusters
    
    def _calculate_cluster_means(self, blue_heights: List[float], 
                                 clusters: List[Tuple[int, int]]) -> List[float]:
        """Calculate representative height (mean) for each cluster."""
        means = []
        for start_idx, end_idx in clusters:
            cluster_heights = blue_heights[start_idx:end_idx + 1]
            mean_height = np.mean(cluster_heights)
            means.append(mean_height)
        return means
    
    # ══════════════════════════════════════════════════════════════════════════
    #  SLOT ASSIGNMENT (HEIGHT-BASED MATCHING)
    # ══════════════════════════════════════════════════════════════════════════
    
    def _calculate_slot_assignments(
        self,
        blue_heights: List[float],
        red_heights: List[float]
    ) -> Dict[int, int]:
        """
        Calculate slot assignments using height-based matching.
        
        Each slot is between two adjacent blue books. Slot target height is
        the average of the two adjacent blue book heights.
        
        Uses optimal assignment (Hungarian-like) to minimize total matching error.
        
        Returns:
            Dictionary mapping red book index -> insertion position (0-based)
        """
        num_red = len(red_heights)
        num_blue = len(blue_heights)
        
        # Calculate slot positions and target heights
        # Slots are between adjacent blue books: gap j between blue[i] and blue[i+1]
        # Gap j (0-indexed) is at position i+1 (insert after blue book i)
        
        # Generate slots between blue books (preferred)
        slot_positions = []
        slot_targets = []
        
        # Slots between blue books: positions 1, 2, ..., num_blue-1
        # (position i means between blue[i-1] and blue[i])
        for i in range(1, num_blue):
            slot_positions.append(i)
            target = (blue_heights[i - 1] + blue_heights[i]) / 2.0
            slot_targets.append(target)
        
        # If we need more slots, add slots at the ends
        # Position 0: before first blue book
        # Position num_blue: after last blue book
        if len(slot_positions) < num_red:
            # Add slot before first blue book
            slot_positions.insert(0, 0)
            slot_targets.insert(0, blue_heights[0])  # Use first blue book height as target
            
            if len(slot_positions) < num_red:
                # Add slot after last blue book
                slot_positions.append(num_blue)
                slot_targets.append(blue_heights[num_blue - 1])  # Use last blue book height as target
        
        # Ensure we have exactly num_red slots
        if len(slot_positions) > num_red:
            # Randomly select num_red slots for more diverse gap patterns
            # This creates varied distributions instead of uniform spacing
            selected_indices = sorted(random.sample(range(len(slot_positions)), num_red))
            slot_positions = [slot_positions[i] for i in selected_indices]
            slot_targets = [slot_targets[i] for i in selected_indices]
        elif len(slot_positions) < num_red:
            # This shouldn't happen with the logic above, but handle it
            raise ValueError(f"Cannot create {num_red} slots with {num_blue} blue books")
        
        # Optimal assignment: minimize sum of |red_height - slot_target|
        # Use Hungarian algorithm or brute force for small problems
        assignment = self._optimal_assignment(red_heights, slot_targets, slot_positions)
        
        return assignment
    
    def _optimal_assignment(
        self,
        red_heights: List[float],
        slot_targets: List[float],
        slot_positions: List[int]
    ) -> Dict[int, int]:
        """
        Find optimal one-to-one assignment of red books to slots.
        
        Minimizes: sum |red_heights[i] - slot_targets[assignment[i]]|
        
        Uses brute force for small problems, or a simple greedy with tie-breaking
        for larger problems.
        """
        num_red = len(red_heights)
        num_slots = len(slot_targets)
        
        assert num_red == num_slots, "Number of red books must equal number of slots"
        
        # For small problems (n <= 8), use brute force (try all permutations)
        if num_red <= 8:
            return self._brute_force_assignment(red_heights, slot_targets, slot_positions)
        else:
            # For larger problems, use a greedy approach with optimal matching
            # Sort red books by height (stable: preserve original order for ties)
            red_with_idx = [(i, h) for i, h in enumerate(red_heights)]
            red_with_idx.sort(key=lambda x: (x[1], x[0]))  # Sort by height, then by index
            
            # Sort slots by target height (stable: prefer left slots for ties)
            slot_with_pos = [(i, t, p) for i, (t, p) in enumerate(zip(slot_targets, slot_positions))]
            slot_with_pos.sort(key=lambda x: (x[1], -x[2]))  # Sort by target, then by position (descending for left preference)
            
            # Assign: smallest red to smallest slot, etc.
            assignment = {}
            for (red_idx, _), (slot_idx, _, slot_pos) in zip(red_with_idx, slot_with_pos):
                assignment[red_idx] = slot_pos
            
            return assignment
    
    def _brute_force_assignment(
        self,
        red_heights: List[float],
        slot_targets: List[float],
        slot_positions: List[int]
    ) -> Dict[int, int]:
        """Brute force: try all permutations to find optimal assignment."""
        from itertools import permutations
        
        num = len(red_heights)
        best_cost = float('inf')
        best_perm = None
        
        # Try all permutations of slot assignments
        for perm in permutations(range(num)):
            cost = sum(abs(red_heights[i] - slot_targets[perm[i]]) for i in range(num))
            if cost < best_cost:
                best_cost = cost
                best_perm = perm
        
        # Build assignment dictionary
        assignment = {}
        for red_idx in range(num):
            slot_idx = best_perm[red_idx]
            assignment[red_idx] = slot_positions[slot_idx]
        
        return assignment
    
    # ══════════════════════════════════════════════════════════════════════════
    #  RENDERING
    # ══════════════════════════════════════════════════════════════════════════
    
    def _calculate_layout_params(
        self,
        width: int,
        scale_factor: float,
        all_positions: List,
        num_red: int,
        book_width: int,
        spacing: int
    ) -> Tuple[int, int, int]:
        """
        Calculate layout parameters for centered shelf with red books queue on the right.
        
        Returns:
            (x_start, red_queue_x_start, red_spacing)
        """
        # Calculate required space for red books queue
        red_spacing = spacing  # Use same spacing for red books
        required_red_space = num_red * (book_width + red_spacing) - red_spacing  # Last book doesn't need spacing after
        right_margin = int(20 * scale_factor)  # Keep some margin from right edge
        red_queue_width = required_red_space + right_margin  # Total width needed for red books queue
        
        # Calculate shelf (blue books + gaps) total width
        num_blue_and_gaps = len(all_positions)
        shelf_width = num_blue_and_gaps * (book_width + spacing) - spacing  # Last item doesn't need spacing after
        
        # Calculate gap between shelf and red queue
        gap_between = int(30 * scale_factor)  # Gap between shelf and red books queue
        
        # Center the shelf in the remaining space (left side)
        # Available space for shelf area = width - red_queue_width
        available_for_shelf = width - red_queue_width
        x_start = (available_for_shelf - shelf_width) // 2  # Center shelf in available space
        
        # Red books queue starts after shelf + gap
        red_queue_x_start = x_start + shelf_width + gap_between
        
        return x_start, red_queue_x_start, red_spacing
    
    def _render_initial_state(self, blue_heights: List[float], 
                             red_heights: List[float],
                             insertion_indices: Dict[int, int],
                             red_queue_order: List[int],
                             color_scheme: Dict[str, Tuple[Tuple[int, int, int], str]],
                             visual_props: Dict[str, any]) -> Image.Image:
        """
        Render initial state: blue books on shelf with gaps, red books queued on the right.
        
        Blue books are arranged in final order with gaps at insertion positions.
        Red books are positioned on the right side of the shelf, on the same baseline,
        in random order (not sorted by height) to show intelligent placement.
        """
        img = self.renderer.create_blank_image(bg_color=(255, 255, 255))
        draw = ImageDraw.Draw(img)
        
        width, height = img.size
        # Scale parameters for 1024x1024 (from 800x400 base)
        scale_factor = width / 800.0  # Scale based on width
        shelf_y = height // 2  # Shelf position (baseline) - vertically centered
        shelf_height = int(10 * scale_factor)  # Shelf thickness
        
        # Extract colors and properties
        existing_color, _ = color_scheme['existing']
        new_color, _ = color_scheme['new']
        book_width = visual_props['book_width']
        shelf_color = visual_props['shelf_color']
        
        # Draw shelf (full width)
        draw.rectangle([0, shelf_y, width, shelf_y + shelf_height], fill=shelf_color)
        
        spacing = int(5 * scale_factor)  # Scaled spacing
        
        # Build the layout structure (blue books + gaps)
        # This structure remains constant - red books only fill gaps, don't change structure
        all_positions = self._build_layout_structure(blue_heights, red_heights, insertion_indices)
        num_red = len(red_heights)
        
        # Calculate layout parameters (centered shelf, red queue on right)
        x_start, red_queue_x_start, red_spacing = self._calculate_layout_params(
            width, scale_factor, all_positions, num_red, book_width, spacing
        )
        
        # Draw blue books and gaps on shelf
        for i, (pos_type, pos_height, red_idx) in enumerate(all_positions):
            x = x_start + i * (book_width + spacing)
            
            if pos_type == 'blue':
                # Draw existing book with dynamic color
                scaled_h = int(pos_height * 1.5)
                y_top = shelf_y - scaled_h
                draw.rectangle(
                    [x, y_top, x + book_width, shelf_y],
                    fill=existing_color,
                    outline=(0, 0, 0),
                    width=max(2, int(2 * scale_factor))  # Scaled outline width
                )
            # Gap: just leave blank space (no drawing, no border, no height indicator)
            # The gap is represented only by the horizontal spacing
        
        # Draw red books on the right side, queued on the baseline
        # Use random order to show that books intelligently choose their positions
        # Use provided random queue order (not sorted by height or insertion position)
        for i, red_idx in enumerate(red_queue_order):
            x = red_queue_x_start + i * (book_width + red_spacing)
            
            scaled_h = int(red_heights[red_idx] * 1.5)
            y_top = shelf_y - scaled_h  # On baseline, not floating
            
            # Draw red book (should always be within bounds now)
            draw.rectangle(
                [x, y_top, x + book_width, shelf_y],
                fill=new_color,
                outline=(0, 0, 0),
                width=max(2, int(2 * scale_factor))  # Scaled outline width
            )
        
        return img
    
    def _build_layout_structure(
        self,
        blue_heights: List[float],
        red_heights: List[float],
        insertion_indices: Dict[int, int]
    ) -> List[Tuple[str, float, int]]:
        """
        Build the layout structure (blue books + gaps) that remains constant.
        
        This structure is used in both initial and final states.
        Red books only fill existing gaps, they don't change the structure.
        
        Returns:
            List of (type, height, red_idx) where type is 'blue' or 'gap'
            red_idx is None for blue books, and the assigned red book index for gaps
        """
        # Sort red books by insertion position, then by height (same as initial state)
        red_insertions = sorted(
            insertion_indices.items(),
            key=lambda x: (x[1], red_heights[x[0]])  # First by position, then by height (ascending)
        )
        
        # Build layout: blue books + gaps at insertion positions
        all_positions = []  # List of (type, height, red_idx) where type is 'blue' or 'gap'
        blue_idx = 0
        gap_idx = 0
        
        for pos in range(len(blue_heights) + len(red_heights)):
            # Check if this position should be a gap (red book insertion point)
            if gap_idx < len(red_insertions) and red_insertions[gap_idx][1] == pos:
                red_idx = red_insertions[gap_idx][0]
                all_positions.append(('gap', red_heights[red_idx], red_idx))
                gap_idx += 1
            elif blue_idx < len(blue_heights):
                all_positions.append(('blue', blue_heights[blue_idx], None))
                blue_idx += 1
        
        return all_positions
    
    def _render_final_state(self, blue_heights: List[float], 
                           red_heights: List[float],
                           insertion_indices: Dict[int, int],
                           color_scheme: Dict[str, Tuple[Tuple[int, int, int], str]],
                           visual_props: Dict[str, any]) -> Image.Image:
        """
        Render final state: red books fill the gaps.
        
        Uses the same layout structure as initial state, just fills gaps with red books.
        Blue books remain in exactly the same positions.
        """
        img = self.renderer.create_blank_image(bg_color=(255, 255, 255))
        draw = ImageDraw.Draw(img)
        
        width, height = img.size
        # Scale parameters for 1024x1024 (from 800x400 base)
        scale_factor = width / 800.0  # Scale based on width
        shelf_y = height // 2  # Shelf position (baseline) - vertically centered
        shelf_height = int(10 * scale_factor)
        
        # Extract colors and properties
        existing_color, _ = color_scheme['existing']
        new_color, _ = color_scheme['new']
        book_width = visual_props['book_width']
        shelf_color = visual_props['shelf_color']
        
        # Draw shelf
        draw.rectangle([0, shelf_y, width, shelf_y + shelf_height], fill=shelf_color)
        
        # Build the same layout structure as initial state
        all_positions = self._build_layout_structure(blue_heights, red_heights, insertion_indices)
        
        # Draw all books (existing books and new books filling gaps)
        spacing = int(5 * scale_factor)  # Scaled spacing
        x_start = int(50 * scale_factor)  # Scaled start position
        
        for i, (pos_type, pos_height, red_idx) in enumerate(all_positions):
            x = x_start + i * (book_width + spacing)
            scaled_h = int(pos_height * 1.5)
            y_top = shelf_y - scaled_h
            
            if pos_type == 'blue':
                # Draw existing book (unchanged)
                fill_color = existing_color
            else:
                # Draw new book (filling gap)
                fill_color = new_color
            
            draw.rectangle(
                [x, y_top, x + book_width, shelf_y],
                fill=fill_color,
                outline=(0, 0, 0),
                width=2
            )
        
        return img
    
    # ══════════════════════════════════════════════════════════════════════════
    #  VIDEO GENERATION
    # ══════════════════════════════════════════════════════════════════════════
    
    def _generate_video(
        self,
        blue_heights: List[float],
        red_heights: List[float],
        insertion_indices: Dict[int, int],
        task_id: str,
        red_queue_order: List[int],
        color_scheme: Dict[str, Tuple[Tuple[int, int, int], str]],
        visual_props: Dict[str, any]
    ) -> str:
        """Generate animation video showing red books being inserted."""
        temp_dir = Path(tempfile.gettempdir()) / f"{self.config.domain}_videos"
        temp_dir.mkdir(parents=True, exist_ok=True)
        video_path = temp_dir / f"{task_id}_ground_truth.mp4"
        
        # Create animation frames
        frames = self._create_insertion_animation_frames(
            blue_heights, red_heights, insertion_indices, red_queue_order, color_scheme, visual_props
        )
        
        result = self.video_generator.create_video_from_frames(
            frames,
            video_path
        )
        
        return str(result) if result else None
    
    def _create_insertion_animation_frames(
        self,
        blue_heights: List[float],
        red_heights: List[float],
        insertion_indices: Dict[int, int],
        red_queue_order: List[int],
        color_scheme: Dict[str, Tuple[Tuple[int, int, int], str]],
        visual_props: Dict[str, any],
        hold_frames: int = 10,
        transition_frames: int = 30
    ) -> List[Image.Image]:
        """
        Create animation frames showing red books moving horizontally from right queue
        to their assigned slots.
        
        Frame count is dynamically adjusted to ensure video duration ≈ 5 seconds.
        """
        # Calculate number of red books
        num_red = len(red_heights)
        
        # Target: ~50 frames (5 seconds at 10 fps)
        # Reserve 0.5 seconds (5 frames) for final hold to ensure task completion is visible
        target_duration = 5.0  # seconds
        target_fps = self.config.video_fps
        target_total_frames = int(target_duration * target_fps)  # ~50 frames
        final_hold_frames = max(5, int(0.5 * target_fps))  # 0.5 seconds for final hold
        
        # Calculate frame budget for animation (excluding final hold)
        animation_budget = target_total_frames - final_hold_frames
        
        # Calculate frame allocation:
        # initial_hold + num_red * transition + (num_red - 1) * mid_hold ≤ animation_budget
        # We want to maintain smooth animation while staying within limit
        
        # Minimum values for smooth animation
        min_initial_hold = 3
        min_transition = 8
        min_mid_hold = 2
        
        # Try to find optimal values that fit within budget
        best_initial_hold = min_initial_hold
        best_transition = min_transition
        best_mid_hold = min_mid_hold
        
        # Calculate required frames for minimum values
        min_required = min_initial_hold + num_red * min_transition + (num_red - 1) * min_mid_hold
        
        if min_required <= animation_budget:
            # We have budget, try to maximize quality
            # Allocate proportionally: transitions get most frames, then holds
            remaining_budget = animation_budget - min_required
            
            # Allocate extra frames proportionally
            # Give 60% to transitions, 20% to initial hold, 20% to mid holds
            extra_transition = int(remaining_budget * 0.6 / num_red) if num_red > 0 else 0
            extra_initial_hold = int(remaining_budget * 0.2)
            extra_mid_hold = int(remaining_budget * 0.2 / max(1, num_red - 1)) if num_red > 1 else 0
            
            best_initial_hold = min_initial_hold + extra_initial_hold
            best_transition = min_transition + extra_transition
            best_mid_hold = min_mid_hold + extra_mid_hold
            
            # Ensure we don't exceed budget
            total = best_initial_hold + num_red * best_transition + (num_red - 1) * best_mid_hold
            if total > animation_budget:
                # Scale down proportionally
                scale = animation_budget / total
                best_initial_hold = max(min_initial_hold, int(best_initial_hold * scale))
                best_transition = max(min_transition, int(best_transition * scale))
                best_mid_hold = max(min_mid_hold, int(best_mid_hold * scale))
        else:
            # Budget is tight, use minimum values and scale down if needed
            scale = animation_budget / min_required
            best_initial_hold = max(2, int(min_initial_hold * scale))
            best_transition = max(5, int(min_transition * scale))
            best_mid_hold = max(1, int(min_mid_hold * scale))
        
        hold_frames = best_initial_hold
        transition_frames = best_transition
        mid_hold_frames = best_mid_hold
        
        frames = []
        
        # Initial state (with gaps and red books queued on the right)
        first_frame = self._render_initial_state(blue_heights, red_heights, insertion_indices, red_queue_order, color_scheme, visual_props)
        for _ in range(hold_frames):
            frames.append(first_frame.copy())
        
        # Sort red books by insertion position for sequential animation
        red_insertions = sorted(insertion_indices.items(), key=lambda x: x[1])
        
        # Animate each red book moving from right queue to its slot
        filled_slots = 0  # Track how many slots have been filled
        
        for red_idx, insertion_pos in red_insertions:
            # Render frames showing this red book moving horizontally to its slot
            for i in range(transition_frames):
                progress = i / (transition_frames - 1) if transition_frames > 1 else 1.0
                
                # Create frame with red book at intermediate position
                frame = self._render_horizontal_move_frame(
                    blue_heights, red_heights, insertion_indices,
                    red_idx, insertion_pos, progress, filled_slots, red_queue_order, color_scheme, visual_props
                )
                frames.append(frame)
            
            filled_slots += 1
            
            # Hold frame after insertion (only if not all books are inserted)
            if filled_slots < len(red_insertions):
                # Show partial state (some slots filled)
                partial_frame = self._render_partial_state(
                    blue_heights, red_heights, insertion_indices, filled_slots, red_queue_order, color_scheme, visual_props
                )
                for _ in range(mid_hold_frames):
                    frames.append(partial_frame.copy())
        
        # Final state: all new books inserted, keep this state static
        # Use reserved final_hold_frames to ensure task completion is clearly visible
        # Use _render_partial_state with all slots filled to avoid "flash/alignment" effect
        # This maintains the same visual layout as animation frames (with spacing between books)
        final_frame = self._render_partial_state(
            blue_heights, red_heights, insertion_indices, len(red_insertions), red_queue_order, color_scheme, visual_props
        )
        for _ in range(final_hold_frames):
            frames.append(final_frame.copy())
        
        return frames
    
    def _render_horizontal_move_frame(
        self,
        blue_heights: List[float],
        red_heights: List[float],
        insertion_indices: Dict[int, int],
        red_idx: int,
        target_slot_pos: int,
        progress: float,
        filled_slots: int,
        red_queue_order: List[int],
        color_scheme: Dict[str, Tuple[Tuple[int, int, int], str]],
        visual_props: Dict[str, any]
    ) -> Image.Image:
        """
        Render frame with red book moving horizontally from right queue to its slot.
        
        Uses two-stage path: slight upward lift (optional) -> horizontal move -> back to baseline.
        
        Args:
            progress: 0.0 = in right queue, 1.0 = in target slot
            filled_slots: Number of slots already filled
        """
        img = self.renderer.create_blank_image(bg_color=(255, 255, 255))
        draw = ImageDraw.Draw(img)
        
        width, height = img.size
        # Scale parameters for 1024x1024 (from 800x400 base)
        scale_factor = width / 800.0  # Scale based on width
        shelf_y = height // 2  # Shelf position (baseline) - vertically centered  # Baseline
        shelf_height = int(10 * scale_factor)
        spacing = int(5 * scale_factor)  # Scaled spacing
        x_start = int(50 * scale_factor)  # Scaled start position
        
        # Extract colors and properties
        existing_color, _ = color_scheme['existing']
        new_color, _ = color_scheme['new']
        book_width = visual_props['book_width']
        shelf_color = visual_props['shelf_color']
        
        # Draw shelf
        draw.rectangle([0, shelf_y, width, shelf_y + shelf_height], fill=shelf_color)
        
        # Build layout structure (same as initial/final state)
        all_positions = self._build_layout_structure(blue_heights, red_heights, insertion_indices)
        
        # Calculate layout parameters (centered shelf, red queue on right)
        num_red = len(red_heights)
        x_start, red_queue_x_start, red_spacing = self._calculate_layout_params(
            width, scale_factor, all_positions, num_red, book_width, spacing
        )
        
        # Find gap index in layout for the target red book
        # The gap corresponding to red_idx is at a specific position in the layout
        gap_layout_idx = None
        for layout_idx, (pos_type, _, red_idx_at_gap) in enumerate(all_positions):
            if pos_type == 'gap' and red_idx_at_gap == red_idx:
                gap_layout_idx = layout_idx
                break
        
        if gap_layout_idx is None:
            # Fallback: use target_slot_pos to find gap
            red_insertions_sorted = sorted(
                insertion_indices.items(),
                key=lambda x: (x[1], red_heights[x[0]])
            )
            for layout_idx, (pos_type, _, red_idx_at_gap) in enumerate(all_positions):
                if pos_type == 'gap':
                    gap_insertion_pos = insertion_indices[red_idx_at_gap]
                    if gap_insertion_pos == target_slot_pos:
                        gap_layout_idx = layout_idx
                        break
        
        # Calculate initial and target positions for moving red book
        red_height = red_heights[red_idx]
        scaled_h = int(red_height * 1.5)
        
        # Find initial x position in queue (using random queue order)
        red_queue_idx = red_queue_order.index(red_idx)
        initial_x = red_queue_x_start + red_queue_idx * (book_width + spacing)
        
        # Find target x position (gap position in layout)
        # Use gap_layout_idx if found, otherwise fall back to target_slot_pos
        if gap_layout_idx is not None:
            target_x = x_start + gap_layout_idx * (book_width + spacing)
        else:
            # Fallback: use target_slot_pos
            target_x = x_start + target_slot_pos * (book_width + spacing)
        
        # Two-stage movement: slight lift -> horizontal -> back down
        # Scale factor is already defined above
        lift_height = int(10 * scale_factor)  # Pixels to lift (scaled)
        if progress < 0.2:
            # Stage 1: Lift up slightly
            lift_progress = progress / 0.2
            current_y = shelf_y - scaled_h - lift_progress * lift_height
            current_x = initial_x
        elif progress < 0.8:
            # Stage 2: Horizontal movement
            move_progress = (progress - 0.2) / 0.6
            current_x = initial_x + (target_x - initial_x) * move_progress
            current_y = shelf_y - scaled_h - lift_height  # Stay lifted
        else:
            # Stage 3: Drop back to baseline
            drop_progress = (progress - 0.8) / 0.2
            current_x = target_x
            current_y = shelf_y - scaled_h - lift_height * (1 - drop_progress)
        
        # Draw blue books and gaps (using same layout structure)
        red_insertions_sorted = sorted(
            insertion_indices.items(),
            key=lambda x: (x[1], red_heights[x[0]])
        )
        
        for i, (pos_type, pos_height, gap_red_idx) in enumerate(all_positions):
            x = x_start + i * (book_width + spacing)
            
            if pos_type == 'blue':
                # Draw blue book
                scaled_h_blue = int(pos_height * 1.5)
                y_top = shelf_y - scaled_h_blue
                draw.rectangle(
                    [x, y_top, x + book_width, shelf_y],
                    fill=existing_color,
                    outline=(0, 0, 0),
                    width=max(2, int(2 * scale_factor))  # Scaled outline width
                )
            else:
                # This is a gap position
                if gap_red_idx in [r[0] for r in red_insertions_sorted[:filled_slots]]:
                    # This gap is already filled with red book
                    scaled_h_gap = int(pos_height * 1.5)
                    gap_y_top = shelf_y - scaled_h_gap
                    draw.rectangle(
                        [x, gap_y_top, x + book_width, shelf_y],
                        fill=new_color,
                        outline=(0, 0, 0),
                        width=2
                    )
                # Empty gap: just leave blank space (no drawing, no border, no height indicator)
                # The gap is represented only by the horizontal spacing
        
        # Draw red books still in queue (excluding the one currently moving)
        # Use random queue order to maintain consistency with initial state
        # red_spacing is already calculated by _calculate_layout_params
        for i, queue_red_idx in enumerate(red_queue_order):
            if queue_red_idx == red_idx:
                continue  # Skip the moving book
            
            # Check if this book has already been placed
            if queue_red_idx in [r[0] for r in red_insertions_sorted[:filled_slots]]:
                continue  # Already placed
            
            x = red_queue_x_start + i * (book_width + red_spacing)
            
            queue_red_height = red_heights[queue_red_idx]
            queue_scaled_h = int(queue_red_height * 1.5)
            y_top = shelf_y - queue_scaled_h
            
            draw.rectangle(
                [x, y_top, x + book_width, shelf_y],
                fill=new_color,
                outline=(0, 0, 0),
                width=max(2, int(2 * scale_factor))  # Scaled outline width
            )
        
        # Draw moving red book
        draw.rectangle(
            [int(current_x), int(current_y), int(current_x) + book_width, int(current_y) + scaled_h],
            fill=new_color,
            outline=(0, 0, 0),
            width=2
        )
        
        return img
    
    def _render_partial_state(
        self,
        blue_heights: List[float],
        red_heights: List[float],
        insertion_indices: Dict[int, int],
        filled_slots: int,
        red_queue_order: List[int],
        color_scheme: Dict[str, Tuple[Tuple[int, int, int], str]],
        visual_props: Dict[str, any]
    ) -> Image.Image:
        """
        Render partial state with some slots filled, red books still queued on right.
        
        Args:
            filled_slots: Number of slots that have been filled so far
        """
        img = self.renderer.create_blank_image(bg_color=(255, 255, 255))
        draw = ImageDraw.Draw(img)
        
        width, height = img.size
        # Scale parameters for 1024x1024 (from 800x400 base)
        scale_factor = width / 800.0  # Scale based on width
        shelf_y = height // 2  # Shelf position (baseline) - vertically centered  # Baseline
        shelf_height = int(10 * scale_factor)
        spacing = int(5 * scale_factor)  # Scaled spacing
        x_start = int(50 * scale_factor)  # Scaled start position
        
        # Extract colors and properties
        existing_color, _ = color_scheme['existing']
        new_color, _ = color_scheme['new']
        book_width = visual_props['book_width']
        shelf_color = visual_props['shelf_color']
        
        # Draw shelf
        draw.rectangle([0, shelf_y, width, shelf_y + shelf_height], fill=shelf_color)
        
        # Build layout structure (same as initial/final state)
        all_positions = self._build_layout_structure(blue_heights, red_heights, insertion_indices)
        
        # Calculate layout parameters (centered shelf, red queue on right)
        num_red = len(red_heights)
        x_start, red_queue_x_start, red_spacing = self._calculate_layout_params(
            width, scale_factor, all_positions, num_red, book_width, spacing
        )
        
        # Sort red books to determine which gaps are filled
        red_insertions_sorted = sorted(
            insertion_indices.items(),
            key=lambda x: (x[1], red_heights[x[0]])
        )
        filled_red_indices = set(r[0] for r in red_insertions_sorted[:filled_slots])
        
        # Draw blue books and gaps
        for i, (pos_type, pos_height, gap_red_idx) in enumerate(all_positions):
            x = x_start + i * (book_width + spacing)
            
            if pos_type == 'blue':
                # Draw blue book (unchanged)
                scaled_h = int(pos_height * 1.5)
                y_top = shelf_y - scaled_h
                draw.rectangle(
                    [x, y_top, x + book_width, shelf_y],
                    fill=existing_color,
                    outline=(0, 0, 0),
                    width=max(2, int(2 * scale_factor))  # Scaled outline width
                )
            else:
                # This is a gap position
                if gap_red_idx in filled_red_indices:
                    # Gap is filled with red book
                    scaled_h = int(pos_height * 1.5)
                    gap_y_top = shelf_y - scaled_h
                    draw.rectangle(
                        [x, gap_y_top, x + book_width, shelf_y],
                        fill=new_color,
                        outline=(0, 0, 0),
                        width=2
                    )
                # Empty gap: just leave blank space (no drawing, no border, no height indicator)
                # The gap is represented only by the horizontal spacing
        
        # Draw red books still in queue (using random queue order)
        # red_spacing is already calculated by _calculate_layout_params
        for i, queue_red_idx in enumerate(red_queue_order):
            # Check if this book has already been placed
            if queue_red_idx in filled_red_indices:
                continue  # Already placed
            
            x = red_queue_x_start + i * (book_width + red_spacing)
            
            queue_red_height = red_heights[queue_red_idx]
            queue_scaled_h = int(queue_red_height * 1.5)
            y_top = shelf_y - queue_scaled_h
            
            draw.rectangle(
                [x, y_top, x + book_width, shelf_y],
                fill=new_color,
                outline=(0, 0, 0),
                width=max(2, int(2 * scale_factor))  # Scaled outline width
            )
        
        return img