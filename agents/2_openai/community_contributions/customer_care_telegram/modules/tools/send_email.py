import smtplib
from email.mime.text import MIMEText
import os

def send_email(recipient: str, body: str):
    msg = MIMEText(body)
    msg["Subject"] = "Order Summary from Muallim"
    msg["From"] = "<your_email>"
    msg["To"] = recipient

    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()  # Enable TLS
            server.login("<your_email>", os.getenv("GMAIL_PASSWORD"))
            server.send_message(msg)
            print(f"Email sent successfully to {recipient}")
    except Exception as e:
        print(f"Failed to send email: {e}")