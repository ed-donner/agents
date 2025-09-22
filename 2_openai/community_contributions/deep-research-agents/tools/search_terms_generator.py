from schema import WebSearchPlan
from tools.tool_wrapper import tool_from_agent


HOW_MANY_SEARCHES = 3


# Instructions for the SearchTermsGenerator
SEARCH_TERMS_INSTRUCTIONS = f"""
Role:
- You are a helpful research assistant.

Task:
- Produce exactly {HOW_MANY_SEARCHES} web search terms based on the user’s initial query and the insights gathered from prior Q&A turns.

Input:
- the user input will be a ResearchContext JSON string.

Steps:
1) Parse the JSON from the user message to get the initial_query and qa_history.
2) Based on the initial query and previous answers from qa_history, provide exactly {HOW_MANY_SEARCHES} distinct, non-overlapping search terms to best answer the user's query.
3) Each search term should reflect a different angle (definition, comparison, latest data, authoritative source, etc.).
4) Fill 'reason' for each term with a short, practical justification.

Output:
- A WebSearchPlan schema with exactly {HOW_MANY_SEARCHES} search terms. No duplicates.
"""

search_terms_generator_tool = tool_from_agent(
    agent_name="SearchTermsGenerator",
    agent_instructions=SEARCH_TERMS_INSTRUCTIONS,
    output_type=WebSearchPlan,
    tool_name="generate_search_terms",
    tool_description="Generate search terms to best answer the user's query"
)
