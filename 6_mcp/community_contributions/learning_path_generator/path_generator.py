"""
Path Generator Agent

Uses Brave Search, Fetch, and Memory MCP servers to dynamically generate
learning paths by searching for resources and compiling them.
"""

import os
from dotenv import load_dotenv
from agents import Agent, Runner, trace, gen_trace_id
from agents.mcp import MCPServerStdio
from contextlib import AsyncExitStack
import json
import asyncio

load_dotenv(override=True)

brave_env = {"BRAVE_API_KEY": os.getenv("BRAVE_API_KEY")}


def get_path_generator_mcp_servers():
    """Get MCP servers for path generation: Brave Search, Fetch, Memory, and Learning Path Server."""
    return [
        {"command": "uvx", "args": ["mcp-server-fetch"]},
        {
            "command": "npx",
            "args": ["-y", "@modelcontextprotocol/server-brave-search"],
            "env": brave_env,
        },
        {
            "command": "npx",
            "args": ["-y", "mcp-memory-libsql"],
            "env": {"LIBSQL_URL": "file:./data/learning_memory.db"},
        },
        {"command": "uv", "args": ["run", "learning_server.py"]},
    ]


async def generate_learning_path(goal: str, level: str = "beginner") -> dict:
    """
    Generate a learning path dynamically by searching for resources.
    
    Args:
        goal: Learning goal (e.g., "Learn Python", "Web Development")
        level: Skill level (beginner, intermediate, advanced)
    
    Returns:
        Dictionary with path_id and generated path
    """
    instructions = f"""You are a learning path generator. Create a structured learning path for: "{goal}" at "{level}" level.

CRITICAL: You MUST complete these steps in order:

STEP 1: Call generate_path tool immediately with goal="{goal}" and level="{level}". This returns a path_id.

STEP 2: Search for learning resources using Brave Search. IMPORTANT: Make only 2-3 strategic searches to avoid rate limits:
- Search 1: "{goal} {level} free course tutorial" (combine terms to get comprehensive results)
- Search 2: "{goal} documentation official" (for official docs)
- Search 3: "{goal} {level} project practice" (for hands-on projects)

If you get a rate limit error, wait a moment and try again, or proceed with the resources you already found.

STEP 3: Organize findings into 5-8 learning steps. Each step needs:
- title: Clear step name
- description: What will be learned
- resources: Array of 2-4 resources, each with: {{"title": "...", "url": "...", "type": "course/tutorial/video/documentation"}}
- estimated_time: e.g., "2-3 hours"

STEP 4: Call update_path_content tool with:
- path_id: from STEP 1
- steps: Your steps array (can be passed as a list directly, or as a JSON string)

STEP 5: Confirm completion by stating the path_id.

IMPORTANT: 
- You MUST call update_path_content before finishing
- Be efficient with searches - combine search terms to reduce API calls
- If rate limited, use the resources you already found and proceed"""

    mcp_server_params = get_path_generator_mcp_servers()

    async with AsyncExitStack() as stack:
        mcp_servers = [
            await stack.enter_async_context(
                MCPServerStdio(params, client_session_timeout_seconds=120)
            )
            for params in mcp_server_params
        ]

        agent = Agent(
            name="path_generator",
            instructions=instructions,
            model="gpt-4o-mini",
            mcp_servers=mcp_servers,
        )

        prompt = f"""Create a learning path for: {goal} at {level} level.

Follow these steps:
1. Call generate_path to create the path structure
2. Search for free learning resources (use 2-3 strategic searches, combine terms to avoid rate limits)
3. Organize into 5-8 steps with resources
4. Call update_path_content with the path_id and steps
5. Confirm the path_id when done

IMPORTANT: If you encounter rate limit errors, proceed with the resources you've already found."""

        # Generate trace ID and use it
        trace_id = gen_trace_id()
        
        with trace("path_generation", trace_id=trace_id):
            print(f"Starting path generation. Trace: https://platform.openai.com/traces/trace?trace_id={trace_id}")
            result = await Runner.run(agent, prompt, max_turns=40)
            print(f"Agent completed. Final output: {result.final_output[:200]}...")

        # Wait a moment for any async operations to complete
        await asyncio.sleep(1)
        
        # Get the most recent path for this goal/level
        from learning_data import get_all_paths
        
        all_paths = get_all_paths()
        latest_path = None
        latest_time = None
        
        for path_id, path in all_paths.items():
            if (path.get('goal', '').lower() == goal.lower() and 
                path.get('level') == level):
                created_at = path.get('created_at', '')
                if not latest_time or created_at > latest_time:
                    latest_time = created_at
                    latest_path = path_id
        
        trace_url = f"https://platform.openai.com/traces/trace?trace_id={trace_id}"
        
        return {
            "path_id": latest_path,
            "result": result.final_output,
            "trace_id": trace_id,
            "trace_url": trace_url
        }


if __name__ == "__main__":
    import asyncio

    # Test the path generator
    async def test():
        result = await generate_learning_path("Learn Python", "beginner")
        print(result)

    asyncio.run(test())

