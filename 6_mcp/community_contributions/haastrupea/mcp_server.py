from mcp.server.fastmcp import FastMCP
from Account import Account

mcp = FastMCP("transaction_server")

@mcp.tool()
def get_balance(user_id):
    # search mock wallet data
    """
    Get Account balanace of a user by user_id

    Args:
    user_id: user id of the account holder
    """
    return Account.get_balance(user_id)


@mcp.tool()
def get_transaction_status(trx_id):
    """
    Get Transaction status by transaction id

    Args:
    trx_id: transaction id
    """
    # search mock wallet data
    return Account.get_transaction_status(trx_id)

@mcp.tool()
def get_user_transactions(user_id: str) -> dict:
    """
    Get All Transactions belonging to a user by user_id

    Args:
    user_id: user id of the account holder
    """
    return Account.get_user_transactions(user_id)

@mcp.tool()
def get_fee_explanation(topic: str) -> dict:
    """
    Get Transaction fee details based on topic

    Args:
    topic: topic for the category the fee belong to
    """

    return Account.get_fee_explanation(topic)

if __name__ == "__main__":
    mcp.run(transport='stdio')