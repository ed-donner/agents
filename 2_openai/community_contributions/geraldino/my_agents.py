
import os
from typing import Dict

import sendgrid
from sendgrid.helpers.mail import Email, Mail, Content, To
from openai import AsyncOpenAI
from pydantic import BaseModel, Field
from agents import Agent, WebSearchTool, ModelSettings, OpenAIChatCompletionsModel, function_tool

from dotenv import load_dotenv
load_dotenv(override=True) 

# Model clients (OpenRouter) 

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

openrouter_client = AsyncOpenAI(
    base_url=OPENROUTER_BASE_URL,
    api_key=os.environ.get("OPENROUTER_API_KEY"),
)

gemini_model = OpenAIChatCompletionsModel("google/gemini-2.0-flash-001", openai_client=openrouter_client)
deepseek_model = OpenAIChatCompletionsModel("deepseek/deepseek-chat", openai_client=openrouter_client)


# Pydantic schemas 

class RefinedQuery(BaseModel): #  structured output to be used by refiner agent
    original_query: str = Field(description="The original user query, unchanged.")
    refined_query: str = Field(description="A grammatically precise, well-structured research query that best captures the user's intent.")
    refinement_reasoning: str = Field(description="Brief explanation of what was improved and why.")


class WebSearchItem(BaseModel): #  structured output to be used by planner agent
    reason: str = Field(description="Your reasoning for why this search is important to the query.")
    query: str = Field(description="The search term to use for the web search.")


class WebSearchPlan(BaseModel): #  structured output to be used by planner agent
    searches: list[WebSearchItem] = Field(description="A list of web searches to perform to best answer the query.")


class ValidationResult(BaseModel): #  structured output to be used by validator agent
    is_sufficient: bool = Field(description="True if the queries sufficiently cover the refined question, False otherwise.")
    reasoning: str = Field(description="Explanation of why the queries are or are not sufficient.")
    gaps: list[str] = Field(description="List of topics or angles that are missing, if any.")


class ReportData(BaseModel): #  structured output to be used by writer agent
    short_summary: str = Field(description="A short 2-3 sentence summary of the findings.")
    markdown_report: str = Field(description="The final report")
    follow_up_questions: list[str] = Field(description="Suggested topics to research further")


class EvaluationResult(BaseModel): #  structured output to be used by evaluator agent
    score: int = Field(description="A score from 1 to 10 rating the quality of the research.")
    coverage_assessment: str = Field(description="How well did the search queries cover the refined question?")
    quality_assessment: str = Field(description="How thorough and accurate are the search result summaries?")
    alignment_assessment: str = Field(description="How well do the search results align with and answer the refined question?")
    strengths: list[str] = Field(description="What the research did well.")
    weaknesses: list[str] = Field(description="What the research missed or could improve.")
    verdict: str = Field(description="One sentence overall verdict on the research quality.")


# ── Agent definitions 
# Query Refiner Agent: This agent is responsible for refining the user's query into a more specific and focused research question.

HOW_MANY_SEARCHES = 3

query_refiner_agent = Agent(
    name="Query Refiner",
    instructions="""
You are an expert research query specialist. Your job is to take a user's raw question 
and rewrite it into a precise, well-structured research query that will yield the best 
results from a web search planner.

When refining a query:
- Fix grammar and improve clarity
- Add specificity where the original is vague
- Include relevant context (e.g. year, domain, scope)
- Make it actionable for a research agent
- Do NOT change the user's intent — only improve the structure
""",
    model=gemini_model,
    output_type=RefinedQuery,
)


# Web Search Planner Agent: This agent is responsible for planning the web searches needed to answer the research question.
planner_agent = Agent(
    name="PlannerAgent",
    instructions=f"""You are a helpful research assistant. Given a query, come up with a set of web searches 
to perform to best answer the query. Output {HOW_MANY_SEARCHES} terms to query for.

Important rule: Always include at least ONE broad, general search query that captures 
the overall landscape of the topic. The other queries can be more specific.""",
    model="gpt-4o-mini",
    output_type=WebSearchPlan,
)

# Query Validator Agent: This agent is responsible for validating the web searches planned by the planner agent.
validator_agent = Agent(
    name="Query Validator",
    instructions="""
You are a research quality analyst. You are given:
1. A refined research question
2. A set of proposed web search queries from a planner agent

Your job is to evaluate whether the proposed search queries are 
REASONABLY sufficient to answer the refined research question.

Guidelines for your assessment:
- 3 search queries CANNOT cover everything — that is expected and acceptable
- Mark is_sufficient = True if the queries cover the CORE aspects of the question
- Only mark is_sufficient = False if there are CRITICAL missing angles
- Do NOT list minor or nice-to-have gaps as blockers
- Be pragmatic — good enough IS sufficient

Ask yourself: "Would these 3 searches give someone a solid understanding 
of the topic?" If yes, mark True.
""",
    model=deepseek_model,
    output_type=ValidationResult,
)

# Search Agent: This agent is responsible for searching the web for the given search term and returning a concise summary of the results.
search_agent = Agent(
    name="Search agent",
    instructions=(
        "You are a research assistant. Given a search term, you search the web for that term and "
        "produce a concise summary of the results. The summary must 2-3 paragraphs and less than 300 "
        "words. Capture the main points. Write succintly, no need to have complete sentences or good "
        "grammar. This will be consumed by someone synthesizing a report, so its vital you capture the "
        "essence and ignore any fluff. Do not include any additional commentary other than the summary itself. "
        "For every fact, framework or tool you mention, you MUST include the source URL in parentheses "
        "immediately after the mention, like this: (https://example.com). Never omit source links."
    ),
    tools=[WebSearchTool(search_context_size="low")],
    model="gpt-4o-mini",
    model_settings=ModelSettings(tool_choice="required"),
)

# Writer Agent: This agent is responsible for writing a report based on the search results.
writer_agent = Agent(
    name="WriterAgent",
    instructions=(
        "You are a senior researcher tasked with writing a cohesive report for a research query. "
        "You will be provided with the original query, and some initial research done by a research assistant.\n"
        "You should first come up with an outline for the report that describes the structure and "
        "flow of the report. Then, generate the report and return that as your final output.\n"
        "The final output should be in markdown format, and it should be lengthy and detailed. Aim "
        "for 5-10 pages of content, at least 1000 words.\n"
        "Make sure to include: real statistics and analyst predictions where available, "
        "case studies of specific implementations, and cite all sources with links where provided."
    ),
    model="gpt-4o-mini",
    output_type=ReportData,
)


# Research Evaluator Agent: This agent is responsible for evaluating the quality of the research report.
evaluator_agent = Agent(
    name="Research Evaluator",
    instructions="""
You are a senior research quality evaluator with high standards. You will be given:
1. The refined research question
2. The 3 search queries that were used (with their reasoning)
3. The 3 search result summaries that were returned

Your job is to score the research quality from 1 to 10 where:
- 1-3: Poor. Queries were off-target or results were thin and irrelevant
- 4-6: Acceptable. Some coverage but notable gaps or shallow results
- 7-8: Good. Solid coverage, mostly relevant, minor gaps
- 9-10: Excellent. Comprehensive, deeply relevant, well-structured coverage

Be honest and critical. A score of 10 should be rare. Justify your score clearly.
Do NOT suggest reruns — just evaluate what was done.
""",
    model="gpt-4o",
    output_type=EvaluationResult,
)


# Email Agent: This agent is responsible for sending the research report via email.
@function_tool
def send_email(subject: str, html_body: str) -> Dict[str, str]:
    """Send an email with the given subject and HTML body"""
    sg = sendgrid.SendGridAPIClient(api_key=os.environ.get("SENDGRID_API_KEY"))
    from_email = Email("youremail@gmail.com")  # put your verified sender here
    to_email = To("youremail@gmail.com")            # put your recipient here
    content = Content("text/html", html_body)
    mail = Mail(from_email, to_email, subject, content).get()
    response = sg.client.mail.send.post(request_body=mail)
    print("Email response", response.status_code)
    return "success"


email_agent = Agent(
    name="Email agent",
    instructions="""You are able to send a nicely formatted HTML email based on a detailed report.
You will be provided with a detailed report. You should use your tool to send one email, providing the 
report converted into clean, well presented HTML with an appropriate subject line.

CRITICAL RULES — you must follow these exactly:
- Preserve ALL in-text citations and source links exactly as they appear in the report
- Every URL mentioned in the report MUST appear as a clickable hyperlink in the HTML
- Do NOT summarize, shorten, or rewrite any section of the report
- Do NOT remove any statistics, quotes, or referenced facts
- The email must be a faithful HTML conversion of the full report, not a summary""",
    tools=[send_email],
    model="gpt-4o-mini",
)