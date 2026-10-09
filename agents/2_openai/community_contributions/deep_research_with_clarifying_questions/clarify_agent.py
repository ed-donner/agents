from agents import Agent

INSTRUCTIONS = (
    "You are a clarification agent. You will be given a research query, your job is to generate a list of questions that user has to answer to clarify the query."
    "The questions should narrow down the scope of the research to a more specific topic, by asking questions that explore the intention of the user that he or she forgot to include in the query."
)

clarify_agent = Agent(
    name="ClarifyAgent",
    instructions=INSTRUCTIONS,
    model="gpt-4o-mini",
    output_type=str,
)