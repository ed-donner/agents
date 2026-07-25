from typing import Annotated
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from dotenv import load_dotenv
from langgraph.prebuilt import ToolNode
from langchain_openai import ChatOpenAI
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from typing import List, Any, Optional, Dict
from pydantic import BaseModel, Field
from sidekick_tools import playwright_tools, other_tools
import uuid
import asyncio
from datetime import datetime
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver

load_dotenv(override=True)

DB_PATH = "memory.db"


class State(TypedDict):
    messages: Annotated[List[Any], add_messages]
    success_criteria: str
    feedback_on_work: Optional[str]
    success_criteria_met: bool
    user_input_needed: bool
    pending_question: Optional[str]


class EvaluatorOutput(BaseModel):
    feedback: str = Field(description="Feedback on the assistant's response")
    success_criteria_met: bool = Field(description="Whether the success criteria have been met")
    user_input_needed: bool = Field(
        description="True if more input is needed from the user, or clarifications, or the assistant is stuck"
    )
   
    pending_question: Optional[str] = Field(
        default=None,
        description="If the assistant asked a clarifying question, extract it verbatim here. Otherwise null."
    )


class Sidekick:
    def __init__(self, user_id: str = "default"):
        """
        user_id: a stable identifier for the user so that memory persists
                 across sessions. Pass a username/email from your auth layer,
                 or keep "default" for single-user setups.
        """
        self.worker_llm_with_tools = None
        self.evaluator_llm_with_output = None
        self.tools = None
        self.llm_with_tools = None
        self.graph = None
        # Use a stable ID tied to the user so the same thread is resumed across process restarts
        self.sidekick_id = f"user-{user_id}"
        self.browser = None
        self.playwright = None

    async def setup(self):
        self.tools, self.browser, self.playwright = await playwright_tools()
        self.tools += await other_tools()
        worker_llm = ChatOpenAI(model="gpt-4o")
        self.worker_llm_with_tools = worker_llm.bind_tools(self.tools)
        evaluator_llm = ChatOpenAI(model="gpt-4o-mini")
        self.evaluator_llm_with_output = evaluator_llm.with_structured_output(EvaluatorOutput)
        self._memory_ctx = AsyncSqliteSaver.from_conn_string(DB_PATH)
        self.memory = await self._memory_ctx.__aenter__()
        await self.build_graph()

   
    def worker(self, state: State) -> Dict[str, Any]:
        system_message = f"""You are a helpful assistant that can use tools to complete tasks.
            You keep working on a task until either you have a question or clarification for the user, or the success criteria is met.
            You have many tools to help you, including tools to browse the internet, navigating and retrieving web pages.
            You have a tool to run python code, but note that you would need to include a print() statement if you wanted to receive output.
            The current date and time is {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

            This is the success criteria:
            {state["success_criteria"]}

            IMPORTANT — BEFORE doing anything else, check whether critical information is missing:
            - Flight/travel/hotel tasks: you MUST know the departure location, destination, and travel date(s)
            - Writing/email tasks: you MUST know the audience and purpose
            - Purchase/booking tasks: you MUST know the specific item and budget

            If ANY required detail is missing, your ENTIRE response must be ONLY:
            Question: <one specific question asking for the most important missing piece of information>

            Do NOT attempt the task. Do NOT call any tools. Do NOT guess, assume, or invent locations or dates.
            This check applies on every turn — even retries. If feedback reveals critical info is still missing,
            ask a Question: instead of proceeding.

            If you have all the information you need, proceed with the task.
            When you write or save a file, you MUST also include a full summary of its contents in your reply.
            Never just say "I have created a file" — always show the key information inline so the user can read it.
            """

        if state.get("feedback_on_work"):
            system_message += f"""
                Previously you thought you completed the assignment, but your reply was rejected.
                Here is the feedback on why:
                {state["feedback_on_work"]}
                Review this feedback carefully. If it reveals that critical information (like locations or dates) is still
                missing, respond with a Question: to ask the user. Otherwise, address the feedback and try again."""

        found_system_message = False
        messages = state["messages"]
        for message in messages:
            if isinstance(message, SystemMessage):
                message.content = system_message
                found_system_message = True

        if not found_system_message:
            messages = [SystemMessage(content=system_message)] + messages

        response = self.worker_llm_with_tools.invoke(messages)
        return {"messages": [response]}

    def _is_question_to_user(self, content: str) -> bool:
        """
        Detect if the worker reply is asking the user for input.
        Robust to models that ignore the 'Question:' prefix format instruction.
        """
        if not content:
            return False
        content_stripped = content.strip()
        content_lower = content_stripped.lower()

        if content_stripped.startswith("Question:"):
            return True

        question_starters = (
            "could you", "can you", "what is", "what are", "where are",
            "where is", "when are", "when is", "which ", "would you",
            "do you", "did you", "have you", "please provide", "please share",
            "please clarify", "i need to know", "i need more",
            "to help you", "before i", "in order to",
        )
        if any(content_lower.startswith(s) for s in question_starters):
            return True

        if len(content_stripped) < 300 and content_stripped.endswith("?"):
            return True

        has_list = any(f"{i}." in content_stripped for i in range(1, 6))
        if has_list and "?" in content_stripped:
            return True

        return False

    def worker_router(self, state: State) -> str:
        last_message = state["messages"][-1]
        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            return "tools"
        # Detect questions directly here
        if self._is_question_to_user(last_message.content or ""):
            return "user_input"
        return "evaluator"

    def format_conversation(self, messages: List[Any]) -> str:
        conversation = "Conversation history:\n\n"
        for message in messages:
            if isinstance(message, HumanMessage):
                conversation += f"User: {message.content}\n"
            elif isinstance(message, AIMessage):
                text = message.content or "[Tool use]"
                conversation += f"Assistant: {text}\n"
        return conversation

    def evaluator(self, state: State) -> State:
        last_response = state["messages"][-1].content

        system_message = """You are an evaluator that determines if a task has been completed successfully by an Assistant.
                Assess the Assistant's last response based on the given criteria.

                Use these fields precisely:
                - success_criteria_met: True only if the response fully satisfies the success criteria.
                - user_input_needed: True ONLY if the assistant's reply starts with "Question:" — i.e. the assistant
                explicitly asked the user for something. Do NOT set this True for incomplete work, low quality output,
                or needing more research. For those cases set success_criteria_met=False and user_input_needed=False
                so the worker loops back with your feedback and tries again.
                - pending_question: copy the full question text here when user_input_needed is True. Otherwise null."""

        user_message = f"""You are evaluating a conversation between the User and Assistant.

                The entire conversation:
                {self.format_conversation(state["messages"])}

                The success criteria:
                {state["success_criteria"]}

                The final response from the Assistant you are evaluating:
                {last_response}

                Respond with your feedback, and decide if the success criteria is met by this response.
                Also decide if more user input is required (assistant has a question, needs clarification, or seems stuck).
                IMPORTANT: If the assistant's response starts with "Question:", set user_input_needed=True,
                success_criteria_met=False, and copy the full question into pending_question.
                If the response does NOT start with "Question:", user_input_needed MUST be False regardless of quality.

                The Assistant has access to a tool to write files. You may assume a file was written if the assistant says so.
                However, if the task requires showing information to the user (summaries, results, data), the assistant must include
                that content in the reply itself — not just state that a file was created. Reject responses that say "I created a file"
                without also showing the key contents inline.
                """
        if state.get("feedback_on_work"):
            user_message += f"\nIn a prior attempt you gave this feedback: {state['feedback_on_work']}\n"
            user_message += "If the Assistant is repeating the same mistakes, respond that user input is required."

        evaluator_messages = [
            SystemMessage(content=system_message),
            HumanMessage(content=user_message),
        ]

        eval_result = self.evaluator_llm_with_output.invoke(evaluator_messages)

        new_state = {
            "messages": [
                {
                    "role": "assistant",
                    "content": f"Evaluator Feedback: {eval_result.feedback}",
                }
            ],
            "feedback_on_work": eval_result.feedback,
            "success_criteria_met": eval_result.success_criteria_met,
            "user_input_needed": eval_result.user_input_needed,
            "pending_question": eval_result.pending_question,
        }
        return new_state

    def route_based_on_evaluation(self, state: State) -> str:
        if state["success_criteria_met"] or state["user_input_needed"]:
            return "END"
        else:
            return "worker"

    def handle_user_input_needed(self, state: State) -> Dict[str, Any]:
        """
        Node reached when the worker has asked the user a clarifying question.
        Extracts the question from the worker reply and sets state fields so
        run_superstep can surface it in the Gradio UI.
        """
        last_message = state["messages"][-1]
        content = (last_message.content or "").strip()

        # Strip the "Question:" prefix if present for clean display
        if content.startswith("Question:"):
            question_text = content[len("Question:"):].strip()
        else:
            question_text = content

        return {
            "user_input_needed": True,
            "success_criteria_met": False,
            "pending_question": question_text,
        }


    async def build_graph(self):
        graph_builder = StateGraph(State)

        graph_builder.add_node("worker", self.worker)
        graph_builder.add_node("tools", ToolNode(tools=self.tools))
        graph_builder.add_node("evaluator", self.evaluator)
        graph_builder.add_node("user_input", self.handle_user_input_needed)

        graph_builder.add_conditional_edges(
            "worker", self.worker_router,
            {"tools": "tools", "evaluator": "evaluator", "user_input": "user_input"}
        )
        graph_builder.add_edge("tools", "worker")
        graph_builder.add_edge("user_input", END)
        graph_builder.add_conditional_edges(
            "evaluator", self.route_based_on_evaluation, {"worker": "worker", "END": END}
        )
        graph_builder.add_edge(START, "worker")

        self.graph = graph_builder.compile(checkpointer=self.memory)


    async def run_superstep(self, message: str, success_criteria: str, history: list):
        config = {"configurable": {"thread_id": self.sidekick_id}}

        saved = await self.graph.aget_state(config)
        if saved and saved.values:
            state = {
                "messages": [HumanMessage(content=message)],
                "feedback_on_work": None,
                "success_criteria_met": False,
                "user_input_needed": False,
                "pending_question": None,
            }
        else:
            state = {
                "messages": [HumanMessage(content=message)],
                "success_criteria": success_criteria or "The answer should be clear and accurate",
                "feedback_on_work": None,
                "success_criteria_met": False,
                "user_input_needed": False,
                "pending_question": None,
            }
        result = await self.graph.ainvoke(state, config=config)

        user_entry = {"role": "user", "content": message}

        pending_question = result.get("pending_question")

        if pending_question:
            worker_reply = result["messages"][-1].content or ""
            display_reply = worker_reply
            if display_reply.startswith("Question:"):
                display_reply = display_reply[len("Question:"):].strip()
            reply_entry = {"role": "assistant", "content": display_reply}
            new_history = history + [user_entry, reply_entry]
        else:
            worker_reply = result["messages"][-2].content or ""
            evaluator_feedback = result["messages"][-1].content or ""
            reply_entry = {"role": "assistant", "content": worker_reply}
            feedback_entry = {"role": "assistant", "content": evaluator_feedback}
            new_history = history + [user_entry, reply_entry, feedback_entry]

        return new_history, pending_question

    def cleanup(self):
        try:
            loop = asyncio.get_running_loop()
            if self.browser:
                loop.create_task(self.browser.close())
            if self.playwright:
                loop.create_task(self.playwright.stop())
            if hasattr(self, "_memory_ctx"):
                loop.create_task(self._memory_ctx.__aexit__(None, None, None))
        except RuntimeError:
            if self.browser:
                asyncio.run(self.browser.close())
            if self.playwright:
                asyncio.run(self.playwright.stop())
            if hasattr(self, "_memory_ctx"):
                asyncio.run(self._memory_ctx.__aexit__(None, None, None))