import os
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from pydantic import BaseModel, Field
from typing_extensions import Annotated, TypedDict

from repo_onboarding_tools import make_repo_tools

load_dotenv(override=True)

OPENROUTER_DEFAULT_BASE = "https://openrouter.ai/api/v1"
OPENROUTER_DEFAULT_MODEL = "openai/gpt-4o-mini"


def openrouter_model_label() -> str:
    """Resolved model id for Gradio status text."""
    return (os.getenv("OPENROUTER_MODEL") or "").strip() or OPENROUTER_DEFAULT_MODEL


def _build_openrouter_chat(**kwargs: Any) -> ChatOpenAI:
    api_key = (os.getenv("OPENROUTER_API_KEY") or "").strip()
    if not api_key:
        raise RuntimeError(
            "Set OPENROUTER_API_KEY in the environment or .env (https://openrouter.ai/keys)."
        )
    base = (os.getenv("OPENROUTER_BASE_URL") or OPENROUTER_DEFAULT_BASE).strip()
    model = (os.getenv("OPENROUTER_MODEL") or OPENROUTER_DEFAULT_MODEL).strip()
    headers: dict[str, str] = {}
    ref = (os.getenv("OPENROUTER_HTTP_REFERER") or "").strip()
    if ref:
        headers["HTTP-Referer"] = ref
    title = (os.getenv("OPENROUTER_APP_TITLE") or "").strip()
    if title:
        headers["X-Title"] = title
    params: dict[str, Any] = {
        "model": model,
        "api_key": api_key,
        "base_url": base,
        **kwargs,
    }
    if headers:
        params["default_headers"] = headers
    return ChatOpenAI(**params)


DEFAULT_SUCCESS_CRITERIA = """The answer must be grounded in the repository (cite paths and filenames).
Include: (1) a short architecture overview, (2) how to run or test the project if discoverable from README/config,
(3) where a newcomer would change code for a typical task, (4) one small, concrete first contribution idea.
If something cannot be determined from the repo, say so explicitly."""


class State(TypedDict):
    messages: Annotated[List[Any], add_messages]
    success_criteria: str
    feedback_on_work: Optional[str]
    success_criteria_met: bool
    user_input_needed: bool


class EvaluatorOutput(BaseModel):
    feedback: str = Field(description="Feedback on the assistant's response")
    success_criteria_met: bool = Field(description="Whether the success criteria have been met")
    user_input_needed: bool = Field(
        description="True if more input is needed from the user, or clarifications, or the assistant is stuck"
    )


class RepoOnboardingSidekick:
    def __init__(self) -> None:
        self.worker_llm_with_tools = None
        self.evaluator_llm_with_output = None
        self.tools: List[Any] = []
        self.graph = None
        self.sidekick_id = str(uuid.uuid4())
        self.memory = MemorySaver()
        self.repo_root: str = ""

    async def setup(self, repo_root: str) -> None:
        self.repo_root = repo_root
        self.tools = make_repo_tools(repo_root)
        worker_llm = _build_openrouter_chat()
        self.worker_llm_with_tools = worker_llm.bind_tools(self.tools)
        evaluator_llm = _build_openrouter_chat()
        self.evaluator_llm_with_output = evaluator_llm.with_structured_output(EvaluatorOutput)
        await self.build_graph()

    def worker(self, state: State) -> Dict[str, Any]:
        system_message = f"""You are a senior engineer helping a new contributor onboard to a codebase.
You may ONLY use the provided tools to explore the repository at:
{self.repo_root}
Do not invent file paths or commands; verify with tools when possible.
Prefer reading README, pyproject.toml, package.json, Makefile, or docs/ when they exist.
Keep working until you can answer clearly or you must ask the user one specific question.

The current date and time is {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

Success criteria for this turn:
{state["success_criteria"]}

If you need clarification from the user, start your reply with "Question:" on its own line, then the question.
If you are done, give a structured final answer with clear headings (no leading "Question:").
"""

        if state.get("feedback_on_work"):
            system_message += f"""
Previously your answer did not satisfy the evaluator. Feedback:
{state["feedback_on_work"]}
Address this feedback using tools as needed."""

        found_system_message = False
        messages = state["messages"]
        for message in messages:
            if isinstance(message, SystemMessage):
                message.content = system_message
                found_system_message = True

        if not found_system_message:
            messages = [SystemMessage(content=system_message)] + list(messages)

        response = self.worker_llm_with_tools.invoke(messages)
        return {"messages": [response]}

    def worker_router(self, state: State) -> str:
        last_message = state["messages"][-1]
        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            return "tools"
        return "evaluator"

    def format_conversation(self, messages: List[Any]) -> str:
        conversation = "Conversation history:\n\n"
        for message in messages:
            if isinstance(message, HumanMessage):
                conversation += f"User: {message.content}\n"
            elif isinstance(message, AIMessage):
                text = message.content or "[Tool calls]"
                conversation += f"Assistant: {text}\n"
        return conversation

    def evaluator(self, state: State) -> State:
        last_response = state["messages"][-1].content or ""

        system_message = """You evaluate whether the Assistant successfully onboarded the user to the repository.
The Assistant only had read-only repo tools; do not expect file writes or running servers."""

        user_message = f"""Repository root (read-only exploration): {self.repo_root}

Conversation:
{self.format_conversation(state["messages"])}

Success criteria:
{state["success_criteria"]}

Assistant's last message to evaluate:
{last_response}

Return feedback, whether success criteria are met, and whether user input is required (e.g. unclear goal or blocked without credentials).
Give the benefit of the doubt if the Assistant clearly used repo evidence; reject vague answers with no paths or invented structure.
"""
        if state.get("feedback_on_work"):
            user_message += f"\nPrior evaluator feedback was: {state['feedback_on_work']}\n"

        evaluator_messages = [
            SystemMessage(content=system_message),
            HumanMessage(content=user_message),
        ]

        eval_result = self.evaluator_llm_with_output.invoke(evaluator_messages)
        return {
            "messages": [
                {
                    "role": "assistant",
                    "content": f"Evaluator feedback: {eval_result.feedback}",
                }
            ],
            "feedback_on_work": eval_result.feedback,
            "success_criteria_met": eval_result.success_criteria_met,
            "user_input_needed": eval_result.user_input_needed,
        }

    def route_based_on_evaluation(self, state: State) -> str:
        if state["success_criteria_met"] or state["user_input_needed"]:
            return "END"
        return "worker"

    async def build_graph(self) -> None:
        graph_builder = StateGraph(State)
        graph_builder.add_node("worker", self.worker)
        graph_builder.add_node("tools", ToolNode(tools=self.tools))
        graph_builder.add_node("evaluator", self.evaluator)

        graph_builder.add_conditional_edges(
            "worker", self.worker_router, {"tools": "tools", "evaluator": "evaluator"}
        )
        graph_builder.add_edge("tools", "worker")
        graph_builder.add_conditional_edges(
            "evaluator", self.route_based_on_evaluation, {"worker": "worker", "END": END}
        )
        graph_builder.add_edge(START, "worker")

        self.graph = graph_builder.compile(checkpointer=self.memory)

    async def run_superstep(
        self,
        message: str,
        success_criteria: Optional[str],
        history: List[dict],
    ) -> List[dict]:
        config = {"configurable": {"thread_id": self.sidekick_id}}
        msgs: List[Any] = [HumanMessage(content=message)]
        state: State = {
            "messages": msgs,
            "success_criteria": success_criteria or DEFAULT_SUCCESS_CRITERIA,
            "feedback_on_work": None,
            "success_criteria_met": False,
            "user_input_needed": False,
        }
        result = await self.graph.ainvoke(state, config=config)
        user = {"role": "user", "content": message}
        messages_out = result["messages"]
        assistant_msg = messages_out[-2]
        eval_msg = messages_out[-1]
        reply_content = getattr(assistant_msg, "content", None) or str(assistant_msg)
        if isinstance(eval_msg, dict):
            feedback_content = eval_msg.get("content", str(eval_msg))
        else:
            feedback_content = getattr(eval_msg, "content", str(eval_msg))
        reply = {"role": "assistant", "content": reply_content}
        feedback = {"role": "assistant", "content": feedback_content}
        return history + [user, reply, feedback]

    def cleanup(self) -> None:
        pass
