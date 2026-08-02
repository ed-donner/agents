import json

import gradio as gr

from model_client import DEFAULT_OPENROUTER_MODEL
from world import run_pipeline_sync


EXAMPLES = [
    [
        "Healthcare operations for small clinics",
        "Clinic owners and front-desk staff",
        "Nigeria and Ghana",
        "Keep the MVP lightweight, B2B, and deployable in under 8 weeks.",
        3,
    ],
    [
        "University admissions and scholarship guidance",
        "High school leavers and admission offices",
        "West Africa",
        "Start with one narrow workflow and avoid building a generic chatbot.",
        3,
    ],
]


def launch_venture_studio(
    problem_area: str,
    target_users: str,
    geography: str,
    constraints: str,
    idea_count: int,
):
    result = run_pipeline_sync(
        problem_area=problem_area,
        target_users=target_users,
        geography=geography,
        constraints=constraints,
        idea_count=idea_count,
    )
    logs = "\n".join(f"- {entry}" for entry in result["logs"])
    artifacts = (
        f"Report: `{result['report_path']}`\n\n"
        f"Evaluation JSON: `{result['evaluation_path']}`\n\n"
        f"Model: `{DEFAULT_OPENROUTER_MODEL}`"
    )
    return (
        result["report"],
        json.dumps(result["evaluation"], indent=2),
        result["research"],
        result["ideas"],
        result["critique"],
        logs,
        artifacts,
    )


with gr.Blocks(title="Igniters Task Week 5") as demo:
    gr.Markdown(
        """
        # Igniters Venture Studio
        A Creator assembles the specialist team,
        the team researches and critiques startup ideas, and an evaluator ranks the final opportunities.
        """
    )

    with gr.Row():
        with gr.Column(scale=1):
            problem_area = gr.Textbox(
                label="Problem Area",
                placeholder="Example: AI workflow support for small clinics",
            )
            target_users = gr.Textbox(
                label="Target Users",
                placeholder="Example: clinic managers, admissions officers, logistics coordinators",
            )
            geography = gr.Textbox(
                label="Geography or Market",
                placeholder="Example: Nigeria, East Africa, remote-first global SMBs",
            )
            constraints = gr.Textbox(
                label="Constraints",
                lines=4,
                placeholder="Example: Must be B2B, low-cost, and possible to build as a narrow MVP.",
            )
            idea_count = gr.Slider(
                label="Number of Ideas",
                minimum=2,
                maximum=5,
                value=3,
                step=1,
            )
            run_button = gr.Button("Run Venture Studio", variant="primary")

        with gr.Column(scale=2):
            final_report = gr.Markdown(label="Final Report")
            evaluation_json = gr.Code(label="Evaluation JSON", language="json")

    with gr.Accordion("Pipeline Detail", open=False):
        artifacts = gr.Markdown(label="Artifacts")
        logs = gr.Markdown(label="Run Log")
        research = gr.Markdown(label="Researcher Output")
        ideas = gr.Markdown(label="Idea Generator Output")
        critique = gr.Markdown(label="Risk Critic Output")

    gr.Examples(
        examples=EXAMPLES,
        inputs=[problem_area, target_users, geography, constraints, idea_count],
    )

    run_button.click(
        fn=launch_venture_studio,
        inputs=[problem_area, target_users, geography, constraints, idea_count],
        outputs=[final_report, evaluation_json, research, ideas, critique, logs, artifacts],
    )


if __name__ == "__main__":
    demo.launch()
