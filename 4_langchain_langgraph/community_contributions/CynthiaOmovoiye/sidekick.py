import re
import uuid
import asyncio
import os
from datetime import datetime
from pathlib import Path
from typing import Annotated, Any, Dict, List, Literal, Optional

from dotenv import load_dotenv
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from pydantic import BaseModel, Field
from typing_extensions import NotRequired, TypedDict

from sidekick_tools import other_tools, playwright_tools

load_dotenv(override=True)

# Persist checkpoints next to this module (works regardless of cwd)
_CHECKPOINT_DB = Path(__file__).resolve().parent / "sidekick_memory.db"

# Worker↔evaluator cycles when the model never sets success or user_input_needed (infinite loop guard)
_MAX_WORKER_EVAL_LOOPS = 8
# Tool-heavy runs need more than LangGraph's default (25) supersteps
_GRAPH_RECURSION_LIMIT = 120


def make_thread_id(username: str, session_id: str) -> str:
    """Use username as thread id when set so checkpoints survive page reloads; else anonymous session."""
    uname = re.sub(r"[^a-zA-Z0-9_.-]+", "_", (username or "").strip())[:80]
    if uname:
        return uname
    return f"anon:{session_id}"


class OneClarifyingQuestion(BaseModel):
    question: str = Field(
        description="A single short, concrete clarifying question that builds on any prior Q&A"
    )


class State(TypedDict):
    messages: Annotated[List[Any], add_messages]
    success_criteria: str
    feedback_on_work: Optional[str]
    success_criteria_met: bool
    user_input_needed: bool
    # Sequential clarification: one question per user turn, then worker
    clarification_complete: NotRequired[bool]
    clarification_questions_asked: NotRequired[int]
    clarification_transcript: NotRequired[str]
    clarification_task_snapshot: NotRequired[str]
    clarification_summary: NotRequired[Optional[str]]
    # Legacy checkpoints (older sidekick.py); treat >=2 as done
    clarification_phase: NotRequired[int]
    eval_loop_count: NotRequired[int]


class EvaluatorOutput(BaseModel):
    feedback: str = Field(description="Feedback on the assistant's response")
    success_criteria_met: bool = Field(description="Whether the success criteria have been met")
    user_input_needed: bool = Field(
        description="True if more input is needed from the user, or clarifications, or the assistant is stuck"
    )


class Sidekick:
    def __init__(self, thread_id: str):
        self.thread_id = thread_id
        self.worker_llm_with_tools = None
        self.evaluator_llm_with_output = None
        self.clarifier_llm = None
        self.tools = None
        self.graph = None
        self.memory = None
        self.memory_context = None
        self.browser = None
        self.playwright = None

    async def setup(self):
        if self.memory is None:
            self.memory_context = AsyncSqliteSaver.from_conn_string(str(_CHECKPOINT_DB))
            self.memory = await self.memory_context.__aenter__()

        self.tools, self.browser, self.playwright = await playwright_tools()
        self.tools += await other_tools()
        llm_kwargs = {
            "model": "openai/gpt-4o-mini",
            "base_url": "https://openrouter.ai/api/v1",
            "api_key": os.getenv("OPENROUTER_API_KEY"),
        }
        worker_llm = ChatOpenAI(**llm_kwargs)
        self.worker_llm_with_tools = worker_llm.bind_tools(self.tools)
        evaluator_llm = ChatOpenAI(**llm_kwargs)
        self.evaluator_llm_with_output = evaluator_llm.with_structured_output(EvaluatorOutput)
        clarifier_llm = ChatOpenAI(**llm_kwargs)
        self.clarifier_llm = clarifier_llm.with_structured_output(OneClarifyingQuestion)
        await self.build_graph()

    @staticmethod
    def _last_human_text(state: State) -> str:
        for message in reversed(state["messages"]):
            if isinstance(message, HumanMessage):
                c = message.content
                return c if isinstance(c, str) else str(c)
        return ""

    @staticmethod
    def _last_clarifying_ai_text(state: State) -> str:
        """Most recent assistant message that is not evaluator feedback."""
        for message in reversed(state["messages"]):
            if isinstance(message, AIMessage):
                text = message.content or ""
                if isinstance(text, str) and text.startswith("Evaluator Feedback on this answer:"):
                    continue
                return text if isinstance(text, str) else str(text)
        return ""

    def _clarification_done(self, state: State) -> bool:
        if state.get("clarification_complete"):
            return True
        return state.get("clarification_phase", 0) >= 2

    def route_entry(self, state: State) -> Literal["sequential_clarify", "worker"]:
        if self._clarification_done(state):
            return "worker"
        return "sequential_clarify"

    def clarify_exit_router(self, state: State) -> Literal["worker", "END"]:
        return "worker" if state.get("clarification_complete") else "END"

    def sequential_clarify(self, state: State) -> Dict[str, Any]:
        """Ask one clarifying question at a time; each new question uses prior answers."""
        asked = state.get("clarification_questions_asked", 0)
        transcript = state.get("clarification_transcript") or ""
        criteria = state.get("success_criteria", "")

        if asked == 0:
            task = self._last_human_text(state)
            system_message = """You are a planning assistant. Before any tools run, you ask clarifying questions
one at a time. You output exactly ONE short question the user can answer in one message.
The user will answer; later you will get a follow-up turn to ask another question that builds on their answer."""

            human = f"""Original user request:\n{task}\n\nSuccess criteria:\n{criteria}\n\nPrior Q&A so far:\n(none — this is the first question)\n\nAsk question 1 of 3. Focus on the biggest ambiguity or risk of misunderstanding."""

            out = self.clarifier_llm.invoke(
                [SystemMessage(content=system_message), HumanMessage(content=human)]
            )
            body = f"**Question 1 of 3:** {out.question}"
            return {
                "messages": [AIMessage(content=body)],
                "clarification_questions_asked": 1,
                "clarification_task_snapshot": task,
                "clarification_transcript": transcript,
            }

        last_answer = self._last_human_text(state)
        last_question = self._last_clarifying_ai_text(state)
        task = state.get("clarification_task_snapshot") or self._last_human_text(state)

        transcript = f"{transcript}Q{asked}: {last_question}\nA{asked}: {last_answer}\n"

        if asked >= 3:
            summary = f"Clarifying Q&A (use for the rest of the task):\n{transcript}"
            return {
                "clarification_complete": True,
                "clarification_summary": summary,
                "clarification_transcript": transcript,
                "clarification_questions_asked": asked,
            }

        system_message = """You are a planning assistant. You ask clarifying questions one at a time.
Output exactly ONE new short question. It must logically build on the user's previous answers in the transcript—
narrow scope, resolve tradeoffs they hinted at, or ask the next most important detail. Never repeat a question
already in the transcript."""

        human = f"""Original user request:\n{task}\n\nSuccess criteria:\n{criteria}\n\nPrior Q&A so far:\n{transcript}\n\nAsk question {asked + 1} of 3 next. Make it depend on what they already said."""

        out = self.clarifier_llm.invoke(
            [SystemMessage(content=system_message), HumanMessage(content=human)]
        )
        body = f"**Question {asked + 1} of 3:** {out.question}"
        return {
            "messages": [AIMessage(content=body)],
            "clarification_questions_asked": asked + 1,
            "clarification_transcript": transcript,
        }

    def worker(self, state: State) -> Dict[str, Any]:
        clarification = state.get("clarification_summary") or ""
        system_message = f"""You are a helpful assistant that can use tools to complete tasks.
    You keep working on a task until either you have a question or clarification for the user, or the success criteria is met.
    You have many tools to help you, including tools to browse the internet, navigating and retrieving web pages.
    You have a tool to run python code, but note that you would need to include a print() statement if you wanted to receive output.
    The current date and time is {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

    {clarification}

    This is the success criteria:
    {state["success_criteria"]}
    You should reply either with a question for the user about this assignment, or with your final response.
    If you have a question for the user, you need to reply by clearly stating your question. An example might be:

    Question: please clarify whether you want a summary or a detailed answer

    If you've finished, reply with the final answer, and don't ask a question; simply reply with the answer.
    """

        if state.get("feedback_on_work"):
            system_message += f"""
    Previously you thought you completed the assignment, but your reply was rejected because the success criteria was not met.
    Here is the feedback on why this was rejected:
    {state["feedback_on_work"]}
    With this feedback, please continue the assignment, ensuring that you meet the success criteria or have a question for the user."""

        found_system_message = False
        msgs = state["messages"]
        for message in msgs:
            if isinstance(message, SystemMessage):
                message.content = system_message
                found_system_message = True

        if not found_system_message:
            msgs = [SystemMessage(content=system_message)] + list(msgs)

        response = self.worker_llm_with_tools.invoke(msgs)
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
                text = message.content or "[Tools use]"
                conversation += f"Assistant: {text}\n"
        return conversation

    def evaluator(self, state: State) -> State:
        last_response = state["messages"][-1].content

        system_message = """You are an evaluator that determines if a task has been completed successfully by an Assistant.
    Assess the Assistant's last response based on the given criteria. Respond with your feedback, and with your decision on whether the success criteria has been met,
    and whether more input is needed from the user."""

        user_message = f"""You are evaluating a conversation between the User and Assistant. You decide what action to take based on the last response from the Assistant.

    The entire conversation with the assistant, with the user's original request and all replies, is:
    {self.format_conversation(state["messages"])}

    The success criteria for this assignment is:
    {state["success_criteria"]}

    And the final response from the Assistant that you are evaluating is:
    {last_response}

    Respond with your feedback, and decide if the success criteria is met by this response.
    Also, decide if more user input is required, either because the assistant has a question, needs clarification, or seems to be stuck and unable to answer without help.

    The Assistant has access to a tool to write files. If the Assistant says they have written a file, then you can assume they have done so.
    Overall you should give the Assistant the benefit of the doubt if they say they've done something. But you should reject if you feel that more work should go into this.

    """
        if state.get("feedback_on_work"):
            user_message += f"Also, note that in a prior attempt from the Assistant, you provided this feedback: {state['feedback_on_work']}\n"
            user_message += "If you're seeing the Assistant repeating the same mistakes, then consider responding that user input is required."

        evaluator_messages = [
            SystemMessage(content=system_message),
            HumanMessage(content=user_message),
        ]

        eval_result = self.evaluator_llm_with_output.invoke(evaluator_messages)

        n = state.get("eval_loop_count", 0)
        if eval_result.success_criteria_met or eval_result.user_input_needed:
            next_n = 0
        elif n >= _MAX_WORKER_EVAL_LOOPS:
            eval_result = EvaluatorOutput(
                feedback=(
                    f"{eval_result.feedback}\n\n"
                    f"[Stopped after {_MAX_WORKER_EVAL_LOOPS} revise cycles because the evaluator kept "
                    "asking for more work without requesting user input. Try narrowing your success "
                    "criteria or send a follow-up message.]"
                ),
                success_criteria_met=True,
                user_input_needed=False,
            )
            next_n = 0
        else:
            next_n = n + 1

        return {
            "messages": [
                {
                    "role": "assistant",
                    "content": f"Evaluator Feedback on this answer: {eval_result.feedback}",
                }
            ],
            "feedback_on_work": eval_result.feedback,
            "success_criteria_met": eval_result.success_criteria_met,
            "user_input_needed": eval_result.user_input_needed,
            "eval_loop_count": next_n,
        }

    def route_based_on_evaluation(self, state: State) -> str:
        if state["success_criteria_met"] or state["user_input_needed"]:
            return "END"
        return "worker"

    async def build_graph(self):
        graph_builder = StateGraph(State)
        graph_builder.add_node("sequential_clarify", self.sequential_clarify)
        graph_builder.add_node("worker", self.worker)
        graph_builder.add_node("tools", ToolNode(tools=self.tools))
        graph_builder.add_node("evaluator", self.evaluator)

        graph_builder.add_conditional_edges(
            START,
            self.route_entry,
            {"sequential_clarify": "sequential_clarify", "worker": "worker"},
        )
        graph_builder.add_conditional_edges(
            "sequential_clarify",
            self.clarify_exit_router,
            {"worker": "worker", "END": END},
        )
        graph_builder.add_conditional_edges(
            "worker", self.worker_router, {"tools": "tools", "evaluator": "evaluator"}
        )
        graph_builder.add_edge("tools", "worker")
        graph_builder.add_conditional_edges(
            "evaluator", self.route_based_on_evaluation, {"worker": "worker", "END": END}
        )

        self.graph = graph_builder.compile(checkpointer=self.memory)

    async def clear_thread_checkpoint_async(self) -> None:
        if self.memory:
            await self.memory.adelete_thread(self.thread_id)

    async def run_superstep(self, message: str, success_criteria: str, history: list):
        config = {"configurable": {"thread_id": self.thread_id}}

        criteria = success_criteria or "The answer should be clear and accurate"
        state: Dict[str, Any] = {
            "messages": [HumanMessage(content=message)],
            "success_criteria": criteria,
            "feedback_on_work": None,
            "success_criteria_met": False,
            "user_input_needed": False,
            "eval_loop_count": 0,
        }

        result = await self.graph.ainvoke(
            state,
            config={**config, "recursion_limit": _GRAPH_RECURSION_LIMIT},
        )

        user = {"role": "user", "content": message}
        msgs = result["messages"]
        last = msgs[-1]
        last_content = getattr(last, "content", None) or (isinstance(last, dict) and last.get("content")) or ""

        if isinstance(last_content, str) and last_content.startswith("Evaluator Feedback on this answer:"):
            reply_msg = msgs[-2]
            reply_text = getattr(reply_msg, "content", None) or str(reply_msg)
            return history + [user, {"role": "assistant", "content": reply_text}, {"role": "assistant", "content": last_content}]

        reply_msg = last
        reply_text = getattr(reply_msg, "content", None) or str(reply_msg)
        return history + [user, {"role": "assistant", "content": reply_text}]

    async def cleanup_async(self):
        if self.browser:
            await self.browser.close()
            if self.playwright:
                await self.playwright.stop()
        if self.memory_context:
            await self.memory_context.__aexit__(None, None, None)
            self.memory_context = None
            self.memory = None

    def cleanup(self):
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(self.cleanup_async())
        except RuntimeError:
            asyncio.run(self.cleanup_async())
