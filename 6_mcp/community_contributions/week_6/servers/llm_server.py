import asyncio
from fastapi import FastAPI
from pydantic import BaseModel
from typing import Any
from config import client, MODEL, MAX_TOKENS, TEMPERATURE  # Keep your LLM client settings here

app = FastAPI()
class CompleteRequest(BaseModel):
    system: str
    prompt: str
    max_tokens: int = MAX_TOKENS
    temperature: float = TEMPERATURE
class CompleteResponse(BaseModel):
    response: str
async def call_llm(system: str, prompt: str, max_tokens: int, temperature: float) -> str:
    try:
        maybe_awaitable = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "system", "content": system}, {"role": "user", "content": prompt}],
            max_tokens=max_tokens,
            temperature=temperature,
        )
        if asyncio.iscoroutine(maybe_awaitable):
            response = await maybe_awaitable
        else:
            response = maybe_awaitable
    except Exception as e:
        try:
            response = client.chat.completions.create(
                model=MODEL,
                messages=[{"role": "system", "content": system}, {"role": "user", "content": prompt}],
                max_tokens=max_tokens,
                temperature=temperature,
            )
        except Exception as e2:
            return f"LLM client error: {e2}"
    
    try:
        content = response.choices[0].message.content
    except Exception:
        try:
            content = getattr(response, "text", str(response))
        except Exception:
            content = str(response)
    if isinstance(content, list):
        content = "".join([c.get("text", "") if isinstance(c, dict) else str(c) for c in content])
    return content.strip()

@app.post("/complete", response_model=CompleteResponse)
async def complete(request: CompleteRequest):
    out = await call_llm(request.system, request.prompt, request.max_tokens, request.temperature)
    return CompleteResponse(response=out)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)
