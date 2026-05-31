
from typing import Annotated, List, Any, Optional, Dict
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from dotenv import load_dotenv
from langgraph.prebuilt import ToolNode
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from pydantic import BaseModel, Field
from sidekick_tools import playwright_tools, other_tools
from guardrails import GuardrailsManager
import uuid
import asyncio
from datetime import datetime
import os

load_dotenv(override=True)

class State(TypedDict):
    """
    The state that flows through the graph.
    
    Attributes:
        messages: Conversation history
        success_criteria: What defines successful completion
        feedback_on_work: Evaluator's feedback on worker's output
        success_criteria_met: Whether task is complete
        user_input_needed: Whether we need to ask user for clarification
        clarification_question: The question to ask user
        guardrails_issues: Any safety/content issues detected
    """
    messages: Annotated[List[Any], add_messages]
    success_criteria: str
    feedback_on_work: Optional[str]
    success_criteria_met: bool
    user_input_needed: bool
    clarification_question: Optional[str]
    guardrails_issues: List[str]


class EvaluatorOutput(BaseModel):
    """Output from the evaluator that checks task completion"""
    feedback: str = Field(description="Feedback on the assistant's response")
    success_criteria_met: bool = Field(description="Whether the success criteria have been met")
    user_input_needed: bool = Field(
        description="True if more input is needed from the user, or clarifications, or the assistant is stuck"
    )


class ClarificationOutput(BaseModel):
    """Output when assistant needs user clarification"""
    needs_clarification: bool = Field(description="Whether clarification is needed")
    question: Optional[str] = Field(description="The clarification question to ask user")
    missing_info: List[str] = Field(description="List of missing information needed")


class Sidekick:
    """
    Main AI assistant class with enhanced capabilities.
    
    Features:
    - Tool usage (web browsing, search, code execution, etc.)
    - Automatic clarification questions when info is missing
    - Guardrails for safety and content moderation
    - Self-evaluation to ensure quality responses
    """
    
    def __init__(self):
        """Initialize the Sidekick assistant"""
        self.worker_llm_with_tools = None
        self.evaluator_llm_with_output = None
        self.clarification_llm = None
        self.tools = None
        self.graph = None
        self.sidekick_id = str(uuid.uuid4())
        self.memory = MemorySaver()
        self.browser = None
        self.playwright = None
        self.guardrails = GuardrailsManager(max_tokens=8000)

    async def setup(self):
        """
        Initialize all components of the assistant.
        
        Sets up:
        - Browser tools (Playwright)
        - Search, research, and utility tools
        - LLM instances with appropriate configurations
        - The workflow graph
        """
        # Initialize tools
        self.tools, self.browser, self.playwright = await playwright_tools()
        self.tools += await other_tools()
        
        # Worker LLM - does the actual work with tools
        worker_llm = ChatOpenAI(
            model="nvidia/nemotron-3-nano-30b-a3b:free",
            openai_api_key=os.getenv("OPENROUTER_API_KEY"),
            openai_api_base="https://openrouter.ai/api/v1",
        )
        self.worker_llm_with_tools = worker_llm.bind_tools(self.tools)
        
        # Evaluator LLM - checks if work meets success criteria
        evaluator_llm = ChatOpenAI(
            model="nvidia/nemotron-3-nano-30b-a3b:free",
            openai_api_key=os.getenv("OPENROUTER_API_KEY"),
            openai_api_base="https://openrouter.ai/api/v1",
        )
        self.evaluator_llm_with_output = evaluator_llm.with_structured_output(EvaluatorOutput)
        
        # Clarification LLM - asks follow-up questions
        self.clarification_llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.3
        ).with_structured_output(ClarificationOutput)
        
        await self.build_graph()

    
    def worker(self, state: State) -> Dict[str, Any]:
        """
        The worker node that uses tools to complete tasks.
        
        This is the core agent that:
        - Understands the user's request
        - Uses tools to gather information or perform actions
        - Works towards meeting the success criteria
        
        Args:
            state: Current state with messages and success criteria
            
        Returns:
            Updated state with worker's response
        """
        system_message = f"""You are a highly capable AI assistant with access to many tools.
            Your goal is to help the user complete their task successfully.

            CURRENT DATE/TIME: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

            SUCCESS CRITERIA:
            {state["success_criteria"]}

            IMPORTANT GUIDELINES:
            1. If information is missing or unclear, ask a specific clarification question
            2. Use tools proactively to gather information
            3. When using Python REPL, always use print() to see output
            4. For web searches, try multiple tools if one doesn't give good results
            5. Be thorough but concise in your responses

            AVAILABLE TOOLS:
            - Web browsing (Playwright)
            - Search (Google, Tavily)
            - Research (Wikipedia)
            - Code execution (Python REPL)
            - File operations (read/write in sandbox/)
            - Notifications (push alerts)
            - LLM tools (summarization, translation)
            """

                    # Add feedback if previous attempt was rejected
        if state.get("feedback_on_work"):
            ystem_message += f"""
            PREVIOUS ATTEMPT FEEDBACK:
            Your last response did not meet the success criteria. Here's why:
            {state["feedback_on_work"]}

            Please improve your response based on this feedback.
            """

        # Build messages list with system message
        messages = state["messages"]
        found_system_message = False
        
        for message in messages:
            if isinstance(message, SystemMessage):
                message.content = system_message
                found_system_message = True
                break

        if not found_system_message:
            messages = [SystemMessage(content=system_message)] + messages

        # Invoke the worker LLM
        response = self.worker_llm_with_tools.invoke(messages)

        return {"messages": [response]}

    
    def worker_router(self, state: State) -> str:
        """
        Route after worker node based on whether tools need to be called.
        
        Args:
            state: Current state
            
        Returns:
            "tools" if worker wants to use tools, "clarification_check" otherwise
        """
        last_message = state["messages"][-1]

        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            return "tools"
        else:
            return "clarification_check"

    
    async def clarification_check(self, state: State) -> Dict[str, Any]:
        """
        Check if the worker's response contains a clarification question.
        
        This node analyzes the worker's output to see if they're asking
        the user for more information or clarification.
        
        Args:
            state: Current state
            
        Returns:
            Updated state with clarification info
        """
        last_response = state["messages"][-1].content
        
        prompt = f"""Analyze this assistant's response to determine if it's asking for clarification:

            "{last_response}"

            Check if:
            1. The response contains a question for the user
            2. The assistant is asking for missing information
            3. The assistant needs clarification to proceed

            If yes, extract the clarification question."""
                    
        try:
            result = await self.clarification_llm.ainvoke([
                {"role": "system", "content": "You are an analyzer that detects clarification questions."},
                {"role": "user", "content": prompt}
            ])
            
            return {
                "user_input_needed": result.needs_clarification,
                "clarification_question": result.question
            }
        except:
            # If analysis fails, check for question marks as fallback
            has_question = "?" in last_response
            return {
                "user_input_needed": has_question,
                "clarification_question": last_response if has_question else None
            }

    
    async def evaluator(self, state: State) -> Dict[str, Any]:
        """
        Evaluate if the worker's response meets the success criteria.
        
        This node:
        - Reviews the conversation history
        - Checks against success criteria
        - Provides feedback if criteria not met
        - Decides if user input is needed
        
        Args:
            state: Current state
            
        Returns:
            Updated state with evaluation results
        """
        last_response = state["messages"][-1].content

        system_message = """You are an evaluator that determines if a task has been completed successfully.
            Assess the assistant's response based on the given success criteria.
            Be fair but thorough in your evaluation."""

        user_message = f"""CONVERSATION HISTORY:
            {self.format_conversation(state["messages"])}

            SUCCESS CRITERIA:
            {state["success_criteria"]}

            ASSISTANT'S FINAL RESPONSE:
            {last_response}

            EVALUATION INSTRUCTIONS:
            1. Check if the success criteria is fully met
            2. If the assistant says they completed an action (e.g., "I wrote the file"), trust them
            3. Provide constructive feedback if criteria not met
            4. Determine if more user input is needed

            Previous feedback (if any): {state.get('feedback_on_work', 'None')}
            """

        evaluator_messages = [
            SystemMessage(content=system_message),
            HumanMessage(content=user_message),
        ]

        eval_result = await self.evaluator_llm_with_output.ainvoke(evaluator_messages)
        
        return {
            "messages": [
                AIMessage(content=f"📊 Evaluation: {eval_result.feedback}")
            ],
            "feedback_on_work": eval_result.feedback,
            "success_criteria_met": eval_result.success_criteria_met,
            "user_input_needed": eval_result.user_input_needed,
        }

    
    def route_after_clarification_check(self, state: State) -> str:
        """Route based on whether clarification is needed"""
        if state.get("user_input_needed"):
            return "END"  # Need user input, stop and show question
        else:
            return "evaluator"  # No clarification needed, proceed to evaluation

    def route_based_on_evaluation(self, state: State) -> str:
        """Route based on evaluator's decision"""
        if state["success_criteria_met"] or state["user_input_needed"]:
            return "END"  # Task complete or needs user input
        else:
            return "worker"  # Criteria not met, try again


    def format_conversation(self, messages: List[Any]) -> str:
        """Format conversation history for display"""
        conversation = ""
        for message in messages:
            if isinstance(message, HumanMessage):
                conversation += f"👤 User: {message.content}\n\n"
            elif isinstance(message, AIMessage):
                text = message.content or "[Using tools...]"
                conversation += f"🤖 Assistant: {text}\n\n"
        return conversation

    
    async def build_graph(self):
        """
        Build the workflow graph that defines how the assistant operates.
        
        Graph flow:
        START → worker → [tools OR clarification_check]
        tools → worker
        clarification_check → [evaluator OR END]
        evaluator → [worker OR END]
        """
        graph_builder = StateGraph(State)

        # Add nodes
        graph_builder.add_node("worker", self.worker)
        graph_builder.add_node("tools", ToolNode(tools=self.tools))
        graph_builder.add_node("clarification_check", self.clarification_check)
        graph_builder.add_node("evaluator", self.evaluator)

        # Add edges
        graph_builder.add_conditional_edges(
            "worker", 
            self.worker_router, 
            {"tools": "tools", "clarification_check": "clarification_check"}
        )
        
        graph_builder.add_edge("tools", "worker")
        
        graph_builder.add_conditional_edges(
            "clarification_check",
            self.route_after_clarification_check,
            {"evaluator": "evaluator", "END": END}
        )
        
        graph_builder.add_conditional_edges(
            "evaluator", 
            self.route_based_on_evaluation, 
            {"worker": "worker", "END": END}
        )
        
        graph_builder.add_edge(START, "worker")

        # Compile with memory
        self.graph = graph_builder.compile(checkpointer=self.memory)

    
    async def run_superstep(self, message: str, success_criteria: str, history: List) -> List:
        """
        Execute one complete interaction with the assistant.
        
        This includes:
        1. Validating input with guardrails
        2. Running the graph workflow
        3. Formatting results for UI
        
        Args:
            message: User's message
            success_criteria: What defines success for this task
            history: Previous conversation history
            
        Returns:
            Updated conversation history
        """
        # Apply guardrails to user input
        validation = await self.guardrails.validate_input(message)
        
        if not validation["is_valid"]:
            # Input failed guardrails
            error_msg = "⚠️ Input validation failed:\n" + "\n".join(validation["issues"])
            return history + [
                {"role": "user", "content": message},
                {"role": "assistant", "content": error_msg}
            ]
        
        # Show warnings if any (but still proceed)
        warnings = [issue for issue in validation["issues"] if "⚠️" in issue]
        
        config = {"configurable": {"thread_id": self.sidekick_id}}

        state = {
            "messages": message,
            "success_criteria": success_criteria or "Provide a clear, accurate, and helpful response",
            "feedback_on_work": None,
            "success_criteria_met": False,
            "user_input_needed": False,
            "clarification_question": None,
            "guardrails_issues": warnings
        }
        
        # Run the graph
        result = await self.graph.ainvoke(state, config=config)
        
        # Format results for UI
        user_msg = {"role": "user", "content": message}
        
        # Add warnings if any
        if warnings:
            warning_msg = {"role": "assistant", "content": "\n".join(warnings)}
            history = history + [user_msg, warning_msg]
        else:
            history = history + [user_msg]
        
        # Add assistant's response
        assistant_response = result["messages"][-2].content
        reply = {"role": "assistant", "content": assistant_response}
        
        # Add evaluator feedback
        eval_feedback = result["messages"][-1].content
        feedback = {"role": "assistant", "content": eval_feedback}
        
        return history + [reply, feedback]

    
    def cleanup(self):
        """Clean up browser resources"""
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
