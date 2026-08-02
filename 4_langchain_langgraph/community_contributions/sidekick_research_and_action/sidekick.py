from typing import Annotated, List, Any, Optional, Dict
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from pydantic import BaseModel, Field
from sidekick_tools import playwright_tools, get_research_tools, get_action_tools
import uuid
import asyncio
from datetime import datetime

load_dotenv(override=True)

class State(TypedDict):
    """Simplified state with essential fields only"""
    messages: Annotated[List[Any], add_messages]
    success_criteria: str
    success_criteria_met: bool
    user_input_needed: bool
    
    # Task coordination
    task_plan: Dict[str, Any]  # Contains research_tasks, action_tasks, strategy
    agent_status: Dict[str, str]  # Track completion: {research: "pending/complete/error"}

class CoordinationPlan(BaseModel):
    """Single definition for coordinator llm's output"""
    research_tasks: List[str] = Field(default_factory=list, description="Information gathering tasks")
    action_tasks: List[str] = Field(default_factory=list, description="Execution/creation tasks") 
    requires_both: bool = Field(default=False, description="Whether both agents are needed")
    strategy: str = Field(description="Overall approach")
    direct_response: Optional[str] = Field(default=None, description="Direct response if no agents needed")

class EvaluatorOutput(BaseModel):
    """Evaluator structured output"""
    response: str = Field(description="Final response to user")
    success_criteria_met: bool = Field(description="Whether criteria were met")
    user_input_needed: bool = Field(description="If more input is needed")

class Sidekick:
    def __init__(self):
        self.research_llm = None
        self.action_llm = None
        self.coordinator_llm = None
        self.evaluator_llm = None
        self.research_tools = None
        self.action_tools = None
        self.graph = None
        self.memory = MemorySaver()
        self.browser = None
        self.playwright = None

    async def setup(self):
        """Initialize tools and LLMs"""
        # Get tools
        self.research_tools = await get_research_tools()
        self.action_tools = await get_action_tools()
        
        # Set up browser tools
        browser_tools, self.browser, self.playwright = await playwright_tools()
        self.action_tools += browser_tools
        
        # Initialize LLMs (single model for consistency)
        base_llm = ChatOpenAI(model="gpt-4o-mini")
        
        self.research_llm = base_llm.bind_tools(self.research_tools)
        self.action_llm = base_llm.bind_tools(self.action_tools)
        self.coordinator_llm = base_llm.with_structured_output(CoordinationPlan)
        self.evaluator_llm = base_llm.with_structured_output(EvaluatorOutput)
        
        await self.build_graph()

    def coordinator_agent(self, state: State) -> Dict[str, Any]:
        """Analyze request and create execution plan or respond directly"""
        user_request = state["messages"][-1].content if state["messages"] else ""
        success_criteria = state["success_criteria"]

        system_message = f"""You are a Coordinator that analyzes user requests and creates execution plans using specialized agents.

First, decide if you can respond directly (greetings, thanks, capability questions, clarifications). Otherwise, delegate to agents based on the task.

RESEARCH AGENT (info gathering): web search, Wikipedia, read files – cannot run code or edit files  
ACTION AGENT (execution): run Python, modify files, send notifications – cannot search web or read Wikipedia

CRITICAL: If the request is vague, ambiguous, or missing key details, ask clarifying questions before assigning tasks.

Analyze this request: "{user_request}"  
Success criteria: "{success_criteria}"

Output a coordination plan with:
1. Research tasks (if any)
2. Action tasks (if any)
3. Whether both agents are needed
4. How they should interact
"""


        result = self.coordinator_llm.invoke([
            SystemMessage(content=system_message),
            HumanMessage(content=f"Request: {user_request}\nSuccess criteria: {success_criteria}")
        ])
        
        # Initialize agent status
        agent_status = {}
        task_plan = {
            "research_tasks": result.research_tasks,
            "action_tasks": result.action_tasks,
            "strategy": result.strategy,
            "requires_both": result.requires_both
        }
        
        # Set initial agent status based on tasks
        if result.research_tasks:
            agent_status["research"] = "pending"
        if result.action_tasks:
            agent_status["action"] = "pending"
        
        # Direct response path
        if result.direct_response and not (result.research_tasks or result.action_tasks):
            return {
                "task_plan": task_plan,
                "agent_status": agent_status,
                "messages": [AIMessage(content=result.direct_response)]
            }
        
        # Delegation path
        return {
            "task_plan": task_plan,
            "agent_status": agent_status,
            "messages": [AIMessage(content=f"Plan: {result.strategy}")]
        }

    def research_agent(self, state: State) -> Dict[str, Any]:
        """Gather information using search and read tools"""
        try:
            task_plan = state.get("task_plan", {})
            research_tasks = task_plan.get("research_tasks", [])
            success_criteria = state.get("success_criteria")
            
            if not research_tasks:
                agent_status = state.get("agent_status", {})
                agent_status["research"] = "skipped"
                return {
                    "agent_status": agent_status,
                    "messages": [AIMessage(content="No research needed")]
                }
            
            system_message = f"""You are a Research Agent specialized in information gathering ONLY.

YOUR ROLE: Gather information and pass it to the Action Agent. You CANNOT create files or execute code.

TASKS TO COMPLETE:
{chr(10).join(f"- {task}" for task in research_tasks)}

SUCCESS CRITERIA: {success_criteria}

AVAILABLE TOOLS:
- search: For current information and trends
- wikipedia_api_wrapper: For background knowledge
- read_file: To READ existing files (you cannot create files)
- list_directory: To see what files exist

CRITICAL RULES:
1. You ONLY gather information - you CANNOT create, write, or modify files
2. After gathering all requested information, STOP and summarize your findings
3. Do NOT attempt to create reports or files - the Action Agent will handle that
4. When your research is complete, provide a clear summary without making more tool calls

Current time: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

IMPORTANT: Once you've gathered the information for all tasks, summarize it and STOP. 
The Action Agent will use your findings to create any required files or reports.
"""

            messages = [SystemMessage(content=system_message)] + state["messages"]
            response = self.research_llm.invoke(messages)
            
            result = {"messages": [response]}
            
            # Check if complete (no tool calls)
            if not (hasattr(response, "tool_calls") and response.tool_calls):
                agent_status = state.get("agent_status", {})
                agent_status["research"] = "complete"
                result["agent_status"] = agent_status
            
            return result
            
        except Exception as e:
            agent_status = state.get("agent_status", {})
            agent_status["research"] = "error"
            return {
                "agent_status": agent_status,
                "messages": [AIMessage(content=f"Research error: {str(e)}")],
                "user_input_needed": True
            }

    def action_agent(self, state: State) -> Dict[str, Any]:
        """Execute tasks using code, files, and browser tools"""
        try:
            task_plan = state.get("task_plan", {})
            action_tasks = task_plan.get("action_tasks", [])
            success_criteria = state.get("success_criteria")
            
            if not action_tasks:
                agent_status = state.get("agent_status", {})
                agent_status["action"] = "skipped"
                return {
                    "agent_status": agent_status,
                    "messages": [AIMessage(content="No actions needed")]
                }
            
            # Get research results if available
            research_content = ""
            if state.get("agent_status", {}).get("research") == "complete":
                # Find research agent's findings
                for msg in reversed(state["messages"]):
                    if isinstance(msg, AIMessage) and any(word in msg.content.lower() for word in ["research", "findings", "gathered", "information"]):
                        research_content = msg.content
                        break
            
            system_message = f"""You are an Action Agent specialized in executing tasks and creating deliverables.

YOUR TASKS:
{chr(10).join(f"- {task}" for task in action_tasks)}

SUCCESS CRITERIA: {success_criteria}

RESEARCH FINDINGS FROM RESEARCH AGENT:
{research_content if research_content else "No prior research available"}

AVAILABLE TOOLS:
- python_repl: Execute code and calculations
- write_file: Create new files with content
- copy_file: Copy existing files
- move_file: Move/rename files
- markdown_to_pdf: Convert markdown to PDF
- send_push_notification: Notify user
- Browser tools for web automation

YOUR MISSION:
1. Use the research findings above to complete your tasks
2. Create any required files or reports
3. Test your outputs for quality
4. Summarize what you created when done

IMPORTANT: The Research Agent has already gathered the information. Your job is to USE that information to create the deliverables.
"""


            messages = [SystemMessage(content=system_message)] + state["messages"]
            response = self.action_llm.invoke(messages)
            
            result = {"messages": [response]}
            
            # Check if complete (no tool calls)
            if not (hasattr(response, "tool_calls") and response.tool_calls):
                agent_status = state.get("agent_status", {})
                agent_status["action"] = "complete"
                result["agent_status"] = agent_status
            
            return result
            
        except Exception as e:
            agent_status = state.get("agent_status", {})
            agent_status["action"] = "error"
            return {
                "agent_status": agent_status,
                "messages": [AIMessage(content=f"Action error: {str(e)}")],
                "user_input_needed": True
            }

    def evaluator(self, state: State) -> Dict[str, Any]:
        """Create final response and evaluate success"""
        task_plan = state.get("task_plan", {})
        agent_status = state.get("agent_status", {})
        success_criteria = state["success_criteria"]
        
        # Gather agent results
        agent_results = []
        for msg in state["messages"][-5:]:  # Check recent messages
            if isinstance(msg, AIMessage):
                agent_results.append(msg.content)
        
        system_message = f"""You are an Evaluator/Synthesizer Agent that creates the final response.

ORIGINAL REQUEST: {state['messages'][0].content if state['messages'] else ''}
COORDINATION PLAN: {task_plan.get('strategy', 'Direct response')}
SUCCESS CRITERIA: {success_criteria}

AGENT STATUS: {agent_status}
RESULTS:
{chr(10).join(agent_results)}

GUIDELINES:
1. Address the original request clearly
2. Integrate research and action results
3. Evaluate if success criteria were met
4. Highlight key info, deliverables, and follow-ups
5. Note any missing info or need for user input

Provide a clear, professional response.
"""


        result = self.evaluator_llm.invoke([
            SystemMessage(content=system_message),
            HumanMessage(content="Create final response")
        ])
        
        return {
            "messages": [AIMessage(content=result.response)],
            "success_criteria_met": result.success_criteria_met,
            "user_input_needed": result.user_input_needed
        }

    # Simplified routing functions
    def coordinator_router(self, state: State) -> str:
        """Route from coordinator based on task plan"""
        task_plan = state.get("task_plan", {})
        
        if task_plan.get("research_tasks"):
            return "research_agent"
        elif task_plan.get("action_tasks"):
            return "action_agent"
        else:
            return "evaluator"

    def research_router(self, state: State) -> str:
        """Route from research agent"""
        last_message = state["messages"][-1]
        
        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            return "research_tools"
        
        # Research complete - check if action needed
        task_plan = state.get("task_plan", {})
        agent_status = state.get("agent_status", {})
        
        if task_plan.get("action_tasks") and agent_status.get("action") == "pending":
            return "action_agent"
        else:
            return "evaluator"

    def action_router(self, state: State) -> str:
        """Route from action agent"""
        last_message = state["messages"][-1]
        
        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            return "action_tools"
        else:
            return "evaluator"

    def evaluator_router(self, state: State) -> str:
        """Route from evaluator"""
        if state.get("success_criteria_met") or state.get("user_input_needed"):
            return "END"
        else:
            return "coordinator"  # Retry if needed

    async def build_graph(self):
        """Construct the agent graph"""
        graph = StateGraph(State)
        
        # Add nodes
        graph.add_node("coordinator", self.coordinator_agent)
        graph.add_node("research_agent", self.research_agent)
        graph.add_node("action_agent", self.action_agent)
        graph.add_node("evaluator", self.evaluator)
        graph.add_node("research_tools", ToolNode(self.research_tools))
        graph.add_node("action_tools", ToolNode(self.action_tools))
        
        # Add edges
        graph.add_edge(START, "coordinator")
        graph.add_edge("research_tools", "research_agent")
        graph.add_edge("action_tools", "action_agent")
        
        # Add conditional edges
        graph.add_conditional_edges("coordinator", self.coordinator_router)
        graph.add_conditional_edges("research_agent", self.research_router)
        graph.add_conditional_edges("action_agent", self.action_router)
        graph.add_conditional_edges("evaluator", self.evaluator_router)
        
        self.graph = graph.compile(checkpointer=self.memory)

    async def run_superstep(self, message, success_criteria, history, thread_id=None):
        """Execute one conversation turn"""
        if thread_id is None:
            thread_id = str(uuid.uuid4())
        
        config = {"configurable": {"thread_id": thread_id}}
        
        # Convert history to messages
        messages = []
        for msg in history:
            if msg["role"] == "user":
                messages.append(HumanMessage(content=msg["content"]))
            else:
                messages.append(AIMessage(content=msg["content"]))
        
        # Initialize state
        state = {
            "messages": messages + [HumanMessage(content=message)],
            "success_criteria": success_criteria or "Provide a helpful response",
            "success_criteria_met": False,
            "user_input_needed": False,
            "task_plan": {},
            "agent_status": {}
        }
        
        # Run the graph
        result = await self.graph.ainvoke(state, config=config)
        
        # Prepare response
        user = {"role": "user", "content": message}
        reply = {"role": "assistant", "content": result["messages"][-1].content}
        
        return history + [user, reply], thread_id

    async def cleanup(self):
        """Clean up browser resources"""
        if self.browser:
            try:
                await self.browser.close()
                if self.playwright:
                    await self.playwright.stop()
            except Exception as e:
                print(f"Cleanup error: {e}")