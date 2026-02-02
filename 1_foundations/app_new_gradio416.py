"""
IntellaPersona - Intellecta Solutions
Copyright © 2024-2025 Gönenç Aydın / Intellecta Solutions
All Rights Reserved - Patent Pending Technology

PROPRIETARY SOFTWARE - CONFIDENTIAL AND PROPRIETARY INFORMATION

This software and associated documentation files (the "Software") contain
proprietary and confidential information belonging to Intellecta Solutions.

UNAUTHORIZED COPYING, MODIFICATION, DISTRIBUTION, OR USE OF THIS SOFTWARE
IS STRICTLY PROHIBITED AND MAY RESULT IN SEVERE CIVIL AND CRIMINAL PENALTIES.

For licensing inquiries: contact@intellectasolutions.com
"""

from dotenv import load_dotenv
from openai import OpenAI
import json
import os
import requests
from pypdf import PdfReader
from functools import partial
import gradio as gr
import sqlite3
from datetime import datetime
import numpy as np
import secrets
import hashlib
from pathlib import Path

# ============================================
# CONFIGURATION FLAGS
# ============================================
# Set to True for development/testing (disables IP restrictions)
# Set to False for production deployment
TEST_MODE = False  # ✅ PRODUCTION MODE - IP restrictions enabled

# Security: Disable Gradio analytics and telemetry
os.environ["GRADIO_ANALYTICS_ENABLED"] = "False"
os.environ["GRADIO_SERVER_NAME"] = "0.0.0.0"

# Load .env from parent directory (agents/)
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path, override=True)

# ============================================
# UTILITY FUNCTIONS
# ============================================
def send_pushover_notification(title, message, priority=0):
    """Send notification via PushOver API"""
    pushover_user_key = os.getenv("PUSHOVER_USER")
    pushover_api_token = os.getenv("PUSHOVER_TOKEN")
    
    if not pushover_user_key or not pushover_api_token:
        print("⚠️ PushOver credentials not configured")
        return False
    
    try:
        response = requests.post(
            "https://api.pushover.net/1/messages.json",
            data={
                "token": pushover_api_token,
                "user": pushover_user_key,
                "title": title,
                "message": message,
                "priority": priority,
            },
            timeout=10
        )
        
        if response.status_code == 200:
            print(f"✅ PushOver notification sent: {title}")
            return True
        else:
            print(f"❌ PushOver error: {response.text}")
            return False
    except Exception as e:
        print(f"❌ PushOver exception: {e}")
        return False

# ============================================
# SECURITY: RATE LIMITING & SESSION MANAGEMENT
# ============================================
class SecurityManager:
    """Manage rate limiting, session timeout, and usage logging"""
    
    def __init__(self, db_path="career_bot.db"):
        self.db_path = db_path
        self.sessions = {}  # In-memory session store: {username: {last_activity: datetime, login_time: datetime}}
        self.rate_limits = {}  # Rate limiting: {username: {last_request: datetime, request_count: int}}
        self.init_security_tables()
    
    def init_security_tables(self):
        """Initialize security and logging tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Usage logging table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS usage_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT,
                action TEXT,
                details TEXT,
                ip_address TEXT,
                user_agent TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Session tracking table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS active_sessions (
                username TEXT PRIMARY KEY,
                login_time TIMESTAMP,
                last_activity TIMESTAMP,
                ip_address TEXT,
                expires_at TIMESTAMP
            )
        ''')
        
        # Rate limit violations table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS rate_limit_violations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT,
                violation_type TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def log_usage(self, username, action, details="", ip_address="unknown"):
        """Log user activity"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO usage_logs (username, action, details, ip_address)
            VALUES (?, ?, ?, ?)
        ''', (username, action, details, ip_address))
        
        conn.commit()
        conn.close()
    
    def create_session(self, username, session_timeout_minutes=30):
        """Create new session with timeout"""
        now = datetime.now()
        expires_at = now + timedelta(minutes=session_timeout_minutes)
        
        self.sessions[username] = {
            "login_time": now,
            "last_activity": now,
            "expires_at": expires_at
        }
        
        # Save to database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO active_sessions 
            (username, login_time, last_activity, expires_at)
            VALUES (?, ?, ?, ?)
        ''', (username, now, now, expires_at))
        
        conn.commit()
        conn.close()
        
        self.log_usage(username, "session_created", f"Expires at {expires_at}")
        return True
    
    def check_session_valid(self, username):
        """Check if session is still valid"""
        if username not in self.sessions:
            # Try to load from database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                SELECT login_time, last_activity, expires_at 
                FROM active_sessions 
                WHERE username = ?
            ''', (username,))
            result = cursor.fetchone()
            conn.close()
            
            if not result:
                return False, "No active session"
            
            login_time, last_activity, expires_at = result
            self.sessions[username] = {
                "login_time": datetime.fromisoformat(login_time),
                "last_activity": datetime.fromisoformat(last_activity),
                "expires_at": datetime.fromisoformat(expires_at)
            }
        
        session = self.sessions[username]
        now = datetime.now()
        
        # Check if session expired
        if now > session["expires_at"]:
            self.destroy_session(username)
            return False, "Session expired - please login again"
        
        # Update last activity
        session["last_activity"] = now
        return True, "Session valid"
    
    def update_session_activity(self, username):
        """Update last activity timestamp"""
        if username in self.sessions:
            now = datetime.now()
            self.sessions[username]["last_activity"] = now
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE active_sessions 
                SET last_activity = ? 
                WHERE username = ?
            ''', (now, username))
            conn.commit()
            conn.close()
    
    def destroy_session(self, username):
        """Destroy user session"""
        if username in self.sessions:
            del self.sessions[username]
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('DELETE FROM active_sessions WHERE username = ?', (username,))
        conn.commit()
        conn.close()
        
        self.log_usage(username, "session_destroyed", "User logged out or session expired")
    
    def check_rate_limit(self, username, max_requests=10, time_window_seconds=60):
        """Check if user exceeded rate limit"""
        now = datetime.now()
        
        if username not in self.rate_limits:
            self.rate_limits[username] = {
                "first_request": now,
                "request_count": 1
            }
            return True, f"Rate limit: 1/{max_requests}"
        
        rate_data = self.rate_limits[username]
        time_passed = (now - rate_data["first_request"]).total_seconds()
        
        # Reset if time window passed
        if time_passed > time_window_seconds:
            self.rate_limits[username] = {
                "first_request": now,
                "request_count": 1
            }
            return True, f"Rate limit: 1/{max_requests}"
        
        # Check limit
        if rate_data["request_count"] >= max_requests:
            # Log violation
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO rate_limit_violations (username, violation_type)
                VALUES (?, ?)
            ''', (username, f"Exceeded {max_requests} requests in {time_window_seconds}s"))
            conn.commit()
            conn.close()
            
            wait_time = int(time_window_seconds - time_passed)
            return False, f"⚠️ Rate limit exceeded! Please wait {wait_time} seconds."
        
        # Increment counter
        rate_data["request_count"] += 1
        return True, f"Rate limit: {rate_data['request_count']}/{max_requests}"

from datetime import timedelta

# ============================================
# USER MANAGEMENT & AUTHENTICATION
# ============================================
class UserManager:
    def __init__(self, db_path="career_bot.db"):
        self.db_path = db_path
        self.init_user_tables()
    
    def init_user_tables(self):
        """Initialize user management tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Users table with tiers
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE,
                password_hash TEXT,
                email TEXT,
                tier TEXT DEFAULT 'visitor',
                query_count INTEGER DEFAULT 0,
                query_limit INTEGER DEFAULT 5,
                status TEXT DEFAULT 'pending',
                contact_submitted INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                approved_at TIMESTAMP,
                notes TEXT
            )
        ''')
        
        # Session tracking
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sessions (
                session_id TEXT PRIMARY KEY,
                username TEXT,
                last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (username) REFERENCES users(username)
            )
        ''')
        
        # Upgrade requests
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS upgrade_requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT,
                email TEXT,
                intent TEXT,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                processed_at TIMESTAMP,
                FOREIGN KEY (username) REFERENCES users(username)
            )
        ''')
        
        # IP tracking for visitor creation
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ip_tracking (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ip_address TEXT,
                username TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (username) REFERENCES users(username)
            )
        ''')
        
        # Credentials log - stores generated credentials for approved users
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS credentials_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                old_username TEXT,
                new_username TEXT,
                password_plain TEXT,
                email TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                sent_to_user BOOLEAN DEFAULT FALSE
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def hash_password(self, password):
        """Hash password using SHA-256"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def check_ip_visitor_limit(self, ip_address):
        """Check if IP already created a visitor account in last 24 hours"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT COUNT(*) FROM ip_tracking 
            WHERE ip_address = ? 
            AND created_at > datetime('now', '-24 hours')
        ''', (ip_address,))
        
        count = cursor.fetchone()[0]
        conn.close()
        
        return count > 0
    
    def create_visitor_account(self, ip_address=None):
        """Create a temporary visitor account"""
        username = f"visitor_{secrets.token_hex(4)}"
        password = secrets.token_urlsafe(8)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO users (username, password_hash, tier, query_limit)
            VALUES (?, ?, 'visitor', 5)
        ''', (username, self.hash_password(password)))
        
        # Track IP if provided
        if ip_address:
            cursor.execute('''
                INSERT INTO ip_tracking (ip_address, username)
                VALUES (?, ?)
            ''', (ip_address, username))
        
        conn.commit()
        conn.close()
        
        return username, password
    
    def authenticate(self, username, password):
        """Authenticate user and return user data"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT username, tier, query_count, query_limit, status
            FROM users
            WHERE username = ? AND password_hash = ?
        ''', (username, self.hash_password(password)))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return {
                "username": result[0],
                "tier": result[1],
                "query_count": result[2],
                "query_limit": result[3],
                "status": result[4]
            }
        return None
    
    def get_user_data(self, username):
        """Get user data without password"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT username, tier, query_count, query_limit, status, contact_submitted
            FROM users
            WHERE username = ?
        ''', (username,))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return {
                "username": result[0],
                "tier": result[1],
                "query_count": result[2],
                "query_limit": result[3],
                "status": result[4],
                "contact_submitted": result[5]
            }
        return None
    
    def increment_query_count(self, username):
        """Increment user's query count"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE users
            SET query_count = query_count + 1
            WHERE username = ?
        ''', (username,))
        
        cursor.execute('''
            SELECT query_count, query_limit FROM users WHERE username = ?
        ''', (username,))
        
        result = cursor.fetchone()
        conn.commit()
        conn.close()
        
        return result if result else (0, 5)
    
    def check_query_limit(self, username):
        """Check if user has remaining queries"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT query_count, query_limit, tier
            FROM users
            WHERE username = ?
        ''', (username,))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            query_count, query_limit, tier = result
            if tier == "unlimited":
                return True, float('inf'), float('inf')
            return query_count < query_limit, query_count, query_limit
        
        return False, 0, 0
    
    def request_upgrade(self, username, email, intent):
        """Request upgrade from visitor to unlimited"""
        # Email validation
        import re
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email):
            return False, "❌ Invalid email format. Please provide a valid email address."
        
        # Check if email already used
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT username FROM users WHERE email = ? AND username != ?', (email, username))
        existing = cursor.fetchone()
        
        if existing:
            conn.close()
            return False, f"❌ Email already registered with another account: {existing[0]}"
        
        # Update user email
        cursor.execute('''
            UPDATE users
            SET email = ?, notes = ?
            WHERE username = ?
        ''', (email, intent, username))
        
        # Create upgrade request
        cursor.execute('''
            INSERT INTO upgrade_requests (username, email, intent)
            VALUES (?, ?, ?)
        ''', (username, email, intent))
        
        request_id = cursor.lastrowid
        
        conn.commit()
        conn.close()
        
        # Send push notification with approval instructions
        push(f"""🔔 UPGRADE REQUEST #{request_id}

Username: {username}
Email: {email}
Intent: {intent}

To approve, run:
python admin_approve.py {username}

Or use the admin panel.""")
        
        return True, "✅ Request submitted successfully!"
    
    def approve_upgrade(self, username):
        """Approve user upgrade to unlimited tier and generate login credentials"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get user's email
        cursor.execute('SELECT email FROM users WHERE username = ?', (username,))
        user = cursor.fetchone()
        
        if not user or not user[0]:
            conn.close()
            return {"success": False, "error": "User email not found"}
        
        email = user[0]
        
        # Generate new credentials using email prefix
        email_prefix = email.split('@')[0]
        # Create unique username: email_prefix + random 4 chars
        new_username = f"{email_prefix}_{secrets.token_hex(2)}"
        new_password = secrets.token_urlsafe(12)  # Strong random password
        
        # Update user to unlimited with new credentials
        cursor.execute('''
            UPDATE users
            SET tier = 'unlimited', 
                query_limit = -1, 
                status = 'approved', 
                approved_at = ?,
                username = ?,
                password_hash = ?
            WHERE username = ?
        ''', (datetime.now(), new_username, self.hash_password(new_password), username))
        
        # Update request status with new username
        cursor.execute('''
            UPDATE upgrade_requests
            SET status = 'approved', processed_at = ?
            WHERE username = ? AND status = 'pending'
        ''', (datetime.now(), username))
        
        # Log the credentials for reference
        cursor.execute('''
            INSERT INTO credentials_log (old_username, new_username, password_plain, email)
            VALUES (?, ?, ?, ?)
        ''', (username, new_username, new_password, email))
        
        conn.commit()
        conn.close()
        
        return {
            "success": True,
            "username": new_username,
            "password": new_password,
            "email": email
        }

# ============================================
# NOTIFICATION SYSTEM
# ============================================
def push(text):
    try:
        requests.post(
            "https://api.pushover.net/1/messages.json",
            data={
                "token": os.getenv("PUSHOVER_TOKEN"),
                "user": os.getenv("PUSHOVER_USER"),
                "message": text,
            },
            timeout=5
        )
    except Exception as e:
        print(f"Push notification failed: {e}")

# ============================================
# TOOL FUNCTIONS
# ============================================
def record_user_details(email, name="Name not provided", notes="not provided"):
    push(f"Recording {name} with email {email} and notes {notes}")
    db = Database()
    db.save_contact(email, name, notes)
    return {"recorded": "ok", "message": f"Thank you {name}! I've recorded your details."}

def record_unknown_question(question):
    push(f"Unknown question: {question}")
    db = Database()
    db.save_unknown_question(question)
    return {"recorded": "ok"}

def search_knowledge_base(query):
    """Search the knowledge base for relevant information"""
    db = Database()
    results = db.search_qa(query)
    if results:
        return {"found": True, "results": results}
    return {"found": False, "message": "No relevant information found"}

# ============================================
# TOOL DEFINITIONS
# ============================================
record_user_details_json = {
    "name": "record_user_details",
    "description": "Use this tool to record that a user is interested in being in touch and provided an email address",
    "parameters": {
        "type": "object",
        "properties": {
            "email": {"type": "string", "description": "The email address of this user"},
            "name": {"type": "string", "description": "The user's name, if they provided it"},
            "notes": {"type": "string", "description": "Any additional information about the conversation"}
        },
        "required": ["email"],
        "additionalProperties": False
    }
}

record_unknown_question_json = {
    "name": "record_unknown_question",
    "description": "Always use this tool to record any question that couldn't be answered",
    "parameters": {
        "type": "object",
        "properties": {
            "question": {"type": "string", "description": "The question that couldn't be answered"}
        },
        "required": ["question"],
        "additionalProperties": False
    }
}

search_knowledge_base_json = {
    "name": "search_knowledge_base",
    "description": "Search the knowledge base for previously answered questions or additional context",
    "parameters": {
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "The search query or question to look up"}
        },
        "required": ["query"],
        "additionalProperties": False
    }
}

tools = [
    {"type": "function", "function": record_user_details_json},
    {"type": "function", "function": record_unknown_question_json},
    {"type": "function", "function": search_knowledge_base_json}
]

# ============================================
# HELPER FUNCTION: Cosine Similarity with NumPy
# ============================================
def cosine_similarity_numpy(vec1, vec2):
    """Calculate cosine similarity between two vectors"""
    vec1 = np.array(vec1)
    vec2 = np.array(vec2)
    
    dot_product = np.dot(vec1, vec2)
    norm1 = np.linalg.norm(vec1)
    norm2 = np.linalg.norm(vec2)
    
    if norm1 == 0 or norm2 == 0:
        return 0.0
    
    return dot_product / (norm1 * norm2)

# ============================================
# DATABASE CLASS
# ============================================
class Database:
    def __init__(self, db_path="career_bot.db"):
        self.db_path = db_path
        self.init_db()
        self.add_username_column_if_missing()  # Migration
    
    def init_db(self):
        """Initialize the database with required tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Contacts table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS contacts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT,
                email TEXT,
                reason TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (username) REFERENCES users(username)
            )
        ''')
        
        # Q&A knowledge base
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS knowledge_base (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                question TEXT,
                answer TEXT,
                category TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                used_count INTEGER DEFAULT 0
            )
        ''')
        
        # Unknown questions
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS unknown_questions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                question TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                resolved BOOLEAN DEFAULT FALSE
            )
        ''')
        
        # Conversation logs
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_message TEXT,
                bot_response TEXT,
                username TEXT DEFAULT 'anonymous',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def add_username_column_if_missing(self):
        """Migration: Add username column if it doesn't exist"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Check if column exists by trying to select it
            cursor.execute('SELECT username FROM conversations LIMIT 1')
        except sqlite3.OperationalError:
            # Column doesn't exist, add it
            cursor.execute('ALTER TABLE conversations ADD COLUMN username TEXT DEFAULT "anonymous"')
            conn.commit()
            print("✅ Added username column to conversations table")
        
        conn.close()
    
    def save_contact(self, email, name, notes):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO contacts (email, name, notes)
            VALUES (?, ?, ?)
        ''', (email, name, notes))
        conn.commit()
        conn.close()
    
    def save_qa(self, question, answer, category="general"):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO knowledge_base (question, answer, category)
            VALUES (?, ?, ?)
        ''', (question, answer, category))
        conn.commit()
        conn.close()
    
    def search_qa(self, query, limit=3):
        """Simple keyword-based search"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        keywords = query.lower().split()
        
        if not keywords:
            conn.close()
            return []
        
        like_conditions = " OR ".join(["question LIKE ? OR answer LIKE ?" for _ in keywords])
        like_params = []
        for keyword in keywords:
            like_params.extend([f'%{keyword}%', f'%{keyword}%'])
        
        cursor.execute(f'''
            SELECT question, answer, category, used_count
            FROM knowledge_base
            WHERE {like_conditions}
            ORDER BY used_count DESC
            LIMIT ?
        ''', (*like_params, limit))
        
        results = cursor.fetchall()
        
        if results:
            for result in results:
                cursor.execute('''
                    UPDATE knowledge_base 
                    SET used_count = used_count + 1
                    WHERE question = ?
                ''', (result[0],))
        
        conn.commit()
        conn.close()
        
        return [{"question": r[0], "answer": r[1], "category": r[2]} for r in results]
    
    def save_unknown_question(self, question):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO unknown_questions (question)
            VALUES (?)
        ''', (question,))
        conn.commit()
        conn.close()
    
    def save_conversation(self, user_message, bot_response, username="anonymous"):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO conversations (user_message, bot_response, username)
            VALUES (?, ?, ?)
        ''', (user_message, bot_response, username))
        conn.commit()
        conn.close()

# ============================================
# RAG KNOWLEDGE BASE
# ============================================
class KnowledgeBase:
    """Enhanced knowledge base with embeddings for better RAG"""
    
    def __init__(self, openai_client):
        self.openai = openai_client
        self.documents = []
        self.embeddings = []
    
    def add_document(self, text, metadata=None):
        """Add a document to the knowledge base"""
        if not text or len(text.strip()) == 0:
            return
        
        self.documents.append({"text": text, "metadata": metadata or {}})
        try:
            embedding = self.get_embedding(text)
            self.embeddings.append(embedding)
        except Exception as e:
            print(f"Error generating embedding: {e}")
            self.embeddings.append([0] * 1536)
    
    def get_embedding(self, text):
        """Get embedding from OpenAI"""
        response = self.openai.embeddings.create(
            model="text-embedding-3-small",
            input=text[:8000]
        )
        return response.data[0].embedding
    
    def search(self, query, top_k=2):
        """Search for relevant documents using cosine similarity"""
        if not self.documents or not self.embeddings:
            return []
        
        try:
            query_embedding = self.get_embedding(query)
            
            similarities = []
            for doc_embedding in self.embeddings:
                sim = cosine_similarity_numpy(query_embedding, doc_embedding)
                similarities.append(sim)
            
            top_indices = np.argsort(similarities)[-top_k:][::-1]
            
            results = []
            for idx in top_indices:
                if similarities[idx] > 0.5:
                    results.append({
                        "text": self.documents[idx]["text"],
                        "metadata": self.documents[idx]["metadata"],
                        "score": float(similarities[idx])
                    })
            
            return results
        except Exception as e:
            print(f"Error in RAG search: {e}")
            return []

# ============================================
# MAIN CLASS WITH USER MANAGEMENT
# ============================================
class Me:
    def __init__(self):
        self.openai = OpenAI()
        self.name = "Gönenç Aydın"
        self.db = Database()
        self.kb = KnowledgeBase(self.openai)
        self.user_manager = UserManager()
        self.security = SecurityManager()  # Security manager for rate limiting & sessions
        
        # Load LinkedIn profile
        try:
            reader = PdfReader("me/Profile.pdf")
            self.linkedin = ""
            for page in reader.pages:
                text = page.extract_text()
                if text:
                    self.linkedin += text
        except Exception as e:
            print(f"Error loading PDF: {e}")
            self.linkedin = "LinkedIn profile not available"
        
        # Load summary
        try:
            with open("me/summary.txt", "r", encoding="utf-8") as f:
                self.summary = f.read()
        except Exception as e:
            print(f"Error loading summary: {e}")
            self.summary = "Summary not available"
        
        # Initialize knowledge base
        self.init_knowledge_base()
        self.populate_initial_qa()
    
    def init_knowledge_base(self):
        """Add documents to the knowledge base for RAG"""
        if self.linkedin and len(self.linkedin) > 50:
            self.kb.add_document(self.linkedin, {"source": "linkedin", "type": "profile"})
        
        if self.summary and len(self.summary) > 50:
            self.kb.add_document(self.summary, {"source": "summary", "type": "overview"})
        
        # Load GitHub projects into knowledge base
        self.load_github_projects()
        
        # Load knowledge files (support multiple formats)
        if os.path.exists("me/knowledge"):
            for filename in os.listdir("me/knowledge"):
                # Support: .txt, .md, .json, .jsonl, .csv
                if filename.endswith((".txt", ".md", ".json", ".jsonl", ".csv")):
                    try:
                        filepath = os.path.join("me/knowledge", filename)
                        # Skip if it's a directory
                        if os.path.isfile(filepath):
                            content = self._load_knowledge_file(filepath, filename)
                            if content and len(content) > 50:
                                # Determine type based on filename
                                file_type = "persona" if "persona" in filename.lower() else "additional"
                                self.kb.add_document(
                                    content, 
                                    {
                                        "source": filename, 
                                        "type": file_type,
                                        "category": "knowledge_root",
                                        "format": filename.split(".")[-1]
                                    }
                                )
                                print(f"✅ Loaded {filename} into KB (knowledge_root)")
                    except Exception as e:
                        print(f"❌ Error loading {filename}: {e}")
    
    def _load_knowledge_file(self, filepath, filename):
        """Load knowledge file based on format"""
        import json
        import csv
        
        ext = filename.split(".")[-1].lower()
        
        try:
            if ext in ["txt", "md"]:
                # Plain text and markdown
                with open(filepath, "r", encoding="utf-8") as f:
                    return f.read()
            
            elif ext == "json":
                # JSON format - convert to readable text
                with open(filepath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    return self._json_to_text(data, filename)
            
            elif ext == "jsonl":
                # JSON Lines format - each line is a JSON object
                with open(filepath, "r", encoding="utf-8") as f:
                    lines = []
                    for line in f:
                        if line.strip():
                            obj = json.loads(line)
                            lines.append(self._json_to_text(obj))
                    return "\n\n---\n\n".join(lines)
            
            elif ext == "csv":
                # CSV format - convert to readable text
                with open(filepath, "r", encoding="utf-8") as f:
                    reader = csv.DictReader(f)
                    rows = []
                    for row in reader:
                        row_text = "\n".join([f"{k}: {v}" for k, v in row.items()])
                        rows.append(row_text)
                    return "\n\n---\n\n".join(rows)
            
            else:
                return None
                
        except Exception as e:
            print(f"❌ Error parsing {filename}: {e}")
            return None
    
    def _json_to_text(self, data, prefix=""):
        """Convert JSON data to readable text format"""
        if isinstance(data, dict):
            lines = []
            if prefix:
                lines.append(f"# {prefix}\n")
            for key, value in data.items():
                if isinstance(value, (dict, list)):
                    lines.append(f"## {key}")
                    lines.append(self._json_to_text(value))
                else:
                    lines.append(f"**{key}:** {value}")
            return "\n".join(lines)
        elif isinstance(data, list):
            return "\n".join([f"- {self._json_to_text(item)}" for item in data])
        else:
            return str(data)
    
    def load_github_projects(self):
        """Load GitHub project documentation into knowledge base"""
        project_dirs = [
            "me/knowledge/company",
            "me/knowledge/llmops", 
            "me/knowledge/agentic_projects",
            "me/knowledge/github_projects"
        ]
        
        for project_dir in project_dirs:
            if os.path.exists(project_dir):
                for filename in os.listdir(project_dir):
                    if filename.endswith(".md"):
                        try:
                            filepath = os.path.join(project_dir, filename)
                            with open(filepath, "r", encoding="utf-8") as f:
                                content = f.read()
                                if content and len(content) > 50:
                                    # Extract category from directory name
                                    category = os.path.basename(project_dir)
                                    self.kb.add_document(
                                        content, 
                                        {
                                            "source": filename, 
                                            "type": "project",
                                            "category": category
                                        }
                                    )
                                    print(f"✅ Loaded {filename} into KB ({category})")
                        except Exception as e:
                            print(f"Error loading {filename}: {e}")
    
    def populate_initial_qa(self):
        """Pre-populate the database with common Q&A"""
        common_qa = [
            ("What is your email?", "You can reach me through the contact form on my website.", "contact"),
            ("What are your main skills?", "I specialize in AI, machine learning, and software development.", "skills"),
            ("Where are you located?", "I'm based in Turkey.", "personal"),
        ]
        
        conn = sqlite3.connect(self.db.db_path)
        cursor = conn.cursor()
        
        for question, answer, category in common_qa:
            try:
                cursor.execute('''
                    INSERT OR IGNORE INTO knowledge_base (question, answer, category)
                    VALUES (?, ?, ?)
                ''', (question, answer, category))
            except Exception as e:
                print(f"Error inserting Q&A: {e}")
        
        conn.commit()
        conn.close()
    
    def handle_tool_call(self, tool_calls):
        results = []
        for tool_call in tool_calls:
            tool_name = tool_call.function.name
            arguments = json.loads(tool_call.function.arguments)
            print(f"Tool called: {tool_name} with args: {arguments}", flush=True)
            tool = globals().get(tool_name)
            result = tool(**arguments) if tool else {}
            results.append({
                "role": "tool",
                "content": json.dumps(result),
                "tool_call_id": tool_call.id
            })
        return results
    
    def system_prompt(self, rag_context="", user_tier="visitor", queries_remaining=5):
        tier_message = ""
        if user_tier == "visitor":
            tier_message = f"\n\n**Note to user**: You have {queries_remaining} queries remaining as a visitor. To get unlimited access, please provide your email and intent for reaching out."
        elif user_tier == "unlimited":
            tier_message = "\n\n**You have unlimited access to this chatbot.**"
        
        system_prompt = f"""You are acting as {self.name}, an AI Solutions Architect and the founder of Intellecta Solutions. 
You are answering questions on {self.name}'s professional website, representing him in a friendly, professional, and engaging manner.

**Your Communication Style:**
- Be warm and welcoming - always end responses with a follow-up question to keep the conversation going
- Show genuine interest in helping visitors learn about {self.name}'s work and Intellecta Solutions
- Be conversational but professional - imagine talking to a potential client or collaborator
- When providing information, invite visitors to ask more: "Is there anything specific about [topic] you'd like to know more about?"
- Encourage exploration: "Would you like to hear about Gönenç's experience with [related topic]?" or "Curious about Intellecta's other solutions?"

**About {self.name} & Intellecta Solutions:**
- **Intellecta Solutions**: AI-first company founded by {self.name}, specializing in enterprise AI/ML solutions
- **Core Focus**: LLMOps, Agentic AI Systems, DevSecOps Automation, Cloud Infrastructure
- **Recent Projects**: 
  - 🏢 **Company Portfolio**: Intellecta Website, TestBot Premium, CodeGuard Enterprise, BuildMaster Pro
  - 🤖 **LLMOps Tools**: Intellecta CLI, Intellecta Framework, Intellecta WhatsApp Bot  
  - 🏗️ **Agentic Systems**: SDLC Knowledge Library, KubeGenius, Web Orchestrator, CI/CD Agentic Flow
  - ☁️ **Infrastructure**: VSCode AWS Spot Terraform, WorkplaceSpace, Kubeflow Agent

**Your Expertise Areas (to confidently discuss):**
- AI/ML Engineering & LLMOps best practices
- Building production-grade agentic systems
- DevSecOps automation and CI/CD pipelines
- Kubernetes, cloud infrastructure (AWS, GCP)
- Enterprise software architecture
- Team leadership and technical mentorship

**Important Instructions:**
- Always search the knowledge base for relevant context before answering
- If you don't have specific information, use record_unknown_question tool
- When users show interest in collaboration, politely ask for their email using record_user_details tool
- **End EVERY response with an engaging question** like:
  - "Is there anything about Gönenç's work that particularly interests you?"
  - "Would you like to know more about Intellecta Solutions or any specific project?"
  - "Curious about how we approach [relevant topic]?"
  - "What brings you here today - are you exploring AI solutions or looking to collaborate?"

## Summary:
{self.summary}

## LinkedIn Profile:
{self.linkedin[:1000]}...

## Additional Context (RAG):
{rag_context}

{tier_message}

Remember: Be helpful, inviting, and always keep the conversation flowing with a friendly question!"""
        
        return system_prompt
    
    def chat(self, message, history, username="visitor"):
        try:
            # Check if user is logged in
            if not username or username == "visitor":
                return f"""👋 Welcome! To use this chatbot, please activate your visitor account first.

**Steps to get started:**
1. Go to the '🔐 Login / Sign Up' tab
2. Click 'Get Visitor Credentials'
3. You'll receive 5 free questions to learn about {self.name}

Looking forward to chatting with you! 😊"""
            
            # Check if message contains contact information (Email + Reason format)
            import re
            
            # More flexible regex patterns - handles both formats:
            # 1. "Email: xyz@mail.com\nReason: abc" (multi-line)
            # 2. "Email: xyz@mail.com / Reason: abc" (single-line with slash)
            # 3. "Email: xyz@mail.com Reason: abc" (single-line space-separated)
            email_pattern = r'(?i)email\s*:\s*([^\n/]+?)(?:\s*[/\n]|\s*reason\s*:|$)'
            reason_pattern = r'(?i)reason\s*:\s*([^\n/]+?)(?:\s*[/\n]|\s*email\s*:|$)'
            
            email_match = re.search(email_pattern, message)
            reason_match = re.search(reason_pattern, message)
            
            if email_match and reason_match:
                email = email_match.group(1).strip()
                reason = reason_match.group(1).strip()
                
                # Save to database
                self.user_manager.request_upgrade(username, email, reason)
                
                # Send PushOver notification
                send_pushover_notification(
                    title=f"📧 Contact Request from {username}",
                    message=f"""New contact request from chatbot:
                    
👤 Username: {username}
📧 Email: {email}
💬 Reason: {reason}

This user has completed their free queries and wants to continue the conversation.""",
                    priority=1
                )
                
                return f"""✅ **Thank you for providing your contact information!**

I've received your details:
- 📧 Email: {email}
- 💬 Reason: {reason}

**What happens next:**

1. ✅ Your request has been sent to {self.name}
2. 📬 I'll review your information within 24-48 hours
3. 📧 If approved, you'll receive an email with unlimited access credentials
4. 🎉 You can then continue our conversation without any limits!

**Why this process?**
I personally review each request to ensure quality conversations and to understand how I can best help you. Your information is kept confidential and will only be used to contact you regarding your request.

Thank you for your interest, and I look forward to connecting with you! 😊

---

*You can also submit a formal request via the **'⬆️ Request Unlimited Access'** tab if you prefer.*"""
            
            # SECURITY: Check session validity
            session_valid, session_msg = self.security.check_session_valid(username)
            if not session_valid:
                self.security.log_usage(username, "session_expired", session_msg)
                return f"""🔒 **Session Expired**

{session_msg}

Please go to the **'🔐 Login / Sign Up'** tab and login again.

Your credentials are still valid, just re-enter them to continue."""
            
            # SECURITY: Check rate limit
            rate_ok, rate_msg = self.security.check_rate_limit(username, max_requests=10, time_window_seconds=60)
            if not rate_ok:
                self.security.log_usage(username, "rate_limit_exceeded", rate_msg)
                return rate_msg
            
            # SECURITY: Update session activity
            self.security.update_session_activity(username)
            
            # SECURITY: Log this query
            self.security.log_usage(username, "chat_query", f"Message: {message[:100]}...")
            
            # Check query limit
            can_query, current_count, limit = self.user_manager.check_query_limit(username)
            
            if not can_query:
                return f"""🚫 You've reached your query limit ({limit} queries). 

**To continue our conversation:**

Please go to the '⬆️ Request Unlimited Access' tab and provide:
- Your email address
- Why you'd like to connect with {self.name}

I'll review your request and get back to you soon!"""
            
            # Increment query count
            current_count, limit = self.user_manager.increment_query_count(username)
            queries_remaining = limit - current_count if limit != -1 else float('inf')
            
            # Get user tier
            user_data = self.user_manager.get_user_data(username)
            user_tier = user_data["tier"] if user_data else "visitor"
            
            # Search knowledge base for relevant context (RAG)
            rag_results = self.kb.search(message, top_k=2)
            rag_context = "\n\n".join([f"- {r['text'][:200]}..." for r in rag_results]) if rag_results else "No additional context found."
            
            # Also search SQL database
            db_results = self.db.search_qa(message)
            if db_results:
                rag_context += "\n\n## From Knowledge Base:\n"
                for r in db_results:
                    rag_context += f"Q: {r['question']}\nA: {r['answer']}\n\n"
            
            messages = [
                {"role": "system", "content": self.system_prompt(rag_context, user_tier, queries_remaining)}
            ] + history + [
                {"role": "user", "content": message}
            ]
            
            done = False
            max_iterations = 5
            iteration = 0
            
            while not done and iteration < max_iterations:
                iteration += 1
                response = self.openai.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=messages,
                    tools=tools
                )
                
                if response.choices[0].finish_reason == "tool_calls":
                    message_obj = response.choices[0].message
                    tool_calls = message_obj.tool_calls
                    results = self.handle_tool_call(tool_calls)
                    messages.append(message_obj)
                    messages.extend(results)
                else:
                    done = True
            
            bot_response = response.choices[0].message.content
            
            # Add query count info for visitors
            if user_tier == "visitor" and queries_remaining <= 3:
                bot_response += f"\n\n---\n📊 **Queries remaining: {queries_remaining}/{limit}**"
            
            # Save conversation to database
            self.db.save_conversation(message, bot_response, username)
            
            return bot_response
        
        except Exception as e:
            print(f"Error in chat: {e}")
            return f"I apologize, but I encountered an error. Please try again. Error: {str(e)}"

# ============================================
# GRADIO INTERFACE WITH CUSTOM UI
# ============================================
def login_user(username, password):
    """Authenticate user"""
    user_manager = UserManager()
    security = SecurityManager()
    
    user_data = user_manager.authenticate(username, password)
    
    if user_data:
        # SECURITY: Create session (30 min timeout)
        security.create_session(username, session_timeout_minutes=30)
        security.log_usage(username, "login_success", f"Tier: {user_data['tier']}")
        
        if user_data["status"] == "approved":
            welcome_msg = f"""✅ **Welcome back, {username}!**

You have **unlimited access** to the chatbot. Feel free to ask anything!

🔒 Session expires in 30 minutes of inactivity."""
            return True, welcome_msg, user_data["username"]
        elif user_data["tier"] == "visitor":
            remaining = user_data["query_limit"] - user_data["query_count"]
            welcome_msg = f"""✅ **Welcome, {username}!**

You have **{remaining} queries remaining** as a visitor.

**Quick Start:**
- Ask about my experience and skills
- Learn about my projects
- Discuss potential collaborations

After {remaining} queries, you can request unlimited access!

🔒 Session expires in 30 minutes of inactivity."""
            return True, welcome_msg, user_data["username"]
        else:
            return True, f"✅ Logged in! Status: {user_data['status']}\n\n🔒 Session expires in 30 minutes.", user_data["username"]
    
    # SECURITY: Log failed login attempt
    security.log_usage(username, "login_failed", "Invalid credentials")
    return False, "❌ Invalid credentials. Please try again or create a visitor account.", None

def request_unlimited_access(username, email, intent):
    """Request upgrade to unlimited access"""
    user_manager = UserManager()
    security = SecurityManager()
    
    if not email or "@" not in email:
        return "❌ Please provide a valid email address."
    
    if not intent or len(intent) < 10:
        return "❌ Please provide a detailed intent (minimum 10 characters)."
    
    success, message = user_manager.request_upgrade(username, email, intent)
    
    if not success:
        return message  # Error message from validation
    
    # Log upgrade request
    security.log_usage(username, "upgrade_request", f"Email: {email}, Intent: {intent[:50]}...")
    
    if success:
        return f"""✅ **Upgrade request submitted!**

Your request has been sent to {me.name}.

**What happens next:**
1. {me.name} will review your request
2. If approved, you'll receive unlimited access
3. {me.name} will reach out to you at: {email}

You can continue using your remaining queries while waiting for approval.
        """
    else:
        return "❌ Failed to submit upgrade request. Please try again."

# ============================================
# LAUNCH WITH CUSTOM UI
# ============================================
if __name__ == "__main__":
    me = Me()
    
    # Custom CSS for gradient theme
    custom_css = """
    /* Logo pulsing glow animation with gradient colors */
    @keyframes logoPulse {
        0% {
            box-shadow: 0 0 20px rgba(30, 58, 138, 0.4),
                        0 0 40px rgba(59, 130, 246, 0.3),
                        0 0 60px rgba(96, 165, 250, 0.2),
                        0 4px 15px rgba(0, 0, 0, 0.2);
        }
        33% {
            box-shadow: 0 0 25px rgba(59, 130, 246, 0.6),
                        0 0 50px rgba(96, 165, 250, 0.5),
                        0 0 75px rgba(30, 58, 138, 0.3),
                        0 4px 18px rgba(0, 0, 0, 0.25);
        }
        66% {
            box-shadow: 0 0 30px rgba(96, 165, 250, 0.7),
                        0 0 60px rgba(30, 58, 138, 0.5),
                        0 0 90px rgba(59, 130, 246, 0.4),
                        0 4px 20px rgba(0, 0, 0, 0.3);
        }
        100% {
            box-shadow: 0 0 20px rgba(30, 58, 138, 0.4),
                        0 0 40px rgba(59, 130, 246, 0.3),
                        0 0 60px rgba(96, 165, 250, 0.2),
                        0 4px 15px rgba(0, 0, 0, 0.2);
        }
    }
    
    /* Animated gradient for buttons */
    @keyframes gradientShift {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }
    
    /* Typewriter animation for welcome message */
    @keyframes typewriter {
        from { width: 0; }
        to { width: 100%; }
    }
    
    @keyframes blink {
        50% { border-color: transparent; }
    }
    
    .typewriter-text {
        overflow: hidden;
        border-right: 3px solid #60a5fa;
        white-space: nowrap;
        margin: 0 auto;
        animation: 
            typewriter 4s steps(60, end) 0.5s 1 normal both,
            blink 0.75s step-end infinite;
        display: inline-block;
        max-width: 100%;
        color: #ffffff !important;
    }
    
    /* After animation completes, show full text */
    .typewriter-text.completed {
        white-space: normal;
        border-right: none;
        animation: none;
        color: #ffffff !important;
    }
    
    /* Typewriter text should be white */
    .typewriter-text,
    .typewriter-text * {
        color: #ffffff !important;
        -webkit-text-fill-color: #ffffff !important;
    }
    
    /* Make chatbot container wider and more spacious */
    .intellecta-chatbot {
        max-width: 100% !important;
        width: 100% !important;
        padding: 24px !important;
    }
    
    /* Increase font size for better readability */
    .intellecta-chatbot .message {
        font-size: 1.1em !important;
        line-height: 1.8 !important;
        padding: 16px 20px !important;
    }
    
    /* GLOBAL OVERRIDE: All text in chatbot should be dark blue */
    .chatbot, .chatbot * {
        color: #0c1e47 !important;
        -webkit-text-fill-color: #0c1e47 !important;
    }
    
    /* GLOBAL OVERRIDE: All markdown/prose text should be dark blue */
    .prose, .prose *,
    .markdown, .markdown *,
    [class*="prose"], [class*="prose"] *,
    [class*="markdown"], [class*="markdown"] * {
        color: #0c1e47 !important;
        -webkit-text-fill-color: #0c1e47 !important;
        font-weight: 600 !important;
    }
    
    /* ULTRA CRITICAL: Force dark blue text everywhere - NUCLEAR OPTION */
    *:is(textarea, input[type="text"], input[type="password"], input) {
        color: #0c1e47 !important;
        -webkit-text-fill-color: #0c1e47 !important;
        -moz-text-fill-color: #0c1e47 !important;
        background-color: rgba(255, 255, 255, 0.98) !important;
        font-weight: 700 !important;
        caret-color: #0c1e47 !important;
    }
    
    /* Target all possible Gradio input classes */
    textarea[class],
    input[type="text"][class],
    input[type="password"][class],
    label textarea,
    label input,
    .gr-box textarea,
    .gr-box input,
    .gr-input textarea,
    .gr-input input,
    .gr-text-input,
    .gr-text-input *,
    [class*="input"] textarea,
    [class*="input"] input,
    [class*="textbox"] textarea,
    [class*="textbox"] input {
        color: #0c1e47 !important;
        -webkit-text-fill-color: #0c1e47 !important;
        -moz-text-fill-color: #0c1e47 !important;
        background-color: rgba(255, 255, 255, 0.98) !important;
        font-weight: 700 !important;
        caret-color: #0c1e47 !important;
    }
    
    /* Override any inline styles */
    textarea[style],
    input[type="text"][style],
    input[type="password"][style] {
        color: #0c1e47 !important;
        -webkit-text-fill-color: #0c1e47 !important;
        background-color: rgba(255, 255, 255, 0.98) !important;
    }
    
    /* Main dark gradient background */
    .gradio-container {
        background: linear-gradient(135deg,
            rgba(16, 213, 194, 0.05) 0%,
            rgba(138, 43, 226, 0.07) 25%,
            rgba(0, 240, 255, 0.05) 50%,
            rgba(255, 60, 110, 0.06) 75%,
            rgba(16, 213, 194, 0.05) 100%
        ) !important;
        background-color: #0a0e27 !important;
    }
    
    /* Chat area with colorful glass morphism effect */
     {
        background: linear-gradient(135deg,
            rgba(16, 213, 194, 0.08) 0%,
            rgba(138, 43, 226, 0.10) 25%,
            rgba(0, 240, 255, 0.08) 50%,
            rgba(255, 60, 110, 0.09) 75%,
            rgba(16, 213, 194, 0.08) 100%
        ) !important;
        backdrop-filter: blur(15px) !important;
        border-radius: 20px !important;
        border: 2px solid rgba(16, 213, 194, 0.3) !important;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3) !important;
    }
    
    /* ============================================
       CHATBOT REDESIGN - Clean & Professional
       ============================================ */
    
    /* Chatbot container - Dark flat background like the reference image */
    .intellecta-chatbot,
    .chatbot {
        background: #1e293b !important;
        border: 2px solid #334155 !important;
        border-radius: 12px !important;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3) !important;
        padding: 20px !important;
        width: 100% !important;
        max-width: 100% !important;
    }
    
    /* Message wrap - Individual message container */
    .intellecta-chatbot .message-wrap,
    .chatbot .message-wrap,
    .message-wrap {
        background: transparent !important;
        border: none !important;
        padding: 0 !important;
        margin: 0 !important;
    }
    
    /* Bot messages - Flat dark card like the reference */
    .bot-message,
    .message.bot,
    [data-testid="bot"] {
        background: #334155 !important;
        border: 1px solid #475569 !important;
        border-radius: 12px !important;
        padding: 16px 20px !important;
        margin: 12px 0 !important;
        box-shadow: none !important;
    }
    
    /* Bot message text - Light gray/white */
    .bot-message *,
    .message.bot *,
    [data-testid="bot"] * {
        color: #e2e8f0 !important;
        -webkit-text-fill-color: #e2e8f0 !important;
        font-weight: 400 !important;
        line-height: 1.6 !important;
        font-size: 1em !important;
    }
    
    /* User messages - Slightly lighter flat card */
    .user-message,
    .message.user,
    [data-testid="user"] {
        background: #475569 !important;
        border: 1px solid #64748b !important;
        border-radius: 12px !important;
        padding: 16px 20px !important;
        margin: 12px 0 !important;
        box-shadow: none !important;
    }
    
    /* User message text - White */
    .user-message *,
    .message.user *,
    [data-testid="user"] * {
        color: #ffffff !important;
        -webkit-text-fill-color: #ffffff !important;
        font-weight: 400 !important;
        line-height: 1.6 !important;
        font-size: 1em !important;
    }
    
    /* ============================================
       INPUT BOX REDESIGN - Flat & Clean
       ============================================ */
    
    /* Input box - Dark flat design matching reference */
    .input-box, textarea, input[type="text"], input[type="password"] {
        background: #334155 !important;
        border: 1px solid #475569 !important;
        border-radius: 8px !important;
        color: #e2e8f0 !important;
        font-weight: 400 !important;
        font-size: 15px !important;
        box-shadow: none !important;
        -webkit-text-fill-color: #e2e8f0 !important;
        padding: 12px 16px !important;
        line-height: 1.5 !important;
        transition: border-color 0.2s ease !important;
    }
    
    /* Input focus state - Subtle blue highlight */
    .input-box:focus, textarea:focus, input:focus {
        border-color: #60a5fa !important;
        box-shadow: 0 0 0 3px rgba(96, 165, 250, 0.1) !important;
        outline: none !important;
    }
    
    /* Placeholder styling - Darker gray */
    input::placeholder, textarea::placeholder {
        color: #94a3b8 !important;
        -webkit-text-fill-color: #94a3b8 !important;
        font-weight: 400 !important;
        font-style: normal !important;
    }
    
    /* Force text color in all input areas - Light gray */
    textarea, input, 
    textarea[class*="textbox"],
    input[type="text"],
    input[type="password"],
    .gr-textbox,
    .gr-textbox textarea,
    .gr-textbox input,
    [data-testid="textbox"] textarea,
    [data-testid="textbox"] input,
    .input-class,
    .input-class textarea,
    .input-class input {
        color: #e2e8f0 !important;
        -webkit-text-fill-color: #e2e8f0 !important;
        font-weight: 400 !important;
        background: #334155 !important;
    }
    
    /* Extra specificity for textarea elements */
    textarea[class*="scroll-hide"],
    textarea.scroll-hide {
        color: #e2e8f0 !important;
        -webkit-text-fill-color: #e2e8f0 !important;
        background: #334155 !important;
    }
    
    /* Primary buttons - Animated gradient */
    .primary, button.primary {
        background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 50%, #60a5fa 100%) !important;
        background-size: 200% 200% !important;
        animation: gradientShift 3s ease infinite !important;
        border: 2px solid #1e40af !important;
        border-radius: 12px !important;
        color: #ffffff !important;
        -webkit-text-fill-color: #ffffff !important;
        font-weight: 600 !important;
        text-transform: uppercase !important;
        letter-spacing: 0.5px !important;
        padding: 12px 28px !important;
        box-shadow: 0 4px 12px rgba(30, 58, 138, 0.3) !important;
        transition: all 0.3s ease !important;
    }
    
    .primary:hover, button.primary:hover {
        border-color: #3b82f6 !important;
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 16px rgba(30, 58, 138, 0.4) !important;
        color: #ffffff !important;
        -webkit-text-fill-color: #ffffff !important;
    }
    
    /* Secondary buttons - Light blue with clean design */
    .secondary, button.secondary {
        background: #f0f9ff !important;
        border: 2px solid #bfdbfe !important;
        border-radius: 12px !important;
        color: #1e3a8a !important;
        -webkit-text-fill-color: #1e3a8a !important;
        font-weight: 600 !important;
        padding: 12px 28px !important;
        box-shadow: 0 2px 8px rgba(30, 58, 138, 0.1) !important;
        transition: all 0.3s ease !important;
    }
    
    .secondary:hover, button.secondary:hover {
        background: #e0f2fe !important;
        border-color: #93c5fd !important;
        transform: translateY(-2px) !important;
        box-shadow: 0 4px 12px rgba(30, 58, 138, 0.2) !important;
        color: #1e3a8a !important;
        -webkit-text-fill-color: #1e3a8a !important;
    }
    
    /* Quick action buttons - Animated gradient design */
    button[size="sm"] {
        background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 50%, #60a5fa 100%) !important;
        background-size: 200% 200% !important;
        animation: gradientShift 3s ease infinite !important;
        border: 2px solid #2563eb !important;
        border-radius: 10px !important;
        color: #ffffff !important;
        -webkit-text-fill-color: #ffffff !important;
        font-weight: 600 !important;
        padding: 8px 16px !important;
        box-shadow: 0 2px 8px rgba(59, 130, 246, 0.3) !important;
        transition: transform 0.2s ease, box-shadow 0.2s ease !important;
    }
    
    button[size="sm"]:hover {
        border-color: #1d4ed8 !important;
        transform: scale(1.05) translateY(-2px) !important;
        box-shadow: 0 4px 12px rgba(59, 130, 246, 0.5) !important;
        color: #ffffff !important;
        -webkit-text-fill-color: #ffffff !important;
    }
    
    /* General button styling */
    button, .button, input[type="button"], input[type="submit"] {
        background: #3b82f6 !important;
        border: 2px solid #2563eb !important;
        border-radius: 10px !important;
        color: #ffffff !important;
        -webkit-text-fill-color: #ffffff !important;
        font-weight: 600 !important;
        padding: 10px 20px !important;
        box-shadow: 0 2px 8px rgba(59, 130, 246, 0.2) !important;
        transition: all 0.3s ease !important;
        cursor: pointer !important;
    }
    
    button:hover, .button:hover, input[type="button"]:hover, input[type="submit"]:hover {
        background: #2563eb !important;
        border-color: #1d4ed8 !important;
        transform: translateY(-1px) !important;
        box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3) !important;
        color: #ffffff !important;
        -webkit-text-fill-color: #ffffff !important;
    }
    
    /* ULTRA PRIORITY: Chat messages - DARK BLUE for maximum visibility */
    .markdown-text, .prose,
    .markdown-text *, .prose * {
        color: #0c1e47 !important;
        -webkit-text-fill-color: #0c1e47 !important;
        font-weight: 600 !important;
    }
    
    /* Bot message content - DARK BLUE with high specificity */
    .message.bot .content, .message.bot p, .message.bot span, .message.bot div,
    .bot .content, .bot p, .bot span, .bot div,
    .message.bot .content *, .bot .content *,
    .message.bot, .message.bot * {
        color: #0c1e47 !important;
        -webkit-text-fill-color: #0c1e47 !important;
        font-weight: 600 !important;
    }
    
    /* User message content - DARK BLUE for visibility */
    .message.user .content, .message.user p, .message.user span, .message.user div,
    .user .content, .user p, .user span, .user div,
    .message.user .content *, .user .content *,
    .message.user, .message.user * {
        color: #0c1e47 !important;
        -webkit-text-fill-color: #0c1e47 !important;
        font-weight: 600 !important;
    }
    
    /* All text in chatbot messages - DARK BLUE and readable */
    .message p, .message span, .message div, .message strong, .message em,
    .chatbot p, .chatbot span, .chatbot div, .chatbot strong, .chatbot em,
    .chatbot .message *, .message *,
    .message, .message * {
        color: #0c1e47 !important;
        font-weight: 600 !important;
        -webkit-text-fill-color: #0c1e47 !important;
    }
    
    /* Chatbot container text - all DARK BLUE */
    .intellecta-chatbot, .intellecta-chatbot *,
    .intellecta-chatbot p, .intellecta-chatbot div, .intellecta-chatbot span {
        color: #0c1e47 !important;
        -webkit-text-fill-color: #0c1e47 !important;
        font-weight: 600 !important;
    }
    
    /* Extra specificity for message text visibility - DARK BLUE */
    .chatbot .message, 
    .chatbot .message *,
    .intellecta-chatbot .message,
    .intellecta-chatbot .message *,
    [class*="message"] *,
    .bot-message *,
    .user-message *,
    [class*="message"],
    [class*="bot"],
    [class*="user"] {
        color: #0c1e47 !important;
        -webkit-text-fill-color: #0c1e47 !important;
        font-weight: 600 !important;
    }
    
    /* Ensure all paragraph and div text is visible - DARK BLUE */
    .chatbot p, .chatbot div, .chatbot span,
    .intellecta-chatbot p, .intellecta-chatbot div, .intellecta-chatbot span,
    .message p, .message div, .message span {
        color: #0c1e47 !important;
        -webkit-text-fill-color: #0c1e47 !important;
        font-weight: 600 !important;
    }
    
    /* Headers outside chatbot can stay white */
    h1:not(.chatbot *):not(.message *), 
    h2:not(.chatbot *):not(.message *), 
    h3:not(.chatbot *):not(.message *), 
    h4:not(.chatbot *):not(.message *), 
    h5:not(.chatbot *):not(.message *), 
    h6:not(.chatbot *):not(.message *) {
        color: #ffffff !important;
        -webkit-text-fill-color: #ffffff !important;
    }
    
    /* Tab styling - modern colorful tabs */
    .tab-nav {
        background: linear-gradient(135deg,
            rgba(16, 213, 194, 0.08) 0%,
            rgba(138, 43, 226, 0.10) 25%,
            rgba(0, 240, 255, 0.08) 50%,
            rgba(255, 60, 110, 0.09) 75%,
            rgba(16, 213, 194, 0.08) 100%
        ) !important;
        border-radius: 15px !important;
        padding: 8px !important;
        backdrop-filter: blur(10px) !important;
    }
    
    .tab-nav button {
        background: linear-gradient(135deg,
            rgba(16, 213, 194, 0.10) 0%,
            rgba(138, 43, 226, 0.12) 25%,
            rgba(0, 240, 255, 0.10) 50%,
            rgba(255, 60, 110, 0.11) 75%,
            rgba(16, 213, 194, 0.10) 100%
        ) !important;
        border: 2px solid rgba(16, 213, 194, 0.3) !important;
        border-radius: 10px !important;
        color: #ffffff !important;
        -webkit-text-fill-color: #ffffff !important;
        margin: 0 4px !important;
        font-weight: 600 !important;
        transition: all 0.3s ease !important;
    }
    
    .tab-nav button:hover {
        background: linear-gradient(135deg,
            rgba(16, 213, 194, 0.15) 0%,
            rgba(138, 43, 226, 0.17) 25%,
            rgba(0, 240, 255, 0.15) 50%,
            rgba(255, 60, 110, 0.16) 75%,
            rgba(16, 213, 194, 0.15) 100%
        ) !important;
        border-color: rgba(0, 240, 255, 0.5) !important;
        color: #ffffff !important;
        -webkit-text-fill-color: #ffffff !important;
    }
    
    .tab-nav button.selected {
        background: linear-gradient(135deg,
            rgba(16, 213, 194, 0.20) 0%,
            rgba(138, 43, 226, 0.22) 25%,
            rgba(0, 240, 255, 0.20) 50%,
            rgba(255, 60, 110, 0.21) 75%,
            rgba(16, 213, 194, 0.20) 100%
        ) !important;
        color: #ffffff !important;
        -webkit-text-fill-color: #ffffff !important;
        border: 2px solid rgba(16, 213, 194, 0.6) !important;
        box-shadow: 0 4px 15px rgba(16, 213, 194, 0.4) !important;
        font-weight: 700 !important;
    }
    
    /* Chatbot messages */
    .bot-message {
        background: rgba(240, 248, 255, 0.98) !important;
        border-left: 4px solid #1e3a8a !important;
        border-radius: 12px !important;
        box-shadow: 0 2px 10px rgba(30, 58, 138, 0.2) !important;
        padding: 12px !important;
        margin: 8px 0 !important;
    }
    
    .user-message {
        background: rgba(219, 234, 254, 0.98) !important;
        border-left: 4px solid #3b82f6 !important;
        border-radius: 12px !important;
        box-shadow: 0 2px 10px rgba(59, 130, 246, 0.2) !important;
        padding: 12px !important;
        margin: 8px 0 !important;
    }
    
    /* Labels with better visibility - bright white */
    label:not(.chatbot *):not(.message *) {
        color: #ffffff !important;
        -webkit-text-fill-color: #ffffff !important;
        font-weight: 700 !important;
        text-transform: uppercase !important;
        font-size: 0.9em !important;
        letter-spacing: 0.5px !important;
    }
    
    /* Labels inside chatbot should be blue */
    .chatbot label, .message label {
        color: #1e3a8a !important;
        -webkit-text-fill-color: #1e3a8a !important;
    }
    
    /* Default text color - white for general UI */
    body, .gradio-container {
        color: #ffffff !important;
    }
    
    /* Tabs and navigation text - white */
    .tab-nav, .tab-nav * {
        color: #ffffff !important;
        -webkit-text-fill-color: #ffffff !important;
    }
    
    /* Markdown content outside chatbot - white */
    .markdown:not(.chatbot *):not(.message *), 
    .markdown:not(.chatbot *):not(.message *) * {
        color: #ffffff !important;
        -webkit-text-fill-color: #ffffff !important;
    }
    
    /* Block content outside chatbot - white */
    .block:not(.chatbot *):not(.message *), 
    .block:not(.chatbot *):not(.message *) * {
        color: #ffffff !important;
        -webkit-text-fill-color: #ffffff !important;
    }
    
    /* Chatbot label styling */
    .chatbot {
        background: rgba(30, 58, 138, 0.12) !important;
        border-radius: 20px !important;
        border: 2px solid rgba(30, 58, 138, 0.4) !important;
    }
    
    /* ============================================
       TOP HEADER LOGO - Above Everything
       ============================================ */
    
    /* Pulsing glow animation - always active */
    @keyframes logo-pulse {
        0%, 100% {
            box-shadow: 0 0 20px rgba(96, 165, 250, 0.4),
                        0 0 40px rgba(59, 130, 246, 0.2),
                        0 4px 15px rgba(0, 0, 0, 0.2);
        }
        50% {
            box-shadow: 0 0 40px rgba(96, 165, 250, 0.8),
                        0 0 80px rgba(59, 130, 246, 0.5),
                        0 0 100px rgba(96, 165, 250, 0.3),
                        0 4px 20px rgba(0, 0, 0, 0.3);
        }
    }
    
    /* AGGRESSIVELY remove all backgrounds from logo area - but NOT from img */
    .top-header-logo,
    #top-logo,
    .top-header-logo > div,
    #top-logo > div,
    .top-header-logo .block,
    #top-logo .block,
    .top-header-logo button,
    #top-logo button,
    .top-header-logo button:hover,
    #top-logo button:hover {
        background: transparent !important;
        background-color: transparent !important;
        background-image: none !important;
        border: none !important;
        box-shadow: none !important;
        padding: 0 !important;
        margin: 0 !important;
    }
    
    /* Center the logo wrapper - clickable */
    .top-header-logo,
    #top-logo {
        display: flex !important;
        justify-content: center !important;
        align-items: center !important;
        margin: 20px auto !important;
        width: 150px !important;
        height: 150px !important;
        position: relative !important;
        overflow: visible !important;
        cursor: pointer !important;
    }
    
    /* The actual logo image - with continuous pulsing glow */
    .top-header-logo img,
    #top-logo img {
        border-radius: 50% !important;
        border: 3px solid rgba(96, 165, 250, 0.6) !important;
        object-fit: cover !important;
        background: transparent !important;
        padding: 8px !important;
        display: block !important;
        margin: 0 auto !important;
        cursor: pointer !important;
        animation: logoPulse 3s ease-in-out infinite !important;
    }
    
    /* ============================================
       HEADER LOGO - Clean with Hover Glow Effect
       ============================================ */
    
    /* Header logo at the top - No border, just the image */
    .intellecta-header-logo,
    #header-logo {
        margin: 30px auto 20px auto !important;
        display: flex !important;
        justify-content: center !important;
        align-items: center !important;
        transition: all 0.3s ease !important;
    }
    
    .intellecta-header-logo img,
    #header-logo img {
        border-radius: 50% !important;
        object-fit: cover !important;
        transition: all 0.4s ease !important;
        filter: drop-shadow(0 0 0 transparent) !important;
    }
    
  
    
    /* Old logo styles - Keep for chat avatar */
    .intellecta-logo {
        margin: 20px auto !important;
        display: block !important;
        text-align: center !important;
        border-radius: 50% !important;
        box-shadow: 0 8px 32px rgba(94, 129, 172, 0.5) !important;
        border: 3px solid rgba(94, 129, 172, 0.6) !important;
        background: linear-gradient(135deg, rgba(15, 52, 96, 0.3) 0%, rgba(22, 33, 62, 0.3) 100%) !important;
        padding: 10px !important;
        transition: all 0.3s ease !important;
    }
    
   
    
    /* Bot avatar in chat */
    .avatar-container img {
        border-radius: 50% !important;
        border: 2px solid rgba(94, 129, 172, 0.5) !important;
    }
    
    /* Security Watermark - Bottom Right Corner */
    .gradio-container::after {
        content: "© Intellecta Solutions | Patent Pending" !important;
        position: fixed !important;
        bottom: 10px !important;
        right: 10px !important;
        background: rgba(0, 0, 0, 0.7) !important;
        color: rgba(255, 255, 255, 0.6) !important;
        padding: 5px 15px !important;
        border-radius: 20px !important;
        font-size: 11px !important;
        font-weight: 600 !important;
        z-index: 999999 !important;
        pointer-events: none !important;
        border: 1px solid rgba(94, 129, 172, 0.4) !important;
        backdrop-filter: blur(10px) !important;
    }
    
    /* Disable right-click for security */
    * {
        -webkit-user-select: none !important;
        -moz-user-select: none !important;
        -ms-user-select: none !important;
        user-select: none !important;
    }
    
    /* Allow text selection only in input/textarea */
    input, textarea, .message-wrap {
        -webkit-user-select: text !important;
        -moz-user-select: text !important;
        -ms-user-select: text !important;
        user-select: text !important;
    }
    
    /* HIDE GRADIO DEFAULT FOOTER - API & Settings Links */
    footer {
        display: none !important;
        visibility: hidden !important;
    }
    
    /* Header logo styling - Disable download */
    .intellecta-header-logo img {
        border-radius: 50% !important;
        border: 4px solid white !important;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3) !important;
        object-fit: cover !important;
        pointer-events: none !important;
    }
    
    /* Chat logo with pulsing glow animation - Enhanced visibility */
    .intellecta-logo, #chat-logo {
        display: block !important;
        visibility: visible !important;
        position: relative !important;
        margin: 20px auto !important;
        text-align: center !important;
        z-index: 100 !important;
    }
    
    .intellecta-logo img, #chat-logo img {
        display: inline-block !important;
        visibility: visible !important;
        border-radius: 50% !important;
        border: 5px solid rgba(16, 213, 194, 0.9) !important;
        box-shadow: 0 0 30px rgba(16, 213, 194, 0.8),
                    0 0 60px rgba(138, 43, 226, 0.6),
                    inset 0 0 30px rgba(0, 240, 255, 0.3),
                    0 0 100px rgba(255, 60, 110, 0.3) !important;
        animation: pulse-glow 2s ease-in-out infinite !important;
        pointer-events: none !important;
        opacity: 1 !important;
        background: rgba(16, 213, 194, 0.05) !important;
    }
    
    @keyframes pulse-glow {
        0% {
            box-shadow: 0 0 30px rgba(16, 213, 194, 0.8), 
                        0 0 60px rgba(138, 43, 226, 0.6),
                        inset 0 0 30px rgba(16, 213, 194, 0.3),
                        0 0 100px rgba(255, 60, 110, 0.3) !important;
            transform: scale(1) !important;
            border-color: rgba(16, 213, 194, 0.9) !important;
        }
        50% {
            box-shadow: 0 0 50px rgba(0, 240, 255, 1), 
                        0 0 100px rgba(255, 60, 110, 0.8),
                        inset 0 0 40px rgba(138, 43, 226, 0.5),
                        0 0 150px rgba(16, 213, 194, 0.5) !important;
            transform: scale(1.08) !important;
            border-color: rgba(138, 43, 226, 1) !important;
        }
        100% {
            box-shadow: 0 0 30px rgba(16, 213, 194, 0.8), 
                        0 0 60px rgba(138, 43, 226, 0.6),
                        inset 0 0 30px rgba(16, 213, 194, 0.3),
                        0 0 100px rgba(255, 60, 110, 0.3) !important;
            transform: scale(1) !important;
            border-color: rgba(16, 213, 194, 0.9) !important;
        }
    }
    
    /* Intensify animation when bot is responding */
    .intellecta-logo.responding img {
        animation: pulse-glow-fast 1s ease-in-out infinite !important;
    }
    
    @keyframes pulse-glow-fast {
        0% {
            box-shadow: 0 0 30px rgba(16, 213, 194, 0.8), 
                        0 0 60px rgba(138, 43, 226, 0.6),
                        inset 0 0 25px rgba(0, 240, 255, 0.4) !important;
            transform: scale(1) rotate(0deg) !important;
        }
        25% {
            transform: scale(1.08) rotate(2deg) !important;
        }
        50% {
            box-shadow: 0 0 50px rgba(0, 240, 255, 1), 
                        0 0 100px rgba(255, 60, 110, 0.8),
                        inset 0 0 40px rgba(138, 43, 226, 0.6) !important;
            transform: scale(1.1) rotate(0deg) !important;
            border-color: rgba(0, 240, 255, 0.95) !important;
        }
        75% {
            transform: scale(1.08) rotate(-2deg) !important;
        }
        100% {
            box-shadow: 0 0 30px rgba(16, 213, 194, 0.8), 
                        0 0 60px rgba(138, 43, 226, 0.6),
                        inset 0 0 25px rgba(0, 240, 255, 0.4) !important;
            transform: scale(1) rotate(0deg) !important;
        }
    }
    
    .footer {
        display: none !important;
        visibility: hidden !important;
    }
    
    .gradio-footer {
        display: none !important;
    }
    
    /* Hide "Built with Gradio" and API links */
    .svelte-1eq475l {
        display: none !important;
    }
    
    /* Hide any footer-like elements */
    [class*="footer"] {
        display: none !important;
    }
    
    /* Ensure our custom footer shows */
    .markdown-text footer {
        display: block !important;
        visibility: visible !important;
    }
    """
    
    # Copyright and security configuration
    with gr.Blocks(
        theme=gr.themes.Default(
            primary_hue="blue",
            secondary_hue="slate",
            font=("Source Sans Pro", "ui-sans-serif", "system-ui", "sans-serif"),
        ), 
        css=custom_css, 
        title=f"IntellaPersona - {me.name}",
        analytics_enabled=False,  # Disable analytics
        # Note: delete_cache parameter removed for Gradio 4.16.0 compatibility
        head="""
        <script>
        // Security: Disable right-click context menu
        document.addEventListener('contextmenu', event => event.preventDefault());
        
        // Security: Disable common keyboard shortcuts
        document.addEventListener('keydown', function(e) {
            // F12, Ctrl+Shift+I, Ctrl+Shift+J, Ctrl+U
            if(e.keyCode == 123 || 
               (e.ctrlKey && e.shiftKey && e.keyCode == 73) ||
               (e.ctrlKey && e.shiftKey && e.keyCode == 74) ||
               (e.ctrlKey && e.keyCode == 85)) {
                e.preventDefault();
                return false;
            }
        });
        
        // Security: Disable developer tools detection
        (function() {
            const devtools = /./;
            devtools.toString = function() {
                console.log('⚠️ Developer tools detected - Intellecta Solutions © 2024-2025');
            };
        })();
        
        // Copyright notice in console
        console.log('%c⚠️ STOP!', 'color: red; font-size: 50px; font-weight: bold;');
        console.log('%c© 2024-2025 Intellecta Solutions - Patent Pending Technology', 'color: #667eea; font-size: 16px; font-weight: bold;');
        console.log('%cThis is a proprietary AI system. Unauthorized access, copying, or reverse engineering is strictly prohibited.', 'color: #764ba2; font-size: 14px;');
        console.log('%cFor licensing: contact@intellectasolutions.com', 'color: #888; font-size: 12px;');
        
        // Logo click handler - IMMEDIATE AND GLOBAL
        const linkedinUrl = 'https://www.linkedin.com/company/107938459/admin/dashboard/';
        
        // Global click handler on document for logo
        document.addEventListener('click', function(e) {
            const target = e.target;
            
            // Check if clicked element or any parent is the logo
            let element = target;
            for (let i = 0; i < 10; i++) {
                if (!element) break;
                
                const id = element.id || '';
                const classes = element.className || '';
                
                // Check if this is a logo element
                if (id === 'top-logo' || 
                    classes.includes('top-header-logo') ||
                    id.includes('logo') && element.tagName === 'IMG') {
                    
                    e.preventDefault();
                    e.stopPropagation();
                    console.log('🎯 Logo clicked! Redirecting to LinkedIn...');
                    window.open(linkedinUrl, '_blank');
                    return;
                }
                
                element = element.parentElement;
            }
        }, true);
        
        console.log('✅ Global logo click handler installed');
        
        // MAIN INITIALIZATION FUNCTION
        function initializeApp() {
            console.log('🚀 INITIALIZING APPLICATION...');
            console.log('📍 Document ready state:', document.readyState);
            
            // Function to setup logo click handlers
            function setupLogoHandlers() {
                // Try multiple selectors to find the logo
                const selectors = [
                    '#top-logo',
                    '.top-header-logo',
                    '#top-logo img',
                    '.top-header-logo img',
                    '[id*="top-logo"]',
                    '[class*="top-header-logo"]'
                ];
                
                let foundElements = 0;
                
                selectors.forEach(selector => {
                    try {
                        const elements = document.querySelectorAll(selector);
                        elements.forEach(element => {
                            if (element && !element.dataset.clickHandlerAdded) {
                                element.style.cursor = 'pointer';
                                element.dataset.clickHandlerAdded = 'true';
                                
                                element.addEventListener('click', function(e) {
                                    e.preventDefault();
                                    e.stopPropagation();
                                    console.log('🎯 Logo element clicked via selector:', selector);
                                    window.open(linkedinUrl, '_blank');
                                }, true);
                                
                                foundElements++;
                                console.log('✅ Click handler added to:', selector, element);
                            }
                        });
                    } catch (err) {
                        console.error('Error with selector:', selector, err);
                    }
                });
                
                if (foundElements > 0) {
                    console.log(`✅ Total ${foundElements} logo elements found and configured`);
                } else {
                    console.log('⚠️ No logo elements found yet...');
                }
            }
            
            // Try to setup handlers immediately
            setupLogoHandlers();
            
            // Also setup handlers after delays
            setTimeout(setupLogoHandlers, 100);
            setTimeout(setupLogoHandlers, 500);
            setTimeout(setupLogoHandlers, 1000);
            setTimeout(setupLogoHandlers, 2000);
            setTimeout(setupLogoHandlers, 3000);
            setTimeout(setupLogoHandlers, 5000);
            
            // Watch for logo element to be added to DOM
            const observer = new MutationObserver(function(mutations) {
                setupLogoHandlers();
            });
            
            observer.observe(document.body, {
                childList: true,
                subtree: true
            });
            
            // Typewriter effect completion
            setTimeout(() => {
                const typewriterElements = document.querySelectorAll('.typewriter-text');
                typewriterElements.forEach(el => {
                    el.classList.add('completed');
                });
            }, 5000); // Complete after 5 seconds (animation duration + buffer)
            
            // ULTRA FORCE INPUT TEXT COLOR - Aggressive JavaScript override
            function forceInputColors() {
                const selectors = [
                    'textarea',
                    'input[type="text"]',
                    'input[type="password"]',
                    'input',
                    '.gr-box textarea',
                    '.gr-box input',
                    '[class*="textbox"] textarea',
                    '[class*="textbox"] input',
                    '[class*="input"] textarea',
                    '[class*="input"] input'
                ];
                
                const allInputs = document.querySelectorAll(selectors.join(', '));
                allInputs.forEach(input => {
                    // Force all color properties for dark theme
                    input.style.setProperty('color', '#e2e8f0', 'important');
                    input.style.setProperty('-webkit-text-fill-color', '#e2e8f0', 'important');
                    input.style.setProperty('-moz-text-fill-color', '#e2e8f0', 'important');
                    input.style.setProperty('background-color', '#334155', 'important');
                    input.style.setProperty('font-weight', '400', 'important');
                    input.style.setProperty('caret-color', '#e2e8f0', 'important');
                    
                    // Also set as regular properties (fallback)
                    input.style.color = '#e2e8f0';
                    input.style.webkitTextFillColor = '#e2e8f0';
                    input.style.backgroundColor = '#334155';
                    input.style.fontWeight = '400';
                    
                    // Add event listeners to force on focus/input
                    input.addEventListener('focus', function() {
                        this.style.color = '#e2e8f0';
                        this.style.webkitTextFillColor = '#e2e8f0';
                    });
                    
                    input.addEventListener('input', function() {
                        this.style.color = '#e2e8f0';
                        this.style.webkitTextFillColor = '#e2e8f0';
                    });
                });
            }
            
            // Run on load
            forceInputColors();
            
            // Run more frequently - every 100ms for first 5 seconds
            let counter = 0;
            const rapidInterval = setInterval(() => {
                forceInputColors();
                counter++;
                if (counter > 50) { // 50 * 100ms = 5 seconds
                    clearInterval(rapidInterval);
                }
            }, 100);
            
            // Then continue with slower interval
            setTimeout(() => {
                setInterval(forceInputColors, 500);
            }, 5000);
            
            // FORCE CHATBOT MESSAGE COLORS - Light gray/white for dark theme
            function forceChatbotColors() {
                const selectors = [
                    '.chatbot p', '.chatbot div', '.chatbot span',
                    '.intellecta-chatbot p', '.intellecta-chatbot div', '.intellecta-chatbot span',
                    '.message p', '.message div', '.message span',
                    '.message', '.message *',
                    '.bot-message', '.bot-message *',
                    '.user-message', '.user-message *',
                    '[class*="message"]', '[class*="message"] *',
                    '.markdown-text', '.markdown-text *',
                    '.prose', '.prose *'
                ];
                
                const allElements = document.querySelectorAll(selectors.join(', '));
                allElements.forEach(el => {
                    el.style.setProperty('color', '#e2e8f0', 'important');
                    el.style.setProperty('-webkit-text-fill-color', '#e2e8f0', 'important');
                    el.style.setProperty('font-weight', '400', 'important');
                    
                    // Fallback
                    el.style.color = '#e2e8f0';
                    el.style.webkitTextFillColor = '#e2e8f0';
                    el.style.fontWeight = '400';
                });
            }
            
            // Run chatbot colors on load
            forceChatbotColors();
            
            // Run more frequently for chatbot messages
            setInterval(forceChatbotColors, 200);
            
            // Observer for dynamic content
            const inputObserver = new MutationObserver(forceInputColors);
            inputObserver.observe(document.body, { 
                childList: true, 
                subtree: true 
            });
            
            // Observer for chatbot messages
            const chatObserver = new MutationObserver(forceChatbotColors);
            chatObserver.observe(document.body, { 
                childList: true, 
                subtree: true 
            });
            
            // Disable download on all logo images
            const logos = document.querySelectorAll('.intellecta-logo img, .intellecta-header-logo img');
            logos.forEach(logo => {
                logo.addEventListener('contextmenu', e => e.preventDefault());
                logo.addEventListener('dragstart', e => e.preventDefault());
                logo.style.pointerEvents = 'none';
            });
            
            // Animate logo when chatbot is responding
            const logoObserver = new MutationObserver(function(mutations) {
                const chatLogo = document.querySelector('.intellecta-logo');
                const chatbot = document.querySelector('.chatbot');
                
                if (chatLogo && chatbot) {
                    // Check if there's new content being added
                    mutations.forEach(mutation => {
                        if (mutation.addedNodes.length > 0) {
                            chatLogo.classList.add('responding');
                            setTimeout(() => {
                                chatLogo.classList.remove('responding');
                            }, 3000); // Animation lasts 3 seconds
                        }
                    });
                }
            });
            
            // Observe chatbot for changes
            const chatbot = document.querySelector('.chatbot');
            if (chatbot) {
                logoObserver.observe(chatbot, { 
                    childList: true, 
                    subtree: true 
                });
            }
            
            // ===== PROJECT CARD MODAL HANDLERS =====
            console.log('🎨 INITIALIZING PROJECT CARD HANDLERS...');
            
            // Store current project name
            let currentProjectName = '';
            let handlersSetupCount = 0;
            
            // Function to setup project card click handlers
            function setupProjectCardHandlers() {
                const projectCards = document.querySelectorAll('.project-card');
                
                if (projectCards.length > 0) {
                    console.log(`🔍 [Attempt #${++handlersSetupCount}] Found ${projectCards.length} project cards`);
                    
                    let newHandlersAdded = 0;
                    projectCards.forEach((card, index) => {
                        if (!card.dataset.handlerAdded) {
                            card.dataset.handlerAdded = 'true';
                            newHandlersAdded++;
                            
                            // Make card visually clickable
                            card.style.cursor = 'pointer';
                            
                            card.addEventListener('click', function(e) {
                                e.preventDefault();
                                e.stopPropagation();
                                console.log(`🎯 PROJECT CARD ${index} CLICKED!`);
                                
                                // Get project name from card
                                const projectNameElement = this.querySelector('.project-name');
                                currentProjectName = projectNameElement ? projectNameElement.textContent : 'this project';
                                console.log(`📌 Project name: ${currentProjectName}`);
                                
                                // Update modal with project name
                                const modalProjectName = document.getElementById('projectName');
                                if (modalProjectName) {
                                    modalProjectName.textContent = currentProjectName;
                                    console.log('✅ Modal text updated');
                                } else {
                                    console.warn('⚠️ projectName element not found');
                                }
                                
                                // Show modal
                                const modal = document.getElementById('projectModal');
                                if (modal) {
                                    modal.classList.add('show');
                                    modal.style.display = 'flex'; // Force display
                                    console.log('✅ MODAL SHOWN');
                                } else {
                                    console.error('❌ MODAL NOT FOUND!');
                                    // Try to find any modal
                                    const anyModal = document.querySelector('.project-modal');
                                    console.log('Looking for .project-modal:', anyModal);
                                }
                            }, true); // Use capture phase
                            
                            console.log(`✅ Handler added to card ${index}`);
                        }
                    });
                    
                    if (newHandlersAdded > 0) {
                        console.log(`✅ Added ${newHandlersAdded} new handlers (Total cards: ${projectCards.length})`);
                    }
                } else {
                    console.log(`⏳ [Attempt #${++handlersSetupCount}] No project cards found yet...`);
                }
            }
            
            // Window-level functions for modal
            window.getVisitorAccess = function() {
                console.log('🚀 GET VISITOR ACCESS CLICKED');
                
                // Close modal first
                window.closeProjectModal();
                
                // Wait a bit for modal to close, then proceed
                setTimeout(() => {
                    console.log('🔍 Looking for Chat tab...');
                    
                    // Find and click the Chat tab (first tab - 💬 Chat)
                    const tabs = document.querySelectorAll('button[role="tab"]');
                    console.log(`� Found ${tabs.length} tabs`);
                    
                    let chatTabFound = false;
                    tabs.forEach((tab, index) => {
                        const text = tab.textContent || '';
                        console.log(`Tab ${index}: "${text}"`);
                        
                        // Look for Chat tab (first tab)
                        if (text.includes('Chat') || text.includes('💬') || index === 0) {
                            console.log(`✅ Found Chat tab at index ${index}`);
                            tab.click();
                            chatTabFound = true;
                        }
                    });
                    
                    if (!chatTabFound && tabs.length > 0) {
                        console.log('⚠️ Chat tab not found by text, clicking first tab');
                        tabs[0].click();
                    }
                    
                    // Wait for tab switch, then find and click "Get Started" button
                    setTimeout(() => {
                        console.log('🔍 Looking for Get Started button...');
                        
                        // Find the "Get Started" button
                        const buttons = document.querySelectorAll('button');
                        let getStartedBtn = null;
                        
                        buttons.forEach(btn => {
                            const text = btn.textContent || '';
                            if (text.includes('Get Started') || text.includes('🚀')) {
                                console.log('✅ Found Get Started button:', text);
                                getStartedBtn = btn;
                            }
                        });
                        
                        if (getStartedBtn) {
                            console.log('🎯 Clicking Get Started button...');
                            getStartedBtn.click();
                            
                            // After Get Started is clicked, wait and focus on message input
                            setTimeout(() => {
                                console.log('🔍 Looking for message input...');
                                
                                // Find the message input textarea
                                const textareas = document.querySelectorAll('textarea');
                                let messageInput = null;
                                
                                // Look for textarea with "YOUR MESSAGE" placeholder or similar
                                textareas.forEach(textarea => {
                                    const placeholder = textarea.placeholder || '';
                                    const parentText = textarea.closest('.gr-box')?.textContent || '';
                                    
                                    console.log(`Textarea found - placeholder: "${placeholder}"`);
                                    
                                    // Match the message input (not username/password fields)
                                    if (placeholder.includes('message') || 
                                        placeholder.includes('type') || 
                                        placeholder.includes('chat') ||
                                        parentText.includes('YOUR MESSAGE')) {
                                        messageInput = textarea;
                                        console.log('✅ Found message input');
                                    }
                                });
                                
                                // Fallback: use the first visible textarea
                                if (!messageInput && textareas.length > 0) {
                                    console.log('⚠️ Using first textarea as fallback');
                                    messageInput = textareas[0];
                                }
                                
                                if (messageInput) {
                                    console.log('✨ Focusing message input...');
                                    messageInput.focus();
                                    messageInput.scrollIntoView({ behavior: 'smooth', block: 'center' });
                                    console.log('✅ Message input focused!');
                                } else {
                                    console.error('❌ Message input not found!');
                                }
                            }, 1000); // Wait 1s for Get Started to process
                        } else {
                            console.error('❌ Get Started button not found!');
                        }
                    }, 500); // Wait 500ms for tab switch
                }, 200); // Wait 200ms for modal close
            };
            
            window.closeProjectModal = function() {
                console.log('❌ CLOSING MODAL');
                const modal = document.getElementById('projectModal');
                if (modal) {
                    modal.classList.remove('show');
                    modal.style.display = 'none'; // Force hide
                    console.log('✅ MODAL CLOSED');
                } else {
                    console.error('❌ MODAL NOT FOUND!');
                }
            };
            
            // Close modal on background click
            document.addEventListener('click', function(e) {
                const modal = document.getElementById('projectModal');
                if (modal && e.target === modal) {
                    window.closeProjectModal();
                }
            });
            
            // ===== CHATBOT AUTO-SCROLL TO TOP =====
            // When user sends a message, scroll chatbot to show the user's question at top
            function setupChatbotScroll() {
                console.log('🔧 Setting up chatbot scroll handlers...');
                
                // Find all chatbot containers
                const chatbotSelectors = [
                    '.intellecta-chatbot',
                    '[class*="chatbot"]',
                    '.gr-chatbot',
                    '[data-testid="chatbot"]'
                ];
                
                chatbotSelectors.forEach(selector => {
                    const chatbots = document.querySelectorAll(selector);
                    
                    chatbots.forEach((chatbot, index) => {
                        if (chatbot.dataset.scrollHandlerAdded) {
                            return; // Skip if already set up
                        }
                        chatbot.dataset.scrollHandlerAdded = 'true';
                        
                        console.log(`✅ Found chatbot ${index} with selector: ${selector}`);
                        
                        // Observer for new messages
                        const chatObserver = new MutationObserver(function(mutations) {
                            let shouldScroll = false;
                            
                            mutations.forEach(mutation => {
                                if (mutation.addedNodes.length > 0) {
                                    // Check if it's a new message (not just UI updates)
                                    mutation.addedNodes.forEach(node => {
                                        if (node.nodeType === 1 && (
                                            node.classList?.contains('message') ||
                                            node.classList?.contains('user') ||
                                            node.classList?.contains('bot') ||
                                            node.querySelector('[class*="message"]')
                                        )) {
                                            shouldScroll = true;
                                        }
                                    });
                                }
                            });
                            
                            if (shouldScroll) {
                                // Find all possible scroll containers
                                const scrollTargets = [
                                    chatbot.querySelector('[class*="overflow"]'),
                                    chatbot.querySelector('[class*="scroll"]'),
                                    chatbot.querySelector('.scroll-container'),
                                    chatbot.closest('[class*="overflow"]'),
                                    chatbot
                                ];
                                
                                scrollTargets.forEach(target => {
                                    if (target && target.scrollHeight > target.clientHeight) {
                                        console.log('📜 Scrolling chatbot to top');
                                        target.scrollTop = 0;
                                        target.scrollTo({ top: 0, behavior: 'instant' });
                                    }
                                });
                            }
                        });
                        
                        chatObserver.observe(chatbot, {
                            childList: true,
                            subtree: true,
                            attributes: false
                        });
                        
                        console.log(`✅ Chatbot ${index} scroll handler installed`);
                    });
                });
            }
            
            // Setup chatbot scroll multiple times to catch dynamically loaded chatbots
            setupChatbotScroll();
            setTimeout(setupChatbotScroll, 500);
            setTimeout(setupChatbotScroll, 1000);
            setTimeout(setupChatbotScroll, 2000);
            setTimeout(setupChatbotScroll, 5000);
            
            // Also observe body for new chatbots
            const bodyObserver = new MutationObserver(function() {
                setupChatbotScroll();
            });
            bodyObserver.observe(document.body, {
                childList: true,
                subtree: true
            });
            
            // AGGRESSIVE CONTINUOUS POLLING STRATEGY
            console.log('🚀 Starting aggressive polling for project cards...');
            
            // 1. Immediate setup attempt
            setupProjectCardHandlers();
            
            // 2. Poll every 100ms for first 10 seconds
            let pollAttempts = 0;
            const maxPolls = 100; // 10 seconds at 100ms intervals
            const pollInterval = setInterval(() => {
                setupProjectCardHandlers();
                pollAttempts++;
                
                if (pollAttempts >= maxPolls) {
                    clearInterval(pollInterval);
                    console.log(`⏹️ Polling stopped after ${maxPolls} attempts`);
                }
            }, 100);
            
            // 3. Watch for DOM changes with MutationObserver
            const projectObserver = new MutationObserver(function(mutations) {
                console.log('🔄 DOM mutation detected');
                setupProjectCardHandlers();
            });
            
            projectObserver.observe(document.body, {
                childList: true,
                subtree: true
            });
            
            // 4. Additional delayed attempts at key intervals
            [500, 1000, 2000, 3000, 5000, 10000, 15000].forEach(delay => {
                setTimeout(() => {
                    console.log(`⏰ Scheduled attempt at ${delay}ms`);
                    setupProjectCardHandlers();
                }, delay);
            });
            
            console.log('✅ PROJECT CARD POLLING SYSTEM INITIALIZED');
        }
        
        // Run initialization based on document state
        if (document.readyState === 'loading') {
            console.log('⏳ Document still loading, waiting for DOMContentLoaded...');
            document.addEventListener('DOMContentLoaded', initializeApp);
        } else {
            console.log('✅ Document already loaded, initializing immediately...');
            initializeApp();
        }
        """
    ) as demo:
        # Logo at the very top - above everything
        gr.Image(
            value="IntellectaLinkedIn.png",
            label=None,
            show_label=False,
            show_download_button=False,
            container=False,
            height=150,
            width=150,
            elem_classes="top-header-logo",
            elem_id="top-logo"
        )
        
        # Modern Project Showcase with Auto-Scroll Carousel
        gr.HTML("""
        <style>
        @keyframes slideIn {
            from { opacity: 0; transform: translateY(20px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
        @keyframes float {
            0%, 100% { transform: translateY(0px); }
            50% { transform: translateY(-10px); }
        }
        
        .showcase-container {
            width: 100%;
            overflow: hidden;
            background: linear-gradient(135deg,
                rgba(30, 58, 138, 0.15) 0%,
                rgba(59, 130, 246, 0.12) 50%,
                rgba(96, 165, 250, 0.15) 100%
            );
            border-radius: 20px;
            padding: 40px 20px;
            margin-bottom: 30px;
            box-shadow: 0 10px 40px rgba(30, 58, 138, 0.3);
            border: 2px solid rgba(96, 165, 250, 0.3);
            animation: slideIn 0.8s ease-out;
        }
        
        .showcase-header {
            text-align: center;
            margin-bottom: 35px;
            animation: slideIn 1s ease-out;
        }
        
        .showcase-title {
            font-size: 36px;
            font-weight: 800;
            background: linear-gradient(135deg, #60a5fa 0%, #3b82f6 50%, #1e3a8a 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            margin: 0 0 10px 0;
            text-shadow: 0 2px 20px rgba(96, 165, 250, 0.3);
        }
        
        .showcase-subtitle {
            font-size: 18px;
            color: #e2e8f0;
            margin: 5px 0;
            font-weight: 500;
        }
        
        .showcase-legal {
            font-size: 12px;
            color: #cbd5e1;
            margin: 15px 0 5px 0;
            opacity: 0.9;
        }
        
        .carousel-wrapper {
            position: relative;
            width: 100%;
            max-width: 1200px;
            margin: 0 auto;
            overflow: hidden;
            border-radius: 15px;
        }
        
        .carousel-track {
            display: flex;
            gap: 20px;
            animation: scroll 30s linear infinite;
            will-change: transform;
        }
        
        .carousel-track:hover {
            animation-play-state: paused;
        }
        
        @keyframes scroll {
            0% { transform: translateX(0); }
            100% { transform: translateX(calc(-280px * 11 - 220px)); }
        }
        
        .project-card {
            min-width: 280px;
            height: 200px;
            background: linear-gradient(135deg, 
                rgba(30, 58, 138, 0.6) 0%,
                rgba(59, 130, 246, 0.5) 100%
            );
            border-radius: 15px;
            padding: 25px;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            transition: all 0.3s ease;
            border: 2px solid rgba(96, 165, 250, 0.4);
            box-shadow: 0 5px 20px rgba(30, 58, 138, 0.3);
            cursor: pointer;
            backdrop-filter: blur(10px);
        }
        
        .project-card:hover {
            transform: translateY(-5px) scale(1.02);
            box-shadow: 0 10px 30px rgba(96, 165, 250, 0.5);
            border-color: rgba(96, 165, 250, 0.8);
            animation: float 2s ease-in-out infinite;
        }
        
        .project-card:active {
            transform: scale(0.98);
        }
        
        /* Click notification modal */
        .project-modal {
            display: none;
            position: fixed;
            z-index: 10000;
            left: 0;
            top: 0;
            width: 100%;
            height: 100%;
            background-color: rgba(0,0,0,0.7);
            backdrop-filter: blur(5px);
        }
        
        .project-modal.show {
            display: flex;
            align-items: center;
            justify-content: center;
            animation: fadeIn 0.3s ease-out;
        }
        
        @keyframes fadeIn {
            from { opacity: 0; }
            to { opacity: 1; }
        }
        
        .modal-content {
            background: linear-gradient(135deg, 
                rgba(30, 58, 138, 0.95) 0%,
                rgba(59, 130, 246, 0.95) 100%
            );
            padding: 40px;
            border-radius: 20px;
            max-width: 500px;
            text-align: center;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5);
            border: 2px solid rgba(96, 165, 250, 0.6);
            animation: slideUp 0.3s ease-out;
        }
        
        @keyframes slideUp {
            from { transform: translateY(50px); opacity: 0; }
            to { transform: translateY(0); opacity: 1; }
        }
        
        .modal-icon {
            font-size: 60px;
            margin-bottom: 20px;
        }
        
        .modal-title {
            font-size: 24px;
            font-weight: 700;
            color: #ffffff;
            margin-bottom: 15px;
        }
        
        .modal-text {
            font-size: 16px;
            color: #dbeafe;
            line-height: 1.6;
            margin-bottom: 25px;
        }
        
        .modal-button {
            background: linear-gradient(135deg, #60a5fa 0%, #3b82f6 100%);
            color: white;
            border: none;
            padding: 12px 30px;
            border-radius: 10px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
            box-shadow: 0 4px 15px rgba(96, 165, 250, 0.4);
            margin: 5px;
        }
        
        .modal-button:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(96, 165, 250, 0.6);
        }
        
        .modal-button.secondary {
            background: linear-gradient(135deg, #94a3b8 0%, #64748b 100%);
        }
        
        .modal-button.secondary:hover {
            box-shadow: 0 6px 20px rgba(148, 163, 184, 0.6);
        }
        
        .modal-buttons {
            display: flex;
            gap: 10px;
            justify-content: center;
            flex-wrap: wrap;
            margin-top: 20px;
        }
        
        .project-icon {
            font-size: 40px;
            margin-bottom: 10px;
        }
        
        .project-name {
            font-size: 18px;
            font-weight: 700;
            color: #ffffff;
            margin: 0 0 8px 0;
            text-shadow: 0 2px 10px rgba(0, 0, 0, 0.3);
        }
        
        .project-category {
            font-size: 13px;
            color: #bfdbfe;
            font-weight: 500;
            opacity: 0.9;
        }
        
        .project-desc {
            font-size: 13px;
            color: #dbeafe;
            line-height: 1.4;
            margin-top: auto;
        }
        
        @media (max-width: 768px) {
            .showcase-title {
                font-size: 28px;
            }
            
            .project-card {
                min-width: 240px;
                height: 180px;
                padding: 20px;
            }
            
            .project-icon {
                font-size: 32px;
            }
            
            .project-name {
                font-size: 16px;
            }
        }
        </style>
        
        <div class="showcase-container">
            <div class="showcase-header">
                <h1 class="showcase-title">Intellecta AI Product Family</h1>
                <p class="showcase-subtitle">🤖 IntellaPersona-Career Agentic Bot</p>
                <p class="showcase-legal">© 2024-2025 Intellecta Solutions. All Rights Reserved. | Patent Pending Technology</p>
                <p class="showcase-legal">🔒 Proprietary AI System - Unauthorized use is strictly prohibited.</p>
            </div>
            
            <div class="carousel-wrapper">
                <div class="carousel-track">
                    <!-- Company -->
                    <div class="project-card">
                        <div class="project-icon">🏢</div>
                        <div>
                            <h3 class="project-name">Intellecta Website</h3>
                            <p class="project-category">Company</p>
                        </div>
                        <p class="project-desc">Corporate web platform with modern UI/UX</p>
                    </div>
                    
                    <!-- LLMOps Tools -->
                    <div class="project-card">
                        <div class="project-icon">🔧</div>
                        <div>
                            <h3 class="project-name">Intellecta CLI</h3>
                            <p class="project-category">LLMOps Tools</p>
                        </div>
                        <p class="project-desc">AI-powered command line interface</p>
                    </div>
                    
                    <div class="project-card">
                        <div class="project-icon">🎯</div>
                        <div>
                            <h3 class="project-name">Intellecta Framework</h3>
                            <p class="project-category">LLMOps Tools</p>
                        </div>
                        <p class="project-desc">Core AI development platform</p>
                    </div>
                    
                    <div class="project-card">
                        <div class="project-icon">💬</div>
                        <div>
                            <h3 class="project-name">WhatsApp Bot</h3>
                            <p class="project-category">LLMOps Tools</p>
                        </div>
                        <p class="project-desc">Intelligent messaging automation</p>
                    </div>
                    
                    <!-- Agentic Projects -->
                    <div class="project-card">
                        <div class="project-icon">☁️</div>
                        <div>
                            <h3 class="project-name">Cloud Automation/Management With Terraform Agents For AWS/Azure/GCP</h3>
                            <p class="project-category">Agentic Projects</p>
                        </div>
                        <p class="project-desc">Cost-effective cloud development and management</p>
                    </div>
                    
                    <div class="project-card">
                        <div class="project-icon">🌐</div>
                        <div>
                            <h3 class="project-name">Web Orchestrator</h3>
                            <p class="project-category">Agentic Projects</p>
                        </div>
                        <p class="project-desc">Browser automation platform</p>
                    </div>
                    
                    <!-- DevSecOps Solutions -->
                    <div class="project-card">
                        <div class="project-icon">🧪</div>
                        <div>
                            <h3 class="project-name">TestBot Premium</h3>
                            <p class="project-category">Agentic DevSecOps</p>
                        </div>
                        <p class="project-desc">AI-driven automated testing solution</p>
                    </div>
                    
                    <div class="project-card">
                        <div class="project-icon">🛡️</div>
                        <div>
                            <h3 class="project-name">CodeGuard Enterprise</h3>
                            <p class="project-category">Pipeline Security</p>
                        </div>
                        <p class="project-desc">AI-powered vulnerability scanning</p>
                    </div>
                    
                    <div class="project-card">
                        <div class="project-icon">🚀</div>
                        <div>
                            <h3 class="project-name">BuildMaster Pro</h3>
                            <p class="project-category">Build Operations</p>
                        </div>
                        <p class="project-desc">ML-optimized CI/CD pipelines</p>
                    </div>
                    
                    <!-- RAG & Kubernetes -->
                    <div class="project-card">
                        <div class="project-icon">📚</div>
                        <div>
                            <h3 class="project-name">SDLC Knowledge Library</h3>
                            <p class="project-category">Agentic RAG</p>
                        </div>
                        <p class="project-desc">Enterprise knowledge base solution</p>
                    </div>
                    
                    <div class="project-card">
                        <div class="project-icon">☸️</div>
                        <div>
                            <h3 class="project-name">KubeGenius</h3>
                            <p class="project-category">K8s Deployment</p>
                        </div>
                        <p class="project-desc">AI-powered release strategies</p>
                    </div>
                    
                    <!-- Duplicate for seamless loop -->
                    <div class="project-card">
                        <div class="project-icon">🏢</div>
                        <div>
                            <h3 class="project-name">Intellecta Backend/Frontend API Orchestrator</h3>
                            <p class="project-category">Company</p>
                        </div>
                        <p class="project-desc">End-to-end API orchestration for seamless integration</p>
                    </div>
                    
                    <div class="project-card">
                        <div class="project-icon">🔧</div>
                        <div>
                            <h3 class="project-name">Intellecta CLI</h3>
                            <p class="project-category">LLMOps Tools</p>
                        </div>
                        <p class="project-desc">AI-powered command line interface</p>
                    </div>
                    
                    <div class="project-card">
                        <div class="project-icon">🎯</div>
                        <div>
                            <h3 class="project-name">Intellecta Framework</h3>
                            <p class="project-category">LLMOps Tools</p>
                        </div>
                        <p class="project-desc">Core AI development platform</p>
                    </div>
                    
                    <div class="project-card">
                        <div class="project-icon">💬</div>
                        <div>
                            <h3 class="project-name">WhatsApp Bot</h3>
                            <p class="project-category">LLMOps Tools</p>
                        </div>
                        <p class="project-desc">Intelligent messaging automation</p>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- Project Details Modal -->
        <div id="projectModal" class="project-modal">
            <div class="modal-content">
                <div class="modal-icon">🔒</div>
                <h2 class="modal-title">Interested in This Project?</h2>
                <p class="modal-text">
                    To learn more about <strong id="projectName">this project</strong> and other Intellecta Solutions offerings:
                    <br><br>
                    <strong style="color: #60a5fa;">✨ Choose Your Path:</strong>
                </p>
                
                <div class="modal-buttons">
                    <button class="modal-button" onclick="getVisitorAccess()">
                        🎫 Get Visitor Access<br>
                        <small style="font-size: 12px; opacity: 0.8;">(5 Free Questions)</small>
                    </button>
                    <button class="modal-button secondary" onclick="closeProjectModal()">
                        ❌ Close
                    </button>
                </div>
                
                <p class="modal-text" style="margin-top: 20px; font-size: 14px; opacity: 0.9;">
                    <strong>💡 Alternative:</strong> Contact us directly<br>
                    <code style="background: rgba(0,0,0,0.3); padding: 5px 10px; border-radius: 5px; display: inline-block; margin-top: 5px; font-size: 12px;">
                        Email: your@email.com / Reason: I'm interested in [project]
                    </code>
                </p>
            </div>
        </div>
        """)
        
        # State management
        current_username = gr.State(value=None)
        
        # Tabs with controllable selection - Default to Chat tab
        with gr.Tabs(selected=0) as tabs:  # selected=0 means Chat tab opens by default
            # Chat Section (First Tab - Default)
            with gr.Tab("💬 Chat", id=0):
                # Limit reached message
                limit_reached_display = gr.Markdown(visible=False)
                
                # Welcome message (shown after login)
                welcome_message = gr.Markdown(visible=False)
                
                # Login status display (hidden after login)
                login_status_display = gr.Markdown(visible=False)
                
                # Clickable button to navigate to Login tab
                get_started_btn = gr.Button("🚀 Get Started - Login / Sign Up", variant="primary", size="lg")
                
                # Chat area - Comfortable size with proper spacing
                # Note: Using Gradio 4.16.0 compatible parameters only
                chatbot = gr.Chatbot(
                    label="💬 IntellaPersona AI Assistant",
                    height=550,
                    value=[[None, f"👋 **Welcome! I'm IntellaPersona**\n\nPlease click the **'Get Started'** button above to **Login** or **Sign Up** and start chatting with me!\n\n✨ I'm here to help you learn about {me.name}'s professional experience, skills, and projects."]],
                    elem_classes="intellecta-chatbot"
                )
                
                # Input area
                msg = gr.Textbox(
                    label="Your message", 
                    placeholder="👆 Click 'Get Started' button above to activate chat...",
                    interactive=False
                )
                
                # Send and Clear buttons - visible from start
                with gr.Row():
                    send_btn = gr.Button("Send 📤", variant="primary", interactive=False)
                    clear_btn = gr.Button("Clear 🗑️", variant="secondary")
                
                # Quick action cards below chat - visible from start
                gr.Markdown("**💡 Quick Start Topics:**")
                with gr.Row() as quick_actions:
                    quick_btn1 = gr.Button("📊 Experience", size="sm", scale=1)
                    quick_btn2 = gr.Button("🛠️ Skills", size="sm", scale=1)
                    quick_btn3 = gr.Button("💼 Projects", size="sm", scale=1)
                    quick_btn4 = gr.Button("🤝 Collaborate", size="sm", scale=1)
                
                # Query counter display
                query_status = gr.Markdown()
            
            # Chat functions
            def respond(message, history, username):
                if not username or username == "visitor":
                    return history, "❌ Please login first! Redirecting you to Login/Sign Up tab...", "", gr.Tabs(selected=1)
                
                # IMMEDIATE: Add user message to history first (so it shows immediately)
                if not message.strip():
                    return history, "", "", gr.Tabs()
                
                # Show user question immediately
                history.append({"role": "user", "content": message})
                
                # Note: We removed yield here - Gradio will show the user message immediately anyway
                # The key is that we append it BEFORE processing the response
                
                # Check if message contains Email/Reason format (PRIORITY CHECK - before query limit)
                import re
                email_match = re.search(r'(?i)email\s*:\s*([^\n/]+?)(?:\s*[/\n]|\s*reason\s*:|$)', message)
                reason_match = re.search(r'(?i)reason\s*:\s*([^\n/]+?)(?:\s*[/\n]|\s*email\s*:|$)', message)
                
                if email_match and reason_match:
                    # User wants to contact directly - bypass query system
                    email = email_match.group(1).strip()
                    reason = reason_match.group(1).strip()
                    
                    user_manager = UserManager()
                    user_data = user_manager.get_user_data(username)
                    
                    # User message already added to history above
                    # (removed duplicate append)
                    
                    # Save to database using user_manager
                    user_manager.request_upgrade(username, email, reason)
                    
                    # Also save to contacts table
                    conn = sqlite3.connect(user_manager.db_path)
                    cursor = conn.cursor()
                    cursor.execute("""
                        INSERT INTO contacts (username, email, reason, created_at)
                        VALUES (?, ?, ?, datetime('now'))
                    """, (username, email, reason))
                    conn.commit()
                    
                    # Mark contact_submitted flag and END query access
                    cursor.execute("""
                        UPDATE users SET contact_submitted = 1, query_count = query_limit WHERE username = ?
                    """, (username,))
                    conn.commit()
                    conn.close()
                    
                    # Send PushOver notification
                    try:
                        send_pushover_notification(
                            title=f"📧 DIRECT Contact Request from {username}",
                            message=f"""Direct contact request (before query limit):
                            
Username: {username}
Email: {email}
Reason: {reason}
Queries used: {user_data.get('query_count', 0)}/{user_data.get('query_limit', 5)}

This user chose to contact you directly without using all their queries.""",
                            priority=1
                        )
                        notification_status = "✅ Notification sent via PushOver"
                    except Exception as e:
                        notification_status = f"⚠️ Notification failed: {str(e)}"
                        print(f"PushOver notification error: {e}")
                    
                    # Confirmation message
                    bot_response = f"""### ✅ Thank you for reaching out directly!

**I've received:**
- 📧 Email: {email}
- 💬 Reason: {reason}

**What happens next:**
1. ✅ Your request has been sent to {me.name} via PushOver
2. 📬 I'll review your information within 24-48 hours
3. 📧 You'll receive a response at: {email}
4. 🎉 If approved, you'll get unlimited access to continue our conversation

**Your contact information is confidential and will only be used to respond to your request.**

Thank you for your interest in Intellecta Solutions! 😊

{notification_status}

---

*Note: Your visitor queries have been closed since you've chosen to contact directly. Awaiting approval for unlimited access.*"""
                    
                    history.append({"role": "assistant", "content": bot_response})
                    
                    status_msg = "📧 **Direct contact submitted!** Awaiting approval..."
                    return history, status_msg, "", gr.Tabs()
                
                # Check if user has reached limit BEFORE processing
                user_manager = UserManager()
                can_query, current, limit = user_manager.check_query_limit(username)
                user_data = user_manager.get_user_data(username)
                
                # If limit reached, this is for contact info collection only (NO LLM call)
                if not can_query and user_data["tier"] == "visitor":
                    # User message already added to history above
                    # (removed duplicate append)
                    
                    # Parse email and reason directly (NO LLM call)
                    import re
                    
                    # More flexible regex patterns:
                    # - Captures until newline, slash, or "Reason:" keyword (whichever comes first)
                    # - Case insensitive
                    # - Handles both single-line and multi-line formats
                    email_match = re.search(r'(?i)email\s*:\s*([^\n/]+?)(?:\s*[/\n]|\s*reason\s*:|$)', message)
                    reason_match = re.search(r'(?i)reason\s*:\s*([^\n/]+?)(?:\s*[/\n]|\s*email\s*:|$)', message)
                    
                    if email_match and reason_match:
                        email = email_match.group(1).strip()
                        reason = reason_match.group(1).strip()
                        
                        # Save to database using user_manager (saves to both users and upgrade_requests)
                        user_manager.request_upgrade(username, email, reason)
                        
                        # Also save to contacts table for backward compatibility
                        conn = sqlite3.connect(user_manager.db_path)
                        cursor = conn.cursor()
                        cursor.execute("""
                            INSERT INTO contacts (username, email, reason, created_at)
                            VALUES (?, ?, ?, datetime('now'))
                        """, (username, email, reason))
                        conn.commit()
                        
                        # Mark contact_submitted flag
                        cursor.execute("""
                            UPDATE users SET contact_submitted = 1 WHERE username = ?
                        """, (username,))
                        conn.commit()
                        conn.close()
                        
                        # Send PushOver notification
                        try:
                            send_pushover_notification(
                                title=f"📧 Contact Request from {username}",
                                message=f"Username: {username}\nEmail: {email}\nReason: {reason}",
                                priority=1  # High priority to bypass quiet hours
                            )
                            notification_status = "✅ Notification sent"
                        except Exception as e:
                            notification_status = f"⚠️ Notification failed: {str(e)}"
                            print(f"PushOver notification error: {e}")
                        
                        # Confirmation message to user
                        bot_response = f"""### ✅ Thank you for your contact information!

**I've received:**
- Email: {email}
- Reason: {reason}

**What happens next:**
1. Your request has been sent to {me.name}
2. I'll review your information within 24-48 hours
3. If approved, you'll receive unlimited access
4. I'll reach out to you personally at: {email}

Thank you for your interest in connecting! 😊

{notification_status}"""
                    else:
                        # Invalid format - guide the user with flexible options
                        bot_response = f"""### ⚠️ Invalid format

Please provide your information using **Email:** and **Reason:** keywords.

**You can use either format:**

**Option 1** (Multi-line):
```
Email: your.email@example.com
Reason: I'm interested in...
```

**Option 2** (Single-line with slash):
```
Email: your.email@example.com / Reason: I'm interested in...
```

**Option 3** (Single-line space-separated):
```
Email: your.email@example.com Reason: I'm interested in...
```

**Example:**
```
Email: john.doe@company.com / Reason: Discussing collaboration opportunities
```

Please try again with one of these formats. 😊"""
                    
                    # Add bot response to history
                    history.append({"role": "assistant", "content": bot_response})
                    
                    status_msg = "📧 **Contact information processed!** Check the message above."
                    return history, status_msg, "", gr.Tabs()
                
                # Normal query processing
                # User message already added to history above
                # (removed duplicate append)
                
                # Get bot response
                bot_response = me.chat(message, history, username)
                
                # Add bot response to history
                history.append({"role": "assistant", "content": bot_response})
                
                # Update query status
                can_query_after, current_after, limit_after = user_manager.check_query_limit(username)
                
                # Check if this was the last query for a visitor
                if user_data and user_data["tier"] == "visitor" and current_after >= limit_after:
                    # Add automatic follow-up message requesting contact info
                    contact_request_msg = f"""

---

### 🎉 Thank you for using all your free queries!

I hope I was able to help you learn about {me.name}'s experience and skills.

**📧 Would you like to continue our conversation?**

If you'd like unlimited access or want to discuss potential collaboration opportunities, please share:

1. **Your email address**
2. **Why you'd like to connect** (e.g., job opportunity, collaboration, consultation, etc.)

**You can use any of these formats:**

**Multi-line:**
```
Email: your.email@example.com
Reason: I'm interested in...
```

**Single-line (easier):**
```
Email: your@email.com / Reason: I'm interested in...
```

I'll review your request and reach out to you personally! 😊"""
                    history.append({"role": "assistant", "content": contact_request_msg})
                
                if limit_after == -1:
                    status_msg = f"✅ **Unlimited access** | Queries used: {current_after}"
                else:
                    remaining = limit_after - current_after
                    if remaining <= 0:
                        status_msg = f"� **Awaiting your contact information** | Please use the format shown above"
                    elif remaining <= 2:
                        status_msg = f"⚠️ **{remaining} queries remaining** | Consider requesting unlimited access"
                    else:
                        status_msg = f"📊 **Queries:** {current_after}/{limit_after} | Remaining: {remaining}"
                
                return history, status_msg, "", gr.Tabs()
            
            # Enable/disable chat based on user status
            def update_chat_interface(username, current_history):
                if username and username != "visitor":
                    user_manager = UserManager()
                    user_data = user_manager.get_user_data(username)
                    
                    if user_data:
                        tier = user_data["tier"]
                        current = user_data["query_count"]
                        limit = user_data["query_limit"]
                        remaining = limit - current
                        contact_submitted = user_data.get("contact_submitted", 0)
                        
                        # Check if contact already submitted - DISABLE input
                        if contact_submitted == 1:
                            submitted_msg = f"""### ✅ Contact Information Received!

Thank you for submitting your contact information.

**What happens next:**
1. Your request has been sent to {me.name}
2. I'll review your information within 24-48 hours
3. If approved, you'll receive unlimited access
4. I'll reach out to you personally at your email

**Please wait for approval.** You'll be notified soon! 😊"""
                            
                            return (
                                gr.update(value=submitted_msg, visible=True),  # limit_reached_display
                                gr.update(visible=False),  # welcome_message
                                gr.update(visible=False),  # login_status_display
                                gr.update(visible=False),  # quick_actions (hidden)
                                gr.update(interactive=False, placeholder="✅ Contact info submitted! Awaiting approval..."),
                                gr.update(interactive=False),
                                f"✅ **Contact submitted!** Awaiting approval...",
                                current_history  # Keep current history
                            )
                        
                        # Check if limit reached (but contact NOT submitted yet)
                        if tier == "visitor" and remaining <= 0:
                            limit_msg = """### 🎉 Thank you for using all your free queries!

I hope I was able to help you learn about {me.name}'s experience and skills.

**📧 Would you like to continue our conversation?**

If you'd like unlimited access or want to discuss potential collaboration opportunities, please share:

1. **Your email address**
2. **Why you'd like to connect** (e.g., job opportunity, collaboration, consultation, etc.)

**You can use any of these formats:**

**Multi-line:**
```
Email: your.email@example.com
Reason: I'm interested in...
```

**Single-line (easier):**
```
Email: your@email.com / Reason: I'm interested in...
```

I'll review your request and reach out to you personally! 😊"""
                            
                            return (
                                gr.update(visible=False),
                                gr.update(value=limit_msg, visible=True),
                                gr.update(visible=False),
                                gr.update(visible=False),
                                gr.update(interactive=True, placeholder="Email: your@email.com / Reason: I'm interested in..."),
                                gr.update(interactive=True),
                                f"� **Awaiting contact info** | Please use the format shown above",
                                current_history  # Keep current history
                            )
                        
                        # Create welcome message - COMPACT for better UX
                        welcome_msg = ""
                        if tier == "unlimited":
                            welcome_msg = f"""### 👋 Welcome back!

You have **unlimited access**. Ask me anything! 🚀"""
                            status = "✅ **Unlimited access** | Ask away!"
                        else:
                            welcome_msg = f"""### 👋 Ready to chat!

**You have {remaining} free questions.** Ask about my experience, skills, or projects! 

💡 Tip: Use the quick buttons below or type your own question."""
                            status = f"✅ **Welcome!** | {remaining} queries remaining"
                        
                        # Only add greeting if history is empty
                        if not current_history or len(current_history) == 0:
                            initial_history = [{
                                "role": "assistant", 
                                "content": f"Hello! 👋 I'm an AI assistant representing {me.name}. I'm here to answer your questions about professional experience, skills, projects, and potential collaborations. What would you like to know?"
                            }]
                        else:
                            initial_history = current_history
                        
                        return (
                            gr.update(visible=False),  # limit_reached_display
                            gr.update(value=welcome_msg, visible=True),  # welcome_message
                            gr.update(visible=False),  # login_status_display
                            gr.update(visible=True),  # quick_actions
                            gr.update(interactive=True, placeholder="Ask me about my experience, skills, or projects..."),
                            gr.update(interactive=True),
                            status,
                            initial_history  # Keep or initialize history
                        )
                
                return (
                    gr.update(visible=False),  # limit_reached_display
                    gr.update(visible=False),  # welcome_message
                    gr.update(visible=False),  # login_status_display
                    gr.update(visible=True),  # quick_actions (still visible for preview)
                    gr.update(interactive=False, placeholder="👆 Click 'Get Started' button above to activate chat..."),
                    gr.update(interactive=False),
                    "⚠️ Please click 'Get Started' to begin",
                    [{
                        "role": "assistant",
                        "content": f"👋 Welcome! I'm {me.name}'s AI assistant.\n\n**Click 'Get Started' above to begin chatting!**\n\nI can help you learn about:\n• Professional experience\n• Technical skills\n• Projects & achievements\n• Collaboration opportunities"
                    }]
                )
            
            # Quick action handlers
            def quick_action(question, history, username):
                return respond(question, history, username)
            
            quick_btn1.click(
                lambda h, u: quick_action("Tell me about your professional experience and background", h, u),
                inputs=[chatbot, current_username],
                outputs=[chatbot, query_status, msg, tabs]
            ).then(
                update_chat_interface,
                inputs=[current_username, chatbot],
                outputs=[limit_reached_display, welcome_message, login_status_display, quick_actions, msg, send_btn, query_status, chatbot]
            )
            
            quick_btn2.click(
                lambda h, u: quick_action("What are your main technical skills and expertise?", h, u),
                inputs=[chatbot, current_username],
                outputs=[chatbot, query_status, msg, tabs]
            ).then(
                update_chat_interface,
                inputs=[current_username, chatbot],
                outputs=[limit_reached_display, welcome_message, login_status_display, quick_actions, msg, send_btn, query_status, chatbot]
            )
            
            quick_btn3.click(
                lambda h, u: quick_action("Can you show me some of your notable projects?", h, u),
                inputs=[chatbot, current_username],
                outputs=[chatbot, query_status, msg, tabs]
            ).then(
                update_chat_interface,
                inputs=[current_username, chatbot],
                outputs=[limit_reached_display, welcome_message, login_status_display, quick_actions, msg, send_btn, query_status, chatbot]
            )
            
            quick_btn4.click(
                lambda h, u: quick_action("I'm interested in collaboration opportunities. How can we work together?", h, u),
                inputs=[chatbot, current_username],
                outputs=[chatbot, query_status, msg, tabs]
            ).then(
                update_chat_interface,
                inputs=[current_username, chatbot],
                outputs=[limit_reached_display, welcome_message, login_status_display, quick_actions, msg, send_btn, query_status, chatbot]
            )
            
            # Note: State.change() not available in Gradio 4.16.0
            # Chat interface updates are handled by login_btn.click() and other events
            
            send_btn.click(
                respond,
                inputs=[msg, chatbot, current_username],
                outputs=[chatbot, query_status, msg, tabs]
            ).then(
                update_chat_interface,
                inputs=[current_username, chatbot],
                outputs=[limit_reached_display, welcome_message, login_status_display, quick_actions, msg, send_btn, query_status, chatbot]
            )
            
            msg.submit(
                respond,
                inputs=[msg, chatbot, current_username],
                outputs=[chatbot, query_status, msg, tabs]
            ).then(
                update_chat_interface,
                inputs=[current_username, chatbot],
                outputs=[limit_reached_display, welcome_message, login_status_display, quick_actions, msg, send_btn, query_status, chatbot]
            )
            
            clear_btn.click(lambda: ([], ""), outputs=[chatbot, query_status])
        
        # Login / Sign Up Section (Second Tab)
        with gr.Tab("🔐 Login / Sign Up", id=1):
            gr.Markdown("""### 🔑 Approved User Login
            
**Already have approved credentials?** Login here to access unlimited queries.

**New visitor?** Go to the **'💬 Chat'** tab and click **'Get Started'** for 5 free questions!
            """)
            
            login_username = gr.Textbox(label="Username", placeholder="Enter your approved username")
            login_password = gr.Textbox(label="Password", type="password", placeholder="Enter your password")
            login_btn = gr.Button("Login", variant="primary", size="lg")
            login_output = gr.Markdown()
            
            # Keep visitor_output for compatibility but make it invisible
            visitor_output = gr.Markdown(visible=False)
            
            
            def handle_login(username, password):
                success, message, user = login_user(username, password)
                if success:
                    return message, user, gr.update(), gr.update()
                return message, None, gr.update(), gr.update()
            
            def handle_visitor_creation(request: gr.Request, show_credentials=True):
                """Create visitor credentials with IP tracking and auto-login
                
                Args:
                    show_credentials: If True, shows username/password. If False, just welcomes user.
                """
                user_manager = UserManager()
                security = SecurityManager()
                
                # Get client IP
                client_ip = None
                try:
                    if hasattr(request, 'client') and hasattr(request.client, 'host'):
                        client_ip = request.client.host
                except:
                    pass
                
                # Check IP limit - Only allow one visitor account per IP per 24 hours
                # Skip this check in TEST_MODE for development/testing
                if not TEST_MODE and client_ip and user_manager.check_ip_visitor_limit(client_ip):
                    message = """### ⚠️ Visitor Account Already Created

You've already created a visitor account from this IP address in the last 24 hours.

**What you can do:**
- Use your existing visitor credentials to login in the **'🔐 Login / Sign Up'** tab
- Wait 24 hours to create a new visitor account
- Request unlimited access if you've used your queries

If you lost your credentials, please use the direct contact method:
**Email:** your@email.com / **Reason:** I lost my credentials and need help
                    """
                    return message, None, gr.Tabs(selected=1)  # Redirect to Login tab
                
                username, password = user_manager.create_visitor_account(client_ip)
                
                # ✅ CRITICAL: Create session for the visitor (30 min timeout)
                security.create_session(username, session_timeout_minutes=30)
                security.log_usage(username, "visitor_created", f"IP: {client_ip or 'unknown'}")
                
                # Two different messages based on context
                if show_credentials:
                    # For Login tab - show full credentials
                    message = f"""### 🎉 Welcome! Your Free Account is Ready!

**Username:** `{username}`  
**Password:** `{password}`

⚠️ **Save these credentials!** You'll need them to log back in.

---

✅ **You're now logged in with 5 free questions!**

🚀 **Click on the '💬 Chat' tab above to start chatting!**
"""
                else:
                    # For Chat tab - no credentials needed (seamless experience)
                    message = ""  # Will be replaced by update_chat_interface
                
                return message, username, gr.Tabs(selected=0)
            
            # Get Started button from Chat tab - creates visitor WITHOUT showing credentials
            # Wrapper to pass show_credentials=False
            def handle_get_started(request: gr.Request):
                return handle_visitor_creation(request, show_credentials=False)
            
            get_started_btn.click(
                handle_get_started,
                outputs=[login_status_display, current_username, tabs]
            ).then(
                update_chat_interface,
                inputs=[current_username, chatbot],
                outputs=[limit_reached_display, welcome_message, login_status_display, quick_actions, msg, send_btn, query_status, chatbot]
            )
            
            login_btn.click(
                handle_login,
                inputs=[login_username, login_password],
                outputs=[login_output, current_username, login_username, login_password]
            )
        
        # Upgrade Request Section (Third Tab)
        with gr.Tab("⬆️ Request Unlimited Access", id=2):
            gr.Markdown(f"""
            ### 🚀 Get Unlimited Access!
            
            Reached your query limit? Request unlimited access by providing:
            - Your email address
            - Your intent for reaching out to {me.name}
            
            {me.name} will review your request and reach out to you if approved.
            """)
            
            upgrade_username_display = gr.Textbox(label="Your Username (will be filled automatically)", interactive=False)
            upgrade_email = gr.Textbox(label="Email Address", placeholder="your.email@example.com")
            upgrade_intent = gr.Textbox(
                label="Why do you want to connect?",
                placeholder="I'm interested in discussing collaboration opportunities...",
                lines=5
            )
            upgrade_btn = gr.Button("Submit Request", variant="primary")
            upgrade_output = gr.Markdown()
            
            # Note: State.change() not available in Gradio 4.16.0
            # Username display updates are handled by login events
            
            upgrade_btn.click(
                request_unlimited_access,
                inputs=[current_username, upgrade_email, upgrade_intent],
                outputs=[upgrade_output]
            )
        
        # About Section
        with gr.Tab("ℹ️ About", id=3):
            gr.Markdown(f"""
            ## About This Chatbot
            
            This AI assistant represents **{me.name}** and can answer questions about:
            - 📊 Professional background and experience
            - 🛠️ Technical skills and expertise
            - 🎓 Education and certifications
            - 💼 Projects and achievements
            
            ### Access Tiers:
            
            | Tier | Queries | Features |
            |------|---------|----------|
            | 🎫 Visitor | 5 | Basic Q&A access |
            | ✨ Unlimited | ∞ | Full access after approval |
            
            ### How It Works:
            1. Create a visitor account (5 free queries)
            2. Ask questions about {me.name}
            3. Request unlimited access by providing email + intent
            4. Get approved and enjoy unlimited conversations!
            
            ---
            
            **Powered by:** OpenAI GPT-4, RAG (Retrieval-Augmented Generation), and Gradio
            """)
        
        # Intellecta Solutions - Company Section (Tab 4)
        with gr.Tab("🏢 Intellecta Solutions", id=4):
            def render_company_section(username):
                user_manager = UserManager()
                user_data = user_manager.get_user_data(username) if username else None
                tier = user_data.get("tier", "visitor") if user_data else "visitor"
                
                if tier == "unlimited":
                    # Full access for approved users
                    return gr.Markdown("""
# 🏢 Intellecta Solutions

## Kurumsal Web Sitesi Projesi

**Intellecta Solutions** şirketinin resmi web platformu. Modern web teknolojileri ile geliştirilmiş, kurumsal kimliği yansıtan kapsamlı bir dijital varlık.

### 📊 Proje Özellikleri
- **Boyut:** 130 MB (Zengin görsel ve içerik kütüphanesi)
- **Teknoloji Stack:** Modern web teknolojileri
- **Durum:** Private repository
- **Son Güncelleme:** 2024-06-30

### 🎯 Şirket Vizyonu
Intellecta Solutions, yapay zeka ve LLM teknolojilerini iş süreçlerine entegre ederek kurumsal dönüşümü hızlandıran teknoloji şirketidir.

### 💡 Hizmetler
- **AI/LLM Danışmanlığı** - Kurumsal AI stratejileri
- **MLOps Solutions** - Production-grade ML sistemleri
- **Agentic AI Development** - Akıllı otonom sistemler
- **RAG Implementations** - Knowledge base entegrasyonları

### 🔗 Ürün Ekosistemi

**Intellecta Framework** - Core AI development framework (Python, Apache 2.0)

**Intellecta CLI** - Terminal tabanlı AI aracı (Python, MIT License)

**Intellecta WhatsApp Bot** - Mesajlaşma AI entegrasyonu (JavaScript, GPL-3.0)

### 🌐 Web Platformu Özellikleri
- Responsive tasarım
- SEO optimize edilmiş içerik
- Hızlı yüklenme süreleri
- Modern UI/UX deneyimi
- Erişilebilirlik standartları

---

*Intellecta Solutions - Building the future with AI*
                    """)
                else:
                    # Locked preview for visitors
                    return gr.Markdown("""
# 🏢 Intellecta Solutions

## 🔒 Premium İçerik - Onaylı Kullanıcılar İçin

**Intellecta Solutions** hakkında detaylı bilgi görmek için **unlimited access** gereklidir.

### 👀 İçerik Önizlemesi:
- ✅ Kurumsal web sitesi projesi bilgileri
- ✅ Şirket vizyonu ve hizmetler
- ✅ Ürün ekosistemi (Intellecta Framework, CLI, WhatsApp Bot)
- ✅ Teknoloji stack ve özellikler

### 🚀 Erişim İçin:
1. **'⬆️ Request Unlimited Access'** sekmesine gidin
2. Email ve iletişim nedeninizi paylaşın
3. Onay aldıktan sonra bu içeriğe **tam erişim** kazanın

---

💡 **5 ücretsiz sorunuzla chat sekmesinden benimle konuşabilirsiniz!**
                    """)
            
            company_content = gr.Markdown()
            
            # Note: State.change() not available in Gradio 4.16.0
            # Content rendering handled by login events and initial render
            
            # Initial render
            demo.load(
                lambda: render_company_section(None),
                outputs=[company_content]
            )
        
        # LLMOps Projects Section (Tab 5) - LOCKED for visitors
        with gr.Tab("🤖 LLMOps Çalışmaları", id=5):
            def render_llmops_section(username):
                user_manager = UserManager()
                user_data = user_manager.get_user_data(username) if username else None
                tier = user_data.get("tier", "visitor") if user_data else "visitor"
                
                if tier == "unlimited":
                    # Full access
                    return gr.Markdown("""
# 🤖 LLMOps Çalışmaları ve AI Projeleri

## Intellecta AI Ekosistemi

### 1️⃣ Intellecta CLI - AI Command Line Interface

**Komut satırı üzerinden AI gücü**

#### 🚀 Özellikler
- Terminal tabanlı AI etkileşimleri
- Hızlı komut satırı işlemleri
- DevOps ve CI/CD pipeline entegrasyonları
- Script automation desteği

#### 💻 Teknoloji
- **Python** ile geliştirildi
- **MIT License** - Açık kaynak dostu
- Modüler ve genişletilebilir yapı

#### 🎯 Kullanım Senaryoları
```bash
# AI-powered code review
intellecta review --file app.py

# Documentation generation
intellecta docs --project ./my-project

# Automated testing suggestions
intellecta test-gen --module users.py
```

---

### 2️⃣ Intellecta Framework - Core AI Development Platform

**AI uygulamaları için temel framework**

#### 🏗️ Mimari Bileşenler
- **LLM Integrations** - Multiple provider support
- **RAG Engine** - Retrieval Augmented Generation
- **Agent System** - Multi-agent orchestration
- **Tool Registry** - Extensible tool ecosystem

#### 📦 Teknoloji Stack
- **Python** (Apache 2.0 License)
- Modüler ve ölçeklenebilir yapı
- Production-ready components

#### 💡 Özellikler
- Hızlı prototipleme
- Enterprise-grade güvenlik
- Comprehensive documentation
- Active community support

---

### 3️⃣ Intellecta WhatsApp Bot - Messaging AI Integration

**WhatsApp üzerinden AI asistan**

#### 📱 Platform Özellikleri
- WhatsApp Business API entegrasyonu
- 7/24 otomatik yanıt sistemi
- Müşteri desteği otomasyonu
- Multi-language support

#### 🔧 Teknoloji
- **JavaScript/Node.js**
- **GPL-3.0 License**
- Real-time message processing

#### 🎯 Kullanım Alanları
- Customer support automation
- Lead generation
- Information dissemination
- Interactive surveys

---

## 📊 LLMOps Best Practices

### CI/CD for AI Models
- Automated testing pipelines
- Model versioning
- A/B testing infrastructure
- Rollback strategies

### Monitoring & Observability
- Real-time performance tracking
- Cost optimization
- Error rate monitoring
- User feedback loops

---

*Tüm projeler production-grade quality ile geliştirilmiştir.*
                    """)
                else:
                    # Locked preview
                    return gr.Markdown("""
# 🤖 LLMOps Çalışmaları

## 🔒 Premium İçerik - Onaylı Kullanıcılar İçin

Bu bölümde **3 özel LLMOps projesi** hakkında detaylı bilgi bulunmaktadır.

### 🎯 İçerik:

#### 1️⃣ Intellecta CLI
- AI-powered command line tool
- DevOps automation
- MIT License

#### 2️⃣ Intellecta Framework
- Core AI development platform
- RAG engine & multi-agent system
- Apache 2.0 License

#### 3️⃣ Intellecta WhatsApp Bot
- Messaging AI integration
- Customer support automation
- GPL-3.0 License

---

### 🚀 Bu İçeriğe Nasıl Erişirim?

**Unlimited access** ile bu projelerin:
- ✅ Detaylı açıklamalarını
- ✅ Teknik stack bilgilerini
- ✅ Kullanım senaryolarını
- ✅ Code snippets ve best practices

görebilirsiniz!

**Erişim için:**
1. **'⬆️ Request Unlimited Access'** sekmesine gidin
2. Email ve iletişim nedeninizi paylaşın
3. Onaylandıktan sonra **tüm içeriklere erişin**

---

💡 **Chat sekmesinden 5 ücretsiz soru sorabilirsiniz!**
                    """)
            
            llmops_content = gr.Markdown()
            
            # Note: State.change() not available in Gradio 4.16.0
            # Content rendering handled by demo.load() and login events
            
            demo.load(
                lambda: render_llmops_section(None),
                outputs=[llmops_content]
            )
        
        # Agentic Projects Section (Tab 6) - LOCKED for visitors
        with gr.Tab("🏗️ Agentic Projects", id=6):
            def render_agentic_section(username):
                user_manager = UserManager()
                user_data = user_manager.get_user_data(username) if username else None
                tier = user_data.get("tier", "visitor") if user_data else "visitor"
                
                if tier == "unlimited":
                    # Full access
                    return gr.Markdown("""
# 🏗️ Agentic AI & Infrastructure Projects

## Enterprise-Grade Automation Systems

### 1️⃣ SDLC Agentic RAG - AI-Powered Development Lifecycle

**Software geliştirme süreçlerini AI ile optimize edin**

#### 🎯 Problem
- Manuel code review süreçleri
- Documentation güncellemeleri
- Sprint planning karmaşıklığı
- Technical debt takibi

#### 💡 Çözüm
RAG-based multi-agent system ile SDLC otomasyonu

#### 🚀 Özellikler
- **Requirements Analysis Agent** - User story'leri analiz eder
- **Code Review Agent** - Otomatik code quality checks
- **Documentation Agent** - Auto-generated docs
- **Planning Agent** - Sprint planning assistance

#### 🔧 Teknoloji Stack
- Python + LangChain/LlamaIndex
- Vector database (Pinecone/Weaviate)
- GitHub API integration
- Jira/Linear automation

---

### 2️⃣ Kubeflow Agent - MLOps Orchestration AI

**ML pipeline'larınızı akıllı yönetin**

#### 🎯 Challenge
- Complex ML pipeline management
- Resource optimization
- Experiment tracking
- Model deployment automation

#### 💡 Solution
AI-powered Kubeflow orchestration

#### 🚀 Capabilities
- **Pipeline Optimizer** - Resource allocation
- **Experiment Tracker** - A/B testing automation
- **Deployment Agent** - Auto-deployment strategies
- **Monitor Agent** - Performance tracking

#### ☸️ Infrastructure
- Kubernetes-native
- Scalable & fault-tolerant
- Cloud-agnostic
- Production-ready

#### 📊 Benefits
- 60% faster deployment cycles
- 40% resource cost reduction
- Automated rollback strategies
- Real-time performance insights

---

### 3️⃣ CI/CD Agentic Flow - DevOps Automation Agent

**Pipeline'larınıza AI zekası ekleyin**

#### 🎯 Vision
Continuous Intelligence for Continuous Integration/Deployment

#### 🤖 Agent Ecosystem

**Build Agent**
- Intelligent build optimization
- Dependency caching strategies
- Parallel execution decisions

**Test Agent**
- Smart test selection
- Flaky test detection
- Coverage optimization

**Deploy Agent**
- Deployment strategy selection (blue-green, canary, rolling)
- Automated rollback decisions
- Environment health checks

**Monitor Agent**
- Post-deployment validation
- Performance regression detection
- Alert prioritization

#### 🔧 Technology
- GitHub Actions / GitLab CI integration
- Python orchestration layer
- Machine learning for decision-making

#### 📊 Impact Metrics
- **Deployment Frequency:** 5x increase
- **Lead Time:** 70% reduction
- **Change Failure Rate:** 60% decrease
- **MTTR:** 80% faster recovery

---

### 4️⃣ VSCode AWS Spot Terraform - Cloud Development Environment

**Maliyet-etkin cloud development**

#### 💰 Cost Optimization
AWS Spot Instances ile %70'e varan tasarruf

#### 🚀 Features
- Automated VS Code setup on cloud
- Terraform infrastructure-as-code
- Spot instance lifecycle management
- Auto-save & snapshot mechanisms

#### 🏗️ Architecture
```
Terraform → AWS Spot Instance → VS Code Server → Remote Development
```

#### 💻 Developer Experience
- Full VS Code features in cloud
- High-performance remote machines
- Persistent workspace state
- Team collaboration support

---

### 5️⃣ Web Orchestrator - Browser Automation Platform

**Web workflow'larını orkestre edin**

#### 🎯 Use Cases
- Multi-site data collection
- E2E testing automation
- Web scraping pipelines
- Form automation

#### 🤖 Agent Approach
TypeScript-based intelligent orchestration

---

### 6️⃣ WorkplaceSpace - Workspace Management System

**Development environment'larını standardize edin**

#### 💡 Problem Solved
- Environment setup complexity
- Team onboarding time
- Configuration drift

#### 🚀 Solution
Automated workspace provisioning and management

---

## 🏆 Impact Summary

| Project | Primary Benefit | Tech Stack |
|---------|----------------|------------|
| SDLC Agentic RAG | Development velocity ↑ | Python, LangChain |
| Kubeflow Agent | ML deployment speed ↑ | K8s, Kubeflow |
| CI/CD Agentic Flow | Deployment reliability ↑ | Python, GH Actions |
| VSCode AWS Spot | Development cost ↓ | Terraform, AWS |
| Web Orchestrator | Automation efficiency ↑ | TypeScript |
| WorkplaceSpace | Onboarding time ↓ | Python |

---

*All projects follow production-grade development practices with comprehensive testing and documentation.*
                    """)
                else:
                    # Locked preview
                    return gr.Markdown("""
# 🏗️ Agentic Projects

## 🔒 Premium İçerik - Onaylı Kullanıcılar İçin

Bu bölümde **6 enterprise-grade agentic AI projesi** bulunmaktadır.

### 🎯 Proje Listesi:

#### 1️⃣ SDLC Agentic RAG
Software Development Lifecycle AI - Development süreçlerini otomatize eder

#### 2️⃣ Kubeflow Agent
MLOps Orchestration - ML pipeline'larını akıllı yönetir

#### 3️⃣ CI/CD Agentic Flow
DevOps Automation - Pipeline'lara AI zekası ekler

#### 4️⃣ VSCode AWS Spot Terraform
Cloud Development Environment - Maliyet-etkin remote development

#### 5️⃣ Web Orchestrator
Browser Automation - Web workflow otomasyonu

#### 6️⃣ WorkplaceSpace
Workspace Management - Development environment standardization

---

### 🚀 Unlimited Access ile Neler Öğrenirsiniz?

Her proje için:
- ✅ **Detaylı teknik açıklamalar**
- ✅ **Architecture diagrams**
- ✅ **Technology stack bilgileri**
- ✅ **Real-world use cases**
- ✅ **Performance metrics**
- ✅ **Implementation patterns**

---

### 🔓 Erişim İçin:

1. **'⬆️ Request Unlimited Access'** sekmesine gidin
2. Email adresinizi ve iletişim nedeninizi paylaşın
3. Onay aldıktan sonra **tüm projelere tam erişim**

---

💡 **Chat sekmesinden benimle konuşup 5 ücretsiz soru sorabilirsiniz!**
                    """)
            
            agentic_content = gr.Markdown()
            
            # Note: State.change() not available in Gradio 4.16.0
            # Content rendering handled by demo.load() and login events
            
            demo.load(
                lambda: render_agentic_section(None),
                outputs=[agentic_content]
            )
        
        # Footer - Copyright and legal
        gr.Markdown("""
        ---
        <div style="text-align: center; padding: 20px; color: #666; font-size: 12px;">
            <p style="margin: 5px 0;">
                <strong>© 2024-2025 Intellecta Solutions | Gönenç Aydın</strong>
            </p>
            <p style="margin: 5px 0;">
                ⚖️ <strong>Patent Pending Technology</strong> - All intellectual property rights reserved.
            </p>
            <p style="margin: 5px 0;">
                🔒 This AI-powered career assistant system is proprietary technology developed by Intellecta Solutions.
            </p>
            <p style="margin: 5px 0; font-size: 11px; opacity: 0.7;">
                Unauthorized copying, modification, distribution, or commercial use of this software or its components 
                is strictly prohibited and may result in legal action.
            </p>
            <p style="margin: 10px 0 5px 0;">
                📧 For licensing inquiries: <a href="mailto:contact@intellectasolutions.com">contact@intellectasolutions.com</a>
            </p>
        </div>
        """)
    
    # Launch with security settings
    demo.launch(
        server_name="0.0.0.0", 
        server_port=7860, 
        share=False,
        show_api=False,  # Hide API documentation
        show_error=False,  # Don't show detailed errors to users
        auth=None,  # No HTTP basic auth (we have custom auth)
        favicon_path="IntellectaLinkedIn.png",  # Intellecta logo as favicon
        ssl_verify=False  # For local development
    )
