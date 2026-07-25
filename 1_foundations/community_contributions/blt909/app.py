from dotenv import load_dotenv
from openai import OpenAI
import json
import os
import requests
from pypdf import PdfReader
import gradio as gr
import anthropic
import google.genai as genai
from google.genai import types


load_dotenv(override=True)

# --- Model name constants ---
MODEL_EXTRACTOR  = "gpt-5-mini"
MODEL_PLANNER    = "claude-sonnet-4-6"
MODEL_DEVELOPER  = "gemini-3.1-flash-lite-preview"

# ---------------------------------------------------------------------------
# Tool functions – operate on a Me instance's todo lists (passed via closure)
# ---------------------------------------------------------------------------

def make_todo_functions(todos: list, completed: list):
    """Return a dict of todo tool callables bound to the given lists."""

    def get_todo_report() -> str:
        result = ""
        for index, todo in enumerate(todos):
            if completed[index]:
                result += f"- [x] Todo #{index + 1}: {todo}\n"
            else:
                result += f"- [ ] Todo #{index + 1}: {todo}\n"
        return result

    def create_todos(descriptions: list[str]) -> str:
        todos.extend(descriptions)
        completed.extend([False] * len(descriptions))
        return get_todo_report()

    def mark_complete(index: int, completion_notes: str) -> str:
        if 1 <= index <= len(todos):
            completed[index - 1] = True
        else:
            return "No todo at this index."
        return get_todo_report()

    return {"create_todos": create_todos, "mark_complete": mark_complete}


def record_user_details(email: str, name: str = "Name not provided", notes: str = "not provided") -> dict:
    _push(f"Recording {name} with email {email} and notes {notes}")
    return {"recorded": "ok"}


def record_unknown_question(question: str) -> dict:
    _push(f"Recording unknown question: {question}")
    return {"recorded": "ok"}


def _push(text: str) -> None:
    """Send a Pushover notification. Logs a warning if credentials are missing."""
    token = os.getenv("PUSHOVER_TOKEN")
    user  = os.getenv("PUSHOVER_USER")
    if not token or not user:
        print(f"[push] PUSHOVER credentials not set – skipped: {text}")
        return
    try:
        requests.post(
            "https://api.pushover.net/1/messages.json",
            data={"token": token, "user": user, "message": text},
            timeout=5,
        )
    except requests.RequestException as e:
        print(f"[push] Pushover request failed: {e}")


# ---------------------------------------------------------------------------
# Tool JSON schemas
# ---------------------------------------------------------------------------

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
            },
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
            }
        },
        "required": ["question"],
        "additionalProperties": False
    }
}

create_todos_json = {
    "name": "create_todos",
    "description": "Add new todos from a list of descriptions and return the full list",
    "parameters": {
        "type": "object",
        "properties": {
            "descriptions": {
                "type": "array",
                "items": {"type": "string"},
                "title": "Descriptions",
                "description": "Array of todo descriptions"
            }
        },
        "required": ["descriptions"],
        "additionalProperties": False
    }
}

mark_complete_json = {
    "name": "mark_complete",
    "description": "Mark complete the todo at the given position (starting from 1) and return the full list",
    "parameters": {
        "type": "object",
        "properties": {
            "index": {
                "type": "integer",
                "title": "Index",
                "description": "The 1-based index of the todo to mark as complete"
            },
            "completion_notes": {
                "type": "string",
                "title": "Completion Notes",
                "description": "Notes about how you completed the todo in rich console markup"
            }
        },
        "required": ["index", "completion_notes"],
        "additionalProperties": False
    }
}

generate_curriculum_json = {
    "name": "generate_curriculum",
    "description": "Call this tool ONLY when the user asks to see the whole career / resume. It generates a full curriculum resume.",
    "parameters": {
        "type": "object",
        "properties": {},
        "additionalProperties": False
    }
}

# Top-level tools exposed to the main chat agent
tools = [
    {"type": "function", "function": record_user_details_json},
    {"type": "function", "function": record_unknown_question_json},
    {"type": "function", "function": generate_curriculum_json},
]

# Sub-tools used by the inner curriculum-generation agents
sub_tools = [
    {"type": "function", "function": create_todos_json},
    {"type": "function", "function": mark_complete_json},
]


# ---------------------------------------------------------------------------
# Me class
# ---------------------------------------------------------------------------

class Me:

    def __init__(self):
        self.openai = OpenAI()
        self.name = "YOUR NAME HERE"
        reader = PdfReader("me/linkedin.pdf")
        self.linkedin = ""
        for page in reader.pages:
            text = page.extract_text()
            if text:
                self.linkedin += text
        with open("me/me.txt", "r", encoding="utf-8") as f:
            self.summary = f.read()
        self.logs: str = ""
        self.html: str = ""

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _append_log(self, result) -> None:
        entry = result if isinstance(result, str) else json.dumps(result)
        self.logs = entry

    def _dispatch_tool(self, func_name: str, arguments: dict, available_functions: dict):
        """Call a tool by name from available_functions, returning its result."""
        func = available_functions.get(func_name)
        return func(**arguments) if func else f"Unknown tool called: {func_name}"

    # ------------------------------------------------------------------
    # Agent runners
    # ------------------------------------------------------------------

    def run_agent_stream(self, agent_sub_tools, available_functions, model, sys_prompt, user_prompt):
        if "claude" in model.lower():
            return (yield from self.run_anthropic_agent(agent_sub_tools, available_functions, model, sys_prompt, user_prompt))
        elif "gemini" in model.lower():
            return (yield from self.run_gemini_agent(agent_sub_tools, available_functions, model, sys_prompt, user_prompt))
        else:
            return (yield from self.run_openai_agent(agent_sub_tools, available_functions, model, sys_prompt, user_prompt))

    def run_openai_agent(self, agent_sub_tools, available_functions, model, sys_prompt, user_prompt):
        # Reuse the existing client (base_url / api_key already configured via env)
        messages = [
            {"role": "system", "content": sys_prompt},
            {"role": "user",   "content": user_prompt},
        ]
        done = False
        while not done:
            response = self.openai.chat.completions.create(
                model=model, messages=messages, tools=agent_sub_tools
            )
            msg = response.choices[0].message
            if getattr(msg, "tool_calls", None):
                messages.append(msg)
                results = []
                for tool_call in msg.tool_calls:
                    func_name = tool_call.function.name
                    try:
                        arguments = json.loads(tool_call.function.arguments)
                    except (json.JSONDecodeError, ValueError):
                        arguments = {}
                    result = self._dispatch_tool(func_name, arguments, available_functions)
                    results.append({
                        "role": "tool",
                        "content": json.dumps(result),
                        "tool_call_id": tool_call.id,
                    })
                    self._append_log(result)
                    yield
                messages.extend(results)
            else:
                messages.append({"role": "assistant", "content": msg.content})
                done = True

        return messages[-1]["content"]

    def run_anthropic_agent(self, agent_sub_tools, available_functions, model, sys_prompt, user_prompt):
        client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

        anthropic_tools = [
            {
                "name": t["function"]["name"],
                "description": t["function"]["description"],
                "input_schema": t["function"]["parameters"],
            }
            for t in agent_sub_tools
        ]

        messages = [{"role": "user", "content": user_prompt}]
        done = False
        final_content = ""
        while not done:
            response = client.messages.create(
                model=model,
                max_tokens=4096,
                system=sys_prompt,
                messages=messages,
                tools=anthropic_tools,
            )
            messages.append({"role": "assistant", "content": response.content})

            if response.stop_reason == "tool_use":
                tool_results = []
                for block in response.content:
                    if block.type == "tool_use":
                        result = self._dispatch_tool(block.name, block.input, available_functions)
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": json.dumps(result),
                        })
                        self._append_log(result)
                        yield
                messages.append({"role": "user", "content": tool_results})
            else:
                final_content = next(
                    (block.text for block in response.content if block.type == "text"), ""
                )
                done = True

        return final_content

    def run_gemini_agent(self, agent_sub_tools, available_functions, model, sys_prompt, user_prompt):
        client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

        # Convert OpenAI-style JSON schemas to Gemini FunctionDeclarations
        gemini_funcs = []
        for tool_def in agent_sub_tools:
            func_def = tool_def["function"]
            props = func_def["parameters"]["properties"]
            required = func_def["parameters"].get("required", [])

            gemini_props = {}
            for prop_name, prop_schema in props.items():
                items_schema = None
                if prop_schema["type"] == "array" and prop_schema.get("items", {}).get("type") == "string":
                    prop_type = types.Type.ARRAY
                    items_schema = types.Schema(type=types.Type.STRING)
                elif prop_schema["type"] == "integer":
                    prop_type = types.Type.INTEGER
                else:
                    prop_type = types.Type.STRING

                schema_kwargs = {"type": prop_type, "description": prop_schema.get("description", "")}
                if items_schema:
                    schema_kwargs["items"] = items_schema
                gemini_props[prop_name] = types.Schema(**schema_kwargs)

            gemini_funcs.append(types.FunctionDeclaration(
                name=func_def["name"],
                description=func_def["description"],
                parameters=types.Schema(
                    type=types.Type.OBJECT,
                    properties=gemini_props,
                    required=required,
                ),
            ))

        tool_config = types.Tool(function_declarations=gemini_funcs)
        chat = client.chats.create(
            model=model,
            config=types.GenerateContentConfig(
                system_instruction=sys_prompt,
                tools=[tool_config],
                temperature=0.0,
            ),
        )

        response = chat.send_message(user_prompt)
        done = False
        while not done:
            if response.function_calls:
                parts = []
                for call in response.function_calls:
                    result = self._dispatch_tool(call.name, call.args, available_functions)
                    response_dict = result if isinstance(result, dict) else {"result": result}
                    parts.append(types.Part.from_function_response(name=call.name, response=response_dict))
                    self._append_log(result)
                    yield
                response = chat.send_message(parts)
            else:
                done = True

        return response.candidates[0].content.parts[0].text

    # ------------------------------------------------------------------
    # Curriculum generation
    # ------------------------------------------------------------------

    def generate_curriculum_stream(self):
        _push("Generating curriculum...")

        # Use already-loaded linkedin text – no need to re-read the PDF
        linkedin = self.linkedin

        # Fresh per-call todo state to avoid cross-call contamination
        todos: list = []
        completed: list = []
        available_functions = make_todo_functions(todos, completed)

        base_sys_prompt = (
            "You are given a problem to solve, by using your todo tools to plan a list of steps, "
            "then carrying out each step in turn.\n"
            "Now use the todo list tools, create a plan, carry out the steps, and reply with the solution.\n"
            "If any quantity isn't provided in the question, include a step to come up with a reasonable estimate.\n"
            "Do not ask the user questions or clarification; respond only with the answer after using your tools.\n"
        )

        sys_1 = (
            "You are an expert data extractor. Extract the content of the linkedin profile, "
            "categorize it and return it as a structured JSON. "
            "Do not output anything other than JSON."
        )
        structured_json = yield from self.run_agent_stream(
            sub_tools, available_functions, MODEL_EXTRACTOR,
            base_sys_prompt + sys_1,
            f"Here is the linkedin profile:\n{linkedin}",
        )

        sys_2 = (
            "You are an expert planner. Write a plan for another AI agent to build an HTML resume "
            "(including CSS and JavaScript, but only inline or in header) that enhances this person's profile. "
            "Add instructions for the artistic design considering the profile data to best suit the kind of "
            "professional the person is."
            "You won't produce any HTML code yourself, only the plan."
        )
        plan = yield from self.run_agent_stream(
            sub_tools, available_functions, MODEL_PLANNER,
            base_sys_prompt + sys_2,
            f"Here is the structured JSON of the profile:\n{structured_json}",
        )

        sys_3 = (
            "You are an expert web developer. "
            "Build the HTML resume using the provided plan. Return only the raw HTML code. "
            "You can use inline CSS and JavaScript or in header at will, but only within this single HTML file."
        )
        html_resume = yield from self.run_agent_stream(
            sub_tools, available_functions, MODEL_DEVELOPER,
            base_sys_prompt + sys_3,
            f"Here is the plan:\n{plan}\n\nHere is the profile data:\n{structured_json}",
        )

        self.html = html_resume
        yield

        return {"status": "success", "message": "The curriculum has been generated. Let the user know!"}

    # ------------------------------------------------------------------
    # System prompt
    # ------------------------------------------------------------------

    def system_prompt(self) -> str:
        prompt = (
            f"You are acting as {self.name}. You are answering questions on {self.name}'s website, "
            f"particularly questions related to {self.name}'s career, background, skills and experience. "
            f"Your responsibility is to represent {self.name} for interactions on the website as faithfully as possible. "
            f"You are given a summary of {self.name}'s background and LinkedIn profile which you can use to answer questions. "
            "Be professional and engaging, as if talking to a potential client or future employer who came across the website. "
            "If you don't know the answer to any question, use your record_unknown_question tool to record it, even if it's trivial or unrelated to career. "
            "If the user is engaging in discussion, try to steer them towards getting in touch via email; ask for their email and record it using your record_user_details tool. "
            "If the user asks about the agent, you can answer honestly and openly about your capabilities and limitations. "
            "If the user asks for your resume or to have a full view of your career, use your generate_curriculum tool to generate one."
        )
        prompt += f"\n\n## Summary:\n{self.summary}\n\n## LinkedIn Profile:\n{self.linkedin}\n\n"
        prompt += f"With this context, please chat with the user, always staying in character as {self.name}."
        return prompt

    # ------------------------------------------------------------------
    # Main chat stream
    # ------------------------------------------------------------------

    def chat_stream(self, message: str, history: list):
        messages = (
            [{"role": "system", "content": self.system_prompt()}]
            + history
            + [{"role": "user", "content": message}]
        )
        self.logs = ""
        self.html = ""

        done = False
        while not done:
            response = self.openai.chat.completions.create(
                model="gpt-4o-mini", messages=messages, tools=tools
            )
            if response.choices[0].finish_reason == "tool_calls":
                msg = response.choices[0].message
                tool_calls = msg.tool_calls
                messages.append(msg)

                results = []
                for tool_call in tool_calls:
                    tool_name = tool_call.function.name
                    try:
                        arguments = json.loads(tool_call.function.arguments)
                    except (json.JSONDecodeError, ValueError):
                        arguments = {}

                    yield "Thinking...", self.logs, self.html

                    if tool_name == "generate_curriculum":
                        gen = self.generate_curriculum_stream()
                        result = None
                        while True:
                            try:
                                next(gen)
                                yield "Let me generate a resume for you.", self.logs, self.html
                            except StopIteration as e:
                                result = e.value
                                break
                    elif tool_name == "record_user_details":
                        result = record_user_details(**arguments)
                    elif tool_name == "record_unknown_question":
                        result = record_unknown_question(**arguments)
                    else:
                        result = {}

                    results.append({
                        "role": "tool",
                        "content": json.dumps(result),
                        "tool_call_id": tool_call.id,
                    })
                messages.extend(results)
            else:
                done = True

        yield response.choices[0].message.content, self.logs, self.html


# ---------------------------------------------------------------------------
# Gradio UI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    me = Me()

    with gr.Blocks(title=f"{me.name} - AMA AI Assistant", fill_width=True) as demo:
        gr.Markdown(f"# {me.name} - AMA AI Assistant")
        with gr.Row():
            with gr.Column(scale=2):
                chatbot = gr.Chatbot(type="messages", height=500)
                msg = gr.Textbox(label="Type a message...", placeholder="Ask me anything...")
                clear = gr.ClearButton([msg, chatbot])
            with gr.Column(scale=1):
                logs_box = gr.Markdown(value="## Agent Logs\n")

        html_box = gr.HTML(label="Generated Resume (Curriculum)", elem_id="html_resume")

        def user_turn(user_message, chat_history):
            return "", chat_history + [{"role": "user", "content": user_message}]

        def bot_turn(chat_history):
            if not chat_history:
                yield chat_history, "", ""
                return

            user_message = chat_history[-1]["content"]
            history_for_api = chat_history[:-1]

            for bot_msg, logs, html in me.chat_stream(user_message, history_for_api):
                current_history = history_for_api + [
                    {"role": "user",      "content": user_message},
                    {"role": "assistant", "content": bot_msg},
                ]
                yield current_history, logs, html

        msg.submit(user_turn, [msg, chatbot], [msg, chatbot], queue=True).then(
            bot_turn, [chatbot], [chatbot, logs_box, html_box]
        )

    demo.launch()