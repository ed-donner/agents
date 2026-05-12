import os
import uuid
from datetime import datetime
from typing import Annotated, Any, Dict, List, Optional
from typing_extensions import TypedDict

from dotenv import load_dotenv
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from pydantic import BaseModel, Field

from sidekick_tools import (
    create_run,
    init_db,
    log_client_note,
    make_tools,
    push,
    save_client_brief,
    save_clarification,
    search_client_memory,
    update_run,
)

load_dotenv(override=True)


def make_llm():
    openrouter_key = os.getenv("OPENROUTER_API_KEY")
    if openrouter_key:
        return ChatOpenAI(
            model=os.getenv("OPENROUTER_MODEL", "openai/gpt-4o-mini"),
            base_url="https://openrouter.ai/api/v1",
            api_key=openrouter_key,
        )
    return ChatOpenAI(model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"))


class State(TypedDict):
    messages: Annotated[List[Any], add_messages]
    success_criteria: str
    feedback_on_work: Optional[str]
    success_criteria_met: bool
    user_input_needed: bool
    company_name: str
    goal: str
    research_plan: List[str]
    clarification_question: Optional[str]
    briefing_context: Optional[str]
    final_brief: Optional[str]
    brief_summary: Optional[str]
    saved_brief_path: Optional[str]
    current_run_id: int


class ClarifierOutput(BaseModel):
    company_name: str = Field(description="The company or client name inferred from the request.")
    goal: str = Field(description="The main purpose of the discovery work.")
    ready_to_research: bool = Field(description="Whether the request is specific enough to continue.")
    question_for_user: str = Field(description="A clarification question to ask the user if more information is needed.")


class PlannerOutput(BaseModel):
    research_plan: List[str] = Field(description="A short ordered plan for researching this client.")
    discovery_angle: str = Field(description="How the brief should be framed.")


class WriterOutput(BaseModel):
    summary: str = Field(description="A short summary of the client brief.")
    brief_markdown: str = Field(description="The full client brief in markdown.")


class EvaluatorOutput(BaseModel):
    feedback: str = Field(description="Feedback on the assistant's response")
    success_criteria_met: bool = Field(description="Whether the success criteria have been met")
    user_input_needed: bool = Field(description="True if more input or clarification is needed from the user")


class ClientDiscoverySidekick:
    def __init__(self):
        self.tools = []
        self.tool_node = None
        self.graph = None
        self.memory = MemorySaver()
        self.sidekick_id = str(uuid.uuid4())
        self.worker_llm = make_llm()
        self.research_llm = make_llm()
        self.writer_llm = make_llm()
        self.evaluator_llm = make_llm()
        self.clarifier_llm = make_llm()
        self.planner_llm = make_llm()
        self.research_llm_with_tools = None
        self.evaluator_llm_with_output = None
        self.clarifier_llm_with_output = None
        self.planner_llm_with_output = None
        self.writer_llm_with_output = None

    async def setup(self):
        init_db()
        self.tools = make_tools()
        self.tool_node = ToolNode(tools=self.tools)
        self.research_llm_with_tools = self.research_llm.bind_tools(self.tools)
        self.evaluator_llm_with_output = self.evaluator_llm.with_structured_output(EvaluatorOutput)
        self.clarifier_llm_with_output = self.clarifier_llm.with_structured_output(ClarifierOutput)
        self.planner_llm_with_output = self.planner_llm.with_structured_output(PlannerOutput)
        self.writer_llm_with_output = self.writer_llm.with_structured_output(WriterOutput)
        self.build_graph()

    def clarifier(self, state: State) -> Dict[str, Any]:
        system = SystemMessage(
            content=(
                "You are a client discovery clarifier. Decide if the user's request is specific enough to research. "
                "If not, ask exactly one concise clarification question. Focus on missing company name, goal, or desired output. "
                f"Today is {datetime.now().strftime('%B %d, %Y')}."
            )
        )
        result = self.clarifier_llm_with_output.invoke([system] + state["messages"])
        message = (
            f"Question: {result.question_for_user}" if not result.ready_to_research else
            f"Understood. I'll research {result.company_name} with the goal: {result.goal}."
        )
        return {
            "messages": [AIMessage(content=message)],
            "company_name": result.company_name,
            "goal": result.goal,
            "clarification_question": result.question_for_user if not result.ready_to_research else None,
            "user_input_needed": not result.ready_to_research,
        }

    def clarifier_router(self, state: State) -> str:
        return END if state["user_input_needed"] else "planner"

    def planner(self, state: State) -> Dict[str, Any]:
        memory = search_client_memory(state["company_name"]) if state["company_name"] else ""
        system = SystemMessage(
            content=(
                "You are a planner for client discovery work. Create a short, practical research plan that helps "
                "someone prepare outreach, discovery, or interview notes for a company."
            )
        )
        user = HumanMessage(
            content=(
                f"Original request: {self.latest_user_request(state)}\n"
                f"Company: {state['company_name']}\n"
                f"Goal: {state['goal']}\n"
                f"Past memory: {memory}\n"
                f"Success criteria: {state['success_criteria']}"
            )
        )
        result = self.planner_llm_with_output.invoke([system, user])
        plan_text = "\n".join([f"- {step}" for step in result.research_plan])
        return {
            "messages": [AIMessage(content=f"Research plan ready:\n{plan_text}\n\nAngle: {result.discovery_angle}")],
            "research_plan": result.research_plan,
            "briefing_context": result.discovery_angle,
        }

    def researcher(self, state: State) -> Dict[str, Any]:
        system_message = SystemMessage(
            content=(
                "You are a client discovery researcher. Use tools to gather practical information about the company, "
                "including what they do, recent developments, possible needs, and useful outreach angles. "
                "Use search_client_memory before repeating work if the company is known. "
                "Use log_client_note when you find something worth preserving. "
                f"Today is {datetime.now().strftime('%B %d, %Y')}."
            )
        )
        user_message = HumanMessage(
            content=(
                f"Company: {state['company_name']}\n"
                f"Goal: {state['goal']}\n"
                f"Research plan: {state['research_plan']}\n"
                f"Success criteria: {state['success_criteria']}"
            )
        )
        response = self.research_llm_with_tools.invoke([system_message, user_message] + state["messages"])
        return {"messages": [response]}

    def researcher_router(self, state: State) -> str:
        last_message = state["messages"][-1]
        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            return "tools"
        return "writer"

    def writer(self, state: State) -> Dict[str, Any]:
        system = SystemMessage(
            content=(
                "You are a writer producing a client discovery brief. Write a concise but useful markdown brief with these sections: "
                "Company Snapshot, Why They Matter, Discovery Notes, Outreach Angles, Risks or Unknowns, and Next Steps."
            )
        )
        user = HumanMessage(
            content=(
                f"Request: {self.latest_user_request(state)}\n"
                f"Company: {state['company_name']}\n"
                f"Goal: {state['goal']}\n"
                f"Plan: {state['research_plan']}\n"
                f"Conversation and findings:\n{self.format_conversation(state['messages'])}"
            )
        )
        result = self.writer_llm_with_output.invoke([system, user])
        return {
            "messages": [AIMessage(content=result.brief_markdown)],
            "final_brief": result.brief_markdown,
            "brief_summary": result.summary,
        }

    def evaluator(self, state: State) -> Dict[str, Any]:
        last_response = state["messages"][-1].content
        system_message = SystemMessage(
            content=(
                "You are an evaluator that checks whether a client discovery brief meets the stated success criteria. "
                "Approve if the brief is actionable, grounded in research, and aligned with the user's goal."
            )
        )
        user_message = HumanMessage(
            content=(
                f"Conversation:\n{self.format_conversation(state['messages'])}\n\n"
                f"Success criteria:\n{state['success_criteria']}\n\n"
                f"Latest response:\n{last_response}"
            )
        )
        eval_result = self.evaluator_llm_with_output.invoke([system_message, user_message])
        return {
            "messages": [AIMessage(content=f"Evaluator Feedback: {eval_result.feedback}")],
            "feedback_on_work": eval_result.feedback,
            "success_criteria_met": eval_result.success_criteria_met,
            "user_input_needed": eval_result.user_input_needed,
        }

    def evaluation_router(self, state: State) -> str:
        if state["success_criteria_met"] or state["user_input_needed"]:
            return END
        return "planner"

    def build_graph(self):
        graph_builder = StateGraph(State)
        graph_builder.add_node("clarifier", self.clarifier)
        graph_builder.add_node("planner", self.planner)
        graph_builder.add_node("researcher", self.researcher)
        graph_builder.add_node("tools", self.tool_node)
        graph_builder.add_node("writer", self.writer)
        graph_builder.add_node("evaluator", self.evaluator)
        graph_builder.add_edge(START, "clarifier")
        graph_builder.add_conditional_edges("clarifier", self.clarifier_router, {"planner": "planner", END: END})
        graph_builder.add_edge("planner", "researcher")
        graph_builder.add_conditional_edges("researcher", self.researcher_router, {"tools": "tools", "writer": "writer"})
        graph_builder.add_edge("tools", "researcher")
        graph_builder.add_edge("writer", "evaluator")
        graph_builder.add_conditional_edges("evaluator", self.evaluation_router, {"planner": "planner", END: END})
        self.graph = graph_builder.compile(checkpointer=self.memory)

    def latest_user_request(self, state: State) -> str:
        for message in reversed(state["messages"]):
            if isinstance(message, HumanMessage):
                return message.content
        return ""

    def format_conversation(self, messages: List[Any]) -> str:
        lines = []
        for message in messages:
            if isinstance(message, HumanMessage):
                lines.append(f"User: {message.content}")
            elif isinstance(message, AIMessage):
                text = message.content or "[Tool usage]"
                lines.append(f"Assistant: {text}")
        return "\n".join(lines)

    async def run_superstep(self, message, success_criteria, history):
        request_text = message.strip()
        success_criteria = success_criteria or "Produce a useful, research-backed client brief with practical outreach angles."
        run_id = create_run(self.sidekick_id, request_text, success_criteria)
        config = {"configurable": {"thread_id": self.sidekick_id}}
        state = {
            "messages": [HumanMessage(content=request_text)],
            "success_criteria": success_criteria,
            "feedback_on_work": None,
            "success_criteria_met": False,
            "user_input_needed": False,
            "company_name": "",
            "goal": "",
            "research_plan": [],
            "clarification_question": None,
            "briefing_context": None,
            "final_brief": None,
            "brief_summary": None,
            "saved_brief_path": None,
            "current_run_id": run_id,
        }
        result = await self.graph.ainvoke(state, config=config)

        company_name = result.get("company_name", "")
        goal = result.get("goal", "")
        if result.get("clarification_question"):
            save_clarification(run_id, result["clarification_question"])
            update_run(run_id, "awaiting_user_input", company_name, goal)
        elif result.get("final_brief"):
            saved_path = save_client_brief(company_name or "client", goal, result.get("brief_summary", ""), result["final_brief"], run_id)
            log_client_note(company_name or "client", result.get("brief_summary", "Client brief completed"), "brief_summary", run_id)
            update_run(run_id, "completed", company_name, goal)
            push(f"Client brief ready for {company_name or 'client'}")
            result["saved_brief_path"] = saved_path
        else:
            update_run(run_id, "stopped", company_name, goal)

        user = {"role": "user", "content": request_text}
        assistant_reply = result["messages"][-2].content if len(result["messages"]) >= 2 else result["messages"][-1].content
        evaluator_feedback = result["messages"][-1].content
        reply = {"role": "assistant", "content": assistant_reply}
        feedback = {"role": "assistant", "content": evaluator_feedback}
        if result.get("saved_brief_path"):
            feedback = {"role": "assistant", "content": f"{evaluator_feedback}\n\nSaved brief: {result['saved_brief_path']}"}
        return history + [user, reply, feedback]
