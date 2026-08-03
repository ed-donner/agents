import os
import shlex
import subprocess
import tempfile
from typing import Optional, Type

from pydantic import BaseModel, Field
from langchain.tools import BaseTool

class _PyInput(BaseModel):
    code: str = Field(..., description="Python code to run in the sandbox")

class PythonREPLDockerTool(BaseTool):
    """Run short Python snippets in an isolated Docker container.
    - No network, read-only rootfs
    - CPU / memory / pids limited
    - Per-call ephemeral container
    """
    name: str = "python_repl_docker"
    description: str = (
        "Execute small, side-effect-free Python snippets safely. "
        "No internet, limited CPU/RAM, read-only filesystem."
    )
    args_schema: Type[BaseModel] = _PyInput

    # Tunables
    image: str = "pyrepl-sandbox:latest"
    timeout_s: int = 6
    mem: str = "256m"
    cpus: str = "0.5"
    pids: int = 128
    output_limit: int = 4000  # truncate overly long output

    def _run(self, code: str) -> str:  # type: ignore[override]
        # Send code inline to the docker.

        cmd = [
            "docker", "run", "--rm",
            "--network", "none", "--read-only",
            "--cpus", self.cpus, "--memory", self.mem,
            "--pids-limit", str(self.pids),
            "--security-opt", "no-new-privileges", "--cap-drop", "ALL",
            "--tmpfs", "/tmp:rw,noexec,nosuid,size=64m",
            self.image, "bash", "-lc", f"python - <<'PYEOF'\n{code}\nPYEOF"
        ]

        try:
            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.timeout_s,
            )
        except subprocess.TimeoutExpired:
            return "Execution timed out."

        out = (proc.stdout or "") + (("\n" + proc.stderr) if proc.stderr else "")
        if len(out) > self.output_limit:
            out = out[: self.output_limit] + "\n... [truncated]"
        if proc.returncode != 0 and not out:
            return f"Process exited with code {proc.returncode} and no output."
        return out.strip() or "(no output)"

    async def _arun(self, code: str) -> str:  # type: ignore[override]
        # Use sync for simplicity; you can add asyncio.to_thread if you prefer.
        return self._run(code)
