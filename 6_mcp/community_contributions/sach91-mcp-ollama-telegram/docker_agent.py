from agents import Agent, ModelSettings
from base_model import ollama_model
from dockertool import run_docker

INSTRUCTIONS = (
    "Call docker tool only once and provide the response from the docker.\n"
)


# Get docker response either from tool or mcp server as the agent decides.
def get_docker_agent(mcp_server) -> Agent:
    ts_agent = Agent(
        name="DockerAgent",
        instructions=INSTRUCTIONS,
        model=ollama_model,
        tools=[run_docker],
        mcp_servers=[mcp_server],
        model_settings=ModelSettings(temperature=0),    # tool_choice="required",
    )
    return ts_agent
