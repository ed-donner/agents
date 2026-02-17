from crewai import Agent
from gradio import Markdown

proposer = Agent(
    role="Proposer",
    goal="Argue that being vegan is better for the environment",
    backstory="You are a passionate environmentalist with deep knowledge in sustainability and climate science.",
    verbose=True
)

opposer = Agent(
    role="Opposer",
    goal="Argue that being vegan is not necessarily better for the environment",
    backstory="You are a critical thinker who questions mainstream beliefs and supports nuanced ecological arguments.",
    verbose=True
)

judge = Agent(
    role="Judge",
    goal="Impartially evaluate the arguments and decide who made a stronger case",
    backstory="You are a neutral academic with expertise in logic, debate, and environmental science.",
    verbose=True
)
