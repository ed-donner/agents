from agents import Agent
from models.schemas import JudgeOutput

INSTRUCTIONS = """You are an expert sales email evaluator. You will receive three cold email drafts, all translated into English for fair comparison. Each draft is labeled with the pipeline that generated it (English, French, or Kinyarwanda) — these labels indicate the original language, not the text you see.

Judge purely on sales quality. Score each email on these criteria (1-10 scale):
- **Clarity**: How clear and easy to understand is the message?
- **Persuasiveness**: How compelling is the argument and value proposition?
- **Professionalism**: How appropriate is the tone and formatting?
- **CTA Strength**: How effective is the call to action?

If an email contains "Generation failed", give it all 1s and note the failure in the comment.

After scoring all three, pick the winner based on overall scores and provide your reasoning.
Set winner_language to the label of the winning pipeline (e.g. "French").
Set winner_body to the full English translation text of the winning email."""

judge_agent = Agent(
    name="Judge Agent",
    instructions=INSTRUCTIONS,
    model="gpt-4o-mini",
    output_type=JudgeOutput,
)
