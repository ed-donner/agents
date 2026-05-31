"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                ⚠️  EDUCATIONAL USE ONLY ⚠️                                   ║
╚══════════════════════════════════════════════════════════════════════════════╝
DISCLAIMER: This trading agent example is provided for EDUCATIONAL and
DEMONSTRATION purposes ONLY. Built by Samuel Kalu Euclid.
"""

import os
import asyncio
import nest_asyncio
import gradio as gr
import requests
from dotenv import load_dotenv
from agents import Agent, Runner, trace
from agents.mcp import MCPServerStdio

# 1. SETUP - Load .env immediately
nest_asyncio.apply()
load_dotenv(override=True)

# 2. EXTRACT CREDENTIALS
MT5_LOGIN = os.getenv("MT5_LOGIN")
MT5_PASS = os.getenv("MT5_PASSWORD")
MT5_SERVER = os.getenv("MT5_SERVER")
MT5_PATH = os.getenv("MT5_PATH")
PUSHOVER_USER_KEY = os.getenv("PUSHOVER_USER_KEY")
PUSHOVER_API_TOKEN = os.getenv("PUSHOVER_API_TOKEN")

# Pre-flight check: If these are missing in .env, stop here.
if not all([MT5_LOGIN, MT5_PASS, MT5_SERVER]):
    print("❌ ERROR: Missing credentials in .env file! Check MT5_LOGIN, MT5_PASSWORD, and MT5_SERVER.")

# 3. PUSHOVER NOTIFICATION LOGIC
def send_pushover_notification(message):
    if not PUSHOVER_USER_KEY or not PUSHOVER_API_TOKEN:
        print("[-] Pushover keys missing in .env. Skipping notification.")
        return

    try:
        url = "https://api.pushover.net/1/messages.json"
        data = {
            "token": PUSHOVER_API_TOKEN,
            "user": PUSHOVER_USER_KEY,
            "message": message,
            "title": "MT5 Agent Alert"
        }
        response = requests.post(url, data=data, timeout=10)
        if response.status_code == 200:
            print("[+] Pushover notification sent.")
        else:
            print(f"[-] Pushover error: {response.text}")
    except Exception as e:
        print(f"[-] Failed to send Pushover notification: {e}")

# 4. MCP SERVER CONFIGURATION
mcp_params = {
    "command": "uvx",
    "args": [
        "--from", 
        "git+https://github.com/Qoyyuum/mcp-metatrader5-server.git", 
        "mt5mcp"
    ],
    "env": {**os.environ} # Pass all env vars to the MCP process
}

# 5. AGENT DEFINITIONS
async def get_trading_assistant(mcp_server):
    analyst = Agent(
        name="MarketAnalyst",
        instructions=f"""You are the Master MT5 Analyst.
        
        CRITICAL RULE: NEVER ask the user for credentials. They are provided below.
        
        STEP 1: Call 'initialize' using path: "{MT5_PATH}"
        STEP 2: Call 'login' using:
           - login: {MT5_LOGIN}
           - password: "{MT5_PASS}"
           - server: "{MT5_SERVER}"
        
        Once logged in, perform the market analysis or account check requested.""",
        model="gpt-4o-mini",
        mcp_servers=[mcp_server]
    )
    
    manager = Agent(
        name="TradingManager",
        instructions=f"""You are the Autonomous Trading Manager.
        
        DIRECTIVE:
        1. Instruct the MarketAnalyst to login IMMEDIATELY using the credentials in its instructions.
        2. Once the Analyst confirms login, ask it for the account balance or market data.
        3. Do NOT engage in conversation or ask for passwords. Just execute.""",
        model="gpt-4o-mini",
        tools=[
            analyst.as_tool(
                tool_name="MarketAnalysis", 
                tool_description="Executes MT5 logins and retrieves live market/account data."
            )
        ],
        mcp_servers=[mcp_server]
    )
    return manager

# 6. WORKFLOW EXECUTION
async def run_strategy(objective):
    print(f"\n[*] Target Objective: {objective}")
    try:
        async with MCPServerStdio(mcp_params, client_session_timeout_seconds=300) as mt5_server:
            print("[+] MCP Server Online.")
            assistant = await get_trading_assistant(mt5_server)
            
            with trace("Samuel-Kalu-MT5-Live"):
                print("[*] Agent is executing strategy...")
                result = await Runner.run(assistant, objective)
                
                # Send Pushover Notification
                send_pushover_notification(result.final_output)
                
                return result.final_output
                
    except Exception as e:
        error_msg = f"### ❌ System Error\n{str(e)}"
        send_pushover_notification(f"MT5 Agent Error: {str(e)}")
        print(f"[-] System Error: {str(e)}")
        return error_msg

# 7. GRADIO UI
def handle_query(query):
    return asyncio.run(run_strategy(query))

with gr.Blocks(theme=gr.themes.Soft(), title="MT5 Agentic Station") as demo:
    gr.Markdown("# 🤖 Samuel Kalu Euclid - MT5 Agentic Station")
    gr.Markdown("Automatic MetaTrader 5 Bridge with Pushover Notifications")
    
    with gr.Row():
        with gr.Column(scale=2):
            input_text = gr.Textbox(
                label="What should the Agent do?", 
                placeholder="e.g., Get my account balance and equity.",
                lines=4
            )
            submit_btn = gr.Button("⚡ Run Agent Strategy", variant="primary")
        with gr.Column(scale=3):
            output_md = gr.Markdown("### Agent Output\nSystem standby...")
            
    submit_btn.click(handle_query, inputs=input_text, outputs=output_md)

if __name__ == "__main__":
    print("\n" + "="*50)
    print("   🚀 SAMUEL KALU EUCLID - MT5 STATION ONLINE")
    print("   URL: http://127.0.0.1:7860 ")
    print("="*50 + "\n")
    demo.launch(server_name="127.0.0.1", server_port=7860, share=False)
