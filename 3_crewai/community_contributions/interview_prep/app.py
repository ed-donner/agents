import gradio as gr
import os
import json
from dotenv import load_dotenv

load_dotenv()
os.makedirs("output", exist_ok=True)


def run_crew(company, role, job_description):
    from interview_prep.crew import InterviewPrepCrew

    if not company.strip() or not role.strip():
        return "Please provide both company and role.", "", ""

    jd = job_description.strip() or "No specific job description provided."
    inputs = {"company": company.strip(), "role": role.strip(), "job_description": jd}

    result = InterviewPrepCrew().crew().kickoff(inputs=inputs)

    # Format pydantic output as readable markdown — one-week plan shown first
    if result.pydantic:
        p = result.pydantic
        prep_md = f"## 7-Day Study Plan\n\n{p.one_week_plan}\n\n"

        prep_md += "## Round Breakdown\n\n"
        for r in p.round_breakdown:
            prep_md += f"- {r}\n"

        prep_md += "\n## Topic Weightage\n\n"
        for t in p.topic_weightage:
            prep_md += f"### {t.topic} — {t.weightage_percent}%\n"
            for q in t.sample_questions:
                prep_md += f"- {q}\n"
            prep_md += "\n"

        prep_md += "## Must-Know Questions\n\n"
        for q in p.must_know_questions:
            prep_md += f"- {q}\n"
    else:
        prep_md = result.raw or ""

    resources_md = ""
    if os.path.exists("output/resources.md"):
        with open("output/resources.md", encoding="utf-8") as f:
            resources_md = f.read()

    json_str = ""
    if result.pydantic:
        json_str = f"```json\n{json.dumps(result.pydantic.model_dump(), indent=2)}\n```"

    return prep_md, resources_md, json_str


def chat_fn(message: str, history: list, company: str, role: str):
    """Generator function — yields partial text so Gradio streams the response."""
    try:
        from google import genai
    except ImportError:
        yield "google-genai package not found. Run: pip install google-genai"
        return

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        yield "GEMINI_API_KEY not set. Add it to your .env file or Space secrets."
        return

    context = ""
    if os.path.exists("output/prep_guide.md"):
        with open("output/prep_guide.md", encoding="utf-8") as f:
            context = f.read()

    system_instruction = f"""You are a senior technical interviewer at {company} \
conducting a realistic mock {role} interview.

Preparation context for this role:
{context}

Interview rules:
- Ask exactly ONE question at a time. Wait for the candidate to answer before continuing.
- Give 2-3 sentences of constructive feedback after each answer.
- Cover all rounds: behavioral first, then DSA, then system design.
- When the candidate says "end" or "quit", give an overall performance summary."""

    client = genai.Client(api_key=api_key)

    def as_text(content):
        """Gradio may store content as a plain string OR a list of parts
        like [{'text': '...', 'type': 'text'}]. Normalize to a string."""
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            return "".join(
                part.get("text", "") for part in content if isinstance(part, dict)
            )
        return str(content)

    # Rebuild full conversation for Gemini on each call.
    # Gradio passes history as list of dicts: {"role": "user"/"assistant", "content": ...}
    # Gemini needs "model" instead of "assistant"
    contents = []
    for turn in history:
        gemini_role = "model" if turn["role"] == "assistant" else "user"
        contents.append({"role": gemini_role, "parts": [{"text": as_text(turn["content"])}]})
    contents.append({"role": "user", "parts": [{"text": as_text(message)}]})

    try:
        partial = ""
        for chunk in client.models.generate_content_stream(
            model="gemini-3.1-flash-lite",
            contents=contents,
            config={"system_instruction": system_instruction},
        ):
            if chunk.text:
                partial += chunk.text
                yield partial  # yield full string so far — Gradio replaces the bubble each time
    except Exception as e:
        yield f"Error from Gemini: {e}"


CUSTOM_CSS = """
.gradio-container { max-width: 960px !important; margin: 0 auto !important; }
#hero {
    text-align: center;
    padding: 34px 20px 22px;
    background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
    border-radius: 16px;
    margin-bottom: 18px;
    color: #fff;
}
#hero h1 { font-size: 2.1rem; margin: 0 0 10px; color: #fff; }
#hero p { font-size: 1rem; max-width: 620px; margin: 0 auto; line-height: 1.7; opacity: 0.95; }
#hero .agents { margin-top: 16px; font-size: 0.85rem; opacity: 0.9; }
.empty-hint { color: #9ca3af; text-align: center; padding: 40px 0; font-style: italic; }
footer { display: none !important; }
"""

EMPTY = "<div class='empty-hint'>Fill in the details above and hit generate — your guide will appear here.</div>"


with gr.Blocks(title="Interview Prep Crew", css=CUSTOM_CSS) as demo:

    gr.HTML("""
    <div id="hero">
        <h1>🎯 Interview Prep Crew</h1>
        <p>
            Four AI agents research your target company, surface real interview questions,
            find curated prep resources, and build a personalised study plan.
            Then practise live with a Gemini-powered mock interviewer.
        </p>
        <div class="agents">🔍 Researcher &nbsp;·&nbsp; 🕵️ Intel Agent &nbsp;·&nbsp; 📚 Resource Curator &nbsp;·&nbsp; 🧠 Strategist</div>
    </div>
    """)

    with gr.Tab("📋 Generate Prep Guide"):
        with gr.Row():
            company_in = gr.Textbox(
                label="Company",
                placeholder="e.g. Google",
                info="The company you are interviewing at",
                scale=1,
            )
            role_in = gr.Textbox(
                label="Role",
                placeholder="e.g. Software Engineer",
                info="The exact position you are applying for",
                scale=1,
            )

        with gr.Accordion("➕ Add a Job Description (optional, recommended)", open=False):
            jd_in = gr.Textbox(
                label="Job Description",
                lines=5,
                placeholder="Paste the full JD here for sharper topic weightage and questions...",
                show_label=False,
            )

        gr.Examples(
            examples=[
                ["Google", "Software Engineer"],
                ["Stripe", "Backend Engineer"],
                ["Netflix", "Data Scientist"],
                ["OpenAI", "ML Engineer"],
            ],
            inputs=[company_in, role_in],
            label="Quick start — click an example",
        )

        run_btn = gr.Button("🚀 Generate My Prep Guide", variant="primary", size="lg")
        gr.Markdown(
            "> ⏳ *Takes 2–5 minutes — four agents are searching the web and reasoning in real time.*"
        )

        with gr.Tabs():
            with gr.TabItem("📖 Prep Guide"):
                prep_out = gr.Markdown(EMPTY)
            with gr.TabItem("🔗 Resources"):
                resources_out = gr.Markdown(EMPTY)
            with gr.TabItem("{ } JSON"):
                json_out = gr.Markdown(EMPTY)

        run_btn.click(
            fn=run_crew,
            inputs=[company_in, role_in, jd_in],
            outputs=[prep_out, resources_out, json_out],
            show_progress="full",
        )

    with gr.Tab("🎤 Mock Interview"):
        gr.Markdown(
            "**Run the prep guide first**, then start your mock interview here. "
            "Company and role are taken from the first tab automatically. "
            "Type **begin** to start."
        )

        gr.ChatInterface(
            fn=chat_fn,
            additional_inputs=[company_in, role_in],
            chatbot=gr.Chatbot(
                height=500,
                placeholder="Type 'begin' to start your mock interview...",
            ),
        )


if __name__ == "__main__":
    demo.launch(theme=gr.themes.Soft())
