#!/usr/bin/env python3

import asyncio
import json
from typing import List, Dict, Any
from agents.mcp import MCPServerStdio

class RandomDogMCPClient:
    """MCP Client for the Random Dog server"""
    
    def __init__(self):
        self.server_params = {"command": "uv", "args": ["run", "random_dog_server.py"]}
        self.server = None
    
    async def __aenter__(self):
        """Async context manager entry"""
        self.server = MCPServerStdio(params=self.server_params, client_session_timeout_seconds=30)
        await self.server.__aenter__()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.server:
            await self.server.__aexit__(exc_type, exc_val, exc_tb)
    
    async def list_tools(self) -> List:
        """List available tools from the MCP server"""
        if not self.server:
            raise RuntimeError("Client not initialized. Use 'async with' context manager.")
        return await self.server.list_tools()
    
    async def get_random_dog(self) -> Dict[str, Any]:
        """Get a random dog image data"""
        if not self.server:
            raise RuntimeError("Client not initialized. Use 'async with' context manager.")
        return await self.server.call_tool("get_random_dog", {})
    
    async def get_dog_image_url(self) -> str:
        """Get just the URL of a random dog image"""
        if not self.server:
            raise RuntimeError("Client not initialized. Use 'async with' context manager.")
        return await self.server.call_tool("get_dog_image_url", {})

# Example usage functions
async def test_client():
    """Test the MCP client directly"""
    print("🐕 Testing Random Dog MCP Client...")
    
    async with RandomDogMCPClient() as client:
        # List tools
        tools = await client.list_tools()
        print(f"\n📋 Available tools: {[tool.name for tool in tools]}")
        
        # Get random dog data
        dog_data = await client.get_random_dog()
        print(f"\n🐕 Random dog data: {dog_data}")
        
        # Get just the URL
        dog_url = await client.get_dog_image_url()
        print(f"\n🔗 Dog image URL: {dog_url}")

# Utility function to get a simple random dog
async def get_random_dog_simple() -> Dict[str, Any]:
    """Simple utility function to get a random dog"""
    async with RandomDogMCPClient() as client:
        return await client.get_random_dog()

if __name__ == "__main__":
    print("🐕 Random Dog MCP Client Test")
    print("=" * 50)
    
    # Run tests
    asyncio.run(test_client())
    
    print("\n" + "=" * 50)
    print("✅ Random Dog MCP Client tests completed!") 