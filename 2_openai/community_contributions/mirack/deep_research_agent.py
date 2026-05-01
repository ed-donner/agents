

import os
import json
import asyncio
from dotenv import load_dotenv
from agents import Agent, Runner, function_tool, trace
from pydantic import BaseModel

load_dotenv(override=True)

os.environ["OPENAI_AGENTS_DISABLE_TRACING"] = "1"

os.environ["OPENAI_API_KEY"] = os.getenv("API_TOKEN")
os.environ["OPENAI_BASE_URL"] = "https://openrouter.ai/api/v1"


class ClarifyingQuestions(BaseModel):
    questions: list[str]
    reasoning: str

class SourceRating(BaseModel):
    source_name: str
    credibility_score: int  
    tier: str  
    reason: str

class CredibilityReport(BaseModel):
    sources: list[SourceRating]
    overall_source_quality: str 
    warning: str  

class ResearchSection(BaseModel):
    title: str
    content: str
    key_sources: list[str]

class ResearchDraft(BaseModel):
    title: str
    executive_summary: str
    sections: list[ResearchSection]
    all_sources: list[str]
    limitations: str

class EvaluationResult(BaseModel):
    score: int
    is_good_enough: bool
    feedback: str
    missing_areas: list[str]


# Tools

@function_tool
def web_search(query: str) -> str:
    """Search the web for information. Returns results for the given query."""
    return json.dumps({
        "query": query,
        "note": "Using model knowledge. In production, connect to DuckDuckGo or Serper API.",
        "status": "completed"
    })

@function_tool
def save_finding(topic: str, finding: str, source: str, confidence: str) -> str:
    """Save a research finding with its source and confidence level."""
    return json.dumps({
        "saved": True,
        "topic": topic,
        "source": source,
        "confidence": confidence,
        "length": len(finding)
    })

@function_tool
def rate_source(source_name: str, source_type: str) -> str:
    """Rate a source's credibility based on its type and reputation.
    source_type should be one of: peer_reviewed, government, major_news, industry_report,
    blog, social_media, wiki, unknown"""
    tier_map = {
        "peer_reviewed": {"score": 9, "tier": "primary"},
        "government": {"score": 8, "tier": "primary"},
        "major_news": {"score": 7, "tier": "primary"},
        "industry_report": {"score": 7, "tier": "primary"},
        "blog": {"score": 4, "tier": "secondary"},
        "social_media": {"score": 2, "tier": "unreliable"},
        "wiki": {"score": 5, "tier": "secondary"},
        "unknown": {"score": 3, "tier": "unreliable"}
    }
    rating = tier_map.get(source_type, tier_map["unknown"])
    return json.dumps({
        "source": source_name,
        "type": source_type,
        "score": rating["score"],
        "tier": rating["tier"]
    })


# Agents

clarifier = Agent(
    name="Research Clarifier",
    instructions="""Given a research query, come up with exactly 3 clarifying questions
that would help produce more targeted, useful research.

Think about what specific angle, time frame, geography, or depth the user wants.
Return structured output with your questions and reasoning.""",
    output_type=ClarifyingQuestions,
    model="gpt-4o-mini"
)

searcher = Agent(
    name="Research Searcher",
    instructions="""You are a thorough researcher. Given a query and context:

1. Do at least 3 searches with different angles using web_search tool
2. Save key findings with save_finding tool — always include the source name
3. For each source you reference, call rate_source to record its credibility
4. Prefer primary sources (academic papers, government data, major outlets)
5. Be specific — include numbers, dates, names where you can

Always track where your information comes from.""",
    tools=[web_search, save_finding, rate_source],
    model="gpt-4o-mini"
)

writer = Agent(
    name="Research Writer",
    instructions="""Write a structured research report from the findings provided.

Requirements:
- Executive summary: 3-4 sentences, no filler
- 3-5 sections with descriptive titles
- Each section must list its key_sources
- Collect ALL sources mentioned into all_sources list
- Limitations section: be honest about gaps
- Every sentence should add value. Cut anything generic.""",
    output_type=ResearchDraft,
    model="gpt-4o-mini"
)

source_scorer = Agent(
    name="Source Credibility Scorer",
    instructions="""You evaluate the credibility of sources used in a research report.

For each source in the list:
1. Identify what type of source it is (peer_reviewed, government, major_news, industry_report, blog, social_media, wiki, unknown)
2. Give it a credibility score 1-10
3. Classify it as "primary" (score 7+), "secondary" (4-6), or "unreliable" (1-3)
4. Explain briefly why you gave that rating

Then give an overall_source_quality rating:
- "strong" if most sources are primary
- "moderate" if mixed
- "weak" if mostly secondary or unreliable

Add a warning if any unreliable sources were used for key claims.""",
    output_type=CredibilityReport,
    model="gpt-4o-mini"
)

evaluator = Agent(
    name="Research Evaluator",
    instructions="""Evaluate a research report for quality. Score it 1-10.

Check:
- Is the executive summary actually useful? (not just restating the query)
- Are sections substantive with specific details?
- Are sources cited and are they credible?
- Are limitations honestly stated?
- Would a busy professional pay for this report?

Score >= 7 means good enough. If not, give specific actionable feedback.""",
    output_type=EvaluationResult,
    model="gpt-4o-mini"
)


#  Pipeline
async def run_deep_research(query: str, user_context: str = ""):
    """Full pipeline: clarify -> search -> write -> score sources -> evaluate -> revise."""

    log = []

    with trace("Deep Research Pipeline"):

        log.append("[Clarifier] Generating clarifying questions...")
        clarify_result = await Runner.run(clarifier, f"Research query: {query}")
        questions = clarify_result.final_output
        for q in questions.questions:
            log.append(f"  ? {q}")

        enriched = f"Query: {query}\n"
        if user_context:
            enriched += f"User context: {user_context}\n"
        enriched += "Clarifying angles:\n"
        for q in questions.questions:
            enriched += f"- {q}\n"

        log.append("[Searcher] Gathering information...")
        search_result = await Runner.run(searcher, enriched)
        findings = search_result.final_output
        log.append("[Searcher] Done.")

        log.append("[Writer] Writing initial draft...")
        writer_input = f"Query: {query}\n\nFindings:\n{findings}\n\nWrite a comprehensive report."
        draft_result = await Runner.run(writer, writer_input)
        draft = draft_result.final_output
        log.append(f"[Writer] Draft: '{draft.title}' — {len(draft.sections)} sections, {len(draft.all_sources)} sources")

        log.append("[Source Scorer] Rating source credibility...")
        sources_input = f"Rate the credibility of these sources used in a research report:\n{json.dumps(draft.all_sources)}"
        credibility_result = await Runner.run(source_scorer, sources_input)
        credibility = credibility_result.final_output
        log.append(f"[Source Scorer] Overall quality: {credibility.overall_source_quality}")
        for s in credibility.sources:
            emoji = "+" if s.tier == "primary" else "~" if s.tier == "secondary" else "!"
            log.append(f"  {emoji} {s.source_name}: {s.credibility_score}/10 ({s.tier})")
        if credibility.warning:
            log.append(f"  WARNING: {credibility.warning}")

        final_draft = draft
        evaluation = None
        for attempt in range(2):
            log.append(f"[Evaluator] Reviewing (round {attempt + 1})...")

            eval_input = f"""Evaluate this report:
Title: {final_draft.title}
Summary: {final_draft.executive_summary}
Sections: {json.dumps([{"title": s.title, "content": s.content, "sources": s.key_sources} for s in final_draft.sections])}
Limitations: {final_draft.limitations}
Source quality: {credibility.overall_source_quality}
Original query: {query}"""

            eval_result = await Runner.run(evaluator, eval_input)
            evaluation = eval_result.final_output
            log.append(f"[Evaluator] Score: {evaluation.score}/10")

            if evaluation.is_good_enough:
                log.append("[Evaluator] Approved!")
                break

            log.append(f"[Evaluator] Needs work: {evaluation.feedback}")
            log.append("[Writer] Revising...")

            revision_input = f"""Revise this report:
Title: {final_draft.title}
Summary: {final_draft.executive_summary}
Sections: {json.dumps([{"title": s.title, "content": s.content} for s in final_draft.sections])}
Feedback: {evaluation.feedback}
Missing: {evaluation.missing_areas}
Source credibility issues: {credibility.warning}
Query: {query}
Make it more substantive and address the feedback."""

            revised = await Runner.run(writer, revision_input)
            final_draft = revised.final_output
            log.append(f"[Writer] Revised: '{final_draft.title}'")

    return final_draft, questions, credibility, evaluation, log


# Output

def format_report(draft, credibility, evaluation):
    parts = []
    parts.append(f"# {draft.title}\n")
    parts.append(f"## Executive Summary\n{draft.executive_summary}\n")

    for section in draft.sections:
        parts.append(f"## {section.title}\n{section.content}")
        if section.key_sources:
            parts.append(f"*Sources: {', '.join(section.key_sources)}*\n")

    parts.append(f"## Limitations\n{draft.limitations}\n")

   
    parts.append("## Source Credibility Report")
    parts.append(f"**Overall source quality: {credibility.overall_source_quality.upper()}**\n")
    parts.append("| Source | Score | Tier | Reason |")
    parts.append("|--------|-------|------|--------|")
    for s in credibility.sources:
        parts.append(f"| {s.source_name} | {s.credibility_score}/10 | {s.tier} | {s.reason} |")
    if credibility.warning:
        parts.append(f"\n**Warning:** {credibility.warning}")

    parts.append(f"\n---\n*Evaluation score: {evaluation.score}/10*")
    return "\n".join(parts)


# UI

def build_ui():
    import gradio as gr

    async def get_questions(query):
        result = await Runner.run(clarifier, f"Research query: {query}")
        qs = result.final_output.questions
        return "\n".join([f"{i+1}. {q}" for i, q in enumerate(qs)])

    async def run_research(query, user_answers):
        draft, questions, credibility, evaluation, log = await run_deep_research(query, user_answers)
        report = format_report(draft, credibility, evaluation)
        activity = "\n".join(log)
        return report, activity

    with gr.Blocks(title="Deep Research Agent") as app:
        gr.Markdown(
            """
            # Deep Research Agent
            Enter a topic. The agent asks clarifying questions, researches,
            writes a report, scores source credibility, and evaluates its own work.
            """
        )

        with gr.Row():
            with gr.Column(scale=2):
                query_input = gr.Textbox(
                    label="Research Query",
                    placeholder="e.g. What are the biggest risks of deploying AI agents in healthcare?"
                )
                ask_btn = gr.Button("Step 1: Get Clarifying Questions", variant="secondary")
                questions_display = gr.Textbox(label="Clarifying Questions", lines=4, interactive=False)
                user_answers = gr.Textbox(
                    label="Your Answers (optional)",
                    placeholder="Add context or answer the questions...",
                    lines=3
                )
                research_btn = gr.Button("Step 2: Run Deep Research", variant="primary")

            with gr.Column(scale=3):
                report_output = gr.Markdown(label="Research Report")
                log_output = gr.Textbox(label="Agent Activity Log", lines=12, interactive=False)

        ask_btn.click(fn=get_questions, inputs=query_input, outputs=questions_display)
        research_btn.click(fn=run_research, inputs=[query_input, user_answers], outputs=[report_output, log_output])

    return app


if __name__ == "__main__":
    import sys

    if "--ui" in sys.argv:
        app = build_ui()
        app.launch()
    else:
        async def main():
            query = "What are the real challenges companies face when deploying AI agents in production?"
            print(f"Query: {query}\n")

            draft, questions, credibility, evaluation, log = await run_deep_research(query)

            print("\n--- AGENT LOG ---")
            print("\n".join(log))
            print("\n--- REPORT ---")
            print(format_report(draft, credibility, evaluation))

        asyncio.run(main())
