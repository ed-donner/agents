from typing import List, Tuple, Union, Sequence
from agents import function_tool, RunContextWrapper

from context.app_context import AppContext
from tools.graphic_canvas import HeadlessCanvas  # OpenAI Agents SDK

ColorLike = Union[str, Sequence[int]]

@function_tool
def free_draw_tool(
    ctx: RunContextWrapper[AppContext],
    path: List[List[float]],
    color: ColorLike = "#000000",
    brush_px: int = 3,
) -> str:
    """
    Draw a thick polyline on the global headless canvas.

    Args:
        ctx: RunContextWrapper carrying AppContext, including the canvas.
        path: List of [x, y] coordinate pairs in pixels to connect in order.
        color: Stroke color as "#RRGGBB" or a named color.
        brush_px: Line thickness in pixels.

    Returns:
        A status message indicating success.
    """
    # Normalize path into list of (x, y) tuples
    normalized_path = [(float(p[0]), float(p[1])) for p in path]

    # Assumes canvas.initialize(...) was called earlier in the app lifecycle
    canvas = ctx.context.canvas
    canvas.free_draw(path=normalized_path, color=color, brush_px=brush_px)
    return "free_draw completed"