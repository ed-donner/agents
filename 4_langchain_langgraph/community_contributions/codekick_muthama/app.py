import traceback
import gradio as gr
from graph import agent
from orchestrator import run_with_orchestration


def run_agent(user_prompt: str, recursion_limit: int):
    resp = run_with_orchestration(user_prompt, recursion_limit=recursion_limit, agent_kwargs={"temperature": 0})
    # Build a display string:
    if not resp.get("ok"):
        return f"Agent output: {resp.get('agent_raw')}\n\nError: {resp.get('error')}\nTool result: {resp.get('tool_result')}"
    return f"Agent output: {resp.get('agent_raw')}\n\nTool result: {resp.get('tool_result')}"


def build_ui():
    with gr.Blocks(title="Engineering Project Planner") as ui:
        gr.Markdown("## Engineering Project Planner")
        with gr.Row():
            prompt = gr.Textbox(
                lines=2,
                placeholder="Enter your project prompt...",
                label="Project prompt",
                elem_id="query_textbox"
            )
        with gr.Row():
            run_btn = gr.Button("Generate Project", elem_id="run_button")

        recursion = gr.Number(value=100, label="Recursion limit", precision=0)
        output = gr.Textbox(label="Output", interactive=False, lines=22)

        run_btn.click(fn=run_agent, inputs=[prompt, recursion], outputs=output)
        prompt.submit(fn=run_agent, inputs=[prompt, recursion], outputs=output)

        return ui

if __name__ == "__main__":
    app = build_ui()
    app.launch(server_name="127.0.0.1", server_port=7860)
