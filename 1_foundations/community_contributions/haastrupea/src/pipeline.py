
from pathlib import Path
from config import get_config
from src.agent import Agent
from openai import OpenAI
from src.tools import Tools
from ultils.Pushover import PushOver

from src.rag_system import RAGSystem

class Pipeline:
    config = get_config()

    def __init__(self) -> None:
        config = self.config
        openrouter_url = config.get("openrouter_url")
        openrouter_open_key = config.get("openrouter_api_key")

        llm_client = OpenAI(api_key=openrouter_open_key, base_url=openrouter_url)
        notifier = PushOver(config)
        tools = Tools(notifier)
        name = config.get('name', "Elijah HAASTRUP")
        self.agent = Agent(llm_client, tools, name)

        project_root = Path(__file__).parent.parent
        db_path = str(Path(project_root).resolve() / 'data')
        # rag system setup
        self.rag = RAGSystem(db_path)


    def parse_history_to_message (self, history: list):
        normalised_history = []

        for item in history:
            if not isinstance(item, dict):
                user_message, assitant_message = item
                if user_message:
                    normalised_history.append({"role": "user", "content": user_message })
                if assitant_message:
                    normalised_history.append({"role": "assistant", "content": assitant_message })
            else:
                normalised_history = history

        return normalised_history

    def chat(self, query: str, history: list) -> str:


        contexts = []

        should_retrieve = self.agent.should_use_rag_with_Query(query)

        # get rag contexts
        if should_retrieve:
            print("[RAG] Using RAG for this query")
            rag_context = self.rag.retrieve( query, top_k=self.config["top_k"] )
            if rag_context:
                contexts.extend(rag_context)

        normalised_history = self.parse_history_to_message(history)
        messages =  normalised_history + [{"role": "user", "content": query}]

        # call agent
        response = self.agent.llm_call(messages, contexts)

        return response