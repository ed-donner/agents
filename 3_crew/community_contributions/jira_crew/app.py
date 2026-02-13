"""
Jira Support Crew — Streamlit frontend.
Multi-agent Jira support (epics, sprints, boards) powered by CrewAI.
Uses local Ollama by default; set USE_OLLAMA=false for Gemini.
"""
import os
import sys
from pathlib import Path

# Disable CrewAI telemetry before any crewai import (avoids "signal only works in main thread" in Streamlit)
os.environ.setdefault("CREWAI_DISABLE_TELEMETRY", "true")
os.environ.setdefault("OTEL_SDK_DISABLED", "true")

# Add src so jira_crew package is found
_APP_DIR = Path(__file__).resolve().parent
_SRC = _APP_DIR / "src"
if _SRC.exists() and str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

import streamlit as st
from dotenv import load_dotenv

load_dotenv(_APP_DIR / ".env", override=True)
load_dotenv(override=True)

# Inject Streamlit secrets into env (Ollama is default; Gemini optional)
try:
    import os
    for key in (
        "USE_OLLAMA", "OLLAMA_BASE_URL", "OLLAMA_MODEL",
        "GOOGLE_API_KEY", "GEMINI_API_KEY", "JIRA_BASE_URL", "JIRA_EMAIL", "JIRA_API_TOKEN",
    ):
        if not os.getenv(key) and getattr(st, "secrets", None):
            val = st.secrets.get(key)
            if val is not None:
                os.environ[key] = str(val)
    if os.getenv("GOOGLE_API_KEY") and not os.getenv("GEMINI_API_KEY"):
        os.environ["GEMINI_API_KEY"] = os.environ["GOOGLE_API_KEY"]
except Exception:
    pass

st.set_page_config(
    page_title="Jira Support | Crew AI",
    page_icon="📋",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# Elegant, minimal styling — ensure all text is visible (dark on light)
st.markdown("""
<style>
    .stApp { background: linear-gradient(180deg, #f8fafc 0%, #fff 100%); }
    .main-header { font-size: 1.75rem; font-weight: 700; color: #0f172a !important; margin-bottom: 0.25rem; }
    .sub-header { color: #475569 !important; font-size: 0.95rem; margin-bottom: 1.5rem; }
    /* Chat messages: force visible text */
    div[data-testid="stChatMessage"] {
        background: #f8fafc;
        border-radius: 10px;
        border: 1px solid #e2e8f0;
    }
    div[data-testid="stChatMessage"] p,
    div[data-testid="stChatMessage"] div,
    div[data-testid="stChatMessage"] span,
    div[data-testid="stChatMessage"] .stMarkdown {
        color: #1e293b !important;
    }
    /* General content text */
    .stMarkdown p, .stMarkdown div, .stMarkdown li {
        color: #1e293b !important;
    }
    /* Chat input placeholder visibility */
    input[data-testid="stChatInput"] {
        color: #1e293b !important;
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<p class="main-header">Jira Support</p>', unsafe_allow_html=True)
st.markdown(
    '<p class="sub-header">Ask about epics, sprints, boards, or how to use Jira. I can list or create items when Jira is configured.</p>',
    unsafe_allow_html=True,
)

# Session state for chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Sidebar hint
with st.sidebar:
    st.caption("**Examples**")
    st.markdown("- List all epics")
    st.markdown("- Show my boards")
    st.markdown("- What is a Jira sprint?")
    st.markdown("- Create epic in PROJ with title **New feature**")
    st.caption("**LLM:** Local Ollama (default). Set `USE_OLLAMA=false` + **GOOGLE_API_KEY** for Gemini.")

# Chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Input
prompt = st.chat_input("Ask about Jira…")
if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Thinking…"):
            try:
                from jira_crew.crew import JiraSupportCrew
                inputs = {"user_question": prompt}
                result = JiraSupportCrew().crew().kickoff(inputs=inputs)
                if hasattr(result, "raw") and result.raw:
                    answer = result.raw
                elif hasattr(result, "final_output") and result.final_output:
                    answer = str(result.final_output)
                else:
                    answer = str(result)
            except Exception as e:
                answer = (
                    f"Something went wrong: {str(e)}. "
                    "Ensure **Ollama** is running locally (default), or set **GOOGLE_API_KEY** and USE_OLLAMA=false for Gemini. "
                    "Jira vars optional for live data."
                )
        st.markdown(answer)

    st.session_state.messages.append({"role": "assistant", "content": answer})
