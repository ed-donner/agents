from typing import Annotated
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from dotenv import load_dotenv
from langgraph.prebuilt import ToolNode
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from typing import List, Any, Optional, Dict
from pydantic import BaseModel, Field
from sidekick_tools import playwright_tools, other_tools
import uuid
import asyncio
from datetime import datetime

load_dotenv(override=True)


def _human_turns_plain_text(messages: List[Any]) -> str:
    """Collect user text only — safe to send to APIs that reject orphaned tool_calls in AIMessages."""
    parts: List[str] = []
    for m in messages:
        if isinstance(m, HumanMessage):
            c = m.content
            if isinstance(c, str) and c.strip():
                parts.append(c.strip())
            elif c is not None:
                parts.append(str(c).strip())
    return "\n\n".join(parts) if parts else "(No user message provided.)"


def _format_plan_text(plan: Any) -> Optional[str]:
    """Build readable plan text from PlanOutput, dict (checkpoint), or None."""
    if plan is None:
        return None
    if isinstance(plan, dict):
        steps = plan.get("list_of_steps") or []
        complexity = plan.get("estimated_complexity") or ""
    else:
        steps = getattr(plan, "list_of_steps", None) or []
        complexity = getattr(plan, "estimated_complexity", "") or ""
    if not steps:
        return None
    lines = "\n".join(f"{i + 1}. {s}" for i, s in enumerate(steps))
    return f"{lines}\n\n*Estimated complexity:* {complexity}".strip()


def _plan_text_from_messages(messages: List[Any]) -> Optional[str]:
    """Fallback: planner stores the plan in an AIMessage starting with 'Plan:'."""
    for m in messages:
        if not isinstance(m, AIMessage) or not m.content:
            continue
        text = str(m.content).strip()
        if text.startswith("Plan:"):
            return text
    return None


class PlanOutput(BaseModel):
    list_of_steps: List[str] = Field(description="Steps to accomplish the user's request, in order")
    estimated_complexity: str = Field(
        description="Brief estimate of how hard or time-consuming the plan is (e.g. low/medium/high)"
    )


class State(TypedDict):
    messages: Annotated[List[Any], add_messages]
    success_criteria: str
    feedback_on_work: Optional[str]
    success_criteria_met: bool
    user_input_needed: bool
    plan: Optional[PlanOutput]
    final_worker_response: Optional[str]


class EvaluatorOutput(BaseModel):
    feedback: str = Field(description="Feedback on the assistant's response")
    success_criteria_met: bool = Field(description="Whether the success criteria have been met")
    user_input_needed: bool = Field(
        description="True if more input is needed from the user, or clarifications, or the assistant is stuck"
    )


class Sidekick:
    def __init__(self):
        self.worker_llm_with_tools = None
        self.planner_llm = None
        self.evaluator_llm_with_output = None
        self.tools = None
        self.graph = None
        self.sidekick_id = str(uuid.uuid4())
        self.memory = MemorySaver()
        self.browser = None
        self.playwright = None

    async def setup(self):
        browser_tools, self.browser, self.playwright = await playwright_tools()
        self.tools = list(browser_tools) + await other_tools()
        worker_llm = ChatOpenAI(model="gpt-4o-mini")
        self.worker_llm_with_tools = worker_llm.bind_tools(self.tools)
        planner_base = ChatOpenAI(model="gpt-4o-mini")
        self.planner_llm = planner_base.with_structured_output(PlanOutput)
        evaluator_llm = ChatOpenAI(model="gpt-4o-mini")
        self.evaluator_llm_with_output = evaluator_llm.with_structured_output(EvaluatorOutput)
        await self.build_graph()

    def planner(self, state: State) -> Dict[str, Any]:
        system_message = f"""You are a planner. Given the user's request and success criteria, produce a concrete ordered list of steps
    the worker should follow. Steps should be actionable (what to do or find), not vague.
    The worker has tools: web browser (Playwright), web search (Serper), fetch URL as text, Wikipedia, a safe calculator,
    current time (IANA timezones), Python REPL, file read/write under the sandbox folder, and optional push notifications.
    The current date and time is {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}.
    Success criteria for this task:
    {state["success_criteria"]}
    """

        # Do not forward raw AIMessages from graph state: they may include tool_calls without
        # the following ToolMessages (e.g. after checkpoint merge), which OpenAI rejects.
        messages = [
            SystemMessage(content=system_message),
            HumanMessage(
                content=(
                    "Plan for the following user request(s). "
                    "If there are several blocks, the latest block is the current turn.\n\n"
                    + _human_turns_plain_text(state["messages"])
                )
            ),
        ]

        plan = self.planner_llm.invoke(messages)
        summary = (
            "Plan:\n"
            + "\n".join(f"{i + 1}. {step}" for i, step in enumerate(plan.list_of_steps))
            + f"\n\nEstimated complexity: {plan.estimated_complexity}"
        )
        return {
            "messages": [AIMessage(content=summary)],
            "plan": plan,
        }

    def worker(self, state: State) -> Dict[str, Any]:
        plan = state["plan"]
        plan_block = ""
        if plan is not None:
            plan_block = f"""
    You received a plan for this request (follow the steps in order):
    Steps: {plan.list_of_steps}
    Estimated complexity: {plan.estimated_complexity}
    """

        system_message = f"""You are a helpful assistant that can use tools to complete tasks.
    You keep working on a task until either you have a question or clarification for the user, or the success criteria is met.
    You have many tools to help you, including browser automation, web search, fetching URL text, Wikipedia, a calculator, and timezone clock.
    You have a tool to run python code, but note that you would need to include a print() statement if you wanted to receive output.
    The current date and time is {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
    {plan_block}
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

        current_response = (
            response.content
            if isinstance(response, AIMessage) and response.content
            else state.get("final_worker_response")
        )
        return {
            "messages": [response],
            "final_worker_response": current_response,
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

        graph_builder.add_node("planner", self.planner)
        graph_builder.add_node("worker", self.worker)
        graph_builder.add_node("tools", ToolNode(tools=self.tools))
        graph_builder.add_node("evaluator", self.evaluator)

        graph_builder.add_edge(START, "planner")
        graph_builder.add_edge("planner", "worker")
        graph_builder.add_conditional_edges(
            "worker", self.worker_router, {"tools": "tools", "evaluator": "evaluator"}
        )
        graph_builder.add_edge("tools", "worker")
        graph_builder.add_conditional_edges(
            "evaluator", self.route_based_on_evaluation, {"worker": "worker", "END": END}
        )

        self.graph = graph_builder.compile(checkpointer=self.memory)

    async def run_superstep(self, message, success_criteria, history):
        config = {"configurable": {"thread_id": self.sidekick_id}}

        user_content = message if isinstance(message, str) else str(message)
        state = {
            "messages": [HumanMessage(content=user_content)],
            "success_criteria": success_criteria or "The answer should be clear and accurate",
            "feedback_on_work": None,
            "success_criteria_met": False,
            "user_input_needed": False,
            "plan": None,
            "final_worker_response": None,
        }
        result = await self.graph.ainvoke(state, config=config)

        msgs = result.get("messages") or []
        plan_text = _format_plan_text(result.get("plan")) or _plan_text_from_messages(msgs)

        worker_text = (result.get("final_worker_response") or "").strip()

        feedback_text = result.get("feedback_on_work") or ""
        user = {"role": "user", "content": user_content}

        out: List[Dict[str, str]] = [user]
        if plan_text:
            out.append(
                {
                    "role": "assistant",
                    "content": f"### Plan\n\n{plan_text}",
                }
            )
        out.append(
            {
                "role": "assistant",
                "content": worker_text or "[No assistant text]",
            }
        )
        out.append(
            {
                "role": "assistant",
                "content": f"**Evaluator:** {feedback_text}",
            }
        )
        return history + out

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
