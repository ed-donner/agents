import asyncio
from github_client import GitHubClientBridge

async def main():
    # Initialize the client bridge
    bridge = GitHubClientBridge()
    
    try:
        # Connect to the GitHub MCP server
        print("Connecting to GitHub MCP server...")
        await bridge.connect()
        print("Successfully connected.")
        
        # Request: "List PRs in repo games"
        # We'll use 'BiprofessionalPrasad' as the owner for the 'games' repository.
        owner = "BiprofessionalPrasad"
        repo = "games"
        
        print(f"\nSending call_tool request: list_prs(owner='{owner}', repo='{repo}')")
        
        # Execute the tool
        result = await bridge.execute_tool(
            tool_name="list_prs",
            arguments={
                "owner": owner,
                "repo": repo,
                "state": "open"
            }
        )
        
        print("\n--- Response from Server ---")
        print(result)
        print("----------------------------")
        
    except Exception as e:
        print(f"An error occurred during interaction: {e}")
    finally:
        # Ensure the connection is closed
        await bridge.disconnect()
        print("\nDisconnected from GitHub MCP server.")

if __name__ == "__main__":
    asyncio.run(main())
