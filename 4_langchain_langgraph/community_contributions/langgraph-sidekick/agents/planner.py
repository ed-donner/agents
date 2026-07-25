from schema import State, PlannerOutput, PlannerStateDiff
from utils.utils import dict_to_aimessage, format_conversation, CAPABILITIES_MANIFEST
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.runnables import Runnable
from langchain_core.language_models import LanguageModelInput
from langchain_openai.chat_models.base import _DictOrPydantic
from datetime import datetime
from typing import Any
import json


def planner_agent(
    llm_with_output: Runnable[LanguageModelInput, _DictOrPydantic],
    state: State
) -> dict:

    replanning_context = ""
    if state.replan_needed:
      replanning_context = f"""
****************************************************
CRITICAL: REPLANNING MODE ACTIVATED
****************************************************
The previous execution FAILED. You are now correcting the plan.

PREVIOUS FEEDBACK / ERROR:
"{state.feedback_on_work}"

REQUIREMENTS FOR THE NEW PLAN:
1. Do NOT repeat the exact same steps that just failed.
2. If a tool failed (e.g., file not found), add a diagnostic step first
   (e.g., "List directory" to find the correct name).
3. If a search failed, use DIFFERENT query terms.
4. Your new subtasks MUST explicitly address the failure reason.
"""

    system_msg = f"""
Role:
You are the PLANNER agent in a LangGraph-based multi-agent system.

{replanning_context}

Your responsibility is to convert the conversation into an EXECUTABLE PLAN
that downstream agents can carry out WITHOUT ambiguity, hidden assumptions,
or reliance on implicit intermediate results.

You MUST produce output that conforms exactly to the PlannerOutput schema.

--------------------------------------------------------------------
SYSTEM MODEL (CRITICAL — YOU MUST FOLLOW)
--------------------------------------------------------------------

1. STATE MODEL
- Agents only share information through:
  - State fields (explicitly written)
  - The message history (unstructured text)
- Tool outputs appear ONLY as ToolMessages in the message list.
- Tool outputs are NOT structured unless explicitly extracted by an agent.

2. EXECUTION MODEL
- Subtasks are executed SEQUENTIALLY.
- Each subtask MUST be executable in isolation using only:
  - The current State
  - The full message history
- A subtask MUST NOT assume access to:
  - “previous search results”
  - “earlier findings”
  unless that data is explicitly written to State.

3. TOOL SEMANTICS & PARALLELISM
- **Agents are capable of PARALLEL tool execution.**
- If multiple pieces of information are needed (e.g., "Research X, Y, and Z"),
  assign this as a **SINGLE** subtask.
- The agent will execute all necessary searches/lookups simultaneously.
- DO NOT split independent information gathering into separate sequential subtasks.

4. FAILURE MODES TO AVOID
DO NOT generate subtasks that:
- Refer to “the search results”
- Cause an agent to re-search the same information endlessly
- Create a "waterfall" of tiny tasks when one broad task would suffice.

--------------------------------------------------------------------
AVAILABLE AGENTS & CAPABILITIES
--------------------------------------------------------------------

CAPABILITIES MANIFEST:
{json.dumps(CAPABILITIES_MANIFEST, indent=2)}

--------------------------------------------------------------------
SUBTASK DESIGN RULES (STRICT)
--------------------------------------------------------------------

- Subtasks MUST be:
  - Atomic (in terms of responsibility)
  - Sequential (in terms of dependency)
  - Fully executable
  - Explicit about their expected outcome

**OPTIMIZATION (GROUPING):**
- **Merge independent queries:** ❌ Bad:
    1. "Search for the price of BTC."
    2. "Search for the price of ETH."
    3. "Search for the price of SOL."
  ✅ Good:
    1. "Search for the current prices of BTC, ETH, and SOL."
  (The Researcher will run these 3 searches in parallel).

- **Merge preparation and execution:**
  - If an executor subtask involves sending a message or writing a file,
    the preparation of the payload MUST be included in the SAME subtask.

- **Requires Side Effects:**
  - MUST set requires_side_effects=true for:
      - File writes, moves, deletions
      - Sending messages (e.g., WhatsApp)
      - Any irreversible external action
  - MUST set requires_side_effects=false for:
      - Pure computation, parsing, data transformation
      - **Research and Information gathering** (even if using tools)

--------------------------------------------------------------------
SUCCESS CRITERIA SEMANTICS (CRITICAL)
--------------------------------------------------------------------
- Success criteria MUST be evaluable at the time the Evaluator runs.
- If ANY subtask has requires_side_effects = true, then the criteria
  MUST describe READINESS and APPROVAL, NOT execution.

--------------------------------------------------------------------
CURRENT CONTEXT
--------------------------------------------------------------------
- Read the full conversation.
- Assume NO hidden state.
- Assume NO prior structured data exists.
- Current date/time: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

--------------------------------------------------------------------
BEGIN PLANNING
--------------------------------------------------------------------
"""

    human_msg = f"""
Conversation so far:
{format_conversation(state.messages)}

Generate the plan, subtasks, and success criteria.
"""

    llm_response: PlannerOutput = llm_with_output.invoke([
        SystemMessage(content=system_msg),
        HumanMessage(content=human_msg)
    ])

    diff: PlannerStateDiff = llm_response.state_diff

    updates: dict[str, Any] = {
        "plan": diff.plan,
        "subtasks": diff.subtasks,
        "success_criteria": diff.success_criteria,
        "next_subtask_index": 0,
        "subtask_results": [],
        "replan_needed": False,
        "success_criteria_met": False,
        "feedback_on_work": None
    }

    if diff.messages:
        updates["messages"] = [dict_to_aimessage(m) for m in diff.messages]

    return updates
