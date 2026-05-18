from agents import Agent
from model_client import model_client

from tools import get_balance, get_transaction_status, get_fee_explanation

from tool_agents import tx_id_extractor_tool, fee_simplifier_tool



#balance Agnet

balance_agent = Agent(
    model = model_client,
    name="Balance Agent",
    handoff_description="Handles wallet balance questions",
    instructions=(
        "You handle only balance-related requests. "
        "Use get_balance when needed. "
        "Assume the demo user_id is user_001 unless the user explicitly provides another user_id. "
        "Be direct."
    ),
    tools=[get_balance],
)

#transaction Agnet
transaction_agent = Agent(
    model = model_client,
    name="Transaction Agent",
    handoff_description="Handles transaction status questions",
    instructions=(
        "You handle only transaction-status questions. "
        "First use extract_transaction_id if the transaction reference is embedded in free text or unclear. "
        "If the user directly provides a valid transaction ID, you may use it. "
        "Then call get_transaction_status. "
        "If no transaction ID can be found, tell the user to provide one. "
        "Be concise and clear."
    ),
    tools=[get_transaction_status, tx_id_extractor_tool],
)

#fees Agnet

fees_agent = Agent(
    model = model_client,
    name="Fees Agent",
    handoff_description="Handles fee questions",
    instructions=(
        "You handle only fee-related questions. "
        "Use get_fee_explanation to fetch the rule"
        "Provide only the transaction fee for the Following transaction types:  transfer, withdrawal, and deposit"
        "Then use simplify_fee_explanation when it would help make the answer clearer. "
        "Keep the final answer short and easy to understand."
    ),
    tools=[get_fee_explanation, fee_simplifier_tool],
)

#Triaging agents
manager = Agent(
    model = model_client,
    name="Fintech Triage Agent",
    instructions=(
        "You are the first-line routing agent for a wallet support system. "
        "Your job is to decide whether the user's request is about balance, transaction status, or fees. "
        "Do not answer specialist questions yourself. "
        "Hand off to the most appropriate specialist."
    ),
    handoffs=[balance_agent, transaction_agent, fees_agent],
)