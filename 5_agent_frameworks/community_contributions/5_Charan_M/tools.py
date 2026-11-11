from smolagents import tool
from board import get_board_summary, add_todo, mark_todo_done

@tool
def show_todos() -> str:
    """Returns the current pending goals and tasks on the board."""
    return get_board_summary()

@tool
def plan_steps(goal_id: int, steps: list[str]) -> str:
    """Adds a list of steps as tasks under a specific goal on the board.
    
    Args:
        goal_id: The ID of the goal to add tasks to.
        steps: A list of string descriptions for each step.
    """
    for step in steps:
        add_todo(goal_id, step)
    return f"Added {len(steps)} steps to goal {goal_id}."

@tool
def complete_task(todo_id: int) -> str:
    """Marks a task as completed on the board.
    
    Args:
        todo_id: The ID of the task to complete.
    """
    mark_todo_done(todo_id)
    return f"Marked task {todo_id} as complete."
