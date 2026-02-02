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

load_dotenv(override=True)

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
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
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
        
        # Split query into keywords
        keywords = query.lower().split()
        
        if not keywords:
            conn.close()
            return []
        
        # Build dynamic query
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
        
        # Update usage count
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
    
    def save_conversation(self, user_message, bot_response):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO conversations (user_message, bot_response)
            VALUES (?, ?)
        ''', (user_message, bot_response))
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
        # Generate embedding
        try:
            embedding = self.get_embedding(text)
            self.embeddings.append(embedding)
        except Exception as e:
            print(f"Error generating embedding: {e}")
            self.embeddings.append([0] * 1536)  # Fallback empty embedding
    
    def get_embedding(self, text):
        """Get embedding from OpenAI"""
        response = self.openai.embeddings.create(
            model="text-embedding-3-small",
            input=text[:8000]  # Limit text length
        )
        return response.data[0].embedding
    
    def search(self, query, top_k=2):
        """Search for relevant documents using cosine similarity"""
        if not self.documents or not self.embeddings:
            return []
        
        try:
            query_embedding = self.get_embedding(query)
            
            # Calculate similarities using numpy
            similarities = []
            for doc_embedding in self.embeddings:
                sim = cosine_similarity_numpy(query_embedding, doc_embedding)
                similarities.append(sim)
            
            # Get top k results
            top_indices = np.argsort(similarities)[-top_k:][::-1]
            
            results = []
            for idx in top_indices:
                if similarities[idx] > 0.5:  # Threshold
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
# MAIN CLASS
# ============================================
class Me:
    def __init__(self):
        self.openai = OpenAI()
        self.name = "Gönenç Aydın"
        self.db = Database()
        self.kb = KnowledgeBase(self.openai)
        
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
        
        # Initialize knowledge base with documents
        self.init_knowledge_base()
        
        # Pre-populate Q&A database
        self.populate_initial_qa()
    
    def init_knowledge_base(self):
        """Add documents to the knowledge base for RAG"""
        # Add LinkedIn profile
        if self.linkedin and len(self.linkedin) > 50:
            self.kb.add_document(self.linkedin, {"source": "linkedin", "type": "profile"})
        
        # Add summary
        if self.summary and len(self.summary) > 50:
            self.kb.add_document(self.summary, {"source": "summary", "type": "overview"})
        
        # Add any additional documents from a folder
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
    
    def system_prompt(self, rag_context=""):
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

## Summary:
{self.summary}

## LinkedIn Profile:
{self.linkedin[:1000]}...

## Additional Context (RAG):
{rag_context}

With this context, please chat with the user, always staying in character as {self.name}."""
        
        return system_prompt
    
    def chat(self, message, history):
        try:
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
                {"role": "system", "content": self.system_prompt(rag_context)}
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
            
            # Save conversation to database
            self.db.save_conversation(message, bot_response)
            
            return bot_response
        
        except Exception as e:
            print(f"Error in chat: {e}")
            return f"I apologize, but I encountered an error. Please try again. Error: {str(e)}"

# ============================================
# LAUNCH
# ============================================
if __name__ == "__main__":
    me = Me()
    
    demo = gr.ChatInterface(
        me.chat,
        type="messages",
        title=f"Chat with {me.name}",
        description="Ask me about my career, skills, and experience!",
        theme=gr.themes.Soft(),
    )
    
    # Parse authentication from environment variable
    auth_config = None
    gradio_auth = os.getenv("GRADIO_AUTH")
    if gradio_auth:
        try:
            # Parse "username:password" format
            if ":" in gradio_auth:
                username, password = gradio_auth.split(":", 1)
                auth_config = (username, password)
                print(f"Authentication enabled for user: {username}")
        except Exception as e:
            print(f"Error parsing GRADIO_AUTH: {e}")
    
    # Launch with or without auth - DISABLE SSR to fix auth issues
    if auth_config:
        demo.launch(
            server_name="0.0.0.0",
            server_port=7860,
            auth=auth_config,
            auth_message="Please enter your credentials to access the chat",
            ssr_mode=False  # ← FIX: Disable SSR when using auth
        )
    else:
        print("No authentication configured - launching publicly")
        demo.launch(server_name="0.0.0.0", server_port=7860)
