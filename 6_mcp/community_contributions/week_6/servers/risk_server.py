from fastapi import FastAPI
from pydantic import BaseModel
from datetime import datetime
import requests

LLM_URL = "http://localhost:8003/complete"
app = FastAPI()

class AnalyzeRisksRequest(BaseModel):
    research_summary_text: str
    final_query: str | None = None

class AnalyzeRisksResponse(BaseModel):
    generated_at: str
    risks: list

@app.post("/analyze_risks", response_model=AnalyzeRisksResponse)
def analyze_risks(request: AnalyzeRisksRequest):
    system = "You are a risk analyst. From the provided research summary produce 6 concise risks and a short likelihood/impact note for each."
    
    prompt = f"Final query: {request.final_query}\n\nResearch summary:\n{request.research_summary_text}\n\nReturn up to 6 risks in this format: - Risk: <one-line> | Likelihood: <low/med/high> | Impact: <low/med/high>"
    
    resp = requests.post(LLM_URL, json={"system": system, "prompt": prompt})
    if resp.status_code != 200:
        return AnalyzeRisksResponse(generated_at=datetime.utcnow().isoformat(), risks=[])
    
    content = resp.json().get("response", "")
    lines = [l.strip("- ").strip() for l in content.split("\n") if l.strip()]
    
    return AnalyzeRisksResponse(generated_at=datetime.utcnow().isoformat(), risks=lines[:6])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8006)
