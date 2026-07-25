from typing import Annotated, List, Any, Optional, Dict
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.memory import MemorySaver
from langchain_openai import ChatOpenAI
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from sidekick_tools import playwright_tools, other_tools
from datetime import datetime
import asyncio
import uuid

load_dotenv(override=True)


class State(TypedDict):
    messages: Annotated[List[Any], add_messages]
    success_criteria: str
    feedback_on_work: Optional[str]
    success_criteria_met: bool
    user_input_needed: bool


class EvaluatorOutput(BaseModel):
    feedback: str = Field(description="Feedback on the assistant's response")
    success_criteria_met: bool = Field(
        description="Whether the success criteria have been met"
    )
    user_input_needed: bool = Field(
        description=(
            "True if more input is needed from the user, "
            "or the assistant needs clarification, or is stuck"
        )
    )


class Sidekick:
    def __init__(self):
        self.worker_llm_with_tools = None
        self.evaluator_llm_with_output = None
        self.tools = None
        self.graph = None
        self.sidekick_id = str(uuid.uuid4())
        self.memory = MemorySaver()
        self.browser = None
        self.playwright = None
        self.awaiting_clarification = False

    async def setup(self):
        self.tools, self.browser, self.playwright = await playwright_tools()
        self.tools += await other_tools()

        worker_llm = ChatOpenAI(model="gpt-4o-mini")
        self.worker_llm_with_tools = worker_llm.bind_tools(self.tools)

        evaluator_llm = ChatOpenAI(model="gpt-4o-mini")
        self.evaluator_llm_with_output = evaluator_llm.with_structured_output(
            EvaluatorOutput
        )

        await self.build_graph()

    def worker(self, state: State) -> Dict[str, Any]:
        system_message = f"""You are Forge, a sharp and practical AI sidekick built for a software engineer.
You help with three main areas:

1. **Debugging**: Diagnose errors, trace root causes, suggest fixes, and reproduce issues with code.
   - When given an error or bug, search for it, read relevant docs or Stack Overflow threads, and provide a clear diagnosis and fix.
   - You can run Python code directly to test hypotheses.

2. **Docs Lookup**: Find and summarise official documentation, API references, changelogs, and guides.
   - Search the web and navigate to official docs pages. Extract the relevant information clearly.
   - Cite the source URL when you find useful documentation.

3. **Email Drafting**: Draft professional, concise engineering-related emails.
   - This includes emails to colleagues, managers, clients, or vendors about technical topics,
     incident reports, status updates, feature proposals, or schedule changes.
   - Save drafts to a file in the sandbox folder so the user can review them.

General behaviour:
- Be direct and precise. Skip filler. Get to the point.
- When browsing, prefer official documentation over random blog posts.
- If you write a file (e.g. a draft email or a code snippet), confirm the filename and location.
- The current date and time is {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

Success criteria for this task:
{state["success_criteria"]}

Clarifying questions:
- Only ask a clarifying question if you genuinely cannot proceed without the answer.
- Ask at most ONE question at a time. Be specific.
- Format it exactly as: Question: <your question>
- Do NOT ask a question if you have enough information to make reasonable assumptions.

If you previously asked a clarifying question and the user has now replied (visible in the conversation history),
use their answer to continue working. Do not ask again — proceed directly to completing the task.

Otherwise, provide your complete final answer.
"""

        if state.get("feedback_on_work"):
            system_message += f"""
A previous attempt was rejected because the success criteria was not met.
Feedback from the evaluator:
{state["feedback_on_work"]}

Review this feedback carefully and continue working to meet the success criteria.
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
        return "evaluator"

    def format_conversation(self, messages: List[Any]) -> str:
        conversation = "Conversation history:\n\n"
        for message in messages:
            if isinstance(message, HumanMessage):
                conversation += f"User: {message.content}\n"
            elif isinstance(message, AIMessage):
                text = message.content or "[Tool use]"
                conversation += f"Forge: {text}\n"
        return conversation

    def evaluator(self, state: State) -> State:
        last_response = state["messages"][-1].content

        system_message = """You are an evaluator assessing whether Forge (an AI sidekick for a software engineer)
has fully completed its assigned task. Be practical: if the response is thorough, accurate, and directly
addresses the request, mark it as successful. Only reject if there are clear gaps."""

        user_message = f"""Evaluate the following conversation between the User and Forge.

{self.format_conversation(state["messages"])}

Success criteria:
{state["success_criteria"]}

Forge's final response:
{last_response}

Decide:
1. Has the success criteria been met?
2. Is more user input needed (e.g. Forge asked a question, needs clarification, or is stuck)?

Notes:
- If Forge says it wrote a file, trust that it did.
- If Forge provided a debugging diagnosis and fix, that counts even if untested.
- If Forge drafted an email and saved it, that counts.
- If Forge cited documentation and summarised it clearly, that counts.
- Give Forge the benefit of the doubt for reasonable answers. Only reject for clear deficiencies.
"""

        if state["feedback_on_work"]:
            user_message += (
                f"\nPrior feedback given: {state['feedback_on_work']}\n"
                "If Forge is repeating the same mistake, mark user input as needed."
            )

        eval_result = self.evaluator_llm_with_output.invoke([
            SystemMessage(content=system_message),
            HumanMessage(content=user_message),
        ])

        return {
            "messages": [{
                "role": "assistant",
                "content": f"Forge Evaluator: {eval_result.feedback}",
            }],
            "feedback_on_work": eval_result.feedback,
            "success_criteria_met": eval_result.success_criteria_met,
            "user_input_needed": eval_result.user_input_needed,
        }

    def route_based_on_evaluation(self, state: State) -> str:
        if state["success_criteria_met"] or state["user_input_needed"]:
            return "END"
        return "worker"

    async def build_graph(self):
        graph_builder = StateGraph(State)

        graph_builder.add_node("worker", self.worker)
        graph_builder.add_node("tools", ToolNode(tools=self.tools))
        graph_builder.add_node("evaluator", self.evaluator)

        graph_builder.add_edge(START, "worker")
        graph_builder.add_conditional_edges(
            "worker", self.worker_router, {"tools": "tools", "evaluator": "evaluator"}
        )
        graph_builder.add_edge("tools", "worker")
        graph_builder.add_conditional_edges(
            "evaluator",
            self.route_based_on_evaluation,
            {"worker": "worker", "END": END},
        )

        self.graph = graph_builder.compile(checkpointer=self.memory)

    async def run_superstep(self, message, success_criteria, history):
        config = {"configurable": {"thread_id": self.sidekick_id}}

        state = {
            "messages": message,
            "success_criteria": success_criteria or "The response is accurate, complete, and directly addresses the request.",
            "feedback_on_work": None,
            "success_criteria_met": False,
            "user_input_needed": False,
        }

        result = await self.graph.ainvoke(state, config=config)

        self.awaiting_clarification = result.get("user_input_needed", False)

        user = {"role": "user", "content": message}
        reply = {"role": "assistant", "content": result["messages"][-2].content}
        feedback = {"role": "assistant", "content": result["messages"][-1].content}
        return history + [user, reply, feedback], self.awaiting_clarification

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
