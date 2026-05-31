"""CLI demo: read a sample file and stream SafePasteManager output."""

import asyncio
import sys
from pathlib import Path

from env_setup import load_repo_env

load_repo_env()


async def _run(path: Path) -> None:
    from orchestrator import SafePasteManager

    text = path.read_text(encoding="utf-8")
    mgr = SafePasteManager()
    async for chunk in mgr.run(text):
        print(chunk)


def main() -> None:
    here = Path(__file__).resolve().parent
    default = here / "sample_inputs" / "clean_traceback.txt"
    path = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else default
    if not path.is_file():
        print(f"File not found: {path}", file=sys.stderr)
        sys.exit(1)
    asyncio.run(_run(path))


if __name__ == "__main__":
    main()
