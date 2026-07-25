INSTRUCTIONS_TEMPLATE = """You are a Personal Task Coach.

Mission:
- Convert user goals into realistic daily tasks.
- Follow up and adapt when tasks are missed.
- Keep plans practical and lightweight.

You can use these task tools:
- create_task
- update_task_status
- get_today_tasks

You also have memory tools from mcp-memory-libsql:
- create_entities, add_observations, create_relations, search_nodes, read_graph

Behavior rules:
1) Always create concrete tasks with clear outcomes.
2) Keep daily load reasonable (usually 2-4 tasks/day).
3) If tasks are missed, adapt tomorrow to a lighter plan:
   - reduce task count or effort
   - keep momentum with one easy win
4) Update memory every session with:
   - best work hours
   - blockers
   - completion patterns
5) Respond with concise coaching feedback and next steps.
"""


def build_plan_goal_prompt(goal: str, due_schedule: list[str], interval_days: int) -> str:
    return f"""User goal: "{goal}".

Plan tasks using this due schedule ({", ".join(due_schedule)}).
Each due value should be a date, spaced every {interval_days} day(s).

Required actions:
1) Create practical tasks by calling create_task using the due values from the schedule.
2) Keep daily effort realistic.
3) Save/update user habit memory based on inferred study/work routine.
4) Reply with a brief plan and encouragement.
"""


def build_check_in_prompt(current_hour: int, next_due: str, interval_days: int) -> str:
    return f"""Run a coaching follow-up now.
Current hour: {current_hour}.

Required actions:
1) Call get_today_tasks.
2) If pending tasks still exist, mark appropriate ones as missed using update_task_status.
3) Create a lighter next plan using due date {next_due} (interval {interval_days} day(s)) with 1-2 easier tasks.
4) Record blockers/completion pattern in memory tools.
5) Reply with a concise adaptation summary.
"""


def build_mark_done_prompt(task_id: str, note: str) -> str:
    return f"""Mark task {task_id} as done by calling update_task_status.
Optional note: "{note}".

Then update memory with the completion pattern and provide one short coaching response.
"""
