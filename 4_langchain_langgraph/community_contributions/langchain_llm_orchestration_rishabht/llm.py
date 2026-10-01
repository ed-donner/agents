# import proxy_patch # Incase running behind corp proxy, not a suggested approach for production
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from langchain.agents import create_agent
from langchain.agents.middleware import wrap_tool_call
from langchain_core.tools import tool
from langgraph.checkpoint.memory import MemorySaver
import random

load_dotenv(override=True)

class CityReport(BaseModel):
    city: str = Field(description="The city name")
    weather: str = Field(description="A short weather description")
    population: str = Field(description="The population")
    clothes: str = Field(description="The suitable clothes for the city")

@tool
def get_weather(city:str)->str:
    """Get the weather of a city"""
    weather = {"london": "sunny, 14 degrees", "rome": "rainy, 12 degrees", "new york": "cloudy, 10 degrees", 
    "tokyo": "rainy, 11 degrees", "paris": "cloudy, 12 degrees"}
    return weather.get(city.lower(), "unknown")

@tool
def get_population(city: str) -> str:
    """Return the population of a city."""
    population = {"london": "8.9m", "rome": "6m", "new york": "10.5m", 
    "tokyo": "5.6m", "paris": "5.4m"}
    return population.get(city.lower(), "unknown")

@tool
def suggest_suitable_clothes(city: str) -> str:
    """Return the suitable clothes for a city."""
    clothes = {"london": "TShirt and Shorts", "rome": "Casual, with Raincoat", "new york": "Winter wears, with umbrella", 
    "tokyo": "Winter wears,Raincoat", "paris": "TShirt and Shorts"}
    return clothes.get(city.lower(), "unknown")

@wrap_tool_call
def intercept_tool_call(request,handler)->str:
    print("Intercepting the tool call...")
    tool_call = request.tool_call
    if tool_call['name'] == 'apparel_agent':
       print(f"[middleware] calling subagent tool:  {tool_call['name']} with {tool_call['args']}.") # You can have custom logic here.
    else:
       print(f"[middleware] calling main agent tool:  {tool_call['name']} with {tool_call['args']}.")
    return handler(request)


def apparel_agent():
    apparel_agent=create_agent(
        model="openai:gpt-4o-mini",
        tools=[suggest_suitable_clothes]
    )
    return apparel_agent

@tool("apparel_agent", description="You are a helpful assistant who suggests suitable clothes for a city.")
def call_apparel_agent(city: str):
    subagent = apparel_agent()
    result = subagent.invoke({"messages": [{"role": "user", "content": city}]})
    return result["messages"][-1].content 


def main_agent():
    main_agent=create_agent(
        model="openai:gpt-4o-mini",
        system_prompt="You are a helpful assistant who answers concisely. Use the tools to get the information and answer the question..",
        tools=[get_weather, get_population, call_apparel_agent],
        middleware=[intercept_tool_call],
        checkpointer=MemorySaver(),
        response_format=CityReport
    )
    return main_agent


agent = main_agent()
config = {"configurable": {"thread_id": str(random.randint(1, 1_000_000))}} # If not provided, the LLM cannot answer the second question.

result = agent.invoke({"messages": [{"role": "user", "content": "Planning to visit rome, what should I pack?"}]}, config=config)
print(result["structured_response"])
result = agent.invoke({"messages": [{"role": "user", "content": "what is the population of this city?"}]}, config=config)
print(result["structured_response"])


