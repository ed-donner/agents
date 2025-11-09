# from mcp.server.fastmcp import FastMCP
# from datetime import datetime
# import sys

# mcp = FastMCP("clarifier_server")

# # Tools

# @mcp.tool()
# def start_session(user_input: str) -> dict:
#     print(f"[clarifier_server] start_session registered with user_input={user_input!r}", flush=True)
#     return {
#         "created_at": datetime.utcnow().isoformat(),
#         "round": 1,
#         "history": [{"user": user_input}],
#         "final_query": None,
#     }

# @mcp.tool()
# def update_state(state: dict | None, clarifier_msg: str, user_response: str | None = None) -> dict:
#     print(
#         f"[clarifier_server] update_state registered (round before update: {state.get('round') if state else 'unknown'})",
#         flush=True,
#     )
#     state = state or {"history": [], "round": 1}
#     if clarifier_msg:
#         state["history"].append({"clarifier": clarifier_msg})
#     if user_response:
#         state["history"].append({"user": user_response})
#     state["round"] = state.get("round", 1) + 1
#     return state

# # Main Entrypoint
# def main():
#     print("[clarifier_server] Booting clarifier server...", flush=True)

#     try:
#         print("[clarifier_server] Starting MCP server...", flush=True)

#         print("[clarifier_server] Running mcp.run() with transport='stdio'...", flush=True)
        
#         mcp.run(transport="stdio")  # Start the server loop with stdio communication
        # This line will never be reached if mcp.run() works properly, so log here to confirm if it’s stuck.
#         print("[clarifier_server] Server finished running", flush=True)

#     except Exception as e:
#         print(f"[clarifier_server] Critical error during startup: {e}", flush=True)
#         sys.exit(1)

# if __name__ == "__main__":
#     main()



#not used in the pipeline because it wasn't serving its purpose, i will be updating this with time
from fastapi import FastAPI
from pydantic import BaseModel
from datetime import datetime
import requests

CLARIFIER_NAME = "clarifier_server"
LLM_URL = "http://localhost:8003/complete"

app = FastAPI()
class StartSessionRequest(BaseModel):
    user_input: str
class StartSessionResponse(BaseModel):
    created_at: str
    round: int
    history: list
    final_query: str | None
class UpdateStateRequest(BaseModel):
    state: dict | None
    clarifier_msg: str
    user_response: str | None = None

class UpdateStateResponse(BaseModel):
    state: dict

@app.post("/start_session", response_model=StartSessionResponse)
def start_session(request: StartSessionRequest):
    created = datetime.utcnow().isoformat()
    history = [{"user": request.user_input}]
    return StartSessionResponse(created_at=created, round=1, history=history, final_query=None)

@app.post("/update_state", response_model=UpdateStateResponse)
def update_state(request: UpdateStateRequest):
    state = request.state or {"history": [], "round": 1}
    if request.clarifier_msg:
        state["history"].append({"clarifier": request.clarifier_msg})
    if request.user_response:
        state["history"].append({"user": request.user_response})
    state["round"] = state.get("round", 1) + 1
    return UpdateStateResponse(state=state)

@app.post("/clarify_and_finalize")
def clarify_and_finalize(payload: StartSessionRequest):
    user_input = payload.user_input
    context = ""
    if "AI" in user_input or "artificial intelligence" in user_input:
        context += " Focus on the business implications of AI, especially in emerging markets like Kenya. Consider opportunities, challenges, and risks for entrepreneurs in the AI sector."
    if "finance" in user_input or "business" in user_input:
        context += " Focus on financial viability, cost considerations, and the potential market for new business ventures."
    if "Kenya" in user_input:
        context += " Focus on the AI and tech landscape in Kenya, addressing local challenges, opportunities, and market conditions."
    system = "You are a clarifier assistant. Rephrase and clarify the user's request into 1-2 concise final research questions, including business context where applicable."
    prompt = f"User request: {user_input}\n\nContext: {context}\n\nProduce a concise final query and clarifying sub-questions."
    
    resp = requests.post(LLM_URL, json={"system": system, "prompt": prompt})
    if resp.status_code != 200:
        return {"error": "LLM unavailable", "status": resp.status_code}
    
    content = resp.json().get("response", "")
    created = datetime.utcnow().isoformat()
    
    state = {
        "created_at": created, 
        "round": 1, 
        "history": [{"user": user_input}, {"clarifier_llm": content}],
        "final_query": content
    }
    return state

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
