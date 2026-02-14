from agents import Agent

from constants import CANVAS_WIDTH, CANVAS_HEIGHT
from context.app_context import AppContext
from my_agents.drawing_agent import drawing_agent
from my_agents.input_guardrail_agent import drawing_guardrail

INSTRUCTIONS = f"""You are a talented kid who likes to draw.
You are provided a drawing request.
Form a plan of exactly how to draw the request, and write it in detail: the steps taken, positions, colors, shapes, and so on.
When you are done, hand off the plan to the drawing agent to execute it.
The canvas dimensions are {CANVAS_WIDTH}, {CANVAS_HEIGHT} and your plan should respect those dimensions. 
"""

drawing_planning_agent = Agent[AppContext](
    name="Drawing planning agent",
    instructions=INSTRUCTIONS,
    handoffs=[drawing_agent],
    input_guardrails=[drawing_guardrail],
    model="gpt-4o-mini",
)
