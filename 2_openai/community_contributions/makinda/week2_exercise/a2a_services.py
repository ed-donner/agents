"""
Lightweight HTTP wrappers around each specialist agent (local A2A-style distribution).

Run three terminals from the repo root (agents/), after `uv sync`:

  uv run python 2_openai/community_contributions/makinda/week2_exercise/a2a_services.py researcher
  uv run python 2_openai/community_contributions/makinda/week2_exercise/a2a_services.py judge
  uv run python 2_openai/community_contributions/makinda/week2_exercise/a2a_services.py content_builder

Then start the Gradio app with USE_A2A_REMOTE=1.

Agent card URLs mirror the lab naming:
  http://127.0.0.1:8001/a2a/agent/.well-known/agent-card.json
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import uvicorn

# Runnable as a script: ensure sibling imports resolve
_ROOT = Path(__file__).resolve().parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from agents import Runner  # noqa: E402

from agents_specialists import (  # noqa: E402
    content_builder_agent,
    judge_agent,
    researcher_agent,
)
from schemas import JudgeFeedback  # noqa: E402


class InvokeBody(BaseModel):
    input: str = Field(..., description="User message / assembled prompt for the agent.")


def _agent_card(name: str, description: str, port: int) -> dict[str, Any]:
    base = f"http://127.0.0.1:{port}"
    return {
        "name": name,
        "description": description,
        "url": base,
        "preferredTransport": "http+json",
        "capabilities": {"streaming": False},
    }


def build_researcher_app(port: int) -> FastAPI:
    app = FastAPI(title="Researcher A2A stub")

    @app.get("/a2a/agent/.well-known/agent-card.json")
    async def card() -> JSONResponse:
        return JSONResponse(
            _agent_card(
                "researcher",
                "Gathers information using Google Search (Serper).",
                port,
            )
        )

    @app.post("/a2a/invoke")
    async def invoke(body: InvokeBody) -> dict[str, Any]:
        result = await Runner.run(researcher_agent, body.input)
        return {"output": str(result.final_output)}

    return app


def build_judge_app(port: int) -> FastAPI:
    app = FastAPI(title="Judge A2A stub")

    @app.get("/a2a/agent/.well-known/agent-card.json")
    async def card() -> JSONResponse:
        return JSONResponse(
            _agent_card("judge", "Evaluates research for completeness.", port)
        )

    @app.post("/a2a/invoke")
    async def invoke(body: InvokeBody) -> dict[str, Any]:
        result = await Runner.run(judge_agent, body.input)
        fb = result.final_output
        if isinstance(fb, JudgeFeedback):
            return {"output": fb.model_dump()}
        if isinstance(fb, dict):
            return {"output": fb}
        return {"output": JudgeFeedback.model_validate_json(str(fb)).model_dump()}

    return app


def build_content_builder_app(port: int) -> FastAPI:
    app = FastAPI(title="Content Builder A2A stub")

    @app.get("/a2a/agent/.well-known/agent-card.json")
    async def card() -> JSONResponse:
        return JSONResponse(
            _agent_card(
                "content_builder",
                "Builds a Markdown course from approved research.",
                port,
            )
        )

    @app.post("/a2a/invoke")
    async def invoke(body: InvokeBody) -> dict[str, Any]:
        result = await Runner.run(content_builder_agent, body.input)
        return {"output": str(result.final_output)}

    return app


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "role",
        choices=("researcher", "judge", "content_builder"),
        help="Which specialist service to run.",
    )
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=None)
    args = parser.parse_args()

    default_ports = {
        "researcher": 8001,
        "judge": 8002,
        "content_builder": 8003,
    }
    port = args.port or default_ports[args.role]

    builders = {
        "researcher": build_researcher_app,
        "judge": build_judge_app,
        "content_builder": build_content_builder_app,
    }
    app = builders[args.role](port)
    uvicorn.run(app, host=args.host, port=port, log_level="info")


if __name__ == "__main__":
    main()
