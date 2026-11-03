from pathlib import Path


def record_email_tool(email: str) -> str:
    email_file = Path(__file__).parent / "emails.txt"
    email_file.write_text(email + "\n")

    return f"Email {email} recorded successfully."
