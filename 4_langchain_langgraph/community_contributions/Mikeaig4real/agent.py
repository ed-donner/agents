"""Job Hunter"""

from typing import Annotated, List, Any, Dict
from typing_extensions import TypedDict
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.memory import MemorySaver
from tools import playwright_tools, other_tools
from memory import get_connection, get_cached_resume, save_resume, invalidate_resume
import re
from pypdf import PdfReader
import io
from datetime import datetime
import os
import uuid
import asyncio

# State
class State(TypedDict):
    messages: Annotated[List[Any], add_messages]
    resume_text: str
    resume_url: str


# Agent class
class JobHunterAgent:

    def __init__(self):
        self.tools = None
        self.browser = None
        self.playwright = None
        self.llm_with_tools = None
        self.graph = None
        self.thread_id = str(uuid.uuid4())
        self.db_conn = get_connection()
        self.checkpointer = MemorySaver()

    async def setup(self):
        """Initialise tools, LLM, and compile the graph."""
        browser_tools, self.browser, self.playwright = await playwright_tools()
        extra_tools = await other_tools()
        self.tools = browser_tools + extra_tools

        openrouter_base = "https://openrouter.ai/api/v1"
        openrouter_key = os.getenv("OPENROUTER_API_KEY")

        llm = ChatOpenAI(
            model="deepseek/deepseek-chat-v3-0324",
            base_url=openrouter_base,
            api_key=openrouter_key,
        )
        self.llm_with_tools = llm.bind_tools(self.tools)

        self._build_graph()

    def _system_prompt(self, state: State) -> str:
        """Build the system prompt with current context."""
        resume_snippet = (state.get("resume_text") or "No resume loaded yet.")[:4000]
        return f"""You are Job Hunter AI, a helpful assistant that finds matching jobs for a user based on their resume.
You have tools to browse the web, search for jobs, and send push notifications.
The current date and time is {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}.

RESUME CONTEXT:
{resume_snippet}

INSTRUCTIONS:
1. When the user provides a Google Docs link, let them know you've parsed it.
2. Use the `search_jobs` tool to find potential job openings.
3. **CRITICAL**: For the most promising jobs found in search, use the browser tools (`navigate_browser`, `page_read`) to visit the actual job page.
4. Extract specific details like the **application deadline**, **location**, **salary range** (if available), and **key requirements** directly from the page.
5. Provide the user with: Title, Company, Location, Match Score (0-100), Deadline, and the **Real URL** found in search.
6. **NO PLACEHOLDERS**: Do NOT use `example.com` or other placeholders for links. If you don't have a real link, say so.
7. Use the `send_notification` tool for urgent or highly relevant matches.
- Be concise, professional, and helpful."""

    def worker(self, state: State) -> Dict[str, Any]:
        """Main worker node — calls the LLM with tools."""
        system_message = self._system_prompt(state)
        
        # Add in the system message (alignment with official pattern)
        found_system_message = False
        messages = state["messages"]
        for message in messages:
            if isinstance(message, SystemMessage):
                message.content = system_message
                found_system_message = True
                break

        if not found_system_message:
            messages = [SystemMessage(content=system_message)] + messages

        response = self.llm_with_tools.invoke(messages)
        return {"messages": [response]}

    # routing
    def _router(self, state: State) -> str:
        last = state["messages"][-1]
        if hasattr(last, "tool_calls") and last.tool_calls:
            return "tools"
        return END

    # graph
    def _build_graph(self):
        """Compile the LangGraph state graph."""
        builder = StateGraph(State)

        builder.add_node("worker", self.worker)
        builder.add_node("tools", ToolNode(tools=self.tools))

        builder.add_edge(START, "worker")
        builder.add_conditional_edges("worker", self._router, {"tools": "tools", END: END})
        builder.add_edge("tools", "worker")

        self.graph = builder.compile(checkpointer=self.checkpointer)

    # resume handling
    def _check_refetch(self, message: str) -> bool:
        """Check if the user is asking to refetch their resume."""
        triggers = ["refetch", "update resume", "re-read", "reload resume"]
        return any(t in message.lower() for t in triggers)

    async def _load_resume(self, url: str, force: bool = False) -> str:
        """Load resume from cache or fetch via PDF export."""
        if "docs.google.com/document" not in url:
            return ""

        if not force:
            cached = get_cached_resume(self.db_conn, url)
            if cached:
                try:
                    with open("resume.md", "w", encoding="utf-8") as f:
                        f.write(cached)
                except Exception:
                    pass
                return cached

        # Use PDF export for better structure
        doc_id_match = re.search(r'/document/d/([a-zA-Z0-9_-]+)', url)
        if not doc_id_match:
            return "Invalid Google Docs URL"
        
        doc_id = doc_id_match.group(1)
        pdf_url = f"https://docs.google.com/document/d/{doc_id}/export?format=pdf"
        
        try:
            import requests
            resp = requests.get(pdf_url, timeout=20)
            resp.raise_for_status()
            
            # Extract text
            with io.BytesIO(resp.content) as pdf_file:
                reader = PdfReader(pdf_file)
                text = ""
                for page in reader.pages:
                    text += (page.extract_text() or "") + "\n"
            
            # Save or fallback to text
            if not text.strip():
                # Fallback to plain text export
                txt_url = f"https://docs.google.com/document/d/{doc_id}/export?format=txt"
                resp = requests.get(txt_url, timeout=15)
                text = resp.text
                
            save_resume(self.db_conn, url, text)
                
            return text
        except Exception as e:
            return f"Error reading resume: {e}"

    async def run(self, message: str):
        """Run the agent and yield status updates then the text response."""
        config = {"configurable": {"thread_id": self.thread_id}}
        
        # Get current state
        current_state = await self.graph.aget_state(config)
        resume_url = current_state.values.get("resume_url", "")
        resume_text = current_state.values.get("resume_text", "")

        # Check for Google Docs URL
        url_pattern = r"(https?://docs\.google\.com/document/d/[a-zA-Z0-9_-]+)"
        match = re.search(url_pattern, message)
        
        new_resume_detected = False
        if match:
            new_url = match.group(1)
            if new_url != resume_url:
                yield "**Detecting new resume link...**"
                resume_url = new_url
                yield "**Extracting professional details from PDF...**"
                resume_text = await self._load_resume(resume_url, force=True)
                new_resume_detected = True

        force_refetch = self._check_refetch(message)
        if force_refetch and resume_url:
            yield "**Refetching resume data...**"
            invalidate_resume(self.db_conn, resume_url)
            resume_text = await self._load_resume(resume_url, force=True)
            new_resume_detected = True

        state = {
            "messages": [HumanMessage(content=message)],
            "resume_text": resume_text,
            "resume_url": resume_url,
        }

        # If a new resume was detected, we can add a hint to the LLM
        if new_resume_detected:
            state["messages"].insert(0, SystemMessage(content="[SYSTEM]: A new resume has been successfully parsed and loaded into your context. Please acknowledge this by providing a very brief summary (2-3 bullet points) of the resume (e.g. key skills, last role) as proof that you've read it."))
            yield "**AI is analyzing your resume and generating a summary...**"

        result = await self.graph.ainvoke(state, config=config)
        response = result["messages"][-1].content
        
        # Also prepend a clear visual indicator if it was a new resume
        if new_resume_detected:
            response = "**Resume parsed successfully!**\n\n" + response
            
        yield response

    def cleanup(self):
        """Release browser resources."""
        if self.browser:
            try:
                loop = asyncio.get_running_loop()
                loop.create_task(self.browser.close())
                if self.playwright:
                    loop.create_task(self.playwright.stop())
            except RuntimeError:
                asyncio.run(self.browser.close())
                if self.playwright:
                    asyncio.run(self.playwright.stop())

