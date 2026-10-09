import streamlit as st
import asyncio
from backend import run_agent_query  # type: ignore

# Streamlit UI Configuration
st.set_page_config(page_title="City Matchmaker", page_icon="🏙️", layout="centered")

st.title("🏙️ The Real Estate City Matchmaker")
st.markdown("I am your personalized AI relocation assistant. Ask me to compare cities, find apartment prices, and rate neighborhood vibes! (Powered by OpenRouter & MCP)")

# Initialize session state for chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display existing chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Capture user input
if prompt := st.chat_input("E.g., Compare moving to Seattle vs Austin with a $2000 budget..."):
    # Render user prompt
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # We use st.spinner so the user knows MCP is booting up and querying in background
    with st.chat_message("assistant"):
        with st.spinner("Connecting to Property MCP Servers & Synthesizing Recommendations..."):
            try:
                # Wrap the asynchronous call inside asyncio.run
                response_text = asyncio.run(run_agent_query(prompt))
                st.markdown(response_text)
                st.session_state.messages.append({"role": "assistant", "content": response_text})
            except Exception as e:
                error_msg = f"Uh oh! An error occurred: {str(e)}"
                st.error(error_msg)
                st.session_state.messages.append({"role": "assistant", "content": error_msg})
