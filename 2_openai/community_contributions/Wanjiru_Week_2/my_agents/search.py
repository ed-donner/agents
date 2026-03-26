from agents import Agent, WebSearchTool, ModelSettings

search_agent = Agent(
    name="Search",
    instructions="""
    Search and summarize results in 2-3 short paragraphs.
    """,
    tools=[WebSearchTool()],
    model="gpt-4o-mini",
    model_settings=ModelSettings(tool_choice="required"),
)
