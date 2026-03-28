import asyncio

from dotenv import load_dotenv

from research_manager import ResearchManager

load_dotenv(override=True)


async def main():
    manager = ResearchManager()
    query = input("Research topic: ").strip()
    if not query:
        print("Please provide a non-empty query.")
        return

    clarification = await manager.get_clarifying_questions(query)
    print("\nPlease answer the 3 clarifying questions (press Enter to use defaults):\n")

    answers: list[str] = []
    for idx, question in enumerate(clarification.questions, start=1):
        answer = input(f"{idx}. {question}\n> ").strip()
        answers.append(answer)

    print("\nRunning research...\n")
    final_report = ""
    async for chunk in manager.run(query, answers):
        print(chunk)
        final_report = chunk

    print("\n--- Final Report ---\n")
    print(final_report)


if __name__ == "__main__":
    asyncio.run(main())
