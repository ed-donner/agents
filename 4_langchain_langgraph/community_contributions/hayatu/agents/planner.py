from schema import State, PlannerOutput
from agents.clarifier import format_conversation
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from datetime import datetime


def planner_agent(llm_with_output, state: State, user_preferences: dict) -> dict:
    prefs_text = "\n".join(f"- {k}: {v}" for k, v in user_preferences.items()) if user_preferences else "None yet."
    replan_context = ""
    if state.feedback_on_work:
        replan_context = f"""
REPLANNING: The previous attempt failed.
Feedback: {state.feedback_on_work}
Do NOT repeat the same steps. Address the feedback directly.
"""

    system_message = f"""You are the PLANNER agent in a multi-agent Sidekick system.

Your job is to convert the user's request into an executable plan with ordered subtasks.

{replan_context}

RULES:
- Produce a concise high-level plan description.
- Break the plan into ordered subtasks that the worker agent can execute one at a time.
- Each subtask should be a clear, actionable step.
- Group related work into single subtasks (don't create one subtask per search query).
- Auto-generate success_criteria that an evaluator can check.
- Factor in known user preferences to avoid redundant work.

KNOWN USER PREFERENCES:
{prefs_text}

CONVERSATION HISTORY:
{format_conversation(state.messages)}

Current date/time: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
"""

    result: PlannerOutput = llm_with_output.invoke([
        SystemMessage(content=system_message),
        HumanMessage(content="Generate the plan, subtasks, and success criteria."),
    ])

    plan_summary = f"Plan: {result.plan}\nSteps:\n" + "\n".join(
        f"  {i+1}. {t.task}" for i, t in enumerate(result.subtasks)
    )

    return {
        "plan": result.plan,
        "subtasks": result.subtasks,
        "success_criteria": result.success_criteria,
        "next_subtask_index": 0,
        "feedback_on_work": None,
        "success_criteria_met": False,
        "messages": [AIMessage(content=plan_summary)],
    }
