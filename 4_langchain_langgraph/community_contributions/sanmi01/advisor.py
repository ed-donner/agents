import uuid
from typing import Annotated, Any, Dict, List, Optional
from typing_extensions import TypedDict

from dotenv import load_dotenv
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.prebuilt import ToolNode
from langgraph.graph.message import add_messages
from pydantic import BaseModel, Field

from tools import get_weather, send_push_notification, serper_tool, wiki_tool

load_dotenv(override=True)

# Constants

MODEL = "gpt-4o-mini"

DEFAULT_SUCCESS_CRITERIA = """
1. Specific fertiliser recommendations with NPK ratios and application rates
2. Seed variety recommendations suited to the crop, location, and problem
3. Pesticide recommendations with active ingredients and dosages where relevant
4. Recommendations grounded in the user's stated crop, location, growth stage, and current weather
5. Clear reasoning provided for each recommendation
"""


class State(TypedDict):
    messages: Annotated[List[Any], add_messages]
    info_complete: bool
    crop_type: Optional[str]
    location: Optional[str]
    growth_stage: Optional[str]
    problem_description: Optional[str]
    planner_output: Optional[dict]
    web_results: Optional[str]
    wiki_results: Optional[str]
    weather_data: Optional[dict]
    aggregated: Optional[str]
    advisory_report: Optional[str]
    feedback_on_work: Optional[str]
    success_criteria_met: bool
    user_input_needed: bool
    iteration_count: int


class ClarifierOutput(BaseModel):
    message: str = Field(description="Response message to the farmer")
    info_complete: bool = Field(description="True if enough info to proceed with research")
    crop_type: Optional[str] = Field(description="Crop type extracted from conversation")
    location: Optional[str] = Field(description="Location extracted from conversation")
    growth_stage: Optional[str] = Field(description="Growth stage if mentioned")
    problem_description: Optional[str] = Field(description="Problem or need described by farmer")

class PlannerOutput(BaseModel):
    web_queries: List[str] = Field(description="Search queries for Serper web search")
    wiki_queries: List[str] = Field(description="Search queries for Wikipedia")
    latitude: float = Field(description="Estimated latitude of the location")
    longitude: float = Field(description="Estimated longitude of the location")

class EvaluatorOutput(BaseModel):
    feedback: str = Field(description="Specific feedback on the advisory report")
    success_criteria_met: bool = Field(description="True if the advisory meets all success criteria")
    user_input_needed: bool = Field(description="True if the advisor is stuck or needs clarification")


class FarmAdvisor:
    def __init__(self):
        self.graph = None
        self.advisor_id = str(uuid.uuid4())
        self.memory = MemorySaver()
        self.llm = ChatOpenAI(model=MODEL)

    async def setup(self):
        await self._build_graph()

    # Nodes 

    def clarifier(self, state: State) -> Dict[str, Any]:
        system_message = """You are FarmAdvisor, a friendly and knowledgeable agricultural assistant.
Your job is to gather enough information from the farmer to provide useful input recommendations.

You need at minimum:
- The crop they are growing
- Their location (city or region)
- The problem they are facing OR what they need advice on

Growth stage and soil type are helpful but not required to proceed.

If you have the minimum information, set info_complete to True.
If critical information is missing, ask one focused question and set info_complete to False.
Never ask for more than one thing at a time.
Always be warm and practical in tone."""

        clarifier_llm = self.llm.with_structured_output(ClarifierOutput)
        messages = [SystemMessage(content=system_message)] + state["messages"]
        result = clarifier_llm.invoke(messages)

        return {
            "messages": [AIMessage(content=result.message)],
            "info_complete": result.info_complete,
            "crop_type": result.crop_type,
            "location": result.location,
            "growth_stage": result.growth_stage,
            "problem_description": result.problem_description,
        }

    def planner(self, state: State) -> Dict[str, Any]:
        system_message = """You are an agricultural research planner.
Given the farmer's crop, location, growth stage, and problem, generate targeted search queries
and estimate the GPS coordinates of the location for weather data retrieval.

Generate 3 web search queries focused on: current product availability, prices, and treatment options.
Generate 2 Wikipedia queries focused on: the crop itself and the specific problem or pest mentioned.
Estimate latitude and longitude as accurately as possible for the named location."""

        user_message = f"""Farmer details:
- Crop: {state['crop_type']}
- Location: {state['location']}
- Growth stage: {state['growth_stage'] or 'not specified'}
- Problem: {state['problem_description']}

Generate search queries and coordinates."""

        planner_llm = self.llm.with_structured_output(PlannerOutput)
        messages = [SystemMessage(content=system_message), HumanMessage(content=user_message)]
        result = planner_llm.invoke(messages)

        return {"planner_output": result.model_dump()}

    def web_researcher(self, state: State) -> Dict[str, Any]:
        queries = state["planner_output"]["web_queries"]
        results = []
        for query in queries:
            try:
                result = serper_tool.invoke(query)
                results.append(f"Query: {query}\nResults: {result}")
            except Exception as e:
                results.append(f"Query: {query}\nError: {str(e)}")

        return {"web_results": "\n\n".join(results)}

    def wiki_researcher(self, state: State) -> Dict[str, Any]:
        queries = state["planner_output"]["wiki_queries"]
        results = []
        for query in queries:
            try:
                result = wiki_tool.invoke(query)
                results.append(f"Query: {query}\nResults: {result}")
            except Exception as e:
                results.append(f"Query: {query}\nError: {str(e)}")

        return {"wiki_results": "\n\n".join(results)}

    def weather_fetcher(self, state: State) -> Dict[str, Any]:
        lat = state["planner_output"]["latitude"]
        lon = state["planner_output"]["longitude"]
        try:
            weather = get_weather.invoke({"latitude": lat, "longitude": lon})
        except Exception as e:
            weather = {"error": str(e)}

        return {"weather_data": weather}

    def aggregator(self, state: State) -> Dict[str, Any]:
        system_message = """You are an agricultural research aggregator.
Combine the web search results, Wikipedia information, and weather data into a single
coherent context summary. Remove duplicates, highlight the most relevant facts,
and note how current weather conditions relate to the farmer's problem."""

        weather = state.get("weather_data") or {}
        weather_summary = (
            f"Temperature: {weather.get('temperature_c')}°C, "
            f"Precipitation: {weather.get('precipitation_mm')}mm, "
            f"Humidity: {weather.get('humidity_pct')}%, "
            f"Soil moisture: {weather.get('soil_moisture')}"
            if not weather.get("error")
            else f"Weather unavailable: {weather.get('error')}"
        )

        user_message = f"""Please aggregate the following research for:
Crop: {state['crop_type']} | Location: {state['location']} | Problem: {state['problem_description']}

Current Weather at {state['location']}:
{weather_summary}

Web Research:
{state.get('web_results', 'No web results')}

Wikipedia Research:
{state.get('wiki_results', 'No wiki results')}"""

        messages = [SystemMessage(content=system_message), HumanMessage(content=user_message)]
        result = self.llm.invoke(messages)

        return {"aggregated": result.content}

    def advisor(self, state: State) -> Dict[str, Any]:
        system_message = f"""You are an expert agricultural input advisor.
Based on the research provided, give a structured farm input recommendation covering:

1. FERTILISER -- specific products, NPK ratios, application rates, timing
2. SEEDS -- recommended varieties suited to the crop, location, and problem
3. PESTICIDES -- active ingredients, dosages, application method, safety intervals

Ground every recommendation in the research and current weather conditions.
Be specific -- avoid vague generalities. Include product names where possible.

Success Criteria:
{state.get('success_criteria') or DEFAULT_SUCCESS_CRITERIA}"""

        if state.get("feedback_on_work"):
            system_message += f"""

Your previous advisory was rejected. Feedback:
{state['feedback_on_work']}

Please revise your recommendations to address this feedback."""

        user_message = f"""Farmer details:
- Crop: {state['crop_type']}
- Location: {state['location']}
- Growth stage: {state['growth_stage'] or 'not specified'}
- Problem: {state['problem_description']}

Research and context:
{state.get('aggregated', 'No aggregated research available')}

Please provide your structured farm input advisory."""

        messages = [SystemMessage(content=system_message), HumanMessage(content=user_message)]
        result = self.llm.invoke(messages)

        return {
            "messages": [AIMessage(content=result.content)],
            "advisory_report": result.content,
        }

    def evaluator(self, state: State) -> Dict[str, Any]:
        system_message = f"""You are a senior agronomist evaluating a farm input advisory report.
Assess the advisory strictly against these success criteria:

{state.get('success_criteria') or DEFAULT_SUCCESS_CRITERIA}

Only approve if ALL criteria are met with specific, grounded recommendations.
Reject if any criterion is missing, vague, or not grounded in the farmer's context.
Set user_input_needed to True only if the advisor appears stuck or critical info is truly missing."""

        user_message = f"""Farmer context:
- Crop: {state['crop_type']}
- Location: {state['location']}
- Growth stage: {state['growth_stage'] or 'not specified'}
- Problem: {state['problem_description']}
- Weather at location: {state.get('weather_data') or 'unavailable'}

Advisory report to evaluate:
{state.get('advisory_report', '')}

{f"Previous feedback given: {state['feedback_on_work']}" if state.get('feedback_on_work') else ""}

Evaluate the advisory and provide your verdict."""

        evaluator_llm = self.llm.with_structured_output(EvaluatorOutput)
        messages = [SystemMessage(content=system_message), HumanMessage(content=user_message)]
        result = evaluator_llm.invoke(messages)

        return {
            "messages": [AIMessage(content=f"Evaluator: {result.feedback}")],
            "feedback_on_work": result.feedback,
            "success_criteria_met": result.success_criteria_met,
            "user_input_needed": result.user_input_needed,
            "iteration_count": state.get("iteration_count", 0) + 1,
        }

    def report_sender(self, state: State) -> Dict[str, Any]:
        system_message = """You are a farm advisory delivery agent.
Your job is to:
1. Send a short one-line Pushover push notification summarising the key recommendation
2. Return the full advisory report for display in chat

The push notification should be under 100 characters and mention the crop and top recommendation."""

        user_message = f"""Please send a push notification summarising this advisory for {state['crop_type']} in {state['location']}.

Full report:
{state.get('advisory_report', '')}"""

        report_llm = self.llm.bind_tools([send_push_notification])
        messages = [SystemMessage(content=system_message), HumanMessage(content=user_message)]

        done = False
        while not done:
            response = report_llm.invoke(messages)
            if hasattr(response, "tool_calls") and response.tool_calls:
                tool_node = ToolNode(tools=[send_push_notification])
                tool_results = tool_node.invoke({"messages": messages + [response]})
                messages = messages + [response] + tool_results["messages"]
            else:
                done = True

        return {
            "messages": [AIMessage(content=state.get("advisory_report", ""))],
        }

    # Routers

    def clarifier_router(self, state: State) -> str:
        if state.get("info_complete"):
            return "planner"
        return "END"

    def evaluator_router(self, state: State) -> str:
        max_iterations = 3
        if state.get("iteration_count", 0) >= max_iterations:
            return "report_sender"
        if state.get("success_criteria_met") or state.get("user_input_needed"):
            return "report_sender"
        return "advisor"

    # Graph builder

    async def _build_graph(self):
        builder = StateGraph(State)

        builder.add_node("clarifier", self.clarifier)
        builder.add_node("planner", self.planner)
        builder.add_node("web_researcher", self.web_researcher)
        builder.add_node("wiki_researcher", self.wiki_researcher)
        builder.add_node("weather_fetcher", self.weather_fetcher)
        builder.add_node("aggregator", self.aggregator)
        builder.add_node("advisor", self.advisor)
        builder.add_node("evaluator", self.evaluator)
        builder.add_node("report_sender", self.report_sender)

        builder.add_edge(START, "clarifier")
        builder.add_conditional_edges(
            "clarifier",
            self.clarifier_router,
            {"planner": "planner", "END": END}
        )
        builder.add_edge("planner", "web_researcher")
        builder.add_edge("web_researcher", "wiki_researcher")
        builder.add_edge("wiki_researcher", "weather_fetcher")
        builder.add_edge("weather_fetcher", "aggregator")
        builder.add_edge("aggregator", "advisor")
        builder.add_edge("advisor", "evaluator")
        builder.add_conditional_edges(
            "evaluator",
            self.evaluator_router,
            {"advisor": "advisor", "report_sender": "report_sender"}
        )
        builder.add_edge("report_sender", END)

        self.graph = builder.compile(checkpointer=self.memory)

    # Run

    async def run(self, message: str, history: list) -> list:
        if self.graph is None:
            await self.setup()

        config = {"configurable": {"thread_id": self.advisor_id}}

        history_messages = []
        for entry in history:
            if entry.get("role") == "user":
                history_messages.append(HumanMessage(content=entry["content"]))
            elif entry.get("role") == "assistant":
                history_messages.append(AIMessage(content=entry["content"]))

        history_messages.append(HumanMessage(content=message))

        state = {
            "messages": history_messages,
            "info_complete": False,
            "crop_type": None,
            "location": None,
            "growth_stage": None,
            "problem_description": None,
            "planner_output": None,
            "web_results": None,
            "wiki_results": None,
            "weather_data": None,
            "aggregated": None,
            "advisory_report": None,
            "feedback_on_work": None,
            "success_criteria_met": False,
            "user_input_needed": False,
            "iteration_count": 0,
        }

        result = await self.graph.ainvoke(state, config=config)

        # Extract the last meaningful assistant message
        ai_messages = [
            m for m in result["messages"]
            if isinstance(m, AIMessage)
            and m.content
            and not m.content.startswith("Evaluator:")
        ]

        reply = ai_messages[-1].content if ai_messages else "I was unable to generate a recommendation. Please try again."

        return history + [
            {"role": "user", "content": message},
            {"role": "assistant", "content": reply}
        ]