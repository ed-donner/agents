import os
import shutil
import smtplib
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from typing import Any

from applicant import Applicant
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP
from schema import Evaluation, Evaluations, JobPost, JobPosts, Notification

load_dotenv(override=True)

mcp: FastMCP[Any] = FastMCP("applicant_server")

BASE_URL = Path(__file__).resolve().parent


@mcp.tool()
def save_job_post(name: str, job_post: JobPost):
    """
    Save the job posts to the database.
    """
    return Applicant.get(name).save_job_post(job_post)


@mcp.tool()
def read_job_post(name: str, job_post_id: int) -> JobPost:
    """
    Read a job post from the database.
    """
    return Applicant.get(name).read_job_post(job_post_id)


@mcp.tool()
def save_evaluation(name: str, evaluation: Evaluation):
    """
    Save an evaluation of a job post to the database.
    """
    return Applicant.get(name).save_evaluation(evaluation)


@mcp.tool()
def read_evaluation(name: str, job_post_id: int) -> Evaluation:
    """
    Read an evaluation for a job post from the database.
    """
    return Applicant.get(name).get_evaluation(job_post_id)


@mcp.tool()
def list_unevaluated_job_posts(name: str) -> JobPosts:
    """
    List job posts that have NOT yet been evaluated.
    """
    return Applicant.get(name).list_unevaluated_job_posts()


@mcp.tool()
def list_pending_evaluations(name: str) -> Evaluations:
    """
    List acceptable evaluations that have NOT yet had a notification sent.
    """
    return Applicant.get(name).list_pending_evaluations()


@mcp.tool()
def save_notification(name: str, notification: Notification) -> None:
    """
    Save a notification record to the database.
    """
    return Applicant.get(name).save_notification(notification)


@mcp.tool()
def save_artifact(company_name: str, job_id: int, filename: str, content: str) -> str:
    """
    Create sandbox/{company_name}-{job_id}/ directory and write a file there.
    Returns the absolute path of the saved file.
    """
    folder_name = f"{company_name.replace(' ', '_')}-{job_id}"
    artifact_dir = os.path.abspath(os.path.join(BASE_URL, "sandbox", folder_name))
    os.makedirs(artifact_dir, exist_ok=True)
    file_path = os.path.abspath(os.path.join(artifact_dir, filename))
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)
    return file_path


@mcp.tool()
def move_to_artifact(
    source_path: str, company_name: str, job_id: int, filename: str
) -> str:
    """
    Copy a file from source_path into sandbox/{company_name}-{job_id}/{filename}.
    Use this after create_pdf_from_markdown to move the generated PDF into the artifact folder.
    Returns the absolute destination path.
    """
    folder_name = f"{company_name.replace(' ', '_')}-{job_id}"
    artifact_dir = BASE_URL / "sandbox" / folder_name
    artifact_dir.mkdir(parents=True, exist_ok=True)
    dest_path = artifact_dir / filename
    shutil.copy2(source_path, dest_path)
    return str(dest_path.resolve())


@mcp.tool()
def send_notification_email(
    subject: str, body: str, attachment_paths: list[str]
) -> str:
    """
    Send an email to TO_EMAIL with the given subject, body, and PDF attachments.
    Returns 'Email sent successfully' or an error message.
    """
    from_email = os.getenv("FROM_EMAIL", "")
    to_email = os.getenv("TO_EMAIL", "")
    password = os.getenv("GOOGLE_APP_PASSWORD", "")
    host = os.getenv("EMAIL_HOST", "")
    port = int(os.getenv("EMAIL_PORT") or "465")

    if not all([from_email, to_email, password, host]):
        return "Failed: missing one or more env vars (FROM_EMAIL, TO_EMAIL, GOOGLE_APP_PASSWORD, EMAIL_HOST)"

    msg = MIMEMultipart()
    msg["From"] = from_email
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    for path in attachment_paths:
        try:
            with open(path, "rb") as f:
                part = MIMEApplication(f.read(), Name=Path(path).name)
            part["Content-Disposition"] = f'attachment; filename="{Path(path).name}"'
            msg.attach(part)
        except FileNotFoundError:
            return f"Failed: attachment not found at {path}"

    try:
        with smtplib.SMTP_SSL(host, port) as server:
            server.login(from_email, password)
            server.sendmail(from_email, to_email, msg.as_string())
        return "Email sent successfully"
    except Exception as e:
        return f"Failed to send email: {e}"


@mcp.resource("applicant://{name}/job_posts")
def list_job_posts(name: str) -> JobPosts:
    """
    List the job posts from the database.
    """
    return Applicant.get(name).list_job_posts()


@mcp.resource("applicant://{name}/profile")
def read_profile(name: str) -> Applicant:
    """
    Read the profile of the applicant from the database.
    """
    return Applicant.get(name)


if __name__ == "__main__":
    mcp.run(transport="sse")
