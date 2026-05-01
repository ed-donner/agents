
"""
Key Improvements:

RAG-Ready Integration: Decouples deep biographical data from the system prompt using a 
query_knowledge_base tool. This optimizes the context window and reduces token costs 
while maintaining access to extensive professional history.

Lead Capture & CRM Hook: Includes specialized function calling to identify and extract user 
intent, capturing names and emails for professional follow-up.

Technical Stack
LLM: OpenAI gpt-4o-mini

Interface: Gradio (ChatInterface)

Database: SQLite3

Orchestration: Manual Agentic Loop (no heavy frameworks like LangChain, ensuring low latency and high transparency).
"""

import os
import json
import sqlite3
import requests
from dotenv import load_dotenv
from openai import OpenAI
import gradio as gr

load_dotenv(override=True)

# --- DATABASE SETUP ---
DB_PATH = "bio_memory.db"

def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS qa_log 
                          (id INTEGER PRIMARY KEY, question TEXT, answer TEXT, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
        conn.commit()

init_db()

# --- TOOL LOGIC ---

def query_knowledge_base(query):
    """Simulated RAG: In production, swap this for a Vector DB lookup (Chroma/Pinecone)."""
    return f"Deep Context for '{query}': Nsikan is an AI Engineer with 8+ years experience, specialized in Full Stack and Backend Heavy Development. I have 8+ years of experience facilitating cutting-edge engineering solutions with a wide range of e-commerce applications and technology skills. Proven ability to leverage full-stack knowledge and experience to build interactive and user-centered web services to scale and knowledge of building high-performance mission-critical services. My stacks are Ruby, C++, Rust, Python, NodeJs/JavaScript. I have experience in all aspects of software development. I graduated with a CGPA of 4.43/5.00 from the Federal University of Technonology Minna, Nigeria."




def record_user_details(email, name="Not provided"):
    # Integrated with a simple print/log - in prod, send to your CRM/Webhook
    print(f"DEBUG: Lead Captured -> {name} ({email})")
    return {"status": "success", "message": "Lead recorded successfully."}

def sql_mem_search(topic):
    """Queries the local SQL DB for previously handled similar topics."""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            # Simple LIKE search; in prod, consider FTS5 for better text searching
            cursor.execute("SELECT question, answer FROM qa_log WHERE question LIKE ? OR answer LIKE ? LIMIT 2", 
                           (f'%{topic}%', f'%{topic}%'))
            rows = cursor.fetchall()
            
            if rows:
                results = [{"q": r[0], "a": r[1]} for r in rows]
                return {"found_similar": True, "data": results}
            return {"found_similar": False, "message": "No matching previous conversations."}
    except Exception as e:
        return {"error": str(e)}

# --- TOOL DEFINITIONS ---
tools = [
    {
        "type": "function",
        "function": {
            "name": "query_knowledge_base",
            "description": "Get detailed factual info about Nsikan's technical background and experience.",
            "parameters": {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "sql_mem_search",
            "description": "Search the history of questions and answers to see how similar topics were handled.",
            "parameters": {"type": "object", "properties": {"topic": {"type": "string"}}, "required": ["topic"]}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "record_user_details",
            "description": "Record contact info when a user expresses interest in hiring or connecting.",
            "parameters": {
                "type": "object", 
                "properties": {"email": {"type": "string"}, "name": {"type": "string"}},
                "required": ["email"]
            }
        }
    }
]

class NsikanAgent:
    def __init__(self):
        self.client = OpenAI()
        self.name = "Nsikan Ikpoh"
        self.bio_data = "Nsikan is a learning AI Engineering, agentic workflows and productionizing LLMs. "
        with open("bio.txt", "r", encoding="utf-8") as f:
            self.bio_data += f.read()

    def evaluator(self, query, draft_response):
        """The Evaluator Pattern: Ensures high-quality, persona-aligned output."""
        eval_prompt = (
            f"You are a Quality Evaluator for {self.name}. Review the following draft response: '{draft_response}'. "
            f"Ensure it accurately answers: '{query}' while sounding professional, helpful, and concise. "
            "If the draft is good, return it. If not, rewrite it as Nsikan."
        )
        res = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "system", "content": eval_prompt}]
        )
        return res.choices[0].message.content

    def chat(self, message, history):
        system_msg = {
            "role": "system", 
            "content": f"You are {self.name}. {self.bio_data} Use your tools to check past conversations (sql_mem_search) "
                       "or deep bio info (query_knowledge_base) before answering new technical questions."
        }
        
        # Build the message chain
        current_messages = [system_msg] + history + [{"role": "user", "content": message}]
        
        # 1. GENERATION / TOOL LOOP
        while True:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=current_messages,
                tools=tools,
                tool_choice="auto"
            )
            
            response_message = response.choices[0].message
            current_messages.append(response_message)
            
            if not response_message.tool_calls:
                break
                
            for tool_call in response_message.tool_calls:
                func_name = tool_call.function.name
                args = json.loads(tool_call.function.arguments)
                
                # Dynamic function mapping
                if func_name == "query_knowledge_base":
                    result = query_knowledge_base(**args)
                elif func_name == "sql_mem_search":
                    result = sql_mem_search(**args)
                elif func_name == "record_user_details":
                    result = record_user_details(**args)
                else:
                    result = {"error": "Tool not found"}

                current_messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "name": func_name,
                    "content": json.dumps(result)
                })

        # 2. EVALUATION
        final_draft = current_messages[-1].content
        polished_answer = self.evaluator(message, final_draft)
        
        # 3. PERSISTENCE
        with sqlite3.connect(DB_PATH) as conn:
            conn.execute("INSERT INTO qa_log (question, answer) VALUES (?, ?)", (message, polished_answer))
            conn.commit()

        return polished_answer

if __name__ == "__main__":
    agent = NsikanAgent()
    # Using 'messages' format for Gradio 5.0+ compatibility
    gr.ChatInterface(agent.chat, type="messages").launch()