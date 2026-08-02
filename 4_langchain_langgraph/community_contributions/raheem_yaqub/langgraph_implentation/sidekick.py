from pathlib import Path

from typing import Annotated
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from dotenv import load_dotenv
from langgraph.prebuilt import ToolNode
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
import aiosqlite
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from typing import List, Any, Optional, Dict
from pydantic import BaseModel, Field
from sidekick_tools import playwright_tools, other_tools
import uuid
import asyncio
from datetime import datetime

load_dotenv(override=True)


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
        description="True if more input is needed from the user"
    )


class Sidekick:
    def __init__(self):
        self.worker_llm_with_tools = None
        self.evaluator_llm_with_output = None
        self.tools = None
        self.llm_with_tools = None
        self.graph = None
        self.sidekick_id = str(uuid.uuid4())
        self.memory = None
        self._sqlite_conn = None

        self.browser = None
        self.playwright = None

    async def setup(self):
        self.tools, self.browser, self.playwright = await playwright_tools()
        self.tools += await other_tools()

        db_path = Path(__file__).resolve().parent / "sidekick_checkpoints.sqlite"
        self._sqlite_conn = await aiosqlite.connect(str(db_path))
        self.memory = AsyncSqliteSaver(self._sqlite_conn)

        worker_llm = ChatOpenAI(model="openai/gpt-4o-mini")
        self.worker_llm_with_tools = worker_llm.bind_tools(self.tools)

        evaluator_llm = ChatOpenAI(model="openai/gpt-4o-mini")
        self.evaluator_llm_with_output = evaluator_llm.with_structured_output(EvaluatorOutput)

        await self.build_graph()

    def worker(self, state: State) -> Dict[str, Any]:

    #Clarifying + Planning + Tool Usage Guidance 

        system_message = f"""You are a helpful assistant that can use tools to complete tasks.

            IMPORTANT BEHAVIOR:
            - If the request is unclear, ask EXACTLY 3 clarifying questions and STOP.
            - If clear, proceed step-by-step.

            PLANNING:
            - For complex tasks, briefly break the task into steps before solving.
            - Choose the most efficient approach.

            TOOL USAGE (VERY IMPORTANT):
            You have access to tools. Use them whenever they improve accuracy.

            - Use "generate_report" when the user asks for reports, summaries, analytics, or structured output.
            - Use "sql_query" when the user asks for stored data, history, or database queries.
            - Use "search" when up-to-date or external information is needed.
            - Use "python" for calculations, transformations, or logic.

            RULES:
            - Do NOT guess when data is required → use tools.
            - Prefer tools over assumptions.
            - You can call multiple tools if needed.

            The current date and time is {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

            Success criteria:
            {state["success_criteria"]}

            If asking questions, format as:
            Question 1: ...
            Question 2: ...
            Question 3: ...

            If you've finished, return the final answer only.
        """

        messages = state["messages"]

        found_system_message = False
        for message in messages:
            if isinstance(message, SystemMessage):
                message.content = system_message
                found_system_message = True

        if not found_system_message:
            messages = [SystemMessage(content=system_message)] + messages

        response = self.worker_llm_with_tools.invoke(messages)

        return {"messages": [response]}

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

        system_message = """You are an evaluator...

        IMPORTANT:
        - If the assistant provides a reasonable answer, mark success_criteria_met = True.
        - Do NOT require perfection.
        - Avoid sending the assistant into loops.

        If the assistant used tools and produced a result, consider the task complete unless clearly incorrect.
        """

        user_message = f"""
Conversation:
{self.format_conversation(state["messages"])}

Criteria:
{state["success_criteria"]}

Response:
{last_response}
"""

        evaluator_messages = [
            SystemMessage(content=system_message),
            HumanMessage(content=user_message),
        ]

        eval_result = self.evaluator_llm_with_output.invoke(evaluator_messages)

        return {
            "messages": [
                {"role": "assistant", "content": f"Evaluator Feedback: {eval_result.feedback}"}
            ],
            "feedback_on_work": eval_result.feedback,
            "success_criteria_met": eval_result.success_criteria_met,
            "user_input_needed": eval_result.user_input_needed,
        }

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

        self.graph = graph_builder.compile(checkpointer=self.memory)

    async def run_superstep(self, message, success_criteria, history):
        config = {"configurable": {"thread_id": self.sidekick_id}}

        state = {
            "messages": message,
            "success_criteria": success_criteria or "The answer should be clear and accurate",
            "feedback_on_work": None,
            "success_criteria_met": False,
            "user_input_needed": False,
        }

        result = await self.graph.ainvoke(state, config=config)

        user = {"role": "user", "content": message}
        reply = {"role": "assistant", "content": result["messages"][-2].content}
        feedback = {"role": "assistant", "content": result["messages"][-1].content}

        return history + [user, reply, feedback], []

    def cleanup(self):
        if self._sqlite_conn is not None:
            conn = self._sqlite_conn
            self._sqlite_conn = None
            try:
                loop = asyncio.get_running_loop()

                async def _close() -> None:
                    await conn.close()

                loop.create_task(_close())
            except RuntimeError:
                asyncio.run(conn.close())
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
