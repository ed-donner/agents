import asyncio
import uuid
import os
import subprocess
import sys
import textwrap
import requests
import wikipedia
from datetime import datetime
from typing import Annotated, List, Any, Optional, Dict

from typing_extensions import TypedDict
from pydantic import BaseModel, Field
from dotenv import load_dotenv

from langchain_openai import ChatOpenAI
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_core.tools import tool
from langchain_community.agent_toolkits import PlayWrightBrowserToolkit
from langchain_community.tools.playwright.utils import create_async_playwright_browser
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import ToolNode

import gradio as gr

load_dotenv(override=True)

# ---------------------------------------------------------------------------
# CONSTANTS
# ---------------------------------------------------------------------------

SANDBOX_DIR = os.path.join(os.path.dirname(__file__), "workspace")
os.makedirs(SANDBOX_DIR, exist_ok=True)

BLOCKED_IMPORTS = ["os", "sys", "subprocess", "socket", "shutil", "importlib"]
MAX_OUTPUT_LENGTH = 2000
NOTIFICATION_RATE_LIMIT: Dict[str, int] = {}  # session_id -> count
MAX_NOTIFICATIONS_PER_SESSION = 5


# ---------------------------------------------------------------------------
# INPUT GUARDRAIL
# ---------------------------------------------------------------------------

def input_guardrail(text: str) -> tuple[bool, str]:
    """
    Check user input before passing to the agent.
    - Detect obvious prompt injection patterns (e.g. 'ignore previous instructions')
    - Flag potential PII (credit card patterns, SSN patterns)
    - Block known policy-violating keywords
    Returns (is_safe, reason).
    """
    lowered = text.lower()

    injection_patterns = ["ignore previous", "ignore all instructions", "disregard your instructions"]
    for pattern in injection_patterns:
        if pattern in lowered:
            return False, "Input blocked: possible prompt injection detected."

    # Stub: PII detection (e.g. credit card, SSN) — extend with regex in production
    # import re; if re.search(r'\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b', text): ...

    # Stub: policy keyword blocklist — extend as needed
    blocked_keywords = ["bomb", "malware", "exploit"]
    for kw in blocked_keywords:
        if kw in lowered:
            return False, f"Input blocked: policy violation detected ('{kw}')."

    return True, ""


# ---------------------------------------------------------------------------
# OUTPUT GUARDRAIL
# ---------------------------------------------------------------------------

def output_guardrail(text: str) -> tuple[bool, str]:
    """
    Check agent output before returning to the user.
    - Detect sensitive data leakage (API keys, passwords in output)
    - Cap response length
    - Flag harmful content patterns
    Returns (is_safe, reason).
    """
    # Stub: detect accidental API key leakage (basic heuristic)
    if "sk-" in text and len([c for c in text if c == "-"]) > 3:
        return False, "Output blocked: possible API key detected in response."

    # Cap length
    if len(text) > 8000:
        return False, "Output blocked: response too long."

    # Stub: harmful content check — integrate a moderation API here in production
    # e.g. openai.moderations.create(input=text)

    return True, ""


# ---------------------------------------------------------------------------
# TOOLS
# ---------------------------------------------------------------------------

@tool
def search_web(query: str) -> str:
    """Search the web using DuckDuckGo and return a summary of results."""
    # Input guardrail for tool
    safe, reason = input_guardrail(query)
    if not safe:
        return reason
    try:
        from langchain_community.tools import DuckDuckGoSearchRun
        search = DuckDuckGoSearchRun()
        result = search.run(query)
        # Cap output
        return result[:MAX_OUTPUT_LENGTH]
    except Exception as e:
        return f"Web search failed: {str(e)}"


@tool
def search_wikipedia(query: str) -> str:
    """Search Wikipedia and return a short summary for the given query."""
    safe, reason = input_guardrail(query)
    if not safe:
        return reason
    try:
        summary = wikipedia.summary(query, sentences=5, auto_suggest=False)
        return summary[:MAX_OUTPUT_LENGTH]
    except wikipedia.exceptions.DisambiguationError as e:
        return f"Ambiguous query. Did you mean: {', '.join(e.options[:5])}?"
    except wikipedia.exceptions.PageError:
        return "No Wikipedia page found for that query."
    except Exception as e:
        return f"Wikipedia search failed: {str(e)}"


@tool
def send_notification(title: str, message: str) -> str:
    """Send a push notification to the user via Pushover."""
    # Rate limiting guardrail
    token = os.getenv("PUSHOVER_TOKEN")
    user = os.getenv("PUSHOVER_USER")
    if not token or not user:
        return "Pushover credentials not configured."

    # Input guardrail
    safe, reason = input_guardrail(f"{title} {message}")
    if not safe:
        return reason

    # Stub: rate limiting per session — in production, tie this to session_id
    try:
        response = requests.post(
            "https://api.pushover.net/1/messages.json",
            data={"token": token, "user": user, "title": title, "message": message},
            timeout=10,
        )
        if response.status_code == 200:
            return "Notification sent successfully."
        return f"Failed to send notification: {response.text}"
    except Exception as e:
        return f"Notification error: {str(e)}"


@tool
def write_file(filename: str, content: str) -> str:
    """
    Write content to a file inside the sandboxed workspace directory.
    Path traversal (e.g. '../') is not allowed.
    """
    # Sandbox guardrail: prevent path traversal
    safe_name = os.path.basename(filename)
    if safe_name != filename or ".." in filename:
        return "File write blocked: path traversal is not allowed. Use a plain filename."

    filepath = os.path.join(SANDBOX_DIR, safe_name)
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        return f"File '{safe_name}' written to workspace successfully."
    except Exception as e:
        return f"File write failed: {str(e)}"


@tool
def read_file(filename: str) -> str:
    """Read a file from the sandboxed workspace directory."""
    safe_name = os.path.basename(filename)
    if safe_name != filename or ".." in filename:
        return "File read blocked: path traversal is not allowed."

    filepath = os.path.join(SANDBOX_DIR, safe_name)
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
        return content[:MAX_OUTPUT_LENGTH]
    except FileNotFoundError:
        return f"File '{safe_name}' not found in workspace."
    except Exception as e:
        return f"File read failed: {str(e)}"


@tool
def run_python(code: str) -> str:
    """
    Execute Python code in a restricted subprocess.
    Blocked: os, sys, subprocess, socket, shutil, importlib.
    Include print() statements to see output.
    """
    # Static analysis guardrail: block dangerous imports
    for blocked in BLOCKED_IMPORTS:
        if f"import {blocked}" in code or f"from {blocked}" in code:
            return f"Execution blocked: import of '{blocked}' is not permitted."

    # Wrap in a timeout subprocess for safety
    try:
        wrapped = textwrap.dedent(f"""
import signal, sys
{code}
""")
        result = subprocess.run(
            [sys.executable, "-c", wrapped],
            capture_output=True,
            text=True,
            timeout=10,  # Hard timeout
        )
        output = result.stdout or result.stderr or "(no output)"
        return output[:MAX_OUTPUT_LENGTH]
    except subprocess.TimeoutExpired:
        return "Execution blocked: code timed out after 10 seconds."
    except Exception as e:
        return f"Python execution failed: {str(e)}"


# ---------------------------------------------------------------------------
# PYDANTIC SCHEMAS
# ---------------------------------------------------------------------------

class EvaluatorOutput(BaseModel):
    feedback: str = Field(description="Feedback on the assistant's response")
    success_criteria_met: bool = Field(description="Whether the success criteria have been met")
    user_input_needed: bool = Field(
        description="True if more input is needed from the user, or clarifications, or the assistant is stuck"
    )


# ---------------------------------------------------------------------------
# STATE
# ---------------------------------------------------------------------------

class State(TypedDict):
    messages: Annotated[List[Any], add_messages]
    success_criteria: str
    feedback_on_work: Optional[str]
    success_criteria_met: bool
    user_input_needed: bool


# ---------------------------------------------------------------------------
# SIDEKICK CLASS
# ---------------------------------------------------------------------------

class Sidekick:
    def __init__(self):
        self.graph = None
        self.memory = MemorySaver()
        self.sidekick_id = str(uuid.uuid4())
        self.browser = None
        self.playwright = None
        self.tools = []
        self.worker_llm_with_tools = None
        self.evaluator_llm_with_output = None

    async def setup(self):
        """Initialise browser, tools, LLMs and build the graph."""
        try:
            self.playwright, self.browser = None, None
            async_browser = create_async_playwright_browser(headless=True)
            toolkit = PlayWrightBrowserToolkit.from_browser(async_browser=async_browser)
            playwright_tool_list = toolkit.get_tools()
        except Exception as e:
            print(f"Playwright setup failed (continuing without browser tools): {e}")
            playwright_tool_list = []

        non_browser_tools = [
            search_web,
            search_wikipedia,
            send_notification,
            write_file,
            read_file,
            run_python,
        ]

        self.tools = playwright_tool_list + non_browser_tools

        # Worker LLM — low temperature for consistent task execution
        worker_llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.2,
            max_tokens=1500,
            streaming=True,
        )
        self.worker_llm_with_tools = worker_llm.bind_tools(self.tools)

        # Evaluator LLM — near-zero temperature for deterministic judgement
        evaluator_llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.0,
            max_tokens=500,
        )
        self.evaluator_llm_with_output = evaluator_llm.with_structured_output(EvaluatorOutput)

        self.build_graph()

    def worker(self, state: State) -> Dict[str, Any]:
        """Worker node: executes the task using tools, guided by success criteria."""
        system_message = f"""You are a helpful assistant that can use tools to complete tasks.
You keep working until the success criteria is met or you need user input.
You can browse the web, search Wikipedia, run Python code, manage files, and send notifications.
Current date and time: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

Success criteria:
{state["success_criteria"]}

Reply with a question if you need clarification, or with your final answer when done.
If asking a question, prefix it clearly: "Question: ..."
"""
        if state.get("feedback_on_work"):
            system_message += f"""
A previous attempt was rejected. Feedback:
{state["feedback_on_work"]}
Please address this feedback and try again.
"""
        messages = state["messages"]
        found = False
        for m in messages:
            if isinstance(m, SystemMessage):
                m.content = system_message
                found = True
        if not found:
            messages = [SystemMessage(content=system_message)] + messages

        try:
            response = self.worker_llm_with_tools.invoke(messages)
        except Exception as e:
            response = AIMessage(content=f"Worker encountered an error: {str(e)}")

        return {"messages": [response]}

    def worker_router(self, state: State) -> str:
        """Route to tools if tool calls exist, otherwise to evaluator."""
        last = state["messages"][-1]
        if hasattr(last, "tool_calls") and last.tool_calls:
            return "tools"
        return "evaluator"

    def format_conversation(self, messages: List[Any]) -> str:
        """Format message history for the evaluator prompt."""
        out = "Conversation history:\n\n"
        for m in messages:
            if isinstance(m, HumanMessage):
                out += f"User: {m.content}\n"
            elif isinstance(m, AIMessage):
                out += f"Assistant: {m.content or '[Tool use]'}\n"
        return out

    def evaluator(self, state: State) -> Dict[str, Any]:
        """Evaluator node: judges whether success criteria has been met."""
        last_response = state["messages"][-1].content

        system_message = (
            "You are an evaluator. Assess whether the assistant's response meets the success criteria. "
            "Be fair but rigorous. Give the assistant benefit of the doubt if it says it completed a file or action."
        )
        user_message = f"""{self.format_conversation(state["messages"])}

Success criteria: {state["success_criteria"]}

Last assistant response: {last_response}

Decide: is the criteria met? Is user input needed?
"""
        if state.get("feedback_on_work"):
            user_message += (
                f"\nPrior feedback given: {state['feedback_on_work']}\n"
                "If the assistant keeps repeating mistakes, mark user_input_needed=True."
            )

        try:
            eval_result = self.evaluator_llm_with_output.invoke([
                SystemMessage(content=system_message),
                HumanMessage(content=user_message),
            ])
        except Exception as e:
            # Fail safe: ask user for input if evaluator crashes
            return {
                "messages": [{"role": "assistant", "content": f"Evaluator error: {str(e)}"}],
                "feedback_on_work": "Evaluator failed. Please review manually.",
                "success_criteria_met": False,
                "user_input_needed": True,
            }

        return {
            "messages": [{"role": "assistant", "content": f"Evaluator feedback: {eval_result.feedback}"}],
            "feedback_on_work": eval_result.feedback,
            "success_criteria_met": eval_result.success_criteria_met,
            "user_input_needed": eval_result.user_input_needed,
        }

    def route_based_on_evaluation(self, state: State) -> str:
        if state["success_criteria_met"] or state["user_input_needed"]:
            return "END"
        return "worker"

    def build_graph(self):
        """Compile the LangGraph state machine."""
        builder = StateGraph(State)
        builder.add_node("worker", self.worker)
        builder.add_node("tools", ToolNode(tools=self.tools))
        builder.add_node("evaluator", self.evaluator)

        builder.add_edge(START, "worker")
        builder.add_conditional_edges("worker", self.worker_router, {"tools": "tools", "evaluator": "evaluator"})
        builder.add_edge("tools", "worker")
        builder.add_conditional_edges("evaluator", self.route_based_on_evaluation, {"worker": "worker", "END": END})

        self.graph = builder.compile(checkpointer=self.memory)

    async def run_superstep(self, message: str, success_criteria: str, history: list) -> list:
        """Run one full worker→evaluator cycle and return updated chat history."""
        # Input guardrail
        safe, reason = input_guardrail(message)
        if not safe:
            return history + [
                {"role": "user", "content": message},
                {"role": "assistant", "content": f"⚠️ {reason}"},
            ]

        config = {"configurable": {"thread_id": self.sidekick_id}}
        state = {
            "messages": message,
            "success_criteria": success_criteria or "The answer should be clear and accurate.",
            "feedback_on_work": None,
            "success_criteria_met": False,
            "user_input_needed": False,
        }

        try:
            result = await self.graph.ainvoke(state, config=config)
        except Exception as e:
            return history + [
                {"role": "user", "content": message},
                {"role": "assistant", "content": f"❌ An error occurred: {str(e)}"},
            ]

        reply_content = result["messages"][-2].content
        feedback_content = result["messages"][-1].content

        # Output guardrail
        safe, reason = output_guardrail(reply_content)
        if not safe:
            reply_content = f"⚠️ Output was blocked by safety filter: {reason}"

        return history + [
            {"role": "user", "content": message},
            {"role": "assistant", "content": reply_content},
            {"role": "assistant", "content": feedback_content},
        ]

    async def cleanup(self):
        """Close browser and playwright instances."""
        try:
            if self.browser:
                await self.browser.close()
            if self.playwright:
                await self.playwright.stop()
        except Exception as e:
            print(f"Cleanup error: {e}")


# ---------------------------------------------------------------------------
# GRADIO UI
# ---------------------------------------------------------------------------

async def initialize_sidekick():
    """Create and set up a fresh Sidekick instance for a new session."""
    sk = Sidekick()
    await sk.setup()
    return sk


async def handle_message(message, success_criteria, history, sidekick):
    """Called when the user submits a message."""
    if not message.strip():
        return history, sidekick

    if sidekick is None:
        sidekick = await initialize_sidekick()

    history = await sidekick.run_superstep(message, success_criteria, history)
    return history, sidekick


async def reset_session(sidekick):
    """Reset the session: cleanup old sidekick and create a fresh one."""
    if sidekick is not None:
        await sidekick.cleanup()
    new_sidekick = await initialize_sidekick()
    return [], "", "", new_sidekick


with gr.Blocks(theme=gr.themes.Soft(primary_hue="emerald"), title="Sidekick") as demo:
    gr.Markdown("## 🤖 Sidekick — Your Personal AI Co-worker")

    sidekick_state = gr.State(None)

    chatbot = gr.Chatbot(label="Sidekick", height=420, type="messages")

    with gr.Row():
        message = gr.Textbox(
            placeholder="What do you need help with?",
            label="Your request",
            scale=4,
        )
        go_btn = gr.Button("Go!", variant="primary", scale=1)

    success_criteria = gr.Textbox(
        placeholder="e.g. Provide a concise bullet-point summary with at least 3 points",
        label="Success criteria (optional)",
    )

    reset_btn = gr.Button("Reset session", variant="stop")

    # Wire up interactions
    go_btn.click(
        handle_message,
        inputs=[message, success_criteria, chatbot, sidekick_state],
        outputs=[chatbot, sidekick_state],
    )
    message.submit(
        handle_message,
        inputs=[message, success_criteria, chatbot, sidekick_state],
        outputs=[chatbot, sidekick_state],
    )
    reset_btn.click(
        reset_session,
        inputs=[sidekick_state],
        outputs=[chatbot, message, success_criteria, sidekick_state],
    )

if __name__ == "__main__":
    demo.launch()
