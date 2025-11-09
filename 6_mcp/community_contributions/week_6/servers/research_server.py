# from mcp.server.fastmcp import FastMCP
# from datetime import datetime
# import json

# mcp = FastMCP("research_server")

# @mcp.tool()
# def summarize_research(claims_text: str) -> dict:
#     # For now we simply wrap into structure; orchestrator should call llm_server then pass its text here.
#     summary = {
#         "generated_at": datetime.utcnow().isoformat(),
#         "summary_text": claims_text,
#         "bullets": [line.strip() for line in claims_text.split("\n") if line.strip()][:5],
#     }
#     return summary

# if __name__ == "__main__":
#     mcp.run(transport="stdio")


from fastapi import FastAPI
from pydantic import BaseModel
from datetime import datetime
import requests

LLM_URL = "http://localhost:8003/complete"
app = FastAPI()

class SummarizeResearchRequest(BaseModel):
    claims_text: str
    final_query: str | None = None

class SummarizeResearchResponse(BaseModel):
    generated_at: str
    summary_text: str
    bullets: list

@app.post("/summarize_research", response_model=SummarizeResearchResponse)
def summarize_research(request: SummarizeResearchRequest):
    system = "You are a research assistant that produces concise evidence-backed summaries and bullet points for a given business claim or topic."
    
    prompt = f"Final query: {request.final_query}\n\nClaims / raw text:\n{request.claims_text}\n\nReturn a short summary (2-4 sentences) and 6 supporting bullets (each short)."
    
    resp = requests.post(LLM_URL, json={"system": system, "prompt": prompt})
    if resp.status_code != 200:
        return {"generated_at": datetime.utcnow().isoformat(), "summary_text": "LLM error", "bullets": []}
    
    text = resp.json().get("response", "")
    lines = [l.strip() for l in text.split("\n") if l.strip()]
    summary = lines[0] if lines else text
    bullets = [l for l in lines[1:7]] if len(lines) > 1 else []
    
    return SummarizeResearchResponse(generated_at=datetime.utcnow().isoformat(), summary_text=summary, bullets=bullets)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8005)
