from typing import Annotated
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from dotenv import load_dotenv
from langgraph.prebuilt import ToolNode
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
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
    clarifying_done: bool
    attempt_count: int


class EvaluatorOutput(BaseModel):
    feedback: str = Field(description="Feedback on the assistant's response")
    success_criteria_met: bool = Field(
        description="Whether the success criteria have been met"
    )
    user_input_needed: bool = Field(
        description="True if more input is needed from the user, or clarifications, or the assistant is stuck"
    )


class Sidekick:
    def __init__(self):
        self.worker_llm_with_tools = None
        self.evaluator_llm_with_output = None
        self.clarifier_llm = None
        self.tools = None
        self.llm_with_tools = None
        self.graph = None
        self.sidekick_id = str(uuid.uuid4())
        self.memory_ctx = None
        self.memory = None
        self.browser = None
        self.playwright = None

    async def setup(self):
        if self.memory is None:
            self.memory_ctx = AsyncSqliteSaver.from_conn_string("sidekick_memory.db")
            self.memory = await self.memory_ctx.__aenter__()

        self.tools, self.browser, self.playwright = await playwright_tools()
        self.tools += await other_tools()

        worker_llm = ChatOpenAI(model="gpt-4o-mini")
        self.worker_llm_with_tools = worker_llm.bind_tools(self.tools)

        evaluator_llm = ChatOpenAI(model="gpt-4o-mini")
        self.evaluator_llm_with_output = evaluator_llm.with_structured_output(
            EvaluatorOutput
        )

        self.clarifier_llm = ChatOpenAI(model="gpt-4o-mini")

        await self.build_graph()

    # ---------- NEW CLARIFIER NODE ----------

    def clarifier(self, state: State) -> Dict[str, Any]:
        """
        First-turn node: asks exactly three clarifying questions and then stops.
        It does NOT use tools and is NOT evaluated by the evaluator.
        """
        system_message = f"""You are a clarifying assistant whose ONLY job is to ask the user exactly three clarifying questions about their task before any work is started.

Rules:
- Ask exactly 3 questions, no more and no fewer.
- Do NOT attempt to solve the task.
- Do NOT give explanations, summaries, or greetings.
- Your message MUST contain only the three questions.

Use this exact format:

Q1: <first question>
Q2: <second question>
Q3: <third question>

Take into account the user's most recent message and, if helpful, this success criteria:

Success criteria:
{state["success_criteria"]}
"""

        messages = state["messages"]
        found_system_message = False
        for message in messages:
            if isinstance(message, SystemMessage):
                message.content = system_message
                found_system_message = True

        if not found_system_message:
            messages = [SystemMessage(content=system_message)] + messages

        response = self.clarifier_llm.invoke(messages)

        return {
            "messages": [response],
            "clarifying_done": True,
        }

    # ---------- WORKER / TOOLS / EVALUATOR AS BEFORE ----------

    def worker(self, state: State) -> Dict[str, Any]:
        system_message = f"""You are a helpful assistant that can use tools to complete tasks.
    You keep working on a task until either you have a question or clarification for the user, or the success criteria is met.
    You have many tools to help you, including tools to browse the internet, navigating and retrieving web pages.
    You have a tool to run python code, but note that you would need to include a print() statement if you wanted to receive output.
    The current date and time is {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

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

        # Add in the system message

        found_system_message = False
        messages = state["messages"]
        for message in messages:
            if isinstance(message, SystemMessage):
                message.content = system_message
                found_system_message = True

        if not found_system_message:
            messages = [SystemMessage(content=system_message)] + messages

        # Invoke the LLM with tools
        response = self.worker_llm_with_tools.invoke(messages)

        # Return updated state
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
            elif isinstance(message, dict):
                role = message.get("role", "assistant")
                content = message.get("content", "")
                conversation += f"{role.capitalize()}: {content}\n"
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

        # NEW: increment attempt counter
        prev_attempts = state.get("attempt_count", 0)
        attempts = prev_attempts + 1

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
            "attempt_count": attempts,   # NEW
        }
        return new_state
    
    def route_based_on_evaluation(self, state: State) -> str:
        attempts = state.get("attempt_count", 0)

        # If we've already tried 3 times, stop looping and accept the last answer.
        if attempts >= 3:
            return "END"

        if state["success_criteria_met"] or state["user_input_needed"]:
            return "END"
        else:
            return "worker"

    # ---------- ENTRY ROUTER FOR FIRST-TURN CLARIFIER ----------

    def entry_router(self, state: State) -> str:
        """
        Decides whether to start at the clarifier (first turn) or the worker (later turns).
        """
        if state.get("clarifying_done"):
            return "worker"
        else:
            return "clarifier"

    async def build_graph(self):
        # Set up Graph Builder with State
        graph_builder = StateGraph(State)

        # Nodes
        graph_builder.add_node("clarifier", self.clarifier)
        graph_builder.add_node("worker", self.worker)
        graph_builder.add_node("tools", ToolNode(tools=self.tools))
        graph_builder.add_node("evaluator", self.evaluator)

        # START → clarifier or worker, depending on flag
        graph_builder.add_conditional_edges(
            START,
            self.entry_router,
            {"clarifier": "clarifier", "worker": "worker"},
        )

        # Clarifier simply ends the graph for that turn
        graph_builder.add_edge("clarifier", END)

        # Worker / tools / evaluator loop as before
        graph_builder.add_conditional_edges(
            "worker", self.worker_router, {"tools": "tools", "evaluator": "evaluator"}
        )
        graph_builder.add_edge("tools", "worker")
        graph_builder.add_conditional_edges(
            "evaluator",
            self.route_based_on_evaluation,
            {"worker": "worker", "END": END},
        )

        # Compile the graph with checkpointing
        self.graph = graph_builder.compile(checkpointer=self.memory)

    async def run_superstep(self, message, success_criteria, history):
        """
        message: current user text (string)
        success_criteria: text from box (string)
        history: list of {"role": ..., "content": ...} for Gradio Chatbot display
        """
        config = {"configurable": {"thread_id": self.sidekick_id}}

        # Always treat new input as a fresh HumanMessage;
        # previous turns are pulled from the checkpointer.
        state = {
            "messages": [HumanMessage(content=message)],
            "success_criteria": success_criteria
            or "The answer should be clear and accurate",
            "feedback_on_work": None,
            "success_criteria_met": False,
            "user_input_needed": False,
            # clarifying_done is intentionally omitted so stored value in checkpoint is used
        }

        result = await self.graph.ainvoke(state, config=config)

        user = {"role": "user", "content": message}

        def get_msg_content(msg: Any) -> str:
            """Safely extract content from AIMessage/HumanMessage/SystemMessage or dict."""
            if isinstance(msg, (AIMessage, HumanMessage, SystemMessage)):
                return msg.content
            if isinstance(msg, dict):
                return msg.get("content", "")
            # Fallback, just in case
            return str(msg)

        # If evaluator has run, feedback_on_work will be non-None OR flags will be set
        if (
            result.get("feedback_on_work") is not None
            or result.get("success_criteria_met")
            or result.get("user_input_needed")
        ):
            # Normal worker + evaluator turn
            worker_msg = result["messages"][-2]
            eval_msg = result["messages"][-1]

            worker_content = get_msg_content(worker_msg)
            eval_content = get_msg_content(eval_msg)

            reply = {"role": "assistant", "content": worker_content}
            feedback = {"role": "assistant", "content": eval_content}
            return history + [user, reply, feedback]

        else:
            # Clarifier-only turn: just send the clarifying questions
            last_msg = result["messages"][-1]
            reply_content = get_msg_content(last_msg)
            reply = {"role": "assistant", "content": reply_content}
            return history + [user, reply]

    def cleanup(self):
        if self.browser:
            try:
                loop = asyncio.get_running_loop()
                loop.create_task(self.browser.close())
                if self.playwright:
                    loop.create_task(self.playwright.stop())
            except RuntimeError:
                # If no loop is running, do a direct run
                asyncio.run(self.browser.close())
                if self.playwright:
                    asyncio.run(self.playwright.stop())
