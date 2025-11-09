from fastapi import FastAPI
from pydantic import BaseModel
from datetime import datetime
import requests

LLM_URL = "http://localhost:8003/complete"
app = FastAPI()

class FinancialInsightRequest(BaseModel):
    research_text: str
    risk_text: str
    final_query: str | None = None

class FinancialInsightResponse(BaseModel):
    generated_at: str
    insights: list
    raw_research_excerpt: str
    raw_risk_excerpt: str

@app.post("/financial_insight", response_model=FinancialInsightResponse)
def financial_insight(request: FinancialInsightRequest):
    system = "You are a financial analyst. Based on research text and risk text, produce: (1) top 5 insights, (2) 3 suggested KPI metrics, (3) rough cost drivers."
    prompt = f"Final query: {request.final_query}\n\nResearch:\n{request.research_text}\n\nRisks:\n{request.risk_text}\n\nReturn JSON-like bullet points for insights, KPIs, and cost drivers."
    resp = requests.post(LLM_URL, json={"system": system, "prompt": prompt})
    if resp.status_code != 200:
        return FinancialInsightResponse(generated_at=datetime.utcnow().isoformat(), insights=["LLM error"], raw_research_excerpt=request.research_text[:500], raw_risk_excerpt=request.risk_text[:500])
    content = resp.json().get("response", "")
    lines = [l.strip() for l in content.split("\n") if l.strip()]
    return FinancialInsightResponse(generated_at=datetime.utcnow().isoformat(), insights=lines[:8], raw_research_excerpt=request.research_text[:500], raw_risk_excerpt=request.risk_text[:500])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
