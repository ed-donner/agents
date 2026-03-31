from agents import Runner, trace, gen_trace_id
from tools import Tools


class ResearchManager:

    def __init__(self,planner: tuple[str, str] = ("openrouter", "openai/gpt-4o-mini"),search:  tuple[str, str] = ("openai", "gpt-4o-mini"),
        writer:  tuple[str, str] = ("openrouter", "openai/gpt-4o-mini"),
        email:   tuple[str, str] = ("openrouter", "openai/gpt-4o-mini"),
        manager: tuple[str, str] = ("openrouter", "openai/gpt-4o-mini"),
    ):
        self._manager = Tools(
            planner=planner,
            search=search,
            writer=writer,
            email=email,
            manager=manager,
        ).manager_agent
        

    async def run(self, query: str):
        
        
        with trace("Research trace"):

            yield "Starting research pipeline..."
            result = await Runner.run(self._manager, f"Research query: {query}")

            yield "Pipeline complete. Report ready."
            yield result.final_output