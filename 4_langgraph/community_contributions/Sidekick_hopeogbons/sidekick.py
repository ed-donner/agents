from typing import Annotated
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from dotenv import load_dotenv
from langgraph.prebuilt import ToolNode
from langchain_openai import ChatOpenAI
#from langgraph.checkpoint.memory import MemorySaver
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
    clarifying_questions_asked: int
    planning_complete: bool


class EvaluatorOutput(BaseModel):
    feedback: str = Field(description="Feedback on the assistant's response")
    success_criteria_met: bool = Field(description="Whether the success criteria have been met")
    user_input_needed: bool = Field(
        description="True if more input is needed from the user, or clarifications, or the assistant is stuck"
    )


class PlannerOutput(BaseModel):
    clarification_question: Optional[str] = Field(
        description="A single clarifying question to ask the user, or None if everything is clear"
    )
    ready_to_proceed: bool = Field(
        description="True if the request and success criteria are clear enough to proceed to the worker"
    )
    reasoning: str = Field(
        description="Brief explanation of why clarification is needed or why ready to proceed"
    )


class Sidekick:
    def __init__(self, user_id: str = None):
        self.worker_llm_with_tools = None
        self.evaluator_llm_with_output = None
        self.planner_llm_with_output = None
        self.tools = None
        self.llm_with_tools = None
        self.graph = None
        # Use user_id for thread_id to separate user sessions, fallback to UUID if not provided
        self.sidekick_id = user_id if user_id else str(uuid.uuid4())
        self.memory = None
        self.memory_context = None
        self.browser = None
        self.playwright = None

    async def setup(self):
        # Initialize memory checkpointer with AsyncSqliteSaver
        # Store the async context manager and enter it
        self.memory_context = AsyncSqliteSaver.from_conn_string("memory.db")
        self.memory = await self.memory_context.__aenter__()
        
        self.tools, self.browser, self.playwright = await playwright_tools()
        self.tools += await other_tools()
        worker_llm = ChatOpenAI(model="gpt-4o-mini")
        self.worker_llm_with_tools = worker_llm.bind_tools(self.tools)
        evaluator_llm = ChatOpenAI(model="gpt-4o-mini")
        self.evaluator_llm_with_output = evaluator_llm.with_structured_output(EvaluatorOutput)
        planner_llm = ChatOpenAI(model="gpt-4o-mini")
        self.planner_llm_with_output = planner_llm.with_structured_output(PlannerOutput)
        await self.build_graph()

    def planner(self, state: State) -> Dict[str, Any]:
        # If planning is already complete, skip to worker
        if state.get("planning_complete", False):
            return {"planning_complete": True}
        
        questions_asked = state.get("clarifying_questions_asked", 0)
        max_questions = 3
        
        system_message = f"""You are a planning agent that clarifies user requests before work begins.
Your job is to ensure the user's intention and success criteria are crystal clear.

If anything is ambiguous or unclear about the request or success criteria, ask ONE clarifying question in a conversational, friendly tone.
Once you're satisfied everything is clear, set ready_to_proceed to True.

You have asked {questions_asked} out of a maximum of {max_questions} clarifying questions.
If you've reached the maximum, you must proceed even if things aren't perfectly clear.

Guidelines:
- Ask questions conversationally, not in an itemized list
- Focus on understanding the user's true intent
- Question the success criteria if it's vague or missing
- Don't ask obvious questions
- If the request is already clear, proceed immediately
"""

        user_message = f"""Analyze this request:

User's request: {self.format_conversation(state["messages"])}

Success criteria: {state.get("success_criteria", "Not specified")}

Questions already asked: {questions_asked}/{max_questions}

Decide if you need to ask a clarifying question, or if you're ready to proceed to the worker agent.
"""

        planner_messages = [
            SystemMessage(content=system_message),
            HumanMessage(content=user_message),
        ]

        planner_result = self.planner_llm_with_output.invoke(planner_messages)
        
        # If ready to proceed or max questions reached
        if planner_result.ready_to_proceed or questions_asked >= max_questions:
            return {
                "planning_complete": True,
                "messages": [
                    {
                        "role": "assistant",
                        "content": f"Planner: {planner_result.reasoning}",
                    }
                ],
            }
        
        # Need to ask a clarification question
        return {
            "clarifying_questions_asked": questions_asked + 1,
            "planning_complete": False,
            "user_input_needed": True,
            "messages": [
                {
                    "role": "assistant",
                    "content": planner_result.clarification_question,
                }
            ],
        }

    def planner_router(self, state: State) -> str:
        """Route from planner to either worker (if ready) or END (if need user input)"""
        if state.get("planning_complete", False):
            return "worker"
        else:
            return "END"

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
        # Set up Graph Builder with State
        graph_builder = StateGraph(State)

        # Add nodes
        graph_builder.add_node("planner", self.planner)
        graph_builder.add_node("worker", self.worker)
        graph_builder.add_node("tools", ToolNode(tools=self.tools))
        graph_builder.add_node("evaluator", self.evaluator)

        # Add edges
        # Start with planner
        graph_builder.add_edge(START, "planner")
        
        # Planner routes to worker or END
        graph_builder.add_conditional_edges(
            "planner", self.planner_router, {"worker": "worker", "END": END}
        )
        
        # Worker routes to tools or evaluator
        graph_builder.add_conditional_edges(
            "worker", self.worker_router, {"tools": "tools", "evaluator": "evaluator"}
        )
        
        # Tools go back to worker
        graph_builder.add_edge("tools", "worker")
        
        # Evaluator routes back to worker or END
        graph_builder.add_conditional_edges(
            "evaluator", self.route_based_on_evaluation, {"worker": "worker", "END": END}
        )

        # Compile the graph
        self.graph = graph_builder.compile(checkpointer=self.memory)

    async def run_superstep(self, message, success_criteria, history):
        config = {"configurable": {"thread_id": self.sidekick_id}}

        state = {
            "messages": message,
            "success_criteria": success_criteria or "The answer should be clear and accurate",
            "feedback_on_work": None,
            "success_criteria_met": False,
            "user_input_needed": False,
            "clarifying_questions_asked": 0,
            "planning_complete": False,
        }
        result = await self.graph.ainvoke(state, config=config)
        user = {"role": "user", "content": message}
        reply = {"role": "assistant", "content": result["messages"][-2].content}
        feedback = {"role": "assistant", "content": result["messages"][-1].content}
        return history + [user, reply, feedback]

    async def cleanup_async(self):
        """Async cleanup method"""
        if self.browser:
            await self.browser.close()
            if self.playwright:
                await self.playwright.stop()
        
        if self.memory_context:
            await self.memory_context.__aexit__(None, None, None)
    
    def cleanup(self):
        """Synchronous cleanup wrapper"""
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(self.cleanup_async())
        except RuntimeError:
            # If no loop is running, create one
            asyncio.run(self.cleanup_async())