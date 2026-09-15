"""
cover_letter.py — Iteration 3: Generate tailored cover letters for selected jobs, as PDFs.

Reads jobs_selected.json (produced by job_ui.py), uses each job's full_description
(captured at Scout time from LinkedIn/Indeed's own search APIs — no scraping needed),
generates a tailored cover letter (structured as intro + "What I bring to this role:"
bullet points + closing) using the candidate's full profile.md, and renders each
letter as a PDF matching the candidate's preferred format: name + date top row,
contact line, recipient line (Hiring Team, Company, Location), subject line,
salutation, bolded bullet lead-ins flowing into normal paragraph text, closing.

Usage as a script:
    uv run python cover_letter.py

Usage as a module:
    from cover_letter import run_cover_letters
    letters = await run_cover_letters()
"""

import json
import unicodedata
from datetime import date
from pathlib import Path

from agents import Agent, Runner
from fpdf import FPDF


from user_config import get_config

_cfg = get_config()

SELECTED_PATH = Path("jobs_selected.json")
PROFILE_PATH = _cfg.profile_path
OUTPUT_DIR = Path("cover_letters")

MODEL = "gpt-4.1-mini"
CLIENT_TIMEOUT_SECONDS = 90

CANDIDATE_NAME = _cfg.candidate.name
CANDIDATE_EMAIL = _cfg.candidate.email
CANDIDATE_PHONE = _cfg.candidate.phone
CANDIDATE_LOCATION = _cfg.candidate.location

_UNICODE_REPLACEMENTS = {
    "\u2013": "-", "\u2014": "-", "\u2018": "'", "\u2019": "'",
    "\u201c": '"', "\u201d": '"', "\u2026": "...", "\u00a0": " ",
}


def sanitize_text(text: str) -> str:
    if not text:
        return text
    for uni_char, ascii_char in _UNICODE_REPLACEMENTS.items():
        text = text.replace(uni_char, ascii_char)
    text = unicodedata.normalize("NFKC", text)
    return text.encode("latin-1", errors="replace").decode("latin-1")


def load_selected_jobs(path: Path = SELECTED_PATH) -> list[dict]:
    if not path.exists():
        raise FileNotFoundError(
            f"{path} not found — select jobs in the Gradio UI first (Iteration 2)."
        )
    return json.loads(path.read_text(encoding="utf-8"))


def load_profile(path: Path = PROFILE_PATH) -> str:
    return path.read_text(encoding="utf-8")


def slugify(text: str) -> str:
    return "".join(c if c.isalnum() else "_" for c in text).strip("_").lower()


def build_cover_letter_instructions(job: dict, profile: str) -> str:
    return f"""
You are writing a tailored, professional cover letter for a job application, in a
SPECIFIC STRUCTURED FORMAT (not free-flowing prose).

Step 1: Read the full posting text. The "Full description" field in the JOB section below
was captured directly at Scout time (from LinkedIn/Indeed's own search APIs) and contains the
complete job description — use it to understand the role's real requirements and context.
Do NOT rely only on the short summary.

Step 2: Write the letter content as JSON with exactly these fields:

{{
  "salutation": "Dear Hiring Team," (or similar, generic — do not guess a person's name),
  "intro": "1 short paragraph (3-5 sentences) opening with genuine, specific interest in
             this exact role and company, connecting the candidate's core experience to
             what the role needs.",
  "bring_heading": "What I bring to this role:",
  "bullets": [
    {{"title": "Short bold lead-in phrase (3-6 words, e.g. 'Full product lifecycle
                ownership')", "body": "1-2 sentences of concrete evidence from the
                candidate profile, mapped to a real requirement from the job posting.
                Write this so it reads naturally as a continuation of the bold title,
                like one flowing sentence/paragraph, not a separate fragment."}}
    // Produce 4-6 bullets total, each highlighting a DIFFERENT concrete experience
    // or skill from the candidate profile that maps to an ACTUAL requirement found
    // in the full job posting you fetched. Prioritize the most relevant matches.
  ],
  "closing": "1 short paragraph (2-4 sentences) reiterating enthusiasm for this specific
              company/role and inviting further discussion."
}}

Formatting rules:
- Use only plain ASCII punctuation (straight quotes ', ", regular hyphen -).
  Do NOT use en-dashes, em-dashes, curly quotes, or other special Unicode punctuation.
- Confident, professional, concise tone. No filler, no cliches like
  "I am writing to express my interest".
- Do NOT include name, date, contact info, company address, or "Best regards" —
  those are added separately by the template.

Return ONLY the JSON object. No markdown fences, no preamble, no explanation.

--- CANDIDATE PROFILE ---
{profile}

--- JOB ---
Title: {job.get('title')}
Company: {job.get('company')}
Location: {job.get('location')}
URL: {job.get('url')}
Summary (rough, verify against full description): {job.get('short_description', '')}
Full description: {job.get('full_description', '')}
"""


def parse_letter_json(text: str) -> dict:
    raw = (text or "").strip()
    if raw.startswith("```"):
        parts = raw.split("```")
        raw = parts[1]
        if raw.lstrip().startswith("json"):
            raw = raw.lstrip()[4:]
    raw = raw.strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        start, end = raw.find("{"), raw.rfind("}") + 1
        return json.loads(raw[start:end])


async def generate_letter_for_job(job: dict, profile: str) -> dict:
    print(f"✍️  Generating cover letter: {job.get('title')} @ {job.get('company')}")

    agent = Agent(
        name="Cover Letter Writer",
        instructions=build_cover_letter_instructions(job, profile),
        model=MODEL,
    )

    result = await Runner.run(
        agent,
        "Write the structured cover letter JSON now.",
        max_turns=10,
    )

    return parse_letter_json(result.final_output)


class CoverLetterPDF(FPDF):
    def header(self):
        pass  # header content is drawn manually in render_cover_letter_pdf


def render_cover_letter_pdf(letter: dict, job: dict, out_path: Path) -> None:
    date_str = date.today().strftime("%d.%m.%Y")

    pdf = CoverLetterPDF(format="A4")
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.set_margins(20, 15, 20)
    pdf.add_page()

    # --- Top row: Name (left) + Date (right) ---
    pdf.set_font("Helvetica", "B", 12)
    pdf.set_xy(20, 15)
    pdf.cell(100, 8, sanitize_text(CANDIDATE_NAME), align="L")
    pdf.set_xy(-70, 15)
    pdf.set_font("Helvetica", "", 11)
    pdf.cell(50, 8, date_str, align="R")
    pdf.ln(10)

    # --- Contact line ---
    pdf.set_x(20)
    pdf.set_font("Helvetica", "", 10)
    contact_line = f"{CANDIDATE_EMAIL} | {CANDIDATE_PHONE} | {CANDIDATE_LOCATION}"
    pdf.cell(0, 6, sanitize_text(contact_line))
    pdf.ln(10)

    # --- Recipient line: Hiring Team, Company, Location ---
    pdf.set_x(20)
    pdf.set_font("Helvetica", "", 10)
    recipient_line = f"Hiring Team, {job.get('company', '')}, {job.get('location', '')}"
    pdf.multi_cell(0, 6, sanitize_text(recipient_line))
    pdf.ln(8)

    # --- Application subject line ---
    pdf.set_x(20)
    pdf.set_font("Helvetica", "B", 11)
    subject = f"Application for {job.get('title', '')} at {job.get('company', '')}"
    pdf.multi_cell(0, 6, sanitize_text(subject))
    pdf.ln(6)

    # --- Salutation ---
    pdf.set_x(20)
    pdf.set_font("Helvetica", "", 11)
    pdf.multi_cell(0, 6, sanitize_text(letter.get("salutation", "Dear Hiring Team,")))
    pdf.ln(4)

    # --- Intro paragraph ---
    pdf.set_x(20)
    pdf.multi_cell(0, 6, sanitize_text(letter.get("intro", "")))
    pdf.ln(4)

    # --- "What I bring to this role:" heading ---
    pdf.set_x(20)
    pdf.set_font("Helvetica", "B", 11)
    pdf.multi_cell(0, 6, sanitize_text(letter.get("bring_heading", "What I bring to this role:")))
    pdf.ln(3)

    # --- Bullets: bold title flows inline into regular body text (full page width) ---
    bullets = letter.get("bullets", [])
    for b in bullets:
        title = sanitize_text(b.get("title", ""))
        body = sanitize_text(b.get("body", ""))

        pdf.set_x(24)
        pdf.set_font("Helvetica", "B", 11)
        pdf.write(6, "-  ")
        pdf.write(6, f"{title}: ")
        pdf.set_font("Helvetica", "", 11)
        pdf.write(6, body)
        pdf.ln(10)
        pdf.set_x(24)

    pdf.ln(2)

    # --- Closing paragraph ---
    pdf.set_x(20)
    pdf.set_font("Helvetica", "", 11)
    pdf.multi_cell(0, 6, sanitize_text(letter.get("closing", "")))
    pdf.ln(6)

    # --- Signature ---
    pdf.set_x(20)
    pdf.multi_cell(0, 6, "Best regards,")
    pdf.set_x(20)
    pdf.multi_cell(0, 6, sanitize_text(CANDIDATE_NAME))

    pdf.output(str(out_path))


async def run_cover_letters(save: bool = True) -> dict[str, dict]:
    """Generate cover letters (as PDFs) for all jobs in jobs_selected.json.

    No external scraping tool is needed: each job's full_description (captured at Scout
    time) is passed inline in the prompt, so this stage is a pure LLM call with no MCP
    server dependency."""
    jobs = load_selected_jobs()
    profile = load_profile()

    print(f"✅ Loaded {len(jobs)} selected jobs")

    letters: dict[str, dict] = {}

    if save:
        OUTPUT_DIR.mkdir(exist_ok=True)

    for job in jobs:
        letter = await generate_letter_for_job(job, profile)
        key = f"{job.get('company', 'company')}_{job.get('title', 'role')}"
        letters[key] = letter

        if save:
            filename = f"{slugify(job.get('company',''))}_{slugify(job.get('title',''))}.pdf"
            out_path = OUTPUT_DIR / filename
            render_cover_letter_pdf(letter, job, out_path)
            print(f"   💾 Saved → {out_path}")

    print(f"\n✅ Generated {len(letters)} cover letter(s)")
    return letters


def main():
    import asyncio
    asyncio.run(run_cover_letters())


if __name__ == "__main__":
    main()
