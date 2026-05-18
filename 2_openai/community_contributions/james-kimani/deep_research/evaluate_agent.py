from datetime import date
from agents import Agent, ModelSettings
from schemas import Evaluation

CURRENT_YEAR = date.today().year

INSTRUCTIONS = (
    "You evaluate research artifacts for depth, relevance, and internal consistency. "
    "Be strict but fair: flag missing angles, weak sourcing, or unclear conclusions. "
    f"Flag any information that appears outdated or references pre-{CURRENT_YEAR - 1} data without context. "
    "If the work is good enough to proceed, mark satisfactory and say why."
)

evaluate_agent = Agent(
    name="EvaluateAgent",
    instructions=INSTRUCTIONS,
    model="gpt-4o-mini",
    output_type=Evaluation,
    model_settings=ModelSettings(temperature=0.0, max_tokens=350),
)
