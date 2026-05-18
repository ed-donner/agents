import sqlite3
import json
import os
import numpy as np
from openai import OpenAI
from dotenv import load_dotenv
import gradio as gr
from pypdf import PdfReader

load_dotenv()
client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url=os.getenv("OPEN_ROUTER")
)

current_dir = os.path.dirname(os.path.abspath(__file__))
try:
    # remove existing database for demo purposes; in production, you might want to keep this data
    os.remove(os.path.join(current_dir, "data.db"))
except Exception as e:
    print(f"Error clearing previous data: {e}")

conn = sqlite3.connect(os.path.join(current_dir, "data.db"), check_same_thread=False)
cursor = conn.cursor()
cursor.execute("""
CREATE TABLE IF NOT EXISTS documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    content TEXT,
    embedding TEXT
)
""")
conn.commit()

# -----------------------
# EMBEDDING
# -----------------------
def get_embedding(text: str):
    res = client.embeddings.create(
        model="text-embedding-3-large",
        input=text
    )
    return res.data[0].embedding

# -----------------------
# SIMILARITY
# -----------------------
def cosine_similarity(a, b):
    a = np.array(a)
    b = np.array(b)
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))


def chunk_text(text, size=500):
    return [text[i:i+size] for i in range(0, len(text), size)]

# -----------------------
# LOAD RESUME
# -----------------------
def load_resume(file):
    if hasattr(file, "name"):
        if file.name.endswith(".pdf"):
            reader = PdfReader(file.name)
            text = "\n".join([page.extract_text() or "" for page in reader.pages])
        else:
            with open(file.name, "r", encoding="utf-8") as f:
                text = f.read()
    else:
        text = str(file)

    chunks = chunk_text(text)
    for chunk in chunks:
        embedding = get_embedding(chunk)
        cursor.execute(
            "INSERT INTO documents (content, embedding) VALUES (?, ?)",
            (chunk, json.dumps(embedding))
        )
    conn.commit()
    return f"✅ Stored {len(chunks)} chunks from resume."


def ask(question):
    query_embedding = get_embedding(question)
    cursor.execute("SELECT content, embedding FROM documents")
    rows = cursor.fetchall()

    scored = []
    for content, emb in rows:
        emb = json.loads(emb)
        score = cosine_similarity(query_embedding, emb)
        scored.append((content, score))

    top_chunks = sorted(scored, key=lambda x: x[1], reverse=True)[:5]
    context = "\n\n".join([c for c, _ in top_chunks])

    prompt = f"""
You are an AI assistant representing a professional.

Answer ONLY from the context below.

Context:
{context}

Question:
{question}
"""
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
    )
    return response.choices[0].message.content


def chatbot_reply(user_message, chat_history):
    answer = ask(user_message)
    chat_history = chat_history or []
    chat_history.append((user_message, answer))
    return chat_history, ""


with gr.Blocks() as demo:
    gr.Markdown("## Resume Q&A Chat Assistant")

    with gr.Tab("Load Resume"):
        resume_file = gr.File(label="Upload Resume (.txt or .pdf)")
        load_btn = gr.Button("Load Resume")
        load_output = gr.Textbox(label="Status")
        load_btn.click(load_resume, inputs=resume_file, outputs=load_output)

    with gr.Tab("Chat Me"):
        chatbot_ui = gr.Chatbot()
        user_input = gr.Textbox(placeholder="Ask a question...")
        send_btn = gr.Button("Send")
        send_btn.click(chatbot_reply, inputs=[user_input, chatbot_ui], outputs=[chatbot_ui, user_input])
        user_input.submit(chatbot_reply, inputs=[user_input, chatbot_ui], outputs=[chatbot_ui, user_input])

demo.launch(inbrowser=False)