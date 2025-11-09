import requests
RESEARCH_URL = "http://localhost:8005"
RISK_URL = "http://localhost:8006"
FINANCE_URL = "http://localhost:8002"

def run_pipeline(topic: str):
    #to bypass the clarifier server, i will be updating this with time
    final_query = topic
    clarifying_questions = "No clarifying questions."
    print(f"Final query: {final_query}")
    research_summary = summarize_research(final_query)
    print(f"Research summary: {research_summary}") 
    research_text = research_summary.get("summary_text", "") + "\n" + "\n".join(research_summary.get("bullets", []))
    if not research_text or research_text == "Research summary unavailable.":
        return "No research summary returned."
    risk_analysis = analyze_risks(research_text)
    print(f"Risk analysis: {risk_analysis}") 
    risks_list = [str(r) for r in risk_analysis.get("risks", ["No risks found."])]
    financial_analysis = financial_insight(research_text, "\n".join(risks_list))
    print(f"Financial analysis: {financial_analysis}") 
    insights_list = [str(i) for i in financial_analysis.get("insights", ["No financial insights available."])]

    report = f"""
# Research Report: {topic}

## Clarifying Questions
{clarifying_questions if clarifying_questions else "No clarifying questions."}

## Research Summary
{research_text}

## Risks
{"".join([f"- {r}\n" for r in risks_list])}

## Financial Insights
{"".join([f"- {i}\n" for i in insights_list])}
"""
    return report

def summarize_research(query: str):
    print(f"Sending to researcher: {query}")
    try:
        resp = requests.post(f"{RESEARCH_URL}/summarize_research", json={"claims_text": query}, timeout=5)
        if resp.status_code == 200:
            return resp.json()
        else:
            print(f"Research server responded with error: {resp.status_code} - {resp.text}")
    except Exception as e:
        print(f"Error during research API call: {e}")
    return {"summary_text": "Research summary unavailable."}

def analyze_risks(research_text: str):
    try:
        resp = requests.post(f"{RISK_URL}/analyze_risks", json={"research_summary_text": research_text}, timeout=5)
        if resp.status_code == 200:
            return resp.json()
    except Exception as e:
        print(f"Error during risk API call: {e}")
    return {"risks": ["Risk analysis unavailable."]}

def financial_insight(research_text: str, risk_text: str):
    try:
        resp = requests.post(
            f"{FINANCE_URL}/financial_insight",
            json={"research_text": research_text, "risk_text": risk_text},
            timeout=5
        )
        if resp.status_code == 200:
            return resp.json()
    except Exception as e:
        print(f"Error during finance API call: {e}")
    return {"insights": ["Financial insights unavailable."]}

if __name__ == "__main__":
    pass
