from agents import Agent

refiner = Agent(
    name="Refiner",
    instructions="""
    Improve the research query based on missing information.
    Make it more specific.
    """,
    model="gpt-4o-mini",
)
