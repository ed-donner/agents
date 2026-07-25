from datetime import date
from agents import Agent, ModelSettings

TODAY = date.today().isoformat()

INSTRUCTIONS = (
    f"You are writing in {TODAY}. "
    "Synthesize the research snippets below into a useful markdown report.\n"
    "Answer ONLY using the provided research. Do not use prior knowledge. "
    "If the research is insufficient, say so.\n"
    "Be concise: aim for 400-600 words. End with a '## Follow-up questions' section (3 items max)."
)

writer_agent = Agent(
    name="WriterAgent",
    instructions=INSTRUCTIONS,
    model="gpt-4o-mini",
    model_settings=ModelSettings(temperature=0.2, max_tokens=1800),
)
