# 🛒 Shopping List MCP Server

A simple MCP (Model Context Protocol) server for managing a shopping list with budget tracking. Includes both a test client and an LLM-powered conversational assistant.

## Features

- ✅ Add/remove items with quantities, categories, and prices
- ✅ Track item prices and calculate totals
- ✅ Set and monitor shopping budget
- ✅ Budget warnings (🟢 On track / 🟡 Warning / 🔴 Over budget)
- ✅ Conversational assistant powered by GPT-4.1-mini
- ✅ No external APIs or databases - runs entirely in memory

## File Structure

```
shopping_list_mcp/
├── shopping_list.py      # Core business logic (pure Python)
├── server.py             # MCP server with 6 tools
├── simple_client.py      # Test client (no LLM)
├── shopping_agent.py     # Conversational assistant with GPT
└── README.md             # This file
```

## Setup

```bash
# Navigate to this directory
cd 6_mcp/community_contributions/shopping_list_mcp

# Make sure you have your OpenAI API key in .env (in project root)
# OPENAI_API_KEY=your_key_here
```

## Usage

### Option 1: Test Client (No LLM)
Direct tool calls without AI - good for testing:

```bash
uv run simple_client.py
```

### Option 2: Conversational Assistant (With LLM)
Natural language interface powered by GPT:

```bash
uv run shopping_agent.py
```

## Available MCP Tools

| Tool | Description | Parameters |
|------|-------------|------------|
| `add_item` | Add item to list | name, quantity, category, price |
| `remove_item` | Remove item from list | name |
| `get_list` | Get all items with totals | (none) |
| `set_budget` | Set shopping budget | amount |
| `get_budget_status` | Check budget with warnings | (none) |
| `clear_list` | Remove all items | (none) |

## Example Conversation

```
🛒 Shopping List Assistant
==================================================

🧑 You: Set my budget to $50

🤖 Assistant: I've set your budget to $50.00!

🧑 You: Add milk and eggs

🤖 Assistant: I've added milk and eggs to your shopping list!

🧑 You: The milk was $4.99 and eggs were $5.99

🤖 Assistant: Updated! Your total is now $10.98. 
You have $39.02 remaining. 🟢 You're on track!

🧑 You: What's on my list?

🤖 Assistant: Here's your shopping list:
- Milk (1) - $4.99 - Dairy
- Eggs (1) - $5.99 - Dairy

💰 Total: $10.98 / $50.00 budget

🧑 You: quit

🤖 Assistant: Goodbye! Happy shopping! 🛒
```

## How It Works

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│      User       │     │   GPT-4.1-mini  │     │   MCP Server    │
│                 │     │                 │     │                 │
│ "Add milk"      │ ──▶ │ Understands     │ ──▶ │ add_item()      │
│                 │     │ intent, calls   │     │ executes        │
│                 │ ◀── │ tool, responds  │ ◀── │ returns result  │
└─────────────────┘     └─────────────────┘     └─────────────────┘
```

## Learning Points

This project demonstrates:

1. **MCP Server Basics** - Using `@mcp.tool()` decorator
2. **Singleton Pattern** - Sharing state across tool calls
3. **Type Hints** - How MCP uses them for tool schemas
4. **OpenAI Agents SDK** - Connecting LLMs to MCP tools
5. **Async Python** - Using `async/await` for MCP

## Author

Gandhali Keskar

## License

MIT

