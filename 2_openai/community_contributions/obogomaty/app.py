
       
import os
import re
import logging
from dotenv import load_dotenv
import openai
import gradio as gr

# Setup basic logging
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s: %(message)s')
load_dotenv()

# === 🔍 LIVE WEB SEARCH TOOL ===
def search_web(query: str, max_results: int = 5) -> str:
    """Search the live internet for current information. Returns formatted results with URLs."""
    
    # Option A: Tavily (Recommended for AI agents, needs API key)
    tavily_key = os.getenv("TAVILY_API_KEY")
    if tavily_key:
        try:
            from tavily import TavilyClient
            tavily = TavilyClient(api_key=tavily_key)
            response = tavily.search(query=query, search_depth="advanced", max_results=max_results)
            results = []
            for r in response.get("results", []):
                results.append(f"🔹 {r['title']}\n   URL: {r['url']}\n   📄 {r['content']}\n")
            return "\n---\n".join(results)
        except Exception as e:
            logging.warning(f"Tavily search failed: {e}. Falling back to DuckDuckGo.")
            
    # Option B: DuckDuckGo fallback (No API key needed)
    try:
        from duckduckgo_search import DDGS
        results = DDGS().text(query, max_results=max_results)
        formatted = []
        for r in results:
            formatted.append(f"🔹 {r['title']}\n   URL: {r['href']}\n   📄 {r['body']}\n")
        return "\n---\n".join(formatted)
    except Exception as e:
        return f"⚠️ Web search error: {str(e)}"

# === 📝 UPDATED SYSTEM PROMPT ===
SYSTEM_PROMPT = """You are a DEEP RESEARCH assistant. Follow these rules STRICTLY:

1. 🌐 ALWAYS use the provided LIVE SEARCH RESULTS to answer. Do NOT rely on internal training data.
2. 🔗 CITE SOURCES: Include the exact URL for every key claim. Format: [Source](URL).
3. ⚠️ If search results conflict, note the discrepancy and present both sides.
4. ❌ If search returns no relevant results, say so honestly—do NOT make up information.
5. 📝 Structure your answer:
   - 🔍 Executive Summary (1-2 sentences)
   - 📋 Key Findings (bullet points with citations)
   - 🔗 Sources Used (list URLs)
   - ⏰ Note if information is time-sensitive

Example:
🔍 **Summary**: [Brief answer]
📋 **Findings**:
• Point one [Source](https://...)
• Point two [Source](https://...)
🔗 **Sources**:
1. https://...
2. https://...
⏰ *Information sourced from live web search.*"""

# === 🤖 OPENROUTER CLIENT ===
client = openai.OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url=os.getenv("OPENAI_API_BASE", "https://openrouter.ai/api/v1")
)

# === 💬 RESEARCH CHAT FUNCTION ===
def research_chat(user_message, history):
    # Input guardrail: check for empty or too long input
    if not user_message or not isinstance(user_message, str) or len(user_message.strip()) == 0:
        return "Please enter a valid research question."
    if len(user_message) > 1000:
        return "Your question is too long. Please shorten it to under 1000 characters."

    # Prompt injection filter
    injection_patterns = [
        r"ignore (all|any|the)? ?previous instructions?",
        r"disregard (all|any|the)? ?previous instructions?",
        r"pretend (to be|you are)",
        r"you are now",
        r"as an ai language model",
        r"repeat after me",
        r"do anything now",
        r"bypass",
        r"jailbreak",
        r"forget all previous",
        r"act as",
        r"system prompt",
        r"/system",
        r"### system",
        r"assistant:"
    ]
    for pattern in injection_patterns:
        if re.search(pattern, user_message, re.IGNORECASE):
            return "Your input contains patterns that are not allowed for security reasons. Please rephrase your question."

    # 🔍 STEP 1: SEARCH THE WEB FIRST
    logging.info(f"🌐 Searching the web for: {user_message}")
    search_results = search_web(user_message)

    # 🔍 STEP 2: BUILD MESSAGES WITH HISTORY
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    for turn in history:
        if isinstance(turn, dict) and "role" in turn and "content" in turn:
            messages.append({"role": turn["role"], "content": turn["content"]})
        elif isinstance(turn, (list, tuple)) and len(turn) == 2:
            messages.append({"role": "user", "content": turn[0]})
            messages.append({"role": "assistant", "content": turn[1]})

    # 🔍 STEP 3: ENHANCE USER PROMPT WITH SEARCH RESULTS
    enhanced_user_msg = f"""USER QUERY: {user_message}

🌐 LIVE SEARCH RESULTS (use these as your ONLY source for factual information):
{search_results}

Now answer the user's query using ONLY the search results above. Cite sources with URLs."""
    messages.append({"role": "user", "content": enhanced_user_msg})

    logging.info("Sending to LLM...")
    response = client.chat.completions.create(
        model="openai/gpt-3.5-turbo",
        messages=messages
    )
    result = response.choices[0].message.content.strip()

    # Output sanitization
    result = re.sub(r'<(script|iframe|object|embed)[^>]*>.*?</\\1>', '', result, flags=re.IGNORECASE|re.DOTALL)
    if len(result) > 3000:
        result = result[:3000] + "... [output truncated]"

    logging.info("LLM response received.")
    return result

# === 🚀 MAIN / CLI / GRADIO ===
def main():
    print("Welcome to the Deep Research App (OpenRouter + Live Web Search)")
    print("Type your research question (or 'quit' to exit):")
    while True:
        user_input = input("You: ").strip()
        if user_input.lower() in {"quit", "exit"}:
            print("Goodbye!")
            break
        print("AI:", research_chat(user_input, []))

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "cli":
        main()
    else:
        gr.ChatInterface(
            research_chat,
            title="Deep Research App (Live Web Search)",
            description="Ask research questions and get detailed, cited answers from live internet sources."
        ).launch()