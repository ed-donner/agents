from agents import Agent, ModelSettings
from ai_model import anthropic_model
from email_agent import email_agent
from planner_agent import planner_agent
from response_model import ResearchAgentResponse
from search_agent import search_agent
from writer_agent import writer_agent

search_planner_agent_tool = planner_agent.as_tool(
    tool_name="search_planner_tool",
    tool_description="Use this tool to come up with a set of web searches to perform to gather in detail all the required information about the query's topic.",
)
search_agent_tool = search_agent.as_tool(
    tool_name="search_agent_tool",
    tool_description="Use this tool to search the web for the provided search term and produce a concise summary of the results. The summary must 2-3 paragraphs and less than 300 words. Capture the main points and be succinct. Reply only with the summary.",
)
write_agent_tool = writer_agent.as_tool(
    tool_name="writer_agent_tool",
    tool_description="Use this tool to write a comprehensive report based on the research and the query. The final output should be in markdown format, and it should be lengthy and detailed. Aim for 5-10 pages of content, at least 1000 words.",
)
email_agent_tool = email_agent.as_tool(
    tool_name="email_agent_tool",
    tool_description="Use this tool to send an email with the provided subject and body. The body should be in Makrdown format.",
)

RESEARCH_AGENT_INSTRUCTIONS = """
        You are a research assistant that receives various queries from users on specific scientific topis.

        Guidelines:
            1. Plan Searches: For each query, come up with a set of web searches to be able to gather in detail all the required information about the query's topic. [use search planner tool]
            2. Perform Searches: For each search term, search the web and produce a concise summary of the results. The summary must be 2-3 paragraphs and less than 300 words. Capture the main points and be succinct. Reply only with the summary. [use search web tool]
            3. Write Report: Based on the original query and the summarized search results, write a comprehensive report. The final output should be in markdown format, and it should be lengthy and detailed [use write report tool]
            4. Send Report Email: Send an email with the provided subject and body extracted from the report. The subject should be different form the query. The body should be in Markdown format. [use send email tool]
            5. Finally you answer the user with the report and the email sent confirmation.

        ***Important:*** You must follow the above guidelines in order. Do not skip any steps. You must use the provided tools to perform each step. Do not try to do everything in one step. Each step is important and must be done in order.
        ***Important:*** Answer only on queries related to scientific topics. If the query is not related to a scientific topic, respond with "I am sorry, I can only answer queries related to scientific topics."
    """

model_settings = ModelSettings(tool_choice="required")
research_agent = Agent(
    name="Research Agent",
    instructions=RESEARCH_AGENT_INSTRUCTIONS,
    tools=[
        search_planner_agent_tool,
        search_agent_tool,
        write_agent_tool,
        email_agent_tool,
    ],
    model=anthropic_model,
    model_settings=model_settings,
    output_type=ResearchAgentResponse,
)
