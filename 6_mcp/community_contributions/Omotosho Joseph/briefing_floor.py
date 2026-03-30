from reporters import Reporter
import asyncio
from briefing_tracers import BriefingTracer
from agents import add_trace_processor
from dotenv import load_dotenv
import os

load_dotenv(override=True)

RUN_EVERY_N_MINUTES = int(os.getenv("RUN_EVERY_N_MINUTES", "60"))

names = ["Ada", "Marcus", "Zara"]
model_names = ["gpt-4o-mini"] * 3


def create_reporters():
    return [
        Reporter(name, model_name)
        for name, model_name in zip(names, model_names)
    ]


async def run_briefing_cycle():
    add_trace_processor(BriefingTracer())
    reporters = create_reporters()
    while True:
        print("Starting briefing cycle...")
        await asyncio.gather(*[reporter.run() for reporter in reporters])
        print(
            f"Cycle complete. Next run in {RUN_EVERY_N_MINUTES} minutes."
        )
        await asyncio.sleep(RUN_EVERY_N_MINUTES * 60)


if __name__ == "__main__":
    print(
        f"Starting briefing floor — running every "
        f"{RUN_EVERY_N_MINUTES} minutes"
    )
    asyncio.run(run_briefing_cycle())
