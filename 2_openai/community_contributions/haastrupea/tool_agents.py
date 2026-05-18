from agents import Agent
from model_client import model_client



#balance Agnet

transaction_id_extractor_agent = Agent(
    model = model_client,
    name="Transaction ID Extractor",
    instructions=(
        "Extract the transaction reference from the user's message. "
        "Return only the transaction ID if found, for example TXN-1002. "
        "If no valid transaction ID is present, return exactly: NOT_FOUND"
    ),
)


#fees Agnet

fee_simplifier_agent = Agent(
    model = model_client,
    name="Fee Simplifier",
    instructions=(
        "You explain fee information in simple user-friendly language. "
        "Keep it brief and practical."
    ),
)


# Turn sub-agents into tools
tx_id_extractor_tool = transaction_id_extractor_agent.as_tool(
    tool_name="extract_transaction_id",
    tool_description="Extract a transaction ID from a user's free-text message",
)

fee_simplifier_tool = fee_simplifier_agent.as_tool(
    tool_name="simplify_fee_explanation",
    tool_description="Turn raw fee data into a simple explanation for the user",
)