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
        "You have a bookshelf with {existing_color} books (already placed) and {new_color} books (to be inserted). Each {existing_color} book has a height, and they are arranged from left to right. {existing_color} books are clustered by height: if two adjacent {existing_color} books have similar heights, they belong to the same cluster. For each {new_color} book, find the {existing_color} book cluster whose representative height (average of all books in that cluster) is closest to the {new_color} book's height. Insert each {new_color} book at the end of its assigned cluster. If multiple {new_color} books are assigned to the same position, insert them in order of increasing height. Output the 0-based insertion position for each {new_color} book.",
        "Given a row of {existing_color} books (existing books on shelf) and {new_color} books (to insert), determine where each {new_color} book should be inserted. {existing_color} books form clusters based on adjacent height differences: adjacent books with similar heights belong to the same cluster. Each cluster has a representative height (mean of all books in that cluster). Assign each {new_color} book to the cluster with the nearest representative height, and insert it at the end of that cluster. If multiple {new_color} books target the same position, insert them sorted by height (ascending). Output the 0-based insertion position for each {new_color} book.",
        "A bookshelf contains {existing_color} books arranged left to right. {existing_color} books are grouped into clusters where adjacent books with similar heights form a cluster. {new_color} books need to be inserted. For each {new_color} book, find the cluster whose average height (mean of all books in that cluster) is closest to the {new_color} book's height, and insert the {new_color} book at the end of that cluster. If multiple {new_color} books target the same position, insert them sorted by height (ascending). Output the 0-based insertion position for each {new_color} book.",
    ],
}


def get_prompt(task_type: str = "default", color_scheme=None) -> str:
    """
    Select a random prompt for the given task type with color substitution.
    
    Args:
        task_type: Type of task (key in PROMPTS dict)
        color_scheme: Dictionary with color information for substitution
        
    Returns:
        Random prompt string with colors substituted
    """
    prompts = PROMPTS.get(task_type, PROMPTS["default"])
    prompt_template = random.choice(prompts)
    
    # Perform color substitution if color_scheme is provided
    if color_scheme:
        existing_color = color_scheme['existing'][1]  # Color name
        new_color = color_scheme['new'][1]  # Color name
        
        prompt = prompt_template.format(
            existing_color=existing_color,
            new_color=new_color
        )
        return prompt
    else:
        # Fallback to default colors if no color scheme provided
        return prompt_template.format(
            existing_color="blue",
            new_color="red"
        )


def get_all_prompts(task_type: str = "default") -> list[str]:
    """Get all prompts for a given task type."""
    return PROMPTS.get(task_type, PROMPTS["default"])
