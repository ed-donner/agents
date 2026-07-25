from typing import Dict
from typing import Any
from pydantic import BaseModel
import json
import logging
from typing import Callable
import PyPDF2
import os
from pathlib import Path
from chromadb import PersistentClient
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings
import requests
from utilities.settings import Settings
from utilities.models import Model


collection_name = "cvs"

DB_NAME = "./vector_db"


embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
vectorstore = Chroma(persist_directory=DB_NAME, embedding_function=embeddings)

RETRIEVAL_K = 2

class Property(BaseModel):
    name: str
    type: str
    description: str

class Parameter(BaseModel):
    type: str = "object"
    properties: list[Property]
    required: list[str]
    additionalProperties: bool = False

class Tool(BaseModel):
    name: str
    description: str
    parameters: Parameter




class ToolCreation:

    def __init__(self):
        self._tool_call: list[dict[str, Any]] = []
        self._tool_registry: dict[str, Callable] = {}
        self._logger = logging.getLogger(__name__)
        self.chunk_ratio:float = 0.2
        self.retriever = vectorstore.as_retriever()
        self.settings = Settings()
        self.model = Model(type="openrouter")
        self.model_name = "meta-llama/Llama-3.1-70B-Instruct"

    def create_tool(self, details: Tool, fn: Callable) -> list[dict[str, Any]]:
        properties = {}
        for prop in details.parameters.properties:
            properties[prop.name] = {"type":prop.type, "description":prop.description}
        tool = {
            "name": details.name,
            "description": details.description,
            "parameters" : {
                "type": details.parameters.type,
                "properties": properties,
                 "required": details.parameters.required,
                 "additionalProperties": details.parameters.additionalProperties
            }
        }
        
        self._tool_registry[details.name] = fn

        existing_names = [t["function"]["name"] for t in self._tool_call]

        if details.name not in existing_names:
            self._tool_call.append({"type": "function", "function": tool})

        self._tool_call.append({"type": "function", "function": tool})

        
        return self._tool_call


    def handle_tool_call(self, tool_name: Any, tool_args: Any) -> str:
        fn = self._tool_registry.get(tool_name)
        if fn is None:
            return json.dumps({"error": f"Unknown tool: {tool_name}","status": "failed","message": "This tool does not exist. Inform the user you are unable to complete this action."})
        try:
            return json.dumps(fn(**tool_args))
        except Exception as exc:
            self._logger.exception("Tool %s failed: %s", tool_name, exc)
            return json.dumps({"error": str(exc),"status": "failed","message": "This tool does not exist. Inform the user you are unable to complete this action."})

    
    def read_pdf(self, file_path: str) -> list[str]:
        chunks:list[str] = []
        prior_overlap:str = ""
        for path in Path(file_path).glob("*.pdf"):
            with open(path, "rb") as file:
                reader = PyPDF2.PdfReader(file)
                for page in reader.pages:
                    page_text = page.extract_text()
                    if page_text:
                        page_text = page_text.strip()
                        extract = prior_overlap + page_text
                        chunks.append(extract)
                        overlap_size = int(len(extract) * self.chunk_ratio)
                        prior_overlap = extract[-overlap_size:] if overlap_size > 0 else ""
                    else:
                        continue
        return chunks

    def create_embeddings(self,chunks):
        docs = [Document(page_content=chunk) for chunk in chunks]

        if os.path.exists(DB_NAME):
            Chroma(persist_directory=DB_NAME, embedding_function=embeddings).delete_collection()

        vectorstore = Chroma.from_documents(
            documents=docs, embedding=embeddings, persist_directory=DB_NAME
        )

        collection = vectorstore._collection
        count = collection.count()
        self.retriever = vectorstore.as_retriever()
        print(f"There are {count:,} vectors in the vector store")
        
        return vectorstore

    def retrieve_context(self, query: str) -> list[str]:
        docs = self.retriever.invoke(query, k=RETRIEVAL_K)
        return [doc.page_content for doc in docs]

   

    def get_cal_availability(self,start_date, end_date):
        
        url = self.settings.cal_slot_url
        print(f"Getting availability for {start_date} to {end_date}")
        
        params = {
            "startTime": f"{start_date}T00:00:00Z",
            "endTime": f"{end_date}T23:59:59Z",
            "username": self.settings.cal_username,
            "eventTypeId": 5110491,
            "timeZone": "Africa/Lagos"
        }
        
        headers = {
            "Authorization": f"Bearer {self.settings.cal_api_key}",
            "cal-api-version": self.settings.cal_api_version
        }

        response = requests.get(url, params=params, headers=headers)
    
        
        slots = response.json().get("data", {}).get("slots", {})
        
        if not slots:
            return "No available slots found for these dates."
            
        formatted = []
        for date, times in slots.items():
            time_list = [t["time"].split("T")[1][:5] for t in times] 
            formatted.append(f"{date}: {', '.join(time_list)}")
        
        return "\n".join(formatted)
    
    def evaluate_response(self, messages, response, name):
        raw_response = response.choices[0].message.content

        clean_messages = []
        #filter out tool calls
        for m in messages:
            if isinstance(m, dict) and m.get("role") in ("user", "assistant", "system"):
                content = m.get("content")
                if content and isinstance(content, str):
                    clean_messages.append({"role": m["role"], "content": content})

        system_prompt = f"""You are a response quality checker for {name}'s AI assistant.

    Your ONLY job is to review the assistant's response and return the final text to show the user.

    STRICT RULES:
    - Return ONLY the final response text — nothing else
    - Do NOT mention tools, tool calls, send_email, or any internal processes
    - Do NOT explain what you are doing or what needs to happen
    - Do NOT include any markup like [send_email] or function calls
    - Do NOT add reasoning, commentary, or preamble
    - If the response is good, return it exactly as-is
    - If it needs fixing, return only the corrected version

    You are NOT an agent. You cannot call tools. You only return text."""

        eval_messages = [
            {"role": "system", "content": system_prompt},
            *clean_messages,
            {"role": "assistant", "content": raw_response},
            {"role": "user", "content": "Return the final response text only."}
        ]

        result = self.model.get_model(self.model_name, eval_messages, tool_choice="none")
        return result.choices[0].message.content
