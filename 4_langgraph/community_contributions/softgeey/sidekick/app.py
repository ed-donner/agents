"""
SideKick FastAPI application.
Serves the web UI and exposes the /chat endpoint.
"""

import logging
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from langchain_core.messages import HumanMessage

from config import config
from graph import sidekick_graph
from agents.state import AgentState

logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(name)s  %(message)s")
logger = logging.getLogger(__name__)

app = FastAPI(title="SideKick", version="1.0.0")
app.mount("/static", StaticFiles(directory="ui/static"), name="static")
templates = Jinja2Templates(directory="ui/templates")

# In-memory conversation history (single-user, resets on server restart)
_conversation: list = []


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    response: str
    intent: str


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/chat", response_model=ChatResponse)
async def chat(body: ChatRequest):
    global _conversation

    user_message = body.message.strip()
    if not user_message:
        return JSONResponse(status_code=400, content={"detail": "Message cannot be empty."})

    _conversation.append(HumanMessage(content=user_message))

    state = AgentState(messages=_conversation)

    try:
        result = sidekick_graph.invoke(state)
    except Exception as e:
        logger.error("Graph invocation error: %s", e)
        return JSONResponse(
            status_code=500,
            content={"detail": f"Agent error: {str(e)}"},
        )

    # Persist updated messages for next turn
    _conversation = list(result["messages"])

    return ChatResponse(
        response=result.get("response", ""),
        intent=result.get("intent", "general"),
    )


@app.post("/reset")
async def reset_conversation():
    """Clear conversation history."""
    global _conversation
    _conversation = []
    return {"status": "ok"}


@app.get("/health")
async def health():
    return {"status": "ok", "model": config.MODEL}
