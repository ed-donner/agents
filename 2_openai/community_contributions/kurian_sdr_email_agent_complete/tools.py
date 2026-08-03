import uuid

from agents import function_tool
import base64
from email.mime.text import MIMEText

from dotenv import load_dotenv
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from sqlite_tools import init_db, save_thread
import os


load_dotenv(override=True)

SCOPES = ["https://www.googleapis.com/auth/gmail.send", "https://www.googleapis.com/auth/gmail.readonly"]
CREDENTIALS_FILE = "credentials.json"
TOKEN_FILE = "token.json"

init_db()


def get_gmail_service():
    creds = None

    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())

        else:
            # Build client config from env vars instead of JSON file.
            client_config = {
                "installed" : {
                    "client_id" : os.getenv("GOOGLE_CLIENT_ID"),
                    "client_secret": os.getenv("GOOGLE_CLIENT_SECRET"),
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "redirect_uris": ["http://localhost"]
                }
            }

            flow = InstalledAppFlow.from_client_config(client_config, SCOPES)
            creds = flow.run_local_server(port=0)

        with open(TOKEN_FILE, "w") as f:
            f.write(creds.to_json())

    return build("gmail", "v1", credentials=creds)




@function_tool
def send_email(from_email, to_email, subject, content):
    """
    Send an email from sender to recipient.
    :param from_email: Please use the email you were told in your instructions as a sender
    :param to_email: Please use the email that you were told in your instructions as a recipient
    :param subject: Subject of the email
    :param content: HTML content of the email
    :return:
    """
    service = get_gmail_service()

    message = MIMEText(content, "html")
    message['to'] = to_email
    message['from'] = from_email
    message['subject'] = subject

    encoded = base64.urlsafe_b64encode(message.as_bytes()).decode()

    result = service.users().messages().send(
        userId="me",
        body ={"raw": encoded}
    ).execute()

    thread_id = result["threadId"]
    save_thread(thread_id, to_email, subject)
    print(f"Email sent ! Message ID: {result["id"]} , Thread ID : {thread_id} saved to DB")
    return result



def register_gmail_watch():
    service = get_gmail_service()
    topic_name = "projects/indigo-union-382218/topics/gmail-notifications"
    response = service.users().watch(
        userId="me",
        body={
            "labelIds": ["INBOX"],
            "topicName": topic_name
        }
    ).execute()
    print(f"Watch registered! Expiry: {response['expiration']}")

