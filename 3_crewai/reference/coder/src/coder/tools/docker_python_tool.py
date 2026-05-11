from crewai.tools import tool
import subprocess


@tool("Run Python in Docker")
def run_python_in_docker(code: str) -> str:
    """
    Execute a Python code string inside an ephemeral Docker container and
    return whatever the code printed to stdout. Works on macOS and Windows
    provided Docker Desktop is installed and running.

    Args:
        code: The Python source code to execute. Can be multi-line.
    Returns:
        The text printed to stdout by the executed code.
    """
    result = subprocess.run(
        ["docker", "run", "--rm", "-i", "python:3.13-slim", "python", "-"],
        input=code,
        capture_output=True,
        text=True,
        timeout=60,
    )
    return result.stdout
