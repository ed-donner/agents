import asyncio
import os
from dotenv import load_dotenv
from huggingface_hub import Agent

# 1. Load the HF_TOKEN from your .env file
load_dotenv()

async def run_agent():
    hf_token = os.getenv("HF_TOKEN")
    
    if not hf_token:
        print("❌ Error: HF_TOKEN not found in .env")
        return

    # 2. Configuration for the MCP Server
    # Note: Use 'http' and the base '/mcp' endpoint for the global HF server
    mcp_servers = [{
        "type": "http", 
        "url": "https://huggingface.co/mcp",
        "headers": {"Authorization": f"Bearer {hf_token}"}
    }]

    print("Agent is ready. Thinking...")

    try:
        # 3. Use 'async with' to manage the lifecycle and prevent UserWarnings
        async with Agent(
            model="Qwen/Qwen2.5-7B-Instruct",
            api_key=hf_token,
            servers=mcp_servers
        ) as agent:
            
            prompt = "Search the Hub for the top 3 trending text-to-video models and give me their names."
            
            # 4. Consume the stream fully
            async for chunk in agent.run(prompt):
                # The agent yields 'AgentMessage' objects. 
                # We want the content specifically.
                if hasattr(chunk, 'content') and chunk.content:
                    print(chunk.content, end="", flush=True)
            
            print("\n\n✅ Task completed.")

    except Exception as e:
        print(f"\n❌ Execution failed: {e}")

if __name__ == "__main__":
    # Standard entry point for async scripts
    asyncio.run(run_agent())