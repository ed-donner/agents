import os
from dotenv import load_dotenv
from agents import Agent, OpenAIChatCompletionsModel, function_tool, ModelSettings, Runner
from openai import AsyncOpenAI
from planner_agent import planner_agent
from search_agent import search_agent
from reporter_agent import reporter_agent
from evaluator import evaluator_agent
from email_manager import email_manager
from clarification_agent import CLARIFYING_QUESTIONS, clarification_agent
from guardrail_agent import guardrail_against_abuse
from constants import gemini_default_model, default_model
from models import ResearchManagerUpdates
# from deep_research import DeepResearchHooks
import asyncio

load_dotenv(override=True)

# deepseek_client = AsyncOpenAI(base_url=DEEPSEEK_BASE_URL, api_key=deepseek_api_key)
gemini_client = AsyncOpenAI(base_url=os.environ.get("GEMINI_BASE_URL"), api_key=os.environ.get("GOOGLE_API_KEY"))
# groq_client = AsyncOpenAI(base_url=GROQ_BASE_URL, api_key=groq_api_key)

# deepseek_model = OpenAIChatCompletionsModel(model=deepseek_default_model, openai_client=deepseek_client)
gemini_model = OpenAIChatCompletionsModel(model=gemini_default_model, openai_client=gemini_client)
# llama3_3_model = OpenAIChatCompletionsModel(model=groq_default_model, openai_client=groq_client)

CLARIFYING_QUESTIONS=3
MAX_RETRY=2

INSTRUCTIONS = (
  "Context: You are a Reasearch Manager. You have a team of research assistants to help you complete the research and generate"
  " and a cohesive report for the research query. Your research assistants are available to you as a set of tools. "
  f"Step 1: Given a query and clarifying questions, if clarifying questions are provided in input then skip this step and proceed to next step else if no clarifying questions given then use your tool to come up with {CLARIFYING_QUESTIONS} clarifying questions based on the query, provide output in format {ResearchManagerUpdates} and stop further execution."
  "Step 2: Use your tools to come up with a set of search terms based on query and clarifying questions that you came up with. "
  "Step 3: Evaluate the results using your tools and suggest changes if needed and finalize the search terms with the help of tools."
  "Step 4: Once the search terms are finalized, perform the searches parallelly using your tools and evaluate the results using the tools,"
  "Step 5: use tool to evaluate if it is not satisfied with results ask to perform the searches again using the tools incorporating any suggestions if needed." 
  f" Web search retries should not exceed more than {MAX_RETRY} times."
  "Step 6: Finalize the results and use your tools to generate a cohesive report, Step 7 : evaluate the report using your tools and suggest changes if needed"
  " and Step 8: finalize the report with the help of tools."
  "Step 9: Once the final report is generated use handoffs to send out an email with the report."
  "Note: As a research manager it is crucial you provide status updates on every step you perform and also log any information that you receive or changes your suggest using your tools"
)

clarification_agent_tool = clarification_agent.as_tool("clarification_agent", tool_description=f"Given a query, help come up with {CLARIFYING_QUESTIONS} clarifying questions based on the provided query.")
planner_agent_tool = planner_agent.as_tool("planner_agent", tool_description="Help come up with a set of web search terms given a query, clarifying questions")
search_agent_tool = search_agent.as_tool("search_agent", tool_description="Help perform web searches")
reporter_agent_tool = reporter_agent.as_tool("report_agent", tool_description="Help generate a cohesive report")
evaluator_agent_tool = evaluator_agent.as_tool("evaluator_agent", tool_description="Help evaluate any findings")

@function_tool
async def logger_tool(msg: str):
  print(msg)
  return msg

tools = [clarification_agent_tool, planner_agent_tool, search_agent_tool, reporter_agent_tool, evaluator_agent_tool, logger_tool]

research_manager = Agent(
  name="research_manager",
  instructions=INSTRUCTIONS,
  tools=tools,
  handoffs=[email_manager],
  input_guardrails=[guardrail_against_abuse],
  model=default_model,
  output_type=ResearchManagerUpdates
)

# async def main():
#   result = await Runner.run(research_manager, f"Query: Best training to learn LLM engineering and Agenting AI", hooks=DeepResearchHooks())
#   print(result)
#   return result.report

# if __name__ == "__main__":
#   result = asyncio.run(main())