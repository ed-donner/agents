"""Print Mermaid for the compiled graph (requires full Sidekick.setup() — API keys, Playwright)."""

import asyncio

from sidekick import Sidekick


async def main() -> None:
    sk = Sidekick()
    await sk.setup()
    print(sk.graph.get_graph().draw_mermaid())
    sk.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
