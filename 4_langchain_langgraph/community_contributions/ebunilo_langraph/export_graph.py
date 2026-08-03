from __future__ import annotations

import asyncio
from pathlib import Path

from sidekick import Sidekick, bec_tools
from sidekick_tools import build_files_tools, build_research_tools


OUTPUT_PATH = Path(__file__).resolve().parent / "app_graph.mmd"
PNG_OUTPUT_PATH = Path(__file__).resolve().parent / "app_graph.png"


async def main() -> None:
    sidekick = Sidekick()
    # Build only the graph structure; avoid full runtime setup so Playwright is not required.
    sidekick.research_tools = build_research_tools(sidekick._username_getter)
    sidekick.browser_tools = []
    sidekick.files_tools = build_files_tools(sidekick._username_getter)
    sidekick.bec_tools = list(bec_tools)
    await sidekick.build_graph()
    try:
        graph = sidekick.graph.get_graph()
        mermaid = graph.draw_mermaid()
        OUTPUT_PATH.write_text(mermaid, encoding="utf-8")
        graph.draw_mermaid_png(output_file_path=str(PNG_OUTPUT_PATH))
        print(f"Wrote graph to {OUTPUT_PATH}")
        print(f"Wrote graph PNG to {PNG_OUTPUT_PATH}")
    finally:
        sidekick.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
