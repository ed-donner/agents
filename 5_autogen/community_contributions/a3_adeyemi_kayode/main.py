"""
Multi-agent AutoGen chat: Education, Food, and Healthcare interests. 
This is a simple multi-agent chat that uses the SelectorGroupChat to coordinate the agents.
Requires: OPENAI_API_KEY (and the autogen stack from the course venv).
"""

import os

import gradio as gr
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.conditions import MaxMessageTermination, TextMentionTermination
from autogen_agentchat.messages import TextMessage
from autogen_agentchat.teams import SelectorGroupChat
from autogen_ext.models.openai import OpenAIChatCompletionClient
from dotenv import load_dotenv

load_dotenv(override=True)

model_client = OpenAIChatCompletionClient(
    model="gpt-4o-mini",
    api_key=os.environ.get("OPENAI_API_KEY"),
)

education_agent = AssistantAgent(
    name="Education",
    system_message="""You are the Education specialist. You care about learning design, schools, universities,
skills, lifelong learning, accessibility, and how people teach and learn. Offer practical, evidence-minded
ideas. Keep replies to 2–3 short paragraphs unless the user needs detail. Stay in your lane unless asked to integrate.""",
    model_client=model_client,
)

food_agent = AssistantAgent(
    name="Food",
    system_message="""You are the Food & nutrition specialist. You focus on healthy eating patterns, culinary culture,
food security, meal planning, and sustainable food systems. Be clear and non-alarmist. Keep replies concise.
Do not give personalized medical diagnoses—defer clinical questions to Healthcare.""",
    model_client=model_client,
)

healthcare_agent = AssistantAgent(
    name="Healthcare",
    system_message="""You are the Healthcare & wellness specialist. You discuss prevention, public health themes,
mental well-being, and navigating care systems. You are not a substitute for a clinician: remind users to seek
professionals for urgent or personal medical decisions. Keep replies focused and brief.""",
    model_client=model_client,
)

coordinator = AssistantAgent(
    name="Coordinator",
    system_message="""You host the conversation across Education, Food, and Healthcare. After the specialists have
contributed, synthesize themes, flag trade-offs, and suggest next steps. When the discussion is sufficiently
addressed, end your message with the exact word TERMINATE on its own line.""",
    model_client=model_client,
)

termination = TextMentionTermination("TERMINATE") | MaxMessageTermination(max_messages=14)

team = SelectorGroupChat(
    [education_agent, food_agent, healthcare_agent, coordinator],
    model_client=model_client,
    termination_condition=termination,
)


async def chat(user_input: str, history: list):
    if not (user_input or "").strip():
        yield history, ""
        return
    bot_reply = ""
    history = history or []
    history.append((user_input, bot_reply))

    async for event in team.run_stream(task=user_input):
        if isinstance(event, TextMessage):
            bot_reply += f"\n\n**{event.source}**: {event.content}"
            history[-1] = (user_input, bot_reply.strip())
            yield history, ""

    yield history, ""


with gr.Blocks(title="Education · Food · Healthcare — AutoGen") as demo:
    gr.Markdown(
        "## Multi-agent discussion (Education, Food, Healthcare)\n"
        "Ask about learning, meals, wellness, or how they intersect. The **Coordinator** wraps up and may end the turn."
    )
    chatbot = gr.Chatbot(height=420)
    with gr.Column():
        msg = gr.Textbox(
            label="Your question",
            placeholder="E.g., How can a busy student eat better and manage stress during exams?",
            lines=2,
        )
        submit_btn = gr.Button("Submit", variant="primary")

    submit_btn.click(chat, [msg, chatbot], [chatbot, msg])
    msg.submit(chat, [msg, chatbot], [chatbot, msg])

if __name__ == "__main__":
    demo.launch()
