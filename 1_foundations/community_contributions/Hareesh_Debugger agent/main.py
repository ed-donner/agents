import gradio as gr
from agent import DebugAgent

agent = DebugAgent()

def start_debugging(buggy_code):
    # agent.run returns (report_text, count)
    report_text, count = agent.run(buggy_code)
    
    with open("sandbox.py", "r") as f:
        fixed_code = f.read()
        
    stats = f"## 🚀 Mission Accomplished\n**Autonomous Loops Required:** {count}"
    return fixed_code, stats, report_text

with gr.Blocks(theme=gr.themes.Soft(primary_hue="indigo")) as demo:
    gr.Markdown("# 🤖 Autonomous Debugger")
    gr.Markdown("An LLM-driven system that independently executes, observes, and corrects code in a recursive loop.")
    
    with gr.Row():
        with gr.Column(scale=1):
            input_code = gr.Code(label="Buggy Input", language="python", lines=12, value=open("sandbox.py").read())
            run_btn = gr.Button("Start Debugging Loop", variant="primary")
            loop_display = gr.Markdown()
            
        with gr.Column(scale=1):
            output_code = gr.Code(label="Final Verified Code", language="python", lines=12)
            # Accordion makes the UI look clean but professional
            with gr.Accordion("Agent Reasoning Log (The 'Thought' Process)", open=True):
                report_display = gr.Markdown()

    run_btn.click(
        fn=start_debugging, 
        inputs=[input_code], 
        outputs=[output_code, loop_display, report_display]
    )

demo.launch()