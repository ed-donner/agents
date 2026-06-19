import csv
import time
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib
import os
from dotenv import load_dotenv

load_dotenv(override=True)

# Ensure logs folder exists
os.makedirs("logs", exist_ok=True)

logging.basicConfig(
    filename="logs/email_logs.txt",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

SENDER_EMAIL = os.getenv("EMAIL")
APP_PASSWORD = os.getenv("APP_PASSWORD")

if not SENDER_EMAIL or not APP_PASSWORD:
    raise ValueError("EMAIL or APP_PASSWORD not found in .env")

def generate_email_body(investor_name: str) -> str:
    return f"""
Dear {investor_name},

I hope this message finds you well. We are reaching out because of your impressive track record in supporting innovative startups.
We believe our AI-driven startup aligns with your investment philosophy and would love to explore potential collaboration.

Best regards,
Philip
AI Startup Launcher
"""

def send_email(recipient_email: str, subject: str, body: str) -> bool:
    try:
        msg = MIMEMultipart()
        msg["From"] = SENDER_EMAIL
        msg["To"] = recipient_email
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))

        server = smtplib.SMTP("smtp.gmail.com", 587, timeout=60)
        server.ehlo()
        server.starttls()
        server.login(SENDER_EMAIL, APP_PASSWORD)

        server.sendmail(SENDER_EMAIL, recipient_email, msg.as_string())
        server.quit()

        logging.info(f"Email sent to {recipient_email}")
        return True

    except Exception as e:
        logging.error(f"Failed sending to {recipient_email}: {e}")
        return False

def send_bulk_emails(csv_path: str):
    with open(csv_path, newline="") as f:
        reader = csv.DictReader(f)

        for row in reader:
            name = row["Name"]
            email = row["Email"]

            body = generate_email_body(name)
            subject = "AI Startup Opportunity"

            success = send_email(email, subject, body)

            time.sleep(5)

            if success:
                print(f"Email sent to {email}")
            else:
                print(f"Failed to send email to {email}")

if __name__ == "__main__":
    send_bulk_emails("data/investors.csv")