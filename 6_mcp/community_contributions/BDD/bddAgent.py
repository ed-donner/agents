import os
from dotenv import load_dotenv
from agents import Agent, Runner, trace, Tool
from agents.mcp import MCPServerStdio
from IPython.display import Markdown, display
from datetime import datetime
import asyncio, traceback
from pathlib import Path
import re
import anyio

load_dotenv(override=True)

# Setup
current_dir = os.getcwd()
test_results_dir = os.path.join(current_dir, "test-results")
reports_dir = os.path.join(test_results_dir, "reports")
screenshots_dir = os.path.join(test_results_dir, "screenshots")

os.makedirs(reports_dir, exist_ok=True)
os.makedirs(screenshots_dir, exist_ok=True)
    
print("🚀 Starting Full BDD Agent Test")
print(f"📁 Test results: {test_results_dir}\n")

# System prompt for the agent
system_prompt = f"""You are an expert BDD testing engineer with MEMORY of previous scenarios.

## Available Tools:
1. **Browser Automation** (Playwright): browser_navigate, browser_fill_form, browser_press_key, browser_take_screenshot, browser_snapshot, browser_click
2. **Assertions**: assert_equals, assert_contains, assert_not_contains, assert_count, assert_greater_than
3. **Filesystem**: write_file, read_file, list_directory

## Your Task:
Execute the provided Gherkin feature file scenario by scenario, maintaining context across all scenarios.

## Context Memory Rules:
1. **Learn Once, Apply Many**: When you figure out how to do something (e.g., "add a todo"), remember the exact steps
2. **Pattern Matching**: Recognize when new steps match patterns you've already learned
3. **Incremental Knowledge**: Each scenario adds to your understanding of the application
4. **Don't Repeat Discovery**: If you learned "add todo" means "type input + press Enter", don't rediscover it

## Concrete Example:
```gherkin
Scenario 1: Add a new todo item
  When I type the input field "Enter new todo text here" with text "Buy groceries"
  And I press the "Enter" key
  # You learn: "add todo" = specific selectors and actions

Scenario 2: Add multiple todos  
  When I add todo "First task"
  # You apply: Use the pattern from Scenario 1 automatically
  # You know: type the input field "Enter new todo text here" with text + press "Enter"
```

## Execution Standards:
- Execute steps sequentially in each scenario
- If a step fails, capture diagnostic information and continue to next scenario
- Use intelligent selectors (prefer text content, labels, roles over CSS selectors)
- Wait for elements to be ready before interacting with them
- Take screenshots: start of scenario, before actions, after assertions
- Save report after each scenario to: {reports_dir}.
- Use the BDD feature name and current date/time as the filename, in the format:
  "<feature_name>_<YYYYMMDD_HHMMSS>_report.json".
- Before writing:
  1. Use `list_directory` to check if a file with that name already exists.
  2. If it exists, use `read_file` to read the existing JSON.
  3. Parse it as JSON, append the new scenario’s results to the `"scenarios"` array.
  4. Write the updated JSON back using `write_file`.
- If the file does not exist, create a new one with a structure like:
  '''json
  {{
    "feature": "<feature_name>",
    "created_at": "<YYYY-MM-DD HH:MM:SS>",
    "scenarios": [ ... ]
  }}
  '''
- Each report file should contain all scenarios executed for that feature in the same run.
- Ensure all report files are valid JSON and stored under: {reports_dir}.
- Example filename: "Login_20251023_204512_report.json".
- Reuse learned patterns for efficiency
- Pause for 30 seconds between each scenario.
- Handle errors gracefully and provide clear error messages

## Important Notes
- Always verify elements exist before interacting with them
- Use appropriate waits (wait for elements to be visible/enabled)
- Be patient with page loads and dynamic content
- If an assertion fails, mark the step as failed but continue
- The current datetime is {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

Execute with intelligence and memory across all scenarios.
"""

# parameters
mcp_server_params = [
    {"command":"npx", "args":["@playwright/mcp@latest", "--browser", "chromium", "--headless", "--isolated"]},
    {"command":"python", "args":["mcp-servers/assertion-server/assertion_server_python.py"]},
    {"command":"npx", "args":["-y", "@modelcontextprotocol/server-filesystem", test_results_dir]}
]

class BDDAgent:

    def __init__(self, bddPrompt):
        print("Initial BDDAgent")
        self.bdd_prompt = bddPrompt
        print(self.bdd_prompt)


    # BDD Agent
    async def getBddAgent(self, mcp_servers) -> Agent:
        bddAgent = Agent(
            name = "BddAgent",
            instructions=system_prompt,
            model="gpt-4o-mini",
            mcp_servers=mcp_servers
        )

        return bddAgent;


    async def run(self):
        mcp_servers = []
        try:
            # --- Connect to all MCP servers ---
            for i, params in enumerate(mcp_server_params):
                print(f"\nTesting server {i+1}: {params['args']}")
                server = MCPServerStdio(params, client_session_timeout_seconds=600)
                await server.connect()
                mcp_servers.append(server)
                await asyncio.sleep(3.0)
                print("Connected OK!")
            print("\n✅ All MCP servers connected.\n")

            # --- Run the BDD agent ---
            bddAgent = await self.getBddAgent(mcp_servers)
            #with trace("Bdd-Python"):  # ✅ use async context manager
            #    await Runner.run(bddAgent, self.bdd_prompt, max_turns=60)

            max_retries = 5
            retry_delay = 20  # seconds

            for attempt in range(1, max_retries + 1):
                try:
                    with trace("Bdd-Python"):
                        await Runner.run(bddAgent, self.bdd_prompt, max_turns=60)
                    break  # ✅ Success, exit retry loop
                except Exception as e:
                    err_str = str(e)
                    if "rate_limit_exceeded" in err_str or "Error code: 429" in err_str:
                        match = re.search(r"try again in ([\d.]+)s", err_str)
                        if match:
                            retry_delay = float(match.group(1)) + 2
                        else:
                            retry_delay *= 1.5  # exponential backoff
                        print(f"⚠️ Rate limit hit (attempt {attempt}/{max_retries}). Retrying in {retry_delay} seconds...")
                        await asyncio.sleep(retry_delay)
                        continue
                    else:
                        raise  # other errors should bubble up

        except Exception as e:
            print(f"\n❌ Error during execution: {e}")
            traceback.print_exc()

        finally:
            # --- Gracefully close all servers ---
            for s in mcp_servers:
                try:
                    if hasattr(s, "disconnect"):
                        await s.disconnect()
                    elif hasattr(s, "shutdown"):
                        await s.shutdown()
                    await asyncio.sleep(0.5)
                except Exception:
                    traceback.print_exc()

            await asyncio.sleep(5.0)
            print("\n🛑 All MCP servers closed.\n")
      
def ignore_anyio_cancel_error(loop, context):
    msg = context.get("exception")
    if isinstance(msg, RuntimeError) and "Attempted to exit cancel scope" in str(msg):
        return  # swallow it
    loop.default_exception_handler(context)

def load_bdd_prompt(prompt_path) -> str:
    """Load Gerkin prompt"""
    tprompt_path = Path(prompt_path)
    if tprompt_path.exists():
        return tprompt_path.read_text()

    return "";

async def main():
    prompt = load_bdd_prompt("prompt/bdd_prompt2.feature")

    agent = BDDAgent(prompt)
    async with anyio.create_task_group() as tg:
        tg.start_soon(agent.run)
    # Allow background MCP cleanup
    await asyncio.sleep(2.0)

if __name__ == "__main__":
    try:
        #asyncio.get_event_loop().set_exception_handler(ignore_anyio_cancel_error)
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Interrupted by user. Cleaning up...")


#To run: uv run bddAgent.py
