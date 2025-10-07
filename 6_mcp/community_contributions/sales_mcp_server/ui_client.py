import asyncio, os, logging

import streamlit as st
from langgraph.prebuilt import create_react_agent
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langgraph.graph.state import CompiledStateGraph
from requests.exceptions import ConnectionError
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

st.title("Sales UI")

load_dotenv(override=True)

# Configuration constants
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise RuntimeError("GEMINI_API_KEY must be set in environment variables (no default).")

MCP_SERVER_URL = os.getenv("MCP_SERVER")
if not MCP_SERVER_URL:
    raise RuntimeError("MCP_SERVER must be set in environment variables.")

def google_agent():
    
    logger.info("Initializing Google agent...")
    
    mcp_server_url = os.getenv('MCP_SERVER')

    model = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash-preview-05-20",
        api_key=os.getenv("GEMINI_API_KEY")
    )

    client = MultiServerMCPClient(
        {
            "Sales Agent Tools Server": {
                "url": mcp_server_url,
                "transport": "streamable_http"
                }
        }
    )

    logger.info("Fetching MCP tools...")
    tools = asyncio.run(client.get_tools())
    logger.info(f"Loaded {len(tools)} MCP tools")

    agent = create_react_agent(model=model, tools=tools)
    logger.info("Agent created successfully")
    return agent

if __name__ == "__main__":


    user_input = st.chat_input("Lets create some emails")
    instructions = """
    You are a Sales Manager at ComplAI. Your goal is to find the single best cold sales email using the sales_agent tools.
    
    Crucial Rule:
    - You must use the sales agent tools to generate a draft — do not write them yourself.
    """

    if 'messages' not in st.session_state:
        st.session_state.messages = [SystemMessage(content=instructions)]


    # display chat messages
    for msg in st.session_state.messages:
        if isinstance(msg, HumanMessage):
            with st.chat_message("user"):
                st.markdown(msg.content)
        elif isinstance(msg, AIMessage):
            with st.chat_message("sales manager"):
                st.markdown(msg.content)


    if user_input:

        if user_input.lower() == "clear history":
            st.session_state.messages = [st.session_state.messages[0]]
        else:

            st.session_state.messages.append(HumanMessage(content=user_input))

            async def run_agent(agent: CompiledStateGraph):

                response = await agent.ainvoke(
                    {'messages': st.session_state.messages}
                )
                return response

            with st.spinner("Generating email..."):
                logger.info(f"User prompt: {user_input}")
                try:
                    loop = asyncio.get_event_loop()
                except RuntimeError:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                result = loop.run_until_complete(run_agent(google_agent()))
                logger.info("Agent responded")
    
            st.session_state.messages.append(result['messages'][-1])

        st.rerun()