"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                          BOOKSHELF TASK PROMPTS                               ║
║                                                                               ║
║  Unified parameterized prompt template for bookshelf insertion task.         ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""


# ══════════════════════════════════════════════════════════════════════════════
#  UNIFIED PROMPT TEMPLATE
# ══════════════════════════════════════════════════════════════════════════════

PROMPT_TEMPLATE = (
    "You have a bookshelf with {existing_color} books (already placed) and {new_color} books (to insert). "
    "The {existing_color} books are arranged from left to right and form clusters by height. "
    "Adjacent books with similar heights belong to the same cluster. "
    "For each {new_color} book, find the cluster whose average height is closest to the book's height, "
    "and insert it at the end of that cluster. "
    "If multiple {new_color} books target the same position, insert them sorted by height (ascending). "
    "Output the 0-based insertion position for each {new_color} book."
)


def get_prompt(task_type: str = "default", color_scheme=None) -> str:
    """
    Get unified prompt for bookshelf insertion task.

    Args:
        task_type: Type of task (kept for compatibility)
        color_scheme: Dictionary with color information for substitution

    Returns:
        Formatted prompt string with colors substituted
    """
    if color_scheme:
        existing_color = color_scheme['existing'][1]  # Color name
        new_color = color_scheme['new'][1]  # Color name
    else:
        existing_color = "blue"
        new_color = "red"
    
    return PROMPT_TEMPLATE.format(
        existing_color=existing_color,
        new_color=new_color
    )


def get_all_prompts(task_type: str = "default") -> list[str]:
    """Get all prompts for a given task type (returns single prompt in a list for compatibility)."""
    return [get_prompt(task_type)]
