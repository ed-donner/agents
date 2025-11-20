from agents import Agent
from planner_agent import planner_agent
from search_agent import search_agent
from writer_agent import writer_agent

# Convert agents to tools using .as_tool() method
search_plan_tool = planner_agent.as_tool(
    tool_name="search_plan_tool",
    tool_description="Create a comprehensive search plan with multiple search terms for a research query"
)

search_tool = search_agent.as_tool(
    tool_name="search_tool", 
    tool_description="Perform a web search on a specific term and return a concise summary of results"
)

research_tools = [search_plan_tool, search_tool]

RESEARCH_MANAGER_INSTRUCTIONS = """You are a research manager responsible for conducting comprehensive research on any given topic.

CRITICAL: You MUST complete the entire handoff chain. Do NOT consider your task complete until ALL handoffs are executed.

Your MANDATORY process:
1. First, use the search_plan_tool to create a detailed research plan for the given query
2. Then, use the search_tool multiple times to gather information based on each search term in your plan
3. Use the search_tool at least once for each search term in your plan - don't skip any searches
4. You can use the search_tool multiple times if you're not satisfied with the results from the first try
5. Collect and organize all search results into a comprehensive document
6. **MANDATORY HANDOFF**: Once you have gathered sufficient information from all planned searches, you MUST handoff to the Writer Agent to create a professional report

HANDOFF REQUIREMENT: 
- You are REQUIRED to handoff to the Writer Agent
- Do NOT provide a final response without executing the handoff
- Your job is NOT complete until the Writer Agent has received your research findings
- If the handoff fails, you must retry the handoff
- Always end your work by executing the handoff to Writer Agent

Never skip the planning step. Always use all your tools effectively before handing off. Make sure you gather comprehensive information and then ALWAYS handoff to Writer Agent."""


research_manager = Agent(
    name="Research Manager",
    instructions=RESEARCH_MANAGER_INSTRUCTIONS,
    tools=research_tools,
    handoffs=[writer_agent],
    model="gpt-4o-mini",
    handoff_description="Gather comprehensive research information on a topic and hand off findings to writer"
)
