"""LangGraph job agency: CV review, browser-based job search, evaluator, save + notify."""

import json
from typing import Any, Dict, List, Literal, Optional, TypedDict

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_core.tools import BaseTool
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph
from pydantic import BaseModel, Field
from tools import notify_user, playwright_tools, save_job_results

DEFAULT_MODEL = "gpt-4o-mini"
MIN_MATCH_PERCENT = 80
TARGET_APPROVED_JOBS = 3
DEFAULT_MAX_SEARCH_ATTEMPTS = 5


class Job(BaseModel):
    title: str = Field(description="Job title")
    company: str = Field(description="Company name")
    location: Optional[str] = Field(default=None, description="Location if known")
    description: Optional[str] = Field(
        default=None, description="Short summary of the role"
    )
    url: str = Field(
        description="Exact URL string copied verbatim from a browser ToolMessage (same characters); "
        "if you cannot find that substring in tool output, omit the job"
    )


class JobSearchBatch(BaseModel):
    jobs: List[Job] = Field(description="Distinct job postings found")


class CVReview(BaseModel):
    technical_skills: List[str] = Field(description="Technical skills")
    soft_skills: List[str] = Field(description="Soft skills")
    experience_years: int = Field(description="Estimated years of experience")
    has_bachelors_degree: bool = Field(description="Likely has bachelor's")
    has_masters_degree: bool = Field(description="Likely has master's")
    possible_positions: List[str] = Field(
        description="Roles the candidate could target"
    )
    seniority_level: str = Field(description="e.g. junior, mid, senior, lead")


class JobMatch(BaseModel):
    url: str
    match_percent: int = Field(ge=0, le=100, description="0-100 CV fit score")
    rationale: str = Field(description="Brief justification")


class BatchJobMatch(BaseModel):
    matches: List[JobMatch] = Field(description="One entry per job evaluated")


class JobAgencyState(TypedDict, total=False):
    cv: str
    cv_review: Optional[Dict[str, Any]]
    search_attempt_count: int
    max_search_attempts: int
    candidate_jobs: List[Dict[str, Any]]
    approved_jobs: List[Dict[str, Any]]
    rejected_jobs: List[Dict[str, Any]]
    search_hints: str
    evaluator_notes: str
    final_markdown: str
    output_md_path: str
    output_json_path: str
    terminal_reason: str
    notify_status: str


def _job_key(job: Dict[str, Any]) -> str:
    return (job.get("url") or "").strip().lower()


def _merge_unique_by_url(
    existing: List[Dict[str, Any]], incoming: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    seen = {_job_key(j) for j in existing if _job_key(j)}
    out = list(existing)
    for j in incoming:
        k = _job_key(j)
        if not k or k in seen:
            continue
        seen.add(k)
        out.append(j)
    return out


def _format_jobs_markdown(approved: List[Dict[str, Any]], remark: str) -> str:
    lines = [remark, ""]
    if not approved:
        lines.append("No jobs met the **80%** match threshold.")
        return "\n".join(lines)
    for i, job in enumerate(approved, start=1):
        lines.append(f"## {i}. {job.get('title', 'Role')}")
        lines.append(f"- **Company:** {job.get('company', '')}")
        if job.get("location"):
            lines.append(f"- **Location:** {job['location']}")
        lines.append(f"- **Match:** {job.get('match_percent', '')}%")
        lines.append(f"- **URL:** {job.get('url', '')}")
        if job.get("description"):
            lines.append("")
            lines.append(str(job["description"]))
        lines.append("")
    return "\n".join(lines).strip()


class JobAgencyGraph:
    def __init__(self, model: str = DEFAULT_MODEL):
        self.model = model
        self.llm = ChatOpenAI(model=model, temperature=0)
        self.tools: List[BaseTool] = []
        self.tool_map: Dict[str, BaseTool] = {}
        self.browser = None
        self.playwright = None

    async def setup(self) -> None:
        if self.tools:
            return
        tools, browser, playwright = await playwright_tools()
        self.tools = tools
        self.tool_map = {tool.name: tool for tool in tools}
        self.browser = browser
        self.playwright = playwright

    @classmethod
    async def create(cls, model: str = DEFAULT_MODEL) -> "JobAgencyGraph":
        graph = cls(model=model)
        await graph.setup()
        return graph

    async def cleanup(self) -> None:
        browser, playwright = self.browser, self.playwright
        self.browser = None
        self.playwright = None
        self.tools = []
        self.tool_map = {}
        if browser:
            await browser.close()
        if playwright:
            await playwright.stop()

    def _browser_tool_descriptions(self) -> str:
        if not self.tools:
            return "- Browser tools will be initialized before use."
        descriptions = []
        for tool in self.tools:
            description = " ".join((tool.description or "").split())
            descriptions.append(f"- {tool.name}: {description}")
        return "\n".join(descriptions)

    @staticmethod
    def _normalize_tool_input(args: Any) -> Any:
        if isinstance(args, dict) and "__arg1" in args and len(args) == 1:
            return args["__arg1"]
        return args

    async def _run_tool(self, tool_name: str, tool_args: Any) -> str:
        tool = self.tool_map.get(tool_name)
        if tool is None:
            return f"Unknown tool {tool_name}"
        try:
            result = await tool.ainvoke(self._normalize_tool_input(tool_args))
        except Exception as exc:  # noqa: BLE001
            result = f"{type(exc).__name__}: {exc}"
        return str(result)

    def review_cv(self, state: JobAgencyState) -> Dict[str, Any]:
        cv = (state.get("cv") or "").strip()
        structured = self.llm.with_structured_output(CVReview)
        result: CVReview = structured.invoke(
            [
                SystemMessage(
                    content="You are a CV reviewer. Extract structured facts that will help search for matching jobs."
                ),
                HumanMessage(content=f"CV:\n\n{cv}"),
            ]
        )
        return {"cv_review": result.model_dump()}

    async def search_jobs(self, state: JobAgencyState) -> Dict[str, Any]:
        await self.setup()
        count = int(state.get("search_attempt_count") or 0) + 1
        cv_review = state.get("cv_review") or {}
        hints = (state.get("search_hints") or "").strip()
        approved = state.get("approved_jobs") or []
        rejected = state.get("rejected_jobs") or []

        exclude_urls = {_job_key(j) for j in approved + rejected if _job_key(j)}
        exclude_note = ""
        if exclude_urls:
            sample = list(exclude_urls)[:30]
            exclude_note = (
                "\nDo NOT return these URLs again (already processed):\n"
                + "\n".join(sample)
            )

        system = f"""You are a job scout using browser automation tools to find real job postings on the web.
Use one or more browser tools before producing the final structured list. Aim for up to 10 distinct roles per attempt.
Prefer direct application or careers-page URLs you can verify from browser tool output.

You have no knowledge of job URLs except what appears in browser ToolMessages. Before outputting each job, mentally check that its url is a contiguous substring you could point to in those messages.

Required discovery workflow (Google first, ATS-focused):
1. Start on Google: open `https://www.google.com` or go directly to a search URL like `https://www.google.com/search?q=...` with a URL-encoded query. Do not begin by navigating straight to lever.co, greenhouse.io, or other job-board homepages—use Google to find postings on those domains.
2. Build queries that bias results toward these ATS/careers hosts using `site:` (one domain per query is clearest; you can run several searches per attempt). Target domains: lever.co, greenhouse.io, workday.com, bamboohr.com, workable.com, icims.com, smartrecruiters.com, jazzhr.com, recruitee.com, ashbyhq.com. Example patterns: `site:lever.co software engineer`, `site:greenhouse.io backend remote`, combining role keywords from the candidate profile with location or seniority when helpful.
3. From Google result pages, open only links whose URLs you can later cite verbatim from tool output; follow through to the actual job posting page when the snippet is not enough.
4. Extract page text or links via browser tools as needed. Only keep job URLs that appear exactly in browser ToolMessages.

Available browser tools:
{self._browser_tool_descriptions()}

Rules for the final JobSearchBatch:
- Every url must be copied character-for-character from a browser ToolMessage (including scheme, path, query). No paraphrasing, no "fixing", no completing partial links.
- If you are unsure whether a URL appeared in tool output, omit that job. An empty batch is better than a fabricated link.
- Never use placeholders, example domains, or URLs built from company names.

Current attempt number: {count} of {state.get("max_search_attempts", DEFAULT_MAX_SEARCH_ATTEMPTS)}.
"""
        human = f"""Candidate profile (structured):\n{json.dumps(cv_review, indent=2)[:12000]}

{f"Refinement hints from evaluator: {hints}" if hints else ""}
{exclude_note}

Use Google search with `site:` filters for the listed ATS domains to find roles that fit this profile, then output the final list as structured data."""

        llm_tools = self.llm.bind_tools(self.tools)
        messages: List[BaseMessage] = [
            SystemMessage(content=system),
            HumanMessage(content=human),
        ]
        max_tool_rounds = 12
        for _ in range(max_tool_rounds):
            ai = llm_tools.invoke(messages)
            if not isinstance(ai, AIMessage):
                break
            messages.append(ai)
            tool_calls = getattr(ai, "tool_calls", None) or []
            if not tool_calls:
                break
            for tc in tool_calls:
                name = tc.get("name")
                args = tc.get("args") or {}
                obs = await self._run_tool(str(name), args)
                tid = tc.get("id") or "tool_call"
                messages.append(
                    ToolMessage(content=str(obs)[:15000], tool_call_id=str(tid))
                )

        structured = self.llm.with_structured_output(JobSearchBatch)
        batch: JobSearchBatch = structured.invoke(
            messages
            + [
                HumanMessage(
                    content=(
                        "Output JobSearchBatch: distinct jobs (title, company, location, description, url). "
                        "Scroll back through every browser ToolMessage: each url must appear there as an exact substring. "
                        "If you cannot find it, delete that job from the batch."
                    )
                )
            ]
        )
        candidates = [j.model_dump() for j in batch.jobs]
        filtered = [
            j for j in candidates if _job_key(j) and _job_key(j) not in exclude_urls
        ]

        return {
            "search_attempt_count": count,
            "candidate_jobs": filtered,
        }

    def evaluate_jobs(self, state: JobAgencyState) -> Dict[str, Any]:
        cv = (state.get("cv") or "").strip()
        cv_review = state.get("cv_review") or {}
        candidates = state.get("candidate_jobs") or []
        approved_prev = state.get("approved_jobs") or []
        rejected_prev = state.get("rejected_jobs") or []

        if not candidates:
            notes = (
                "No new candidates this round; broaden queries or try adjacent titles."
            )
            return {
                "evaluator_notes": notes,
                "search_hints": notes,
            }

        structured = self.llm.with_structured_output(BatchJobMatch)
        eval_prompt = f"""You are an evaluator. For each job, score how well the candidate's CV fits (0-100).
Only scores >= {MIN_MATCH_PERCENT} should be treated as strong matches, but you must still score every job.
Be strict: generic postings or weak skill overlap should score below {MIN_MATCH_PERCENT}.

The scout should only use URLs from browser tool output. If a URL looks like a placeholder, template, or unlikely real posting (e.g. wrong domain for the company, obvious pattern fill), score 0 and explain in rationale.

CV text:
{cv[:12000]}

Structured CV review:
{json.dumps(cv_review, indent=2)[:8000]}

Jobs (JSON):
{json.dumps(candidates, indent=2)[:12000]}
"""
        batch: BatchJobMatch = structured.invoke(
            [
                SystemMessage(
                    content="Return BatchJobMatch with one JobMatch per job; copy each job's url exactly into JobMatch.url."
                ),
                HumanMessage(content=eval_prompt),
            ]
        )

        by_url = {m.url.strip().lower(): m for m in batch.matches}

        new_approved: List[Dict[str, Any]] = []
        new_rejected: List[Dict[str, Any]] = []

        for job in candidates:
            key = _job_key(job)
            m = by_url.get(key)
            pct = m.match_percent if m else 0
            enriched = {
                **job,
                "match_percent": pct,
                "match_rationale": (m.rationale if m else "not scored"),
            }
            if pct >= MIN_MATCH_PERCENT:
                new_approved.append(enriched)
            else:
                new_rejected.append(enriched)

        approved = _merge_unique_by_url(approved_prev, new_approved)
        rejected = _merge_unique_by_url(rejected_prev, new_rejected)

        need = max(0, TARGET_APPROVED_JOBS - len(approved))
        hints = (
            f"We still need {need} job(s) with >= {MIN_MATCH_PERCENT}% match. "
            "Search for more specific titles or companies; avoid already-listed URLs."
        )
        if len(new_approved) == 0 and candidates:
            hints += " Last batch had no qualifying matches; try different keywords or locations from the CV review."

        return {
            "approved_jobs": approved,
            "rejected_jobs": rejected,
            "evaluator_notes": hints,
            "search_hints": hints,
        }

    def route_after_eval(
        self, state: JobAgencyState
    ) -> Literal["search_again", "save"]:
        approved = state.get("approved_jobs") or []
        attempts = int(state.get("search_attempt_count") or 0)
        max_a = int(state.get("max_search_attempts") or DEFAULT_MAX_SEARCH_ATTEMPTS)
        if len(approved) >= TARGET_APPROVED_JOBS:
            return "save"
        if attempts >= max_a:
            return "save"
        return "search_again"

    def save_result(self, state: JobAgencyState) -> Dict[str, Any]:
        approved = state.get("approved_jobs") or []
        attempts = int(state.get("search_attempt_count") or 0)
        max_a = int(state.get("max_search_attempts") or DEFAULT_MAX_SEARCH_ATTEMPTS)

        if len(approved) >= TARGET_APPROVED_JOBS:
            reason = f"Found {TARGET_APPROVED_JOBS}+ jobs with >= {MIN_MATCH_PERCENT}% match."
        elif attempts >= max_a:
            reason = f"Stopped after {max_a} search attempts without {TARGET_APPROVED_JOBS} qualifying jobs."
        else:
            reason = "Search complete."

        remark = f"**Status:** {reason}\n\n**Search attempts used:** {attempts}/{max_a}"
        md = _format_jobs_markdown(approved, remark)
        payload = {
            "terminal_reason": reason,
            "search_attempts": attempts,
            "max_search_attempts": max_a,
            "cv_review": state.get("cv_review"),
            "approved_jobs": approved,
            "rejected_jobs": state.get("rejected_jobs") or [],
            "evaluator_notes": state.get("evaluator_notes"),
        }
        md_path, json_path = save_job_results(md, payload)
        msg = f"Job agency: your search is ready. Markdown: {md_path}"
        status = notify_user(msg)
        return {
            "final_markdown": md,
            "output_md_path": str(md_path),
            "output_json_path": str(json_path),
            "terminal_reason": reason,
            "notify_status": status,
        }

    def build(self, checkpointer: Optional[MemorySaver] = None):
        g = StateGraph(JobAgencyState)
        g.add_node("review_cv", self.review_cv)
        g.add_node("search_jobs", self.search_jobs)
        g.add_node("evaluate_jobs", self.evaluate_jobs)
        g.add_node("save_result", self.save_result)

        g.add_edge(START, "review_cv")
        g.add_edge("review_cv", "search_jobs")
        g.add_edge("search_jobs", "evaluate_jobs")
        g.add_conditional_edges(
            "evaluate_jobs",
            self.route_after_eval,
            {"search_again": "search_jobs", "save": "save_result"},
        )
        g.add_edge("save_result", END)
        return g.compile(checkpointer=checkpointer or MemorySaver())


def build_job_agency_graph(checkpointer: Optional[MemorySaver] = None):
    return JobAgencyGraph().build(checkpointer=checkpointer)
