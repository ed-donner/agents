"""
Gradio UI for the Learning Path Generator.
Tool testing mode - testing each node as we build.
"""

import sys
sys.stdout.reconfigure(line_buffering=True)

import gradio as gr
from nodes.researcher import ResearcherNode
from nodes.curriculum_builder import CurriculumBuilderNode
from nodes.evaluator import EvaluatorNode

print("Starting Learning Planner - Node Testing...")

researcher = ResearcherNode()
curriculum_builder = CurriculumBuilderNode()
evaluator = EvaluatorNode()


def test_full_chain(
    topic: str,
    skill_level: str,
    time_commitment: str,
) -> tuple[str, str, str]:
    """Test the full chain: Researcher → Curriculum Builder → Evaluator."""
    if not topic.strip():
        return "Please enter a topic.", "", ""
    
    state = {
        "topic": topic,
        "current_skill_level": skill_level,
        "time_commitment": time_commitment,
        "messages": [],
        "prerequisites": [],
        "key_concepts": [],
        "research_summary": "",
        "curriculum": None,
        "evaluation_feedback": None,
        "is_complete": False,
        "needs_user_input": False,
    }
    
    research_result = researcher.execute(state)
    state["prerequisites"] = research_result["prerequisites"]
    state["key_concepts"] = research_result["key_concepts"]
    state["research_summary"] = research_result["research_summary"]
    
    curriculum_result = curriculum_builder.execute(state)
    state["curriculum"] = curriculum_result["curriculum"]
    
    eval_result = evaluator.execute(state)
    
    research_output = f"""**Prerequisites:**
{chr(10).join([f"- {p}" for p in state["prerequisites"]])}

**Key Concepts:**
{chr(10).join([f"- {c}" for c in state["key_concepts"]])}
"""

    curriculum = state["curriculum"]
    curriculum_output = f"""## {topic} Learning Path

**Overview:** {curriculum.overview}

**Duration:** {curriculum.total_estimated_days} days

---

"""
    for m in curriculum.milestones:
        curriculum_output += f"""### Phase {m.phase_number}: {m.title}
**Goal:** {m.goal}

{m.description}

**Resources:**
"""
        for r in m.resources:
            curriculum_output += f"- [{r.title}]({r.url}) ({r.type})\n"
        
        if m.project_idea:
            curriculum_output += f"\n**Project:** {m.project_idea}\n"
        curriculum_output += f"\n*Duration: {m.estimated_days} days*\n\n---\n\n"

    status_icon = "✅" if eval_result["is_complete"] else "⚠️"
    eval_output = f"""{status_icon} **Status:** {"Approved" if eval_result["is_complete"] else "Needs Revision"}

**Feedback:**
{eval_result["evaluation_feedback"]}

**Needs User Input:** {"Yes" if eval_result["needs_user_input"] else "No"}
"""

    return research_output, curriculum_output, eval_output


with gr.Blocks(title="Learning Planner - Node Testing") as ui:
    gr.Markdown("## Node Testing: Full Chain")
    gr.Markdown("Researcher → Curriculum Builder → Evaluator")
    
    with gr.Row():
        topic_input = gr.Textbox(
            label="Topic",
            placeholder="e.g., LangGraph, Kubernetes, Machine Learning"
        )
    with gr.Row():
        with gr.Column():
            skill_level = gr.Dropdown(
                label="Current Skill Level",
                choices=["none", "beginner", "intermediate", "advanced"],
                value="beginner"
            )
        with gr.Column():
            time_commitment = gr.Dropdown(
                label="Time Commitment",
                choices=["30min/day", "1hr/day", "2hr/day", "weekends"],
                value="1hr/day"
            )
    with gr.Row():
        run_btn = gr.Button("Generate & Evaluate", variant="primary")
    
    with gr.Row():
        with gr.Column(scale=1):
            research_output = gr.Markdown(label="Research")
        with gr.Column(scale=2):
            curriculum_output = gr.Markdown(label="Curriculum")
        with gr.Column(scale=1):
            eval_output = gr.Markdown(label="Evaluation")
    
    run_btn.click(
        test_full_chain,
        inputs=[topic_input, skill_level, time_commitment],
        outputs=[research_output, curriculum_output, eval_output]
    )


if __name__ == "__main__":
    ui.launch()
