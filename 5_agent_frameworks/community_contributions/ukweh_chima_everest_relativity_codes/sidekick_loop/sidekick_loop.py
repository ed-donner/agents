import asyncio
from typing import Annotated
from autogen_ext.models.openai import OpenAIChatCompletionClient
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.messages import TextMessage
from autogen_core import CancellationToken
from dotenv import load_dotenv

# Define tools
def google_search(query: Annotated[str, "The search query"]) -> str:
    """Search Google for real-time information."""
    print(f"🔍 Searching Google for: {query}")
    return f"Simulated search results for: {query}. (Agentic bootcamp results show massive success!)"

def send_notification(message: Annotated[str, "The message to send"]) -> str:
    """Send a push notification to the user."""
    print(f"📱 Sending Notification: {message}")
    return "✅ Notification sent successfully."

async def main():
    load_dotenv(override=True)
    model_client = OpenAIChatCompletionClient(model="gpt-4o-mini")

    worker = AssistantAgent(
        name="worker",
        model_client=model_client,
        tools=[google_search, send_notification],
        system_message="""You are a helpful worker. 
        1. Use google_search to find information if you're unsure. 
        2. Use send_notification to alert the user once a task is done.
        3. Complete tasks thoroughly."""
    )

    evaluator = AssistantAgent(
        name="evaluator",
        model_client=model_client,
        system_message="""You are a strict evaluator.
        If the worker's response is complete and accurate, respond with 'APPROVED'.
        Otherwise, provide specific feedback starting with 'FEEDBACK:'."""
    )

    task = "Research the latest trend in Agentic AI and notify me of the result."
    print(f"🚀 Starting task: {task}")

    messages = [TextMessage(content=task, source="user")]
    max_iterations = 3
    
    for i in range(max_iterations):
        print(f"\n--- Iteration {i+1} ---")
        response = await worker.on_messages(messages, cancellation_token=CancellationToken())
        worker_output = response.chat_message.content
        print(f"Worker output: {worker_output[:100]}...")
        
        eval_input = [TextMessage(content=f"Review this worker output for completeness: {worker_output}", source="user")]
        eval_response = await evaluator.on_messages(eval_input, cancellation_token=CancellationToken())
        feedback = eval_response.chat_message.content
        print(f"Evaluator: {feedback}")

        if "APPROVED" in feedback.upper():
            print("\n✅ Task approved!")
            break
        else:
            messages.append(TextMessage(content=f"Refine your previous answer based on feedback: {feedback}", source="user"))

    print("\nFinal Result:")
    print(worker_output)

if __name__ == "__main__":
    asyncio.run(main())
