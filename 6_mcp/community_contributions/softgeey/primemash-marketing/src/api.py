"""
FastAPI backend for Primemash Marketing Agent System.
Provides REST API consumed by the Next.js dashboard.
"""

import os
import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from jose import JWTError, jwt
from dotenv import load_dotenv

from src.agents.marketing_team import run_agent_task
from src.lib.scheduler import start_scheduler, stop_scheduler
from src.lib.database import (
    get_recent_posts,
    get_campaigns,
    get_analytics_summary,
    save_post,
    update_post_status,
)

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

API_SECRET_KEY = os.environ.get("API_SECRET_KEY", "change-me")
ALGORITHM = "HS256"
security = HTTPBearer()


# ── App lifecycle ─────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    start_scheduler()
    logger.info("🚀 Primemash Marketing API started")
    yield
    stop_scheduler()
    logger.info("API shutting down")


app = FastAPI(
    title="Primemash Marketing API",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", os.environ.get("NEXTAUTH_URL", "")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Auth ──────────────────────────────────────────────────────────────────────

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """Verify JWT token issued by Next.js / NextAuth."""
    try:
        payload = jwt.decode(
            credentials.credentials,
            API_SECRET_KEY,
            algorithms=[ALGORITHM],
            options={"verify_exp": False},  # NextAuth tokens may not have exp
        )
        return payload
    except JWTError as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {e}")


# ── Request / Response models ─────────────────────────────────────────────────

class AgentTaskRequest(BaseModel):
    task: str
    context: Optional[dict] = None


class CreatePostRequest(BaseModel):
    platform: str
    content: str
    content_type: str
    status: str = "draft"
    campaign_id: Optional[str] = None


class CampaignRequest(BaseModel):
    name: str
    objective: str
    platforms: list[str]
    duration_days: int


class GenerateContentRequest(BaseModel):
    platform: str          # linkedin | twitter | instagram
    content_type: str
    topic: Optional[str] = None


# ── Routes ────────────────────────────────────────────────────────────────────


@app.get("/ping")
async def ping():
    """No-auth connectivity test."""
    return {"status": "ok", "service": "Primemash API"}


@app.post("/api/agent/test")
async def agent_test(_: dict = Depends(verify_token)):
    """Quick agent test - just returns today's theme, no LLM call."""
    from datetime import datetime
    from src.lib.brand_context import CONTENT_CALENDAR
    day = datetime.now().strftime("%A").lower()
    theme = CONTENT_CALENDAR.get(day, "educational")
    return {"status": "ok", "day": day, "theme": theme}


@app.post("/api/agent/llm-test")
async def llm_test(_: dict = Depends(verify_token)):
    """Test OpenRouter LLM connectivity directly."""
    import asyncio
    from openai import AsyncOpenAI
    import os
    client = AsyncOpenAI(
        api_key=os.environ.get("OPENROUTER_API_KEY", ""),
        base_url=os.environ.get("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"),
    )
    try:
        response = await asyncio.wait_for(
            client.chat.completions.create(
                model=os.environ.get("OPENROUTER_MODEL", "anthropic/claude-3.5-sonnet"),
                messages=[{"role": "user", "content": "Reply with just: ok"}],
                max_tokens=5,
            ),
            timeout=15.0,
        )
        reply = response.choices[0].message.content
        return {"status": "ok", "llm_reply": reply}
    except asyncio.TimeoutError:
        raise HTTPException(status_code=504, detail="OpenRouter timed out after 15 seconds")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OpenRouter error: {e}")

@app.get("/health")
async def health():
    return {"status": "ok", "service": "Primemash Marketing API"}


# Agent endpoint
@app.post("/api/agent/run")
async def run_agent(
    request: AgentTaskRequest,
    background_tasks: BackgroundTasks,
    _: dict = Depends(verify_token),
):
    """Run any task through the marketing agent team."""
    logger.info(f"Agent task received: {request.task[:80]}")
    try:
        result = await asyncio.wait_for(
            run_agent_task(request.task, request.context),
            timeout=90.0,
        )
        logger.info("Agent task completed successfully")
        return {"success": True, "result": result}
    except asyncio.TimeoutError:
        raise HTTPException(status_code=504, detail="Agent timed out after 90 seconds. Try a simpler task.")
    except Exception as e:
        logger.error(f"Agent task failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/agent/daily-run")
async def trigger_daily_run(
    background_tasks: BackgroundTasks,
    _: dict = Depends(verify_token),
):
    """Manually trigger the daily content creation and publishing cycle."""
    async def _run():
        await run_agent_task(
            "Generate and publish today's content for LinkedIn and Twitter. "
            "One post per platform. Use today's content theme. Skip Instagram — it is disabled."
        )

    background_tasks.add_task(_run)
    return {"success": True, "message": "Daily run triggered in background"}


# Posts
@app.get("/api/posts")
async def list_posts(limit: int = 20, _: dict = Depends(verify_token)):
    posts = get_recent_posts(limit)
    return {"posts": posts}


@app.post("/api/posts")
async def create_post(request: CreatePostRequest, _: dict = Depends(verify_token)):
    try:
        post = save_post(
            platform=request.platform,
            content=request.content,
            content_type=request.content_type,
            status=request.status,
            campaign_id=request.campaign_id,
        )
        return {"success": True, "post": post}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.patch("/api/posts/{post_id}/status")
async def patch_post_status(
    post_id: str,
    body: dict,
    _: dict = Depends(verify_token),
):
    status = body.get("status")
    if not status:
        raise HTTPException(status_code=400, detail="status field required")
    post = update_post_status(post_id, status)
    return {"success": True, "post": post}


# Content generation (single post, no publish)
@app.post("/api/content/generate")
async def generate_content(request: GenerateContentRequest, _: dict = Depends(verify_token)):
    """Generate content for a platform without publishing."""
    try:
        result = await run_agent_task(
            f"Generate a {request.content_type} post for {request.platform}. "
            f"Topic: {request.topic or 'choose the best topic for today'}. "
            f"Save it to the database as a draft. Return the content and post_id."
        )
        logger.info("Agent task completed successfully")
        return {"success": True, "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Campaigns
@app.get("/api/campaigns")
async def list_campaigns(_: dict = Depends(verify_token)):
    campaigns = get_campaigns()
    return {"campaigns": campaigns}


@app.post("/api/campaigns")
async def create_campaign_endpoint(
    request: CampaignRequest,
    _: dict = Depends(verify_token),
):
    """Create a campaign and generate its full content plan."""
    try:
        platforms_str = ",".join(request.platforms)
        result = await run_agent_task(
            f"Create a marketing campaign called '{request.name}'. "
            f"Objective: {request.objective}. "
            f"Platforms: {platforms_str}. "
            f"Duration: {request.duration_days} days. "
            f"Generate the full content calendar plan."
        )
        logger.info("Agent task completed successfully")
        return {"success": True, "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Analytics
@app.get("/api/analytics")
async def analytics(_: dict = Depends(verify_token)):
    try:
        summary = get_analytics_summary()
        return {"success": True, "analytics": summary}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/analytics/report")
async def analytics_report(_: dict = Depends(verify_token)):
    """Run agent analytics report."""
    try:
        result = await run_agent_task(
            "Generate a detailed analytics report with performance insights "
            "and 3 actionable recommendations for improving our social media strategy."
        )
        return {"success": True, "report": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
