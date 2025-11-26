from agents import Agent

from constants import CANVAS_WIDTH, CANVAS_HEIGHT
from context.app_context import AppContext
from tools.graphic_tool import free_draw_tool

INSTRUCTIONS = f"""You are a talented kid who knows how to draw.
You are provided a tool to draw freely using a brush, by providing drawing paths.
You will be provided a detailed drawing plan, which you must follow accurately, by using the tool up to 50 times.
The canvas dimensions are {CANVAS_WIDTH}, {CANVAS_HEIGHT}. 
"""

drawing_agent = Agent[AppContext](
    name="Drawing agent",
    instructions=INSTRUCTIONS,
    tools=[free_draw_tool],
    model="gpt-4o-mini",
)

print(free_draw_tool)
