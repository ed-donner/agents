import asyncio

from agents import trace, Runner
from dotenv import load_dotenv

from context.app_context import AppContext
from my_agents.drawing_evaluation_agent import run_evaluation_agent
from my_agents.drawing_planning_agent import drawing_planning_agent
from tools.graphic_canvas import HeadlessCanvas

load_dotenv(override=True)

OUTPUT_FILE = "agent_output.png"
DRAW_REQUEST = "Draw a beautiful house with a garden and a dog"


async def main():
    canvas = HeadlessCanvas()
    canvas.initialize(640, 480)
    app_ctx = AppContext(canvas=canvas)
    with trace("Drawing agents"):
        print("Starting drawing planning agent")
        result = await Runner.run(drawing_planning_agent,
                                  f"{DRAW_REQUEST}",
                                  context=app_ctx,
                                  max_turns=60)
        print("Agent response:" + result.final_output)
        canvas.save_and_cleanup(OUTPUT_FILE)
        evaluation_result = await run_evaluation_agent("The drawing request was: " + DRAW_REQUEST, OUTPUT_FILE)
        print("Evaluation result:" + evaluation_result.final_output)


if __name__ == "__main__":
    asyncio.run(main())
