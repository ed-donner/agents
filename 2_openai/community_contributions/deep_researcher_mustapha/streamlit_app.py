"""
streamlit_app.py — Streamlit UI for the Deep Research agent pipeline.

Run with:
    streamlit run streamlit_app.py

Reuses the existing agent modules:
    deep_research.py, planner_agent.py, research_agent.py,
    writer_agent.py, email_agent.py, research_manager.py
"""
import asyncio
import sys
import os

import streamlit as st

# Ensure local modules are importable
sys.path.insert(0, os.path.dirname(__file__))

from deep_research import setup_client
from research_manager import (
    plan_searches,
    perform_searches,
    write_report,
    send_report_email,
    run_security_scan,
)

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="KOMA-BAJE Deep Researcher",
    page_icon="🔬",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ── Setup OpenRouter client once per session ──────────────────────────────────
@st.cache_resource
def init_client():
    setup_client()

init_client()

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown(
    """
    <h1 style='text-align:center; color:#00bfff;'>🔬 Deep Researcher</h1>
    <p style='text-align:center; color:#94a3b8;'>
        Enter a research topic and your email — the AI will search the web,
        write a detailed report, and deliver it straight to your inbox.
    </p>
    """,
    unsafe_allow_html=True,
)
st.divider()

# ── Input form ────────────────────────────────────────────────────────────────
with st.form("research_form"):
    query = st.text_input(
        "🔍 Research Topic",
        placeholder="e.g. Latest AI agent frameworks in 2025",
    )
    recipient_email = st.text_input(
        "📧 Send Report To",
        placeholder="you@example.com",
    )
    submitted = st.form_submit_button("🚀 Start Research", use_container_width=True)

# ── Research pipeline ─────────────────────────────────────────────────────────
if submitted:
    if not query.strip():
        st.error("Please enter a research topic.")
    elif not recipient_email.strip():
        st.error("Please enter a recipient email address.")
    else:
        try:
            report = None
            search_plan = None
            search_results = None

            with st.status("🛠️ Security & Setup…", expanded=True) as status:
                # Step 0 — Security Scan
                status.update(label="🛡️ Running security scan (Llama Guard 3)…")
                guard_result = asyncio.run(run_security_scan(query.strip(), recipient_email.strip()))
                
                if not guard_result.is_safe:
                    status.update(label="⚠️ Security scan failed!", state="error")
                    st.warning(f"🛡️ **Security Alert**: {guard_result.reason}")
                    st.stop()
                
                status.write("✅ Security scan passed.")
                
                # Step 1 — Plan
                status.update(label="🧠 Planning search queries…")
                search_plan = asyncio.run(plan_searches(query.strip()))
                search_queries = [s.query for s in search_plan.searches]
                status.write(
                    f"📋 **Planned {len(search_queries)} searches:**  \n"
                    + "  \n".join(f"• {q}" for q in search_queries)
                )

            # ── Step 1 Result ──
            with st.expander("🧠 Research Strategy (Planner Agent)", expanded=True):
                for q in search_queries:
                    st.markdown(f"- {q}")

            with st.status("Gathering evidence…", expanded=True) as status:
                search_results = asyncio.run(perform_searches(search_plan))
                status.write(f"✅ All {len(search_results)} searches complete.")

            # ── Step 2 Result ──
            with st.expander("📚 Gathered Evidence (Research Agent)", expanded=True):
                for i, result in enumerate(search_results):
                    st.markdown(f"**Source {i+1}:**")
                    st.markdown(result)
                    if i < len(search_results) - 1:
                        st.divider()

            with st.status("Finalizing report…", expanded=True) as status:
                # Step 3 — Write
                status.update(label="✍️ Synthesising results into a report…")
                report = asyncio.run(write_report(query.strip(), list(search_results)))
                status.write("📄 Report ready.")

                # Step 4 — Email
                status.update(label=f"📧 Sending report to {recipient_email.strip()}…")
                asyncio.run(send_report_email(report, recipient_email.strip(), search_plan, search_results))
                status.write(f"✉️ Email delivered to **{recipient_email.strip()}**")

                status.update(label="🎉 Research complete!", state="complete", expanded=False)

            # ── Display results ───────────────────────────────────────────────
            st.success(f"✉️ Full report delivered to **{recipient_email.strip()}**")

            # Executive summary
            st.subheader("📋 Executive Summary")
            st.info(report.short_summary)

            st.divider()

            # Full Markdown report
            st.markdown(report.markdown_report)

            # Follow-up questions
            if report.follow_up_questions:
                st.divider()
                with st.expander("🔎 Follow-Up Questions to Explore", expanded=True):
                    for q in report.follow_up_questions:
                        st.markdown(f"→ {q}")

            st.divider()
            st.caption("Powered by KOMA-BAJE Deep Researcher · OpenRouter · DuckDuckGo · Gmail SMTP")

        except Exception as e:
            st.error(f"❌ **An unexpected error occurred during research**")
            st.info("Check your API keys, network connection, and Gmail credentials in the .env file.")
            with st.expander("Debug details", expanded=False):
                st.code(str(e))
            if st.button("Reset App"):
                st.rerun()
