from agents import Agent, ModelSettings, Runner
from planner import WebSearchItem


INSTRUCTIONS = """
You are a research analyst with MCP tools for web search and optional page fetching.

Workflow:
1. Use the available Brave web-search MCP tool to search for the requested topic.
2. If the search snippets are too thin, use the page-fetching MCP tool on one or two promising URLs.
3. Return a concise synthesis grounded in the search findings.

Output rules:
- Keep the response under 300 words.
- Use 2-3 compact paragraphs or short sections.
- Finish with a "Sources:" section containing 2-5 URLs.
- Do not mention tool names or internal workflow details.
"""

class Searcher:
    def __init__(self, servers):
        self.agent = Agent(
            name="Searcher",
            instructions=INSTRUCTIONS,
            model="gpt-4o-mini",
            mcp_servers=servers,
            model_settings=ModelSettings(tool_choice="required")
        )


    async def run(self, item: WebSearchItem):
        prompt = (
            "Research this search request and summarize what matters for the final report.\n\n"
            f"Search term: {item.query}\n"
            f"Why this search matters: {item.reason}"
        )
        result = await Runner.run(self.agent, prompt)

        return str(result.final_output)
