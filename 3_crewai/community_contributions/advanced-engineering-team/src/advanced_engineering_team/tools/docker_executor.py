import tempfile
import os
import subprocess
from typing import Type

from pydantic import BaseModel, Field

from crewai.tools import BaseTool


class DockerExecutorInput(BaseModel):
    """Input schema for Docker code execution."""
    code: str = Field(..., description="Python3 code to execute. ALWAYS print the final result.")
    libraries: str = Field(
        default="",
        description="Comma-separated list of pip packages to install, e.g. 'requests,pandas'"
    )


class DockerCodeExecutor(BaseTool):
    name: str = "Docker Code Executor"
    description: str = (
        "Executes Python code inside a Docker container and returns the output. "
        "Use this to test and validate Python code."
    )
    args_schema: Type[BaseModel] = DockerExecutorInput

    def _run(self, code: str, libraries: str = "") -> str:
        with tempfile.TemporaryDirectory() as tmpdir:
            script_path = os.path.join(tmpdir, "script.py")
            with open(script_path, "w") as f:
                f.write(code)

            dockerfile = ["FROM python:3.12-slim"]
            if libraries:
                pkgs = [p.strip() for p in libraries.split(",") if p.strip()]
                if pkgs:
                    dockerfile.append(f"RUN pip install {' '.join(pkgs)} || echo 'Some packages failed to install'")
            dockerfile.append("COPY script.py /script.py")
            dockerfile.append("CMD python /script.py")

            with open(os.path.join(tmpdir, "Dockerfile"), "w") as f:
                f.write("\n".join(dockerfile))

            try:
                result = subprocess.run(
                    ["docker", "build", "-q", "-t", "crew-exec", tmpdir],
                    capture_output=True, text=True, timeout=120
                )
                if result.returncode != 0:
                    return f"Build error:\n{result.stderr.strip()}"

                result = subprocess.run(
                    ["docker", "run", "--rm", "crew-exec"],
                    capture_output=True, text=True, timeout=60
                )
                output = result.stdout.strip()
                if result.stderr:
                    output += f"\n(Stderr: {result.stderr.strip()})"
                return output if output else "(No output)"

            except subprocess.TimeoutExpired:
                return "Error: Execution timed out"
            except FileNotFoundError:
                return "Error: Docker not found. Is Docker running?"
            except Exception as e:
                return f"Error: {e}"
