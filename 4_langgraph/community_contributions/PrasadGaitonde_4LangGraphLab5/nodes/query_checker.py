"""
Query Checker Node for the Intelligent Data Analysis Agent.
Validates query results and determines if rewrite is needed.
"""
from typing import Dict, Any, List
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field
from config import QUERY_CHECKER_MODEL


class QueryCheckResult(BaseModel):
    """Output schema for query validation."""
    is_valid: bool = Field(default=False, description="Whether the query results appear valid and correct")
    needs_rewrite: bool = Field(default=False, description="True if the query needs to be rewritten")
    issues_found: List[str] = Field(default_factory=list, description="List of issues detected in the query or results")
    rewrite_feedback: str = Field(default="", description="Specific feedback for improving the query")
    confidence: float = Field(default=0.5, description="Confidence level 0.0-1.0 in this assessment")


class QueryCheckerNode:
    """Node that validates query results and determines if rewrite is needed."""

    def __init__(self):
        self.llm = ChatOpenAI(model=QUERY_CHECKER_MODEL)
        self.structured_llm = self.llm.with_structured_output(QueryCheckResult, method="function_calling")

    def generate_system_prompt(self, schema_info: str, user_request: str) -> str:
        """Generate the system prompt for the query checker."""
        return f"""You are a Query Checker for a data analysis system.
Your job is to validate that SQL query results correctly answer the user's request.

Database Schema:
{schema_info}

Original User Request:
"{user_request}"

Check for these issues:
1. Syntax errors in the query execution
2. Wrong table joins or missing relationships
3. Incorrect filters or aggregations
4. Results that don't match the user's request
5. Unrealistic results (NULL values, negative numbers where inappropriate, etc.)
6. Empty results that might indicate wrong conditions

Be thorough but fair - if the query appears to correctly answer the request, mark it as valid.
"""

    def __call__(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate query results and determine if rewrite is needed.

        Args:
            state: Current state containing query, results, and context

        Returns:
            Updated state with validation results
        """
        # Get schema
        from tools.database_tools import get_db_manager
        db = get_db_manager()
        schema = db.get_schema()
        schema_info = self._format_schema(schema)

        # Get query info
        sql_query = state.get("generated_query", "")
        results = state.get("query_results")
        execution_error = state.get("execution_error")
        user_request = self._get_user_request(state)

        # Get prior feedback for loop detection
        prior_feedback = state.get("rewrite_feedback", "")
        rewrite_attempt = state.get("rewrite_attempt", 0)

        # Build validation prompt
        system_prompt = self.generate_system_prompt(schema_info, user_request)

        user_prompt = f"""SQL Query executed:
```sql
{sql_query}
```

Execution Error (if any):
{execution_error or "None"}

Query Results:
{str(results) if results else "No results returned"}

Previous Rewrite Feedback (if any):
{prior_feedback or "None"}

This is rewrite attempt #{rewrite_attempt + 1}.

Validate whether the query correctly answers the user's request."""

        checker_messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ]

        result = self.structured_llm.invoke(checker_messages)

        # Detect infinite loop - if same issue persists after multiple attempts
        if rewrite_attempt >= 2 and result.needs_rewrite:
            # Check if feedback is similar to prior feedback
            if prior_feedback and result.rewrite_feedback in prior_feedback:
                # Force user input instead of continuing loop
                result.needs_rewrite = False
                result.is_valid = False
                result.issues_found.append("Query rewrite loop detected - user clarification needed")
                result.rewrite_feedback = "Multiple rewrite attempts have not resolved the issue. User clarification is needed."

        # Format output
        if result.is_valid:
            output_content = f"Query Validation: PASSED\n\nThe query results appear to correctly answer the user's request."
        elif result.needs_rewrite:
            output_content = f"Query Validation: NEEDS REWRITE\n\nIssues Found:\n"
            for issue in result.issues_found:
                output_content += f"  - {issue}\n"
            output_content += f"\nFeedback for Query Writer:\n{result.rewrite_feedback}"
        else:
            output_content = f"Query Validation: FAILED - User Input Needed\n\n"
            output_content += f"Issues: {', '.join(result.issues_found)}\n"
            output_content += f"Reason: {result.rewrite_feedback}"

        return {
            "query_is_valid": result.is_valid,
            "needs_rewrite": result.needs_rewrite,
            "checker_issues": result.issues_found,
            "rewrite_feedback": result.rewrite_feedback,
            "checker_confidence": result.confidence,
            "user_input_needed": not result.is_valid and not result.needs_rewrite,
            "messages": [{
                "role": "assistant",
                "content": output_content
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


def query_checker_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """Standalone query checker node function."""
    checker = QueryCheckerNode()
    return checker(state)
