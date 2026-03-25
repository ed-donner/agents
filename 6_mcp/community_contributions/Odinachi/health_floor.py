

from __future__ import annotations

import argparse
import asyncio
import sys

from dotenv import load_dotenv

load_dotenv(override=True)


def main() -> None:
    parser = argparse.ArgumentParser(description="Odinachi health navigator (multi-agent + MCP)")
    parser.add_argument("message", nargs="?", help="User message (stdin if omitted and piped)")
    parser.add_argument(
        "--session",
        default="odinachi_health",
        help="Stem for libsql memory file under Odinachi/memory/",
    )
    args = parser.parse_args()
    if args.message:
        text = args.message
    else:
        if sys.stdin.isatty():
            parser.print_help()
            sys.exit(1)
        text = sys.stdin.read().strip()
    if not text:
        print("Empty message.", file=sys.stderr)
        sys.exit(1)

    async def _run() -> str:
        from health_agents import run_health_navigator

        return await run_health_navigator(text, session_stem=args.session)

    out = asyncio.run(_run())
    print(out)


if __name__ == "__main__":
    main()
