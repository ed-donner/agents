from dotenv import load_dotenv
from openai import OpenAI
import json
import os
import requests
from pypdf import PdfReader
import gradio as gr
from pydantic import BaseModel


load_dotenv(override=True)

APP_CSS = """
/* ============================================================
   Google Fonts – Inter for clean, modern typography
   ============================================================ */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

/* ============================================================
   Design Tokens
   ============================================================ */
:root {
  --surface: #f5f1ea;
  --surface-strong: #ffffff;
  --accent: #0e7c86;
  --accent-dark: #0a5c63;
  --accent-soft: #e0f3f1;
  --accent-glow: rgba(14, 124, 134, 0.12);
  --ink: #1a1a2e;
  --ink-secondary: #2d3748;
  --muted: #4a5568;
  --edge: rgba(14, 124, 134, 0.18);
  --radius-lg: 22px;
  --radius-md: 16px;
  --radius-sm: 12px;
  --shadow-sm: 0 4px 14px rgba(0, 0, 0, 0.06);
  --shadow-md: 0 12px 32px rgba(14, 124, 134, 0.10);
  --shadow-lg: 0 20px 60px rgba(14, 124, 134, 0.15);
}

/* ============================================================
   Animations
   ============================================================ */
@keyframes fadeInUp {
  from { opacity: 0; transform: translateY(16px); }
  to   { opacity: 1; transform: translateY(0); }
}

@keyframes shimmer {
  0%   { background-position: -200% 0; }
  100% { background-position: 200% 0; }
}

/* ============================================================
   Global Styles
   ============================================================ */
body, .gradio-container {
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif !important;
  background:
    radial-gradient(ellipse at 10% 0%, rgba(14, 124, 134, 0.08) 0%, transparent 50%),
    radial-gradient(ellipse at 90% 0%, rgba(250, 204, 140, 0.12) 0%, transparent 40%),
    radial-gradient(ellipse at 50% 100%, rgba(14, 124, 134, 0.05) 0%, transparent 50%),
    linear-gradient(180deg, #f0ece4 0%, #f6f3ed 40%, #faf8f4 100%);
  color: var(--ink) !important;
}

/* ============================================================
   App Shell
   ============================================================ */
.app-shell {
  max-width: 1300px;
  margin: 0 auto;
  padding: 0 16px;
  animation: fadeInUp 0.5s ease-out;
}

/* ============================================================
   Hero Card
   ============================================================ */
.hero-card {
  background:
    linear-gradient(135deg, #0a5c63 0%, #0e7c86 40%, #11959f 70%, #0e7c86 100%);
  color: #ffffff;
  border-radius: var(--radius-lg);
  padding: 32px 34px 26px 34px;
  box-shadow: var(--shadow-lg);
  position: relative;
  overflow: hidden;
}

.hero-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(
    90deg,
    transparent 0%,
    rgba(255, 255, 255, 0.06) 40%,
    rgba(255, 255, 255, 0.12) 50%,
    rgba(255, 255, 255, 0.06) 60%,
    transparent 100%
  );
  background-size: 200% 100%;
  animation: shimmer 6s ease-in-out infinite;
  pointer-events: none;
}

.hero-card h1 {
  margin: 0 0 10px 0;
  font-size: 2.4rem;
  font-weight: 800;
  letter-spacing: -0.03em;
  color: #ffffff !important;
  text-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
}

.hero-card p {
  margin: 0;
  max-width: 780px;
  line-height: 1.65;
  font-size: 1.05rem;
  font-weight: 400;
  color: rgba(255, 255, 255, 0.95) !important;
}

/* ============================================================
   Panel Cards (status, feedback, etc.)
   ============================================================ */
.panel-card {
  background: var(--surface-strong) !important;
  border: 1.5px solid var(--edge) !important;
  border-radius: var(--radius-lg) !important;
  padding: 20px 22px !important;
  box-shadow: var(--shadow-md) !important;
  animation: fadeInUp 0.6s ease-out;
}

/* Force ALL text inside panels to be dark and readable */
.panel-card,
.panel-card *,
.panel-card h1, .panel-card h2, .panel-card h3,
.panel-card h4, .panel-card h5, .panel-card h6,
.panel-card p, .panel-card li, .panel-card span,
.panel-card strong, .panel-card em, .panel-card code {
  color: var(--ink) !important;
}

.panel-card h3 {
  font-size: 1.1rem !important;
  font-weight: 700 !important;
  margin-bottom: 8px !important;
}

.panel-card li {
  font-size: 0.95rem !important;
  line-height: 1.6 !important;
}

.panel-card code {
  background: var(--accent-soft) !important;
  padding: 2px 7px !important;
  border-radius: 6px !important;
  font-size: 0.88rem !important;
  font-weight: 600 !important;
  color: var(--accent-dark) !important;
}

/* ============================================================
   Chatbot Column
   ============================================================ */
.chatbot-shell {
  overflow: visible;
}

.chatbot-shell .wrap {
  border-radius: var(--radius-lg);
}

/* Force chatbot container and messages area to have a light background */
.chatbot-shell .chatbot,
.chatbot-shell .chatbot > div,
.chatbot-shell .messages-wrapper,
.chatbot-shell .message-wrap,
.chatbot-shell [class*="chatbot"],
.chatbot-shell [data-testid="chatbot"],
.chatbot-shell [role="log"],
.chatbot-shell .wrap,
.chatbot-shell .wrap > div {
  background: #ffffff !important;
  background-color: #ffffff !important;
}

/* Ensure chatbot messages have readable dark text */
.chatbot-shell .message,
.chatbot-shell .message *,
.chatbot-shell .bot,
.chatbot-shell .bot *,
.chatbot-shell .user,
.chatbot-shell .user *,
.chatbot-shell p,
.chatbot-shell span {
  color: var(--ink) !important;
}

/* User message bubble - slightly tinted */
.chatbot-shell .user .message-bubble-border,
.chatbot-shell .user .message-content {
  background: var(--accent-soft) !important;
  color: var(--ink) !important;
}

/* Bot message bubble - white */
.chatbot-shell .bot .message-bubble-border,
.chatbot-shell .bot .message-content {
  background: #f8f9fa !important;
  color: var(--ink) !important;
}

/* Chatbot label */
.chatbot-shell label,
.chatbot-shell .label-wrap span {
  color: var(--ink) !important;
  font-weight: 600 !important;
  font-size: 0.95rem !important;
}

/* Chatbot empty state / placeholder */
.chatbot-shell .placeholder,
.chatbot-shell .empty {
  background: #ffffff !important;
  color: var(--muted) !important;
}

/* ============================================================
   Textbox Input
   ============================================================ */
.app-shell textarea,
.app-shell input[type="text"] {
  font-family: 'Inter', sans-serif !important;
  color: var(--ink) !important;
  background: var(--surface-strong) !important;
  border: 1.5px solid var(--edge) !important;
  border-radius: var(--radius-sm) !important;
  font-size: 0.95rem !important;
  transition: border-color 0.2s ease, box-shadow 0.2s ease;
}

.app-shell textarea:focus,
.app-shell input[type="text"]:focus {
  border-color: var(--accent) !important;
  box-shadow: 0 0 0 3px var(--accent-glow) !important;
  outline: none !important;
}

.app-shell textarea::placeholder {
  color: var(--muted) !important;
  opacity: 0.7;
}

/* Textbox labels */
.app-shell .input-label,
.app-shell label span {
  color: var(--ink) !important;
  font-weight: 600 !important;
}

/* ============================================================
   Buttons – Send & Clear
   ============================================================ */
.app-shell button.primary {
  background: linear-gradient(135deg, var(--accent) 0%, var(--accent-dark) 100%) !important;
  color: #ffffff !important;
  font-weight: 600 !important;
  border: none !important;
  border-radius: var(--radius-sm) !important;
  padding: 10px 28px !important;
  font-size: 0.95rem !important;
  box-shadow: 0 4px 16px rgba(14, 124, 134, 0.25) !important;
  transition: transform 0.15s ease, box-shadow 0.15s ease !important;
}

.app-shell button.primary:hover {
  transform: translateY(-1px) !important;
  box-shadow: 0 6px 22px rgba(14, 124, 134, 0.35) !important;
}

.app-shell button.primary:active {
  transform: translateY(0) !important;
}

.app-shell button.secondary,
.app-shell button:not(.primary):not(.example-btn) {
  color: var(--ink) !important;
  font-weight: 500 !important;
  border: 1.5px solid var(--edge) !important;
  border-radius: var(--radius-sm) !important;
  background: var(--surface-strong) !important;
  transition: background 0.2s ease, border-color 0.2s ease !important;
}

.app-shell button.secondary:hover,
.app-shell button:not(.primary):not(.example-btn):hover {
  background: var(--accent-soft) !important;
  border-color: var(--accent) !important;
}


/* ============================================================
   Global Gradio Overrides – Ensure All Labels & Text Visible
   ============================================================ */
.gradio-container label,
.gradio-container .label-wrap,
.gradio-container .label-wrap span,
.gradio-container .block label span {
  color: var(--ink) !important;
}

/* Markdown rendered inside any block */
.gradio-container .prose,
.gradio-container .prose * {
  color: var(--ink) !important;
}

/* Ensure tab labels and accordion headers are visible */
.gradio-container .tab-nav button,
.gradio-container .accordion .label-wrap {
  color: var(--ink) !important;
}

"""


def push(text):
    requests.post(
        "https://api.pushover.net/1/messages.json",
        data={
            "token": os.getenv("PUSHOVER_TOKEN"),
            "user": os.getenv("PUSHOVER_USER"),
            "message": text,
        }
    )


def record_user_details(email, name="Name not provided", notes="not provided"):
    push(f"Recording {name} with email {email} and notes {notes}")
    return {"recorded": "ok"}

def record_unknown_question(question):
    push(f"Recording {question}")
    return {"recorded": "ok"}

record_user_details_json = {
    "name": "record_user_details",
    "description": "Use this tool to record that a user is interested in being in touch and provided an email address",
    "parameters": {
        "type": "object",
        "properties": {
            "email": {
                "type": "string",
                "description": "The email address of this user"
            },
            "name": {
                "type": "string",
                "description": "The user's name, if they provided it"
            }
            ,
            "notes": {
                "type": "string",
                "description": "Any additional information about the conversation that's worth recording to give context"
            }
        },
        "required": ["email"],
        "additionalProperties": False
    }
}

record_unknown_question_json = {
    "name": "record_unknown_question",
    "description": "Always use this tool to record any question that couldn't be answered as you didn't know the answer",
    "parameters": {
        "type": "object",
        "properties": {
            "question": {
                "type": "string",
                "description": "The question that couldn't be answered"
            },
        },
        "required": ["question"],
        "additionalProperties": False
    }
}

tools = [{"type": "function", "function": record_user_details_json},
        {"type": "function", "function": record_unknown_question_json}]


class Evaluation(BaseModel):
    is_acceptable: bool
    feedback: str 

class Me:

    def __init__(self):
        self.openai = OpenAI()
        self.gemini = OpenAI(api_key=os.getenv('GOOGLE_API_KEY'), 
                             base_url='https://generativelanguage.googleapis.com/v1beta/openai/')
        self.name = "Joshua Balogun"
        reader = PdfReader("assets/Profile.pdf")
        self.linkedin = ""
        for page in reader.pages:
            text = page.extract_text()
            if text:
                self.linkedin += text
        with open("assets/summary.txt", "r", encoding="utf-8") as f:
            self.summary = f.read()


    def handle_tool_calls(self, tool_calls):
        results = []
        for tool_call in tool_calls:
            tool_name = tool_call.function.name
            arguments = json.loads(tool_call.function.arguments)
            print(f"Tool called: {tool_name}", flush=True)
            tool = globals().get(tool_name)
            result = tool(**arguments) if tool else {}
            results.append({"role": "tool","content": json.dumps(result),"tool_call_id": tool_call.id})
        return results
    

    def system_prompt(self):
        system_prompt = f"You are acting as {self.name}. You are answering questions on {self.name}'s website, \
        particularly questions related to {self.name}'s career, background, skills and experience. \
        Your responsibility is to represent {self.name} for interactions on the website as faithfully as possible. \
        You are given a summary of {self.name}'s background and LinkedIn profile which you can use to answer questions. \
        Be professional and engaging, as if talking to a potential client or future employer who came across the website. \
        If you don't know the answer to any question, use your record_unknown_question tool to record the question that you couldn't answer, even if it's about something trivial or unrelated to career. \
        If the user is engaging in discussion, try to steer them towards getting in touch via email; ask for their email and record it using your record_user_details tool. "

        system_prompt += f"\n\n## Summary:\n{self.summary}\n\n## LinkedIn Profile:\n{self.linkedin}\n\n"
        system_prompt += f"With this context, please chat with the user, always staying in character as {self.name}."
        return system_prompt


    def evaluator_system_prompt(self):
        evaluator_system_prompt = f"You are an evaluator that decides whether a response to a question is acceptable. \
        You are provided with a conversation between a User and an Agent. Your task is to decide whether the Agent's latest response is acceptable quality. \
        The Agent is playing the role of {self.name} and is representing {self.name} on their website. \
        The Agent has been instructed to be professional and engaging, as if talking to a potential client or future employer who came across the website. \
        The Agent has been provided with context on {self.name} in the form of their summary and LinkedIn details. Here's the information:"

        evaluator_system_prompt += f"\n\n## Summary:\n{self.summary}\n\n## LinkedIn Profile:\n{self.linkedin}\n\n"
        evaluator_system_prompt += f"With this context, please evaluate the latest response, replying with whether the response is acceptable and your feedback."
        return evaluator_system_prompt
    

    def evaluator_user_prompt(self, reply, message, history):
        user_prompt = f"Here's the conversation between the User and the Agent: \n\n{history}\n\n"
        user_prompt += f"Here's the latest message from the User: \n\n{message}\n\n"
        user_prompt += f"Here's the latest response from the Agent: \n\n{reply}\n\n"
        user_prompt += "Please evaluate the response, replying with whether it is acceptable and your feedback."
        return user_prompt          
 

    def evaluate(self, reply, message, history) -> Evaluation:
        messages = [{"role": "system", "content": self.evaluator_system_prompt()}] + [{"role": "user", "content": self.evaluator_user_prompt(reply, message, history)}]
        response = self.gemini.beta.chat.completions.parse(model="gemini-2.5-flash", messages=messages, response_format=self.Evaluation)
        return response.choices[0].message.parsed


    def rerun(self, reply, message, history, feedback):
        updated_system_prompt = self.system_prompt() + "\n\n## Previous answer rejected\nYou just tried to reply, but the quality control rejected your reply\n"
        updated_system_prompt += f"## Your attempted answer:\n{reply}\n\n"
        updated_system_prompt += f"## Reason for rejection:\n{feedback}\n\n"
        messages = [{"role": "system", "content": updated_system_prompt}] + history + [{"role": "user", "content": message}]
        response = self.openai.chat.completions.create(model="gpt-4o-mini", messages=messages)
        return response.choices[0].message.content


    def talker(self, message):
        response = self.openai.audio.speech.create(
            model="gpt-4o-mini-tts",
            voice="onyx",
            input=message
        )
        return response.content


    
    def chat(self, history):
        history = [{"role": h["role"], "content": h["content"]} for h in history] 
        messages = [{"role": "system", "content": self.system_prompt()}] + history 
        
        done = False
        while not done:
            # This is the call to the LLM - see that we pass in the tools json
            response = self.openai.chat.completions.create(model="gpt-4o-mini", messages=messages, tools=tools)
            finish_reason = response.choices[0].finish_reason
            
            # If the LLM wants to call a tool, we do that
            if finish_reason=="tool_calls":
                message = response.choices[0].message
                tool_calls = message.tool_calls
                results = self.handle_tool_calls(tool_calls)
                messages.append(message)
                messages.extend(results)
            else:
                done = True
        reply = response.choices[0].message.content

        history.append({"role": "assistant", "content": reply})
        voice = self.talker(reply)
        
        return history, voice


if __name__ == "__main__":
    me = Me()

    def put_message_in_chatbot(message, history):
        return "", history + [{"role":"user", "content":message}]

    # UI definition
    with gr.Blocks(
        title="Joshua Balogun's A.I. Resume",
        theme=gr.themes.Soft(
            primary_hue="teal",
            secondary_hue="amber",
            neutral_hue="stone",
        ),
        css=APP_CSS,
    ) as ui:
        with gr.Column():
            gr.Markdown(
                """
                <div class="hero-card">
                  <h1>Joshua Balogun's A.I. Resume</h1>
                  <p>
                    My AI-powered resume ask questions, get answers, and get to know me. 
                  </p>
                </div>
                """
            )
        with gr.Row():
            chatbot = gr.Chatbot(height=500, type="messages")
        with gr.Row():
            audio_output = gr.Audio(autoplay=True)
        with gr.Row():
            message = gr.Textbox(label="Chat with my AI Assistant:")

    # Hooking up events to callbacks
        message.submit(put_message_in_chatbot, inputs=[message, chatbot], outputs=[message, chatbot]).then(
            me.chat, inputs=chatbot, outputs=[chatbot, audio_output]
        )

    ui.launch(inbrowser=True)
    