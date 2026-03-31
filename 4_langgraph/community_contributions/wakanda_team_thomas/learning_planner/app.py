"""
Gradio UI for the Learning Path Generator.
"""

import sys
sys.stdout.reconfigure(line_buffering=True)
import gradio as gr
from utils import generate_learning_path, clear_outputs, disable_button

EXAMPLE_TOPICS = [
    "LangGraph",
    "Kubernetes",
    "Machine Learning",
    "Docker",
    "React",
    "Python",
    "AWS",
    "GraphQL",
]


with gr.Blocks(
    title="Learning Path Generator",
    theme=gr.themes.Soft(primary_hue="emerald"),
) as ui:
    gr.Markdown("# Learning Path Generator")
    gr.Markdown("*Create personalized learning paths*")
    
    with gr.Group():
        with gr.Row():
            topic_input = gr.Textbox(
                label="What do you want to learn?",
                placeholder="e.g., LangGraph, Kubernetes, Machine Learning",
                scale=3
            )
            gr.Examples(
                examples=[[t] for t in EXAMPLE_TOPICS],
                inputs=[topic_input],
                label="Quick picks"
            )
        
        with gr.Row():
            skill_level = gr.Dropdown(
                label="Current Skill Level",
                choices=["none", "beginner", "intermediate", "advanced"],
                value="beginner"
            )
            time_commitment = gr.Dropdown(
                label="Time Commitment",
                choices=["30min/day", "1hr/day", "2hr/day", "weekends"],
                value="1hr/day"
            )
            email_input = gr.Textbox(
                label="Email (optional - to receive PDF)",
                placeholder="your@email.com"
            )
    
    with gr.Row():
        clear_btn = gr.Button("Clear", variant="secondary")
        run_btn = gr.Button("Generate Learning Path", variant="primary", scale=2)
    
    with gr.Tabs():
        with gr.Tab("Curriculum"):
            curriculum_output = gr.Markdown()
        
        with gr.Tab("Research"):
            research_output = gr.Markdown()
        
        with gr.Tab("Evaluation"):
            eval_output = gr.Markdown()
        
        with gr.Tab("Output Files"):
            output_status = gr.Markdown()
    
    # Event handlers
    run_btn.click(
        disable_button,
        outputs=[run_btn]
    ).then(
        generate_learning_path,
        inputs=[topic_input, skill_level, time_commitment, email_input],
        outputs=[research_output, curriculum_output, eval_output, output_status, run_btn]
    )
    
    clear_btn.click(
        clear_outputs,
        outputs=[topic_input, research_output, curriculum_output, eval_output, output_status]
    )
    
    topic_input.submit(
        disable_button,
        outputs=[run_btn]
    ).then(
        generate_learning_path,
        inputs=[topic_input, skill_level, time_commitment, email_input],
        outputs=[research_output, curriculum_output, eval_output, output_status, run_btn]
    )
    
    gr.Markdown("""**Design by M.T.Gasmyr**""")


if __name__ == "__main__":
    ui.launch()
