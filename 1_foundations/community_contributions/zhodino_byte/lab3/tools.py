from pathlib import Path


def record_email_tool(email: str) -> str:
    email_file = Path(__file__).parent / "emails.txt"
    with email_file.open(mode="a", encoding="utf-8") as file:
        file.write(email + "\n")

    return f"Email {email} recorded successfully."
