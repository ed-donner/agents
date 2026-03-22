import os
import shutil
import tempfile
from pathlib import Path
from agents import function_tool
import git


# ── Constants ─────────────────────────────────────────────────────────────────

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

MAX_FILE_SIZE_BYTES = 1_000_000  # 1MB — skip files larger than this


# ── clone_repo_tool ───────────────────────────────────────────────────────────

@function_tool
def clone_repo_tool(github_url: str) -> dict:
    """
    Clones a public GitHub repository into a temporary directory.

    Args:
        github_url: The full GitHub repository URL to clone.
                    Example: https://github.com/username/repo

    Returns:
        A dict with:
          - success (bool): Whether the clone succeeded.
          - repo_dir (str): Absolute path to the cloned repository.
          - error (str): Error message if the clone failed.
    """
    try:
        # Validate URL format before attempting clone
        if not github_url.startswith("https://github.com"):
            return {
                "success": False,
                "repo_dir": "",
                "error": f"Invalid GitHub URL: '{github_url}'. "
                         f"URL must start with https://github.com"
            }

        # Create a unique temp directory for this clone
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


# ── read_files_tool ───────────────────────────────────────────────────────────

@function_tool
def read_files_tool(repo_dir: str) -> dict:
    """
    Recursively walks a directory and reads all supported source files,
    skipping ignored directories, unsupported file types, and oversized files.

    Args:
        repo_dir: Absolute path to the root directory of the codebase.

    Returns:
        A dict with:
          - success (bool): Whether the read operation succeeded.
          - files (list[dict]): List of file objects, each containing:
              - file_path (str): Relative path from repo root.
              - content (str): Full file content as a string.
              - line_count (int): Number of lines in the file.
              - size_bytes (int): File size in bytes.
          - skipped (list[dict]): Files that were skipped, each with:
              - file_path (str): Relative path.
              - reason (str): Why the file was skipped.
          - total_files_read (int): Total number of files successfully read.
          - error (str): Error message if the operation failed entirely.
    """
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
            # Skip directories themselves
            if path.is_dir():
                continue

            relative_path = str(path.relative_to(root))

            # Skip ignored directories anywhere in the path
            path_parts = set(path.parts)
            if path_parts & IGNORED_DIRS:
                skipped.append({
                    "file_path": relative_path,
                    "reason": "Inside an ignored directory"
                })
                continue

            # Skip ignored file names
            if path.name in IGNORED_FILES:
                skipped.append({
                    "file_path": relative_path,
                    "reason": "Ignored file name"
                })
                continue

            # Skip unsupported extensions
            if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
                skipped.append({
                    "file_path": relative_path,
                    "reason": f"Unsupported extension: '{path.suffix}'"
                })
                continue

            # Skip oversized files
            size_bytes = path.stat().st_size
            if size_bytes > MAX_FILE_SIZE_BYTES:
                skipped.append({
                    "file_path": relative_path,
                    "reason": f"File too large: {size_bytes} bytes (limit: {MAX_FILE_SIZE_BYTES})"
                })
                continue

            # Read file content
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


# ── cleanup_repo_tool ─────────────────────────────────────────────────────────

@function_tool
def cleanup_repo_tool(repo_dir: str) -> dict:
    """
    Deletes the temporary directory created by clone_repo_tool after the
    review pipeline has completed. Always call this at the end of the pipeline
    to avoid accumulating temp directories on disk.

    Args:
        repo_dir: Absolute path to the temp directory to delete.

    Returns:
        A dict with:
          - success (bool): Whether cleanup succeeded.
          - error (str): Error message if cleanup failed.
    """
    try:
        if not os.path.isdir(repo_dir):
            return {
                "success": False,
                "error": f"Directory not found: '{repo_dir}'"
            }

        # Safety check — only delete directories inside the system temp folder
        # to prevent accidental deletion of important directories
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