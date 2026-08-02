import os
import asyncio
import gradio as gr
import httpx
from dotenv import load_dotenv

from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.teams import SelectorGroupChat
from autogen_agentchat.conditions import MaxMessageTermination, TextMentionTermination
from autogen_agentchat.messages import TextMessage
from autogen_ext.models.openai import OpenAIChatCompletionClient

from langchain_community.tools.tavily_search import TavilySearchResults


#  CONFIG
load_dotenv(override=True)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
GOMAILER_API_KEY = os.getenv("GOMAILER_API_KEY")

DEFAULT_EMAIL = os.getenv("DEFAULT_RECIPIENT_EMAIL", "")


#  TOOL: Market Research
tavily_search = TavilySearchResults(api_key=TAVILY_API_KEY, max_results=5)


async def fetch_market_data(query: str) -> str:
    """Fetch market & competitive intelligence with retry + fallback."""
    print(f"[TOOL] Market Data Query: {query}")

    for attempt in range(2):
        try:
            # Try async first
            if hasattr(tavily_search, "arun"):
                result = await tavily_search.arun(query)
            else:
                # fallback sync → thread
                result = await asyncio.to_thread(tavily_search.run, query)

            return f"[Market Intelligence]\n{result}"

        except Exception as e:
            if attempt == 1:
                return f"[ERROR] Market data failed: {e}"

    return "[ERROR] Market data unavailable"


#  TOOL: Send Email (ASYNC SAFE)
async def send_email(subject: str, body: str, recipient: str) -> str:
    """Send email with retry + timeout."""
    print(f"[TOOL] Sending email to {recipient}")

    if not recipient:
        return "[ERROR] No recipient email provided."

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                "https://api.go-mailer.com/v1/transactionals",
                json={
                    "template_code": "TEST_EMAIL",
                    "recipient_email": recipient,
                    "data": {"email_subject": subject},
                    "html": body,
                },
                headers={"Authorization": f"Bearer {GOMAILER_API_KEY}"},
            )

        if response.status_code == 200:
            return "Email sent successfully."
        return f"[ERROR] Email failed: {response.status_code}"

    except Exception as e:
        return f"[ERROR] Email exception: {e}"


#  MODEL CLIENT
model_client = OpenAIChatCompletionClient(model="gpt-4o-mini", api_key=OPENAI_API_KEY)


# AGENTS

analyst = AssistantAgent(
    name="Market_Analyst",
    system_message="""
    You are a Market Analyst.
    - Identify target market, competitors, and trends.
    - Be concise and data-driven.
    - Do NOT hallucinate numbers.
    """,
    tools=[fetch_market_data],
    model_client=model_client,
)

risk_officer = AssistantAgent(
    name="Risk_Officer",
    system_message="""
    You are a Risk Officer.
    - Identify financial, operational, and market risks.
    - Be skeptical and realistic.
    """,
    model_client=model_client,
)

portfolio_manager = AssistantAgent(
    name="Portfolio_Manager",
    system_message="""
    You are the Portfolio Manager.
    - Make the final INVEST / PASS decision.
    - Justify based on risk vs return.
    - Be decisive.
    """,
    model_client=model_client,
)

cfo = AssistantAgent(
    name="CFO",
    system_message="""
    You are the CFO.

    MANDATORY RULE:
    - You MUST call fetch_market_data before giving ANY financial opinion.

    Tasks:
    - Validate revenue potential, pricing, and market size.
    - Challenge unrealistic assumptions.
    """,
    tools=[fetch_market_data],
    model_client=model_client,
)

secretary = AssistantAgent(
    name="Investment_Secretary",
    system_message="""
    You are the Investment Committee Secretary.

    Wait for all agents to speak, then:

    1. Create a professional subject line.
    2. Generate HTML report:
    - <h2> sections
    - bullet points
    - clear verdict

    3. Call send_email with:
    - subject
    - HTML body
    - recipient email

    End with: TERMINATE
    """,
    tools=[send_email],
    model_client=model_client,
)


# TEAM SETUP
termination = TextMentionTermination("TERMINATE") | MaxMessageTermination(15)

team = SelectorGroupChat(
    [analyst, cfo, risk_officer, portfolio_manager, secretary],
    model_client=model_client,
    termination_condition=termination,
)


#  CHAT LOGIC
async def chat(user_input, history, email):
    history.append((user_input, ""))

    async for event in team.run_stream(
        task=f"""
        Startup Pitch:
        {user_input}

        Recipient Email: {email}
        """
    ):
        if isinstance(event, TextMessage):
            formatted = f"\n\n🔹 **{event.source}**:\n{event.content}"
            history[-1] = (user_input, history[-1][1] + formatted)
            yield history, "", email


# UI (GRADIO)
with gr.Blocks(title="AI Investment Committee") as demo:
    gr.Markdown("#  AI Investment Committee")
    gr.Markdown(
        "Pitch your startup. A full investment committee will evaluate and email you a decision."
    )

    chatbot = gr.Chatbot()

    with gr.Row():
        msg = gr.Textbox(
            placeholder="E.g., AI tool for automating SME bookkeeping in Africa..."
        )
        email = gr.Textbox(
            placeholder="Enter your email for the report...", value=DEFAULT_EMAIL
        )

    msg.submit(chat, [msg, chatbot, email], [chatbot, msg, email])

#  RUN
if __name__ == "__main__":
    demo.launch()
