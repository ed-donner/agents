"""
SDR Auto-Reply System
=====================
This module implements an automated Sales Development Representative (SDR) that:
1. Receives email replies via SendGrid Inbound Parse webhook
2. Tracks conversation history in SQLite
3. Uses AI agents to generate contextual responses
4. Sends automated follow-up emails

SETUP INSTRUCTIONS:
===================
1. Install ngrok: https://ngrok.com/download
2. Run this server: python sdr_auto_reply.py
3. In another terminal, run: ngrok http 5000
4. Copy the ngrok HTTPS URL (e.g., https://abc123.ngrok.io)
5. Go to SendGrid Dashboard:
   - Settings > Inbound Parse > Add Host & URL
   - Set your domain (or use SendGrid's test domain)
   - Set the webhook URL to: https://your-ngrok-url.ngrok.io/webhook/email
6. Configure your domain's MX records to point to: mx.sendgrid.net
   (Priority: 10)

For testing without a custom domain, you can use SendGrid's Inbound Parse
sandbox or forward emails manually.
"""

import os
import json
import sqlite3
import hashlib
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass
from flask import Flask, request, jsonify
from dotenv import load_dotenv
import sendgrid
from sendgrid.helpers.mail import Mail, Email, To, Content
import asyncio
from agents import Agent, Runner, trace, function_tool

load_dotenv(override=True)

# =============================================================================
# Database Setup - Conversation Tracking
# =============================================================================

DB_PATH = "sdr_conversations.db"

def init_db():
    """Initialize the SQLite database for conversation tracking."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Conversations table - tracks email threads
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS conversations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            thread_id TEXT UNIQUE NOT NULL,
            prospect_email TEXT NOT NULL,
            prospect_name TEXT,
            subject TEXT,
            status TEXT DEFAULT 'active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Messages table - stores all messages in a thread
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            thread_id TEXT NOT NULL,
            direction TEXT NOT NULL,  -- 'inbound' or 'outbound'
            sender TEXT NOT NULL,
            recipient TEXT NOT NULL,
            subject TEXT,
            body TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (thread_id) REFERENCES conversations(thread_id)
        )
    """)
    
    conn.commit()
    conn.close()
    print("✅ Database initialized")

def generate_thread_id(email: str, subject: str) -> str:
    """Generate a unique thread ID based on email and subject."""
    # Remove Re:, Fwd:, etc. from subject to group related emails
    clean_subject = subject.lower()
    for prefix in ['re:', 'fwd:', 'fw:', 're: ', 'fwd: ', 'fw: ']:
        clean_subject = clean_subject.replace(prefix, '')
    clean_subject = clean_subject.strip()
    
    # Create hash from email + cleaned subject
    key = f"{email.lower()}:{clean_subject}"
    return hashlib.md5(key.encode()).hexdigest()[:12]

def get_or_create_conversation(prospect_email: str, prospect_name: str, subject: str) -> str:
    """Get existing conversation or create a new one. Returns thread_id."""
    thread_id = generate_thread_id(prospect_email, subject)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT thread_id FROM conversations WHERE thread_id = ?", (thread_id,))
    existing = cursor.fetchone()
    
    if not existing:
        cursor.execute("""
            INSERT INTO conversations (thread_id, prospect_email, prospect_name, subject)
            VALUES (?, ?, ?, ?)
        """, (thread_id, prospect_email, prospect_name, subject))
        conn.commit()
        print(f"📝 Created new conversation thread: {thread_id}")
    else:
        cursor.execute("""
            UPDATE conversations SET updated_at = CURRENT_TIMESTAMP WHERE thread_id = ?
        """, (thread_id,))
        conn.commit()
        print(f"📝 Found existing conversation thread: {thread_id}")
    
    conn.close()
    return thread_id

def save_message(thread_id: str, direction: str, sender: str, recipient: str, 
                 subject: str, body: str):
    """Save a message to the conversation history."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO messages (thread_id, direction, sender, recipient, subject, body)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (thread_id, direction, sender, recipient, subject, body))
    
    conn.commit()
    conn.close()
    print(f"💾 Saved {direction} message to thread {thread_id}")

def get_conversation_history(thread_id: str) -> List[Dict]:
    """Retrieve all messages in a conversation thread."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT direction, sender, recipient, subject, body, created_at
        FROM messages
        WHERE thread_id = ?
        ORDER BY created_at ASC
    """, (thread_id,))
    
    messages = []
    for row in cursor.fetchall():
        messages.append({
            "direction": row[0],
            "sender": row[1],
            "recipient": row[2],
            "subject": row[3],
            "body": row[4],
            "timestamp": row[5]
        })
    
    conn.close()
    return messages

# =============================================================================
# Email Sending
# =============================================================================

YOUR_EMAIL = os.environ.get("SENDGRID_VERIFIED_SENDER", "srinidhiyerraguntala@gmail.com")

def send_reply_email(to_email: str, subject: str, body: str) -> Dict:
    """Send a reply email using SendGrid."""
    try:
        sg = sendgrid.SendGridAPIClient(api_key=os.environ.get('SENDGRID_API_KEY'))
        from_email = Email(YOUR_EMAIL)
        to_email_obj = To(to_email)
        
        # Ensure subject has Re: prefix for replies
        if not subject.lower().startswith('re:'):
            subject = f"Re: {subject}"
        
        content = Content("text/plain", body)
        mail = Mail(from_email, to_email_obj, subject, content).get()
        response = sg.client.mail.send.post(request_body=mail)
        
        print(f"📧 Sent reply to {to_email} (Status: {response.status_code})")
        return {"status": "success", "code": response.status_code}
    except Exception as e:
        print(f"❌ Failed to send email: {e}")
        return {"status": "error", "message": str(e)}

# =============================================================================
# AI Agent for Response Generation
# =============================================================================

sdr_instructions = """You are an AI Sales Development Representative (SDR) for ComplAI, 
a company that provides a SaaS tool for ensuring SOC2 compliance and preparing for audits, powered by AI.

Your role is to continue sales conversations via email. You are:
- Professional but personable
- Focused on understanding the prospect's needs
- Knowledgeable about SOC2 compliance challenges
- Goal-oriented: moving prospects toward a demo/meeting

When responding to emails:
1. Acknowledge what the prospect said
2. Address any questions or concerns they raised
3. Provide value (insights, relevant info)
4. Include a clear call-to-action (schedule demo, call, etc.)

Keep responses concise (under 200 words) and conversational.
Do NOT include subject lines - just the email body.
Sign off as "The ComplAI Team" unless you have a specific rep name."""

sdr_agent = Agent(
    name="SDR Agent",
    instructions=sdr_instructions,
    model="gpt-4o-mini"
)

async def generate_response(conversation_history: List[Dict], latest_message: str) -> str:
    """Use AI agent to generate a contextual response."""
    
    # Build context from conversation history
    context_parts = ["Here is the conversation history:\n"]
    
    for msg in conversation_history:
        direction = "PROSPECT" if msg["direction"] == "inbound" else "SDR (us)"
        context_parts.append(f"[{direction}]: {msg['body']}\n---\n")
    
    context = "".join(context_parts)
    
    prompt = f"""{context}

The prospect just replied with:
"{latest_message}"

Write a professional follow-up email response to continue the sales conversation. 
Remember to address their message and move the conversation toward scheduling a demo."""

    with trace("SDR Auto-Reply"):
        result = await Runner.run(sdr_agent, prompt)
        return result.final_output

# =============================================================================
# Flask Webhook Server
# =============================================================================

app = Flask(__name__)

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({"status": "healthy", "service": "SDR Auto-Reply"})

@app.route('/webhook/email', methods=['POST'])
def receive_email():
    """
    SendGrid Inbound Parse Webhook endpoint.
    
    SendGrid sends POST requests with the following form fields:
    - from: Sender email
    - to: Recipient email  
    - subject: Email subject
    - text: Plain text body
    - html: HTML body (if available)
    - envelope: JSON with sender/recipient info
    - headers: Email headers
    - attachments: Number of attachments
    """
    try:
        # Extract email data from SendGrid POST
        sender_email = request.form.get('from', '')
        # Parse email address from "Name <email@example.com>" format
        if '<' in sender_email and '>' in sender_email:
            sender_name = sender_email.split('<')[0].strip().strip('"')
            sender_email = sender_email.split('<')[1].split('>')[0]
        else:
            sender_name = sender_email.split('@')[0]
        
        recipient = request.form.get('to', '')
        subject = request.form.get('subject', 'No Subject')
        text_body = request.form.get('text', '')
        html_body = request.form.get('html', '')
        
        # Prefer text body, fall back to HTML
        body = text_body if text_body else html_body
        
        # Clean up the body (remove quoted replies for cleaner processing)
        body = clean_email_body(body)
        
        print("\n" + "="*60)
        print("📨 INCOMING EMAIL RECEIVED")
        print("="*60)
        print(f"From: {sender_name} <{sender_email}>")
        print(f"Subject: {subject}")
        print(f"Body preview: {body[:200]}...")
        print("="*60 + "\n")
        
        # Get or create conversation thread
        thread_id = get_or_create_conversation(sender_email, sender_name, subject)
        
        # Save the incoming message
        save_message(
            thread_id=thread_id,
            direction="inbound",
            sender=sender_email,
            recipient=recipient,
            subject=subject,
            body=body
        )
        
        # Get conversation history
        history = get_conversation_history(thread_id)
        
        # Generate AI response
        print("🤖 Generating AI response...")
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        response_body = loop.run_until_complete(generate_response(history, body))
        loop.close()
        
        print(f"📝 Generated response:\n{response_body[:300]}...")
        
        # Send the reply
        send_result = send_reply_email(sender_email, subject, response_body)
        
        # Save the outbound message
        if send_result["status"] == "success":
            save_message(
                thread_id=thread_id,
                direction="outbound",
                sender=YOUR_EMAIL,
                recipient=sender_email,
                subject=f"Re: {subject}" if not subject.lower().startswith('re:') else subject,
                body=response_body
            )
        
        return jsonify({
            "status": "processed",
            "thread_id": thread_id,
            "response_sent": send_result["status"] == "success"
        }), 200
        
    except Exception as e:
        print(f"❌ Error processing webhook: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"status": "error", "message": str(e)}), 500

def clean_email_body(body: str) -> str:
    """
    Clean up email body by removing quoted replies and signatures.
    This helps the AI focus on the new content.
    """
    lines = body.split('\n')
    cleaned_lines = []
    
    for line in lines:
        # Stop at common reply indicators
        if line.strip().startswith('>'):
            continue
        if 'On ' in line and ' wrote:' in line:
            break
        if line.strip().startswith('From:') and '@' in line:
            break
        if '-------- Original Message --------' in line:
            break
        if line.strip() == '--':  # Signature delimiter
            break
            
        cleaned_lines.append(line)
    
    return '\n'.join(cleaned_lines).strip()

@app.route('/conversations', methods=['GET'])
def list_conversations():
    """List all conversation threads."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT c.thread_id, c.prospect_email, c.prospect_name, c.subject, 
               c.status, c.created_at, COUNT(m.id) as message_count
        FROM conversations c
        LEFT JOIN messages m ON c.thread_id = m.thread_id
        GROUP BY c.thread_id
        ORDER BY c.updated_at DESC
    """)
    
    conversations = []
    for row in cursor.fetchall():
        conversations.append({
            "thread_id": row[0],
            "prospect_email": row[1],
            "prospect_name": row[2],
            "subject": row[3],
            "status": row[4],
            "created_at": row[5],
            "message_count": row[6]
        })
    
    conn.close()
    return jsonify(conversations)

@app.route('/conversations/<thread_id>', methods=['GET'])
def get_conversation(thread_id):
    """Get full conversation history for a thread."""
    history = get_conversation_history(thread_id)
    return jsonify(history)

@app.route('/test/simulate', methods=['POST'])
def simulate_incoming_email():
    """
    Test endpoint to simulate an incoming email without needing SendGrid webhook.
    
    Send a POST request with JSON body:
    {
        "from": "prospect@example.com",
        "name": "John Doe",
        "subject": "Re: SOC2 Compliance",
        "body": "Hi, I'm interested in learning more about your solution."
    }
    """
    data = request.json
    
    sender_email = data.get('from', 'test@example.com')
    sender_name = data.get('name', 'Test User')
    subject = data.get('subject', 'Test Subject')
    body = data.get('body', 'This is a test message.')
    
    print("\n" + "="*60)
    print("🧪 SIMULATED EMAIL RECEIVED")
    print("="*60)
    print(f"From: {sender_name} <{sender_email}>")
    print(f"Subject: {subject}")
    print(f"Body: {body}")
    print("="*60 + "\n")
    
    # Get or create conversation thread
    thread_id = get_or_create_conversation(sender_email, sender_name, subject)
    
    # Save the incoming message
    save_message(
        thread_id=thread_id,
        direction="inbound",
        sender=sender_email,
        recipient=YOUR_EMAIL,
        subject=subject,
        body=body
    )
    
    # Get conversation history
    history = get_conversation_history(thread_id)
    
    # Generate AI response
    print("🤖 Generating AI response...")
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    response_body = loop.run_until_complete(generate_response(history, body))
    loop.close()
    
    print(f"\n📝 Generated response:\n{'-'*40}\n{response_body}\n{'-'*40}\n")
    
    # Send the reply
    send_result = send_reply_email(sender_email, subject, response_body)
    
    # Save the outbound message
    if send_result["status"] == "success":
        save_message(
            thread_id=thread_id,
            direction="outbound",
            sender=YOUR_EMAIL,
            recipient=sender_email,
            subject=f"Re: {subject}" if not subject.lower().startswith('re:') else subject,
            body=response_body
        )
    
    return jsonify({
        "status": "processed",
        "thread_id": thread_id,
        "response_body": response_body,
        "email_sent": send_result["status"] == "success"
    }), 200

# =============================================================================
# Main Entry Point
# =============================================================================

if __name__ == '__main__':
    print("""
╔══════════════════════════════════════════════════════════════════╗
║                    SDR AUTO-REPLY SYSTEM                         ║
╠══════════════════════════════════════════════════════════════════╣
║  This server receives email replies and auto-responds using AI   ║
║                                                                  ║
║  ENDPOINTS:                                                      ║
║  • GET  /health           - Health check                         ║
║  • POST /webhook/email    - SendGrid Inbound Parse webhook       ║
║  • GET  /conversations    - List all conversation threads        ║
║  • GET  /conversations/<id> - Get conversation history           ║
║  • POST /test/simulate    - Simulate incoming email (for testing)║
║                                                                  ║
║  SETUP:                                                          ║
║  1. Run: ngrok http 5000                                         ║
║  2. Copy ngrok URL to SendGrid Inbound Parse settings            ║
║  3. Configure MX records for your domain                         ║
╚══════════════════════════════════════════════════════════════════╝
    """)
    
    # Initialize database
    init_db()
    
    # Run the Flask server
    app.run(host='0.0.0.0', port=5000, debug=True)

