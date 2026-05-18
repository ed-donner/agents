from agents import Agent, Runner, trace
from agents.mcp import MCPServerStdio
from dotenv import load_dotenv

load_dotenv(override=True)

INSTRUCTIONS = """You are a friendly, knowledgeable meal planning assistant.
You help users discover recipes, plan weekly meals, and generate shopping lists.

Your capabilities via tools:
- Search recipes by keyword, category, cuisine, or ingredient
- Get full recipe details (ingredients, instructions, video links)
- Get random recipe inspiration
- Build and manage a day-by-day meal plan (breakfast, lunch, dinner, snack)
- Generate a consolidated shopping list from the meal plan

When helping a user plan meals:
1. Ask about preferences: dietary restrictions, cuisines they enjoy, how many days to plan
2. Suggest varied meals across the week (mix cuisines, balance proteins/carbs)
3. For each suggested meal, use the search tools to find real recipes
4. Add confirmed meals to the plan with their meal IDs so shopping lists work
5. Once the plan is set, offer to generate the shopping list

Keep responses concise and well-formatted. Use bullet points and organize by day."""

meal_server = MCPServerStdio(
    name="Meal Planner MCP",
    params={"command": "uv", "args": ["run", "meal_server.py"]},
)


async def run_agent(user_message: str, history: list[dict] | None = None):
    messages = []
    if history:
        messages.extend(history)
    messages.append({"role": "user", "content": user_message})

    async with meal_server:
        agent = Agent(
            name="Meal Planner",
            instructions=INSTRUCTIONS,
            mcp_servers=[meal_server],
            model="gpt-4o-mini",
        )
        with trace("Meal Planning Session"):
            result = await Runner.run(agent, messages)
        return result.final_output


if __name__ == "__main__":
    import asyncio

    async def main():
        print("Meal Planner Agent (type 'quit' to exit)\n")
        history = []
        while True:
            user_input = input("You: ").strip()
            if user_input.lower() in ("quit", "exit", "q"):
                break
            response = await run_agent(user_input, history)
            history.append({"role": "user", "content": user_input})
            history.append({"role": "assistant", "content": response})
            print(f"\nAssistant: {response}\n")

    asyncio.run(main())
