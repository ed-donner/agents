from crewai.tools import tool
from pathlib import Path
import shutil
import subprocess
import sys


SANDBOX_DIR = Path(__file__).parents[3] / "sandbox"
SANDBOX_DIR.mkdir(parents=True, exist_ok=True)


def reset_sandbox() -> None:
    """Wipe the sandbox and re-initialize it as a fresh uv project with gradio."""
    if SANDBOX_DIR.exists():
        try:
            shutil.rmtree(SANDBOX_DIR)
        except OSError:
            # A prior Docker run may have left a Linux-style symlink (e.g. a
            # venv's lib64 -> lib) inside the bind-mounted sandbox. Windows'
            # shutil.rmtree can't traverse that reparse point, but the native
            # `rmdir /s /q` deletes it without needing to enumerate it.
            if sys.platform == "win32":
                subprocess.run(["cmd", "/c", "rmdir", "/s", "/q", str(SANDBOX_DIR)], check=True)
            else:
                raise
    SANDBOX_DIR.mkdir(parents=True, exist_ok=True)

    subprocess.run(["uv", "init", "--bare", "--python", "3.13"], cwd=SANDBOX_DIR, check=True)
    subprocess.run(["uv", "add", "--no-sync", "gradio"], cwd=SANDBOX_DIR, check=True)

@tool("List Sandbox Files")
def list_sandbox_files() -> str:
    """
    List the filenames currently in the sandbox directory.

    Returns:
        A newline-separated list of filenames, or a message if the
        sandbox is empty.
    """
    names = sorted(p.name for p in SANDBOX_DIR.iterdir())
    return "\n".join(names) if names else "The sandbox is empty."


@tool("Read Sandbox File")
def read_sandbox_file(filename: str) -> str:
    """
    Read and return the text contents of a file in the sandbox directory.

    Args:
        filename: The name of the file to read (e.g. "solution.py").
    Returns:
        The file's contents, or a message if the file does not exist.
    """
    path = SANDBOX_DIR / filename
    if not path.is_file():
        return f"No such file in the sandbox: {filename}"
    return path.read_text(encoding="utf-8")


@tool("Write Sandbox File")
def write_sandbox_file(filename: str, content: str) -> str:
    """
    Write text to a file in the sandbox directory, replacing any existing
    file with the same name.

    Args:
        filename: The name of the file to write (e.g. "solution.py").
        content: The text content to write.
    Returns:
        A confirmation message.
    """
    path = SANDBOX_DIR / filename
    path.write_text(content, encoding="utf-8")
    return f"Wrote {len(content)} characters to {filename}."


@tool("Run Sandbox Python File")
def run_sandbox_python(filename: str) -> str:
    """
    Execute a Python file from the sandbox directory inside an ephemeral
    Docker container, with the sandbox mounted as the working directory,
    using a uv run to run the code in the uv project,
    and return whatever the script printed to stdout and stderr.

    Note: the stdlib `unittest` module writes test results (including
    failures and tracebacks) to stderr by default, so stderr must be
    captured too or test runs will appear to produce no output.

    Args:
        filename: The name of the Python file to run (e.g. "solution.py").
    Returns:
        The text printed to stdout and stderr by the executed script.
    """
    result = subprocess.run(
        [
            "docker", "run", "--rm",
            "-v", f"{SANDBOX_DIR}:/workspace",
            "-w", "/workspace",
            "-e", "UV_PROJECT_ENVIRONMENT=/opt/venv",
            "ghcr.io/astral-sh/uv:python3.13-bookworm-slim",
            "uv", "run", filename,
        ],
        capture_output=True,
        text=True,
        timeout=300,
    )
    output = result.stdout
    if result.stderr:
        output += f"\n--- stderr ---\n{result.stderr}"
    return output

sandbox_tools = [list_sandbox_files, read_sandbox_file, write_sandbox_file, run_sandbox_python]


def _never_cache(*_args, **_kwargs) -> bool:
    return False


# Sandbox state changes between calls (files appear/change/run), so caching tool
# results would feed agents stale data. Opt out of CrewAI's default tool caching.
for _t in sandbox_tools:
    _t.cache_function = _never_cache
