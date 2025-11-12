# accounts_server.py
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="Accounts MCP Server")

ACCOUNTS = {"bharat": {"balance": 10000, "holdings": {}}}

class Trade(BaseModel):
    user: str
    ticker: str
    price: float
    qty: int

@app.get("/balance/{user}")
async def get_balance(user: str):
    return ACCOUNTS.get(user, {"balance": 0, "holdings": {}})

@app.post("/buy")
async def buy_stock(t: Trade):
    acct = ACCOUNTS.setdefault(t.user, {"balance": 10000, "holdings": {}})
    total_cost = t.price * t.qty
    if acct["balance"] < total_cost:
        return {"error": "Insufficient balance"}
    acct["balance"] -= total_cost
    acct["holdings"][t.ticker] = acct["holdings"].get(t.ticker, 0) + t.qty
    return {"message": f"Bought {t.qty} of {t.ticker}", "balance": acct["balance"]}

@app.post("/sell")
async def sell_stock(t: Trade):
    acct = ACCOUNTS.setdefault(t.user, {"balance": 10000, "holdings": {}})
    if acct["holdings"].get(t.ticker, 0) < t.qty:
        return {"error": "Insufficient shares"}
    acct["holdings"][t.ticker] -= t.qty
    acct["balance"] += t.price * t.qty
    return {"message": f"Sold {t.qty} of {t.ticker}", "balance": acct["balance"]}
