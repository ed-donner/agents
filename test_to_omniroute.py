from langchain_openai import ChatOpenAI
# Set your environment variables if you need a dummy key, though it might not be used
import os
os.environ["OPENAI_API_KEY"] = ""


# 1. Define the local base URL
# OLLAMA_BASE_URL = "http://localhost:11434"  # This should match your local service's URL
LOCAL_ENDPOINT_URL = "http://localhost:20128/v1"  # This should match your local service's endpoint

try:
    # 2. Initialize the model, pointing it to your local endpoint
    # We use 'gpt-3.5-turbo' as a placeholder name for the model you want the service to use.
    llm = ChatOpenAI(
        api_key="dummy-key",  # Keep this even if the server doesn't require it
        openai_api_base=LOCAL_ENDPOINT_URL, # <--- THIS IS THE CRITICAL LINE
        model="auto"           # Tell LangChain which model name to use (or leave it blank)
    )

    print("Successfully initialized ChatOpenAI pointing to local endpoint.")

    # 3. Invoke the LLM
    prompt = "Write a short poem about running local AI."
    response = llm.invoke(prompt) # Use .invoke() for modern LangChain calls

    print("\n--- Prompt ---")
    print(prompt)
    print("\n--- Response from Local LLM ---")
    # The response object usually contains the text directly
    print(response.content)

except Exception as e:
    print(f"\n!!! ERROR !!!")
    print("Could not connect to your local endpoint.")
    print("Please ensure the service is running at 'http://localhost:20128/v1'.")
    print(f"Details: {e}")
