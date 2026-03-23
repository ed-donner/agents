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
from nodes.markdown_writer import MarkdownWriterNode
from nodes.pdf_writer import PDFWriterNode
from nodes.notifier import NotifierNode

print("Starting Learning Planner - Node Testing...")

researcher = ResearcherNode()
curriculum_builder = CurriculumBuilderNode()
evaluator = EvaluatorNode()
markdown_writer = MarkdownWriterNode()
pdf_writer = PDFWriterNode()
notifier = NotifierNode()


def test_full_chain(
    topic: str,
    skill_level: str,
    time_commitment: str,
    user_email: str,
) -> tuple[str, str, str, str]:
    """Test the full chain: Research → Build → Evaluate → Write → Notify."""
    if not topic.strip():
        return "Please enter a topic.", "", "", ""
    
    state = {
        "topic": topic,
        "current_skill_level": skill_level,
        "time_commitment": time_commitment,
        "user_email": user_email.strip() if user_email else "",
        "messages": [],
        "prerequisites": [],
        "key_concepts": [],
        "research_summary": "",
        "curriculum": None,
        "evaluation_feedback": None,
        "is_complete": False,
        "needs_user_input": False,
        "markdown_content": None,
        "markdown_path": None,
        "pdf_path": None,
        "notification_status": None,
        "notification_sent": False,
    }
    
    # Step 1: Research
    research_result = researcher.execute(state)
    state["prerequisites"] = research_result["prerequisites"]
    state["key_concepts"] = research_result["key_concepts"]
    state["research_summary"] = research_result["research_summary"]
    
    # Step 2: Build Curriculum
    curriculum_result = curriculum_builder.execute(state)
    state["curriculum"] = curriculum_result["curriculum"]
    
    # Step 3: Evaluate
    eval_result = evaluator.execute(state)
    state["is_complete"] = eval_result["is_complete"]
    
    # Step 4, 5, 6: Write Markdown, PDF & Send Email (only if approved)
    output_status = ""
    if eval_result["is_complete"]:
        # Markdown
        md_result = markdown_writer.execute(state)
        state["markdown_content"] = md_result["markdown_content"]
        state["markdown_path"] = md_result["markdown_path"]
        
        # PDF
        pdf_result = pdf_writer.execute(state)
        state["pdf_path"] = pdf_result["pdf_path"]
        
        output_status = f"""✅ **Files Generated:**

- **Markdown:** `{state['markdown_path']}`
- **PDF:** `{state['pdf_path']}`
"""
        
        # Notify (if email provided)
        if state["user_email"]:
            notify_result = notifier.execute(state)
            state["notification_status"] = notify_result["notification_status"]
            state["notification_sent"] = notify_result["notification_sent"]
            
            if notify_result["notification_sent"]:
                output_status += f"\n📧 **Email sent to:** `{state['user_email']}`"
            else:
                output_status += f"\n⚠️ **Email failed:** {notify_result['notification_status']}"
        else:
            output_status += "\n📧 No email provided - skipping notification."
        
        output_status += f"""

---

**Preview:**

{state['markdown_content'][:1200]}...
"""
    else:
        output_status = "⏸️ Files not generated - curriculum needs revision first."

    # Format outputs
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

    return research_output, curriculum_output, eval_output, output_status


with gr.Blocks(title="Learning Planner - Node Testing") as ui:
    gr.Markdown("## Learning Path Generator")
    gr.Markdown("Researcher → Curriculum Builder → Evaluator → Writers → Notifier")
    
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
        email_input = gr.Textbox(
            label="Email (optional - to receive PDF)",
            placeholder="your@email.com"
        )
    with gr.Row():
        run_btn = gr.Button("Generate Learning Path", variant="primary")
    
    with gr.Row():
        with gr.Column(scale=1):
            research_output = gr.Markdown(label="Research")
        with gr.Column(scale=2):
            curriculum_output = gr.Markdown(label="Curriculum")
    
    with gr.Row():
        with gr.Column(scale=1):
            eval_output = gr.Markdown(label="Evaluation")
        with gr.Column(scale=2):
            output_status = gr.Markdown(label="Output")
    
    run_btn.click(
        test_full_chain,
        inputs=[topic_input, skill_level, time_commitment, email_input],
        outputs=[research_output, curriculum_output, eval_output, output_status]
    )


if __name__ == "__main__":
    ui.launch()
