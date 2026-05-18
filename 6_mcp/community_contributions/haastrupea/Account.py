from mock_data import USERS, TRANSACTIONS, FEES


class Account():
    users: dict = USERS
    transaction: dict = TRANSACTIONS
    fee: dict = FEES

    @classmethod
    def get_balance(cls, user_id):
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

    @classmethod
    def get_transaction_status(cls, trx_id):
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

    @classmethod
    def get_user_transactions(cls, user_id: str) -> dict:
        user_txs = [
            tx for tx in TRANSACTIONS.values()
            if tx["user_id"] == user_id
        ]

        return {
            "status": "success",
            "count": len(user_txs),
            "transactions": user_txs,
        }

    @classmethod
    def get_fee_explanation(cls, topic: str) -> dict:
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

