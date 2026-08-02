import os
import gradio as gr
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.teams import SelectorGroupChat
from autogen_agentchat.conditions import MaxMessageTermination, TextMentionTermination
from autogen_agentchat.messages import TextMessage
from autogen_ext.models.openai import OpenAIChatCompletionClient
from langchain_community.tools.tavily_search import TavilySearchResults
from dotenv import load_dotenv
import requests

load_dotenv(override=True)

tavily_search = TavilySearchResults(
    api_key=os.environ.get("TAVILY_API_KEY"),
    max_results=5
)

async def fetch_market_data(query: str) -> str:
    """Fetches market data using the Tavily Search tool."""
    try:
        print(f"--- [Tool Call] Fetching market data for: '{query}' ---")
        results = await tavily_search.arun(query)
        return results
    except Exception as e:
        print(f"Error fetching market data: {e}")
        return "Error fetching market data."

async def send_email(subject: str, body: str) -> str:
    """Sends a final email summary of the meeting to the founder."""
    try:
        print(f"--- [Tool Call] Sending email with subject: '{subject}' ---")
        response = requests.post(
            "https://api.go-mailer.com/v1/transactionals",
            json={
                "template_code": "TEST_EMAIL",
                "recipient_email": "adisco4420@gmail.com",
                "data": {"email_subject": subject},
                "html": body
            },
            headers={
                "Authorization": f"Bearer {os.environ.get('GOMAILER_API_KEY')}"
            }
        )
        if response.status_code == 200:
            return "Email sent successfully."
        else:
            return f"Failed to send email. Status code: {response.status_code}"
    except Exception as e:
        print(f"Error sending email: {e}")
        return f"Error sending email: {e}"


model_client = OpenAIChatCompletionClient(
    model="gpt-4o-mini",
    api_key=os.environ.get("OPENAI_API_KEY")
)

visionary = AssistantAgent(
    name="Visionary_CEO",
    system_message="You are the Visionary CEO. Drive the product vision. Keep responses to 2 short paragraphs.",
    model_client=model_client
)

engineer = AssistantAgent(
    name="Lead_Engineer",
    system_message="You are the pragmatic Lead Engineer. Question the technical feasibility and security. Keep responses short.",
    model_client=model_client
)

cfo = AssistantAgent(
    name="CFO",
    system_message="You are the strict CFO. Use the fetch_market_data tool to validate the financial viability of the pitch before speaking.",
    tools=[fetch_market_data],
    model_client=model_client
)

secretary = AssistantAgent(
    name="Secretary",
    system_message="""You are the board secretary. Wait until the others have debated, then summarize the meeting.
    
    Your task is to:
    1. Generate a concise and professional subject line for the meeting summary.
    2. Create a clean, well-formatted HTML email body. Use <h2> for section headers, <ul>/<li> for bullet points, and <b> for emphasis.
    3. Use the `send_email` tool to send the subject and HTML body.
    
    After the tool succeeds, end your message with the exact word TERMINATE.""",
    tools=[send_email],
    model_client=model_client
)

termination = TextMentionTermination("TERMINATE") | MaxMessageTermination(max_messages=10)

team = SelectorGroupChat(
    [visionary, engineer, cfo, secretary],
    model_client=model_client,
    termination_condition=termination
)


async def chat(user_input, history):
    bot_reply = ""
    history.append((user_input, bot_reply))
    
    async for event in team.run_stream(task=user_input):
        if isinstance(event, TextMessage):
            bot_reply += f"\n\n**{event.source}**: {event.content}"
            history[-1] = (user_input, bot_reply.strip())
            yield history, ""


with gr.Blocks(title="AI Startup Boardroom") as demo:
    gr.Markdown("## Pitch Your Startup Idea")
    gr.Markdown("The Visionary, Engineer, and CFO will debate your idea. The Secretary will email you the final summary.")
    
    chatbot = gr.Chatbot()
    msg = gr.Textbox(placeholder="E.g., An AI agent that auto-reconciles vendor invoices for local businesses...")
    
    msg.submit(chat, [msg, chatbot], [chatbot, msg])

if __name__ == "__main__":
    demo.launch()