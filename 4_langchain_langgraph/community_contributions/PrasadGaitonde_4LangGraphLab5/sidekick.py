"""
Sidekick - Intelligent Data Analysis Agent
Multi-agent architecture with Plan-Do-Check loop for reliable SQL query generation.
"""
from typing import Annotated, List, Any, Optional, Dict
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from dotenv import load_dotenv
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from pydantic import BaseModel, Field
import uuid
import asyncio

# Import configuration
from config import (
    DATABASE_PATH, MEMORY_DB_PATH, MAX_QUERY_REWRITE_ATTEMPTS,
    CLARIFYING_QUESTION_COUNT
)

# Import SQL memory
from sql_memory import SQLMemory

# Import nodes
from nodes.clarifier import clarifier_node
from nodes.planner import planner_node
from nodes.query_writer import query_writer_node
from nodes.query_executor import query_executor_node
from nodes.query_checker import query_checker_node
from nodes.output_formatter import output_formatter_node

load_dotenv(override=True)


class State(TypedDict):
    """State schema for the Intelligent Data Analysis Agent."""
    messages: Annotated[List[Any], add_messages]

    # User input
    user_request: Optional[str]
    success_criteria: Optional[str]

    # Clarification phase
    clarifying_questions: Optional[List[str]]
    questions_text: Optional[str]
    user_clarifications: Optional[str]
    awaiting_user_clarification: bool

    # Planning phase
    analysis_plan: Optional[List[str]]
    target_tables: Optional[List[str]]
    required_columns: Optional[Dict[str, List[str]]]
    join_strategy: Optional[str]
    potential_challenges: Optional[List[str]]
    plan_text: Optional[str]

    # Query generation phase
    generated_query: Optional[str]
    query_explanation: Optional[str]
    tables_used: Optional[List[str]]
    query_confidence: Optional[float]

    # Execution phase
    query_results: Optional[List[Dict]]
    execution_error: Optional[str]
    execution_success: Optional[bool]
    results_text: Optional[str]

    # Validation phase
    query_is_valid: Optional[bool]
    needs_rewrite: Optional[bool]
    checker_issues: Optional[List[str]]
    rewrite_feedback: Optional[str]
    checker_confidence: Optional[float]
    user_input_needed: Optional[bool]

    # Loop control
    rewrite_attempt: int
    max_rewrite_attempts: int

    # Memory and session
    session_id: str
    memory: Optional[SQLMemory]

    # Final output
    formatted_output: Optional[str]


class Sidekick:
    """
    Intelligent Data Analysis Agent with multi-agent Plan-Do-Check architecture.

    Architecture:
    1. Clarifier: Asks 3 clarifying questions before analysis
    2. Planner: Creates step-by-step analysis plan
    3. Query Writer: Generates SQL based on plan
    4. Query Executor: Executes SQL safely
    5. Query Checker: Validates results (loops back if needed)
    6. Output Formatter: Presents final results
    """

    def __init__(self):
        self.graph = None
        self.sidekick_id = str(uuid.uuid4())
        self.memory = None
        self.browser = None
        self.playwright = None

    async def setup(self):
        """Initialize the agent, memory, and build the graph."""
        # Initialize SQL memory
        self.memory = SQLMemory(db_path=MEMORY_DB_PATH)

        # Build the graph
        await self.build_graph()

    def clarifier(self, state: State) -> Dict[str, Any]:
        """Clarifier node: Generate 3 clarifying questions."""
        result = clarifier_node(state)

        # Store in memory
        if state.get("memory") and result.get("clarifying_questions"):
            # Will be fully saved after planner runs
            pass

        return result

    def planner(self, state: State) -> Dict[str, Any]:
        """Planner node: Create analysis plan."""
        return planner_node(state)

    def query_writer(self, state: State) -> Dict[str, Any]:
        """Query Writer node: Generate SQL query."""
        return query_writer_node(state)

    def query_executor(self, state: State) -> Dict[str, Any]:
        """Query Executor node: Execute SQL query."""
        return query_executor_node(state)

    def query_checker(self, state: State) -> Dict[str, Any]:
        """Query Checker node: Validate results."""
        return query_checker_node(state)

    def output_formatter(self, state: State) -> Dict[str, Any]:
        """Output Formatter node: Format final results."""
        return output_formatter_node(state)

    # Routing functions
    def clarifier_router(self, state: State) -> str:
        """Route after clarifier: wait for user input."""
        return "awaiting_input"

    def planner_router(self, state: State) -> str:
        """Route after planner: proceed to query writing."""
        return "write_query"

    def checker_router(self, state: State) -> str:
        """Route after checker: rewrite, finish, or get user input."""
        if state.get("user_input_needed"):
            return "awaiting_input"
        elif state.get("needs_rewrite") and state.get("rewrite_attempt", 0) < state.get("max_rewrite_attempts", 3):
            return "rewrite_query"
        else:
            return "format_output"

    def rewrite_router(self, state: State) -> str:
        """Route for rewrite: increment counter and go back to writer."""
        return "write_query"

    async def build_graph(self):
        """Build the LangGraph workflow."""
        graph_builder = StateGraph(State)

        # Add nodes
        graph_builder.add_node("clarifier", self.clarifier)
        graph_builder.add_node("planner", self.planner)
        graph_builder.add_node("write_query", self.query_writer)
        graph_builder.add_node("execute_query", self.query_executor)
        graph_builder.add_node("check_query", self.query_checker)
        graph_builder.add_node("format_output", self.output_formatter)

        # Add edges
        # Start -> Clarifier
        graph_builder.add_edge(START, "clarifier")

        # Clarifier -> awaiting input (user provides clarifications)
        graph_builder.add_conditional_edges(
            "clarifier",
            self.clarifier_router,
            {"awaiting_input": "planner"}  # After user input, go to planner
        )

        # Planner -> Query Writer
        graph_builder.add_edge("planner", "write_query")

        # Query Writer -> Executor
        graph_builder.add_edge("write_query", "execute_query")

        # Executor -> Checker
        graph_builder.add_edge("execute_query", "check_query")

        # Checker -> (rewrite | format | awaiting_input)
        graph_builder.add_conditional_edges(
            "check_query",
            self.checker_router,
            {
                "rewrite_query": "write_query",
                "format_output": "format_output",
                "awaiting_input": END
            }
        )

        # Format output -> END
        graph_builder.add_edge("format_output", END)

        # Compile with memory
        self.graph = graph_builder.compile()

    async def run_superstep(
        self,
        message: str,
        success_criteria: Optional[str] = None,
        history: Optional[List[Dict]] = None,
        user_clarifications: Optional[str] = None
    ) -> tuple:
        """
        Run the analysis workflow.

        Args:
            message: User's data analysis request
            success_criteria: Optional success criteria
            history: Conversation history
            user_clarifications: Optional clarifications (if already provided)

        Returns:
            Updated history with new messages
        """
        history = history or []
        session_id = str(uuid.uuid4())

        # Create session in memory
        if self.memory:
            self.memory.create_session(session_id)
            self.memory.save_message(session_id, "user", message, "request")

        # Initial state
        state = {
            "messages": [HumanMessage(content=message)],
            "user_request": message,
            "success_criteria": success_criteria or "Return accurate query results",

            # Clarification
            "clarifying_questions": None,
            "questions_text": None,
            "user_clarifications": user_clarifications,
            "awaiting_user_clarification": user_clarifications is None,

            # Planning
            "analysis_plan": None,
            "target_tables": None,
            "required_columns": None,
            "join_strategy": None,
            "potential_challenges": None,
            "plan_text": None,

            # Query
            "generated_query": None,
            "query_explanation": None,
            "tables_used": None,
            "query_confidence": None,

            # Execution
            "query_results": None,
            "execution_error": None,
            "execution_success": None,
            "results_text": None,

            # Validation
            "query_is_valid": None,
            "needs_rewrite": None,
            "checker_issues": None,
            "rewrite_feedback": None,
            "checker_confidence": None,
            "user_input_needed": False,

            # Loop control
            "rewrite_attempt": 0,
            "max_rewrite_attempts": MAX_QUERY_REWRITE_ATTEMPTS,

            # Memory
            "session_id": session_id,
            "memory": self.memory,

            # Output
            "formatted_output": None,
        }

        # Run the graph
        result = await self.graph.ainvoke(state)

        # Build response messages
        user_msg = {"role": "user", "content": message}

        # Get the formatted output
        formatted_output = result.get("formatted_output", "Analysis completed.")
        assistant_msg = {"role": "assistant", "content": formatted_output}

        # Save to memory
        if self.memory:
            self.memory.save_message(session_id, "assistant", formatted_output, "response")
            self.memory.update_session_status(session_id, "completed")

        return history + [user_msg, assistant_msg], result

    def needs_clarification(self, result: Dict) -> bool:
        """Check if the result indicates we need user clarifications."""
        return result.get("awaiting_user_clarification", False)

    def get_clarifying_questions(self, result: Dict) -> List[str]:
        """Get the clarifying questions from result."""
        return result.get("clarifying_questions", [])

    def cleanup(self):
        """Clean up resources."""
        if self.memory:
            self.memory.close()
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
