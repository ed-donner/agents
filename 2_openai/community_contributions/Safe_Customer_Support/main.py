import os
import asyncio
from dotenv import load_dotenv

dotenv_path = os.getenv("PROJECT_ENV_PATH", ".env")
load_dotenv(dotenv_path=dotenv_path, override=True)

from openai import AsyncOpenAI
from agents import Agent, Runner, trace, function_tool, input_guardrail, GuardrailFunctionOutput

from ai_agents.customer_support_agent import CustomerSupportAgent

load_dotenv(override=True)

async def main():
    support_agent = CustomerSupportAgent()

    print("\nWelcome to the Gravizot University Support Assistant!\n")
    print("Ask a question about Gravizot University and I'll do my best to help.")

    print("I can provide information on the following topics:\n")
    print("- Gravizot University Contact Information")
    print("- Courses of Study Offered by the University")
    print("- Procedures for Applying to the University")
    print("- Financial Aid\n")

    print("Type 'quit' or 'exit' to leave.")

    while True:
        message = input("\nPlease enter your question: ").strip()

        if message.lower() in {"quit", "exit"}:
            print("Thanks for stopping by, Goodbye!")
            break

        result = await support_agent.run_task(message)
        print(result)

if __name__ == "__main__":
    asyncio.run(main())
