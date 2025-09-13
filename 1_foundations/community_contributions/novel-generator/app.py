import asyncio
from dotenv import load_dotenv
from novel_generator_manager import NovelGeneratorManager

load_dotenv(override=True)

async def run():
  await NovelGeneratorManager().run()

if __name__ == "__main__":
    asyncio.run(run())
