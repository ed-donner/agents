import base64
import re
from email.mime.text import MIMEText

from agents import trace, Runner
from dotenv import load_dotenv
from fastapi import FastAPI, Request

import local_agents
from sqlite_tools import init_db, save_thread, is_watched_thread, save_history_id, get_last_history_id, is_replied, mark_replied
from tools import register_gmail_watch, send_email, get_gmail_service
import os
import json

load_dotenv(override=True)

app = FastAPI(title="SendGrid Full Chain Inbound Handler")

DB_FILE = "threads.db"
TOKEN_FILE = "token.json"


def get_thread_history(service, thread_id):
    """Fetch full conversation thread with actual message bodies."""
    thread = service.users().threads().get(
        userId="me",
        id=thread_id,
        format="full"
    ).execute()

    messages = []
    for msg in thread.get("messages", []):
        headers = {h["name"]: h["value"] for h in msg["payload"]["headers"]}

        # Extract body
        body = ""
        payload = msg.get("payload", {})
        if payload.get("body", {}).get("data"):
            body = base64.urlsafe_b64decode(payload["body"]["data"]).decode("utf-8")
        elif payload.get("parts"):
            for part in payload["parts"]:
                if part["mimeType"] == "text/plain" and part["body"].get("data"):
                    body = base64.urlsafe_b64decode(part["body"]["data"]).decode("utf-8")
                    break

        messages.append({
            "from": headers.get("From", ""),
            "date": headers.get("Date", ""),
            "subject": headers.get("Subject", ""),
            "body": body
        })

    return messages



def extract_email(from_header):
    """Extract just the email address from 'Name <email>' format."""
    match = re.search(r'<(.+?)>', from_header)
    return match.group(1).lower() if match else from_header.lower()


async def reply_to_thread(service, thread_id, to, subject):

    history = get_thread_history(service, thread_id)
    print(history)

    reply_agent_system_prompt = f"""
    Here is the full history of the conversation: {history}. 
    Your name is James. 
    You are a reply agent working for Translife Solar Solutions. 
    Based on the history of what you read, you will reply in a professional manner and within the context of the history. 
    In your reply,
        - Sound Human,
        - Sound Engaging 
        - Make sure you do not include any intermediate notes like (here is a professional and engaging reply based on ...). 
        - Write in html code so that the email can be neat. 
    """
    reply_agent = local_agents.build_deep_seek_agent(name="James", instructions=reply_agent_system_prompt)
    result = ""
    with trace("reply_agent_james"):
        result = await Runner.run(reply_agent, "Reply in a professional manner and engaging manner")

    body = f"{result.final_output}"
    message = MIMEText(body, "html")
    message["to"] = to
    message["subject"] = f"Re: {subject}"
    message["In-Reply-To"] = thread_id
    message["References"] = thread_id

    encoded = base64.urlsafe_b64encode(message.as_bytes()).decode()

    result = service.users().messages().send(
        userId="me",
        body={
            "raw": encoded,
            "threadId": thread_id
        }
    ).execute()
    print(f"Reply sent! Message ID: {result['id']}")


@app.post("/inbound-reply")
async def inbound_reply(request: Request):
    try:
        MY_EMAIL = os.getenv("MY_EMAIL", "").lower()

        envelope = await request.json()
        pubsub_message = envelope.get("message", {})
        data = json.loads(base64.b64decode(pubsub_message["data"]).decode("utf-8"))

        print(f"Notification received: {data}")

        new_history_id = data.get("historyId")
        if not new_history_id:
            return {"status": "no historyId"}

        last_history_id = get_last_history_id()
        print(f"Last history ID: {last_history_id}, New: {new_history_id}")

        if not last_history_id:
            print("No previous historyId, bootstrapping.")
            save_history_id(new_history_id)
            return {"status": "ok"}

        # Only move forward, never replay old history
        if int(new_history_id) <= int(last_history_id):
            print(f"Ignoring older historyId {new_history_id}, keeping {last_history_id}")
            return {"status": "ok"}

        service = get_gmail_service()

        history = service.users().history().list(
            userId="me",
            startHistoryId=last_history_id,
            historyTypes=["messageAdded"],
            labelId="INBOX",
        ).execute()

        print(f"History records found: {len(history.get('history', []))}")

        latest_replies = {}

        for record in history.get("history", []):
            for added in record.get("messagesAdded", []):
                thread_id = added["message"]["threadId"]
                msg_id = added["message"]["id"]

                try:
                    msg = service.users().messages().get(
                        userId="me", id=msg_id, format="metadata",
                        metadataHeaders=["From", "In-Reply-To"]
                    ).execute()
                except Exception as e:
                    print(f"Skipping message {msg_id}, could not fetch: {e}")
                    continue

                headers = {h["name"]: h["value"] for h in msg["payload"]["headers"]}
                from_raw = headers.get("From", "")
                from_email = extract_email(from_raw)
                in_reply_to = headers.get("In-Reply-To", "")

                print(f"from_raw: {from_raw}")
                print(f"from_email extracted: {from_email}")
                print(f"MY_EMAIL: {MY_EMAIL}")
                print(f"Match: {MY_EMAIL in from_email}")
                print(f"In-Reply-To: {in_reply_to}, Thread: {thread_id}")

                # Skip own messages
                if MY_EMAIL and MY_EMAIL in from_email:
                    print(f"Skipping own message in thread {thread_id}")
                    continue

                # Skip non-replies
                if not in_reply_to:
                    print(f"Not a reply, skipping.")
                    continue

                # Check if thread is watched
                details = is_watched_thread(thread_id)
                print(f"DB lookup for thread {thread_id}: {details}")

                if not details:
                    print(f"Thread {thread_id} not watched, ignoring.")
                    continue

                subject = details[1] if details[1] else "No Subject"

                # Store only the latest message per thread
                # Reply to whoever sent the inbound reply
                latest_replies[thread_id] = {
                    "to": from_email,
                    "subject": subject,
                    "msg_id": msg_id,
                }

        # Reply once per thread using the latest message only
        for thread_id, reply_info in latest_replies.items():
            try:
                if is_replied(reply_info["msg_id"]):
                    print(f"Already replied to msg {reply_info['msg_id']}, skipping.")
                    continue

                print(f"Replying to {reply_info['to']} on thread {thread_id}, latest msg {reply_info['msg_id']}")
                await reply_to_thread(service, thread_id, reply_info["to"], reply_info["subject"])
                mark_replied(reply_info["msg_id"])

            except Exception as e:
                import traceback
                print(f"Error replying to thread {thread_id}:\n{traceback.format_exc()}")

        save_history_id(new_history_id)
        return {"status": "ok"}

    except Exception as e:
        import traceback
        print(f"Error:\n{traceback.format_exc()}")
        return {"status": "error", "message": str(e)}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)