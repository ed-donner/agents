from agents import Agent, WebSearchTool, Runner, trace, function_tool
from agents.model_settings import ModelSettings
from pydantic import BaseModel, Field
from dotenv import load_dotenv
import asyncio
import gradio as gr
import requests
import sendgrid
import os

load_dotenv(override=True)

# ---------------------------------------------------------------------------
# Pydantic models (structured outputs)
# ---------------------------------------------------------------------------

class WebSearchItem(BaseModel):
    reason: str = Field(description="Why this search angle matters for validating the idea.")
    query: str = Field(description="The search term to use.")


class WebSearchPlan(BaseModel):
    searches: list[WebSearchItem] = Field(
        description="Exactly 5 web searches covering market size, competitors, funding, demand signals, and barriers."
    )


class StartupValidation(BaseModel):
    verdict: str = Field(
        description="One of: 'High Potential', 'Proceed with Caution', or 'Crowded Market'."
    )
    confidence: int = Field(description="Confidence in the verdict from 1 (low) to 10 (high).")
    market_size: str = Field(description="Estimated TAM, e.g. '$4.2B by 2027'.")
    top_competitors: list[str] = Field(description="Names of the most relevant existing players.")
    similar_funded_startups: list[str] = Field(
        description="Recently funded startups tackling a similar problem."
    )
    key_risks: list[str] = Field(description="The biggest risks this idea faces.")
    key_opportunities: list[str] = Field(description="The strongest opportunities or tailwinds.")
    what_would_need_to_be_true: list[str] = Field(
        description="VC-style beliefs that must hold for this idea to succeed."
    )
    recommendation: str = Field(description="A concise final recommendation paragraph.")


class ReportData(BaseModel):
    short_summary: str = Field(description="A 2-3 sentence summary of the findings.")
    markdown_report: str = Field(description="The full report in markdown.")
    follow_up_questions: list[str] = Field(description="Suggested areas to research further.")


# ---------------------------------------------------------------------------
# Agents
# ---------------------------------------------------------------------------

NUM_SEARCHES = 5

planner_agent = Agent(
    name="PlannerAgent",
    instructions=(
        "You are a startup validation strategist. Given a startup idea, generate exactly "
        f"{NUM_SEARCHES} web search queries to validate it. Each query must target a distinct "
        "angle:\n"
        "1. Market size / TAM for the problem space\n"
        "2. Existing competitors and alternatives\n"
        "3. Recent funding rounds or acquisitions in the space\n"
        "4. Customer pain points, demand signals, or forum discussions\n"
        "5. Regulatory, technical, or adoption barriers\n\n"
        "Make queries specific and current (include the current year when relevant)."
    ),
    model="gpt-4o-mini",
    output_type=WebSearchPlan,
)

search_agent = Agent(
    name="SearchAgent",
    instructions=(
        "You are a research assistant. Given a search term, search the web and produce a "
        "concise summary of the results. The summary must be 2-3 paragraphs and under 300 "
        "words. Capture concrete data points — numbers, company names, dates, dollar amounts. "
        "Write succinctly; this will be consumed by an analyst, so capture the essence and "
        "skip the fluff. Do not add commentary beyond the summary."
    ),
    tools=[WebSearchTool(search_context_size="low")],
    model="gpt-4o-mini",
    model_settings=ModelSettings(tool_choice="required"),
)

analyst_agent = Agent(
    name="AnalystAgent",
    instructions=(
        "You are a startup analyst at a top-tier VC firm. Given the original startup idea and "
        "a set of research summaries, produce a structured viability assessment.\n\n"
        "Rules:\n"
        "- Be brutally honest. Founders deserve the truth.\n"
        "- Ground every claim in the research provided — do not invent data.\n"
        "- If data is missing or inconclusive, say so and lower your confidence score.\n"
        "- The 'what_would_need_to_be_true' field is critical: list the assumptions that must "
        "hold for this startup to reach product-market fit and scale.\n"
        "- Verdict must be exactly one of: 'High Potential', 'Proceed with Caution', "
        "or 'Crowded Market'."
    ),
    model="gpt-4o-mini",
    output_type=StartupValidation,
)

writer_agent = Agent(
    name="WriterAgent",
    instructions=(
        "You are a senior analyst writing a polished startup validation report. You will "
        "receive the original idea and a structured validation object.\n\n"
        "Write a detailed markdown report with these sections:\n"
        "1. **Executive Summary** — verdict, confidence, and one-paragraph recommendation\n"
        "2. **Market Analysis** — TAM, growth drivers, timing\n"
        "3. **Competitive Landscape** — key players, their strengths, white space\n"
        "4. **Funding Activity** — recent rounds, acqui-hires, signals\n"
        "5. **Risks & Opportunities** — side by side\n"
        "6. **What Would Need to Be True** — the beliefs required for success\n"
        "7. **Recommendation & Next Steps**\n\n"
        "Aim for at least 800 words. Use concrete data from the validation object."
    ),
    model="gpt-4o-mini",
    output_type=ReportData,
)

EMAIL_INSTRUCTIONS = (
    "You are able to send a nicely formatted HTML email based on a detailed report. "
    "You will be provided with a detailed report. Use your tool to send one email, "
    "providing the report converted into clean, well-presented HTML with an appropriate "
    "subject line."
)


# ---------------------------------------------------------------------------
# Optional delivery tools
# ---------------------------------------------------------------------------

def push(text: str):
    """Send a Pushover notification."""
    requests.post(
        "https://api.pushover.net/1/messages.json",
        data={
            "token": os.getenv("PUSHOVER_TOKEN"),
            "user": os.getenv("PUSHOVER_USER"),
            "message": text,
        },
    )


def build_email_agent():
    """Build the email agent only when SendGrid credentials are available."""
    @function_tool
    def send_email_tool(subject: str, html_body: str) -> str:
        """Send an HTML email via SendGrid."""
        sg = sendgrid.SendGridAPIClient(api_key=os.environ.get("SENDGRID_API_KEY"))
        from sendgrid.helpers.mail import Mail, Email, To, Content

        from_email = Email(os.environ.get("SENDGRID_FROM_EMAIL", "noreply@example.com"))
        to_email = To(os.environ.get("SENDGRID_TO_EMAIL", "noreply@example.com"))
        content = Content("text/html", html_body)
        mail = Mail(from_email, to_email, subject, content).get()
        sg.client.mail.send.post(request_body=mail)
        return "success"

    return Agent(
        name="EmailAgent",
        instructions=EMAIL_INSTRUCTIONS,
        tools=[send_email_tool],
        model="gpt-4o-mini",
    )


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------

async def plan_searches(idea: str) -> WebSearchPlan:
    result = await Runner.run(planner_agent, f"Startup idea: {idea}")
    return result.final_output


async def search(item: WebSearchItem) -> str:
    input_text = f"Search term: {item.query}\nReason: {item.reason}"
    result = await Runner.run(search_agent, input_text)
    return result.final_output


async def perform_searches(plan: WebSearchPlan) -> list[str]:
    tasks = [asyncio.create_task(search(item)) for item in plan.searches]
    return await asyncio.gather(*tasks)


async def analyze(idea: str, search_results: list[str]) -> StartupValidation:
    input_text = (
        f"Startup idea: {idea}\n\n"
        f"Research summaries:\n" + "\n---\n".join(search_results)
    )
    result = await Runner.run(analyst_agent, input_text)
    return result.final_output


async def write_report(idea: str, validation: StartupValidation) -> ReportData:
    input_text = (
        f"Startup idea: {idea}\n\n"
        f"Structured validation data:\n{validation.model_dump_json(indent=2)}"
    )
    result = await Runner.run(writer_agent, input_text)
    return result.final_output


async def deliver_email(report: ReportData):
    email_agent = build_email_agent()
    await Runner.run(email_agent, report.markdown_report)


def deliver_pushover(validation: StartupValidation):
    msg = (
        f"Startup Validator Result\n"
        f"Verdict: {validation.verdict} ({validation.confidence}/10)\n"
        f"Market: {validation.market_size}\n"
        f"Recommendation: {validation.recommendation[:200]}"
    )
    push(msg)


async def validate_startup(idea: str):
    """Full pipeline: plan -> search -> analyze -> write -> deliver."""
    with trace("Startup Validation"):
        search_plan = await plan_searches(idea)
        search_results = await perform_searches(search_plan)
        validation = await analyze(idea, search_results)
        report = await write_report(idea, validation)

        if os.getenv("SENDGRID_API_KEY"):
            await deliver_email(report)
        if os.getenv("PUSHOVER_TOKEN"):
            deliver_pushover(validation)

        return validation, report


# ---------------------------------------------------------------------------
# Gradio UI
# ---------------------------------------------------------------------------

def build_summary_html(v: StartupValidation) -> str:
    """Render the structured verdict as an HTML summary card."""
    color_map = {
        "High Potential": "#22c55e",
        "Proceed with Caution": "#eab308",
        "Crowded Market": "#ef4444",
    }
    color = color_map.get(v.verdict, "#6b7280")

    competitors = "".join(f"<li>{c}</li>" for c in v.top_competitors[:5])
    risks = "".join(f"<li>{r}</li>" for r in v.key_risks[:5])
    opportunities = "".join(f"<li>{o}</li>" for o in v.key_opportunities[:5])
    beliefs = "".join(f"<li>{b}</li>" for b in v.what_would_need_to_be_true[:5])
    funded = "".join(f"<li>{s}</li>" for s in v.similar_funded_startups[:5])

    return f"""
    <div style="font-family: system-ui, sans-serif; max-width: 800px; margin: 0 auto; color: #1a1a1a;">
      <div style="display: flex; align-items: center; gap: 16px; margin-bottom: 20px; flex-wrap: wrap;">
        <div style="background: {color}; color: white; font-weight: 700; font-size: 1.1rem;
                    padding: 10px 20px; border-radius: 8px;">
          {v.verdict}
        </div>
        <div style="font-size: 1.5rem; font-weight: 700; color: #f0f0f0;">
          Confidence: {v.confidence}<span style="font-size:0.9rem; opacity:0.6">/10</span>
        </div>
        <div style="margin-left: auto; background: #f3f4f6; color: #1a1a1a; padding: 8px 16px; border-radius: 8px;">
          TAM: <strong>{v.market_size}</strong>
        </div>
      </div>

      <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-bottom: 20px;">
        <div style="background: #fef2f2; color: #450a0a; padding: 16px; border-radius: 8px;">
          <h4 style="margin: 0 0 8px; color: #991b1b;">Key Risks</h4>
          <ul style="margin: 0; padding-left: 18px; font-size: 0.9rem;">{risks}</ul>
        </div>
        <div style="background: #f0fdf4; color: #052e16; padding: 16px; border-radius: 8px;">
          <h4 style="margin: 0 0 8px; color: #166534;">Opportunities</h4>
          <ul style="margin: 0; padding-left: 18px; font-size: 0.9rem;">{opportunities}</ul>
        </div>
      </div>

      <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-bottom: 20px;">
        <div style="background: #f8fafc; color: #1e293b; padding: 16px; border-radius: 8px; border: 1px solid #e2e8f0;">
          <h4 style="margin: 0 0 8px; color: #0f172a;">Top Competitors</h4>
          <ul style="margin: 0; padding-left: 18px; font-size: 0.9rem;">{competitors}</ul>
        </div>
        <div style="background: #f8fafc; color: #1e293b; padding: 16px; border-radius: 8px; border: 1px solid #e2e8f0;">
          <h4 style="margin: 0 0 8px; color: #0f172a;">Recently Funded</h4>
          <ul style="margin: 0; padding-left: 18px; font-size: 0.9rem;">{funded}</ul>
        </div>
      </div>

      <div style="background: #fffbeb; color: #451a03; padding: 16px; border-radius: 8px; border: 1px solid #fde68a; margin-bottom: 20px;">
        <h4 style="margin: 0 0 8px; color: #92400e;">What Would Need to Be True</h4>
        <ul style="margin: 0; padding-left: 18px; font-size: 0.9rem;">{beliefs}</ul>
      </div>

      <div style="background: #f0f9ff; color: #0c4a6e; padding: 16px; border-radius: 8px; border: 1px solid #bae6fd;">
        <h4 style="margin: 0 0 8px; color: #075985;">Recommendation</h4>
        <p style="margin: 0; font-size: 0.95rem;">{v.recommendation}</p>
      </div>
    </div>
    """


async def run_validation(idea: str):
    if not idea or not idea.strip():
        return "Please enter a startup idea.", "", ""
    validation, report = await validate_startup(idea.strip())
    summary_html = build_summary_html(validation)
    return summary_html, report.markdown_report, report.short_summary


with gr.Blocks(
    title="Startup Idea Validator",
    theme=gr.themes.Soft(),
) as demo:
    gr.Markdown(
        "# Startup Idea Validator\n"
        "Enter a startup idea in one sentence. The agent pipeline will research the market, "
        "analyze competitors, assess risks, and deliver a structured verdict."
    )

    with gr.Row():
        idea_input = gr.Textbox(
            label="Your Startup Idea",
            placeholder="e.g. An AI-powered meal planning app for people with dietary restrictions",
            lines=2,
            scale=4,
        )
        validate_btn = gr.Button("Validate", variant="primary", scale=1)

    summary_text = gr.Textbox(label="Quick Summary", interactive=False, lines=2)

    gr.Markdown("## Verdict")
    summary_card = gr.HTML()

    gr.Markdown("## Full Report")
    report_output = gr.Markdown()

    validate_btn.click(
        fn=run_validation,
        inputs=[idea_input],
        outputs=[summary_card, report_output, summary_text],
    )
    idea_input.submit(
        fn=run_validation,
        inputs=[idea_input],
        outputs=[summary_card, report_output, summary_text],
    )


if __name__ == "__main__":
    demo.launch()
