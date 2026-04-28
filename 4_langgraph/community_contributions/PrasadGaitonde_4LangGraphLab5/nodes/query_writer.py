"""
Query Writer Node for the Intelligent Data Analysis Agent.
Generates SQL/MDX queries based on the analysis plan.
"""
from typing import Dict, Any, List, Optional
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field
from config import QUERY_WRITER_MODEL
from tools.database_tools import get_db_manager


class GeneratedQuery(BaseModel):
    """Output schema for generated SQL query."""
    sql_query: str = Field(default="", description="The generated SQL SELECT query")
    explanation: str = Field(default="", description="Brief explanation of what the query does")
    tables_used: List[str] = Field(default_factory=list, description="List of tables referenced in the query")
    confidence: float = Field(default=0.5, description="Confidence level 0.0-1.0 in query correctness")


class QueryWriterNode:
    """Node that generates SQL queries from analysis plans."""

    def __init__(self):
        self.llm = ChatOpenAI(model=QUERY_WRITER_MODEL)
        self.structured_llm = self.llm.with_structured_output(GeneratedQuery, method="function_calling")

    def generate_system_prompt(self, schema_info: str) -> str:
        """Generate the system prompt for the query writer."""
        return f"""You are a Query Writer for a data analysis system.
Your job is to generate accurate SQL SELECT queries based on analysis plans.

Database Schema:
{schema_info}

SQL Guidelines:
1. Only write SELECT queries (no INSERT, UPDATE, DELETE, DROP)
2. Use proper JOIN syntax for table relationships
3. Alias tables for readability in complex queries
4. Include comments for complex logic
5. Use parameterized patterns where applicable
6. Respect foreign key relationships shown in schema

Your queries will be validated and executed by downstream nodes.
"""

    def __call__(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a SQL query based on the analysis plan.

        Args:
            state: Current state containing plan, target tables, etc.

        Returns:
            Updated state with generated query
        """
        # Get schema
        db = get_db_manager()
        schema = db.get_schema()
        schema_info = self._format_schema_with_details(schema)

        # Get analysis plan info
        plan_steps = state.get("analysis_plan", [])
        target_tables = state.get("target_tables", [])
        join_strategy = state.get("join_strategy", "")
        user_request = self._get_user_request(state)
        clarifications = state.get("user_clarifications", "")

        # Get rewrite feedback if this is a rewrite attempt
        rewrite_feedback = state.get("rewrite_feedback", "")
        rewrite_attempt = state.get("rewrite_attempt", 0)

        # Generate query
        system_prompt = self.generate_system_prompt(schema_info)

        user_prompt = f"""User's data analysis request:
"{user_request}"

User clarifications:
{clarifications}

Analysis Plan Steps:
{chr(10).join(plan_steps)}

Target Tables: {', '.join(target_tables)}

Join Strategy: {join_strategy}
"""

        if rewrite_feedback:
            user_prompt += f"""

PREVIOUS ATTEMPT FAILED - Rewrite Feedback:
{rewrite_feedback}

This is rewrite attempt #{rewrite_attempt + 1}. Address the issues above."""

        user_prompt += """
Generate a SQL SELECT query that answers the user's request."""

        writer_messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ]

        result = self.structured_llm.invoke(writer_messages)

        # Save query to memory
        if state.get("memory"):
            state["memory"].save_query(
                session_id=state.get("session_id", "unknown"),
                sql=result.sql_query,
                rewrite_attempt=rewrite_attempt
            )

        return {
            "generated_query": result.sql_query,
            "query_explanation": result.explanation,
            "tables_used": result.tables_used,
            "query_confidence": result.confidence,
            "rewrite_attempt": rewrite_attempt,
            "messages": [{
                "role": "assistant",
                "content": f"Generated SQL Query:\n\n```sql\n{result.sql_query}\n```\n\n{result.explanation}"
            }]
        }

    def _format_schema_with_details(self, schema: Dict) -> str:
        """Format schema with column types and relationships."""
        lines = []
        for table, info in schema.items():
            col_defs = []
            for col in info["columns"]:
                pk = " PRIMARY KEY" if col["pk"] else ""
                nn = " NOT NULL" if col["not_null"] else ""
                col_defs.append(f"  {col['name']} {col['type']}{pk}{nn}")

            fk_defs = []
            for fk in info["foreign_keys"]:
                fk_defs.append(f"  FOREIGN KEY ({fk['from']}) -> {fk['table']}.{fk['to']}")

            lines.append(f"Table: {table}")
            lines.extend(col_defs)
            if fk_defs:
                lines.extend(fk_defs)
            lines.append("")

        return "\n".join(lines)

    def _get_user_request(self, state: Dict) -> str:
        """Extract user's original request from state."""
        messages = state.get("messages", [])
        for msg in messages:
            if hasattr(msg, "role") and msg.role == "user":
                return msg.content
        return str(messages[-1]) if messages else "No request provided"


def query_writer_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """Standalone query writer node function."""
    writer = QueryWriterNode()
    return writer(state)
