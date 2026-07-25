import gradio as gr
import sys
import os
from dotenv import load_dotenv

# Load env before imports that initialize agents
load_dotenv(override=True)

# Add app_agents to path so agents can find each other
current_dir = os.path.dirname(os.path.abspath(__file__))
app_agents_path = os.path.join(current_dir, 'app_agents')
if app_agents_path not in sys.path:
    sys.path.append(app_agents_path)

from app_agents.research_manager import research_manager_agent
from agents import Runner, InputGuardrailTripwireTriggered
from app_agents.query_guardrail import ClarificationQuestions

load_dotenv(override=True)


def _build_agent_input(history: list[dict]) -> str:
    """Flatten the chat history into a single string for the agent."""
    lines = []
    for msg in history:
        role = "User" if msg["role"] == "user" else "Assistant"
        lines.append(f"{role}: {msg['content']}")
    return "\n".join(lines)


async def user_message(message, history):
    """Update history with user message and clear input."""
    if not history:
        history = []
    new_history = history + [{"role": "user", "content": message}]
    return "", new_history


async def chat(history):
    """
    Main chat logic. Streams responses to the chatbot and updates the newsletter panel.
    """
    agent_input = _build_agent_input(history)

    # Add an empty assistant message to history that we will update
    history = history + [{"role": "assistant", "content": ""}]
    
    current_response = ""
    newsletter_md = ""
    call_id_to_tool_name = {}

    try:
        # Run the agent stream
        result = Runner.run_streamed(research_manager_agent, agent_input)

        async for chunk in result.stream_events():
            # 1. Handle Tool Calls for Status Updates
            if chunk.type == "run_item_stream_event" and chunk.name == "tool_called":
                tool_call = chunk.item.raw_item
                # Handle different tool call types (Function, Computer, etc.)
                tool_name = getattr(tool_call, "name", None)
                call_id = getattr(tool_call, "call_id", getattr(tool_call, "id", None))
                
                if tool_name and call_id:
                    call_id_to_tool_name[call_id] = tool_name

                status_msg = ""
                if tool_name == "plan_searches":
                    status_msg = "🔍 Planning searches..."
                elif tool_name == "perform_searches":
                    status_msg = "🌐 Searching the web..."
                elif tool_name == "write_newsletter":
                    status_msg = "✍️ Writing newsletter..."
                elif tool_name and "email" in tool_name.lower():
                    status_msg = "📧 Sending email..."
                
                if status_msg:
                    current_response = status_msg
                    history[-1]["content"] = current_response
                    yield history, newsletter_md

            # 2. Capture Tool Output (Specifically the Newsletter)
            elif chunk.type == "run_item_stream_event" and chunk.name == "tool_output":
                output_item = chunk.item.raw_item
                # FunctionCallOutput is a TypedDict
                call_id = output_item.get("call_id") or output_item.get("id")
                tool_name = call_id_to_tool_name.get(call_id)

                if tool_name == "write_newsletter":
                    output = chunk.item.output
                    # Extract markdown_report from Pydantic model or dict
                    if hasattr(output, "markdown_report"):
                        newsletter_md = output.markdown_report
                    elif isinstance(output, dict) and "markdown_report" in output:
                        newsletter_md = output["markdown_report"]
                    yield history, newsletter_md

            # 3. Handle Regular Assistant Messages
            elif chunk.type == "message":
                # If we were showing a status message, clear it when real text arrives
                if current_response.startswith(("🔍", "🌐", "✍️", "📧")):
                    current_response = ""
                
                current_response += chunk.content
                history[-1]["content"] = current_response
                yield history, newsletter_md

        # 4. Final Fallback if no message was generated
        if not current_response.strip() or current_response.startswith(("🔍", "🌐", "✍️", "📧")):
            current_response = "✅ Research complete — your newsletter has been generated and emailed!"
            history[-1]["content"] = current_response
            yield history, newsletter_md

    except InputGuardrailTripwireTriggered as e:
        clarification: ClarificationQuestions = e.guardrail_result.output.output_info
        questions_md = "\n".join(f"{i+1}. {q}" for i, q in enumerate(clarification.questions))
        history[-1]["content"] = (
            "⚠️ Your query needs more detail. "
            "Please answer the following and resubmit:\n\n"
            + questions_md
        )
        yield history, newsletter_md
    except Exception as e:
        history[-1]["content"] = f"❌ An error occurred: {str(e)}"
        yield history, newsletter_md


with gr.Blocks(theme=gr.themes.Default(primary_hue="sky"), title="Deep Research Newsletter") as ui:
    gr.Markdown("# 📰 Deep Research Newsletter")
    gr.Markdown(
        "Describe a topic to receive a detailed newsletter via email. "
        "The AI will ask for clarification if needed."
    )

    with gr.Row():
        with gr.Column(scale=2):
            chatbot = gr.Chatbot(label="Conversation", height=600, type="messages")
            with gr.Row():
                msg = gr.Textbox(
                    placeholder="Enter your topic or answer follow-up questions...",
                    label="Input",
                    scale=8,
                    lines=2
                )
                submit_btn = gr.Button("Send", variant="primary", scale=2)
            
            clear_btn = gr.Button("🗑️ Clear Conversation")

        with gr.Column(scale=3):
            newsletter_panel = gr.Markdown(
                label="Newsletter", 
                value="*The newsletter will appear here once generated.*"
            )

    # State to manage history
    history_state = gr.State([])

    # Wire up events
    submit_btn.click(
        user_message, [msg, history_state], [msg, history_state]
    ).then(
        chat, [history_state], [chatbot, newsletter_panel]
    )
    
    msg.submit(
        user_message, [msg, history_state], [msg, history_state]
    ).then(
        chat, [history_state], [chatbot, newsletter_panel]
    )

    clear_btn.click(lambda: ([], [], "*The newsletter will appear here once generated.*"), None, [history_state, chatbot, newsletter_panel])

if __name__ == "__main__":
    ui.launch(inbrowser=True)