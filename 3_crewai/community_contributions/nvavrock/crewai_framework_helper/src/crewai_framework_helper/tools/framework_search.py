"""Search the indexed CrewAI framework source and documentation."""

from __future__ import annotations

from typing import Type

from crewai.tools import BaseTool
from pydantic import BaseModel, Field

from rag.retrieve import format_results, search


class FrameworkSearchInput(BaseModel):
    query: str = Field(..., description="What to look for in CrewAI source or docs")
    top_k: int = Field(default=6, description="Number of chunks to return")
    kind: str | None = Field(
        default=None,
        description="Optional filter: source, docs, or meta",
    )


class FrameworkSearchTool(BaseTool):
    name: str = "framework_search"
    description: str = (
        "Search indexed CrewAI framework source code and documentation. "
        "Use before answering any question about CrewAI APIs, agents, tasks, "
        "crews, flows, tools, or knowledge."
    )
    args_schema: Type[BaseModel] = FrameworkSearchInput

    def _run(self, query: str, top_k: int = 6, kind: str | None = None) -> str:
        try:
            return format_results(search(query, top_k=top_k, kind=kind))
        except FileNotFoundError as exc:
            return str(exc)
