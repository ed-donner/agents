import asyncio
from agents import Runner,trace,set_tracing_export_api_key

from config import OPENAI_API_KEY
from agents_setup import email_agent1,email_agent2,email_agent3,email_picker

set_tracing_export_api_key(OPENAI_API_KEY)

async def main():
    message = input("Enter the email content: ")
    with trace("Email Picker Workflow"):
        results = await asyncio.gather(
            Runner.run(email_agent1, message),
            Runner.run(email_agent2, message),
            Runner.run(email_agent3, message),
        )
    outputs = [result.final_output for result in results]
    emails = " Generated emails:\n\n" + "\n\nEmail:\n\n".join(outputs)
    best = await Runner.run(email_picker, emails)
    print("Completed! The best email has been sent successfully.")

if __name__ == "__main__":
    asyncio.run(main())