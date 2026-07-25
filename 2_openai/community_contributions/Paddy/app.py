"""
Content Management System — Deep Research with Streamlit.
Uses 3 questions to optimize the result; Gemini 2.5 Flash for planning and writing.
"""
import asyncio
import sys
from pathlib import Path

# Ensure Paddy folder is on path when run from repo root (e.g. Streamlit Cloud)
_APP_DIR = Path(__file__).resolve().parent
if str(_APP_DIR) not in sys.path:
    sys.path.insert(0, str(_APP_DIR))

import os
import streamlit as st
from dotenv import load_dotenv

load_dotenv(override=True)

# Inject Streamlit Cloud secrets into env before config is loaded (config is imported via research_manager)
try:
    for key in ("GOOGLE_API_KEY", "OPENAI_API_KEY"):
        if not os.getenv(key) and getattr(st, "secrets", None):
            val = st.secrets.get(key)
            if val:
                os.environ[key] = val
except Exception:
    pass

from research_manager import ResearchManager
from config import GOOGLE_API_KEY, OPENAI_API_KEY

st.set_page_config(
    page_title="Content Research | Paddy",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="expanded",
)

if not GOOGLE_API_KEY or not OPENAI_API_KEY:
    st.error(
        "**API keys not set.** Use a `.env` file locally with `GOOGLE_API_KEY` and `OPENAI_API_KEY`. "
        "On **Streamlit Cloud**: open **Manage app** (bottom right) → **Settings** → **Secrets** and add:\n\n"
        "`GOOGLE_API_KEY = \"your-gemini-key\"`  \n`OPENAI_API_KEY = \"your-openai-key\"`"
    )
    st.stop()

# Custom CSS — elegant light theme with visible, readable text
st.markdown("""
<style>
    /* Base: white background, dark text */
    .stApp, [data-testid="stAppViewContainer"], main {
        background: linear-gradient(180deg, #fafbfc 0%, #ffffff 100%) !important;
    }
    .stMarkdown, .stMarkdown p {
        color: #1e293b !important;
    }
    [data-testid="stExpander"] {
        background-color: #ffffff !important;
        border-radius: 12px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.06);
    }
    [data-testid="stTextInput"] input, [data-testid="stTextArea"] textarea {
        background-color: #ffffff !important;
        color: #1e293b !important;
        border: 1px solid #d1d5db;
    }
    [data-testid="stCheckbox"] label {
        color: #1e293b !important;
        font-size: 0.95rem;
        line-height: 1.5;
    }
    /* Status / progress — highly visible dark text */
    .status-msg {
        background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);
        color: #0c4a6e !important;
        padding: 1rem 1.25rem;
        border-radius: 10px;
        font-size: 1rem;
        font-weight: 500;
        border-left: 4px solid #0284c7;
        margin: 0.5rem 0;
    }
    /* Primary button — elegant blue */
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%) !important;
        color: white !important;
        font-weight: 600;
        padding: 0.6rem 1.5rem;
        border-radius: 10px;
        box-shadow: 0 2px 8px rgba(37, 99, 235, 0.3);
    }
    .main-header {
        font-size: 2rem;
        font-weight: 700;
        color: #0f172a !important;
        margin-bottom: 0.5rem;
        letter-spacing: -0.02em;
    }
    .sub-header {
        font-size: 1rem;
        color: #475569 !important;
        margin-bottom: 2rem;
    }
    .report-container {
        background: #ffffff;
        border-radius: 12px;
        padding: 2rem;
        border: 1px solid #e2e8f0;
        box-shadow: 0 4px 12px rgba(0,0,0,0.04);
        margin-top: 1.5rem;
    }
    .summary-box {
        background: #f8fafc;
        border-left: 4px solid #2563eb;
        padding: 1.25rem 1.5rem;
        border-radius: 0 10px 10px 0;
        margin: 1rem 0;
        color: #1e293b !important;
    }
    .follow-ups {
        background: #f8fafc;
        padding: 1.25rem;
        border-radius: 10px;
        margin-top: 1rem;
        border: 1px solid #e2e8f0;
    }
    .stMarkdown h1, .stMarkdown h2, .stMarkdown h3 {
        color: #0f172a !important;
        margin-top: 1.5rem;
    }
    /* Tabs — visible labels */
    .stTabs [data-baseweb="tab-list"] {
        gap: 0.5rem;
    }
    .stTabs [data-baseweb="tab"] {
        color: #475569 !important;
        font-weight: 500;
    }
    .stTabs [aria-selected="true"] {
        color: #2563eb !important;
    }
    /* Spinner and status — visible text */
    [data-testid="stSpinner"] label, [data-testid="stStatus"] {
        color: #0c4a6e !important;
        font-weight: 500;
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<p class="main-header">Content Research System</p>', unsafe_allow_html=True)
st.markdown(
    '<p class="sub-header">Get a research-backed report tailored to your topic, audience, and focus. '
    'Powered by Gemini 2.5 Flash and web search.</p>',
    unsafe_allow_html=True,
)

# ——— 3 questions to optimize the result ———
with st.expander("Configure your research", expanded=True):
    st.markdown("#### 1. What do you want to research?")
    topic = st.text_area(
        "Topic or question",
        placeholder="e.g. Latest AI agent frameworks in 2025, or: Best practices for API design",
        height=100,
        label_visibility="collapsed",
    )

    st.markdown("#### 2. Who is the audience?")
    audience = st.selectbox(
        "Audience",
        [
            "Technical team / developers",
            "Executives / decision makers",
            "General public",
            "Marketing / sales",
            "Other (describe below)",
        ],
        label_visibility="collapsed",
    )
    if audience == "Other (describe below)":
        audience = st.text_input("Describe audience", placeholder="e.g. HR managers in mid-size companies")

    st.markdown("#### 3. Any specific focus or constraints?")
    focus = st.text_input(
        "Focus areas, time range, or constraints",
        placeholder="e.g. Focus on 2024–2025, include competitor comparison, keep under 1500 words",
        label_visibility="collapsed",
    )

# Session state for report, context, and follow-up research results
if "last_report" not in st.session_state:
    st.session_state.last_report = None
if "last_audience" not in st.session_state:
    st.session_state.last_audience = ""
if "last_focus" not in st.session_state:
    st.session_state.last_focus = ""
if "follow_up_results" not in st.session_state:
    st.session_state.follow_up_results = []

run = st.button("Run research", type="primary", use_container_width=True)

if run and topic.strip():
    manager = ResearchManager(audience=audience, focus=focus or None)
    progress = st.empty()
    report_placeholder = st.empty()

    async def run_research(query: str):
        last = None
        async for chunk in manager.run(query):
            if hasattr(chunk, "markdown_report"):
                last = chunk
            elif isinstance(chunk, str) and len(chunk) < 200:
                progress.markdown(
                    f'<div class="status-msg">⟳ {chunk}</div>',
                    unsafe_allow_html=True,
                )
        progress.empty()
        return last

    with st.spinner(""):
        report_data = asyncio.run(run_research(topic.strip()))

    if report_data:
        st.session_state.last_report = report_data
        st.session_state.last_audience = audience
        st.session_state.last_focus = focus or ""
        st.session_state.follow_up_results = []

elif run and not topic.strip():
    st.warning("Please enter a topic or question to research.")

# Render report and follow-up section (from session_state so it persists)
report_data = st.session_state.last_report
if report_data:
    st.markdown("---")
    summary_tab, full_tab, follow_tab = st.tabs(["Summary", "Full report", "Follow-up questions"])

    with summary_tab:
        st.markdown('<div class="summary-box">', unsafe_allow_html=True)
        st.markdown(report_data.short_summary)
        st.markdown("</div>", unsafe_allow_html=True)

    with full_tab:
        st.markdown('<div class="report-container">', unsafe_allow_html=True)
        st.markdown(report_data.markdown_report, unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with follow_tab:
        st.markdown('<div class="follow-ups">', unsafe_allow_html=True)
        questions = report_data.follow_up_questions or []

        if questions:
            st.markdown("**Select one or more questions to research further.** You can refine your selection below before running.")
            st.markdown("")  # spacing

            selected = {}
            for i, q in enumerate(questions):
                key = f"follow_up_{i}"
                selected[key] = st.checkbox(q, key=key)

            st.markdown("#### Refine your query (optional)")
            refined = st.text_area(
                "Edit or combine the selected questions before researching",
                placeholder="e.g. Focus on AWS Lambda and Azure Functions specifically",
                height=80,
                key="refine_query",
                label_visibility="collapsed",
            )

            cols = st.columns([1, 1, 2])
            with cols[0]:
                research_followup = st.button("Research selected", type="primary", key="research_followup")

            if research_followup:
                indices = [i for i in range(len(questions)) if selected.get(f"follow_up_{i}", False)]
                if not indices:
                    st.warning("Select at least one follow-up question.")
                else:
                    manager = ResearchManager(
                        audience=st.session_state.last_audience,
                        focus=st.session_state.last_focus or None,
                    )

                    async def run_followup_research(q: str):
                        last = None
                        async for chunk in manager.run(q):
                            if hasattr(chunk, "markdown_report"):
                                last = chunk
                            elif isinstance(chunk, str) and len(chunk) < 200:
                                progress.markdown(
                                    f'<div class="status-msg">⟳ {chunk}</div>',
                                    unsafe_allow_html=True,
                                )
                        progress.empty()
                        return last

                    # Refined text overrides selection; otherwise research each selected question
                    if refined.strip():
                        queries_to_run = [refined.strip()]
                    else:
                        queries_to_run = [questions[i] for i in indices]

                    for q in queries_to_run:
                        progress = st.empty()
                        with st.spinner(f"Researching: {q[:60]}{'…' if len(q) > 60 else ''}"):
                            followup_report = asyncio.run(run_followup_research(q))
                        if followup_report:
                            st.session_state.follow_up_results.append(
                                {"query": q, "report": followup_report}
                            )

        # Show previous follow-up research results
        for i, item in enumerate(st.session_state.follow_up_results):
            with st.expander(f"📄 Research: {item['query'][:80]}{'…' if len(item['query']) > 80 else ''}", expanded=True):
                r = item["report"]
                st.markdown("**Summary**")
                st.markdown(r.short_summary)
                st.markdown("---")
                st.markdown(r.markdown_report)

        if not questions:
            st.info("No follow-up questions generated for this report.")
        st.markdown("</div>", unsafe_allow_html=True)
