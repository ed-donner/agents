# quotes_server.py
from fastapi import FastAPI
import random

app = FastAPI(title="Quotes MCP Server")

@app.get("/quote/{ticker}")
async def get_quote(ticker: str):
    price = round(random.uniform(50, 250), 2)
    return {"ticker": ticker.upper(), "price": price}
