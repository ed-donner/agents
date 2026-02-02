from dotenv import load_dotenv
from openai import OpenAI
import json
import os
import requests
from pypdf import PdfReader
import gradio as gr
import sqlite3
from datetime import datetime
import numpy as np
import secrets
import hashlib

load_dotenv(override=True)

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
            SELECT username, tier, query_count, query_limit, status
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
                "status": result[4]
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
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
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
        
        return True
    
    def approve_upgrade(self, username):
        """Approve user upgrade to unlimited tier"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Update user to unlimited
        cursor.execute('''
            UPDATE users
            SET tier = 'unlimited', query_limit = -1, status = 'approved', approved_at = ?
            WHERE username = ?
        ''', (datetime.now(), username))
        
        # Update request status
        cursor.execute('''
            UPDATE upgrade_requests
            SET status = 'approved', processed_at = ?
            WHERE username = ? AND status = 'pending'
        ''', (datetime.now(), username))
        
        conn.commit()
        conn.close()
        
        return True

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
                email TEXT UNIQUE,
                name TEXT,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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
        
        if os.path.exists("me/knowledge"):
            for filename in os.listdir("me/knowledge"):
                if filename.endswith(".txt"):
                    try:
                        with open(f"me/knowledge/{filename}", "r", encoding="utf-8") as f:
                            content = f.read()
                            if content and len(content) > 50:
                                self.kb.add_document(content, {"source": filename, "type": "additional"})
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
        
        system_prompt = f"""You are acting as {self.name}. You are answering questions on {self.name}'s website, 
particularly questions related to {self.name}'s career, background, skills and experience. 
Your responsibility is to represent {self.name} for interactions on the website as faithfully as possible.

You have access to:
1. A summary of {self.name}'s background
2. {self.name}'s LinkedIn profile
3. A searchable knowledge base with additional context
4. Tools to record user information and unknown questions

Be professional and engaging, as if talking to a potential client or future employer.

**Important Instructions:**
- Try to search the knowledge base for relevant information before answering
- If you don't know the answer, use record_unknown_question tool
- If the user shows interest in connecting, politely ask for their email and use record_user_details tool
- Use the context provided below to enhance your answers
- If a visitor user asks for unlimited access, guide them to provide their email and intent

## Summary:
{self.summary}

## LinkedIn Profile:
{self.linkedin[:1000]}...

## Additional Context (RAG):
{rag_context}

{tier_message}

With this context, please chat with the user, always staying in character as {self.name}."""
        
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
    user_data = user_manager.authenticate(username, password)
    
    if user_data:
        if user_data["status"] == "approved":
            welcome_msg = f"""✅ **Welcome back, {username}!**

You have **unlimited access** to the chatbot. Feel free to ask anything!"""
            return True, welcome_msg, user_data["username"]
        elif user_data["tier"] == "visitor":
            remaining = user_data["query_limit"] - user_data["query_count"]
            welcome_msg = f"""✅ **Welcome, {username}!**

You have **{remaining} queries remaining** as a visitor.

**Quick Start:**
- Ask about my experience and skills
- Learn about my projects
- Discuss potential collaborations

After {remaining} queries, you can request unlimited access!"""
            return True, welcome_msg, user_data["username"]
        else:
            return True, f"✅ Logged in! Status: {user_data['status']}", user_data["username"]
    
    return False, "❌ Invalid credentials. Please try again or create a visitor account.", None

def request_unlimited_access(username, email, intent):
    """Request upgrade to unlimited access"""
    user_manager = UserManager()
    
    if not email or "@" not in email:
        return "❌ Please provide a valid email address."
    
    if not intent or len(intent) < 10:
        return "❌ Please provide a detailed intent (minimum 10 characters)."
    
    success = user_manager.request_upgrade(username, email, intent)
    
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
    
    with gr.Blocks(theme=gr.themes.Soft(), title=f"Chat with {me.name}") as demo:
        # State management
        current_username = gr.State(value=None)
        
        # Header
        gr.Markdown(f"""
        # 💼 Chat with {me.name}
        ### AI-Powered Career Assistant
        
        Welcome! I'm an AI assistant representing {me.name}. Ask me about background, skills, experience, and projects.
        """)
        
        # Chat Section (First Tab - Default)
        with gr.Tab("💬 Chat"):
            # Login status display with bot greeting
            welcome_text = f"""### 👋 Hello! Welcome to my AI Assistant

I'm here to help you learn about **{me.name}'s** professional experience, skills, and projects!

**To get started:**

Please visit the **'🔐 Login / Sign Up'** tab to create your free visitor account.

You'll get **5 free questions** to learn all about me! 🎉

Looking forward to our conversation! 😊"""
            
            login_status_display = gr.Markdown(welcome_text, visible=True)
            
            # Limit reached message
            limit_reached_display = gr.Markdown(visible=False)
            
            # Welcome message (shown after login)
            welcome_message = gr.Markdown(visible=False)
            
            gr.Markdown(f"### Ask me anything about {me.name}!")
            
            # Quick action cards
            with gr.Row(visible=False) as quick_actions:
                with gr.Column(scale=1):
                    gr.Markdown("**🚀 Quick Start**")
                    quick_btn1 = gr.Button("📊 Tell me about your experience", size="sm")
                    quick_btn2 = gr.Button("🛠️ What are your main skills?", size="sm")
                    quick_btn3 = gr.Button("💼 Show me your projects", size="sm")
                    quick_btn4 = gr.Button("🤝 How can we collaborate?", size="sm")
            
            chatbot = gr.Chatbot(type="messages", height=400)
            msg = gr.Textbox(
                label="Your message", 
                placeholder="Please visit the Login / Sign Up tab to get started...",
                interactive=False
            )
            
            with gr.Row():
                send_btn = gr.Button("Send", variant="primary", interactive=False)
                clear_btn = gr.Button("Clear")
            
            # Query counter display
            query_status = gr.Markdown()
        
        # Login / Sign Up Section (Second Tab)
        with gr.Tab("🔐 Login / Sign Up"):
        """)
        
        # Chat Section (First Tab - Default)
        with gr.Tab("� Chat"):
            # Login status display with bot greeting
            login_status_display = gr.Markdown("""
### 👋 Hello! Welcome to my AI Assistant

I'm here to help you learn about {name}'s professional experience, skills, and projects!

**To get started:**

Please visit the **'�🔐 Login / Sign Up'** tab to create your free visitor account.

You'll get **5 free questions** to learn all about me! 🎉

Looking forward to our conversation! 😊
            """.format(name=me.name), visible=True)
            gr.Markdown("### Choose your access level:")
            
            with gr.Row():
                with gr.Column():
                    gr.Markdown("#### 🎫 Visitor Access (5 queries)")
                    visitor_btn = gr.Button("Get Visitor Credentials", variant="secondary")
                    visitor_output = gr.Markdown()
                
                with gr.Column():
                    gr.Markdown("#### 🔑 Approved User Login")
                    gr.Markdown("""
                    *Only for users who have been approved for unlimited access.*
                    
                    If you're a new visitor, use the button on the left.
                    """)
                    login_username = gr.Textbox(label="Username", placeholder="Enter your approved username")
                    login_password = gr.Textbox(label="Password", type="password", placeholder="Enter your password")
                    login_btn = gr.Button("Login", variant="primary")
                    login_output = gr.Markdown()
            
            
            def handle_login(username, password):
                success, message, user = login_user(username, password)
                if success:
                    return message, user, gr.update(), gr.update()
                return message, None, gr.update(), gr.update()
            
            def handle_visitor_creation(request: gr.Request):
                """Create visitor credentials with IP tracking and auto-login"""
                user_manager = UserManager()
                
                # Get client IP
                client_ip = None
                try:
                    if hasattr(request, 'client') and hasattr(request.client, 'host'):
                        client_ip = request.client.host
                except:
                    pass
                
                # Check IP limit
                if client_ip and user_manager.check_ip_visitor_limit(client_ip):
                    return f"""
⚠️ **Visitor account already created from this IP**

You've already created a visitor account in the last 24 hours from this IP address.

**What you can do:**
- Use your existing visitor credentials to login
- Wait 24 hours to create a new visitor account
- Request unlimited access if you've used your queries

If you lost your credentials, please contact support.
                    """, None
                
                username, password = user_manager.create_visitor_account(client_ip)
                
                credentials_text = f"""
# � Welcome! Your Visitor Credentials

**Username:** `{username}`  
**Password:** `{password}`  
**Query Limit:** 5 questions

⚠️ **Important:** Save these credentials! You'll need them to log back in.

---

✅ **You are now automatically logged in!**

**What you can do:**
✨ Ask about my background and experience
💼 Learn about my skills and projects  
🤝 Discuss collaboration opportunities
📧 Request unlimited access after your trial

**Next:** Go to the '💬 Chat' tab to start our conversation!
                """
                
                return credentials_text, username
            
            visitor_btn.click(
                handle_visitor_creation,
                outputs=[visitor_output, current_username]
            )
            
            login_btn.click(
                handle_login,
                inputs=[login_username, login_password],
                outputs=[login_output, current_username, login_username, login_password]
            )
        
        # Upgrade Request Section (Third Tab)
        with gr.Tab("⬆️ Request Unlimited Access"):
            
            def respond(message, history, username):
                if not username or username == "visitor":
                    return history, "❌ Please login first! Go to the '🔐 Login / Sign Up' tab.", ""
                
                # Check if user has reached limit BEFORE processing
                user_manager = UserManager()
                can_query, current, limit = user_manager.check_query_limit(username)
                
                if not can_query:
                    # Don't process the message, just show error
                    return history, f"🚫 **Limit reached!** Please go to '⬆️ Request Unlimited Access' tab.", ""
                
                # Add user message to history
                history.append({"role": "user", "content": message})
                
                # Get bot response
                bot_response = me.chat(message, history, username)
                
                # Add bot response to history
                history.append({"role": "assistant", "content": bot_response})
                
                # Update query status
                can_query_after, current_after, limit_after = user_manager.check_query_limit(username)
                
                if limit_after == -1:
                    status_msg = f"✅ **Unlimited access** | Queries used: {current_after}"
                else:
                    remaining = limit_after - current_after
                    if remaining <= 0:
                        status_msg = f"🚫 **Limit reached!** Go to '⬆️ Request Unlimited Access' tab to continue."
                    elif remaining <= 2:
                        status_msg = f"⚠️ **{remaining} queries remaining** | Consider requesting unlimited access"
                    else:
                        status_msg = f"📊 **Queries:** {current_after}/{limit_after} | Remaining: {remaining}"
                
                return history, status_msg, ""
            
            # Enable/disable chat based on user status
            def update_chat_interface(username):
                if username and username != "visitor":
                    user_manager = UserManager()
                    user_data = user_manager.get_user_data(username)
                    
                    if user_data:
                        tier = user_data["tier"]
                        current = user_data["query_count"]
                        limit = user_data["query_limit"]
                        remaining = limit - current
                        
                        # Check if limit reached
                        if tier == "visitor" and remaining <= 0:
                            # LIMIT REACHED - Disable everything
                            limit_msg = f"""### 🚫 Query Limit Reached

You've used all **{limit} free queries** as a visitor.

**To continue our conversation:**

👉 Go to the **'⬆️ Request Unlimited Access'** tab to:
- Provide your email address
- Share why you'd like to connect

I'll review your request and reach out to you soon! 📧"""
                            
                            return (
                                gr.update(visible=False),  # Hide login warning
                                gr.update(value=limit_msg, visible=True),  # Show limit message
                                gr.update(visible=False),  # Hide welcome
                                gr.update(visible=False),  # Hide quick actions
                                gr.update(interactive=False, placeholder="Please request unlimited access to continue..."),  # Disable input
                                gr.update(interactive=False),  # Disable send button
                                f"🚫 **Limit reached!** {current}/{limit} queries used",
                                []  # Clear chat
                            )
                        
                        # Create welcome message
                        if tier == "unlimited":
                            welcome = f"""### 👋 Welcome back!

You have **unlimited access**. Feel free to ask anything about my experience, skills, and projects!"""
                            status = "✅ **Unlimited access** | Ask away!"
                        else:
                            welcome = f"""### 👋 Hello! I'm {me.name}'s AI assistant

I can help you learn about:
- 📊 **Professional Experience** - Career journey and achievements
- 🛠️ **Technical Skills** - Programming, AI/ML, Cloud technologies
- 💼 **Projects** - Notable work and contributions
- 🤝 **Collaboration** - How we can work together

**You have {remaining} questions available.** Use the quick start buttons below or type your own question!"""
                            status = f"✅ **Welcome!** | {remaining} queries remaining"
                        
                        # Start conversation with bot greeting
                        initial_history = [{
                            "role": "assistant", 
                            "content": f"Hello! 👋 I'm an AI assistant representing {me.name}. I'm here to answer your questions about professional experience, skills, projects, and potential collaborations. What would you like to know?"
                        }]
                        
                        return (
                            gr.update(visible=False),  # Hide login warning
                            gr.update(visible=False),  # Hide limit message
                            gr.update(value=welcome, visible=True),  # Show welcome
                            gr.update(visible=True),  # Show quick actions
                            gr.update(interactive=True, placeholder="Ask me about my experience, skills, or projects..."),  # Enable input
                            gr.update(interactive=True),  # Enable send button
                            status,  # Show status
                            initial_history  # Initial greeting
                        )
                
                return (
                    gr.update(visible=True),  # Show login warning
                    gr.update(visible=False),  # Hide limit message
                    gr.update(visible=False),  # Hide welcome
                    gr.update(visible=False),  # Hide quick actions
                    gr.update(interactive=False, placeholder="Please login first to start chatting..."),
                    gr.update(interactive=False),
                    "⚠️ Please login to start chatting",
                    []  # Empty chat
                )
            
            # Quick action handlers
            def quick_action(question, history, username):
                return respond(question, history, username)
            
            quick_btn1.click(
                lambda h, u: quick_action("Tell me about your professional experience and background", h, u),
                inputs=[chatbot, current_username],
                outputs=[chatbot, query_status, msg]
            ).then(
                update_chat_interface,
                inputs=[current_username],
                outputs=[login_status_display, limit_reached_display, welcome_message, quick_actions, msg, send_btn, query_status, chatbot]
            )
            
            quick_btn2.click(
                lambda h, u: quick_action("What are your main technical skills and expertise?", h, u),
                inputs=[chatbot, current_username],
                outputs=[chatbot, query_status, msg]
            ).then(
                update_chat_interface,
                inputs=[current_username],
                outputs=[login_status_display, limit_reached_display, welcome_message, quick_actions, msg, send_btn, query_status, chatbot]
            )
            
            quick_btn3.click(
                lambda h, u: quick_action("Can you show me some of your notable projects?", h, u),
                inputs=[chatbot, current_username],
                outputs=[chatbot, query_status, msg]
            ).then(
                update_chat_interface,
                inputs=[current_username],
                outputs=[login_status_display, limit_reached_display, welcome_message, quick_actions, msg, send_btn, query_status, chatbot]
            )
            
            quick_btn4.click(
                lambda h, u: quick_action("I'm interested in collaboration opportunities. How can we work together?", h, u),
                inputs=[chatbot, current_username],
                outputs=[chatbot, query_status, msg]
            ).then(
                update_chat_interface,
                inputs=[current_username],
                outputs=[login_status_display, limit_reached_display, welcome_message, quick_actions, msg, send_btn, query_status, chatbot]
            )
            
            # Update chat interface when user logs in or after each query
            current_username.change(
                update_chat_interface,
                inputs=[current_username],
                outputs=[login_status_display, limit_reached_display, welcome_message, quick_actions, msg, send_btn, query_status, chatbot]
            )
            
            send_btn.click(
                respond,
                inputs=[msg, chatbot, current_username],
                outputs=[chatbot, query_status, msg]
            ).then(
                update_chat_interface,
                inputs=[current_username],
                outputs=[login_status_display, limit_reached_display, welcome_message, quick_actions, msg, send_btn, query_status, chatbot]
            )
            
            msg.submit(
                respond,
                inputs=[msg, chatbot, current_username],
                outputs=[chatbot, query_status, msg]
            ).then(
                update_chat_interface,
                inputs=[current_username],
                outputs=[login_status_display, limit_reached_display, welcome_message, quick_actions, msg, send_btn, query_status, chatbot]
            )
            
            clear_btn.click(lambda: ([], ""), outputs=[chatbot, query_status])
        
        # Upgrade Request Section
        with gr.Tab("⬆️ Request Unlimited Access"):
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
            
            # Update username display when user logs in
            current_username.change(
                lambda x: x or "",
                inputs=[current_username],
                outputs=[upgrade_username_display]
            )
            
            upgrade_btn.click(
                request_unlimited_access,
                inputs=[current_username, upgrade_email, upgrade_intent],
                outputs=[upgrade_output]
            )
        
        # About Section
        with gr.Tab("ℹ️ About"):
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
    
    # Launch
    demo.launch(server_name="0.0.0.0", server_port=7860, share=False)
