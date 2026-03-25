from agents import Agent

CLARIFIER_INSTRUCTIONS = """
You are a helpful assistant.
Given a research topic, ask exactly three clear, concise clarifying questions.
Number them 1., 2., 3.
Do not answer the questions, only ask them.
"""

clarifier_agent = Agent(
    name="Clarifier Agent",
    instructions=CLARIFIER_INSTRUCTIONS,
    model="gpt-4o-mini",
)