


#!/usr/bin/env python3
"""
 AGENTIC DEEP RESEARCH AGENT v3.0
- Features True Agentic Loop: Plan → Search → Reflect → Refine → Synthesize
- Self-Correcting: Audits findings and searches for missing data
- Real-time progress updates in Gradio UI
"""

import os
import re
import sys
import json
import socket
import logging
from dotenv import load_dotenv
import openai
import gradio as gr

# ===  INPUT & OUTPUT GUARDRAILS ===
import re

def input_guardrail(query: str) -> tuple[bool, str]:
    """Validates user input. Returns (is_valid, error_message)."""
    if not query or not query.strip():
        return False, " Please enter a research question."
    if len(query) > 1500:
        return False, " Question too long. Keep under 1500 characters."
    
    # Prompt injection / jailbreak detection
    injection_patterns = [
        r"ignore\s+previous\s+instructions",
        r"disregard\s+all\s+rules",
        r"pretend\s+(to\s+be|you\s+are)",
        r"you\s+are\s+now\s+",
        r"jailbreak",
        r"bypass\s+(filters|security)",
        r"system\s+prompt",
        r"/system",
        r"do\s+anything\s+now",
        r"repeat\s+this\s+back"
    ]
    for pattern in injection_patterns:
        if re.search(pattern, query, re.IGNORECASE):
            return False, " Input contains restricted patterns. Please rephrase."
    
    return True, ""

def output_guardrail(text: str) -> str:
    """Sanitizes, validates, and truncates LLM output."""
    if not text or text.isspace():
        return " No response generated. Please try again or rephrase your query."
    
    # Strip potentially dangerous HTML/script tags (XSS prevention)
    text = re.sub(r'<(script|iframe|object|embed|style|link)[^>]*>.*?</\1>', '[REMOVED]', text, flags=re.IGNORECASE|re.DOTALL)
    text = re.sub(r'<[^>]+>', '', text)  # Remove remaining HTML tags
    
    # Truncate excessively long outputs (prevents Gradio lag)
    MAX_OUTPUT = 6000
    if len(text) > MAX_OUTPUT:
        text = text[:MAX_OUTPUT] + "\n\n... [Output truncated for length]"
    
    return text.strip()

#   Setup
print(f" Python: {sys.version.split()[0]}", flush=True)
print(f" Gradio: {gr.__version__}", flush=True)

logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s: %(message)s', stream=sys.stdout)
load_dotenv()

#Search Tool
def search_web(query: str, max_results: int = 4) -> list[dict]:
    results = []
    tavily_key = os.getenv("TAVILY_API_KEY")
    
    if tavily_key:
        try:
            from tavily import TavilyClient
            client = TavilyClient(api_key=tavily_key)
            resp = client.search(query=query, search_depth="advanced", max_results=max_results)
            for r in resp.get("results", []):
                results.append({"title": r.get("title"), "url": r.get("url"), "content": r.get("content")[:2000]})
            return results
        except Exception as e:
            logging.warning(f"Tavily error: {e}")
    
    try:
        from duckduckgo_search import DDGS
        ddg = DDGS().text(query, max_results=max_results)
        for r in ddg:
            results.append({"title": r.get("title"), "url": r.get("href"), "content": r.get("body")[:2000]})
        return results
    except Exception as e:
        logging.error(f"DDG error: {e}")
        return []

#  LLM Client 
client = openai.OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url=os.getenv("OPENAI_API_BASE", "https://openrouter.ai/api/v1")
)
MODEL = os.getenv("LLM_MODEL", "openai/gpt-4o-mini")

def call_llm(messages: list, temperature: float = 0.7) -> str:
    try:
        resp = client.chat.completions.create(model=MODEL, messages=messages, temperature=temperature, max_tokens=2500)
        return resp.choices[0].message.content or ""
    except Exception as e:
        return f" LLM Error: {str(e)}"

# === Agentic Core Functions ===

def plan_initial(query: str) -> list[str]:
    """Step 1: Generate initial research plan."""
    sys_prompt = "Break this query into 3-5 specific, searchable sub-questions. Return ONLY a JSON list of strings."
    resp = call_llm([{"role": "system", "content": sys_prompt}, {"role": "user", "content": f"Query: {query}"}], 0.1)
    try:
        parsed = json.loads(re.search(r'\[.*\]', resp, re.DOTALL).group())
        return [str(q).strip() for q in parsed if len(q) > 10][:5]
    except:
        return [query]

def execute_searches(queries: list[str]) -> tuple[str, list[str]]:
    """Execute searches for a list of queries."""
    findings_text = ""
    urls_found = []
    
    for q in queries:
        res = search_web(q, max_results=3)
        findings_text += f"\n## Query: {q}\n"
        if res:
            for r in res:
                urls_found.append(r["url"])
                findings_text += f"- [{r['title']}]({r['url']}): {r['content'][:300]}...\n"
        else:
            findings_text += "- No results found.\n"
    
    return findings_text, urls_found

def reflect_and_refine(original_query: str, findings_summary: str) -> dict:
    """Step 2: Critic audits findings and identifies gaps."""
    sys_prompt = """You are a Lead Research Auditor. Review findings against the original query.
    1. Check if all aspects are answered with high confidence.
    2. Identify specific missing data, conflicting claims, or gaps.
    3. If gaps exist, generate 2-3 NEW targeted queries to fix them.
    Return ONLY valid JSON: {"satisfied": boolean, "missing_info": "string", "new_queries": ["string"]}"""
    
    resp = call_llm([
        {"role": "system", "content": sys_prompt},
        {"role": "user", "content": f"Query: {original_query}\nFindings Summary:\n{findings_summary}"}
    ], 0.2)
    
    try:
        parsed = json.loads(re.search(r'\{.*\}', resp, re.DOTALL).group())
        return {
            "satisfied": parsed.get("satisfied", False),
            "missing_info": parsed.get("missing_info", ""),
            "new_queries": parsed.get("new_queries", [])
        }
    except:
        return {"satisfied": True, "missing_info": "", "new_queries": []}

def synthesize_report(query: str, all_findings: str, all_urls: list[str]) -> str:
    """Step 3: Final Report Generation."""
    unique_urls = list(dict.fromkeys([u for u in all_urls if u.startswith("http")]))
    sources_list = "\n".join([f"{i+1}. {url}" for i, url in enumerate(unique_urls[:10])])
    
    sys_prompt = f"""Write a comprehensive Deep Research Report.
    Structure:
    1.  Executive Summary (1-2 sentences)
    2.  Key Findings (Bullet points with inline [Source](URL) citations)
    3.  Critical Analysis (Conflicts, tradeoffs, uncertainties)
    4.  Verified Sources:
    {sources_list}
    5.  Time Sensitivity Note
    
    Rules: Use EXACT URLs from sources list. Never fabricate citations."""
    
    return call_llm([
        {"role": "system", "content": sys_prompt},
        {"role": "user", "content": f"Query: {query}\nAll Findings:\n{all_findings}"}
    ], 0.6)

# ===  Gradio Interface Logic ===

def deep_research_agent(user_query: str, history: list):
    """Main Agentic Loop with Streaming Updates."""
    if not user_query or not user_query.strip():
        history.append({"role": "assistant", "content": " Please enter a research question."})
        yield history
        return

    # 1. Add User Message
    history.append({"role": "user", "content": user_query})
    yield history
    
    # 2. Start Agent Response
    history.append({"role": "assistant", "content": " **Initializing Agentic Deep Research...**\n"})
    yield history

    all_findings = ""
    all_urls = []
    iteration = 0
    max_iterations = 3
    satisfied = False
    
    # 3. Initial Plan
    history[-1]["content"] += "\n **Phase 1: Planning**\n"
    yield history
    queries = plan_initial(user_query)
    history[-1]["content"] += f" Initial plan: {len(queries)} queries.\n"
    for i, q in enumerate(queries, 1): history[-1]["content"] += f"   {i}. {q}\n"
    yield history

    # 4. Agentic Loop: Search → Reflect → Refine
    while iteration < max_iterations and not satisfied:
        iteration += 1
        history[-1]["content"] += f"\n **Iteration {iteration}/{max_iterations}**\n"
        yield history

        # A. Execute Search
        history[-1]["content"] += " Searching web...\n"
        yield history
        findings_text, urls_found = execute_searches(queries)
        all_findings += findings_text
        all_urls.extend(urls_found)
        history[-1]["content"] += f" Retrieved data from {len(urls_found)} sources.\n"
        yield history

        # B. Reflect & Critique
        history[-1]["content"] += " Auditing findings for gaps...\n"
        yield history
        critique = reflect_and_refine(user_query, all_findings)
        
        if critique["satisfied"]:
            satisfied = True
            history[-1]["content"] += " **Audit Passed**: Findings are comprehensive. Proceeding to synthesis.\n"
        else:
            history[-1]["content"] += f" **Audit Failed**: {critique['missing_info']}\n"
            history[-1]["content"] += f" Generating {len(critique['new_queries'])} refined queries...\n"
            queries = critique["new_queries"]
            for i, q in enumerate(queries, 1): history[-1]["content"] += f"   {i}. {q}\n"
        yield history

    # 5. Synthesize
    history[-1]["content"] += "\n **Synthesizing Final Report**...\n"
    yield history
    
    report = synthesize_report(user_query, all_findings, all_urls)
    history[-1]["content"] = report
    yield history

def respond(message, history):
    if history is None: history = []
    for update in deep_research_agent(message, history):
        yield update

# ===  Launch ===
def find_free_port(start=7860):
    for p in range(start, start+10):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(('127.0.0.1', p)) != 0: return p
    return 7860

if __name__ == "__main__":
    PORT = find_free_port()
    print(f"\n Agentic Deep Research Agent v3.0")
    print(f" http://127.0.0.1:{PORT}\n")
    
    with gr.Blocks() as demo:
        gr.Markdown("#  Agentic Deep Research v3.0")
        gr.Markdown("✨ **True Agentic Loop**: Plan → Search → **Self-Correct** → Synthesize")
        
        chatbot = gr.Chatbot(label="Research Report", height=700)
        msg = gr.Textbox(label="Query", placeholder="Try: 'Compare economic impacts of AI vs Robotics on global supply chains'", lines=2)
        
        with gr.Row():
            submit = gr.Button(" Start Deep Research", variant="primary")
            clear = gr.ClearButton([msg, chatbot])
        
        msg.submit(respond, [msg, chatbot], [chatbot])
        submit.click(respond, [msg, chatbot], [chatbot])
    
    demo.launch(server_name="127.0.0.1", server_port=PORT)