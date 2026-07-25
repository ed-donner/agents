from __future__ import annotations

from importlib import metadata
from pathlib import Path


distribution = metadata.distribution("openai-agents")
sdk_dir = Path(distribution.locate_file("")) / "agents"

if str(sdk_dir) not in __path__:
    __path__.append(str(sdk_dir))

from .agent import Agent  # type: ignore[attr-defined]
from .model_settings import ModelSettings  # type: ignore[attr-defined]
from .run import Runner  # type: ignore[attr-defined]
from .tool import WebSearchTool  # type: ignore[attr-defined]
from .tracing import gen_trace_id, trace  # type: ignore[attr-defined]

__all__ = [
    "Agent",
    "ModelSettings",
    "Runner",
    "WebSearchTool",
    "gen_trace_id",
    "trace",
]
