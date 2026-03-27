"""
main.py — FastAPI server for the Deep Research web app.

Run with:
    uvicorn main:app --reload --port 8000

Endpoints:
    GET  /           → health check
    POST /research   → starts research, streams SSE events back
"""
import asyncio
import json
import sys
import os

# Ensure the module directory is on the path when running from a subprocess
sys.path.insert(0, os.path.dirname(__file__))

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from deep_research import setup_client
from research_manager import run_deep_research


# ── Startup ───────────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_client()  # Register OpenRouter as the default LLM client
    yield


app = FastAPI(title="Deep Research API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",   # Vite dev server
        "http://localhost:4173",   # Vite preview
        "http://127.0.0.1:5173",
    ],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Request schema ────────────────────────────────────────────────────────────

class ResearchRequest(BaseModel):
    query: str
    email: str


# ── Routes ────────────────────────────────────────────────────────────────────

@app.get("/")
def health():
    return {"status": "Deep Research API is running ✓"}


@app.post("/research")
async def research(req: ResearchRequest):
    """
    Accepts a query + email, runs the full research pipeline,
    and streams progress as Server-Sent Events (SSE).

    SSE event format:
        data: {"event": "<name>", "data": { ... }}\n\n

    Events emitted:
        planning  → planner agent is deciding search queries
        planned   → N queries decided
        searching → parallel web searches started
        searched  → all searches done
        writing   → writer agent is synthesising
        written   → report ready
        emailing  → email agent sending
        emailed   → email delivered
        done      → final report payload (short_summary, markdown_report, follow_up_questions)
        error     → something went wrong
    """

    async def event_stream():
        queue: asyncio.Queue[str | None] = asyncio.Queue()

        async def progress(event: str, data: dict):
            payload = json.dumps({"event": event, "data": data})
            await queue.put(f"data: {payload}\n\n")

        async def run():
            try:
                await run_deep_research(req.query, req.email, progress)
            except Exception as exc:
                err = json.dumps({"event": "error", "data": {"message": str(exc)}})
                await queue.put(f"data: {err}\n\n")
            finally:
                await queue.put(None)  # signal end of stream

        asyncio.create_task(run())

        while True:
            msg = await queue.get()
            if msg is None:
                break
            yield msg

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",   # Disable Nginx buffering if behind a proxy
        },
    )
