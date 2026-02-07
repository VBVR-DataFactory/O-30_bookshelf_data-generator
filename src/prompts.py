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
    "In the scene, there is a bookshelf with a set of books already placed, "
    "and a few {new_color} books waiting on the right. "
    "There are gaps between the books on the shelf. "
    "Place each {new_color} book into a gap where its height is closest to the surrounding books. "
    "Show the insertion process step by step."
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
        new_color = color_scheme['new'][1]  # Color name (only use new book color)
    else:
        new_color = "red"
    
    return PROMPT_TEMPLATE.format(new_color=new_color)


def get_all_prompts(task_type: str = "default") -> list[str]:
    """Get all prompts for a given task type (returns single prompt in a list for compatibility)."""
    return [get_prompt(task_type)]
