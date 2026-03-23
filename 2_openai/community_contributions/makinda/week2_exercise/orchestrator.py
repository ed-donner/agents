"""
Course creation pipeline (OpenAI Agents SDK).

- Loop: researcher → judge → (fail → repeat | pass → break)
- Sequence: research loop → content builder

Local mode: Runner.run in-process.
Remote mode: HTTP to specialist services (A2A-style), enabled with USE_A2A_REMOTE=1.
"""

from __future__ import annotations

from typing import Any

import httpx
from agents import Runner, trace

from agents_specialists import (
    content_builder_agent,
    judge_agent,
    researcher_agent,
)
from config import (
    CONTENT_BUILDER_BASE_URL,
    JUDGE_BASE_URL,
    MAX_RESEARCH_LOOP_ITERATIONS,
    RESEARCHER_BASE_URL,
    USE_A2A_REMOTE,
)
from schemas import JudgeFeedback


def _research_prompt(topic: str, prior_findings: str | None, judge_feedback: str | None) -> str:
    if not prior_findings:
        return (
            f"User topic / request:\n{topic}\n\n"
            "Research this thoroughly using google_search and produce a rich summary of findings."
        )
    return (
        f"User topic / request:\n{topic}\n\n"
        f"Your prior research summary:\n{prior_findings}\n\n"
        f"The judge rejected this round. Address the following feedback with new searches "
        f"and an improved, more complete summary:\n{judge_feedback}"
    )


def _judge_prompt(topic: str, findings: str) -> str:
    return (
        f"User's original request:\n{topic}\n\n"
        f"Research findings to evaluate:\n{findings}"
    )


def _builder_prompt(topic: str, findings: str) -> str:
    return (
        f"User's original request:\n{topic}\n\n"
        f"Approved research findings:\n{findings}\n\n"
        "Produce the course module in Markdown as specified in your instructions."
    )


async def _invoke_local(agent: Any, user_input: str) -> Any:
    result = await Runner.run(agent, user_input)
    return result.final_output


async def _invoke_remote(client: httpx.AsyncClient, base_url: str, user_input: str) -> Any:
    url = base_url.rstrip("/") + "/a2a/invoke"
    response = await client.post(url, json={"input": user_input}, timeout=120.0)
    response.raise_for_status()
    payload = response.json()
    return payload.get("output")


def _coerce_judge_output(raw: Any) -> JudgeFeedback:
    if isinstance(raw, JudgeFeedback):
        return raw
    if isinstance(raw, dict):
        return JudgeFeedback.model_validate(raw)
    if isinstance(raw, str):
        return JudgeFeedback.model_validate_json(raw)
    raise TypeError(f"Unexpected judge output type: {type(raw)}")


async def run_research_loop(
    topic: str,
    *,
    status_log: list[str] | None = None,
) -> tuple[str, JudgeFeedback]:
    """Run researcher ↔ judge until pass or max iterations."""
    log = status_log if status_log is not None else []

    findings = ""
    last_feedback: JudgeFeedback | None = None

    async with httpx.AsyncClient() as http_client:
        for iteration in range(1, MAX_RESEARCH_LOOP_ITERATIONS + 1):
            log.append(f"[loop] iteration {iteration}/{MAX_RESEARCH_LOOP_ITERATIONS}")

            r_prompt = _research_prompt(
                topic,
                findings or None,
                last_feedback.feedback if last_feedback and last_feedback.status == "fail" else None,
            )
            if USE_A2A_REMOTE:
                out = await _invoke_remote(http_client, RESEARCHER_BASE_URL, r_prompt)
                findings = str(out)
            else:
                findings = str(await _invoke_local(researcher_agent, r_prompt))

            log.append("[researcher] updated findings")

            j_prompt = _judge_prompt(topic, findings)
            if USE_A2A_REMOTE:
                raw_j = await _invoke_remote(http_client, JUDGE_BASE_URL, j_prompt)
                last_feedback = _coerce_judge_output(raw_j)
            else:
                last_feedback = _coerce_judge_output(await _invoke_local(judge_agent, j_prompt))

            log.append(f"[judge] status={last_feedback.status}")

            if last_feedback.status == "pass":
                log.append("[escalation_checker] pass → exit research loop")
                return findings, last_feedback

            log.append("[escalation_checker] fail → continue loop")

    assert last_feedback is not None
    return findings, last_feedback


async def run_course_pipeline(
    topic: str,
    *,
    status_log: list[str] | None = None,
) -> str:
    """Sequential pipeline: research loop → content builder."""
    log = status_log if status_log is not None else []

    with trace("course_creation_pipeline"):
        findings, fb = await run_research_loop(topic, status_log=log)
        log.append(f"[pipeline] research ended with judge status={fb.status}")

        b_prompt = _builder_prompt(topic, findings)
        async with httpx.AsyncClient() as http_client:
            if USE_A2A_REMOTE:
                course = await _invoke_remote(http_client, CONTENT_BUILDER_BASE_URL, b_prompt)
            else:
                course = await _invoke_local(content_builder_agent, b_prompt)

        log.append("[content_builder] course generated")
        return str(course)


def format_log_lines(log: list[str]) -> str:
    return "\n".join(log)
