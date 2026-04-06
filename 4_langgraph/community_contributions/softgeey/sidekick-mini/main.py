"""
SideKick Mini — Project Task Structuring Agent
LangGraph + FastAPI  |  single-file backend
"""

import os
from typing import Annotated
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, BaseMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse

load_dotenv()

# ── Config ────────────────────────────────────────────────────────────

API_KEY = os.getenv("OPENROUTER_API_KEY", "")
MODEL   = os.getenv("OPENROUTER_MODEL", "anthropic/claude-sonnet-4-5")

if not API_KEY:
    raise EnvironmentError("OPENROUTER_API_KEY is not set in .env")

# ── LLM ──────────────────────────────────────────────────────────────

def get_llm() -> ChatOpenAI:
    return ChatOpenAI(
        model=MODEL,
        temperature=0.3,
        api_key=API_KEY,
        base_url="https://openrouter.ai/api/v1",
        default_headers={"HTTP-Referer": "http://localhost:8001", "X-Title": "SideKick Mini"},
    )

# ── Agent State ───────────────────────────────────────────────────────

class State(BaseModel):
    messages: Annotated[list[BaseMessage], add_messages] = Field(default_factory=list)
    response: str = ""

    class Config:
        arbitrary_types_allowed = True

# ── System Prompt ─────────────────────────────────────────────────────

SYSTEM = """You are SideKick, a focused AI assistant for a Senior Project Manager at a software company.

Your job: turn raw project input into a clean, structured, actionable task plan.

Always respond with this structure:

## Summary
One sentence describing the project or goal.

## Tasks
List every task with priority and owner placeholder:
- CRITICAL: Task — Owner: @TBD
- IMPORTANT: Task — Owner: @TBD
- NICE-TO-HAVE: Task — Owner: @TBD

## Risks & Blockers
- Risk or blocker — Mitigation: [suggestion]

## Recommended Next Step
One concrete action to take immediately.

Be direct, specific, and concise. No filler."""

# ── Agent Node ────────────────────────────────────────────────────────

def agent_node(state: State) -> dict:
    llm = get_llm()
    messages = [SystemMessage(content=SYSTEM)] + list(state.messages[-10:])
    result = llm.invoke(messages)
    return {
        "response": result.content,
        "messages": [AIMessage(content=result.content)],
    }

# ── Graph ─────────────────────────────────────────────────────────────

def build_graph():
    g = StateGraph(State)
    g.add_node("agent", agent_node)
    g.add_edge(START, "agent")
    g.add_edge("agent", END)
    return g.compile()

graph = build_graph()

# ── FastAPI ───────────────────────────────────────────────────────────

app = FastAPI(title="SideKick Mini", version="1.0.0")

_history: list[BaseMessage] = []


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    response: str


@app.post("/chat", response_model=ChatResponse)
async def chat(body: ChatRequest):
    text = body.message.strip()
    if not text:
        raise HTTPException(status_code=400, detail="Message cannot be empty.")
    _history.append(HumanMessage(content=text))
    result = graph.invoke(State(messages=_history))
    _history.clear()
    _history.extend(result["messages"])
    return ChatResponse(response=result["response"])


@app.post("/reset")
async def reset():
    _history.clear()
    return {"status": "ok"}


@app.get("/", response_class=HTMLResponse)
async def index():
    return HTMLResponse(UI_HTML)


# ── Inline UI ─────────────────────────────────────────────────────────

UI_HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>SideKick Mini</title>
<style>
  @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500&family=IBM+Plex+Sans:wght@400;500;600&display=swap');
  :root{--bg:#0d0f14;--panel:#13161e;--surface:#1a1e2a;--border:#252b3b;--accent:#f59e0b;--glow:rgba(245,158,11,0.1);--txt:#e8eaf0;--muted:#8892a4;--dim:#4a5568;--user-bg:#1e2d4a;--user-br:#2a4a7f;}
  *,*::before,*::after{box-sizing:border-box;margin:0;padding:0;}
  html,body{height:100%;background:var(--bg);color:var(--txt);font-family:'IBM Plex Sans',sans-serif;font-size:14px;overflow:hidden;}
  .layout{display:flex;flex-direction:column;height:100vh;max-width:860px;margin:0 auto;padding:0 16px;}
  header{display:flex;align-items:center;justify-content:space-between;padding:18px 0 16px;border-bottom:1px solid var(--border);flex-shrink:0;}
  .brand{display:flex;align-items:center;gap:10px;}
  .mark{width:30px;height:30px;background:var(--accent);border-radius:6px;display:flex;align-items:center;justify-content:center;}
  .mark svg{width:16px;height:16px;color:#0d0f14;}
  .bname{font-size:15px;font-weight:600;}
  .btag{font-size:10px;color:var(--dim);font-family:'IBM Plex Mono',monospace;letter-spacing:.08em;text-transform:uppercase;margin-top:1px;}
  .reset-btn{background:none;border:1px solid var(--border);border-radius:6px;color:var(--muted);font-size:11px;font-family:'IBM Plex Mono',monospace;padding:5px 10px;cursor:pointer;transition:.15s;}
  .reset-btn:hover{border-color:#2e3650;color:var(--txt);}
  .messages{flex:1;overflow-y:auto;padding:20px 0;scroll-behavior:smooth;}
  .messages::-webkit-scrollbar{width:3px;}
  .messages::-webkit-scrollbar-thumb{background:var(--border);border-radius:2px;}
  .msg{display:flex;gap:10px;margin-bottom:18px;animation:fi .2s ease;}
  .msg.user{flex-direction:row-reverse;}
  @keyframes fi{from{opacity:0;transform:translateY(6px)}to{opacity:1;transform:none}}
  .av{width:28px;height:28px;border-radius:5px;flex-shrink:0;display:flex;align-items:center;justify-content:center;font-size:10px;font-weight:600;font-family:'IBM Plex Mono',monospace;}
  .av.u{background:var(--user-br);color:#93c5fd;}
  .av.a{background:var(--accent);color:#0d0f14;}
  .bubble{max-width:80%;padding:11px 14px;border-radius:10px;font-size:13.5px;line-height:1.65;border:1px solid transparent;}
  .msg.user .bubble{background:var(--user-bg);border-color:var(--user-br);border-bottom-right-radius:2px;}
  .msg.agent .bubble{background:var(--panel);border-color:var(--border);border-bottom-left-radius:2px;}
  .bubble h2{font-size:13px;font-weight:600;color:var(--accent);margin:12px 0 5px;}
  .bubble h2:first-child{margin-top:0;}
  .bubble p{margin-bottom:6px;}
  .bubble ul{padding-left:16px;margin-bottom:6px;}
  .bubble li{margin-bottom:3px;}
  .bubble strong{color:var(--txt);}
  .typing{display:flex;gap:10px;align-items:center;margin-bottom:18px;}
  .dots{display:flex;gap:4px;padding:12px 14px;background:var(--panel);border:1px solid var(--border);border-radius:10px;border-bottom-left-radius:2px;}
  .dots span{width:5px;height:5px;border-radius:50%;background:var(--dim);animation:bn 1.1s infinite ease-in-out;}
  .dots span:nth-child(2){animation-delay:.18s;}
  .dots span:nth-child(3){animation-delay:.36s;}
  @keyframes bn{0%,60%,100%{transform:translateY(0);opacity:.4}30%{transform:translateY(-4px);opacity:1}}
  .prompts{display:flex;gap:7px;flex-wrap:wrap;margin-bottom:10px;}
  .pb{padding:5px 11px;background:var(--surface);border:1px solid var(--border);border-radius:20px;color:var(--muted);font-size:12px;cursor:pointer;transition:.15s;white-space:nowrap;}
  .pb:hover{border-color:var(--accent);color:var(--accent);background:var(--glow);}
  .input-wrap{border-top:1px solid var(--border);padding:14px 0 18px;flex-shrink:0;}
  .input-row{display:flex;align-items:flex-end;gap:8px;background:var(--surface);border:1px solid #2e3650;border-radius:10px;padding:9px 10px;transition:.15s;}
  .input-row:focus-within{border-color:#b45309;box-shadow:0 0 0 3px var(--glow);}
  textarea{flex:1;background:transparent;border:none;outline:none;color:var(--txt);font-family:'IBM Plex Sans',sans-serif;font-size:14px;resize:none;min-height:22px;max-height:120px;overflow-y:auto;line-height:1.5;}
  textarea::placeholder{color:var(--dim);}
  .send{width:32px;height:32px;background:var(--accent);border:none;border-radius:6px;cursor:pointer;display:flex;align-items:center;justify-content:center;flex-shrink:0;transition:.15s;color:#0d0f14;}
  .send:hover{background:#d97706;}
  .send:active{transform:scale(.95);}
  .send:disabled{background:var(--surface);color:var(--dim);cursor:not-allowed;}
  .send svg{width:15px;height:15px;}
  .hint{font-size:11px;color:var(--dim);font-family:'IBM Plex Mono',monospace;margin-top:7px;padding:0 2px;}
  .empty{display:flex;flex-direction:column;align-items:center;justify-content:center;height:100%;gap:10px;color:var(--dim);text-align:center;padding:40px;}
  .empty h2{font-size:16px;font-weight:600;color:var(--muted);}
  .empty p{font-size:13px;max-width:320px;line-height:1.6;}
</style>
</head>
<body>
<div class="layout">
  <header>
    <div class="brand">
      <div class="mark">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M9 11l3 3L22 4"/><path d="M21 12v7a2 2 0 01-2 2H5a2 2 0 01-2-2V5a2 2 0 012-2h11"/>
        </svg>
      </div>
      <div><div class="bname">SideKick Mini</div><div class="btag">Task Structuring</div></div>
    </div>
    <button class="reset-btn" onclick="doReset()">New Session</button>
  </header>

  <div class="messages" id="msgs">
    <div class="empty" id="empty">
      <h2>Describe your project.</h2>
      <p>Paste goals, scope, or a brain dump — I'll structure it into a clear task plan.</p>
    </div>
  </div>

  <div class="input-wrap">
    <div class="prompts">
      <button class="pb" onclick="fill('We need to launch a client portal in 6 weeks. Dev team of 3, a designer, and QA.')">Client portal launch</button>
      <button class="pb" onclick="fill('Migrate our monolith to microservices. No downtime allowed. 4 engineers.')">Monolith migration</button>
      <button class="pb" onclick="fill('Build an MVP mobile app for a fintech startup. 10-week timeline, tight budget.')">Fintech MVP</button>
    </div>
    <div class="input-row">
      <textarea id="inp" rows="1" placeholder="Describe your project, goals, or deliverables…"></textarea>
      <button class="send" id="snd" onclick="send()">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2">
          <path d="M22 2L11 13"/><path d="M22 2L15 22l-4-9-9-4 20-7z"/>
        </svg>
      </button>
    </div>
    <div class="hint">Enter to send &nbsp;·&nbsp; Shift+Enter for new line</div>
  </div>
</div>

<script>
  const msgsEl=document.getElementById('msgs'),inp=document.getElementById('inp'),snd=document.getElementById('snd');
  let busy=false;

  function esc(s){return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');}

  function md(t){
    return t
      .replace(/\*\*(.+?)\*\*/g,'<strong>$1</strong>')
      .replace(/^## (.+)$/gm,'<h2>$1</h2>')
      .replace(/((?:^- .+\n?)+)/gm,b=>'<ul>'+b.trim().split('\n').map(l=>'<li>'+l.slice(2)+'</li>').join('')+'</ul>')
      .replace(/\n\n/g,'</p><p>').replace(/\n/g,'<br>');
  }

  function addMsg(role,text){
    document.getElementById('empty')?.remove();
    const w=document.createElement('div'); w.className='msg '+role;
    const av=document.createElement('div'); av.className='av '+(role==='user'?'u':'a'); av.textContent=role==='user'?'YOU':'SK';
    const b=document.createElement('div'); b.className='bubble';
    b.innerHTML=role==='agent'?'<p>'+md(text)+'</p>':esc(text).replace(/\n/g,'<br>');
    w.appendChild(av); w.appendChild(b); msgsEl.appendChild(w);
    msgsEl.scrollTop=msgsEl.scrollHeight;
  }

  function showTyping(){
    const el=document.createElement('div'); el.className='typing'; el.id='typ';
    el.innerHTML='<div class="av a">SK</div><div class="dots"><span></span><span></span><span></span></div>';
    msgsEl.appendChild(el); msgsEl.scrollTop=msgsEl.scrollHeight;
  }

  async function send(){
    const text=inp.value.trim(); if(!text||busy)return;
    busy=true; snd.disabled=true; inp.disabled=true;
    addMsg('user',text); inp.value=''; resize(); showTyping();
    try{
      const r=await fetch('/chat',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({message:text})});
      document.getElementById('typ')?.remove();
      if(!r.ok){addMsg('agent','Error: '+(await r.json()).detail);return;}
      addMsg('agent',(await r.json()).response);
    }catch(e){document.getElementById('typ')?.remove();addMsg('agent','Network error: '+e.message);}
    finally{busy=false;snd.disabled=false;inp.disabled=false;inp.focus();}
  }

  async function doReset(){
    await fetch('/reset',{method:'POST'});
    msgsEl.innerHTML='<div class="empty" id="empty"><h2>Describe your project.</h2><p>Paste goals, scope, or a brain dump — I\'ll structure it into a clear task plan.</p></div>';
  }

  function fill(t){inp.value=t;resize();inp.focus();}
  function resize(){inp.style.height='auto';inp.style.height=Math.min(inp.scrollHeight,120)+'px';}
  inp.addEventListener('input',resize);
  inp.addEventListener('keydown',e=>{if(e.key==='Enter'&&!e.shiftKey){e.preventDefault();send();}});
</script>
</body>
</html>"""


# ── Entry point ───────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8001, reload=False, log_level="info")
