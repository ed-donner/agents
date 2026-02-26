from typing import Annotated, Any, Dict, List, Optional
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.memory import MemorySaver
from langchain_openai import AzureChatOpenAI
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_core.runnables import RunnableConfig
from pydantic import BaseModel, Field
from sidekick_tools import playwright_tools, other_tools
import uuid
import asyncio
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv(override=True)


class State(TypedDict):
    """Agent state schema"""

    messages: Annotated[List[Any], add_messages]
    success_criteria: str
    feedback_on_work: Optional[str]
    success_criteria_met: bool
    user_input_needed: bool


class EvaluatorOutput(BaseModel):
    """Structured output from the evaluator"""

    feedback: str = Field(description="Detailed feedback on the assistant's response")
    success_criteria_met: bool = Field(
        description="Whether the success criteria have been met"
    )
    user_input_needed: bool = Field(
        description="True if more user input is needed, clarifications required, or assistant is stuck"
    )


class Sidekick:
    """
    Agentic assistant that uses LangGraph to handle complex tasks.
    Supports tool use, evaluation loops, and human feedback.
    """

    def __init__(self):
        self.worker_llm_with_tools = None
        self.evaluator_llm_with_output = None
        self.tools = None
        self.llm_with_tools = None
        self.graph = None
        self.sidekick_id = str(uuid.uuid4())
        self.memory = MemorySaver()
        self.browser = None
        self.playwright = None

    async def setup(self) -> None:
        """Initialize all tools, LLMs, and build the graph"""
        # Initialize browser tools
        self.tools, self.browser, self.playwright = await playwright_tools()
        # Add other tools
        self.tools += await other_tools()

        # Setup worker LLM with tools
        worker_llm = AzureChatOpenAI(
            azure_deployment=os.getenv("AZURE_OPENAI_DEPLOYMENT"),
        )
        self.worker_llm_with_tools = worker_llm.bind_tools(self.tools)

        # Setup evaluator LLM with structured output
        evaluator_llm = AzureChatOpenAI(
            azure_deployment=os.getenv("AZURE_OPENAI_DEPLOYMENT"),
        )
        self.evaluator_llm_with_output = evaluator_llm.with_structured_output(
            EvaluatorOutput
        )

        # Build the graph
        await self.build_graph()

    async def worker(self, state: State, config: RunnableConfig) -> Dict[str, Any]:
        """
        Worker node: uses LLM to think through the task and decide on tool use.
        """
        system_message = f"""You are a helpful assistant that can use tools to complete tasks.
You keep working on a task until either you have a question or clarification for the user, or the success criteria is met.
You have many tools to help you, including tools to:
- Browse the internet and retrieve web pages
- Run Python code (include print() to see output)
- Read and write files
- Search Wikipedia for information
- Send push notifications

The current date and time is {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

Success Criteria:
{state["success_criteria"]}

You should reply either with:
1. A question for the user (if you need clarification)
2. Your final response (if the task is complete)

Format questions clearly:
Question: [Your question here]

If complete, just provide the final answer without asking questions.
"""

        # Add feedback if this is a retry attempt
        if state.get("feedback_on_work"):
            system_message += f"""
Previous Attempt Feedback:
Your previous response was rejected. Here's why:
{state["feedback_on_work"]}

Please try again with this feedback in mind. Ensure the success criteria is met.
"""

        # Update or add system message
        messages = state["messages"]
        found_system_message = False

        for message in messages:
            if isinstance(message, SystemMessage):
                message.content = system_message
                found_system_message = True
                break

        if not found_system_message:
            messages = [SystemMessage(content=system_message)] + messages

        # Invoke the LLM with config for proper async context propagation
        response = await self.worker_llm_with_tools.ainvoke(messages, config)

        return {"messages": [response]}

    def worker_router(self, state: State) -> str:
        """Route to tools if tool calls exist, else go to evaluator"""
        last_message = state["messages"][-1]

        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            return "tools"
        else:
            return "evaluator"

    def format_conversation(self, messages: List[Any]) -> str:
        """Format conversation history for readability"""
        conversation = "Conversation History:\n\n"
        for message in messages:
            if isinstance(message, HumanMessage):
                conversation += f"User: {message.content}\n"
            elif isinstance(message, AIMessage):
                text = message.content or "[Used tools]"
                conversation += f"Assistant: {text}\n"
            elif isinstance(message, SystemMessage):
                continue  # Skip system messages in conversation

        return conversation

    async def evaluator(self, state: State, config: RunnableConfig) -> Dict[str, Any]:
        """
        Evaluator node: determines if success criteria met and if more input needed.
        """
        last_response = state["messages"][-1].content

        system_message = """You are an evaluator that assesses task completion by an Assistant.
Determine if the task meets the success criteria based on the assistant's final response.
Also assess whether the user needs to provide more input, clarification, or if the assistant is stuck."""

        user_message = f"""Evaluate this conversation:

{self.format_conversation(state["messages"])}

Task Success Criteria:
{state["success_criteria"]}

Assistant's Final Response:
{last_response}

Decide:
1. Is the success criteria met?
2. Does the user need to provide more input (clarification, stuck, etc.)?
3. Provide constructive feedback.

Note: If the assistant says they wrote a file, assume they did. Give the benefit of the doubt but reject if more work is needed."""

        if state["feedback_on_work"]:
            user_message += f"""

Previous Feedback Given:
{state["feedback_on_work"]}

If the assistant is repeating the same mistakes, mark that user input is required."""

        evaluator_messages = [
            SystemMessage(content=system_message),
            HumanMessage(content=user_message),
        ]

        eval_result = await self.evaluator_llm_with_output.ainvoke(evaluator_messages, config)

        return {
            "feedback_on_work": eval_result.feedback,
            "success_criteria_met": eval_result.success_criteria_met,
            "user_input_needed": eval_result.user_input_needed,
        }

    def route_based_on_evaluation(self, state: State) -> str:
        """Route based on evaluation: continue work or end"""
        if state["success_criteria_met"] or state["user_input_needed"]:
            return "END"
        else:
            return "worker"

    async def build_graph(self) -> None:
        """Build the LangGraph state machine"""
        graph_builder = StateGraph(State)

        # Add nodes
        graph_builder.add_node("worker", self.worker)
        graph_builder.add_node("tools", ToolNode(tools=self.tools))
        graph_builder.add_node("evaluator", self.evaluator)

        # Add edges
        graph_builder.add_conditional_edges(
            "worker", self.worker_router, {"tools": "tools", "evaluator": "evaluator"}
        )
        graph_builder.add_edge("tools", "worker")
        graph_builder.add_conditional_edges(
            "evaluator",
            self.route_based_on_evaluation,
            {"worker": "worker", "END": END},
        )
        graph_builder.add_edge(START, "worker")

        # Compile the graph
        self.graph = graph_builder.compile(checkpointer=self.memory)

    async def run_superstep(
        self, message: str, success_criteria: str, history: List[Dict[str, str]]
    ) -> List[Dict[str, str]]:
        """
        Execute one step of the agent and return updated history.
        """
        config = {"configurable": {"thread_id": self.sidekick_id}}

        # Build initial state
        state = {
            "messages": [HumanMessage(content=message)],
            "success_criteria": success_criteria
            or "The answer should be clear and accurate",
            "feedback_on_work": None,
            "success_criteria_met": False,
            "user_input_needed": False,
        }

        # Run the graph with proper async invocation
        result = await self.graph.ainvoke(state, config=config)

        # Extract responses
        worker_response = (
            result["messages"][-2].content if len(result["messages"]) > 1 else ""
        )
        evaluator_feedback = result["feedback_on_work"] or "No feedback"

        # Build chat history using Gradio 6.0 message format
        updated_history = history or []
        updated_history.append({"role": "user", "content": message})
        updated_history.append({"role": "assistant", "content": worker_response})
        updated_history.append(
            {"role": "assistant", "content": f"\u2705 **Evaluation:** {evaluator_feedback}"}
        )

        return updated_history

    async def cleanup(self) -> None:
        """Clean up resources (browser, playwright)"""
        print("Cleaning up Sidekick resources...")
        try:
            if self.browser:
                await self.browser.close()
            if self.playwright:
                await self.playwright.stop()
        except Exception as e:
            print(f"Exception during cleanup: {e}")