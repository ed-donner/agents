"""
webhook_server.py — FastAPI server for SendGrid Inbound Parse
─────────────────────────────────────────────────────────────
Setup steps (one-time):
  1. pip install fastapi uvicorn sqlalchemy python-multipart sendgrid ngrok
  2. Set env vars: SENDGRID_API_KEY, DEEPSEEK_API_KEY, OPENAI_API_KEY, FROM_EMAIL
  3. Run:  uvicorn webhook_server:app --port 8000
  4. In another terminal: ngrok http 8000
  5. Copy the ngrok HTTPS URL, e.g. https://abc123.ngrok.io
  6. In SendGrid dashboard:
       Settings → Inbound Parse → Add Host & URL
       URL = https://abc123.ngrok.io/inbound-email
       Check "POST the raw, full MIME message"

How it works:
  • SendGrid POSTs every inbound email to /inbound-email
  • We extract sender, subject, body, and derive a thread_id from the subject
  • Save the inbound email to SQLite
  • Load the full thread history
  • Pass everything to the SDR agent, which replies automatically
"""

import hashlib
import os
import asyncio

from fastapi import FastAPI, Form, Depends, Request
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
from sqlalchemy.orm import Session

from database import init_db, get_db, save_email, get_thread_history
from sdr_agent import handle_reply

load_dotenv(override=True)

app = FastAPI(title="ComplAI SDR Reply Handler")


@app.on_event("startup")
def startup():
    init_db()
    print("✅ Database initialised")


# ── Utility ───────────────────────────────────────────────────────────────────

def derive_thread_id(subject: str) -> str:
    """
    Strip Re:/Fwd: prefixes and hash the base subject to get a stable thread ID.
    e.g. "Re: Re: SOC2 demo?" and "SOC2 demo?" both map to the same thread.
    """
    base = subject.lower()
    for prefix in ("re:", "fwd:", "fw:"):
        while base.startswith(prefix):
            base = base[len(prefix):].strip()
    return hashlib.md5(base.encode()).hexdigest()


# ── Webhook endpoint ──────────────────────────────────────────────────────────

@app.post("/inbound-email")
async def inbound_email(
    request: Request,
    db: Session = Depends(get_db),
):
    """
    SendGrid Inbound Parse posts form-encoded data.
    Key fields: from, to, subject, text (plain body), html
    """
    form = await request.form()

    sender  = form.get("from", "unknown@example.com")
    to_addr = form.get("to", os.environ.get("FROM_EMAIL", ""))
    subject = form.get("subject", "(no subject)")
    body    = form.get("text") or form.get("html") or ""

    # Clean up sender — SendGrid often sends "Name <email@x.com>"
    if "<" in sender:
        prospect_email = sender.split("<")[-1].rstrip(">").strip()
    else:
        prospect_email = sender.strip()

    thread_id = derive_thread_id(subject)

    print(f"\n📨 Inbound email from {prospect_email}")
    print(f"   Subject  : {subject}")
    print(f"   Thread ID: {thread_id}")

    # 1. Persist the inbound email
    save_email(
        db,
        thread_id=thread_id,
        direction="received",
        sender=prospect_email,
        recipient=to_addr,
        subject=subject,
        body=body.strip(),
    )

    # 2. Load full thread history
    history = get_thread_history(db, thread_id)
    print(f"   Thread has {len(history)} message(s) so far")

    # 3. Let the SDR agent craft and send a reply (run in background so
    #    SendGrid doesn't time out waiting for us)
    asyncio.create_task(
        _reply_and_save(
            db_session_factory=None,   # we open a fresh session inside
            prospect_email=prospect_email,
            subject=subject,
            thread_id=thread_id,
            history=history,
            to_addr=to_addr,
        )
    )

    return JSONResponse({"status": "queued"}, status_code=200)


async def _reply_and_save(*, db_session_factory, prospect_email,
                          subject, thread_id, history, to_addr):
    """Generate the SDR reply, then persist it to the DB."""
    from database import SessionLocal, save_email as _save

    try:
        reply_body = await handle_reply(
            prospect_email=prospect_email,
            subject=subject,
            thread_history=history,
        )

        # Save the outbound reply
        db2 = SessionLocal()
        try:
            _save(
                db2,
                thread_id=thread_id,
                direction="sent",
                sender=to_addr,
                recipient=prospect_email,
                subject=f"Re: {subject}",
                body=reply_body,
            )
        finally:
            db2.close()

        print(f"✅ Reply sent to {prospect_email}")

    except Exception as e:
        print(f"❌ Error generating reply: {e}")


# ── Health check ──────────────────────────────────────────────────────────────

@app.get("/health")
def health():
    return {"status": "ok"}


# ── Thread viewer (handy for debugging) ───────────────────────────────────────

@app.get("/threads/{thread_id}")
def view_thread(thread_id: str, db: Session = Depends(get_db)):
    history = get_thread_history(db, thread_id)
    return [
        {
            "direction": row.direction,
            "sender": row.sender,
            "subject": row.subject,
            "body": row.body,
            "timestamp": row.timestamp.isoformat(),
        }
        for row in history
    ]


# ── Run directly ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("webhook_server:app", host="0.0.0.0", port=8000, reload=True)