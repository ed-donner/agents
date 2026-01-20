from agents import Agent

INSTRUCTIONS = f"You are a helpful research assistant. Given a query, come up with a set of questions \
    that can help you understand the query better and plan your research. Output a list of 5 questions."

questions_generator_agent = Agent(
    name="QuestionsGeneratorAgent",
    instructions=INSTRUCTIONS,
    model="gpt-4o-mini",
)