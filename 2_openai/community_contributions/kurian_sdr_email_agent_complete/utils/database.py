"""
database.py — SQLite conversation history using SQLAlchemy
Stores every email sent and every reply received, so the SDR agent
has full context when crafting a follow-up.
"""

from sqlalchemy import create_engine, Column, String, Text, DateTime, Integer
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime

DATABASE_URL = "sqlite:///./conversations.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()


class EmailThread(Base):
    """One row per email (sent or received) in a conversation thread."""
    __tablename__ = "email_threads"

    id          = Column(Integer, primary_key=True, index=True)
    thread_id   = Column(String, index=True)        # groups a conversation together
    direction   = Column(String)                    # "sent" | "received"
    sender      = Column(String)
    recipient   = Column(String)
    subject     = Column(String)
    body        = Column(Text)
    timestamp   = Column(DateTime, default=datetime.utcnow)


def init_db():
    Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ── Helpers ──────────────────────────────────────────────────────────────────

def save_email(db, *, thread_id: str, direction: str,
               sender: str, recipient: str, subject: str, body: str):
    row = EmailThread(
        thread_id=thread_id,
        direction=direction,
        sender=sender,
        recipient=recipient,
        subject=subject,
        body=body,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def get_thread_history(db, thread_id: str) -> list[EmailThread]:
    """Return all emails in a thread ordered oldest-first."""
    return (
        db.query(EmailThread)
        .filter(EmailThread.thread_id == thread_id)
        .order_by(EmailThread.timestamp)
        .all()
    )
