from dotenv import load_dotenv
from openai import OpenAI
import json
import os
import requests
from pypdf import PdfReader
import gradio as gr

load_dotenv(override=True)

# ── Configuration ────────────────────────────────────────────────────────────
ME_DIR = os.path.join(os.path.abspath(os.path.dirname(__file__)) if "__file__" in globals() else os.getcwd(), "me")
os.makedirs(ME_DIR, exist_ok=True)
RESUME_PATH = os.path.join(ME_DIR, "resume.pdf")

# Standard configuration from environment
MODEL = os.getenv("MODEL", "openai/gpt-4o")
SECRET_PHARSE = os.getenv("SECRET_PHARSE", "")
MY_NAME = "Michael Aigbovbiosa"
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

SECTIONS = ["introduction", "tech_and_tools", "experience", "certifications", "projects"]

# Validate API Key
if not OPENROUTER_API_KEY:
    print("\n[WARNING] OPENROUTER_API_KEY is not set. Please add it to your environment variables or Hugging Face Secrets.\n", flush=True)

ai = OpenAI(
    api_key=OPENROUTER_API_KEY or "missing_key",
    base_url="https://openrouter.ai/api/v1",
)


# ── Pusher / Notifications ───────────────────────────────────────────────────
def push(text: str):
    """Send a notification to Pushover."""
    try:
        requests.post(
            "https://api.pushover.net/1/messages.json",
            data={
                "token": os.getenv("PUSHOVER_TOKEN"),
                "user": os.getenv("PUSHOVER_USER"),
                "message": text,
            },
        )
    except Exception as e:
        print(f"[Push error] {e}", flush=True)


# ── Init ─────────────────────────────────────────────────────────────────────
def init():
    """Parse resume.pdf with LLM and write structured md files to me/."""
    if not os.path.exists(RESUME_PATH):
        print("[init] resume.pdf not found, skipping.", flush=True)
        return

    # Read resume text
    try:
        reader = PdfReader(RESUME_PATH)
        resume_text = ""
        for page in reader.pages:
            text = page.extract_text()
            if text:
                resume_text += text
        
        if not resume_text.strip():
            print("[init] resume.pdf appears to be empty or unreadable.", flush=True)
            return
    except Exception as e:
        print(f"[init] Error reading resume.pdf: {e}", flush=True)
        return

    section_prompts = {
        "introduction": (
            "Write a concise first-person professional introduction for the person described in this resume. "
            "Cover who they are, their primary domain, and what makes them stand out. 2-3 paragraphs."
        ),
        "tech_and_tools": (
            "Extract and summarize all technologies, programming languages, frameworks, tools, and platforms "
            "mentioned in this resume. Format as a well-organised markdown document with categories."
        ),
        "experience": (
            "Extract and format all work experience from this resume as detailed markdown. "
            "Include company name, role, dates, and bullet points for key responsibilities and achievements."
        ),
        "certifications": (
            "Extract all certifications, awards, achievements, and professional development from this resume. "
            "Format as clean markdown with dates where available."
        ),
        "projects": (
            "Extract all projects from this resume. For each project include: name, description, "
            "technologies used, and key outcomes. Format as clean markdown."
        ),
    }

    for section, instruction in section_prompts.items():
        filepath = os.path.join(ME_DIR, f"{section}.md")
        try:
            response = ai.chat.completions.create(
                model=MODEL,
                messages=[
                    {"role": "system", "content": "You are a professional resume analyst. Output only clean markdown, no preamble."},
                    {"role": "user", "content": f"{instruction}\n\n---\nRESUME:\n{resume_text}"},
                ],
            )
            content = response.choices[0].message.content or ""
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"[init] {section}.md written.", flush=True)
        except Exception as e:
            print(f"[init] Error generating {section}: {e}", flush=True)

    print("[init] All sections processed.", flush=True)


def ensure_init():
    """Run init only if md files are missing or empty."""
    def is_invalid(s):
        fp = os.path.join(ME_DIR, f"{s}.md")
        return not os.path.exists(fp) or os.path.getsize(fp) == 0

    if any(is_invalid(s) for s in SECTIONS):
        init()


def load_context() -> str:
    """Load all context sections into a single string."""
    parts = []
    for section in SECTIONS:
        fp = os.path.join(ME_DIR, f"{section}.md")
        try:
            if os.path.exists(fp):
                with open(fp, "r", encoding="utf-8") as f:
                    content = f.read().strip()
                    if content:
                        parts.append(f"## {section.replace('_', ' ').title()}\n{content}")
        except Exception as e:
            print(f"[load_context] Error reading {section}.md: {e}", flush=True)
    return "\n\n".join(parts)


# ── Tools ────────────────────────────────────────────────────────────────────
def record_user_details(email: str, name: str = "Name not provided", notes: str = "not provided"):
    """Record user details for follow-up."""
    push(f"New contact from {name} ({email}): {notes}")
    return {"recorded": "ok"}

def record_unknown_question(question: str):
    """Record an unknown question for later review."""
    push(f"Knowledge gap detected!\nA user asked: \"{question}\"")
    return {"recorded": "ok"}

def run_init_tool():
    """Run the init function to parse the resume."""
    init()
    return {"status": "init complete"}

def update_section(section: str, instruction: str):
    """Update a specific section of the resume."""
    if section not in SECTIONS:
        return {"error": "Invalid section"}
    filepath = os.path.join(ME_DIR, f"{section}.md")
    existing_content = ""
    if os.path.exists(filepath):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                existing_content = f.read()
        except Exception as e:
            return {"error": f"Could not read existing section: {e}"}

    try:
        response = ai.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": "You are helping update a personal portfolio. Output only clean markdown."},
                {"role": "user", "content": f"Existing '{section}':\n{existing_content}\n\nInstruction: {instruction}"},
            ],
        )
        new_content = response.choices[0].message.content or ""
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(new_content)
        return {"status": "updated", "section": section}
    except Exception as e:
        return {"error": f"Failed to update section: {e}"}

visitor_tools = [
    {
        "type": "function",
        "function": {
            "name": "record_user_details",
            "description": "Call this when a user wants to get in touch.",
            "parameters": {
                "type": "object",
                "properties": {
                    "email": {"type": "string"},
                    "name": {"type": "string"},
                    "notes": {"type": "string"},
                },
                "required": ["email"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "record_unknown_question",
            "description": "Call this ONLY when a professional or career-related question is asked but the answer is missing from the resume/portfolio context. Do NOT use this for personal, political, or off-topic queries.",
            "parameters": {
                "type": "object",
                "properties": {"question": {"type": "string"}},
                "required": ["question"],
            },
        },
    },
]

admin_tools = [
    {
        "type": "function",
        "function": {
            "name": "run_init_tool",
            "description": "Regenerate markdown files from resume.pdf.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "update_section",
            "description": "Update a specific profile section.",
            "parameters": {
                "type": "object",
                "properties": {
                    "section": {"type": "string", "enum": SECTIONS},
                    "instruction": {"type": "string"},
                },
                "required": ["section", "instruction"],
            },
        },
    },
]

tool_map = {
    "record_user_details": record_user_details,
    "record_unknown_question": record_unknown_question,
    "run_init_tool": run_init_tool,
    "update_section": update_section,
}


# ── Chat Class ───────────────────────────────────────────────────────────────
class PortfolioAssistant:
    """Portfolio Assistant class."""
    def __init__(self):
        """Initialize the Portfolio Assistant."""
        self.is_admin = False

    def handle_tools(self, tool_calls):
        """Handle tool calls."""
        results = []
        for tc in tool_calls:
            name = tc.function.name
            args = json.loads(tc.function.arguments)
            fn = tool_map.get(name)
            result = fn(**args) if fn else {"error": "unknown tool"}
            results.append({"role": "tool", "content": json.dumps(result), "tool_call_id": tc.id})
        return results

    def chat(self, message: str, history: list):
        """Handle chat messages."""
        if message.strip() == SECRET_PHARSE:
            self.is_admin = True
            push(f"Admin access granted to {MY_NAME}.")
            yield (
                f"**Admin mode activated.** Welcome back, {MY_NAME}!\n\n"
                f"You can now:\n"
                f"- Re-run init from resume\n"
                f"- Update any section: `{', '.join(SECTIONS)}`"
            )
            return

        if self.is_admin:
            tools = admin_tools
            sys_prompt = f"You are an admin assistant for {MY_NAME}. Help the owner manage their profile."
        else:
            tools = visitor_tools
            sys_prompt = (
                f"You are acting as {MY_NAME}. Answer questions about your career, background, skills, and experience only. "
                f"Be professional and warm. \n\n"
                f"**GUARDRAILS:**\n"
                f"- If a question is NOT about your professional life (e.g., personal habits, politics, unrelated general knowledge), "
                f"politely decline to answer and explain that you only discuss professional topics here. **Do NOT use any tools for off-topic questions.**\n"
                f"- If a professional question is asked but the info is missing from the context below, use the `record_unknown_question` tool.\n"
                f"- If someone wants to stay in touch, use `record_user_details`.\n\n"
                f"**Context from your resume/profile:**\n{load_context()}"
            )

        messages = [{"role": "system", "content": sys_prompt}] + history + [{"role": "user", "content": message}]

        # Run loop
        is_running = True
        try:
            while is_running:
                response = ai.chat.completions.create(model=MODEL, messages=messages, tools=tools)
                msg = response.choices[0].message
                messages.append(msg)
                if response.choices[0].finish_reason == "tool_calls":
                    messages.extend(self.handle_tools(msg.tool_calls))
                else:
                    is_running = False
        except Exception as e:
            err_msg = f"[AI Error] I encountered an issue while processing your request: {e}"
            push(err_msg)
            yield err_msg
            return

        # Streaming last reply
        try:
            partial = ""
            stream = ai.chat.completions.create(model=MODEL, messages=messages[:-1], tools=tools, stream=True)
            for chunk in stream:
                delta = chunk.choices[0].delta
                if delta and delta.content:
                    partial += delta.content
                    yield partial
        except Exception as e:
            err_msg = f"\n\n[Streaming Error] Connection lost: {e}"
            push(err_msg)
            yield err_msg


# ── Main ─────────────────────────────────────────────────────────────────────
ensure_init()
me = PortfolioAssistant()

demo = gr.ChatInterface(
    me.chat,
    type="messages",
    title=f"{MY_NAME} - Portfolio Assistant",
    description=f"Ask anything about {MY_NAME}'s career and experience."
)

if __name__ == "__main__":
    demo.launch()