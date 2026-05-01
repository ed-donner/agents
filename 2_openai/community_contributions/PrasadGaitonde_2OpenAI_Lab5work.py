import os
import asyncio
from typing import Dict, List
from pydantic import BaseModel, Field
import gradio as gr
from dotenv import load_dotenv
import sendgrid
from sendgrid.helpers.mail import Email, Mail, Content, To
from agents import Agent, Runner, WebSearchTool, ModelSettings, function_tool, trace, gen_trace_id

load_dotenv(override=True)

# --- Constants ---
HOW_MANY_SEARCHES = 5

# --- Models ---
class WebSearchItem(BaseModel):
    reason: str = Field(description="Your reasoning for why this search is important to the query.")
    query: str = Field(description="The search term to use for the web search.")

class WebSearchPlan(BaseModel):
    searches: list[WebSearchItem] = Field(description="A list of web searches to perform to best answer the query.")

class ReportData(BaseModel):
    short_summary: str = Field(description="A short 2-3 sentence summary of the findings.")
    markdown_report: str = Field(description="The final report")
    follow_up_questions: list[str] = Field(description="Suggested topics to research further")

class ClarifyingQuestions(BaseModel):
    questions: list[str] = Field(description="Three clarifying questions to better understand the user's research needs.")

# --- Tools ---
@function_tool
def send_email(subject: str, html_body: str) -> Dict[str, str]:
    """Send an email with the given subject and HTML body"""
    sg = sendgrid.SendGridAPIClient(api_key=os.environ.get("SENDGRID_API_KEY"))
    from_email = Email("pgaitond@gmail.com")  # put your verified sender here
    to_email = To("pgaitond@gmail.com")  # put your recipient here
    content = Content("text/html", html_body)
    mail = Mail(from_email, to_email, subject, content).get()
    response = sg.client.mail.send.post(request_body=mail)
    print("Email response", response.status_code)
    return "success"

# --- Specialized Agents ---

# Planner Agent
PLANNER_INSTRUCTIONS = f"You are a helpful research assistant. Given a query and any clarifying answers, come up with a set of web searches \
to perform to best answer the query. Output {HOW_MANY_SEARCHES} terms to query for."

planner_agent = Agent(
    name="PlannerAgent",
    instructions=PLANNER_INSTRUCTIONS,
    model="gpt-4o-mini",
    output_type=WebSearchPlan,
)

# Search Agent
SEARCH_INSTRUCTIONS = (
    "You are a research assistant. Given a search term, you search the web for that term and "
    "produce a concise summary of the results. The summary must 2-3 paragraphs and less than 300 "
    "words. Capture the main points. Write succintly, no need to have complete sentences or good "
    "grammar. This will be consumed by someone synthesizing a report, so its vital you capture the "
    "essence and ignore any fluff. Do not include any additional commentary other than the summary itself."
)

search_agent = Agent(
    name="Search agent",
    instructions=SEARCH_INSTRUCTIONS,
    tools=[WebSearchTool(search_context_size="low")],
    model="gpt-4o-mini",
    model_settings=ModelSettings(tool_choice="required"),
)

# Writer Agent
WRITER_INSTRUCTIONS = (
    "You are a senior researcher tasked with writing a cohesive report for a research query. "
    "You will be provided with the original query and a set of research summaries.\n"
    "You should first come up with an outline for the report that describes the structure and "
    "flow of the report. Then, generate the report and return that as your final output.\n"
    "The final output should be in markdown format, and it should be lengthy and detailed. Aim "
    "for 5-10 pages of content, at least 1000 words."
)

writer_agent = Agent(
    name="WriterAgent",
    instructions=WRITER_INSTRUCTIONS,
    model="gpt-4o-mini",
    output_type=ReportData,
)

# Email Agent
EMAIL_INSTRUCTIONS = """You are able to send a nicely formatted HTML email based on a detailed report.
You will be provided with a detailed report. You should use your tool to send one email, providing the
report converted into clean, well presented HTML with an appropriate subject line."""

email_agent = Agent(
    name="Email agent",
    instructions=EMAIL_INSTRUCTIONS,
    tools=[send_email],
    model="gpt-4o-mini",
)

# Clarification Agent
CLARIFY_INSTRUCTIONS = "Given a user's research query, generate exactly 3 clarifying questions that would help refine the search and provide a better report."
clarify_agent = Agent(
    name="ClarifyAgent",
    instructions=CLARIFY_INSTRUCTIONS,
    model="gpt-4o-mini",
    output_type=ClarifyingQuestions,
)

# --- Research Manager Agent & Tools ---

@function_tool
async def tool_plan_searches(query: str, clarifications: str) -> str:
    """Plan the web searches needed for the query given the user's clarifications."""
    input_text = f"Original Query: {query}\nClarifications: {clarifications}"
    result = await Runner.run(planner_agent, input_text)
    return str(result.final_output)

@function_tool
async def tool_perform_search(search_term: str) -> str:
    """Perform a web search for a specific term and return a summary."""
    result = await Runner.run(search_agent, search_term)
    return str(result.final_output)

@function_tool
async def tool_write_final_report(context: str) -> str:
    """Synthesize all gathered research into a detailed final markdown report."""
    result = await Runner.run(writer_agent, context)
    return str(result.final_output)

@function_tool
async def tool_send_email_report(report_markdown: str) -> str:
    """Send the final report via email."""
    result = await Runner.run(email_agent, report_markdown)
    return "Email sent successfully."

MANAGER_INSTRUCTIONS = (
    "You are the Chief Research Manager. Your goal is to deliver a comprehensive research report.\n"
    "Follow this dynamic process:\n"
    "1. Use `tool_plan_searches` to create a search strategy based on the user query and their clarifications.\n"
    "2. Use `tool_perform_search` for each item in the plan. You can call this multiple times.\n"
    "3. Evaluate the results. If you feel more information is needed, refine the plan and search again.\n"
    "4. Once sufficient information is gathered, use `tool_write_final_report` to synthesize the findings.\n"
    "5. Finally, use `tool_send_email_report` to deliver the result.\n"
    "Always report your progress to the user (e.g., 'I am now planning the searches...', 'Searching for...')."
)

research_manager_agent = Agent(
    name="ResearchManagerAgent",
    instructions=MANAGER_INSTRUCTIONS,
    tools=[tool_plan_searches, tool_perform_search, tool_write_final_report],
    handoffs= [tool_send_email_report],
    model="gpt-4o-mini",
)

class ResearchManager:
    async def generate_questions(self, query: str) -> List[str]:
        """Generate 3 clarifying questions for the user"""
        result = await Runner.run(clarify_agent, f"Query: {query}")
        return result.final_output_as(ClarifyingQuestions).questions

    async def run(self, query: str, answers: str):
        """Run the agentic deep research process"""
        trace_id = gen_trace_id()
        with trace("Agentic Research trace", trace_id=trace_id):
            yield f"View trace: https://platform.openai.com/traces/trace?trace_id={trace_id}"

            input_text = f"User Query: {query}\nUser Clarifications: {answers}"
            # We use the ResearchManager agent to orchestrate the process
            result = await Runner.run(research_manager_agent, input_text)

            # The result of Runner.run will be the final output of the agent.
            # In a tool-using agent, we might want to yield intermediate steps.
            # For this implementation, we'll yield the final output.
            yield result.final_output

# --- Gradio UI ---

async def start_clarification(query: str):
    questions = await ResearchManager().generate_questions(query)
    # We return the questions and a signal to show the clarification UI
    return (
        gr.update(value="", label=questions[0]),
        gr.update(value="", label=questions[1]),
        gr.update(value="", label=questions[2]),
        gr.update(visible=True),
        gr.update(visible=False)
    )

async def run_research(query: str, ans1: str, ans2: str, ans3: str):
    answers = f"Q1: {ans1}\nQ2: {ans2}\nQ3: {ans3}"
    async for chunk in ResearchManager().run(query, answers):
        yield chunk

if __name__ == "__main__":
    with gr.Blocks(theme=gr.themes.Default(primary_hue="sky")) as ui:
        gr.Markdown("# Deep Research (Agentic)")

        with gr.Row():
            query_textbox = gr.Textbox(label="What topic would you like to research?", scale=4)
            run_button = gr.Button("Run", variant="primary", scale=1)

        # Clarification Section
        with gr.Group(visible=False) as clarify_group:
            gr.Markdown("### Please provide more details to refine the research:")
            q1 = gr.Textbox(label="Question 1")
            q2 = gr.Textbox(label="Question 2")
            q3 = gr.Textbox(label="Question 3")
            submit_answers = gr.Button("Submit Answers & Start Research", variant="primary")

        # Results Section
        report_display = gr.Markdown(label="Report")

        # Flow 1: Initial Query -> Questions
        run_button.click(
            fn=start_clarification,
            inputs=query_textbox,
            outputs=[q1, q2, q3, clarify_group, run_button]
        )

        # Flow 2: Answers -> Research
        submit_answers.click(
            fn=run_research,
            inputs=[query_textbox, q1, q2, q3],
            outputs=report_display
        )

    ui.launch(inbrowser=True)
