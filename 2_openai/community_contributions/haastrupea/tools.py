from agents import Agent, Tool
from agents import function_tool
from mock_data import USERS, TRANSACTIONS, FEES

@function_tool
def get_balance(user_id):
    # search mock wallet data
    user = USERS.get(user_id)

    if not user:
        return {
            "status": "error",
            "message": "User not found"
        }
    
    return {
        "status": "success",
        "user_id": user_id,
        "name": user["name"],
        "currency": user["currency"],
        "balance": user["balance"],
    }


@function_tool
def get_transaction_status(trx_id):
    # search mock wallet data
    tx = TRANSACTIONS.get(trx_id)

    if not tx:
        return {
            "status": "error",
            "message": "Transaction not found",
        }

    return {
        "status": "success",
        "transaction": tx,
    }

@function_tool
def get_user_transactions(user_id: str) -> dict:
    user_txs = [
        tx for tx in TRANSACTIONS.values()
        if tx["user_id"] == user_id
    ]

    return {
        "status": "success",
        "count": len(user_txs),
        "transactions": user_txs,
    }

@function_tool
def get_fee_explanation(topic: str) -> dict:
    topic = topic.lower()
    fee = FEES.get(topic)

    if not fee:
        return {
            "status": "error",
            "message": "Fee type not found",
        }

    return {
        "status": "success",
        "topic": topic,
        "fee": fee,
    }

