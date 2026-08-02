import os
import json
from dotenv import load_dotenv
from autogen_ext.runtimes.grpc import GrpcWorkerAgentRuntimeHost
from agent import Agent
from creator import Creator
from autogen_ext.runtimes.grpc import GrpcWorkerAgentRuntime
from autogen_core import AgentId, CancellationToken
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.messages import TextMessage
from autogen_ext.models.openai import OpenAIChatCompletionClient
import messages
import asyncio

load_dotenv(override=True)
openrouter_url = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
openrouter_api_key = os.getenv("OPENROUTER_API_KEY")
idea = "An Agentic AI platform that helps small businesses automate customer support with safe tool use and human escalation."


async def plan_specialists(business_idea):
    try:
        model_client = OpenAIChatCompletionClient(
            base_url=openrouter_url,
            api_key=openrouter_api_key,
            model="gpt-4o-mini",
            temperature=0.4,
        )
        planner = AssistantAgent(
            "Planner",
            model_client=model_client,
            system_message="You decide which specialist agents are needed for a business plan. Reply with JSON only.",
        )
        prompt = (
            "Business idea:\n"
            + business_idea
            + "\n\nPick 3 to 10 specialist agents; each writes one business plan section.\n"
            + 'Return JSON only: {"agents":[{"module_name":"agent_market","role":"...","task_prompt":"..."}, ...]}\n'
            + "module_name must be snake_case and start with agent_."
        )
        response = await planner.on_messages(
            [TextMessage(content=prompt, source="user")],
            cancellation_token=CancellationToken(),
        )
        data = json.loads(response.chat_message.content.strip())
        out = []
        seen = set()
        for a in data.get("agents", []):
            mod = a["module_name"].strip()
            if mod in seen:
                continue
            seen.add(mod)
            out.append((mod, a["role"], a["task_prompt"]))
        if not out:
            raise ValueError("empty agents")
        return out
    except Exception:
        return [
            (
                "agent_market",
                "Market Research Analyst",
                "Write the Market Analysis section. Include target market, competition, and trends.",
            ),
            (
                "agent_product",
                "Product Strategist",
                "Write the Product and Value Proposition section.",
            ),
            (
                "agent_finance",
                "Financial Analyst",
                "Write the Financial Plan section.",
            ),
        ]


async def create_and_message(worker, creator_id, agent_name, role, task_prompt):
    try:
        payload = f"{agent_name}.py||{role}||{task_prompt}"
        result = await worker.send_message(messages.Message(content=payload), creator_id)
        with open(f"{agent_name}.md", "w") as f:
            f.write(result.content)
        return (agent_name, result.content)
    except Exception as e:
        print(f"Failed to run worker {agent_name} due to exception: {e}")
        return (agent_name, "")


async def main():
    host = GrpcWorkerAgentRuntimeHost(address="localhost:50051")
    host.start()
    worker = GrpcWorkerAgentRuntime(host_address="localhost:50051")
    await worker.start()
    section_agents = await plan_specialists(idea)
    result = await Creator.register(worker, "Creator", lambda: Creator("Creator"))
    creator_id = AgentId("Creator", "default")
    coroutines = [
        create_and_message(worker, creator_id, agent_name, role, task_prompt)
        for agent_name, role, task_prompt in section_agents
    ]
    sections = await asyncio.gather(*coroutines)
    parts = []
    for name, content in sections:
        if content.strip():
            parts.append(name + " section:\n" + content)
    if parts:
        blob = "\n\n".join(parts)
        task = (
            "Turn these specialist drafts into one business plan. Use clear headings: "
            "Executive Summary, Problem, Solution, Market Analysis, Product, Go-To-Market, "
            "Operations, Financial Plan, Risks, Next 90 Days.\n\n"
            + blob
        )
        payload = "coordinator.py||Business Plan Coordinator||" + task
        result = await worker.send_message(messages.Message(content=payload), creator_id)
        with open("business_plan.md", "w", encoding="utf-8") as f:
            f.write(result.content)
    try:
        await worker.stop()
        await host.stop()
    except Exception as e:
        print(e)


if __name__ == "__main__":
    asyncio.run(main())
