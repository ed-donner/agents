from agents import Agent, Runner,WebSearchTool, ModelSettings
from pydantic import BaseModel, Field
from planner import WebSearchPlan
from writer_agent import writer_agent


class SearchExecutionOutput(BaseModel):
    query: str = Field(description="The original search query.")
    results: list[str] = Field(
        description="One summarized search result per planned search item, in the same order."
    )


web_search_agent = Agent(
    name="Web Search agent",
    instructions=(
        "You are a research assistant. Given a search term, you search the web for that term and "
        "produce a concise summary of the results. The summary must 2-3 paragraphs and less than 300 "
        "words. Capture the main points. Write succintly, no need to have complete sentences or good "
        "grammar. This will be consumed by someone synthesizing a report, so its vital you capture the "
        "essence and ignore any fluff. Do not include any additional commentary other than the summary itself."
    ),
    tools=[WebSearchTool(search_context_size="low")],
    model="gpt-4o-mini",
    model_settings=ModelSettings(tool_choice="required"),
)



class ReportGenerator:
    def __init__(self, query: str, search_plan: WebSearchPlan):
        self.query = query
        self.search_plan = search_plan

        self.web_search_tool = web_search_agent.as_tool(
            tool_name="run_web_search_tool",
            tool_description="Execute one web search query with context and summarize findings.",
        )
        self.agent = Agent(
            name="Search Executor Agent",
            instructions=(
                "You execute a list of planned web searches.\n"
                "For each search item, call run_web_search_tool exactly once.\n"
                "Do not skip items.\n"
                "\n"
                "After executing ALL search items, you MUST handoff to the Writer Agent with the original query and the search results.\n"
                "Do NOT attempt to write the final answer yourself.\n"
                "Your job ends after collecting all search results.\n"
                "Return only structured output with the original query and the search results."
            ),
            model="gpt-4o-mini",
            tools=[self.web_search_tool],
            handoffs=[writer_agent],
            output_type=SearchExecutionOutput,
        )

    def run(self):
        """ Run the report generator agent """
        plan_text = "\n".join(
            [
                f"{index + 1}) Search term: {item.query}\nReason: {item.reason}"
                for index, item in enumerate(self.search_plan.searches)
            ]
        )
        payload = (
            "Run all planned searches and return one summarized result per item.\n"
            f"Original query: {self.query}"
            f"Planned searches:\n{plan_text}\n"
        )

        return Runner.run_streamed(self.agent, payload)


