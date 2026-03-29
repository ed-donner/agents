import asyncio
import re
from datetime import datetime
from contextlib import AsyncExitStack

import gradio as gr
from dotenv import load_dotenv
from agents import Agent, Runner, ModelSettings
from agents.mcp import MCPServerStdio
from pypdf import PdfReader

from mcp_params import coach_mcp_server_params

load_dotenv(override=True)

# ── Rate limiting ─────────────────────────────────────────────────────────────
# Tracks number of runs per session to protect the API key.
# Max 5 runs per session — prevents accidental or excessive usage.
MAX_RUNS_PER_SESSION = 5
session_run_count = 0

# ── CV Extraction ─────────────────────────────────────────────────────────────

def extract_cv_text(file_path: str) -> tuple[bool, str]:
    """
    Extracts text from an uploaded CV file.
    Supports .pdf and .txt formats.
    Returns (success, text_or_error_message).
    """
    try:
        if file_path.endswith(".pdf"):
            reader = PdfReader(file_path)
            text = "\n".join(page.extract_text() for page in reader.pages if page.extract_text())
        elif file_path.endswith(".txt"):
            with open(file_path, "r", encoding="utf-8") as f:
                text = f.read()
        else:
            return False, "Unsupported file type. Please upload a PDF or TXT file."
        if not text.strip():
            return False, "Could not extract text from the file. Please check the file and try again."
        return True, text
    except Exception as e:
        return False, f"Failed to read the file: {str(e)}"

# ── Templates ─────────────────────────────────────────────────────────────────

def coach_instructions(cv: str) -> str:
    return f"""You are a professional job application coach helping a candidate apply for jobs.
You have access to tools to fetch job postings and save applications to a tracker.

Your workflow:
1. Fetch the job posting from the URL provided
2. Carefully review the candidate's CV against the job requirements
3. Tailor the CV to highlight the most relevant experience and skills for this specific role
4. Write a compelling cover letter for this specific role
5. Save the application to the tracker
6. Return your response in EXACTLY this format — do not deviate:

---
## Tailored CV

[Write the complete tailored CV here — every section, fully written out]

---
## Cover Letter

[Write the complete cover letter here — fully written out]

---
## Application Saved
Application ID: [id] | Company: [company] | Role: [role] | Date: [date]

IMPORTANT:
- Never summarize or reference the documents — always write them out in full
- Always follow the exact format above with the ## headings
- The current date is {datetime.now().strftime("%Y-%m-%d")}

Here is the candidate's CV:
{cv}
"""

def coach_prompt(job_url: str) -> str:
    return f"""Please help me apply for this job: {job_url}

Fetch the job posting, tailor my CV, write a cover letter, save the application,
and return the FULL tailored CV and FULL cover letter — written out completely, not summarized.
"""

# ── Guardrails ────────────────────────────────────────────────────────────────

def input_guardrail(cv_text: str, job_url: str) -> tuple[bool, str]:
    """
    Input guardrail — validates inputs before sending to the agent.
    Checks:
    - CV file has been uploaded and text extracted
    - CV text is long enough to be a real CV (min 100 characters)
    - URL is not empty
    - URL starts with http:// or https://
    - URL is not a LinkedIn URL (LinkedIn blocks automated fetching)
    - Session run count has not exceeded the maximum allowed (API key protection)
    Future: could validate against a list of supported job boards,
    check for offensive content, or add per-user rate limiting.
    """
    global session_run_count
    if not cv_text or len(cv_text.strip()) < 100:
        return False, "Please upload a valid CV file (PDF or TXT) with sufficient content."
    if not job_url.strip():
        return False, "Please enter a job posting URL."
    if not re.match(r"https?://", job_url.strip()):
        return False, "Please enter a valid URL starting with http:// or https://"
    if "linkedin.com" in job_url.lower():
        return False, "LinkedIn URLs are not supported as LinkedIn blocks automated access. Please use a direct company careers page, Greenhouse, Lever, or Indeed URL."
    if session_run_count >= MAX_RUNS_PER_SESSION:
        return False, f"Maximum of {MAX_RUNS_PER_SESSION} runs per session reached. Please restart the app to continue."
    return True, ""

def output_guardrail(result: str) -> tuple[bool, str]:
    """
    Output guardrail — validates the agent's output before displaying to the user.
    Checks:
    - Output is not empty or too short to be valid
    - Output contains a Tailored CV section
    - Output contains a Cover Letter section
    Future: could check for sensitive data leakage, hallucinated company names,
    or ensure the cover letter is addressed to the correct company.
    """
    if not result or len(result.strip()) < 100:
        return False, "The agent returned an incomplete response. Please try again."
    if "## Tailored CV" not in result:
        return False, "The agent did not return a tailored CV. Please try again."
    if "## Cover Letter" not in result:
        return False, "The agent did not return a cover letter. Please try again."
    return True, ""

# ── Coach ─────────────────────────────────────────────────────────────────────

async def run_coach(cv_file, job_url: str) -> str:
    """
    Runs the Coach Agent with:
    - Model: gpt-4o-mini
    - Max tokens: 4096 — enough for full CV + cover letter output
    - Temperature: 0.7 — balanced between creativity and consistency
    - max_turns: 20 — sufficient for fetch + write + save workflow
    Exception handling covers file reading, MCP connection failures,
    and agent runtime errors.
    Streaming was removed due to incompatibility with MCP server connections.
    """
    global session_run_count

    # Extract CV text from uploaded file
    if cv_file is None:
        return "Please upload your CV file before submitting."

    success, cv_text = extract_cv_text(cv_file.name)
    if not success:
        return cv_text

    # Input guardrail
    valid, message = input_guardrail(cv_text, job_url)
    if not valid:
        return message

    session_run_count += 1
    remaining = MAX_RUNS_PER_SESSION - session_run_count

    try:
        async with AsyncExitStack() as stack:
            mcp_servers = [
                await stack.enter_async_context(
                    MCPServerStdio(params, client_session_timeout_seconds=30)
                )
                for params in coach_mcp_server_params
            ]

            agent = Agent(
                name="Coach",
                instructions=coach_instructions(cv_text),
                mcp_servers=mcp_servers,
                model="gpt-4o-mini",
                model_settings=ModelSettings(temperature=0.7, max_tokens=4096),
            )

            # Run the agent
            result = await Runner.run(agent, coach_prompt(job_url), max_turns=20)
            result_text = result.final_output

            # Output guardrail
            valid, message = output_guardrail(result_text)
            if not valid:
                return message

            return f"*{remaining} runs remaining this session.*\n\n{result_text}"

    except Exception as e:
        session_run_count -= 1  # Don't count failed runs against the limit
        return f"An error occurred: {str(e)}\n\nPlease check your API key, internet connection, and try again."

# ── UI ────────────────────────────────────────────────────────────────────────

with gr.Blocks(title="Job Application Coach") as app:
    gr.Markdown("# Job Application Coach")
    gr.Markdown(
        "Upload your CV and paste a job posting URL. "
        "The coach will tailor your CV, write a cover letter, and save your application. "
        "Avoid LinkedIn URLs — use Greenhouse, Lever, Indeed, or company career pages directly."
    )

    with gr.Row():
        cv_upload = gr.File(
            label="Upload your CV (PDF or TXT)",
            file_types=[".pdf", ".txt"],
            scale=1
        )
        with gr.Column(scale=2):
            job_url_input = gr.Textbox(
                label="Job Posting URL",
                placeholder="https://boards.greenhouse.io/company/jobs/123456",
            )
            submit_btn = gr.Button("Run Coach", variant="primary")

    output = gr.Markdown(label="Result")

    submit_btn.click(
        fn=run_coach,
        inputs=[cv_upload, job_url_input],
        outputs=[output],
    )

if __name__ == "__main__":
    app.launch()
