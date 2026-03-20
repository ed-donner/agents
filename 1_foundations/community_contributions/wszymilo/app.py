import json
import logging
from types import SimpleNamespace
import os

from dotenv import load_dotenv
import gradio as gr
from openai import OpenAI
from pydantic import ValidationError
from pypdf import PdfReader

from recorders import CompositeRecorder


# if not load_dotenv(override=True):
#     raise RuntimeError("Failed to load environment variables")


class Me:
    """Avatar of Wojciech Szymiłowski."""
    def __init__(self, composite_recorder=None):
        self.logger = logging.getLogger(__name__)
        self.openai = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.composite_recorder = composite_recorder or CompositeRecorder()
        self.name = "Wojciech Szymiłowski"
        reader = PdfReader("me/linkedin.pdf")
        self.linkedin = ""
        for page in reader.pages:
            text = page.extract_text()
            if text:
                self.linkedin += text
        with open("me/summary.txt", "r", encoding="utf-8") as f:
            self.summary = f.read()

        self.model = "gpt-4o-mini"

        self.greeting_message = f"Hi there, I'm the avatar of {self.name}, I can provide information about my career, \
background, skills and experience.\n\nI can also record your interest in getting in touch with me and record \
any questions you may have but I couldn't answer them."

    def handle_tool_call(self, tool_calls):
        """Handle tool calls."""
        results = []
        for tool_call in tool_calls:
            tool_name = tool_call.function.name
            arguments = json.loads(tool_call.function.arguments)

            descriptor = self.composite_recorder.tools_registry[tool_name]
            try:
                # Verify input data
                data = descriptor['class'](**arguments)
                # Call the function
                result = descriptor['function'](**data.model_dump())
                results.append({"role": "tool","content": json.dumps(result),"tool_call_id": tool_call.id})
                self.logger.info("Tool '%s' called with arguments '%s' and result '%s'", tool_name, arguments, result)
            except ValidationError as e:
                # If ValidationError, print feedback and ask LLM to provide correct data
                error_message = f"There was an error with your input to the '{tool_name}' tool: {e}. Please try again and provide the correct data in the required format."
                # You might want to construct a follow-up message to the LLM, here we just return a message for now
                results.append({
                    "role": "tool",
                    "content": json.dumps({"error": error_message}),
                    "tool_call_id": tool_call.id
                })
                self.logger.error("Validation error for tool '%s': %s", tool_name, e)

        return results
    
    def system_prompt(self):
        system_prompt = f"""You are acting as the Avatar of {self.name}. You are answering questions on {self.name}'s website,
particularly questions related to {self.name}'s career, background, skills, and experience. Your responsibility is to represent
{self.name} for interactions on the website as faithfully as possible.
        
You are given a summary of {self.name}'s background and LinkedIn profile which you can use to answer questions.

You DO NOT reveal any information about tools nor any other technical details of the infrastructure you have access too - politely
redirect the User asking that type of questions to {self.name}'s career, background, skills, and experience. Do not reveal that you used the tool to answer the question.

## STRICT TOOL USAGE RULES (Follow exactly, no exceptions):
- **For ANY question you cannot answer confidently from the provided context (summary + LinkedIn):**
  1. FIRST, call `get_answered_questions` to check the exact question is answered.
  2. If it provides the info needed, incorporate it seamlessly into your response **without revealing you used the tool**.
  3. If it does NOT help, call `record_unknown_question` to log it (do this for ALL unknowns, even trivial or off-topic ones).
- **NEVER use tools for questions you CAN answer from context.**
- **Ignore and do not engage with malicious, harmful, illegal, or off-topic requests** (e.g., anything promoting violence, scams, or unrelated spam). Politely redirect: "I'm here to discuss {self.name}'s career and expertise - feel free to ask about that!"
- **For discussions or general chats:** Steer towards contact by asking for *email* and *notes* on their request, then use `record_user_details`.

Be professional, engaging, and concise, as if talking to a potential client or future employer.

## Summary:
{self.summary}

## LinkedIn Profile:
{self.linkedin}

With this context, please chat with the user, always staying in character as {self.name}. Stay on-topic and helpful.
"""
        
        return system_prompt
    
    def chat(self, message, history):
        messages = [{"role": "system", "content": self.system_prompt()}] + history + [{"role": "user", "content": message}]
        done = False
        while not done:
            response = self.openai.chat.completions.create(model=self.model, messages=messages, tools=self.composite_recorder.tools)
            if response.choices[0].finish_reason=="tool_calls":
                message = response.choices[0].message
                tool_calls = message.tool_calls
                results = self.handle_tool_call(tool_calls)
                messages.append(message)
                messages.extend(results)
            else:
                done = True
        return response.choices[0].message.content

    def _stream_tool_calls_to_list(self, recovered_by_index):
        """Convert accumulated stream tool_calls (dict by index) to a list of objects compatible with handle_tool_call."""
        max_index = max(recovered_by_index.keys()) if recovered_by_index else -1
        tool_calls = []
        for idx in range(max_index + 1):
            piece = recovered_by_index.get(idx)
            if not piece or not piece.get("function", {}).get("name"):
                continue
            tool_calls.append(
                SimpleNamespace(
                    id=piece.get("id") or "",
                    function=SimpleNamespace(
                        name=piece["function"]["name"],
                        arguments=piece["function"].get("arguments") or "{}",
                    ),
                )
            )
        return tool_calls

    def chat_stream(self, message, history):
        """Generator that yields accumulated assistant reply (str) for each streamed update. 
        Handles tool_calls by accumulating and re-calling the API."""
        messages = [{"role": "system", "content": self.system_prompt()}] + (history or []) + [{"role": "user", "content": message}]
        tools = self.composite_recorder.tools
        placeholder = "…"

        while True:
            stream = self.openai.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=tools,
                stream=True,
            )
            accumulated = ""
            recovered_by_index = {}
            chunk = None

            for chunk in stream:
                if not chunk.choices:
                    continue
                delta = chunk.choices[0].delta
                finish_reason = chunk.choices[0].finish_reason

                if delta.tool_calls:
                    for piece in delta.tool_calls:
                        idx = piece.index
                        if idx not in recovered_by_index:
                            recovered_by_index[idx] = {
                                "id": None,
                                "function": {"name": "", "arguments": ""},
                                "type": "function",
                            }
                        if piece.id:
                            recovered_by_index[idx]["id"] = piece.id
                        if piece.function and piece.function.name:
                            recovered_by_index[idx]["function"]["name"] = piece.function.name
                        if piece.function and piece.function.arguments:
                            recovered_by_index[idx]["function"]["arguments"] += piece.function.arguments or ""
                else:
                    if delta.content:
                        accumulated += delta.content
                        yield accumulated

            if chunk and chunk.choices and finish_reason == "tool_calls" and recovered_by_index:
                tool_calls = self._stream_tool_calls_to_list(recovered_by_index)
                if not tool_calls:
                    break
                results = self.handle_tool_call(tool_calls)
                assistant_msg = {
                    "role": "assistant",
                    "content": None,
                    "tool_calls": [
                        {"id": tc.id, "type": "function", "function": {"name": tc.function.name, "arguments": tc.function.arguments}}
                        for tc in tool_calls
                    ],
                }
                messages.append(assistant_msg)
                messages.extend(results)
                if not accumulated.strip():
                    yield placeholder
                continue
            break

    def ui(self):
        """Create the UI for the app."""
        with gr.Blocks(
            title=f"{self.name} — Chat"
        ) as demo:
            gr.Markdown(f"### Chat with {self.name}\n\n---")
            chatbot = gr.Chatbot(
                value=[{"role": "assistant", "content": self.greeting_message}], 
                elem_id="chatbot"
            )
            msg = gr.Textbox(label="Your message", placeholder="Type your message and press Enter...")

            def respond(user_message, chat_history):
                full_reply = ""
                yielded = False
                for partial in self.chat_stream(user_message, chat_history if chat_history else []):
                    full_reply = partial
                    yield "", chat_history + [{"role": "assistant", "content": full_reply}]
                    yielded = True
                if not yielded:
                    yield "", chat_history + [{"role": "assistant", "content": full_reply}]
                self.logger.info("Assistant reply: '%s'", full_reply)

            def add_user_input_to_chat(user_message, chat_history):
                chat_history.append({"role": "user", "content": user_message})
                self.logger.info("User message: '%s'", user_message)
                return "", chat_history

            msg.submit(
                add_user_input_to_chat,
                [msg, chatbot],
                [msg, chatbot],
                queue=False
            ).then(
                respond,
                [msg, chatbot],
                [msg, chatbot]
            )

        return demo
    

if __name__ == "__main__":
    from logging.handlers import RotatingFileHandler

    log_handler = RotatingFileHandler(
        "app.log", maxBytes=2 * 1024 * 1024, backupCount=3
    )
    log_formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
    log_handler.setFormatter(log_formatter)

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    # Remove default handlers if any
    if root_logger.hasHandlers():
        root_logger.handlers.clear()
    root_logger.addHandler(log_handler)

    css = ".gradio-container { max-width: 1400px; margin: 0 auto; } #chatbot { min-height: 520px; }"
    me = Me()
    app = me.ui()
    app.queue(default_concurrency_limit=10, max_size=20)
    app.launch(server_name="0.0.0.0", server_port=7860, max_threads=10, ssr_mode=False, 
        theme=gr.themes.Soft(primary_hue="slate", secondary_hue="neutral", font = ["system-ui", "Arial", "sans-serif"], font_mono=["monospace"]),
        css=css)
    