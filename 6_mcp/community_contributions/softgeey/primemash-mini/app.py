"""
Primemash Mini — Autonomous LinkedIn Marketing Agent
Single-file demo. Posts AI-generated content to LinkedIn via Make.com webhook.

Stack: FastAPI · OpenAI Agents SDK · OpenRouter · Vanilla HTML/JS UI
Run:   uv run python app.py
Open:  http://localhost:8000
"""

import os
import json
import asyncio
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
from dotenv import load_dotenv
from openai import AsyncOpenAI, OpenAI
from agents import Agent, Runner, function_tool, set_tracing_disabled
from agents.models.openai_chatcompletions import OpenAIChatCompletionsModel

load_dotenv()
set_tracing_disabled(True)

# ── Config ────────────────────────────────────────────────────────────────────

BRAND = """
Primemash Technologies — "Automating African Businesses, Amplifying Growth"
Website: primemash.ng | Based in Lagos, Nigeria
Services: Business automation for Nigerian SMEs — WhatsApp, CRM, invoicing, HR
Target: Lagos/Abuja entrepreneurs, 5-100 staff, ₦500K-₦50M monthly revenue
Tone: Sharp Lagos entrepreneur voice. Specific Naira figures. Real Nigerian pain points.
Always include: #primemashtech in every post.
"""

CONTENT_THEMES = {
    "monday": "motivation_and_tips",
    "tuesday": "case_study",
    "wednesday": "educational",
    "thursday": "thought_leadership",
    "friday": "social_proof",
    "saturday": "behind_scenes",
    "sunday": "engagement",
}


# ── LLM client ────────────────────────────────────────────────────────────────

def get_model() -> OpenAIChatCompletionsModel:
    client = AsyncOpenAI(
        api_key=os.environ.get("OPENROUTER_API_KEY", ""),
        base_url="https://openrouter.ai/api/v1",
        default_headers={"HTTP-Referer": "https://primemash.ng", "X-Title": "Primemash Mini"},
    )
    return OpenAIChatCompletionsModel(
        model=os.environ.get("OPENROUTER_MODEL", "anthropic/claude-3.5-sonnet"),
        openai_client=client,
    )


def llm_call(prompt: str) -> str:
    """Synchronous LLM call via OpenRouter for content generation."""
    client = OpenAI(
        api_key=os.environ.get("OPENROUTER_API_KEY", ""),
        base_url="https://openrouter.ai/api/v1",
        default_headers={"HTTP-Referer": "https://primemash.ng"},
    )
    r = client.chat.completions.create(
        model=os.environ.get("OPENROUTER_MODEL", "anthropic/claude-3.5-sonnet"),
        temperature=0.85,
        messages=[{"role": "user", "content": prompt}],
    )
    return r.choices[0].message.content.strip()


# ── Agent tools ───────────────────────────────────────────────────────────────

@function_tool
def get_todays_theme() -> str:
    """Get today's recommended content theme."""
    day = datetime.now().strftime("%A").lower()
    return json.dumps({"day": day, "theme": CONTENT_THEMES.get(day, "educational")})


@function_tool
def write_linkedin_post(content_type: str, topic: str) -> str:
    """Write a high-quality LinkedIn post for Primemash Technologies."""
    prompt = f"""You are writing a LinkedIn post for Primemash Technologies.

{BRAND}

Content type: {content_type}
Topic: {topic}

Rules:
- Write like a sharp Lagos entrepreneur, not a marketing team
- Include at least one specific Naira figure or time metric
- Reference a real Nigerian business scenario
- Max 1,300 characters
- End with 3-5 hashtags including #primemashtech
- Return ONLY the post text"""
    content = llm_call(prompt)
    return json.dumps({"content": content, "content_type": content_type})


@function_tool
def publish_to_linkedin(content: str) -> str:
    """Publish a post to LinkedIn via Make.com webhook."""
    webhook_url = os.environ.get("MAKE_LINKEDIN_WEBHOOK_URL", "")
    if not webhook_url:
        return json.dumps({"success": False, "error": "MAKE_LINKEDIN_WEBHOOK_URL not set in .env"})
    try:
        r = httpx.post(webhook_url, json={"body": content}, timeout=15)
        if r.status_code in (200, 204):
            return json.dumps({"success": True, "message": "Post published to LinkedIn"})
        return json.dumps({"success": False, "error": f"Webhook {r.status_code}: {r.text}"})
    except Exception as e:
        return json.dumps({"success": False, "error": str(e)})


# ── Agent ─────────────────────────────────────────────────────────────────────

INSTRUCTIONS = f"""You are the autonomous LinkedIn marketing agent for Primemash Technologies.

{BRAND}

You have three tools:
- get_todays_theme   → get today's content theme
- write_linkedin_post → generate the post text
- publish_to_linkedin → publish to LinkedIn via Make.com

RULES — no exceptions:
1. NEVER ask questions. Execute immediately.
2. For any post request: get_todays_theme → write_linkedin_post → publish_to_linkedin → report result.
3. Call publish_to_linkedin EXACTLY ONCE. Never retry.
4. Report only after all tools have run. One final summary."""


def run_agent_sync(task: str) -> str:
    """Run the agent in a fresh event loop (thread-safe with FastAPI)."""
    agent = Agent(
        name="PrimemashMiniAgent",
        model=get_model(),
        instructions=INSTRUCTIONS,
        tools=[get_todays_theme, write_linkedin_post, publish_to_linkedin],
    )
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        result = loop.run_until_complete(Runner.run(agent, task, max_turns=10))
        return result.final_output
    finally:
        loop.close()


async def run_agent(task: str) -> str:
    loop = asyncio.get_event_loop()
    with ThreadPoolExecutor(max_workers=1) as ex:
        return await loop.run_in_executor(ex, run_agent_sync, task)


# ── FastAPI ───────────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    yield

app = FastAPI(title="Primemash Mini", lifespan=lifespan)


class TaskRequest(BaseModel):
    task: str


@app.get("/health")
async def health():
    return {"status": "ok", "service": "Primemash Mini"}


@app.post("/post")
async def create_post(req: TaskRequest):
    """Run the marketing agent on a task."""
    try:
        result = await asyncio.wait_for(run_agent(req.task), timeout=90.0)
        return JSONResponse({"success": True, "result": result})
    except asyncio.TimeoutError:
        return JSONResponse({"success": False, "error": "Agent timed out."}, status_code=504)
    except Exception as e:
        return JSONResponse({"success": False, "error": str(e)}, status_code=500)


@app.get("/", response_class=HTMLResponse)
async def ui():
    """Minimal single-page UI."""
    return HTMLResponse("""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Primemash Mini</title>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: system-ui, sans-serif; background: #f8f9fa; color: #1a1a1a; min-height: 100vh; }
  .header { background: #0369a1; color: white; padding: 16px 24px; display: flex; align-items: center; gap: 12px; }
  .logo { width: 32px; height: 32px; background: white; border-radius: 8px; display: flex; align-items: center; justify-content: center; color: #0369a1; font-weight: 700; font-size: 16px; }
  .header h1 { font-size: 18px; font-weight: 600; }
  .header p { font-size: 13px; opacity: 0.8; }
  .container { max-width: 680px; margin: 32px auto; padding: 0 16px; }
  .card { background: white; border: 1px solid #e5e7eb; border-radius: 12px; padding: 24px; margin-bottom: 16px; }
  label { display: block; font-size: 13px; font-weight: 500; color: #374151; margin-bottom: 6px; }
  textarea { width: 100%; border: 1px solid #d1d5db; border-radius: 8px; padding: 10px 12px; font-size: 14px; font-family: inherit; resize: vertical; min-height: 80px; outline: none; }
  textarea:focus { border-color: #0369a1; box-shadow: 0 0 0 3px #bfdbfe; }
  .quick-btns { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 10px; }
  .quick-btn { background: #f0f9ff; border: 1px solid #bae6fd; color: #0369a1; border-radius: 20px; padding: 4px 12px; font-size: 12px; cursor: pointer; }
  .quick-btn:hover { background: #e0f2fe; }
  .btn { background: #0369a1; color: white; border: none; border-radius: 8px; padding: 10px 20px; font-size: 14px; font-weight: 500; cursor: pointer; width: 100%; margin-top: 12px; }
  .btn:hover { background: #0284c7; }
  .btn:disabled { opacity: 0.6; cursor: not-allowed; }
  .result { background: #f0fdf4; border: 1px solid #bbf7d0; border-radius: 8px; padding: 16px; font-size: 13px; line-height: 1.6; white-space: pre-wrap; margin-top: 16px; }
  .error { background: #fef2f2; border-color: #fecaca; color: #991b1b; }
  .spinner { display: inline-block; width: 14px; height: 14px; border: 2px solid #ffffff55; border-top-color: white; border-radius: 50%; animation: spin 0.7s linear infinite; margin-right: 6px; vertical-align: middle; }
  @keyframes spin { to { transform: rotate(360deg); } }
  .status { font-size: 12px; color: #6b7280; margin-top: 8px; }
</style>
</head>
<body>
<div class="header">
  <div class="logo">P</div>
  <div>
    <h1>Primemash Mini</h1>
    <p>Autonomous LinkedIn Marketing Agent</p>
  </div>
</div>

<div class="container">
  <div class="card">
    <label>Give the agent a task</label>
    <textarea id="task" placeholder="e.g. Post today's content to LinkedIn"></textarea>
    <div class="quick-btns">
      <button class="quick-btn" onclick="setTask('Post today\\'s content to LinkedIn')">Post today's content</button>
      <button class="quick-btn" onclick="setTask('Write and post a LinkedIn tip about WhatsApp automation for Lagos retailers')">WhatsApp automation tip</button>
      <button class="quick-btn" onclick="setTask('Post a LinkedIn case study about a Nigerian e-commerce business that saved ₦500K/month with automation')">Case study post</button>
      <button class="quick-btn" onclick="setTask('Post a thought leadership piece about the future of automation for African SMEs')">Thought leadership</button>
    </div>
    <button class="btn" id="run-btn" onclick="runTask()">Run Agent</button>
    <p class="status" id="status"></p>
  </div>

  <div id="result-box" style="display:none"></div>
</div>

<script>
function setTask(t) { document.getElementById('task').value = t; }

async function runTask() {
  const task = document.getElementById('task').value.trim();
  if (!task) return;

  const btn = document.getElementById('run-btn');
  const status = document.getElementById('status');
  const resultBox = document.getElementById('result-box');

  btn.disabled = true;
  btn.innerHTML = '<span class="spinner"></span>Agent working…';
  status.textContent = 'Generating content and publishing to LinkedIn…';
  resultBox.style.display = 'none';

  try {
    const res = await fetch('/post', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ task }),
    });
    const data = await res.json();
    resultBox.style.display = 'block';
    if (data.success) {
      resultBox.innerHTML = '<div class="result">' + escHtml(data.result) + '</div>';
      status.textContent = 'Done.';
    } else {
      resultBox.innerHTML = '<div class="result error">Error: ' + escHtml(data.error) + '</div>';
      status.textContent = 'Failed.';
    }
  } catch (e) {
    resultBox.style.display = 'block';
    resultBox.innerHTML = '<div class="result error">Network error: ' + e.message + '</div>';
    status.textContent = 'Failed.';
  } finally {
    btn.disabled = false;
    btn.textContent = 'Run Agent';
  }
}

function escHtml(s) {
  return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
}
</script>
</body>
</html>""")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
