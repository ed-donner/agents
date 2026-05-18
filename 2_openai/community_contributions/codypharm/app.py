"""
Deep Research – Gradio app for Hugging Face Spaces or local run.
Runs the same multi-agent pipeline as week2_exercise.ipynb (clarifier → planner → search → writer → email).
Set OPENAI_API_KEY and optionally RESEND_API_KEY in env or Space Secrets.
"""
import asyncio
import os
from typing import Dict

import gradio as gr
import resend
from dotenv import load_dotenv
from pydantic import BaseModel, Field

from agents import Agent, Runner, WebSearchTool, function_tool
from agents.model_settings import ModelSettings

load_dotenv(override=True)

# --- Config ---
HOW_MANY_SEARCHES = 2
HOW_MANY_CLARIFICATION_QUESTIONS = 3
MAX_TURNS = 30


# --- Pydantic schemas ---
class ClarificationQuestionItems(BaseModel):
    reason: str = Field(description="Your reasoning for why this question is important to the query.")
    question: str = Field(description="The question to ask to get a detailed answer for the query.")


class ClarificationQuestions(BaseModel):
    questions: list[ClarificationQuestionItems] = Field(
        description="A list of clarification questions to ask for the query."
    )


class WebSearchItem(BaseModel):
    reason: str = Field(description="Your reasoning for why this search is important to the query.")
    query: str = Field(description="The search term to use for the web search.")


class WebSearchPlan(BaseModel):
    searches: list[WebSearchItem] = Field(
        description="A list of web searches to perform to best answer the query."
    )


class ReportData(BaseModel):
    short_summary: str = Field(description="A short 2-3 sentence summary of the findings.")
    markdown_report: str = Field(description="The final report.")
    follow_up_questions: list[str] = Field(description="Suggested topics to research further.")


# --- Search agent ---
search_instructions = (
    "You are a research assistant. Given a search term, you search the web for that term and "
    "produce a concise summary of the results. The summary must 2-3 paragraphs and less than 300 "
    "words. Capture the main points. Write succinctly. This will be consumed by someone "
    "synthesizing a report, so capture the essence and ignore any fluff."
)
search_agent = Agent(
    name="Search agent",
    instructions=search_instructions,
    tools=[WebSearchTool(search_context_size="low")],
    model="gpt-4o-mini",
    model_settings=ModelSettings(tool_choice="required"),
)
search_tool = search_agent.as_tool(tool_name="search_tool", tool_description="Search the web for a query")


# --- Clarification & planner ---
planner_agent = Agent(
    name="PlannerAgent",
    instructions=(
        f"You are a helpful research assistant. Given a set of questions, come up with web searches "
        f"to perform to best answer them. Output {HOW_MANY_SEARCHES} terms to query for."
    ),
    model="gpt-4o-mini",
    output_type=WebSearchPlan,
)
clarification_agent = Agent(
    name="ClarificationAgent",
    instructions=(
        f"You are a senior researcher. Given a query, come up with clarification questions "
        f"to get a detailed answer. Output {HOW_MANY_CLARIFICATION_QUESTIONS} questions."
    ),
    model="gpt-4o-mini",
    output_type=ClarificationQuestions,
)
clarifier_tool = clarification_agent.as_tool(
    tool_name="clarifier_tool",
    tool_description="Generate clarification questions for a query",
)
planner_tool = planner_agent.as_tool(
    tool_name="planner_tool",
    tool_description="Generate web searches for clarification questions from the clarifier.",
)


# --- Email tool (Resend) ---
@function_tool
def send_email(subject: str, html_body: str) -> Dict[str, str]:
    """Send an email with the given subject and HTML body."""
    resend.api_key = os.environ.get("RESEND_API_KEY")
    if not resend.api_key:
        return {"error": "RESEND_API_KEY not set"}
    params = {
        "from": "onboarding@resend.dev",
        "to": [os.environ.get("RESEND_TO_EMAIL", "williamikeji@gmail.com")],
        "subject": subject,
        "html": html_body,
    }
    resend.Emails.send(params)
    return {"status": "success"}


email_agent = Agent(
    name="Email agent",
    instructions=(
        "You send a nicely formatted HTML email from a detailed report. "
        "Use your tool to send one email: convert the report to clean HTML and set an appropriate subject."
    ),
    tools=[send_email],
    model="gpt-4o-mini",
)
email_tool = email_agent.as_tool(
    tool_name="email_tool",
    tool_description="Send an email with the report as clean, well-formatted HTML and a clear subject line.",
)
reporter_tools = [email_tool]


# --- Writer agent ---
writer_instructions = (
    "You are a senior researcher assistant. You receive the original query and research from the team. "
    "First, create an outline for the report (structure and flow). "
    "Then write the full report in markdown: detailed, 1000+ words. "
    "Finally, use the email tool to send the report: convert your markdown to clean HTML for the email body "
    "and choose a clear subject line. Send exactly one email with the full report."
)
writer_agent = Agent(
    name="WriterAgent",
    instructions=writer_instructions,
    model="gpt-4o-mini",
    tools=reporter_tools,
    output_type=ReportData,
    handoff_description="Write the report and send it to the recipient using the email tool.",
)


# --- Manager agent ---
# Strict sequence so planner runs once and search runs exactly HOW_MANY_SEARCHES times
manager_agent = Agent(
    name="ManagerAgent",
    instructions=(
        "You are a research lab manager. You will be provided with a query. Follow this sequence exactly:\n"
        "1. Call clarifier_tool **once** with the query. You get back clarification questions.\n"
        "2. Call planner_tool **once** with those questions. You get back a list of exactly "
        f"{HOW_MANY_SEARCHES} search terms.\n"
        f"3. Call search_tool **exactly {HOW_MANY_SEARCHES} times** — once per search term from the planner. "
        "Do not call the planner again. Do not call search_tool more than "
        f"{HOW_MANY_SEARCHES} times.\n"
        "4. After you have exactly "
        f"{HOW_MANY_SEARCHES} search results, hand off to the writer agent once with all the research. "
        "Do not hand off before all searches are done."
    ),
    tools=[clarifier_tool, planner_tool, search_tool],
    model="gpt-4o-mini",
    handoffs=[writer_agent],
)


async def run_research(query: str) -> str:
    """Run the deep research pipeline and return a message for the UI."""
    if not query or not query.strip():
        return "Please enter a research query."
    try:
        result = await Runner.run(manager_agent, query.strip(), max_turns=MAX_TURNS)
        # Result may be ReportData, an object with final_output, or a string
        if hasattr(result, "markdown_report"):
            preview = result.markdown_report[:8000] + ("..." if len(result.markdown_report) > 8000 else "")
            return f"**Report sent by email.**\n\n**Summary:** {getattr(result, 'short_summary', '')}\n\n---\n\n**Report preview:**\n\n{preview}"
        if hasattr(result, "final_output"):
            return str(result.final_output) if result.final_output else "Research complete. Report sent by email (if configured)."
        if isinstance(result, str):
            return result
        return "Research complete. If RESEND_API_KEY is set, the report was sent by email."
    except Exception as e:
        return f"Error: {e}"


def run_research_sync(query: str, progress=gr.Progress()) -> str:
    """Sync wrapper for Gradio; progress shows loading while the pipeline runs."""
    if not query or not query.strip():
        return "Please enter a research query."
    progress(0, desc="Running research pipeline (clarifier → planner → search → writer → email)...")
    try:
        result = asyncio.run(run_research(query))
        progress(1.0, desc="Done")
        return result
    except Exception as e:
        progress(1.0, desc="Done")
        return f"Error: {e}"


# --- Gradio UI ---
with gr.Blocks(title="Deep Research – Codypharm", theme=gr.themes.Soft()) as demo:
    gr.Markdown(
        "## Deep Research\n"
        "Enter a topic. The pipeline will: clarify the query → plan searches → search the web → "
        "write a report → email it (if Resend is configured)."
    )
    query_in = gr.Textbox(
        label="Research query",
        placeholder="e.g. Latest AI agent frameworks in 2025",
        lines=2,
    )
    run_btn = gr.Button("Run deep research", variant="primary")
    out = gr.Markdown(label="Result")
    run_btn.click(fn=run_research_sync, inputs=query_in, outputs=out)

demo.launch()
