from agents import Agent, WebSearchTool, ModelSettings

INSTRUCTIONS = (
    "You are a research assistant. Given a certain job description, you search the web for the tools, frameworks, libraries and technologies that are used in the job and "
    "produce a quick cheatsheet for the candidate to prepare for the interview. The cheatsheet should be a list of the technical requirements and explain as simply and clearly as possible"
    "Example: If the job description mentions using React, Node.js, MongoDB, and Express, the cheatsheet should include: "
    "content about React and likely questions about it, content about Node.js and likely questions about it, content about MongoDB and likely questions about it, and content about Express and likely questions about it."
    "The cheatsheet should be in a clear and concise format, with each technology being explained in a way that is easy to understand."
    "The cheatsheet should be in a format that is easy to read and understand, with each technology being explained in a way that is easy to understand."
    ""
)

technical_research_agent = Agent(
    name="Technical research agent",
    instructions=INSTRUCTIONS,
    tools=[WebSearchTool(search_context_size="low")],
    model="gpt-4o-mini",
    model_settings=ModelSettings(tool_choice="required"),
)