#!/usr/bin/env python
import sys
import warnings
import os
import json
os.makedirs('output', exist_ok=True)

from dotenv import load_dotenv
load_dotenv()

from interview_prep.crew import InterviewPrepCrew

warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")


def get_job_description() -> str:
    """Collect optional multiline JD from user. Press Enter twice to skip."""
    print("\nPaste the Job Description below (optional).")
    print("Press Enter twice when done, or just Enter twice to skip:\n")
    lines = []
    while True:
        try:
            line = input()
        except EOFError:
            break
        if line == "" and lines and lines[-1] == "":
            break
        lines.append(line)
    jd = "\n".join(lines).strip().rstrip("")
    return jd if jd else "No specific job description provided."


def run_mock_interview(company: str, role: str, prep_context: str):
    """Interactive mock interview session powered by Gemini."""
    try:
        from google import genai as google_genai
    except ImportError:
        print("\ngoogle-genai not installed. Skipping mock interview.")
        return

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("\nGEMINI_API_KEY not found in .env — skipping mock interview.")
        return

    client = google_genai.Client(api_key=api_key)

    system_instruction = f"""You are a senior technical interviewer at {company} conducting a realistic mock {role} interview.

You have the following preparation context about this role and company:
{prep_context}

Your interview style:
- Ask exactly ONE question at a time. Wait for the candidate's response before continuing.
- Cover all rounds in sequence: start with a warm intro, then Behavioral, Domain-specific.
- After each answer, give 2-3 sentences of constructive feedback before asking the next question.
- Be realistic — mix easy warm-up questions with harder ones.
- When the candidate says "quit" or "end", wrap up with an overall performance summary.

Begin now with a friendly introduction and your first question."""

    print("\n" + "=" * 60)
    print(f"  MOCK INTERVIEW  |  {role.title()} @ {company.title()}")
    print("=" * 60)
    print("  Type your answers below. Type 'quit' to end.\n")

    try:
        chat = client.chats.create(
            model="gemini-3.1-flash-lite",
            config={"system_instruction": system_instruction}
        )
        response = chat.send_message("Begin the interview.")
        print(f"Interviewer: {response.text}\n")

        while True:
            try:
                user_input = input("You: ").strip()
            except (EOFError, KeyboardInterrupt):
                break

            if not user_input:
                continue

            if user_input.lower() in ["quit", "exit", "end", "bye"]:
                response = chat.send_message(
                    "The candidate has ended the session. Give a warm closing and "
                    "an honest overall performance summary with 2-3 key strengths "
                    "and 2-3 areas to improve."
                )
                print(f"\nInterviewer: {response.text}\n")
                break

            response = chat.send_message(user_input)
            print(f"\nInterviewer: {response.text}\n")

    except Exception as e:
        print(f"\nMock interview error: {e}")


def run():
    """Run the full interview prep crew, then optionally start a mock interview."""
    company = input("Company name: ").strip()
    role = input("Role (e.g. Software Engineer): ").strip()

    if not company or not role:
        print("Both company and role are required.")
        sys.exit(1)

    job_description = get_job_description()

    inputs = {
        "company": company,
        "role": role,
        "job_description": job_description,
    }

    try:
        result = InterviewPrepCrew().crew().kickoff(inputs=inputs)

        # Save structured pydantic output as JSON if available
        if result.pydantic:
            with open("output/prep_guide.json", "w", encoding="utf-8") as f:
                json.dump(result.pydantic.model_dump(), f, indent=2, ensure_ascii=False)
            print("\n✓ Structured prep guide → output/prep_guide.json")
            print("✓ Raw prep guide      → output/prep_guide.md")
            print("✓ Resources           → output/resources.md")
            prep_context = result.raw
        else:
            print("\n✓ Prep guide  → output/prep_guide.md")
            print("✓ Resources   → output/resources.md")
            prep_context = result.raw

    except Exception as e:
        raise Exception(f"An error occurred while running the crew: {e}")

    # Optional mock interview
    print("\n" + "-" * 40)
    try:
        start_mock = input("Start a mock interview session? (y/n): ").strip().lower()
    except (EOFError, KeyboardInterrupt):
        return

    if start_mock == "y":
        run_mock_interview(company, role, prep_context)


def train():
    inputs = {"company": "Google", "role": "Software Engineer", "job_description": ""}
    try:
        InterviewPrepCrew().crew().train(
            n_iterations=int(sys.argv[1]), filename=sys.argv[2], inputs=inputs
        )
    except Exception as e:
        raise Exception(f"An error occurred while training the crew: {e}")


def replay():
    try:
        InterviewPrepCrew().crew().replay(task_id=sys.argv[1])
    except Exception as e:
        raise Exception(f"An error occurred while replaying the crew: {e}")


def test():
    inputs = {"company": "Google", "role": "Software Engineer", "job_description": ""}
    try:
        InterviewPrepCrew().crew().test(
            n_iterations=int(sys.argv[1]), eval_llm=sys.argv[2], inputs=inputs
        )
    except Exception as e:
        raise Exception(f"An error occurred while testing the crew: {e}")
