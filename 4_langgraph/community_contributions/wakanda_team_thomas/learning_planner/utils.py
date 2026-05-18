"""
Utility functions for the Learning Path Generator.
"""

import uuid
import gradio as gr
from graph import LearningPlannerGraph

planner = LearningPlannerGraph()


def generate_learning_path(
    topic: str,
    skill_level: str,
    time_commitment: str,
    user_email: str,
):
    """Generate a learning path using the LangGraph pipeline."""
    if not topic.strip():
        yield (
            "Please enter a topic.", "", "", "",
            gr.update(interactive=True, value="Generate Learning Path")
        )
        return
    
    thread_id = str(uuid.uuid4())
    
    try:
        result = planner.run(
            topic=topic,
            skill_level=skill_level,
            time_commitment=time_commitment,
            user_email=user_email.strip() if user_email else "",
            thread_id=thread_id,
        )
    except Exception as e:
        yield (
            f"Error: {str(e)}", "", "", "",
            gr.update(interactive=True, value="Generate Learning Path")
        )
        return
    
    # Format research output
    prerequisites = result.get("prerequisites") or []
    key_concepts = result.get("key_concepts") or []
    research_output = f"""**Prerequisites:**
{chr(10).join([f"- {p}" for p in prerequisites]) if prerequisites else "- None identified"}

**Key Concepts:**
{chr(10).join([f"- {c}" for c in key_concepts]) if key_concepts else "- None identified"}
"""

    # Format curriculum output
    curriculum = result.get("curriculum")
    if curriculum:
        curriculum_output = f"""## {topic} Learning Path

**Overview:** {curriculum.overview}

**Total Duration:** {curriculum.total_estimated_days} days | **Phases:** {len(curriculum.milestones)}

---

"""
        for m in curriculum.milestones:
            curriculum_output += f"""### Phase {m.phase_number}: {m.title}

**Goal:** {m.goal}

{m.description}

**Resources:**
"""
            for r in m.resources:
                curriculum_output += f"- [{r.title}]({r.url}) `{r.type}` `{r.difficulty}`\n"
            
            if m.project_idea:
                curriculum_output += f"\n**Project:** {m.project_idea}\n"
            curriculum_output += f"\n*{m.estimated_days} days*\n\n---\n\n"
    else:
        curriculum_output = "No curriculum generated."

    # Format evaluation output
    is_complete = result.get("is_complete", False)
    eval_feedback = result.get("evaluation_feedback", "No feedback")
    status = "Approved" if is_complete else "Needs Revision"
    eval_output = f"""**Status:** {status}

**Feedback:**
{eval_feedback}
"""

    # Format output status
    markdown_path = result.get("markdown_path")
    pdf_path = result.get("pdf_path")
    notification_sent = result.get("notification_sent", False)
    notification_status = result.get("notification_status", "")
    
    if markdown_path:
        status_msg = "Files Generated!" if is_complete else "Files Generated (with evaluation feedback)"
        output_status = f"""**{status_msg}**

| File | Path |
|------|------|
| Markdown | `{markdown_path}` |
| PDF | `{pdf_path}` |

"""
        if user_email:
            if notification_sent:
                output_status += f"**Email sent to:** `{user_email}`\n"
            else:
                output_status += f"**Email failed:** {notification_status}\n"
        else:
            output_status += "*Tip: Add your email to receive the PDF directly.*\n"
        
        markdown_content = result.get("markdown_content", "")
        if markdown_content:
            output_status += f"""
---

**Preview:**

{markdown_content[:1000]}...
"""
    else:
        output_status = "Files not generated - curriculum revision in progress."

    yield (
        research_output, curriculum_output, eval_output, output_status,
        gr.update(interactive=True, value="Generate Learning Path")
    )


def clear_outputs():
    """Reset all outputs."""
    return "", "", "", "", ""


def disable_button():
    """Disable the button and show processing state."""
    return gr.update(interactive=False, value="Generating...")
