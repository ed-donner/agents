"""
Planner Node for the Intelligent Data Analysis Agent.
Creates a step-by-step analysis plan and identifies target tables.
"""
from typing import Dict, Any, List, Optional
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field
from config import PLANNER_MODEL
from tools.database_tools import get_db_manager


class AnalysisPlan(BaseModel):
    """Output schema for analysis planning."""
    plan_steps: List[str] = Field(default_factory=list, description="Step-by-step plan for analyzing the data request")
    target_tables: List[str] = Field(default_factory=list, description="Names of database tables needed for this analysis")
    required_columns: Dict[str, List[str]] = Field(default_factory=dict, description="Specific columns needed from each table")
    join_strategy: str = Field(default="", description="How tables should be joined together")
    potential_challenges: List[str] = Field(default_factory=list, description="Potential issues or ambiguities to watch for")


class PlannerNode:
    """Node that creates analysis plans for data queries."""

    def __init__(self):
        self.llm = ChatOpenAI(model=PLANNER_MODEL)
        self.structured_llm = self.llm.with_structured_output(AnalysisPlan, method="function_calling")

    def generate_system_prompt(self, schema_info: str) -> str:
        """Generate the system prompt for the planner."""
        return f"""You are a Planning assistant for a data analysis system.
Your job is to create a clear, step-by-step plan for answering a data analysis request.

Database Schema Available:
{schema_info}

When creating your plan:
1. Identify which tables contain the needed data
2. Determine how tables should be joined
3. List the specific columns required
4. Note any potential challenges (ambiguous terms, missing data, complex calculations)

Your plan will guide the Query Writer in generating accurate SQL.
"""

    def __call__(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create an analysis plan based on user request and clarifications.

        Args:
            state: Current state containing messages, clarifications, etc.

        Returns:
            Updated state with analysis plan
        """
        # Get schema
        db = get_db_manager()
        schema = db.get_schema()
        schema_info = self._format_schema(schema)

        # Get user request
        user_request = self._get_user_request(state)

        # Get user clarifications if available
        clarifications = state.get("user_clarifications", "No additional clarifications provided.")

        # Generate plan
        system_prompt = self.generate_system_prompt(schema_info)

        user_prompt = f"""User's data analysis request:
"{user_request}"

User's clarifications (if any):
{clarifications}

Create a detailed analysis plan for this request."""

        planner_messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ]

        result = self.structured_llm.invoke(planner_messages)

        # Save plan to memory if available
        if state.get("memory"):
            state["memory"].save_analysis_plan(
                session_id=state.get("session_id", "unknown"),
                plan_steps=result.plan_steps,
                target_tables=result.target_tables,
                clarifying_questions=state.get("clarifying_questions"),
                user_clarifications=clarifications
            )

        # Format plan for display
        plan_text = self._format_plan(result)

        return {
            "analysis_plan": result.plan_steps,
            "target_tables": result.target_tables,
            "required_columns": result.required_columns,
            "join_strategy": result.join_strategy,
            "potential_challenges": result.potential_challenges,
            "plan_text": plan_text,
            "messages": [{
                "role": "assistant",
                "content": f"Analysis Plan:\n\n{plan_text}"
            }]
        }

    def _format_schema(self, schema: Dict) -> str:
        """Format schema for the LLM prompt."""
        lines = []
        for table, info in schema.items():
            cols = ", ".join([c["name"] for c in info["columns"]])
            lines.append(f"Table '{table}': {cols}")
        return "\n".join(lines)

    def _get_user_request(self, state: Dict) -> str:
        """Extract user's original request from state."""
        messages = state.get("messages", [])
        for msg in messages:
            if hasattr(msg, "role") and msg.role == "user":
                return msg.content
        return str(messages[-1]) if messages else "No request provided"

    def _format_plan(self, plan: AnalysisPlan) -> str:
        """Format analysis plan for display."""
        lines = [
            "**Steps:**",
            *[f"  {i+1}. {step}" for i, step in enumerate(plan.plan_steps)],
            "",
            "**Tables:** " + ", ".join(plan.target_tables),
            "",
            "**Join Strategy:** " + plan.join_strategy,
        ]

        if plan.potential_challenges:
            lines.extend(["", "**Potential Challenges:**"])
            for challenge in plan.potential_challenges:
                lines.append(f"  - {challenge}")

        return "\n".join(lines)


def planner_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """Standalone planner node function."""
    planner = PlannerNode()
    return planner(state)
