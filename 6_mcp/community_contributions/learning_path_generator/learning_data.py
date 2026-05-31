"""
Core learning path data management.
Simple JSON-based storage for dynamically generated paths.
"""

import json
from pathlib import Path
from typing import Dict, Optional
from datetime import datetime

# Path to data directory
DATA_DIR = Path(__file__).parent / "data"
PATHS_FILE = DATA_DIR / "paths.json"
PROGRESS_FILE = DATA_DIR / "progress.json"

# Ensure data directory exists
DATA_DIR.mkdir(exist_ok=True)


def load_json_file(file_path: Path, default: dict = None) -> dict:
    """Load JSON file, return default if file doesn't exist."""
    if file_path.exists():
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return default if default is not None else {}


def save_json_file(file_path: Path, data: dict):
    """Save data to JSON file."""
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def save_path(path: dict):
    """Save or update a learning path."""
    paths = load_json_file(PATHS_FILE, default={})
    paths[path["path_id"]] = path
    save_json_file(PATHS_FILE, paths)


def get_path(path_id: str) -> Optional[dict]:
    """Retrieve a learning path by ID."""
    paths = load_json_file(PATHS_FILE, default={})
    return paths.get(path_id)


def get_all_paths() -> dict:
    """Get all learning paths."""
    return load_json_file(PATHS_FILE, default={})


def mark_step_completed(path_id: str, step_id: str) -> dict:
    """Mark a step as completed and return updated progress."""
    paths = load_json_file(PATHS_FILE, default={})
    progress = load_json_file(PROGRESS_FILE, default={})
    
    if path_id not in paths:
        raise ValueError(f"Path {path_id} not found")
    
    path = paths[path_id]
    
    # Find and mark step as completed in path
    for step in path.get("steps", []):
        if step["id"] == step_id:
            step["completed"] = True
            break
    
    # Update progress
    if path_id not in progress:
        progress[path_id] = {
            "path_id": path_id,
            "completed_steps": [],
            "last_updated": datetime.now().isoformat()
        }
    
    if step_id not in progress[path_id]["completed_steps"]:
        progress[path_id]["completed_steps"].append(step_id)
    
    progress[path_id]["last_updated"] = datetime.now().isoformat()
    
    # Save updates
    save_json_file(PATHS_FILE, paths)
    save_json_file(PROGRESS_FILE, progress)
    
    return {
        "path_id": path_id,
        "step_id": step_id,
        "status": "completed",
        "completed_steps": progress[path_id]["completed_steps"],
        "total_steps": len(path.get("steps", [])),
        "progress_percentage": len(progress[path_id]["completed_steps"]) / len(path.get("steps", [])) * 100 if path.get("steps") else 0
    }


def get_next_step(path_id: str) -> Optional[dict]:
    """Get the next uncompleted step in a learning path."""
    paths = load_json_file(PATHS_FILE, default={})
    progress = load_json_file(PROGRESS_FILE, default={})
    
    if path_id not in paths:
        return None
    
    path = paths[path_id]
    completed_steps = progress.get(path_id, {}).get("completed_steps", [])
    
    # Find first uncompleted step
    for step in path.get("steps", []):
        if step["id"] not in completed_steps:
            return {
                "step": step,
                "step_number": path["steps"].index(step) + 1,
                "total_steps": len(path["steps"]),
                "progress": f"{len(completed_steps)}/{len(path['steps'])} steps completed"
            }
    
    # All steps completed
    return {
        "step": None,
        "message": "Congratulations! You've completed all steps in this learning path.",
        "progress": f"{len(completed_steps)}/{len(path['steps'])} steps completed"
    }


def get_path_progress(path_id: str) -> dict:
    """Get progress information for a path."""
    paths = load_json_file(PATHS_FILE, default={})
    progress = load_json_file(PROGRESS_FILE, default={})
    
    if path_id not in paths:
        return {}
    
    path = paths[path_id]
    path_progress = progress.get(path_id, {})
    completed_steps = path_progress.get("completed_steps", [])
    
    return {
        "completed_steps": completed_steps,
        "total_steps": len(path.get("steps", [])),
        "completed_count": len(completed_steps),
        "progress_percentage": len(completed_steps) / len(path.get("steps", [])) * 100 if path.get("steps") else 0,
        "last_updated": path_progress.get("last_updated", "")
    }
