"""
Output Formatter Node for the Intelligent Data Analysis Agent.
Formats final results for presentation to the user.
"""
from typing import Dict, Any, List
import pandas as pd


class OutputFormatterNode:
    """Node that formats final analysis results for user presentation."""

    def __call__(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format the final results for presentation.

        Args:
            state: Current state containing all analysis information

        Returns:
            Updated state with formatted output
        """
        # Gather all relevant information
        user_request = self._get_user_request(state)
        clarifications = state.get("user_clarifications", "")
        analysis_plan = state.get("analysis_plan", [])
        generated_query = state.get("generated_query", "")
        query_results = state.get("query_results")
        execution_error = state.get("execution_error")
        query_explanation = state.get("query_explanation", "")

        # Build formatted output
        output_sections = []

        # Section 1: Summary
        output_sections.append("## Analysis Results\n")

        if execution_error:
            output_sections.append(f"**Status:** Failed\n")
            output_sections.append(f"**Error:** {execution_error}\n")
        else:
            output_sections.append(f"**Status:** Completed Successfully\n")
            if query_results:
                output_sections.append(f"**Rows Returned:** {len(query_results)}\n")

        # Section 2: What was analyzed
        output_sections.append("\n## Request\n")
        output_sections.append(f"{user_request}\n")

        if clarifications:
            output_sections.append(f"\n**Clarifications:** {clarifications}\n")

        # Section 3: Analysis approach
        if analysis_plan:
            output_sections.append("\n## Analysis Approach\n")
            for i, step in enumerate(analysis_plan, 1):
                output_sections.append(f"{i}. {step}")

        # Section 4: SQL Query (for transparency)
        if generated_query:
            output_sections.append("\n## SQL Query Used\n")
            output_sections.append(f"```sql\n{generated_query}\n```\n")

            if query_explanation:
                output_sections.append(f"**Explanation:** {query_explanation}\n")

        # Section 5: Results table
        if query_results and not execution_error:
            output_sections.append("\n## Results\n")
            df = pd.DataFrame(query_results)

            # Format based on size
            if len(df) <= 20:
                output_sections.append(df.to_string(index=False))
            else:
                output_sections.append(f"*Showing first 20 of {len(df)} rows*\n")
                output_sections.append(df.head(20).to_string(index=False))

        # Section 6: Challenges encountered
        challenges = state.get("potential_challenges", [])
        rewrite_feedback = state.get("rewrite_feedback", "")
        rewrite_attempt = state.get("rewrite_attempt", 0)

        if challenges or rewrite_attempt > 0:
            output_sections.append("\n## Notes\n")
            if challenges:
                output_sections.append("**Potential Challenges Identified:**\n")
                for challenge in challenges:
                    output_sections.append(f"- {challenge}\n")

            if rewrite_attempt > 0:
                output_sections.append(f"\n**Query required {rewrite_attempt} rewrite attempt(s)**\n")
                if rewrite_feedback:
                    output_sections.append(f"Final feedback: {rewrite_feedback}\n")

        formatted_output = "\n".join(output_sections)

        return {
            "formatted_output": formatted_output,
            "messages": [{
                "role": "assistant",
                "content": formatted_output
            }]
        }

    def _get_user_request(self, state: Dict) -> str:
        """Extract user's original request from state."""
        messages = state.get("messages", [])
        for msg in messages:
            if hasattr(msg, "role") and msg.role == "user":
                return msg.content
        return str(messages[-1]) if messages else "No request provided"


def output_formatter_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """Standalone output formatter node function."""
    formatter = OutputFormatterNode()
    return formatter(state)
