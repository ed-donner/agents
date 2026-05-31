import os
from datetime import date, datetime, timedelta
from pathlib import Path


APP_DIR = Path(__file__).resolve().parent
MEMORY_DIR = APP_DIR / "memory"
TASKS_FILE = MEMORY_DIR / "tasks.json"
TASK_DUE_INTERVAL_DAYS = int(os.getenv("TASK_DUE_INTERVAL_DAYS", "1"))
TASK_PLAN_STEPS = int(os.getenv("TASK_PLAN_STEPS", "5"))


def iso_today() -> str:
    return date.today().isoformat()


def now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def build_due_schedule(
    steps: int = TASK_PLAN_STEPS,
    interval_days: int = TASK_DUE_INTERVAL_DAYS,
    start_offset_days: int = 0,
) -> list[str]:
    base = date.today()
    safe_steps = max(1, steps)
    safe_interval = max(1, interval_days)
    safe_start = max(0, start_offset_days)
    return [
        (base + timedelta(days=safe_start + (i * safe_interval))).isoformat()
        for i in range(safe_steps)
    ]
