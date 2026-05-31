"""
shopping_agent_notifications.py - Shopping List Assistant with Email & SMS

An enhanced shopping assistant that can:
- Manage your shopping list (add, remove, view items)
- Send the shopping list to your spouse via email (Resend)
- Send the shopping list to mobile via SMS (FREE Email-to-SMS gateway)

Required Environment Variables:
- OPENAI_API_KEY: Your OpenAI API key
- RESEND_API_KEY: Your Resend API key (get free at https://resend.com)
                  This is used for BOTH email AND SMS (via email gateway)

Run with: uv run shopping_agent_notifications.py

Note: SMS uses free email-to-SMS gateways (no Twilio needed!)
      Supported carriers: AT&T, Verizon, T-Mobile, Sprint, Cricket, Metro, Mint, Google Fi
"""
import asyncio
import shutil
import os
from dotenv import load_dotenv
from agents import Agent, Runner, set_tracing_disabled, OpenAIChatCompletionsModel
from agents.mcp import MCPServerStdio
from openai import AsyncOpenAI

# Load environment variables
load_dotenv(override=True)
set_tracing_disabled(True)

# ─────────────────────────────────────────────────────────────
# LLM Configuration
# ─────────────────────────────────────────────────────────────
# Supports: Gemini (free), Groq (free), OpenAI, or custom gateway

GROQ_BASE_URL = "https://api.groq.com/openai/v1"
GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"

groq_api_key = os.getenv("GROQ_API_KEY")
google_api_key = os.getenv("GOOGLE_API_KEY")

def get_llm_model():
    """Get the best available LLM model."""
    
    # Check environment variable for preferred provider
    # Set LLM_PROVIDER=gemini or LLM_PROVIDER=groq to override
    preferred = os.getenv("LLM_PROVIDER", "openai").lower()
    
    # Gemini (FREE but has rate limits)
    if preferred == "gemini" and google_api_key:
        gemini_client = AsyncOpenAI(base_url=GEMINI_BASE_URL, api_key=google_api_key)
        model_name = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
        return OpenAIChatCompletionsModel(model=model_name, openai_client=gemini_client), f"Gemini/{model_name}"
    
    # Groq (FREE, but Llama has tool calling issues)
    if preferred == "groq" and groq_api_key:
        groq_client = AsyncOpenAI(base_url=GROQ_BASE_URL, api_key=groq_api_key)
        model_name = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
        return OpenAIChatCompletionsModel(model=model_name, openai_client=groq_client), f"Groq/{model_name}"
    
    # Standard OpenAI (no gateway needed - just use OPENAI_API_KEY)
    # The agents SDK handles this automatically when model is a string
    return None, None

# ─────────────────────────────────────────────────────────────
# Path Configuration (for notebook/terminal compatibility)
# ─────────────────────────────────────────────────────────────
node_bin_path = os.path.expanduser("~/.nvm/versions/node/v22.11.0/bin")
npx_path = shutil.which("npx") or f"{node_bin_path}/npx"
uv_path = shutil.which("uv") or os.path.expanduser("~/.local/bin/uv")

# Node environment for npx commands
node_env = os.environ.copy()
node_env["PATH"] = f"{node_bin_path}:{node_env.get('PATH', '')}"


async def main():
    """Run the shopping list assistant with Email & SMS capabilities."""
    
    # ─────────────────────────────────────────────────────────────
    # 1. Validate environment variables
    # ─────────────────────────────────────────────────────────────
    
    # Check for LLM API key (Groq > Gemini > OpenAI)
    llm_model, model_display = get_llm_model()
    
    if not llm_model and not os.getenv("OPENAI_API_KEY"):
        print("❌ Missing LLM API key!")
        print("   Add one of these to your .env file (all FREE!):")
        print("   - GROQ_API_KEY   (recommended - https://console.groq.com/keys)")
        print("   - GOOGLE_API_KEY (Gemini - https://aistudio.google.com/apikey)")
        print("   - OPENAI_API_KEY (paid fallback)")
        return
    
    if not llm_model:
        model_display = "GPT-4o"
    print(f"🤖 Using: {model_display}")
    
    # Check for Resend API key (used for BOTH email and SMS via gateway)
    has_resend = bool(os.getenv("RESEND_API_KEY"))
    has_email = has_resend
    has_sms = has_resend  # SMS uses email-to-SMS gateway, so just needs Resend
    
    print("🛒 Shopping List Assistant with Notifications")
    print("=" * 55)
    print(f"📧 Email (Resend):     {'✅ Configured' if has_email else '⚠️  Not configured'}")
    print(f"📱 SMS (Email Gateway): {'✅ Configured (FREE!)' if has_sms else '⚠️  Not configured'}")
    print("=" * 55)
    
    if not has_resend:
        print("\n⚠️  RESEND_API_KEY not configured.")
        print("   Get a free API key at https://resend.com (100 emails/day)")
        print("   This enables both email AND SMS (via free email gateway).")
        print("   Continuing with shopping list only...\n")

    # ─────────────────────────────────────────────────────────────
    # 2. Configure MCP servers
    # ─────────────────────────────────────────────────────────────
    
    # Shopping list server (always enabled)
    shopping_params = {
        "command": uv_path,
        "args": ["run", "server.py"]
    }
    
    # Email server (Resend) - Python-based MCP server
    email_params = None
    if has_email:
        email_params = {
            "command": uv_path,
            "args": ["run", "email_server.py"]
        }
    
    # SMS server - Python-based MCP server
    sms_params = None
    if has_sms:
        sms_params = {
            "command": uv_path,
            "args": ["run", "sms_server.py"]
        }
    
    # Memory server (Knowledge Graph) - persists preferences and history
    # Uses libsql for local storage in ./memory/ directory
    memory_db_path = os.path.join(os.path.dirname(__file__), "memory", "shopping.db")
    os.makedirs(os.path.dirname(memory_db_path), exist_ok=True)
    
    memory_params = {
        "command": npx_path,
        "args": ["-y", "mcp-memory-libsql"],
        "env": {**node_env, "LIBSQL_URL": f"file:{memory_db_path}"}
    }

    # ─────────────────────────────────────────────────────────────
    # 3. Build dynamic instructions based on available services
    # ─────────────────────────────────────────────────────────────
    
    base_instructions = """You are a smart shopping assistant with MEMORY that persists across sessions.

IMPORTANT: You MUST call tools to do anything. Never just respond with text when a tool can do the job.

SHOPPING TOOLS:
- add_item: Add items to shopping list
- remove_item: Remove items
- get_list: View current list
- set_budget: Set budget
- get_budget_status: Check budget
- clear_list: Clear all items

MEMORY TOOLS (use these to remember preferences!):
- create_entities: Store user preferences, favorite items, dietary restrictions
- search_nodes: Find remembered information
- read_graph: View all stored knowledge
- add_observations: Add notes to existing entities
- create_relations: Link related items (e.g., "user" -> "prefers" -> "organic")

MEMORY GUIDELINES:
1. When user mentions preferences ("I'm vegetarian", "I prefer organic"), IMMEDIATELY store with create_entities
2. When creating a new list, FIRST check memory with search_nodes for user preferences
3. Store frequently bought items as entities for quick recall
4. Remember dietary restrictions, allergies, budget preferences

Example entities to create:
- {name: "user_preferences", type: "preferences", observations: ["vegetarian", "prefers organic", "allergic to nuts"]}
- {name: "weekly_staples", type: "item_list", observations: ["milk", "bread", "eggs", "bananas"]}

"""
    
    notification_instructions = ""
    if has_email:
        notification_instructions += """
EMAIL TOOL USAGE:
When user mentions "email" + an email address, you MUST:
1. First call get_list() to get the items
2. Then call send_email() with:
   - to_email: the email address from user's message
   - subject: "🛒 Your Shopping List"  
   - body: Format the items as a nice list like:
     "Shopping List:\\n- Milk (1)\\n- Bread (1)\\n- Eggs (1)\\nTotal: $X.XX"

NEVER ask "should I send?" - just send it immediately!

"""
    
    if has_sms:
        notification_instructions += """
SMS TOOL USAGE:
When user mentions "text" or "sms" + phone number + carrier:
1. Call get_list() to get items
2. Call send_sms() with phone_number, carrier, and message

If carrier missing, ask: "What carrier? (att/verizon/tmobile/mint)"

"""

    behavior_instructions = """
CRITICAL RULES - FOLLOW EXACTLY:

1. NEVER ask for confirmation before sending email/SMS
2. When you see an email address, IMMEDIATELY call send_email
3. When user says "yes" or confirms, that means DO THE LAST REQUESTED ACTION
4. Always call get_list() BEFORE send_email() to get the items

Example - User says "email list to test@gmail.com":
- WRONG: "Would you like me to send...?" 
- RIGHT: Call get_list(), then call send_email(to_email="test@gmail.com", ...)

Example - User says "add milk then email to test@gmail.com":
- Call add_item(name="milk")
- Call get_list()
- Call send_email(to_email="test@gmail.com", ...)
"""

    instructions = base_instructions + notification_instructions + behavior_instructions

    # ─────────────────────────────────────────────────────────────
    # 4. Print usage help
    # ─────────────────────────────────────────────────────────────
    print("\nI can help you manage your shopping list!")
    print("Try saying things like:")
    print("  • 'Add milk and bread to my list'")
    print("  • 'I need 6 apples at $0.50 each'")
    print("  • 'What's on my list?'")
    print("  • 'Set my budget to $40'")
    if has_email:
        print("  • 'Email my list to spouse@example.com'")
    if has_sms:
        print("  • 'Text my list to +1234567890'")
    print("\n🧠 Memory (I remember across sessions!):")
    print("  • 'I'm vegetarian' → Stores your preference")
    print("  • 'Remember my weekly staples: milk, eggs, bread'")
    print("  • 'What do you know about me?'")
    print("  • 'Generate my usual weekly list'")
    print("\nType 'quit' to exit.\n")
    print("-" * 55)

    # ─────────────────────────────────────────────────────────────
    # 5. Connect to MCP servers and run agent
    # ─────────────────────────────────────────────────────────────
    from contextlib import AsyncExitStack
    
    async with AsyncExitStack() as stack:
        mcp_servers = []
        
        # Always connect shopping list server
        shopping_server = await stack.enter_async_context(
            MCPServerStdio(params=shopping_params, client_session_timeout_seconds=30)
        )
        mcp_servers.append(shopping_server)
        shopping_tools = await shopping_server.list_tools()
        print(f"✅ Shopping list server connected ({len(shopping_tools)} tools)")
        
        # Conditionally add email server
        if email_params:
            try:
                email_server = await stack.enter_async_context(
                    MCPServerStdio(params=email_params, client_session_timeout_seconds=30)
                )
                mcp_servers.append(email_server)
                email_tools = await email_server.list_tools()
                print(f"✅ Email server connected ({len(email_tools)} tools: {[t.name for t in email_tools]})")
            except Exception as e:
                print(f"⚠️  Email server failed to connect: {e}")
                has_email = False
        
        # Conditionally add SMS server
        if sms_params:
            try:
                sms_server = await stack.enter_async_context(
                    MCPServerStdio(params=sms_params, client_session_timeout_seconds=30)
                )
                mcp_servers.append(sms_server)
                sms_tools = await sms_server.list_tools()
                print(f"✅ SMS server connected ({len(sms_tools)} tools: {[t.name for t in sms_tools]})")
            except Exception as e:
                print(f"⚠️  SMS server failed to connect: {e}")
                has_sms = False
        
        # Always connect memory server for persistent storage
        try:
            memory_server = await stack.enter_async_context(
                MCPServerStdio(params=memory_params, client_session_timeout_seconds=30)
            )
            mcp_servers.append(memory_server)
            memory_tools = await memory_server.list_tools()
            print(f"✅ Memory server connected ({len(memory_tools)} tools) - DB: {memory_db_path}")
        except Exception as e:
            print(f"⚠️  Memory server failed to connect: {e}")
            print("   Continuing without memory (preferences won't persist)")
        
        # Create the agent with all connected servers
        # Use Groq/Gemini if available, otherwise GPT-4o
        model = llm_model if llm_model else "gpt-4o"
        
        agent = Agent(
            name="shopping_assistant",
            instructions=instructions,
            model=model,
            mcp_servers=mcp_servers
        )
        
        print("\n" + "=" * 55)
        
        # Maintain conversation history for context
        conversation_history = []
        
        # Interactive chat loop
        while True:
            try:
                user_input = input("\n🧑 You: ").strip()
            except (KeyboardInterrupt, EOFError):
                print("\n\nGoodbye! Happy shopping! 🛒")
                break
            
            if user_input.lower() in ['quit', 'exit', 'q', 'bye']:
                print("\n🤖 Assistant: Goodbye! Happy shopping! 🛒")
                break
            
            if not user_input:
                continue
            
            try:
                # Add user message to history
                conversation_history.append({"role": "user", "content": user_input})
                
                # Run with full conversation history (with retry for rate limits)
                result = None
                for attempt in range(3):
                    try:
                        result = await Runner.run(agent, conversation_history)
                        break
                    except Exception as retry_error:
                        if "429" in str(retry_error) or "rate" in str(retry_error).lower():
                            wait_time = 10 * (attempt + 1)
                            print(f"\n⏳ Rate limited. Waiting {wait_time}s... (attempt {attempt+1}/3)")
                            await asyncio.sleep(wait_time)
                        else:
                            raise retry_error
                
                if result is None:
                    raise Exception("Rate limit exceeded after 3 retries. Try again in a minute.")
                
                # Add assistant response to history
                assistant_response = result.final_output
                conversation_history.append({"role": "assistant", "content": assistant_response})
                
                print(f"\n🤖 Assistant: {assistant_response}")
            except Exception as e:
                error_msg = str(e)
                if "429" in error_msg:
                    print(f"\n⏳ Rate limited. Wait ~30 seconds and try again.")
                else:
                    print(f"\n❌ Error: {e}")
                print("Please try again.")
                # Remove failed user message from history
                if conversation_history and conversation_history[-1]["role"] == "user":
                    conversation_history.pop()


if __name__ == "__main__":
    asyncio.run(main())

