
USERS = {
    "user_001": {
        "name": "Elijah Haastrup",
        "currency": "USD",
        "balance": 1250.75,
    },
    "user_002": {
        "name": "Ada Nwankwo",
        "currency": "USD",
        "balance": 320.40,
    },
}

TRANSACTIONS = {
    "TXN-1001": {
        "user_id": "user_001",
        "amount": 250.00,
        "type": "deposit",
        "status": "successful",
        "date": "2026-03-20",
        "reference": "TXN-1001",
        "description": "Card deposit",
    },
    "TXN-1002": {
        "user_id": "user_001",
        "amount": 100.00,
        "type": "transfer",
        "status": "pending",
        "date": "2026-03-22",
        "reference": "TXN-1002",
        "description": "Transfer to John",
    },
    "TXN-1003": {
        "user_id": "user_001",
        "amount": 75.50,
        "type": "withdrawal",
        "status": "failed",
        "date": "2026-03-21",
        "reference": "TXN-1003",
        "description": "Bank withdrawal",
        "failure_reason": "Insufficient liquidity from partner bank",
    },
    "TXN-2001": {
        "user_id": "user_002",
        "amount": 500.00,
        "type": "deposit",
        "status": "successful",
        "date": "2026-03-18",
        "reference": "TXN-2001",
        "description": "Crypto deposit",
    },
}

FEES = {
    "deposit": {
        "type": "percentage",
        "value": 1.0,
        "description": "1% fee applied to card deposits",
    },
    "withdrawal": {
        "type": "fixed",
        "value": 2.5,
        "description": "Flat $2.5 withdrawal fee",
    },
    "transfer": {
        "type": "none",
        "value": 0,
        "description": "Internal transfers are free",
    },
}