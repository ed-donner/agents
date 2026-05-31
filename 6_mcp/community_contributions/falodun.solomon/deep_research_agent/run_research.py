from dotenv import load_dotenv
import asyncio
import os
import json

from mcp_client.stdio_client.StdioMCPClient import StdioMCPClient
from mcp_client.manager.MCPClientManager import MCPClientManager
from mcp_client.registry.ToolRegistry import ToolRegistry
from agent.executor.Executor import Executor
from orchestrator.research_loop import ResearchOrchestrator

from agent.synthesizer.OpenAISynthesizer import OpenAISynthesizer
from agent.planner.planner import Planner
from agent.query_refiner.QueryRefiner import QueryRefiner
from agent.reflection.OpenAIReflectionEngine import OpenAIReflectionEngine
from agent.credibility.CredibilityScorer import CredibilityScorer

from openai import OpenAI


# =========================
# MAIN
# =========================
async def main():
    load_dotenv(override=True)


    # =========================
    # WORKING / FAKE SEARCH CLIENT
    # =========================
    class FakeSearchClient:
        async def connect(self): pass
        async def close(self): pass

        async def list_tools(self):
            class Tool:
                name = "search_web"
            return [Tool()]

        async def invoke(self, tool, payload):
            print("[FakeSearch] Query:", payload["query"])
            return {
                "content": [
                    {
                        "title": "LangChain",
                        "link": "https://www.langchain.com"
                    },
                    {
                        "title": "AutoGPT",
                        "link": "https://github.com/Significant-Gravitas/AutoGPT"
                    },
                    {
                        "title": "CrewAI",
                        "link": "https://www.crewai.com"
                    }
                ]
            }

    # =========================
    # MCP SERVER FOR MEMORY
    # =========================
    memory_client = StdioMCPClient({
        "command": "npx",
        "args": ["-y", "mcp-memory-libsql"],
        "env": {
            "LIBSQL_URL": "file:./memory/solomon.db"
        }
    })

    # web search MCP is currently broken. 
    web_client = FakeSearchClient()

    clients = [memory_client, web_client]
    manager = MCPClientManager(clients)

    await manager.connect_all()

    try:
        registry = ToolRegistry(clients)
        await registry.build()

        executor = Executor(registry)

        # =========================
        #  OpenAI CLIENT
        # =========================
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

        def llm(prompt: str):
            print("\n[LLM PROMPT]\n", prompt)

            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2
            )

            content = response.choices[0].message.content

            try:
                return json.loads(content)
            except Exception:
                return content

        tools = list(registry.tool_map.keys())

        query_refiner = QueryRefiner(llm=llm)
        planner = Planner(llm=llm, tools=tools, refiner=query_refiner)
        reflection_engine = OpenAIReflectionEngine()

        orchestrator = ResearchOrchestrator(
            planner=planner,
            executor=executor,
            reflection_engine=reflection_engine,
            credibility_scorer=CredibilityScorer(),
            synthesizer=OpenAISynthesizer(),
        )

        result = await orchestrator.run(
            "Best AI agent frameworks in 2026"
        )

        print("\n=== FINAL RESULT ===")
        print(result)

    finally:
        print("\n[INFO] Shutting down MCP clients...")
        # Explicitly close the connections so background tasks exit cleanly
        await manager.disconnect_all() 
        print("[INFO] Shutdown complete.")

if __name__ == "__main__":
    asyncio.run(main())