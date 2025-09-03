from agents import Agent

INSTRUCTIONS = (
    "You are a request refinement agent. When you are given a research query, you generate a list of questions needed to refine the query."
    "The questions should focus the scope of the research to a more specific topic, exploring the intended of the research."
)

refinement_agent = Agent(
    name="RefinementAgent",
    instructions=INSTRUCTIONS,
    model="gpt-4o-mini",
    output_type=str,
)