import streamlit as st
from langchain_core.messages import AIMessage, HumanMessage
from sidekick import Sidekick
import uuid

st.set_page_config(page_title="must_sideKick", page_icon="🦸", layout="wide")

st.title("🦸 must_sideKick Personal Assistant")

# Initialize session state for thread_id and sidekick
if "thread_id" not in st.session_state:
    st.session_state.thread_id = str(uuid.uuid4())

if "sidekick" not in st.session_state:
    st.session_state.sidekick = Sidekick(provider="openrouter", model_name="google/gemini-2.5-pro")

if "messages" not in st.session_state:
    st.session_state.messages = []

# Sidebar for Configuration
with st.sidebar:
    st.header("Settings")
    
    provider_selection = st.selectbox(
        "Model Selection",
        ["OpenRouter (Google Gemini)", "OpenRouter (Qwen)", "Ollama (Local)"]
    )
    
    if provider_selection == "OpenRouter (Google Gemini)":
        provider = "openrouter"
        model_name = "google/gemini-2.5-pro"
        ollama_model = ""
    elif provider_selection == "OpenRouter (Qwen)":
        provider = "openrouter"
        model_name = "qwen/qwen-2.5-72b-instruct"
        ollama_model = ""
    else:
        provider = "ollama"
        ollama_model = st.text_input("Ollama Model Name", value="llama3.2")
        model_name = ollama_model
        
    success_criteria = st.text_area(
        "Success Criteria",
        value="Provide a comprehensive and accurate answer.",
        help="Define what success looks like for your query to help the evaluator."
    )
    
    if st.button("Apply Model & Reset Conversation"):
        st.session_state.thread_id = str(uuid.uuid4())
        st.session_state.messages = []
        st.session_state.sidekick = Sidekick(provider=provider, model_name=model_name)
        st.rerun()

# Display Chat History
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# User Input
if prompt := st.chat_input("What would you like me to do?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        st_placeholder = st.empty()
        final_response = ""
        
        with st.status("Solving your request...", expanded=True) as status_box:
            sidekick = st.session_state.sidekick
            
            try:
                stream = sidekick.run_sync(prompt, success_criteria, st.session_state.thread_id)
                for step in stream:
                    if 'guard' in step:
                        msgs = step['guard'].get('messages', [])
                        if msgs and "🔒 Security Guard" in msgs[-1].content:
                            st.error(msgs[-1].content)
                            final_response = msgs[-1].content
                            
                    elif 'planner' in step:
                        planner_data = step['planner']
                        st.write(f"📝 **Plan Created! Steps:** {len(planner_data.get('plan', []))}")
                        st.write(f"👉 **Current Step:** {planner_data.get('current_step', '')}")
                        
                    elif 'worker' in step:
                        msgs = step['worker'].get('messages', [])
                        if msgs:
                            msg = msgs[-1]
                            if msg.content:
                                final_response = msg.content
                                st.write(f"🛠️ **Worker Output:** {msg.content[:100]}...")
                            if hasattr(msg, "tool_calls") and msg.tool_calls:
                                for tc in msg.tool_calls:
                                    st.write(f"🔧 **Invoking Tool:** `{tc['name']}`")

                    elif 'tools' in step:
                        for t in step['tools'].get('messages', []):
                            with st.expander(f"🔍 Tool Output: {t.name}"):
                                st.text(t.content)
                                
                    elif 'evaluator' in step:
                        eval_data = step['evaluator']
                        st.write(f"⚖️ **Evaluator:** {eval_data.get('feedback_on_work', '')}")
                        if eval_data.get('success_criteria_met'):
                            st.write("✅ **Criteria Met!**")
                        elif eval_data.get('user_input_needed'):
                            st.write("⚠️ **User Input Needed!**")
                            
                status_box.update(label="Complete!", state="complete", expanded=False)
            except Exception as e:
                status_box.update(label="Error occurred", state="error", expanded=True)
                st.error(f"Error: {str(e)}")
                
        if final_response:
            st_placeholder.markdown(final_response)
            st.session_state.messages.append({"role": "assistant", "content": final_response})
