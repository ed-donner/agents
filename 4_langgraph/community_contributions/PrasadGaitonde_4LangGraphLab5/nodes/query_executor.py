"""
Query Executor Node for the Intelligent Data Analysis Agent.
Executes generated SQL queries and returns results.
"""
from typing import Dict, Any, Optional
from tools.database_tools import get_db_manager


class QueryExecutorNode:
    """Node that executes SQL queries safely."""

    def __init__(self):
        self.db = get_db_manager()

    def __call__(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the generated SQL query.

        Args:
            state: Current state containing generated_query

        Returns:
            Updated state with execution results
        """
        sql_query = state.get("generated_query", "")

        if not sql_query:
            return {
                "query_results": None,
                "execution_error": "No query to execute",
                "execution_success": False,
                "messages": [{
                    "role": "assistant",
                    "content": "Error: No SQL query was generated."
                }]
            }

        # Execute the query
        results, error = self.db.execute_query(sql_query)

        # Update query in memory with results
        if state.get("memory"):
            state["memory"].save_query(
                session_id=state.get("session_id", "unknown"),
                sql=sql_query,
                result=str(results) if results else None,
                error=error,
                rewrite_attempt=state.get("rewrite_attempt", 0)
            )

        # Format results for display
        if error:
            result_text = f"Query Execution Failed:\n{error}"
        elif results:
            result_text = f"Query executed successfully. Found {len(results)} row(s).\n\n"
            # Show first 10 rows in output
            import pandas as pd
            df = pd.DataFrame(results)
            result_text += df.head(10).to_string(index=False)
            if len(results) > 10:
                result_text += f"\n... and {len(results) - 10} more rows"
        else:
            result_text = "Query executed successfully but returned no results."

        return {
            "query_results": results,
            "execution_error": error,
            "execution_success": error is None and results is not None,
            "results_text": result_text,
            "messages": [{
                "role": "assistant",
                "content": result_text
            }]
        }


def query_executor_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """Standalone query executor node function."""
    executor = QueryExecutorNode()
    return executor(state)
