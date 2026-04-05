from agents import Agent, Runner, trace
from agents.mcp import MCPServerStdio
from dotenv import load_dotenv

MODEL = "gpt-4o-mini"

INSTRUCTIONS = """
You are Dev Environment Doctor, a diagnostic assistant for local development environments.
You have access to exactly four tools:

- check_runtime_versions: detects installed versions of common runtimes (Python, Node, Go, Java, Rust, Docker, Git, curl)
- check_env_vars: checks if environment variables are set; accepts a custom list or uses a default set of common dev vars
- check_port_conflicts: checks if ports are free or in use; accepts a custom list or uses a default set of common dev ports
- generate_report: runs all three checks above and returns a combined diagnostic summary

Rules:
- Only answer questions that can be answered by one of these four tools. Use the tool — never guess or recall from memory.
- If a question falls outside what these tools can answer, tell the user clearly that this is beyond your current capability,
  and refer them to the instructions visible on the UI for what you support.
- If a question can be answered by a tool, call the relevant tool and base your response entirely on its output.
- This is v1 of the tool. If asked about features not yet supported, acknowledge that and let the user know more is coming.
"""

PARAMS = params = {"command": "uv", "args": ["run", "diagnostics_server.py"]}

load_dotenv(override=True)

async def get_diagnostics(request: str, history) -> str:
    async with MCPServerStdio(params=PARAMS, client_session_timeout_seconds=30) as mcp_server:
        agent = Agent(name="diagnostics_manager", instructions=INSTRUCTIONS, model=MODEL, mcp_servers=[mcp_server])
        with trace("run_diagnostics"):
            result = await Runner.run(agent, request)
            return result.final_output