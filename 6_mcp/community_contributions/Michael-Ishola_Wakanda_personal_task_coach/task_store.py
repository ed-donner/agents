import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any
from uuid import uuid4

from config import now_iso


@dataclass
class Task:
    id: str
    title: str
    description: str
    due_date: str
    status: str = "pending"
    estimated_minutes: int = 30
    difficulty: int = 2
    blocker: str = ""
    created_at: str = ""
    updated_at: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class TaskStore:
    """JSON-backed task storage for local MCP tooling."""

    VALID_STATUSES = {"pending", "done", "missed", "skipped"}

    def __init__(self, file_path: Path):
        self.file_path = file_path
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.file_path.exists():
            self._save([])

    def _load(self) -> list[dict[str, Any]]:
        try:
            return json.loads(self.file_path.read_text(encoding="utf-8"))
        except Exception:
            return []

    def _save(self, tasks: list[dict[str, Any]]) -> None:
        self.file_path.write_text(json.dumps(tasks, indent=2), encoding="utf-8")

    def create_task(
        self,
        title: str,
        description: str,
        due_date: str,
        estimated_minutes: int = 30,
        difficulty: int = 2,
    ) -> dict[str, Any]:
        now = now_iso()
        task = Task(
            id=f"task-{uuid4().hex[:8]}",
            title=title.strip(),
            description=description.strip(),
            due_date=due_date,
            estimated_minutes=max(5, int(estimated_minutes)),
            difficulty=max(1, min(int(difficulty), 5)),
            created_at=now,
            updated_at=now,
        )
        tasks = self._load()
        tasks.append(task.to_dict())
        self._save(tasks)
        return task.to_dict()

    def update_task_status(self, task_id: str, status: str, blocker: str = "") -> dict[str, Any]:
        normalized_status = status.strip().lower()
        if normalized_status not in self.VALID_STATUSES:
            raise ValueError(f"Unsupported status: {normalized_status}")

        tasks = self._load()
        for task in tasks:
            if task["id"] == task_id:
                task["status"] = normalized_status
                task["blocker"] = blocker.strip()
                task["updated_at"] = now_iso()
                self._save(tasks)
                return task

        raise ValueError(f"Task not found: {task_id}")

    def get_tasks_by_date(self, due_date: str) -> list[dict[str, Any]]:
        tasks = self._load()
        selected = due_date.strip()
        if not selected:
            return tasks
        if "T" in selected:
            return [task for task in tasks if str(task.get("due_date", "")).strip() == selected]
        return [
            task
            for task in tasks
            if str(task.get("due_date", "")).strip() == selected
            or str(task.get("due_date", "")).startswith(f"{selected}T")
        ]

    def get_all(self) -> list[dict[str, Any]]:
        return self._load()
