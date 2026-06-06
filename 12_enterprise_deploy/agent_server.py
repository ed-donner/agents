"""
FastAPI-wrapped agent server — the deployable unit.
Run locally: uvicorn agent_server:app --reload
Deploy to any cloud via Dockerfile.
"""

import os
from fastapi import FastAPI, HTTPException, Header
from pydantic import BaseModel
from dotenv import load_dotenv
from openai import OpenAI
from middleware import BudgetMiddleware, PIIScrubber, AuditLogger
from circuit_breaker import CircuitBreaker, CircuitBreakerError

load_dotenv(override=True)

app = FastAPI(title="Enterprise Agent API", version="1.0.0")
raw_client = OpenAI()


# ---------------------------------------------------------------------------
# Base agent
# ---------------------------------------------------------------------------

def _base_agent(prompt: str, **kwargs) -> str:
    resp = raw_client.chat.completions.create(
        model=os.getenv("AGENT_MODEL", "gpt-4o-mini"),
        messages=[
            {"role": "system", "content": "You are a helpful assistant. Be concise."},
            {"role": "user", "content": prompt},
        ],
        max_tokens=500,
    )
    return resp.choices[0].message.content


# ---------------------------------------------------------------------------
# Middleware stack
# ---------------------------------------------------------------------------

_protected = CircuitBreaker(
    fn=_base_agent,
    failure_threshold=5,
    recovery_timeout=60.0,
    fallback=lambda prompt, **kw: "Service temporarily unavailable. Please try again shortly.",
)

_agent = AuditLogger(
    PIIScrubber(
        BudgetMiddleware(
            _protected,
            global_budget_usd=float(os.getenv("GLOBAL_BUDGET_USD", "50.0")),
            per_user_budget_usd=float(os.getenv("PER_USER_BUDGET_USD", "2.0")),
        )
    ),
    log_file=os.getenv("AUDIT_LOG_FILE", "audit.jsonl"),
)


# ---------------------------------------------------------------------------
# API
# ---------------------------------------------------------------------------

class ChatRequest(BaseModel):
    message: str
    user_id: str = "anonymous"

class ChatResponse(BaseModel):
    response: str
    user_id: str

class HealthResponse(BaseModel):
    status: str
    circuit_breaker: str
    audit_entries: int

class BudgetResponse(BaseModel):
    global_spent_usd: float
    global_budget_usd: float
    global_remaining_usd: float
    users: dict


@app.get("/health", response_model=HealthResponse)
def health():
    return HealthResponse(
        status="ok",
        circuit_breaker=_protected.state.value,
        audit_entries=len(_agent.get_log()),
    )


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest, x_api_key: str = Header(default="")):
    # Simple API key check (in production use OAuth2 / JWT)
    expected_key = os.getenv("API_KEY", "")
    if expected_key and x_api_key != expected_key:
        raise HTTPException(status_code=401, detail="Invalid API key")

    try:
        response = _agent(request.message, user_id=request.user_id)
        return ChatResponse(response=response, user_id=request.user_id)
    except CircuitBreakerError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        if "budget" in str(e).lower():
            raise HTTPException(status_code=429, detail=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/admin/budget", response_model=BudgetResponse)
def budget_report(x_api_key: str = Header(default="")):
    if x_api_key != os.getenv("ADMIN_KEY", "admin"):
        raise HTTPException(status_code=401, detail="Admin key required")
    # Navigate the middleware stack to find BudgetMiddleware
    budget_mw = _agent.agent_fn.agent_fn  # AuditLogger → PIIScrubber → BudgetMiddleware
    report = budget_mw.spending_report()
    return BudgetResponse(**report)


@app.get("/admin/audit")
def audit_log(limit: int = 50, x_api_key: str = Header(default="")):
    if x_api_key != os.getenv("ADMIN_KEY", "admin"):
        raise HTTPException(status_code=401, detail="Admin key required")
    entries = _agent.get_log()[-limit:]
    return {
        "total": len(_agent.get_log()),
        "entries": [
            {
                "id": e.entry_id[:8],
                "timestamp": e.timestamp,
                "user_id": e.user_id,
                "prompt_hash": e.prompt_hash,
                "latency": round(e.latency_seconds, 3),
                "error": e.error or None,
            }
            for e in entries
        ],
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
