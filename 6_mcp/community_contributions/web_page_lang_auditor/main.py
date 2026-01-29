import os
import asyncio
from dotenv import load_dotenv
from agents import Agent, Runner, trace
from agents.mcp import MCPServerStdio

load_dotenv(override=True)

async def main():
    print("Hello from web-lang-auditor MCP!")
    input_dir = os.path.abspath(os.path.join(os.getcwd(), "input"))
    output_dir = os.path.abspath(os.path.join(os.getcwd(), "output"))

    if not os.path.exists(input_dir):
        raise FileNotFoundError(f"Input directory not found: {input_dir}")

    csv_files = [f for f in os.listdir(input_dir) if f.lower().endswith(".csv")]
    if not csv_files:
        raise FileNotFoundError(f"No CSV files found in {input_dir}")
    csv_filename = csv_files[0]  
    print(f"Detected CSV file: {csv_filename}")

    files_params = {
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-filesystem", input_dir, output_dir]
    }

    web_params = {"command": "uv", "args": ["run", "web_lang_auditor_server.py"]}

    async with MCPServerStdio(params=files_params, client_session_timeout_seconds=60) as mcp_server_files:
        async with MCPServerStdio(params=web_params, client_session_timeout_seconds=30) as web_auditor_server:
            instructions = """
                You are an internet investigator. Your task is to audit web pages listed in CSV files.
                Use the MCP tool 'run_web_lang_audit' to process input files located in the input directory.
                Provide only the CSV filename as input, not the full path.
                Save results automatically in the output directory.
            """
            agent = Agent(
                name="web-lang-investigator",
                instructions=instructions,
                model="gpt-4.1-mini",
                mcp_servers=[mcp_server_files, web_auditor_server]
            )
            with trace("web-lang-audit"):
                result = await Runner.run(
                    agent,
                    f"Use the tool 'run_web_lang_audit' to audit '{csv_filename}'"
                )
                print(result.final_output)

if __name__ == "__main__":
    asyncio.run(main())
