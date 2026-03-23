from agents import Agent, WebSearchTool, ModelSettings

INSTRUCTIONS = (
    "You are a learning resource curator. Given a skill name, subskills, and learner constraints, "
    "search the web to find the best available learning resources. Prefer current, reputable, and practical sources. "
    "Use budget and learning-style hints when choosing resources. "
    "Find and return: "
    "1. One to two high-quality online courses or tutorials, "
    "2. One official documentation or authoritative reference link, "
    "3. One practical hands-on project or exercise idea. "
    "Be concise. Format your output as plain text with clear labels: Courses:, Docs:, Project:. "
    "Do not include commentary or preamble."
)

search_agent = Agent(
    name="SearchAgent",
    instructions=INSTRUCTIONS,
    tools=[WebSearchTool(search_context_size="low")],
    model="gpt-4o-mini",
    model_settings=ModelSettings(tool_choice="required"),
)
