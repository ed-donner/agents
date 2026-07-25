from __future__ import annotations

import argparse
import asyncio
import json

from agent.orchestrator import LinkedInPostAgent
from config.settings import get_settings
from db.repository import get_repository
from ui.state import parse_urls


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)

    draft_parser = subparsers.add_parser("draft")
    draft_parser.add_argument("--topic", required=True)
    draft_parser.add_argument("--goal", required=True)
    draft_parser.add_argument("--notes", default="")
    draft_parser.add_argument("--urls", default="")

    revise_parser = subparsers.add_parser("revise")
    revise_parser.add_argument("--draft-id", required=True)
    revise_parser.add_argument("--feedback", required=True)

    return parser


async def run_async(args: argparse.Namespace) -> dict:
    agent = LinkedInPostAgent()
    if args.command == "draft":
        return await agent.generate_drafts(
            topic=args.topic,
            goal=args.goal,
            notes=args.notes,
            urls=parse_urls(args.urls),
        )
    return await agent.revise_draft(draft_id=args.draft_id, feedback=args.feedback)


def main() -> None:
    settings = get_settings()
    settings.validate_openrouter()
    get_repository().initialize()
    parser = build_parser()
    args = parser.parse_args()
    result = asyncio.run(run_async(args))
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
