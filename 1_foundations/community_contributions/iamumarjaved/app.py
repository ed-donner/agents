import sys
import json
from openai import OpenAI
import gradio as gr
from typing import Dict, List
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from helpers import load_all_documents, PushoverNotifier, get_config
from rag_system import RAGSystem
from evaluation import RAGEvaluator


class DigitalTwin:
    
    def __init__(self):
        self.config = get_config()
        self.openai = OpenAI(api_key=self.config["openai_api_key"])
        self.name = self.config["name"]
        
        self.notifier = PushoverNotifier(self.config["pushover_user"], self.config["pushover_token"])
        
        self.email_collected = False
        self.user_email = None
        self.user_name = None
        
        print("Loading knowledge base...")
        app_dir = Path(__file__).parent
        self.documents = load_all_documents(str(app_dir / "me"))
        
        if not self.documents:
            raise ValueError("No documents loaded! Please add content to the me/ directory.")
        
        if self.config["rag_enabled"]:
            print("Initializing RAG system...")
            data_dir = str(app_dir / "data")
            self.rag_system = RAGSystem(self.openai, data_dir=data_dir)
            self.rag_system.load_knowledge_base(
                self.documents,
                chunk_size=self.config["chunk_size"],
                overlap=self.config["chunk_overlap"]
            )
            print("RAG system ready!")
        else:
            self.rag_system = None
        
        self.evaluator = RAGEvaluator(self.openai)
        
        self.tools = [
            {
                "type": "function",
                "function": {
                    "name": "record_user_details",
                    "description": "Record user contact information. IMPORTANT: You must ask for their name if they haven't provided it yet. Only call this tool after you have collected both email and name.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "email": {"type": "string", "description": "The email address of this user"},
                            "name": {"type": "string", "description": "The user's full name"},
                            "notes": {"type": "string", "description": "A brief 1-line summary of what the user was asking about or interested in"}
                        },
                        "required": ["email", "name", "notes"],
                        "additionalProperties": False
                    }
                }
            },
            {
                "type": "function",
                "function": {
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
            },
            {
                "type": "function",
                "function": {
                    "name": "search_knowledge_base",
                    "description": "Search the knowledge base for specific information",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {"type": "string", "description": "The search query"},
                            "focus_area": {"type": "string", "description": "Optional: specific area to focus on"}
                        },
                        "required": ["query"],
                        "additionalProperties": False
                    }
                }
            }
        ]
    
    def record_user_details(self, email: str, name: str, notes: str) -> Dict:
        self.email_collected = True
        self.user_email = email
        self.user_name = name
        self.notifier.send(f"New Contact: {name} <{email}>\nInterest: {notes}")
        return {"recorded": "ok", "message": f"Perfect! Thanks {name}. I'll be in touch soon."}
    
    def record_unknown_question(self, question: str) -> Dict:
        self.notifier.send(f"Unanswered: {question}")
        return {"recorded": "ok", "message": "I'll make a note of that question."}
    
    def search_knowledge_base(self, query: str, focus_area: str = None) -> Dict:
        if not self.rag_system:
            return {"success": False, "message": "RAG system not available"}
        
        enhanced_query = f"{focus_area}: {query}" if focus_area else query
        
        context = self.rag_system.retriever.retrieve(
            enhanced_query,
            method=self.config["rag_method"],
            top_k=self.config["top_k"],
            expand_query=self.config["query_expansion"],
            query_expander=self.rag_system.query_expander if self.config["query_expansion"] else None
        )
        
        results = [{"source": doc["source"], "text": doc["text"][:300] + "...", "score": doc["retrieval_score"]} for doc in context]
        return {"success": True, "results": results, "message": f"Found {len(results)} relevant pieces"}
    
    def handle_tool_calls(self, tool_calls) -> List[Dict]:
        results = []
        for tool_call in tool_calls:
            tool_name = tool_call.function.name
            arguments = json.loads(tool_call.function.arguments)
            print(f"[TOOL] Tool called: {tool_name}", flush=True)
            
            tool_func = getattr(self, tool_name, None)
            result = tool_func(**arguments) if tool_func else {"error": f"Unknown tool: {tool_name}"}
            
            results.append({
                "role": "tool",
                "content": json.dumps(result),
                "tool_call_id": tool_call.id
            })
        return results
    
    def get_system_prompt(self, rag_context: List[Dict] = None) -> str:
        prompt = f"""You are acting as {self.name}. You are answering questions on {self.name}'s website, particularly questions related to {self.name}'s career, background, skills and experience.

Your responsibility is to represent {self.name} for interactions on the website as faithfully as possible.
Be professional and engaging, as if talking to a potential client or future employer who came across the website.
"""
        
        if rag_context:
            prompt += "\n## Retrieved Information:\n"
            for doc in rag_context:
                prompt += f"\n[{doc['source']}]:\n{doc['text']}\n"
        else:
            all_context = "\n\n".join([f"## {k.title()}:\n{v}" for k, v in self.documents.items()])
            prompt += f"\n{all_context}\n"
        
        prompt += f"""
## Important Instructions:
- If you don't know the answer to any question, use your record_unknown_question tool
- If you need more specific information, use your search_knowledge_base tool
"""
        
        if not self.email_collected:
            prompt += """- If the user is engaging positively, naturally steer towards getting in touch
- Ask for BOTH their name and email address (ask for name first if they only provide email)
- When using record_user_details tool, include a 1-line summary of what they were interested in
- Only call the tool after you have collected both name and email
"""
        else:
            prompt += f"""- You have already collected contact from {self.user_name or 'this user'} ({self.user_email})
- Continue naturally without repeatedly asking for contact details
"""
        
        prompt += f"\n\nWith this context, please chat with the user, always staying in character as {self.name}."
        return prompt
    
    def chat(self, message: str, history: List) -> str:
        converted_history = []
        for h in history:
            if isinstance(h, (list, tuple)) and len(h) == 2:
                user_msg, bot_msg = h
                if user_msg:
                    converted_history.append({"role": "user", "content": user_msg})
                if bot_msg:
                    converted_history.append({"role": "assistant", "content": bot_msg})
            elif isinstance(h, dict):
                converted_history.append({k: v for k, v in h.items() if k in ["role", "content"]})
        history = converted_history
        
        use_rag = self.config["rag_enabled"] and self.rag_system
        rag_context = None
        
        if use_rag:
            query_check = self.openai.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": f"Is this query asking for specific information about someone's background, experience, or skills? Answer only 'yes' or 'no'.\n\nQuery: {message}"}],
                temperature=0
            )
            should_retrieve = query_check.choices[0].message.content.strip().lower() == "yes"
            
            if should_retrieve:
                print("[RAG] Using RAG for this query")
                rag_context = self.rag_system.retriever.retrieve(
                    message,
                    method=self.config["rag_method"],
                    top_k=self.config["top_k"],
                    expand_query=self.config["query_expansion"],
                    query_expander=self.rag_system.query_expander if self.config["query_expansion"] else None
                )
        
        system_prompt = self.get_system_prompt(rag_context)
        messages = [{"role": "system", "content": system_prompt}] + history + [{"role": "user", "content": message}]
        
        done = False
        max_iterations = 5
        iteration = 0
        
        while not done and iteration < max_iterations:
            iteration += 1
            response = self.openai.chat.completions.create(model="gpt-4o-mini", messages=messages, tools=self.tools, temperature=0.7)
            finish_reason = response.choices[0].finish_reason
            
            if finish_reason == "tool_calls":
                message_obj = response.choices[0].message
                tool_calls = message_obj.tool_calls
                results = self.handle_tool_calls(tool_calls)
                messages.append(message_obj)
                messages.extend(results)
            else:
                done = True
                return response.choices[0].message.content
        
        return response.choices[0].message.content


print("Initializing Digital Twin...")
twin = DigitalTwin()
print("Digital Twin ready!")


def chat_wrapper(message, history):
    return twin.chat(message, history)


with gr.Blocks(theme=gr.themes.Soft(primary_hue="blue", secondary_hue="slate"), css="#chatbot {height: 600px;} .contain {max-width: 900px; margin: auto;}") as demo:
    gr.Markdown(f"""# Chat with {twin.name}

Welcome! I'm an AI assistant representing {twin.name}. Ask me anything about background, experience, skills, or interests.

Features: Advanced RAG - Context-aware - Smart contact collection - Real-time notifications""")
    
    chatbot = gr.ChatInterface(
        chat_wrapper,
        chatbot=gr.Chatbot(elem_id="chatbot"),
        textbox=gr.Textbox(placeholder=f"Ask me about {twin.name}'s experience, skills, or background...", container=False, scale=7),
        title=None,
        description=None
    )
    
    gr.Markdown(f"""---
Powered by Advanced RAG - OpenAI GPT-4 - Hybrid Search and Reranking

RAG Configuration: {twin.config['rag_method'].upper()} - Top {twin.config['top_k']} docs - Query expansion: {'ON' if twin.config['query_expansion'] else 'OFF'}""")


if __name__ == "__main__":
    demo.launch(share=False, server_name="0.0.0.0", server_port=7867)
