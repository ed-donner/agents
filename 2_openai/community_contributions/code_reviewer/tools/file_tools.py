import os
import shutil
import tempfile
from pathlib import Path
from agents import function_tool
import git


SUPPORTED_EXTENSIONS = {
    ".py", ".js", ".ts", ".java", ".go", ".rb", ".php",
    ".cs", ".cpp", ".c", ".h", ".rs", ".swift", ".kt"
}

IGNORED_DIRS = {
    ".git", "__pycache__", "node_modules", ".venv", "venv",
    "env", ".env", "dist", "build", ".idea", ".vscode",
    "migrations", "coverage", ".pytest_cache"
}

IGNORED_FILES = {
    "package-lock.json", "yarn.lock", "poetry.lock",
    "Pipfile.lock", ".DS_Store", "Thumbs.db"
}

MAX_FILE_SIZE_BYTES = 1_000_000


@function_tool
def clone_repo_tool(github_url: str) -> dict:
    """
Clones a public GitHub repository into a temporary directory."""
    try:
        if not github_url.startswith("https://github.com"):
            return {
                "success": False,
                "repo_dir": "",
                "error": f"Invalid GitHub URL: '{github_url}'. "
                         f"URL must start with https://github.com"
            }

        temp_dir = tempfile.mkdtemp(prefix="code_review_")

        git.Repo.clone_from(github_url, temp_dir, depth=1)

        return {
            "success": True,
            "repo_dir": temp_dir,
            "error": ""
        }

    except git.exc.GitCommandError as e:
        return {
            "success": False,
            "repo_dir": "",
            "error": f"Git clone failed: {str(e)}"
        }
    except Exception as e:
        return {
            "success": False,
            "repo_dir": "",
            "error": f"Unexpected error during clone: {str(e)}"
        }


@function_tool
def read_files_tool(repo_dir: str) -> dict:
    """Recursively walks a directory and reads all supported source files,
    skipping ignored directories, unsupported file types, and oversized files."""

    try:
        if not os.path.isdir(repo_dir):
            return {
                "success": False,
                "files": [],
                "skipped": [],
                "total_files_read": 0,
                "error": f"Directory not found: '{repo_dir}'"
            }

        root = Path(repo_dir)
        files = []
        skipped = []

        for path in root.rglob("*"):
            if path.is_dir():
                continue

            relative_path = str(path.relative_to(root))

            path_parts = set(path.parts)
            if path_parts & IGNORED_DIRS:
                skipped.append({
                    "file_path": relative_path,
                    "reason": "Inside an ignored directory"
                })
                continue

            if path.name in IGNORED_FILES:
                skipped.append({
                    "file_path": relative_path,
                    "reason": "Ignored file name"
                })
                continue

            if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
                skipped.append({
                    "file_path": relative_path,
                    "reason": f"Unsupported extension: '{path.suffix}'"
                })
                continue

            size_bytes = path.stat().st_size
            if size_bytes > MAX_FILE_SIZE_BYTES:
                skipped.append({
                    "file_path": relative_path,
                    "reason": f"File too large: {size_bytes} bytes (limit: {MAX_FILE_SIZE_BYTES})"
                })
                continue

            try:
                content = path.read_text(encoding="utf-8", errors="replace")
                files.append({
                    "file_path": relative_path,
                    "content": content,
                    "line_count": len(content.splitlines()),
                    "size_bytes": size_bytes
                })
            except Exception as read_error:
                skipped.append({
                    "file_path": relative_path,
                    "reason": f"Read error: {str(read_error)}"
                })

        return {
            "success": True,
            "files": files,
            "skipped": skipped,
            "total_files_read": len(files),
            "error": ""
        }

    except Exception as e:
        return {
            "success": False,
            "files": [],
            "skipped": [],
            "total_files_read": 0,
            "error": f"Unexpected error reading files: {str(e)}"
        }

@function_tool
def cleanup_repo_tool(repo_dir: str) -> dict:
    """Deletes the temporary directory created by clone_repo_tool after the review pipeline has completed."""
    try:
        if not os.path.isdir(repo_dir):
            return {
                "success": False,
                "error": f"Directory not found: '{repo_dir}'"
            }

        temp_base = tempfile.gettempdir()
        if not repo_dir.startswith(temp_base):
            return {
                "success": False,
                "error": f"Safety check failed: '{repo_dir}' is not inside the "
                         f"system temp directory. Deletion aborted."
            }

        shutil.rmtree(repo_dir)

        return {"success": True, "error": ""}

    except Exception as e:
        return {
            "success": False,
            "error": f"Cleanup failed: {str(e)}"
        }