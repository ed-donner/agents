
import asyncio
from dotenv import load_dotenv
load_dotenv(override=True)

import uvicorn
from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import AgentCapabilities, AgentCard, AgentSkill
from agent_framework.a2a import A2AExecutor
from agent_framework.openai import OpenAIChatCompletionClient

PORT = 9999

# Build the agent
llm_client = OpenAIChatCompletionClient(model="gpt-4o-mini")
travel_agent = llm_client.as_agent(
    name="RemoteTravelAdvisor",
    instructions=(
        "You are a travel advisor. Answer questions about destinations, flights, and trip planning. "
        "Be concise and helpful."
    ),
)

# Describe the service via an AgentCard
agent_card = AgentCard(
    name="Remote Travel Advisor",
    description="A travel advisor agent available over A2A",
    url=f"http://localhost:{PORT}/",
    version="1.0.0",
    defaultInputModes=["text"],
    defaultOutputModes=["text"],
    capabilities=AgentCapabilities(streaming=True),
    skills=[
        AgentSkill(
            id="trip-planning",
            name="Trip Planning",
            description="Help plan trips including flights, hotels, and itineraries",
            tags=["travel", "planning", "flights"],
            examples=["Plan a 5-day trip to Rome", "Best time to visit Japan?"],
        ),
    ],
)

# Wire up executor → request handler → ASGI app
executor = A2AExecutor(travel_agent, stream=True)
handler = DefaultRequestHandler(agent_executor=executor, task_store=InMemoryTaskStore())
app = A2AStarletteApplication(agent_card=agent_card, http_handler=handler).build()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=PORT, log_level="warning")
