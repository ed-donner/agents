import asyncio
import os
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
from guardrails import GuardrailsManager
from langchain_openai import ChatOpenAI
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage, ToolMessage
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from pydantic import BaseModel, Field
from sidekick_tools import other_tools, playwright_tools
from typing_extensions import Annotated, TypedDict


load_dotenv(override=True)


class State(TypedDict):
    messages: Annotated[List[Any], add_messages]
    success_criteria: str
    feedback_on_work: Optional[str]
    success_criteria_met: bool
    user_input_needed: bool
    clarifying_questions_asked: int
    planning_complete: bool
    clarification_question: Optional[str]
    guardrails_issues: List[str]
    final_response: Optional[str]


class EvaluatorOutput(BaseModel):
    feedback: str = Field(description="Feedback on the assistant's response")
    success_criteria_met: bool = Field(description="Whether the success criteria have been met")
    user_input_needed: bool = Field(
        description="True if more user input is needed, or the assistant is blocked."
    )


class PlannerOutput(BaseModel):
    clarification_question: Optional[str] = Field(
        description="A single clarifying question, or None if the task is clear."
    )
    ready_to_proceed: bool = Field(
        description="True if there is enough information to start working."
    )
    reasoning: str = Field(
        description="A brief explanation of why clarification is or is not needed."
    )


class Sidekick:
    def __init__(self) -> None:
        self.worker_llm_with_tools = None
        self.evaluator_llm_with_output = None
        self.planner_llm_with_output = None
        self.tools = None
        self.tool_node = None
        self.graph = None
        self.sidekick_id = str(uuid.uuid4())
        self.memory = MemorySaver()
        self.browser = None
        self.playwright = None
        self.guardrails = None
        self.current_status = "Idle"
        self.current_step = "idle"
        self.progress_log: List[str] = []
        self.last_feedback = "No evaluation yet."
        self.awaiting_clarification = False

    def _openrouter_settings(self) -> tuple[str, str, Dict[str, str]]:
        api_key = os.getenv("OPENROUTER_API_KEY")
        if not api_key:
            raise RuntimeError("OPENROUTER_API_KEY is not set.")

        base_url = (
            os.getenv("OPENROUTER_BASE_URL")
            or os.getenv("OPENROUTER_URL")
            or "https://openrouter.ai/api/v1"
        )

        headers: Dict[str, str] = {}
        referer = os.getenv("OPENROUTER_HTTP_REFERER")
        title = os.getenv("OPENROUTER_TITLE")
        if referer:
            headers["HTTP-Referer"] = referer
        if title:
            headers["X-OpenRouter-Title"] = title
        return api_key, base_url, headers

    def _build_model(
        self,
        env_key: str,
        default_model: str = "openai/gpt-4o-mini",
        temperature: Optional[float] = None,
    ) -> ChatOpenAI:
        api_key, base_url, headers = self._openrouter_settings()
        model = os.getenv(env_key) or os.getenv("OPENROUTER_MODEL") or default_model
        return ChatOpenAI(
            model=model,
            api_key=api_key,
            base_url=base_url,
            default_headers=headers or None,
            temperature=temperature,
        )

    def _update_status(self, status: str, step: str) -> None:
        self.current_status = status
        self.current_step = step
        timestamp = datetime.now().strftime("%H:%M:%S")
        entry = f"[{timestamp}] {step.upper()}: {status}"
        self.progress_log.append(entry)
        self.progress_log = self.progress_log[-40:]

    def get_status_snapshot(self) -> Dict[str, str]:
        return {
            "status": self.current_status,
            "step": self.current_step,
            "progress_log": "\n".join(self.progress_log) if self.progress_log else "Waiting to start.",
            "feedback": self.last_feedback,
        }

    async def setup(self) -> None:
        self._update_status("Initializing tools and models", "setup")
        self.tools, self.browser, self.playwright = await playwright_tools()
        self.tools += await other_tools()
        self.tool_node = ToolNode(tools=self.tools)

        worker_llm = self._build_model("OPENROUTER_WORKER_MODEL")
        self.worker_llm_with_tools = worker_llm.bind_tools(self.tools)

        evaluator_llm = self._build_model("OPENROUTER_EVALUATOR_MODEL")
        self.evaluator_llm_with_output = evaluator_llm.with_structured_output(
            EvaluatorOutput, method="function_calling"
        )

        planner_llm = self._build_model("OPENROUTER_PLANNER_MODEL")
        self.planner_llm_with_output = planner_llm.with_structured_output(
            PlannerOutput, method="function_calling"
        )

        moderation_model = (
            os.getenv("OPENROUTER_GUARDRAILS_MODEL")
            or os.getenv("OPENROUTER_EVALUATOR_MODEL")
            or os.getenv("OPENROUTER_MODEL")
            or "openai/gpt-4o-mini"
        )
        api_key, base_url, headers = self._openrouter_settings()
        self.guardrails = GuardrailsManager(
            max_tokens=int(os.getenv("IGNITERS_MAX_INPUT_TOKENS", "8000")),
            moderation_model=moderation_model,
            api_key=api_key,
            base_url=base_url,
            default_headers=headers,
        )
        await self.build_graph()
        self._update_status("Ready", "setup")

    def _format_conversation(self, messages: List[BaseMessage]) -> str:
        conversation = []
        for message in messages:
            if isinstance(message, HumanMessage):
                conversation.append(f"User: {message.content}")
            elif isinstance(message, AIMessage):
                if getattr(message, "tool_calls", None):
                    continue
                text = self._message_text(message.content)
                if text:
                    conversation.append(f"Assistant: {text}")
        return "\n".join(conversation)

    def _message_text(self, content: Any) -> str:
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            parts = []
            for item in content:
                if isinstance(item, dict) and item.get("type") == "text":
                    parts.append(item.get("text", ""))
            return "\n".join(part for part in parts if part)
        return str(content or "")

    async def guardrails_check(self, state: State) -> Dict[str, Any]:
        self._update_status("Validating user input", "guardrails")
        latest_user_message = ""
        for message in reversed(state["messages"]):
            if isinstance(message, HumanMessage):
                latest_user_message = self._message_text(message.content)
                break

        validation = await self.guardrails.validate_input(latest_user_message)
        if validation["is_valid"]:
            return {
                "guardrails_issues": [],
                "user_input_needed": False,
                "final_response": None,
            }

        issues = validation["issues"] or ["Input failed safety validation."]
        issue_text = "\n".join(f"- {issue}" for issue in issues)
        response = (
            "I cannot act on that request yet because the input failed validation.\n\n"
            f"{issue_text}\n\n"
            "Please revise your request and try again."
        )
        self.last_feedback = "Input blocked by guardrails."
        return {
            "guardrails_issues": issues,
            "user_input_needed": True,
            "final_response": response,
            "messages": [AIMessage(content=response)],
        }

    def guardrails_router(self, state: State) -> str:
        if state.get("guardrails_issues"):
            return "END"
        return "planner"

    def planner(self, state: State) -> Dict[str, Any]:
        self._update_status("Checking whether clarification is needed", "planner")
        questions_asked = state.get("clarifying_questions_asked", 0)
        max_questions = 3

        system_message = f"""You are a planning agent that clarifies user requests before work begins.
Your job is to make sure the user's intent and success criteria are clear enough for execution.

You have asked {questions_asked} clarifying question(s) so far.
Ask at most {max_questions} clarifying questions total before proceeding.

Rules:
- Ask one focused question only if important information is missing.
- If the request is already clear enough, set ready_to_proceed to true.
- Prefer concrete questions about missing scope, output format, constraints, or priorities.
- Do not repeat a question the user has already answered.
"""

        user_message = f"""Conversation:
{self._format_conversation(state["messages"])}

Success criteria:
{state.get("success_criteria", "The answer should be clear and accurate.")}

Decide whether to ask one clarifying question or proceed.
"""

        planner_result = self.planner_llm_with_output.invoke(
            [
                SystemMessage(content=system_message),
                HumanMessage(content=user_message),
            ]
        )

        if planner_result.ready_to_proceed or questions_asked >= max_questions:
            self._update_status("Enough context collected, starting execution", "planner")
            return {
                "planning_complete": True,
                "user_input_needed": False,
                "clarification_question": None,
                "final_response": None,
            }

        question = planner_result.clarification_question or "Could you clarify what outcome you want?"
        self.last_feedback = planner_result.reasoning
        return {
            "planning_complete": False,
            "clarifying_questions_asked": questions_asked + 1,
            "user_input_needed": True,
            "clarification_question": question,
            "final_response": question,
            "messages": [AIMessage(content=question)],
        }

    def planner_router(self, state: State) -> str:
        if state.get("user_input_needed"):
            return "END"
        return "worker"

    def worker(self, state: State) -> Dict[str, Any]:
        self._update_status("Working on the task", "worker")
        system_message = f"""You are a helpful assistant that can use tools to complete tasks.
You keep working until either you need information from the user or the success criteria is met.
You can browse the web, use Python, read and write files in the sandbox, and send notifications.
If you use Python REPL, include print() when you need visible output.

Current date and time: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

Success criteria:
{state["success_criteria"]}

If something essential is missing, ask a concise clarification question.
Otherwise, continue the work and provide the best final answer you can.
"""

        if state.get("feedback_on_work"):
            system_message += (
                "\nPrevious attempt feedback:\n"
                f"{state['feedback_on_work']}\n"
                "Use that feedback to improve the next response."
            )

        messages = [SystemMessage(content=system_message)] + list(state["messages"])
        response = self.worker_llm_with_tools.invoke(messages)
        update: Dict[str, Any] = {"messages": [response]}
        if not getattr(response, "tool_calls", None):
            update["final_response"] = self._message_text(response.content)
        return update

    def worker_router(self, state: State) -> str:
        last_message = state["messages"][-1]
        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            return "tools"
        return "evaluator"

    async def tools_node(self, state: State) -> Dict[str, Any]:
        self._update_status("Executing tool calls", "tools")
        return await self.tool_node.ainvoke(state)

    def evaluator(self, state: State) -> Dict[str, Any]:
        self._update_status("Evaluating the latest response", "evaluator")
        last_response = state.get("final_response") or ""

        system_message = """You are an evaluator that determines if the assistant has completed the task successfully.
Assess the latest assistant response against the success criteria and decide whether the task is complete or whether more user input is needed."""

        user_message = f"""Conversation:
{self._format_conversation(state["messages"])}

Success criteria:
{state["success_criteria"]}

Latest assistant response:
{last_response}

Return feedback, whether the success criteria is met, and whether more user input is needed."""

        eval_result = self.evaluator_llm_with_output.invoke(
            [
                SystemMessage(content=system_message),
                HumanMessage(content=user_message),
            ]
        )
        self.last_feedback = eval_result.feedback
        if eval_result.success_criteria_met:
            self._update_status("Task completed successfully", "evaluator")
        elif eval_result.user_input_needed:
            self._update_status("Waiting for more user input", "evaluator")
        else:
            self._update_status("Need another worker pass", "evaluator")

        return {
            "feedback_on_work": eval_result.feedback,
            "success_criteria_met": eval_result.success_criteria_met,
            "user_input_needed": eval_result.user_input_needed,
        }

    def evaluator_router(self, state: State) -> str:
        if state["success_criteria_met"] or state["user_input_needed"]:
            return "END"
        return "worker"

    async def build_graph(self) -> None:
        graph_builder = StateGraph(State)
        graph_builder.add_node("guardrails", self.guardrails_check)
        graph_builder.add_node("planner", self.planner)
        graph_builder.add_node("worker", self.worker)
        graph_builder.add_node("tools", self.tools_node)
        graph_builder.add_node("evaluator", self.evaluator)

        graph_builder.add_edge(START, "guardrails")
        graph_builder.add_conditional_edges(
            "guardrails",
            self.guardrails_router,
            {"planner": "planner", "END": END},
        )
        graph_builder.add_conditional_edges(
            "planner",
            self.planner_router,
            {"worker": "worker", "END": END},
        )
        graph_builder.add_conditional_edges(
            "worker",
            self.worker_router,
            {"tools": "tools", "evaluator": "evaluator"},
        )
        graph_builder.add_edge("tools", "worker")
        graph_builder.add_conditional_edges(
            "evaluator",
            self.evaluator_router,
            {"worker": "worker", "END": END},
        )
        self.graph = graph_builder.compile(checkpointer=self.memory)

    async def run_superstep(self, message: str, success_criteria: str, history: Optional[List[Dict[str, str]]]):
        self._update_status("Received user input", "input")

        initial_state: State = {
            "messages": [HumanMessage(content=message)],
            "success_criteria": success_criteria or "The answer should be clear and accurate.",
            "feedback_on_work": None,
            "success_criteria_met": False,
            "user_input_needed": False,
            "planning_complete": False,
            "clarification_question": None,
            "guardrails_issues": [],
            "final_response": None,
        }
        if not self.awaiting_clarification:
            initial_state["clarifying_questions_asked"] = 0

        result = await self.graph.ainvoke(
            initial_state,
            config={
                "configurable": {"thread_id": self.sidekick_id},
                "recursion_limit": 30,
            },
        )

        final_response = result.get("final_response") or "I couldn't generate a response."
        output_validation = await self.guardrails.validate_output(final_response)
        if not output_validation["is_valid"]:
            final_response = (
                "I generated a response, but it was blocked by output guardrails. "
                "Please narrow the request or try again."
            )
            self.last_feedback = "\n".join(output_validation["issues"]) or self.last_feedback
            self._update_status("Output guardrails blocked the response", "guardrails")

        self.awaiting_clarification = bool(result.get("user_input_needed"))
        if result.get("success_criteria_met"):
            self.awaiting_clarification = False

        user = {"role": "user", "content": message}
        reply = {"role": "assistant", "content": final_response}
        return (history or []) + [user, reply]

    def cleanup(self) -> None:
        if self.browser:
            try:
                loop = asyncio.get_running_loop()
                loop.create_task(self.browser.close())
                if self.playwright:
                    loop.create_task(self.playwright.stop())
            except RuntimeError:
                asyncio.run(self.browser.close())
                if self.playwright:
                    asyncio.run(self.playwright.stop())
