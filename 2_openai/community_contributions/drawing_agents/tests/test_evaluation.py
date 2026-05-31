import asyncio

from dotenv import load_dotenv

from my_agents.drawing_evaluation_agent import run_evaluation_agent

load_dotenv(override=True)

OUTPUT_FILE = "agent_output.png"
DRAW_REQUEST = "Draw a beautiful house."

async def main():
    evaluation_result = await run_evaluation_agent("The drawing request was: " + DRAW_REQUEST, OUTPUT_FILE)
    print("Evaluation result:" + evaluation_result.final_output)

if __name__ == "__main__":
    asyncio.run(main())
