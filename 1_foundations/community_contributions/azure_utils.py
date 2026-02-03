import os
from openai import AzureOpenAI
from dotenv import load_dotenv

class AzureClientManager:
    """
    Daniel's Production-grade manager for Azure OpenAI.
    Implemented to showcase Object-Oriented AI architecture.
    """
    
    def __init__(self):
        """
        1. SETUP & AUTHENTICATION
        Automatically pulls credentials from your .env file.
        Ensures the client is authenticated before any calls are made.
        """
        # load_dotenv(override=True) ensures that if you update your .env, 
        # the script picks up the new keys without a full restart.
        load_dotenv(override=True)
        
        # Initialize the official Azure SDK client. 
        # Requirement: .env must contain endpoint, key, and version.
        self.client = AzureOpenAI(
            api_key=os.getenv("AZURE_OPENAI_API_KEY"),
            api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
        )
        
        # In Azure, the 'model' parameter is actually your 'Deployment Name'.
        self.deployment_name = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")
        self.embedding_deployment = os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT")

    def get_chat_response(self, prompt, system_message="You are a helpful assistant.", temperature=0.7):
        """
        2. CHAT COMPLETIONS (The "Bread and Butter")
        Sends a conversation history to the model and returns the text response.
        :param temperature: 0.0 (deterministic) to 1.0 (creative).
        """
        try:
            # Azure requires a list of message dictionaries (role + content).
            response = self.client.chat.completions.create(
                model=self.deployment_name,
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": prompt}
                ],
                temperature=temperature,
                max_tokens=800 # Prevents unexpected cost overruns
            )
            return response.choices[0].message.content
        except Exception as e:
            # Production-grade error handling for API timeouts or quota limits.
            return f"Azure SDK Chat Error: {str(e)}"

    def get_embedding(self, text):
        """
        3. GENERATING EMBEDDINGS
        Converts text into a numerical vector for RAG or Semantic Search.
        Critical for projects involving vector databases like Pinecone or Chroma.
        """
        try:
            # We replace newlines with spaces to improve vector accuracy.
            text = text.replace("\n", " ")
            response = self.client.embeddings.create(
                input=[text], 
                model=self.embedding_deployment
            )
            # Returns the raw list of floats (vector).
            return response.data[0].embedding
        except Exception as e:
            return f"Azure SDK Embedding Error: {str(e)}"

    def get_streaming_response(self, prompt):
        """
        4. STREAMING RESPONSES
        Yields chunks of text as they are generated for a smoother UI/UX.
        Optimized for use with Gradio's .stream() functionality.
        """
        try:
            stream = self.client.chat.completions.create(
                model=self.deployment_name,
                messages=[{"role": "user", "content": prompt}],
                stream=True
            )
            for chunk in stream:
                # delta.content contains the new word/character fragment.
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        except Exception as e:
            yield f"Streaming Error: {str(e)}"

# --- 🚀 EXAMPLE WORKFLOW ---
if __name__ == "__main__":
    # Instantiate the manager (this triggers the .env load)
    az_manager = AzureClientManager()
    
    # 1. Test standard chat
    print("--- Testing Chat ---")
    print("AI:", az_manager.get_chat_response("Why is New York called the Big Apple?"))
    
    # 2. Test embedding generation
    print("\n--- Testing Embeddings ---")
    vector = az_manager.get_embedding("Columbia University in the City of New York")
    print(f"Success! Vector Length: {len(vector)}")