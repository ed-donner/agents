from dotenv import load_dotenv
from openai import OpenAI
import json
import os
import requests
from pypdf import PdfReader
import gradio as gr
# Added imports
import chromadb
from chromadb.utils import embedding_functions
import glob

load_dotenv(override=True)


def push(text):
    requests.post(
        "https://api.pushover.net/1/messages.json",
        data={
            "token": os.getenv("PUSHOVER_TOKEN"),
            "user": os.getenv("PUSHOVER_USER"),
            "message": text,
        }
    )


def record_user_details(email, name="Name not provided", notes="not provided"):
    push(f"Recording {name} with email {email} and notes {notes}")
    return {"recorded": "ok"}


def record_unknown_question(question):
    push(f"Recording {question}")
    return {"recorded": "ok"}


record_user_details_json = {
    "name": "record_user_details",
    "description": "Use this tool to record that a user is interested in being in touch and provided an email address",
    "parameters": {
        "type": "object",
        "properties": {
            "email": {
                "type": "string",
                "description": "The email address of this user"
            },
            "name": {
                "type": "string",
                "description": "The user's name, if they provided it"
            }
            ,
            "notes": {
                "type": "string",
                "description": "Any additional information about the conversation that's worth recording to give context"
            }
        },
        "required": ["email"],
        "additionalProperties": False
    }
}

record_unknown_question_json = {
    "name": "record_unknown_question",
    "description": "Always use this tool to record any question that couldn't be answered as you didn't know the answer",
    "parameters": {
        "type": "object",
        "properties": {
            "question": {
                "type": "string",
                "description": "The question that couldn't be answered"
            },
        },
        "required": ["question"],
        "additionalProperties": False
    }
}

tools = [{"type": "function", "function": record_user_details_json},
         {"type": "function", "function": record_unknown_question_json}]


def get_section(md_content, section_title):
    # Split by headers (assuming standard "# Header" format)
    sections = md_content.split('\n# ')
    for section in sections:
        if section.startswith(section_title) or section.startswith('# ' + section_title):
            return section
    return None

def simple_chunk_text(text, chunk_size=500, overlap=50):
    """Simple function to split text into overlapping chunks"""
    words = text.split()
    chunks = []

    for i in range(0, len(words), chunk_size - overlap):
        chunk = ' '.join(words[i:i + chunk_size])
        if chunk:
            chunks.append(chunk)

    return chunks


class Me:

    def __init__(self):
        self.openai = OpenAI()
        self.name = "Andres"

        # Initialize ChromaDB
        self.chroma_client = chromadb.PersistentClient(path="./chroma_db")
        self.embedding_function = embedding_functions.OpenAIEmbeddingFunction(
            api_key=os.getenv("OPENAI_API_KEY"),
            model_name="text-embedding-3-small"
        )

        # Create or get collection
        self.collection = self.chroma_client.get_or_create_collection(
            name="my_documents",
            embedding_function=self.embedding_function
        )

        # Load LinkedIn and summary
        reader = PdfReader("docs/linkedin_profile.pdf")
        self.linkedin = ""
        for page in reader.pages:
            text = page.extract_text()
            if text:
                self.linkedin += text

        # Get summary from CV in Markdown in GitHub portfolio, LinkedIn skills are outdated a few years!
        # I write my Resume with Latex to PDF, I know that gives parser problems, will try it only if I have time!
        with open("docs/private_generic.md", "r", encoding="utf-8") as f:
            content = f.read()
            print()
            self.summary = get_section(content, "Summary")
            #"My name is Andres. I'm a highly creative person who is interested in solving complex problems looking at them from a wide perspective. I feel comfortable"  # get_summary(docs/summary.txt)

 # Load documents into vector DB (only if collection is empty)
        if self.collection.count() == 0:
            self.load_documents()


    def load_documents(self):
        """Load all documents into vector database"""
        print("Loading documents into vector database...", flush=True)

        all_texts = []
        all_metadata = []
        all_ids = []

        # 1. Add summary as chunks
        summary_chunks = simple_chunk_text(self.summary, chunk_size=300, overlap=30)
        for i, chunk in enumerate(summary_chunks):
            all_texts.append(chunk)
            all_metadata.append({"source": "summary", "type": "overview"})
            all_ids.append(f"summary_{i}")

        # 2. Add LinkedIn as chunks
        linkedin_chunks = simple_chunk_text(self.linkedin, chunk_size=300, overlap=30)
        for i, chunk in enumerate(linkedin_chunks):
            all_texts.append(chunk)
            all_metadata.append({"source": "linkedin", "type": "profile"})
            all_ids.append(f"linkedin_{i}")

        # 3. Add all .md files from docs folder
        md_files = glob.glob("docs/*.md")
        for file_path in md_files:
            with open(file_path, "r", encoding="utf-8") as f:
                text = f.read()
            # Split into chunks
            chunks = simple_chunk_text(text, chunk_size=300, overlap=30)

            for i, chunk in enumerate(chunks):
                all_texts.append(chunk)
                all_metadata.append({
                    "source": os.path.basename(file_path),
                    "type": "document"
                })
                all_ids.append(f"{os.path.basename(file_path)}_{i}")

        # Add all documents at once (ChromaDB can handle it)
        if all_texts:
            self.collection.add(
                documents=all_texts,
                metadatas=all_metadata,
                ids=all_ids
            )
            print(f"Added {len(all_texts)} document chunks to vector DB", flush=True)

    def get_relevant_context(self, query, n_results=5):
        """Retrieve relevant context from vector DB"""
        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=n_results
            )

            context = ""
            if results['documents'] and results['documents'][0]:
                context = "\n\nRelevant context from my background:\n"
                for i, doc in enumerate(results['documents'][0]):
                    source = results['metadatas'][0][i].get('source', 'unknown')
                    context += f"\n--- From {source} ---\n{doc}\n"

            return context
        except Exception as e:
            print(f"Error retrieving context: {e}", flush=True)
            return ""

    @staticmethod
    def handle_tool_call(tool_calls):
        results = []
        for tool_call in tool_calls:
            tool_name = tool_call.function.name
            arguments = json.loads(tool_call.function.arguments)
            print(f"Tool called: {tool_name}", flush=True)
            tool = globals().get(tool_name)
            result = tool(**arguments) if tool else {}
            results.append({"role": "tool", "content": json.dumps(result), "tool_call_id": tool_call.id})
        return results

    def system_prompt(self, user_message):
        # Get relevant context for this specific user message
        additional_context = self.get_relevant_context(user_message)

        system_prompt = f"You are acting as {self.name}. You are answering questions on {self.name}'s website, \
                        particularly questions related to {self.name}'s career, background, skills and experience. \
                        Your responsibility is to represent {self.name} for interactions on the website as faithfully as possible. \
                        You are given a private generic information of {self.name}'s background and LinkedIn profile which you can use to answer questions. \
                        Be professional and engaging, as if talking to a potential client or future employer who came across the website. \
                        If you don't know the answer to any question, use your record_unknown_question tool to record the question that you couldn't answer,\
                        even if it's about something trivial or unrelated to career. If the user is engaging in discussion, try to steer them towards getting \
                        in touch via email; ask for their email and record it using your record_user_details tool. "

        # Keep existing content
        system_prompt += f"\n\n## Summary:\n{self.summary}\n\n## LinkedIn Profile:\n{self.linkedin}\n\n"

        # Add retrieved context
        system_prompt += additional_context

        system_prompt += f"\n\nWith all this context, please chat with the user, always staying in character as {self.name}."
        return system_prompt

    def chat(self, message, history):
        # Convert history from Gradio format to OpenAI format
        formatted_history = []
        for item in history:
            if isinstance(item, dict):
                # Newer Gradio versions use dict format
                formatted_history.append({"role": "user", "content": item["content"]})
                if "assistant" in item:
                    formatted_history.append({"role": "assistant", "content": item["assistant"]})
            elif isinstance(item, (list, tuple)) and len(item) == 2:
                # Older Gradio versions use tuple format
                human, assistant = item
                formatted_history.append({"role": "user", "content": human})
                formatted_history.append({"role": "assistant", "content": assistant})

        messages = [{"role": "system", "content": self.system_prompt(message)}] + formatted_history + [
            {"role": "user", "content": message}]

        done = False
        while not done:
            response = self.openai.chat.completions.create(model="gpt-5-mini", messages=messages, tools=tools)
            if response.choices[0].finish_reason == "tool_calls":
                response_message = response.choices[0].message
                tool_calls = response_message.tool_calls
                results = self.handle_tool_call(tool_calls)
                messages.append(response_message)
                messages.extend(results)
            else:
                done = True
        return response.choices[0].message.content


if __name__ == "__main__":
    me = Me()
    me.load_documents()
    gr.ChatInterface(me.chat).launch()
