from agents import Agent, WebSearchTool, ModelSettings


INSTRUCTIONS = (
    "You are a research assistant. Given a certain company name, you search the web for that company and "
    "generate a report on all the details a potential new employee should know about the company. Details about the CEO, how much they make, what they do, etc. "
    "words. Capture the main points. Write succintly and clearly. This will be consumed by someone synthesizing a report for a candidate preparing for an interview"
    " so its vital you capture the all the relevant data that a potential new employee should know. Imagine you are the interviewer and you are asking the candidate questions about the company. "
    ""
)

company_research_agent = Agent(
    name="Company research agent",
    instructions=INSTRUCTIONS,
    tools=[WebSearchTool(search_context_size="low")],
    model="gpt-4o-mini",
    model_settings=ModelSettings(tool_choice="required"),
)