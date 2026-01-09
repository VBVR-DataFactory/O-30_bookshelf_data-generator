# Bookshelf Insertion Task Generator 📚

A data generator for creating synthetic reasoning tasks involving book insertion on a bookshelf. This generator creates tasks where red books need to be intelligently inserted into gaps between blue books based on height clustering and matching.

---

## 🚀 Quick Start

```bash
# 1. Clone the repository
git clone https://github.com/your-org/bookshelf-task-generator.git
cd bookshelf-task-generator

# 2. Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
pip install -e .

# 4. Generate tasks
python examples/generate.py --num-samples 50
```

---

## 📋 Task Description

The **Bookshelf Insertion Task** requires determining where to insert red books into a shelf of blue books:

1. **Blue books** (existing): Arranged left-to-right on a shelf, forming height-based clusters
   - Two adjacent blue books belong to the same cluster if their height difference ≤ `eps`
   - Each cluster has a representative height (mean of cluster members)

2. **Red books** (to insert): Need to be inserted into gaps between blue books
   - Each red book is assigned to the cluster whose representative height is closest
   - Red books are inserted at the end of their assigned cluster
   - If multiple red books target the same position, they are sorted by height (ascending)

3. **Output**: The insertion index (0-based position) for each red book

---

## 📁 Project Structure

```
template-data-generator/
├── core/                    # ✅ Framework utilities (DO NOT MODIFY)
│   ├── base_generator.py   # Abstract base class
│   ├── schemas.py          # Pydantic models (TaskPair)
│   ├── image_utils.py      # Image rendering helpers
│   ├── video_utils.py      # Video generation utilities
│   └── output_writer.py    # File output handler
├── src/                     # ⚠️ Task-specific implementation
│   ├── generator.py        # Bookshelf task generator
│   ├── prompts.py          # Task prompt templates
│   └── config.py           # Task configuration (TaskConfig)
├── examples/
│   └── generate.py         # Entry point script
└── data/                    # Generated output
    └── {domain}_task/       # e.g., bookshelf_task/
        └── {task_id}/       # e.g., bookshelf_0000/
```

---

## 📦 Output Format

Each generated task produces the following files:

```
data/{domain}_task/{task_id}/
├── first_frame.png          # Initial state: blue books with gaps, red books queued on right
├── final_frame.png          # Final state: red books inserted into gaps
├── prompt.txt               # Task instructions (REQUIRED)
├── insertion_indices.txt    # Mapping: red book index -> insertion position (0-based)
└── ground_truth.mp4         # Animation video showing insertion process (OPTIONAL)
```

### Example `insertion_indices.txt`:
```
Red book index -> Insertion position (0-based)
==================================================
Red book 0: insert at position 1
Red book 1: insert at position 3
Red book 2: insert at position 4
```

---

## 🎨 Task Implementation

### Core Algorithm

1. **Generate blue book heights** with clustering structure (2-4 groups)
2. **Calculate slot positions** (gaps between blue books)
3. **Generate red book heights** from adjacent blue books
4. **Optimal assignment**: Match red books to slots using height-based matching
   - Minimizes: `sum |red_height - slot_target_height|`
   - Uses brute force for small problems (n ≤ 8), greedy for larger ones
5. **Render images**: Initial state (with gaps) and final state (filled)
6. **Generate video** (optional): Animated insertion sequence

### Key Features

- **Height-based clustering**: Blue books form natural clusters based on adjacent height differences
- **Optimal matching**: Red books are assigned to slots using optimal assignment algorithm
- **Visual consistency**: Same layout structure in initial and final states (red books only fill gaps)
- **Animation support**: Smooth horizontal movement with lift/drop transitions

---

## ⚙️ Configuration

All hyperparameters are defined in `src/config.py`:

```python
class TaskConfig(GenerationConfig):
    # Domain and image settings
    domain: str = "bookshelf"
    image_size: tuple[int, int] = (800, 400)
    
    # Video settings
    generate_videos: bool = True
    video_fps: int = 10
    
    # Task-specific parameters
    num_blue_books: int = 10        # Number of existing blue books
    num_red_books: int = 3          # Number of red books to insert (varies: 2-5)
    eps: Optional[float] = None     # Clustering threshold (auto: 0.05 * median)
    min_book_height: float = 50.0   # Minimum book height
    max_book_height: float = 200.0  # Maximum book height
```

---

## 🎯 Usage Examples

### Basic generation
```bash
python examples/generate.py --num-samples 100
```

### Custom output directory
```bash
python examples/generate.py --num-samples 50 --output data/my_task
```

### With random seed (for reproducibility)
```bash
python examples/generate.py --num-samples 100 --seed 42
```

### Without video generation (faster)
```bash
python examples/generate.py --num-samples 100 --no-videos
```

---

## 🔧 Dependencies

- **numpy**: Numerical computations
- **Pillow**: Image rendering
- **pydantic**: Data validation and configuration
- **opencv-python**: Video generation (optional, for ground truth videos)

See `requirements.txt` for specific versions.

---

## 📝 Customization

To adapt this generator for a different task:

1. **Modify `src/generator.py`**: Implement your task generation logic
2. **Update `src/prompts.py`**: Define task-specific prompts
3. **Adjust `src/config.py`**: Add your task's hyperparameters
4. **Update `core/schemas.py`**: Extend `TaskPair` if needed (e.g., `insertion_indices`)

The core framework (`core/`) is designed to be task-agnostic and should not be modified.

---

## 📄 License

See `LICENSE` file for details.
