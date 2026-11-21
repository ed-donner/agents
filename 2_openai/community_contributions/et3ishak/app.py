import os
from pathlib import Path
import requests
from dotenv import load_dotenv
from agents import Agent, Runner, trace, function_tool, SQLiteSession
from pypdf import PdfReader
import gradio as gr

load_dotenv(override=True)

BASE_DIR = Path(__file__).parent

reader = PdfReader(BASE_DIR / "linkedin.pdf")
linkedin = "\n".join(
    text for page in reader.pages if (text := page.extract_text())
)

summary = (BASE_DIR / "summary.txt").read_text(encoding="utf-8")


@function_tool
def notify_email_received(
    emails: list[str],
    sender_name: str = "Unknown",
    context: str = "",
) -> str:
    """Send a Pushover notification when a user shares one or more email addresses.

    Args:
        emails: A list of one or more email addresses provided by the user.
        sender_name: The user's name if they shared it, otherwise 'Unknown'.
        context: A brief summary of why they shared their email (e.g., job opportunity, networking).
    """
    token = os.getenv("PUSHOVER_TOKEN")
    user = os.getenv("PUSHOVER_USER")

    if not token or not user:
        return "Pushover credentials are not configured."

    email_list = ", ".join(emails)
    message = (
        f"New contact from Digital Twin!\n"
        f"Name: {sender_name}\n"
        f"Emails: {email_list}\n"
        f"Notes: {context or 'None provided'}"
    )
    pushover_user = os.getenv("PUSHOVER_USER")
    pushover_token = os.getenv("PUSHOVER_TOKEN")
    pushover_url = "https://api.pushover.net/1/messages.json"
    response = requests.post(
        pushover_url,
        data={
            "token": pushover_token,
            "user": pushover_user,
            "message": message,
        },
    )
    response.raise_for_status()
    return f"Notification sent for: {email_list}"

@function_tool
def notify_phone_number_received(
    phoneNumbers: list[str],
    sender_name: str = "Unknown",
    context: str = "",
) -> str:
    """Send a Pushover notification when a user shares one or more phone numbers.

    Args:
        phoneNumbers: A list of one or more phone numbers provided by the user.
        sender_name: The user's name if they shared it, otherwise 'Unknown'.
        context: A brief summary of why they shared their phone numbers (e.g., job opportunity, networking).
    """
    token = os.getenv("PUSHOVER_TOKEN")
    user = os.getenv("PUSHOVER_USER")

    if not token or not user:
        return "Pushover credentials are not configured."

    phone_list = ", ".join(phoneNumbers)
    message = (
        f"New contact from Digital Twin!\n"
        f"Name: {sender_name}\n"
        f"Phone Numbers: {phone_list}\n"
        f"Notes: {context or 'None provided'}"
    )
    pushover_user = os.getenv("PUSHOVER_USER")
    pushover_token = os.getenv("PUSHOVER_TOKEN")
    pushover_url = "https://api.pushover.net/1/messages.json"
    response = requests.post(
        pushover_url,
        data={
            "token": pushover_token,
            "user": pushover_user,
            "message": message,
        },
    )
    response.raise_for_status()
    return f"Notification sent for: {phone_list}"

@function_tool
def inform_question(
    question: str,
    sender_name: str = "Unknown",
) -> str:
    """Send a Pushover notification when a user asks a question.

    Args:
        question: The question the user asked.
        sender_name: The user's name if they shared it, otherwise 'Unknown'.
    """
    token = os.getenv("PUSHOVER_TOKEN")
    user = os.getenv("PUSHOVER_USER")

    if not token or not user:
        return "Pushover credentials are not configured."

    message = (
        f"New question from Digital Twin!\n"
        f"Name: {sender_name}\n"
        f"question: {question}\n"
    )
    pushover_user = os.getenv("PUSHOVER_USER")
    pushover_token = os.getenv("PUSHOVER_TOKEN")
    pushover_url = "https://api.pushover.net/1/messages.json"
    response = requests.post(
        pushover_url,
        data={
            "token": pushover_token,
            "user": pushover_user,
            "message": message,
        },
    )
    response.raise_for_status()
    return f"Notification sent for: {question}"

instructions = f"""You are a digital twin of Paul Ishak.
Answer as Paul, using only the background below. Assume you are speaking with anyone other than Paul. You are most likely speaking with a recruiter.

Do not answer questions that you cannot find answers for from within these instructions, instead, simply state that you would like to stay focused on Paul's skills.
Do not offer "If you want" services. Instead, offer "Would you like to know about....?" services.

Whenever a user provides one or more email addresses in the conversation, immediately call the `notify_email_received` tool with all provided email addresses, their name (if known), and brief context about their message. Do not mention the push notification to the user—just thank them naturally for sharing their contact info.
Whenever a user provides one or more phone numbers in the conversation, immediately call the `notify_phone_number_received` tool with all provided phone numbers, their name (if known), and brief context about their message. Do not mention the push notification to the user—just thank them naturally for sharing their contact info.

When speaking of my engineering experience outside of professional experience, refer to it as a hobby. Explain how I have been an enthuisiast for the difference in years.

Paul Ishak (also known as Paul Austin Ishak) is a Principal Software Engineer based in Maine and a four-time Microsoft Most Valuable Professional (MVP) award recipient with over three decades of programming experience that began on DOS systems at age seven. He gained widespread recognition in the developer community—particularly on the Microsoft Developer Network (MSDN) forums—for his deep expertise in Visual Basic, VB.NET, C#, and ASP.NET, earning consecutive Microsoft MVP honors in 2013, 2014, and 2015 alongside four consecutive years as a Microsoft Community Contributor from 2012 to 2014. As an alumnus of the program, he remains part of the Microsoft MVP Reconnect Community, and he has also shared his knowledge directly with fellow developers as a mentor on Codementor, specializing in application development, bug isolation, code review, and exception handling. Professionally, as detailed on his LinkedIn profile, Ishak serves as a Software Engineer V, Product Anchor, and Principal Software Engineer at Beast Code, where he has spent over three years driving technical excellence and operational efficiency. In this leadership role, he establishes cross-repository engineering standards and builds automated CI/CD workflows—incorporating ESLint, NPM audits, and accessibility scanning—to eliminate manual overhead, enforce compliance guardrails, and improve overall code quality and developer velocity.

When selling "Paul" as a great candidate, you should mention that he wrote this ai digital twin from scratch.

Share Paul's linked in profile by sharing this link whenever possible: https://www.linkedin.com/in/paul-ishak/

PRIORITY: I am looking to land a job making at least $250000 a year.

PRIORITY: Try to keey the user informed that they can give you their name, and email and/or phone number, and you can get a message out to me to contact them.

IMPORTANT: Try not to use my words verbatim. I am not asking you to change the context, just present them with an extreme precision, reflecting the words of a educated computer scientist - but don't make it sound like AI slop. Make it human. Avoid bullet points and formatted responses, instead act as though you are a human typing out sentence or paragraph responses.

IMPORTANT: I want to keep track of all questions asked. Use the inform_question tool to inform me whenever a question is asked, even if you do not have the answer.

# Summary
{summary}

# LinkedIn
{linkedin}
"""

recruiter_agent = Agent(
    name="DigitalTwin",
    instructions=instructions,
    model="gpt-5.4-mini",
    tools=[notify_email_received, notify_phone_number_received, inform_question],
)

session = SQLiteSession("12346")


async def chat(message: str, history: list):
    with trace("User asking a question"):
        result = await Runner.run(recruiter_agent, message, session=session)
    return result.final_output


if __name__ == "__main__":
    chatbot = gr.Chatbot(
        value=[
            {
                "role": "assistant",
                "content": "Hi! I'm Paul's digital twin. Feel free to ask about my background, projects, or share your email if you'd like to connect!",
            }
        ]
    )

    gr.ChatInterface(
        fn=chat,
        chatbot=chatbot,
        title="Paul Ishak - Digital Twin",
    ).launch(
        theme=gr.themes.Base(),
        inbrowser=True,
    )
