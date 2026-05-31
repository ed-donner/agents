from src.database.database import read_company_insights, read_trader_company_insights
import json

def get_company_deep_dive(symbol: str) -> dict:
    insights = read_company_insights(symbol)
    if not insights:
        return {
            "symbol": symbol,
            "total_actions": 0,
            "traders": [],
            "summary": "No trading activity for this company yet."
        }

    trader_insights = {}
    for trader_name, datetime, rationale, action in insights:
        if trader_name not in trader_insights:
            trader_insights[trader_name] = []
        trader_insights[trader_name].append({
            "datetime": datetime,
            "action": action,
            "rationale": rationale
        })

    traders_data = []
    for trader_name, actions in trader_insights.items():
        latest_action = actions[0]
        traders_data.append({
            "trader": trader_name.capitalize(),
            "latest_action": latest_action["action"],
            "datetime": latest_action["datetime"],
            "rationale": latest_action["rationale"],
            "total_trades": len(actions)
        })

    return {
        "symbol": symbol,
        "total_actions": len(insights),
        "traders": traders_data,
    }

def format_company_deep_dive(symbol: str) -> str:
    data = get_company_deep_dive(symbol)

    if data["total_actions"] == 0:
        return f"# {symbol}\n\nNo trading activity yet."

    output = f"# {symbol} - Company Deep Dive\n\n"
    output += f"**Total Trading Actions:** {data['total_actions']}\n\n"

    for trader_data in data["traders"]:
        output += f"## {trader_data['trader']}\n"
        output += f"**Latest Action:** {trader_data['latest_action']} on {trader_data['datetime']}\n"
        output += f"**Total Trades:** {trader_data['total_trades']}\n\n"
        output += f"### Investment Thesis:\n{trader_data['rationale']}\n\n"
        output += "---\n\n"

    return output

def get_all_active_symbols() -> set:
    from src.agents.accounts import Account
    symbols = set()
    for trader_name in ["warren", "george", "ray", "cathie"]:
        account = Account.get(trader_name)
        symbols.update(account.holdings.keys())
    return symbols

def get_trader_symbol_insight(trader_name: str, symbol: str) -> str:
    insights = read_trader_company_insights(trader_name, symbol)
    if not insights:
        return f"No insights available for {symbol}"

    output = f"**{symbol}** - Recent Activity:\n\n"
    for datetime, rationale, action in insights:
        output += f"- **{action}** ({datetime}): {rationale}\n"

    return output
