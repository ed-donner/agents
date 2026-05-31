from agents.extensions.models.litellm_model import LitellmModel

ollama_model = LitellmModel(model="ollama/llama3.2", api_key="ollama")
ollama_model_eval = LitellmModel(model="ollama/llama3.1", api_key="ollama")
