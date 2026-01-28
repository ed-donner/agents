# 🛒 Shopping List MCP Server

A simple MCP (Model Context Protocol) server for managing a shopping list with budget tracking. Includes both a test client and an LLM-powered conversational assistant with **email and SMS notifications**.

## Features

- ✅ Add/remove items with quantities, categories, and prices
- ✅ Track item prices and calculate totals
- ✅ Set and monitor shopping budget
- ✅ Budget warnings (🟢 On track / 🟡 Warning / 🔴 Over budget)
- ✅ Conversational assistant powered by GPT-4.1-mini
- ✅ No external APIs or databases - runs entirely in memory
- ✅ **📧 Email shopping list to spouse (via Resend)**
- ✅ **📱 Text shopping list to mobile (via email gateway)**
- ✅ **🧠 Memory - remembers preferences across sessions**

## File Structure

```
shopping_list_mcp/
├── shopping_list.py       # Core business logic (pure Python)
├── server.py              # MCP server with 6 shopping list tools
├── email_server.py        # MCP server for email (Resend)
├── sms_server.py          # MCP server for SMS (via email gateway)
├── shopping_agent.py      # 🤖 Main assistant (all features)
├── memory/                # 🧠 Persistent memory storage
│   └── shopping.db        # SQLite DB for preferences
├── simple_client.py       # Test client (no LLM)
└── README.md              # This file
```

## Setup

```bash
# Navigate to this directory
cd 6_mcp/community_contributions/shopping_list_mcp

# Required in .env (project root) - choose ONE:
# GOOGLE_API_KEY=your_gemini_key   (recommended - FREE at https://aistudio.google.com/apikey)
# OPENAI_API_KEY=your_openai_key   (alternative)

# Optional for Email + SMS notifications:
# RESEND_API_KEY=your_resend_key   (free at https://resend.com)
```

### LLM Options (All FREE!)

| Provider | API Key | Rate Limits | Get Key |
|----------|---------|-------------|---------|
| **Groq** ⭐ | `GROQ_API_KEY` | 30 req/min | [console.groq.com/keys](https://console.groq.com/keys) |
| Gemini | `GOOGLE_API_KEY` | 15 req/min | [aistudio.google.com/apikey](https://aistudio.google.com/apikey) |
| OpenAI | `OPENAI_API_KEY` | Paid | Fallback only |

**Recommended**: Use **Groq** - fastest, highest rate limits, completely free!

### Resend Free Tier Limitations

⚠️ **Important**: With Resend's free tier:
- ✅ **Email works** to YOUR verified email (the one you signed up with)
- ❌ **SMS won't work** until you verify a custom domain

**To enable SMS** (and send to any email):
1. Go to https://resend.com/domains
2. Add your domain (e.g., `yourdomain.com`)
3. Add the DNS records Resend provides
4. Wait for verification (~5 mins)

## Usage

### Main Assistant (Recommended)
Full-featured assistant with shopping list + email + SMS:

```bash
uv run shopping_agent.py
```

**One agent does everything:**
- "Add milk and bread to my list"
- "Set my budget to $50"
- "What's on my list?"
- "Email my list to spouse@gmail.com"
- "Text my list to 555-123-4567 on Verizon"

### Test Client (No LLM)
Direct tool calls without AI - good for testing:

```bash
uv run simple_client.py
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

