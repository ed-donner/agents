from pathlib import Path
from typing import Type

from pydantic import BaseModel, Field

from crewai.tools import BaseTool

from flow_engineering_team.sandbox import SANDBOX_ROOT, ensure_sandbox_tree


class SandboxWriteInput(BaseModel):
    """Input schema for writing a file into sandbox."""

    relative_path: str = Field(..., description="Path inside sandbox to write.")
    content: str = Field(..., description="Full file content.")


class SandboxReadInput(BaseModel):
    """Input schema for reading a file from sandbox."""

    relative_path: str = Field(..., description="Path inside sandbox to read.")


class SandboxListInput(BaseModel):
    """Input schema for listing sandbox contents."""

    relative_path: str = Field(".", description="Directory inside sandbox to list.")


def _resolve_sandbox_path(relative_path: str) -> Path:
    ensure_sandbox_tree()
    root_path = SANDBOX_ROOT.resolve()
    target_path = (root_path / relative_path).resolve()

    if target_path != root_path and root_path not in target_path.parents:
        raise ValueError(f"Path escapes sandbox: {relative_path}")

    target_path.parent.mkdir(parents=True, exist_ok=True)
    return target_path


class WriteSandboxFileTool(BaseTool):
    name: str = "write_sandbox_file"
    description: str = "Write a file into the shared sandbox workspace."
    args_schema: Type[BaseModel] = SandboxWriteInput

    def _run(self, relative_path: str, content: str) -> str:
        target_path = _resolve_sandbox_path(relative_path)
        target_path.write_text(content, encoding="utf-8")
        return f"Wrote {target_path.as_posix()}"


class ReadSandboxFileTool(BaseTool):
    name: str = "read_sandbox_file"
    description: str = "Read a file from the shared sandbox workspace."
    args_schema: Type[BaseModel] = SandboxReadInput

    def _run(self, relative_path: str) -> str:
        target_path = _resolve_sandbox_path(relative_path)
        return target_path.read_text(encoding="utf-8")


class ListSandboxFilesTool(BaseTool):
    name: str = "list_sandbox_files"
    description: str = "List files available in the shared sandbox workspace."
    args_schema: Type[BaseModel] = SandboxListInput

    def _run(self, relative_path: str = ".") -> str:
        target_path = _resolve_sandbox_path(relative_path)

        if not target_path.exists():
            return ""

        if target_path.is_file():
            return target_path.name

        return "\n".join(sorted(child.name for child in target_path.iterdir()))


sandbox_tools = [
    WriteSandboxFileTool(),
    ReadSandboxFileTool(),
    ListSandboxFilesTool(),
]
