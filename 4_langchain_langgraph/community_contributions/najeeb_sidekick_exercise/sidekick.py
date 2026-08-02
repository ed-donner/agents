from __future__ import annotations

import asyncio
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Annotated, Any, Dict, List, Optional

import aiosqlite
from dotenv import load_dotenv
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from pydantic import BaseModel, Field
from typing_extensions import TypedDict

from sidekick_tools import other_tools, playwright_tools

load_dotenv(override=True)
api_key = os.getenv("OPENAI_API_KEY")
base_url = "https://openrouter.ai/api/v1"

DEFAULT_CHECKPOINT_PATH = Path(__file__).resolve().parent / "sidekick_checkpoints.sqlite"


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


class ClarifyingQuestions(BaseModel):
    questions: list[str] = Field(
        description="Exactly three clarifying questions to narrow scope before work begins.",
        min_length=3,
        max_length=3,
    )


def build_fulfillment_message(
    user_request: str,
    success_criteria: str,
    questions: List[str],
    answers: List[str],
) -> str:
    lines = [
        f"User request:\n{user_request.strip()}",
        "",
        f"Success criteria:\n{success_criteria.strip() or 'The answer should be clear and accurate'}",
        "",
        "Clarifying questions and user answers:",
    ]
    for i, (q, a) in enumerate(zip(questions, answers, strict=True), start=1):
        lines.append(f"{i}. Question: {q}")
        lines.append(f"   Answer: {a}")
        lines.append("")
    return "\n".join(lines).strip()


class Sidekick:
    def __init__(self):
        self.worker_llm_with_tools = None
        self.evaluator_llm_with_output = None
        self.clarifier_llm = None
        self.tools = None
        self.graph = None
        self.sidekick_id = str(uuid.uuid4())
        self.checkpointer: AsyncSqliteSaver | None = None
        self._sqlite_conn: aiosqlite.Connection | None = None
        self.browser = None
        self.playwright = None

    async def setup(self):
        self.tools, self.browser, self.playwright = await playwright_tools()
        self.tools += await other_tools()
        worker_llm = ChatOpenAI(model="gpt-4o-mini", base_url=base_url, api_key=api_key)
        self.worker_llm_with_tools = worker_llm.bind_tools(self.tools)
        evaluator_llm = ChatOpenAI(model="gpt-4o-mini", base_url=base_url, api_key=api_key)
        self.evaluator_llm_with_output = evaluator_llm.with_structured_output(EvaluatorOutput)
        clarifier_llm = ChatOpenAI(model="gpt-4o-mini", base_url=base_url, api_key=api_key)
        self.clarifier_llm = clarifier_llm.with_structured_output(ClarifyingQuestions)

        db_path = os.getenv("SIDEKICK_CHECKPOINT_DB", str(DEFAULT_CHECKPOINT_PATH))
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self._sqlite_conn = await aiosqlite.connect(db_path)
        self.checkpointer = AsyncSqliteSaver(self._sqlite_conn)
        await self.checkpointer.setup()

        await self.build_graph()

    async def propose_clarifications(self, user_request: str, success_criteria: str) -> ClarifyingQuestions:
        """Produce three clarifying questions before the main worker graph runs."""
        system = SystemMessage(
            content=(
                "You are preparing to help the user. Given their request and success criteria, "
                "propose exactly three specific clarifying questions that will narrow scope, "
                "constraints, or definition of done. Questions should be concise and answerable."
            )
        )
        human = HumanMessage(
            content=(
                f"User request:\n{user_request.strip()}\n\n"
                f"Success criteria:\n{(success_criteria or 'The answer should be clear and accurate').strip()}"
            )
        )
        return self.clarifier_llm.invoke([system, human])

    def worker(self, state: State) -> Dict[str, Any]:
        system_message = f"""You are a helpful assistant that can use tools to complete tasks.
    You keep working on a task until either you have a question or clarification for the user, or the success criteria is met.
    You have many tools to help you, including tools to browse the internet, navigating and retrieving web pages.
    You have a tool to run python code, but note that you would need to include a print() statement if you wanted to receive output.
    The current date and time is {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

    The user's message may include clarifying questions and their answers—use those to align your work.

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
        messages = state["messages"]
        for message in messages:
            if isinstance(message, SystemMessage):
                message.content = system_message
                found_system_message = True

        if not found_system_message:
            messages = [SystemMessage(content=system_message)] + messages

        response = self.worker_llm_with_tools.invoke(messages)

        return {
            "messages": [response],
        }

    def worker_router(self, state: State) -> str:
        last_message = state["messages"][-1]

        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            return "tools"
        else:
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
        if state["feedback_on_work"]:
            user_message += f"Also, note that in a prior attempt from the Assistant, you provided this feedback: {state['feedback_on_work']}\n"
            user_message += "If you're seeing the Assistant repeating the same mistakes, then consider responding that user input is required."

        evaluator_messages = [
            SystemMessage(content=system_message),
            HumanMessage(content=user_message),
        ]

        eval_result = self.evaluator_llm_with_output.invoke(evaluator_messages)
        new_state = {
            "messages": [
                {
                    "role": "assistant",
                    "content": f"Evaluator Feedback on this answer: {eval_result.feedback}",
                }
            ],
            "feedback_on_work": eval_result.feedback,
            "success_criteria_met": eval_result.success_criteria_met,
            "user_input_needed": eval_result.user_input_needed,
        }
        return new_state

    def route_based_on_evaluation(self, state: State) -> str:
        if state["success_criteria_met"] or state["user_input_needed"]:
            return "END"
        else:
            return "worker"

    async def build_graph(self):
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

        self.graph = graph_builder.compile(checkpointer=self.checkpointer)

    async def run_superstep(
        self,
        message: str,
        success_criteria: str,
        history: list,
        clarifying_questions: List[str] | None,
        answers: List[str] | None,
    ):
        if not clarifying_questions or len(clarifying_questions) != 3:
            raise ValueError("Provide exactly three clarifying questions from Get clarifying questions.")
        if not answers or len(answers) != 3:
            raise ValueError("Provide exactly three answers before running.")

        content = build_fulfillment_message(message, success_criteria or "", clarifying_questions, answers)
        config = {"configurable": {"thread_id": self.sidekick_id}}

        state = {
            "messages": [HumanMessage(content=content)],
            "success_criteria": success_criteria or "The answer should be clear and accurate",
            "feedback_on_work": None,
            "success_criteria_met": False,
            "user_input_needed": False,
        }
        result = await self.graph.ainvoke(state, config=config)

        messages = result["messages"]
        last = messages[-1]
        prev = messages[-2]
        last_content = last.get("content") if isinstance(last, dict) else getattr(last, "content", None)
        prev_content = prev.get("content") if isinstance(prev, dict) else getattr(prev, "content", None)

        user = {"role": "user", "content": content}
        reply = {"role": "assistant", "content": prev_content}
        feedback = {"role": "assistant", "content": last_content}
        return history + [user, reply, feedback]

    async def _close_sqlite(self) -> None:
        if self._sqlite_conn is not None:
            await self._sqlite_conn.close()
            self._sqlite_conn = None
            self.checkpointer = None

    def cleanup(self):
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
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(self._close_sqlite())
        except RuntimeError:
            asyncio.run(self._close_sqlite())
