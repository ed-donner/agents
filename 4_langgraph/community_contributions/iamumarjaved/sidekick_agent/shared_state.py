"""Shared state for real-time UI updates."""
import threading
from typing import Dict, List

validator_output: Dict[str, any] = {"text": "", "updated": False}
validator_lock = threading.Lock()

plan_output: Dict[str, any] = {"text": "", "updated": False}
plan_lock = threading.Lock()

execution_status: Dict[str, any] = {
    "status": "Idle",
    "iteration": 0,
    "step": "",
    "progress_log": []
}
status_lock = threading.Lock()


def update_validator_output(text: str):
    """Update the global validator output for real-time streaming."""
    global validator_output
    with validator_lock:
        validator_output["text"] = text
        validator_output["updated"] = True


def get_validator_output() -> str:
    """Get the current validator output."""
    with validator_lock:
        return validator_output["text"]


def clear_validator_output():
    """Clear the validator output."""
    global validator_output
    with validator_lock:
        validator_output["text"] = ""
        validator_output["updated"] = False


def update_plan_output(text: str):
    """Update the global plan output for real-time streaming."""
    global plan_output
    with plan_lock:
        plan_output["text"] = text
        plan_output["updated"] = True


def get_plan_output() -> str:
    """Get the current plan output."""
    with plan_lock:
        return plan_output["text"]


def clear_plan_output():
    """Clear the plan output."""
    global plan_output
    with plan_lock:
        plan_output["text"] = ""
        plan_output["updated"] = False


def update_status(status: str, iteration: int = 0, step: str = ""):
    """Update the current execution status for real-time UI updates."""
    global execution_status
    with status_lock:
        execution_status["status"] = status
        execution_status["iteration"] = iteration
        execution_status["step"] = step

        if step and status:
            emoji_map = {
                "plan": "📋",
                "build": "🔨",
                "tools": "🔧",
                "validate": "✅",
                "diagnose": "🔍",
                "review": "👁️",
                "complete": "🎉"
            }
            emoji = emoji_map.get(step.lower(), "⚙️")
            log_entry = f"[Iter {iteration}] {emoji} {step.upper()}: {status}"
            execution_status["progress_log"].append(log_entry)

            if len(execution_status["progress_log"]) > 30:
                execution_status["progress_log"].pop(0)


def get_status() -> dict:
    """Get the current status information."""
    with status_lock:
        return {
            "status": execution_status["status"],
            "iteration": execution_status["iteration"],
            "step": execution_status["step"],
            "progress_log": "\n".join(execution_status["progress_log"]) if execution_status["progress_log"] else "⏳ Waiting to start..."
        }


def clear_status():
    """Clear the status information."""
    global execution_status
    with status_lock:
        execution_status["status"] = "Idle"
        execution_status["iteration"] = 0
        execution_status["step"] = ""
        execution_status["progress_log"] = []

