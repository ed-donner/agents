"""Run the Jira Support Crew with a user question."""
import sys
from pathlib import Path

# Ensure package is importable when run from repo root or app directory
_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from jira_crew.crew import JiraSupportCrew


def run(user_question: str) -> str:
    """Run the crew and return the final answer."""
    inputs = {"user_question": user_question}
    result = JiraSupportCrew().crew().kickoff(inputs=inputs)
    # Crew kickoff returns a CrewOutput; the final output is typically the last task's output
    if hasattr(result, "raw") and result.raw:
        return result.raw
    if hasattr(result, "final_output") and result.final_output:
        return str(result.final_output)
    return str(result)


if __name__ == "__main__":
    q = sys.argv[1] if len(sys.argv) > 1 else "List all epics"
    print(run(q))
