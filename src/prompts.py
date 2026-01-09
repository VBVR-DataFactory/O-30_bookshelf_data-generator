"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                           YOUR TASK PROMPTS                                   ║
║                                                                               ║
║  CUSTOMIZE THIS FILE to define prompts/instructions for your task.            ║
║  Prompts are selected based on task type and returned to the model.           ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import random


# ══════════════════════════════════════════════════════════════════════════════
#  DEFINE YOUR PROMPTS
# ══════════════════════════════════════════════════════════════════════════════

PROMPTS = {
    "default": [
        "You have a bookshelf with blue books (already placed) and red books (to be inserted). Each blue book has a height, and they are arranged from left to right. Blue books are clustered by height: if two adjacent blue books have similar heights (their height difference is small), they belong to the same cluster. For each red book, find the blue book cluster whose representative height (average of all books in that cluster) is closest to the red book's height. Insert each red book at the end of its assigned cluster. If multiple red books are assigned to the same position, insert them in order of increasing height. Output the insertion index (0-based position) for each red book.",
        "Given a row of blue books (existing books on shelf) and red books (to insert), determine where each red book should be inserted. Blue books form clusters based on adjacent height differences: adjacent books with similar heights belong to the same cluster. Each cluster has a representative height (mean of all books in that cluster). Assign each red book to the cluster with the nearest representative height, and insert it at the end of that cluster. If multiple red books target the same position, insert them sorted by height (ascending). Output the 0-based insertion index for each red book.",
        "A bookshelf contains blue books arranged left to right. Blue books are grouped into clusters where adjacent books with similar heights form a cluster. Red books need to be inserted. For each red book, find the cluster whose average height (mean of all books in that cluster) is closest to the red book's height, and insert the red book at the end of that cluster. If multiple red books target the same position, insert them sorted by height (ascending). Provide the insertion index (0-based position) for each red book.",
    ],
}


def get_prompt(task_type: str = "default") -> str:
    """
    Select a random prompt for the given task type.
    
    Args:
        task_type: Type of task (key in PROMPTS dict)
        
    Returns:
        Random prompt string from the specified type
    """
    prompts = PROMPTS.get(task_type, PROMPTS["default"])
    return random.choice(prompts)


def get_all_prompts(task_type: str = "default") -> list[str]:
    """Get all prompts for a given task type."""
    return PROMPTS.get(task_type, PROMPTS["default"])
