"""Graph node functions and routing logic"""

from langchain_openai import ChatOpenAI
from langchain_core.messages import AIMessage, SystemMessage
from agent.state import State, IntakeExtraction, OpportunityList
from agent.tools import tools

NOT_PROVIDED = "Not provided yet"

intake_llm = ChatOpenAI(model="gpt-4o-mini").with_structured_output(IntakeExtraction)
search_llm = ChatOpenAI(model="gpt-4o-mini").bind_tools(tools)
format_llm = ChatOpenAI(model="gpt-4o-mini").with_structured_output(OpportunityList)


def intake(state: State) -> dict:
    """Gathers user preferences through natural conversation."""
    is_restart = state.get("stage") == "complete"

    budget = NOT_PROVIDED if is_restart else state.get("budget", NOT_PROVIDED)
    property_type = NOT_PROVIDED if is_restart else state.get("property_type", NOT_PROVIDED)
    purpose = NOT_PROVIDED if is_restart else state.get("purpose", NOT_PROVIDED)
    area = NOT_PROVIDED if is_restart else state.get("area", NOT_PROVIDED)

    system_prompt = f"""You are Kigali Property Scout, a friendly and knowledgeable real estate assistant \
specializing in Kigali, Rwanda.

CURRENT PREFERENCES:
- Budget: {budget}
- Property type: {property_type}
- Purpose: {purpose}
- Area of Kigali: {area}

YOUR TASK:
Guide the user through providing their 4 preferences in a natural, conversational way.
Ask for ONE missing preference at a time. If the user provides multiple in one message, extract them all.

EXTRACTION RULES:
- Budget: accept any format — USD, RWF, ranges like "$50k-$100k" or "around 30 million RWF"
- Property type: apartment, villa, house, studio, commercial, land, or similar
- Purpose: own use, rental income, resale investment, or similar
- Area: any Kigali neighborhood — Nyarutarama, Kicukiro, Kimihurura, Kacyiru, Rebero, \
Gacuriro, Kanombe, Vision City, Gisozi, Remera, Kibagabaga, Masaka, Kinyinya, Rusororo, \
or "no preference" if they have none

When all 4 are gathered, set all_gathered=True and tell the user you will now search for properties.

TONE: warm, professional, concise. No more than 2-3 sentences per reply."""

    messages = [SystemMessage(content=system_prompt)] + list(state.get("messages", []))
    result = intake_llm.invoke(messages)

    update: dict = {"messages": [AIMessage(content=result.response)]}

    if is_restart:
        update.update(stage="intake", opportunities=[])

    if result.budget:
        update["budget"] = result.budget
    if result.property_type:
        update["property_type"] = result.property_type
    if result.purpose:
        update["purpose"] = result.purpose
    if result.area:
        update["area"] = result.area

    if result.all_gathered:
        update["stage"] = "searching"

    return update


def search(state: State) -> dict:
    """Uses the LLM with bound tools to search for Kigali real estate."""
    budget = state.get("budget", "")
    property_type = state.get("property_type", "")
    purpose = state.get("purpose", "")
    area = state.get("area", "")

    system_prompt = f"""You are a real estate search specialist for Kigali, Rwanda.

The user is looking for:
- Budget: {budget}
- Property type: {property_type}
- Purpose: {purpose}
- Area: {area}

Use the web_search tool to find real estate opportunities matching these preferences.
Make 1-2 targeted searches. Good query strategies:
1. Search for specific developers/projects in the area: "{property_type} for sale {area} Kigali Rwanda {budget}"
2. Search for real estate agencies with listings: "real estate {area} Kigali {property_type} price"

Focus on finding: developer names, project names, prices, payment plans, and property details.
After searching, briefly summarize what you found."""

    messages = [SystemMessage(content=system_prompt)] + list(state.get("messages", []))
    result = search_llm.invoke(messages)

    return {"messages": [result]}


def format_results(state: State) -> dict:
    """Extracts structured opportunity cards from search results."""
    system_prompt = """Extract up to 4 real estate opportunities from the conversation's search results.

CRITICAL RULES:
- NEVER invent or guess prices. If a price is not explicitly stated in the search results, \
leave price_range as an empty string.
- NEVER fabricate source links. Only include URLs that appear in the search results.
- Include only highlights directly supported by the source material.
- If fewer than 4 relevant opportunities exist, return only what you found.
- If no relevant properties were found, return an empty opportunities list.

For each opportunity, extract:
- developer_name: the company or agency
- project_name: the specific project or listing name
- location: neighborhood or area within Kigali
- property_types: what's available (e.g. "2BR apartment, 3BR villa")
- price_range: only if explicitly stated in results
- payment_plan: deposit, installment, or off-plan terms if mentioned
- highlights: up to 3 selling points from the source
- source_link: the URL where this information was found"""

    messages = [SystemMessage(content=system_prompt)] + list(state.get("messages", []))
    result = format_llm.invoke(messages)

    opportunities = [opp.model_dump() for opp in result.opportunities[:4]]

    count = len(opportunities)
    if count == 0:
        closing = "I wasn't able to find properties matching your exact criteria. Try adjusting your budget, area, or property type and start a new search."
    else:
        closing = f"I found {count} {'opportunity' if count == 1 else 'opportunities'} matching your preferences. Take a look at the cards on the right!"

    return {
        "messages": [AIMessage(content=closing)],
        "opportunities": opportunities,
        "stage": "complete",
    }


def route_entry(state: State) -> str:
    """Routes from START based on current stage."""
    stage = state.get("stage", "intake")
    if stage in ("searching", "formatting"):
        return "search"
    return "intake"


def route_intake(state: State) -> str:
    """After intake: search if all gathered, otherwise return to user."""
    if state.get("stage") == "searching":
        return "search"
    return "end"


def search_router(state: State) -> str:
    """After search: route to tools if tool_calls, otherwise format."""
    last_message = state["messages"][-1]
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "tools"
    return "format"
