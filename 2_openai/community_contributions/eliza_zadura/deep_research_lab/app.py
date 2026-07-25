"""
Trust-Aware Deep Research - Gradio UI

Multi-step interface:
1. Topic input -> Generate follow-up questions
2. Answer questions -> Run research with progress
3. Display report -> Option to copy

Run with: python app.py
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# CRITICAL: Load .env BEFORE importing any modules that need environment variables
# Try multiple possible .env locations
possible_env_paths = [
    Path(__file__).parent.parent.parent.parent.parent / '.env',  # agents root
    Path(__file__).parent.parent.parent.parent.parent.parent / '.env',  # agents_mine root
    Path(__file__).parent.parent.parent.parent.parent.parent.parent / '.env',  # ai_engineer_agentic_track root
]

env_loaded = False
for env_path in possible_env_paths:
    if env_path.exists():
        load_dotenv(dotenv_path=env_path, override=True)
        env_loaded = True
        print(f"✓ Loaded .env from: {env_path}")
        break

if not env_loaded:
    # Fallback: try loading from current directory and system env
    load_dotenv(override=True)
    print("⚠️  No .env file found in expected locations, using system environment")

# Explicitly ensure OPENAI_API_KEY is set in environment
api_key = os.getenv('OPENAI_API_KEY')
if api_key:
    # Remove any quotes or whitespace that might have been introduced
    api_key = api_key.strip().strip('"').strip("'")
    os.environ['OPENAI_API_KEY'] = api_key
    print(f"✓ OPENAI_API_KEY set (length: {len(api_key)}, starts with: {api_key[:7]}...)")
else:
    print("⚠️  WARNING: OPENAI_API_KEY not found in environment")

# Now import modules that need environment variables
import gradio as gr
from research_manager import ResearchManager

# Global state for the research session
manager = ResearchManager()
current_topic = ""
current_questions = []


async def generate_questions(topic: str):
    """Phase 1: Generate follow-up questions for the topic."""
    global current_topic, current_questions
    
    if not topic.strip():
        return (
            gr.update(visible=True),   # topic_section stays visible
            gr.update(visible=False),  # questions_section hidden
            gr.update(visible=False),  # research_section hidden
            "",  # q1
            "",  # q2
            "",  # q3
            "",  # status
        )
    
    current_topic = topic
    
    try:
        questions = await manager.get_intake_questions(topic)
        current_questions = questions.questions
        
        return (
            gr.update(visible=False),  # hide topic_section
            gr.update(visible=True),   # show questions_section
            gr.update(visible=False),  # research_section hidden
            current_questions[0] if len(current_questions) > 0 else "",
            current_questions[1] if len(current_questions) > 1 else "",
            current_questions[2] if len(current_questions) > 2 else "",
            f"📋 Questions generated for: **{topic}**",
        )
    except Exception as e:
        return (
            gr.update(visible=True),
            gr.update(visible=False),
            gr.update(visible=False),
            "", "", "",
            f"❌ Error generating questions: {e}",
        )


async def run_research(a1: str, a2: str, a3: str, send_email: bool):
    """Phase 2: Create brief and run the full research pipeline."""
    global current_topic, current_questions
    
    # Build answers dict
    answers = {}
    if len(current_questions) > 0:
        answers[current_questions[0]] = a1
    if len(current_questions) > 1:
        answers[current_questions[1]] = a2
    if len(current_questions) > 2:
        answers[current_questions[2]] = a3
    
    # Initial UI state
    yield (
        gr.update(visible=False),  # questions_section
        gr.update(visible=True),   # research_section
        "🔄 Creating research brief...\n",
        "",  # report
    )
    
    try:
        # Create the brief
        brief = await manager.create_brief(
            current_topic, 
            current_questions, 
            answers
        )
        
        status_log = f"📋 **Research Brief**\n"
        status_log += f"- Topic: {brief.topic}\n"
        status_log += f"- Use: {brief.intended_use}\n"
        status_log += f"- Angle: {brief.desired_angle}\n\n"
        
        yield (
            gr.update(visible=False),
            gr.update(visible=True),
            status_log,
            "",
        )
        
        # Run the research pipeline
        report_content = ""
        async for update in manager.run_research(brief, send_email=send_email):
            if update == "---":
                # Next update will be the report
                continue
            elif update.startswith("#") or update.startswith("**"):
                # This is report content
                report_content += update + "\n"
            else:
                status_log += update + "\n"
            
            yield (
                gr.update(visible=False),
                gr.update(visible=True),
                status_log,
                report_content,
            )
        
    except Exception as e:
        yield (
            gr.update(visible=False),
            gr.update(visible=True),
            f"❌ Error: {e}",
            "",
        )


def reset_ui():
    """Reset to initial state for a new research session."""
    global current_topic, current_questions
    current_topic = ""
    current_questions = []
    
    return (
        gr.update(visible=True),   # topic_section
        gr.update(visible=False),  # questions_section
        gr.update(visible=False),  # research_section
        "",  # topic input
        "",  # q1
        "",  # q2
        "",  # q3
        "", "", "",  # answers
        "",  # status
        "",  # report
    )


# Build the UI
with gr.Blocks(
    theme=gr.themes.Soft(primary_hue="blue"),
    title="Trust-Aware Deep Research"
) as ui:
    
    gr.Markdown("""
    # 🔬 Trust-Aware Deep Research
    
    A research workflow with source quality controls and evidence-backed claims.
    """)
    
    # Phase 1: Topic Input
    with gr.Group(visible=True) as topic_section:
        gr.Markdown("### Step 1: Enter your research topic")
        topic_input = gr.Textbox(
            label="Research Topic",
            placeholder="e.g., 'Impact of AI on healthcare diagnostics'",
            lines=2,
        )
        generate_btn = gr.Button("Generate Questions", variant="primary")
    
    # Phase 2: Answer Questions
    with gr.Group(visible=False) as questions_section:
        gr.Markdown("### Step 2: Answer these questions to scope your research")
        
        q1_label = gr.Markdown("")
        a1_input = gr.Textbox(label="Your answer", lines=2)
        
        q2_label = gr.Markdown("")
        a2_input = gr.Textbox(label="Your answer", lines=2)
        
        q3_label = gr.Markdown("")
        a3_input = gr.Textbox(label="Your answer", lines=2)
        
        with gr.Row():
            send_email_checkbox = gr.Checkbox(
                label="Send report via email", 
                value=False
            )
            research_btn = gr.Button("Start Research", variant="primary")
            back_btn = gr.Button("← Back")
    
    # Phase 3: Research Progress & Report
    with gr.Group(visible=False) as research_section:
        gr.Markdown("### Step 3: Research in progress")
        
        status_output = gr.Markdown(label="Status")
        report_output = gr.Markdown(label="Report")
        
        new_research_btn = gr.Button("Start New Research", variant="secondary")
    
    # Event handlers
    generate_btn.click(
        fn=generate_questions,
        inputs=[topic_input],
        outputs=[
            topic_section, 
            questions_section, 
            research_section,
            q1_label, 
            q2_label, 
            q3_label,
            status_output,
        ],
    )
    
    research_btn.click(
        fn=run_research,
        inputs=[a1_input, a2_input, a3_input, send_email_checkbox],
        outputs=[
            questions_section,
            research_section,
            status_output,
            report_output,
        ],
    )
    
    back_btn.click(
        fn=lambda: (
            gr.update(visible=True),
            gr.update(visible=False),
            gr.update(visible=False),
        ),
        outputs=[topic_section, questions_section, research_section],
    )
    
    new_research_btn.click(
        fn=reset_ui,
        outputs=[
            topic_section,
            questions_section,
            research_section,
            topic_input,
            q1_label, q2_label, q3_label,
            a1_input, a2_input, a3_input,
            status_output,
            report_output,
        ],
    )


if __name__ == "__main__":
    ui.launch(server_name="localhost", inbrowser=True)
