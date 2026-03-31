from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path

from mcp.server.fastmcp import FastMCP

INITIAL_BALANCE = 1_000.0
DATA_PATH = Path(__file__).resolve().parent / "betting_demo_data.json"


@dataclass
class BetRecord:
    match_id: str
    match_label: str
    pick: str
    stake: float
    rationale: str
    placed_at: str
    decimal_odds_taken: float | None = None
    bet_on_market_favorite: bool | None = None
    league_context: str = ""


@dataclass
class BetAccount:
    name: str
    balance: float
    strategy: str
    bets: list[BetRecord] = field(default_factory=list)

    def report(self) -> str:
        lines = [
            f"Account: {self.name}",
            f"Balance (demo units): {self.balance:.2f}",
            f"Strategy: {self.strategy or '(none)'}",
            f"Bets recorded: {len(self.bets)}",
        ]
        if self.bets:
            lines.append("Recent bets:")
            for b in self.bets[-8:]:
                odds = f" @{b.decimal_odds_taken}" if b.decimal_odds_taken else ""
                lines.append(
                    f"  - {b.placed_at} | {b.match_label} | {b.pick} stake={b.stake:.2f}{odds} | {b.rationale[:100]}..."
                )
        return "\n".join(lines)

    def place_bet(
        self,
        match_id: str,
        match_label: str,
        pick: str,
        stake: float,
        rationale: str,
        decimal_odds_taken: float | None = None,
        bet_on_market_favorite: bool | None = None,
        league_context: str = "",
    ) -> float:
        if stake <= 0:
            raise ValueError("Stake must be positive.")
        if stake > self.balance:
            raise ValueError("Insufficient demo balance.")
        self.balance -= stake
        self.bets.append(
            BetRecord(
                match_id=match_id,
                match_label=match_label,
                pick=pick,
                stake=stake,
                rationale=rationale,
                placed_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                decimal_odds_taken=decimal_odds_taken,
                bet_on_market_favorite=bet_on_market_favorite,
                league_context=league_context or "",
            )
        )
        _save_accounts()
        return self.balance

    def change_strategy(self, strategy: str) -> str:
        self.strategy = strategy
        _save_accounts()
        return f"Strategy updated for {self.name}."


def default_accounts() -> dict[str, BetAccount]:
    return {
        "blair": BetAccount("blair", INITIAL_BALANCE, "cautious"),
        "casey": BetAccount("casey", INITIAL_BALANCE, "balanced"),
    }


def _load_accounts() -> dict[str, BetAccount]:
    if not DATA_PATH.exists():
        return default_accounts()
    raw = json.loads(DATA_PATH.read_text())
    out: dict[str, BetAccount] = {}
    for name, d in raw.items():
        bets = []
        for b in d.get("bets", []):
            bets.append(
                BetRecord(
                    match_id=b["match_id"],
                    match_label=b["match_label"],
                    pick=b["pick"],
                    stake=b["stake"],
                    rationale=b["rationale"],
                    placed_at=b["placed_at"],
                    decimal_odds_taken=b.get("decimal_odds_taken"),
                    bet_on_market_favorite=b.get("bet_on_market_favorite"),
                    league_context=b.get("league_context") or "",
                )
            )
        out[name] = BetAccount(
            name=d["name"],
            balance=d["balance"],
            strategy=d.get("strategy", ""),
            bets=bets,
        )
    return out


def _save_accounts() -> None:
    data = {}
    for name, acc in _accounts.items():
        data[name] = {
            "name": acc.name,
            "balance": acc.balance,
            "strategy": acc.strategy,
            "bets": [asdict(b) for b in acc.bets],
        }
    DATA_PATH.write_text(json.dumps(data, indent=2))


_accounts: dict[str, BetAccount] = _load_accounts()
if not DATA_PATH.exists():
    _save_accounts()


def get_account(name: str) -> BetAccount:
    key = name.strip().lower()
    if key not in _accounts:
        _accounts[key] = BetAccount(key, INITIAL_BALANCE, "")
        _save_accounts()
    return _accounts[key]



mcp = FastMCP("betting_server")

DEMO_MATCHES = [
    {
        "match_id": "demo-001",
        "label": "Arsenal vs Chelsea",
        "odds_home": 1.95,
        "odds_draw": 3.50,
        "odds_away": 4.10,
    },
    {
        "match_id": "demo-002",
        "label": "Manchester United vs Liverpool",
        "odds_home": 3.20,
        "odds_draw": 3.30,
        "odds_away": 2.15,
    },
]


def _favorite_side(h: float, d: float, a: float) -> str:
    return min(("home", h), ("draw", d), ("away", a), key=lambda x: x[1])[0]

@mcp.tool()
async def get_demo_matches() -> str:
    """Fictional 1X2 odds. Field favorite_side_by_odds is the shortest decimal (popular side)."""
    rows = []
    for row in DEMO_MATCHES:
        h, d_, a = row["odds_home"], row["odds_draw"], row["odds_away"]
        rows.append({**row, "favorite_side_by_odds": _favorite_side(h, d_, a)})
    return json.dumps(rows, indent=2)


@mcp.tool()
async def get_balance(account_name: str) -> float:
    """Demo balance for account_name."""
    return get_account(account_name).balance


@mcp.tool()
async def place_bet(
    account_name: str,
    match_id: str,
    match_label: str,
    pick: str,
    stake: float,
    rationale: str,
    decimal_odds_taken: float | None = None,
    bet_on_market_favorite: bool | None = None,
    league_context: str = "",
) -> str:
    """Place one demo bet. pick: home | draw | away. stake max 50 recommended."""
    acc = get_account(account_name)
    bal = acc.place_bet(
        match_id,
        match_label,
        pick,
        stake,
        rationale,
        decimal_odds_taken=decimal_odds_taken,
        bet_on_market_favorite=bet_on_market_favorite,
        league_context=league_context,
    )
    return json.dumps({"ok": True, "new_balance": bal, "account": acc.name}, indent=2)


@mcp.tool()
async def reset_demo_ledger() -> str:
    """Delete saved JSON and reload default demo accounts."""
    global _accounts
    if DATA_PATH.exists():
        DATA_PATH.unlink()
    _accounts = _load_accounts()
    _save_accounts()
    return "Demo ledger reset."


@mcp.resource("betting://account/{name}")
async def read_betting_account(name: str) -> str:
    return get_account(name).report()


if __name__ == "__main__":
    mcp.run(transport="stdio")
