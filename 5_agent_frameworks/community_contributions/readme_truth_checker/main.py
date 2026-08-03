"""
README truth checker: structured claims -> tool-grounded verification -> markdown report.

Uses AutoGen AgentChat: structured extraction with on_messages (Lab 2), then
RoundRobinGroupChat for verifier + reporter (Lab 2 teams). Round-robin does not
accept StructuredMessage from group participants, so claims run in a first phase.
"""

from __future__ import annotations

import argparse
import asyncio
from pathlib import Path

from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.conditions import MaxMessageTermination, TextMentionTermination
from autogen_agentchat.messages import TextMessage
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_core import CancellationToken
from autogen_ext.models.openai import OpenAIChatCompletionClient
from dotenv import load_dotenv
from pydantic import BaseModel

from schemas import ClaimBundle
from tools import make_repo_tools

load_dotenv(override=True)


def find_readme(project_root: Path) -> Path:
    for name in ("README.md", "README.MD", "readme.md", "Readme.md"):
        candidate = project_root / name
        if candidate.is_file():
            return candidate
    raise FileNotFoundError(f"No README.md (or variant) found under {project_root}")


def build_claims_agent() -> AssistantAgent:
    model_client = OpenAIChatCompletionClient(model="gpt-4o-mini", temperature=0.1)
    return AssistantAgent(
        name="claims_extractor",
        model_client=model_client,
        output_content_type=ClaimBundle,
        system_message=(
            "You extract checkable factual claims from the README the user sends. "
            "Each claim must be something a verifier can test with directory listings, "
            "file existence, or reading small text files under the repo root. "
            "Do not invent claims that are not grounded in the README text. "
            "Use ids C1, C2, ... in order. "
            "Categories: file_path, command, env_var, dependency, other."
        ),
    )


def build_team(project_root: Path) -> RoundRobinGroupChat:
    project_root = project_root.resolve()
    repo_tools = make_repo_tools(project_root)

    model_client = OpenAIChatCompletionClient(model="gpt-4o-mini", temperature=0.2)

    verifier_agent = AssistantAgent(
        name="filesystem_verifier",
        model_client=model_client,
        tools=repo_tools,
        reflect_on_tool_use=True,
        system_message=(
            "You verify the claims JSON from the user message against the repository. "
            "Use only the provided tools; all paths are relative to the project root. "
            "For each claim id, state PASS, FAIL, or UNKNOWN with a one-line reason and "
            "cite what you observed (e.g. path_exists, list_directory). "
            "If the README mentioned `python main.py`, check whether main.py exists; "
            "you cannot execute commands—only check referenced paths/files. "
            "If a command implies a specific file (e.g. `pip install -r requirements.txt`) "
            "and that file is missing, the claim is FAIL. "
            "Output a markdown table: | id | status | evidence |."
        ),
    )

    reporter_agent = AssistantAgent(
        name="report_editor",
        model_client=model_client,
        system_message=(
            "You produce the final user-facing report in markdown. "
            "Summarize disagreements between the README and the repo, grouped by severity. "
            "Include concrete README edit suggestions (short bullet list). "
            "End your message with the exact line ### README_CHECK_DONE ### when finished."
        ),
    )

    termination = TextMentionTermination("### README_CHECK_DONE ###") | MaxMessageTermination(
        max_messages=20
    )
    return RoundRobinGroupChat(
        [verifier_agent, reporter_agent],
        termination_condition=termination,
        max_turns=10,
    )


def build_verification_task(project_root: Path, claims: ClaimBundle) -> str:
    return f"""Project root (all tool paths are relative to this directory):
{project_root.resolve()}

Extracted claims (JSON, do not re-parse the README for new claims):
{claims.model_dump_json(indent=2)}

Round 1 — filesystem_verifier: verify every claim using tools; output the markdown table.
Round 2 — report_editor: final summary and suggested README fixes; end with the stop token from your system message."""


async def extract_claims(readme_text: str) -> ClaimBundle:
    agent = build_claims_agent()
    msg = TextMessage(
        content=f"README to analyze:\n\n{readme_text}",
        source="user",
    )
    result = await agent.on_messages([msg], cancellation_token=CancellationToken())
    body = result.chat_message.content
    if isinstance(body, ClaimBundle):
        return body
    if isinstance(body, BaseModel):
        return ClaimBundle.model_validate(body.model_dump())
    raise TypeError(f"Expected ClaimBundle, got {type(body)}")


async def run_check(project_root: Path) -> None:
    project_root = project_root.resolve()
    readme_path = find_readme(project_root)
    readme_text = readme_path.read_text(encoding="utf-8", errors="replace")

    print("\n=== Phase 1: structured claims ===\n")
    claims = await extract_claims(readme_text)
    print(claims.model_dump_json(indent=2))

    team = build_team(project_root)
    task = build_verification_task(project_root, claims)
    result = await team.run(task=task)

    print("\n=== Phase 2: verify + report (team transcript) ===\n")
    for message in result.messages:
        body = message.content
        if isinstance(body, BaseModel):
            body = body.model_dump_json(indent=2)
        print(f"**{message.source}**\n{body}\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="Check README claims against repo files (AutoGen AgentChat).")
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parent / "fixtures" / "sample_project",
        help="Path to the project folder containing README.md",
    )
    args = parser.parse_args()
    asyncio.run(run_check(args.root))


if __name__ == "__main__":
    main()
