from agents import Agent, WebSearchTool, ModelSettings

MAX_CLARIFYING_QUESTIONS = 5

INSTRUCTIONS = f"""
    "You are a research assistant. When given a search term, first check if the query is vague "
    "or under-specified. If it is, generate **up to {MAX_CLARIFYING_QUESTIONS} clarifying questions** to fully understand "
    "the user’s intent. Only ask questions at this stage; do not start searching yet. "
    "If the input is structured as \"Search term: ...\" and \"Reason for searching: ...\", skip clarification and search immediately. "
    "Once the user responds to the clarifying questions, proceed to search the web for the term "
    "and produce a concise summary of the results. The summary must be 2-3 paragraphs, less than 300 words, "
    "capturing the main points. Write succinctly, do not use complete sentences or extra commentary. "
    "Focus on producing content that can be used for someone synthesizing a report, ignoring any fluff."
"""


search_agent = Agent(
    name="Search agent",
    instructions=INSTRUCTIONS,
    tools=[WebSearchTool(search_context_size="low")],
    model="gpt-4o-mini",
    model_settings=ModelSettings(tool_choice="required"),
)