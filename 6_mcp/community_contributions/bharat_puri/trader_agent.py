# trader_agent.py
import asyncio
import httpx
from mcp_params import MCP_SERVERS
from rich import print

async def trader_cycle(user="bharat", ticker="AAPL"):
    async with httpx.AsyncClient() as client:
        # 1. Get quote
        quote = await client.get(f"{MCP_SERVERS['quotes']}/quote/{ticker}")
        price = quote.json()["price"]
        print(f"[bold blue]Fetched {ticker} quote: {price}[/bold blue]")

        # 2. Get balance
        balance = (await client.get(f"{MCP_SERVERS['accounts']}/balance/{user}")).json()["balance"]
        print(f"[green]{user} balance: {balance}[/green]")

        # 3. Simple trade decision
        if price < 150 and balance > price * 5:
            qty = 5
            print(f"[yellow]Buying {qty} {ticker} @ {price}[/yellow]")
            buy = await client.post(f"{MCP_SERVERS['accounts']}/buy", json={
                "user": user, "ticker": ticker, "price": price, "qty": qty
            })
            print(buy.json())
        else:
            print(f"[red]No trade made for {ticker}[/red]")

async def main():
    while True:
        await trader_cycle("bharat", "AAPL")
        await asyncio.sleep(5)

if __name__ == "__main__":
    asyncio.run(main())

