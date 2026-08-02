import asyncio
import json
import os
from datetime import datetime
from textwrap import dedent

from autogen_core import AgentId, SingleThreadedAgentRuntime

import messages
from creator import Creator
from evaluator_agent import EvaluatorAgent


TEAM_CREATION_MESSAGE = "create_venture_team"


def _project_dir() -> str:
    return os.path.dirname(os.path.abspath(__file__))


def _output_dir() -> str:
    output_dir = os.path.join(_project_dir(), "output")
    os.makedirs(output_dir, exist_ok=True)
    return output_dir


def _append_log(logs: list[str], message: str) -> None:
    logs.append(message)


def _build_user_brief(
    problem_area: str,
    target_users: str,
    geography: str,
    constraints: str,
    idea_count: int,
) -> str:
    return dedent(
        f"""
        Product brief:
        - Problem area: {problem_area}
        - Target users: {target_users}
        - Geography or market: {geography}
        - Constraints: {constraints}
        - Number of startup ideas required: {idea_count}

        Focus on agentic AI opportunities. Prefer sharp, buildable MVPs over broad generic platforms.
        """
    ).strip()


def _build_report(
    *,
    brief: str,
    research: str,
    ideas: str,
    critique: str,
    evaluation: dict,
    run_timestamp: str,
) -> str:
    ranked_rows = []
    for item in evaluation.get("ranked_ideas", []):
        ranked_rows.append(
            f"| {item['rank']} | {item['idea_name']} | {item['score']} | {item['business_model']} | {item['key_risk']} |"
        )

    execution_plan = "\n".join(f"{index}. {step}" for index, step in enumerate(evaluation["execution_plan"], start=1))
    winning_idea = evaluation["winning_idea"]

    return dedent(
        f"""
        # Venture Studio Report

        Generated at: {run_timestamp}

        ## User Brief
        {brief}

        ## Market Research
        {research}

        ## Draft Startup Ideas
        {ideas}

        ## Risk Review
        {critique}

        ## Final Recommendation
        **Winner:** {winning_idea['idea_name']}

        **Why it wins:** {winning_idea['why_it_wins']}

        **MVP scope:** {winning_idea['mvp_scope']}

        **Best launch user:** {winning_idea['target_launch_user']}

        ## Ranked Ideas
        | Rank | Idea | Score | Business Model | Key Risk |
        | --- | --- | --- | --- | --- |
        {"".join(f"{row}\n" for row in ranked_rows)}

        ## Execution Plan
        {execution_plan}

        ## Executive Summary
        {evaluation['executive_summary']}
        """
    ).strip()


def _write_artifacts(report: str, evaluation: dict) -> tuple[str, str]:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = _output_dir()
    report_path = os.path.join(output_dir, f"venture_report_{timestamp}.md")
    evaluation_path = os.path.join(output_dir, f"venture_evaluation_{timestamp}.json")
    with open(report_path, "w", encoding="utf-8") as handle:
        handle.write(report)
    with open(evaluation_path, "w", encoding="utf-8") as handle:
        json.dump(evaluation, handle, indent=2)
    return report_path, evaluation_path


async def run_pipeline(
    *,
    problem_area: str,
    target_users: str,
    geography: str,
    constraints: str,
    idea_count: int = 3,
) -> dict:
    runtime = SingleThreadedAgentRuntime()
    logs: list[str] = []
    brief = _build_user_brief(
        problem_area=problem_area,
        target_users=target_users,
        geography=geography,
        constraints=constraints,
        idea_count=idea_count,
    )

    await Creator.register(runtime, "Creator", lambda: Creator("Creator"))
    await EvaluatorAgent.register(runtime, "Evaluator", lambda: EvaluatorAgent("Evaluator"))
    runtime.start()

    try:
        creator_id = AgentId("Creator", "default")

        _append_log(logs, "Creator is assembling the specialist venture team.")
        team_result = await runtime.send_message(messages.Message(content=TEAM_CREATION_MESSAGE), creator_id)
        _append_log(logs, str(team_result.content))

        researcher_prompt = dedent(
            f"""
            Use the brief below to produce a market research memo.
            Return a concise but useful markdown report with these sections:
            1. Core pain points
            2. Current alternatives
            3. Why now
            4. Gaps in the market
            5. Opportunity angle for an agentic AI startup

            {brief}
            """
        ).strip()
        _append_log(logs, "Researcher is mapping customer pain, alternatives, and market gaps.")
        researcher_result = await runtime.send_message(
            messages.Message(content=researcher_prompt),
            AgentId("Researcher", "default"),
        )
        research = str(researcher_result.content)

        idea_prompt = dedent(
            f"""
            Use the brief and research below to propose exactly {idea_count} startup ideas.
            Return markdown. For each idea include:
            - Name
            - One-line summary
            - Customer
            - Product workflow
            - Monetization
            - Why this is an agentic AI business
            - Narrow MVP

            USER BRIEF
            {brief}

            RESEARCH
            {research}
            """
        ).strip()
        _append_log(logs, "IdeaGenerator is turning the research into focused startup concepts.")
        idea_result = await runtime.send_message(
            messages.Message(content=idea_prompt),
            AgentId("IdeaGenerator", "default"),
        )
        ideas = str(idea_result.content)

        critic_prompt = dedent(
            f"""
            Review the startup ideas below like a skeptical operator.
            Return markdown with one section per idea.
            For each idea include:
            - Main strength
            - Biggest hidden assumption
            - Go-to-market risk
            - Build risk
            - Suggested refinement to improve the MVP

            USER BRIEF
            {brief}

            RESEARCH
            {research}

            IDEAS
            {ideas}
            """
        ).strip()
        _append_log(logs, "RiskCritic is pressure-testing the concepts and narrowing the MVPs.")
        critic_result = await runtime.send_message(
            messages.Message(content=critic_prompt),
            AgentId("RiskCritic", "default"),
        )
        critique = str(critic_result.content)

        evaluator_prompt = dedent(
            f"""
            Evaluate the following venture studio outputs and rank the ideas.
            Use the structured schema exactly.

            USER BRIEF
            {brief}

            RESEARCH
            {research}

            IDEAS
            {ideas}

            RISK REVIEW
            {critique}
            """
        ).strip()
        _append_log(logs, "Evaluator is ranking the ideas and selecting the best one to build.")
        evaluation_result = await runtime.send_message(
            messages.Message(content=evaluator_prompt),
            AgentId("Evaluator", "default"),
        )
        evaluation = json.loads(str(evaluation_result.content))

        run_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        report = _build_report(
            brief=brief,
            research=research,
            ideas=ideas,
            critique=critique,
            evaluation=evaluation,
            run_timestamp=run_timestamp,
        )
        report_path, evaluation_path = _write_artifacts(report, evaluation)
        _append_log(logs, "Artifacts written to the output folder.")

        return {
            "brief": brief,
            "research": research,
            "ideas": ideas,
            "critique": critique,
            "evaluation": evaluation,
            "report": report,
            "logs": logs,
            "report_path": report_path,
            "evaluation_path": evaluation_path,
        }
    finally:
        await runtime.stop()
        await runtime.close()


def run_pipeline_sync(
    *,
    problem_area: str,
    target_users: str,
    geography: str,
    constraints: str,
    idea_count: int = 3,
) -> dict:
    return asyncio.run(
        run_pipeline(
            problem_area=problem_area,
            target_users=target_users,
            geography=geography,
            constraints=constraints,
            idea_count=idea_count,
        )
    )
