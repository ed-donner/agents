"""
shopping_agent.py - Shopping List Assistant with LLM

Uses OpenAI Agents SDK to create a conversational shopping assistant
that understands natural language and uses MCP tools.

Run with: uv run shopping_agent.py
""" 
import asyncio
import shutil
from dotenv import load_dotenv
from agents import Agent, Runner, set_tracing_disabled
from agents.mcp import MCPServerStdio

# Load environment variables (for OPENAI_API_KEY)
load_dotenv(override=True)
# Disable tracing to avoid the API key warning
set_tracing_disabled(True)

async def main():
    """Run the shopping list assistant with LLM."""
    # ─────────────────────────────────────────────────────────────
    # 1. Configure the MCP server connection
    # ─────────────────────────────────────────────────────────────
    
    # Find uv path (might vary by system)
    uv_path = shutil.which("uv") or "/Users/gkeskar/.local/bin/uv"
    
    params = {
        "command": uv_path,
        "args": ["run", "server.py"]
    }

    # ─────────────────────────────────────────────────────────────
    # 2. Define the agent's personality and capabilities
    # ─────────────────────────────────────────────────────────────
    instructions = """You are a friendly and helpful shopping assistant.
    
Your capabilities:
- Add items to the shopping list (with optional quantities, categories, and prices)
- Remove items from the list
- Show the current shopping list
- Track and manage the shopping budget
- Clear the entire list

Behavior guidelines:
- Be conversational and friendly
- Confirm actions you take (e.g., "I've added milk to your list!")
- If the user mentions a price, include it when adding items
- Use appropriate categories: Produce, Dairy, Meat, Bakery, Pantry, Frozen, Snacks, Beverages, Household
- Proactively check budget status when adding expensive items
- Warn if the user is approaching or over budget

Example interactions:
- "Add milk" → add_item(name="Milk", quantity=1)
- "I need 2 dozen eggs" → add_item(name="Eggs", quantity=2, category="Dairy")
- "Add bread for $3.50" → add_item(name="Bread", price=3.50, category="Bakery")
- "What's on my list?" → get_list()
- "Set my budget to $50" → set_budget(amount=50.0)
- "Am I over budget?" → get_budget_status()
"""
# ─────────────────────────────────────────────────────────────
# 3. Connect to MCP server and create the agent
# ─────────────────────────────────────────────────────────────
    print("🛒 Shopping List Assistant")
    print("=" * 50)
    print("I can help you manage your shopping list!")
    print("Try saying things like:")
    print("  • 'Add milk and bread to my list'")
    print("  • 'I need 6 apples at $0.50 each'")
    print("  • 'What's on my list?'")
    print("  • 'Set my budget to $40'")
    print("  • 'Am I within budget?'")
    print("  • 'Remove the eggs'")
    print("\nType 'quit' to exit.\n")
    print("-" * 50)

# ─────────────────────────────────────────────────────────────
# 4. Create the agent with MCP servers
# ─────────────────────────────────────────────────────────────
    async with MCPServerStdio(params=params, client_session_timeout_seconds=30) as mcp_server:
        print("✅ Connected to MCP server")
    # Create the agent with MCP tools
        agent = Agent(
                name="shopping_assistant",
                instructions=instructions,
                model="gpt-4.1-mini",  # Fast and capable
                mcp_servers=[mcp_server]
            )

        # ─────────────────────────────────────────────────────────
        # 4. Interactive chat loop
        # ─────────────────────────────────────────────────────────
        while True:
            # Get user input
            try:
                user_input = input("\n🧑 You: ").strip()
            except (KeyboardInterrupt, EOFError):
                print("\n\nGoodbye! Happy shopping! 🛒")
                break
            
            # Check for exit
            if user_input.lower() in ['quit', 'exit', 'q', 'bye']:
                print("\n🤖 Assistant: Goodbye! Happy shopping! 🛒")
                break
            
            # Skip empty input
            if not user_input:
                continue
            
            # Run the agent with user's request
            try:
                result = await Runner.run(agent, user_input)
                print(f"\n🤖 Assistant: {result.final_output}")
            except Exception as e:
                print(f"\n❌ Error: {e}")
                print("Please try again.")

if __name__ == "__main__":
    asyncio.run(main())                