import asyncio
from typing import Any

import gradio as gr
import pandas as pd

from coach import TaskCoach


class CoachingView:
    """Gradio interface for task planning, check-ins, and progress tracking."""

    def __init__(self, coach: TaskCoach):
        self.coach = coach

    @staticmethod
    def _to_df(tasks: list[dict[str, Any]]) -> pd.DataFrame:
        if not tasks:
            return pd.DataFrame(
                columns=[
                    "mark_done",
                    "id",
                    "title",
                    "due_date",
                    "status",
                    "estimated_minutes",
                    "difficulty",
                    "blocker",
                ]
            )
        rows = [
            {
                "mark_done": False,
                "id": task["id"],
                "title": task["title"],
                "due_date": task["due_date"],
                "status": task["status"],
                "estimated_minutes": task["estimated_minutes"],
                "difficulty": task["difficulty"],
                "blocker": task.get("blocker", ""),
            }
            for task in tasks
        ]
        return pd.DataFrame(rows)

    def _run(self, coro: Any) -> Any:
        return asyncio.run(coro)

    def plan_goal(self, goal: str) -> tuple[str, pd.DataFrame]:
        if not goal.strip():
            return "Enter a goal first.", self._to_df(self.coach.today_tasks())
        message = self._run(self.coach.plan_goal(goal))
        return message, self._to_df(self.coach.today_tasks())

    def check_in(self) -> tuple[str, pd.DataFrame]:
        message = self._run(self.coach.check_in_and_adapt())
        return message, self._to_df(self.coach.today_tasks())

    def mark_done(self, task_id: str, note: str) -> tuple[str, pd.DataFrame]:
        if not task_id.strip():
            return "Enter a valid task ID.", self._to_df(self.coach.today_tasks())
        message = self._run(self.coach.mark_done(task_id.strip(), note.strip()))
        return message, self._to_df(self.coach.today_tasks())

    def refresh_today(self) -> pd.DataFrame:
        return self._to_df(self.coach.today_tasks())

    def mark_checked_done(self, table_data: Any) -> tuple[str, pd.DataFrame]:
        if table_data is None:
            return "No tasks available.", self._to_df(self.coach.today_tasks())

        table = table_data if isinstance(table_data, pd.DataFrame) else pd.DataFrame(table_data)
        if table.empty or "mark_done" not in table.columns or "id" not in table.columns:
            return "No task rows to update.", self._to_df(self.coach.today_tasks())

        selected = table[table["mark_done"] == True]
        if selected.empty:
            return "Select at least one checkbox in Today Tasks.", self._to_df(self.coach.today_tasks())

        done_count = 0
        failed_ids: list[str] = []
        for _, row in selected.iterrows():
            task_id = str(row.get("id", "")).strip()
            if not task_id:
                continue
            try:
                self._run(self.coach.mark_done(task_id, "Marked done from Today Tasks table"))
                done_count += 1
            except Exception:
                failed_ids.append(task_id)

        refreshed = self._to_df(self.coach.today_tasks())
        if failed_ids:
            return (
                f"Marked {done_count} task(s) done. Failed: {', '.join(failed_ids)}",
                refreshed,
            )
        return f"Marked {done_count} task(s) as done.", refreshed

    def build(self) -> gr.Blocks:
        with gr.Blocks(title="Personal Task Coach") as app:
            gr.Markdown(
                """
# Personal Task Coach Agent
Set a goal, get a daily task plan, and let the coach adapt when tasks are missed.
"""
            )
            with gr.Row():
                with gr.Column(scale=2):
                    goal_input = gr.Textbox(
                        label="Goal",
                        placeholder="e.g., Learn LangGraph this week",
                        lines=2,
                    )
                    plan_btn = gr.Button("Create 5-Day Plan", variant="primary")
                    check_in_btn = gr.Button("Autonomous Check-In + Adapt")
                    status_box = gr.Markdown()

            today_table = gr.Dataframe(
                label="Today Tasks",
                headers=[
                    "mark_done",
                    "id",
                    "title",
                    "due_date",
                    "status",
                    "estimated_minutes",
                    "difficulty",
                    "blocker",
                ],
                datatype=["bool", "str", "str", "str", "str", "number", "number", "str"],
                value=self._to_df(self.coach.today_tasks()),
                interactive=True,
                wrap=True,
            )

            with gr.Row():
                done_btn = gr.Button("Mark Checked as Done")
                refresh_btn = gr.Button("Refresh Today Tasks")

            plan_btn.click(self.plan_goal, inputs=[goal_input], outputs=[status_box, today_table])
            check_in_btn.click(self.check_in, outputs=[status_box, today_table])
            done_btn.click(self.mark_checked_done, inputs=[today_table], outputs=[status_box, today_table])
            refresh_btn.click(self.refresh_today, outputs=[today_table])

        return app
