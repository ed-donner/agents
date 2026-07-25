from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import BaseModel, Field, RootModel
from typing import List


DEFAULT_STRATEGY = "momentum: Buy stocks that are going up, sell when they start going down. Ride the trend."
INITIAL_BALANCE = 10000.0

class Settings(BaseSettings):

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")
    openai_api_key: str = ""
    openrouter_api_key: str = ""
    openrouter_base_url: str = ""
    ollama_base_url: str = ""

    hf_token: str = ""
    hf_base_url: str = ""

    pushover_user_key: str = ""
    pushover_app_token: str = ""
    pushover_url: str = "https://api.pushover.net/1/messages.json"

    mailgun_api_key: str = ""
    mailgun_domain: str = ""
    mailgun_from_email: str = ""
    mailgun_recipient: str = ""

    serper_api_key: str = ""
    serper_base_url: str = ""
    deepseek_api_key: str = ""
    gemini_api_key: str = ""
    groq_api_key: str = ""
    gemini_base_url: str = ""
    deepseek_base_url: str = ""
    groq_base_url: str = ""


class Transaction(BaseModel):
    symbol: str = Field(..., description="The stock ticker symbol")
    quantity: int = Field(..., description="The number of shares traded")
    price: float = Field(..., description="The price per share")
    timestamp: str = Field(..., description="The timestamp of the transaction")
    rationale: str = Field(..., description="The rationale for the transaction")

    def total(self) -> float:
        return self.quantity * self.price

    def __repr__(self):
        return f"{abs(self.quantity)} shares of {self.symbol} at {self.price} each."


class Holdings(BaseModel):
    symbol: str = Field(..., description="The stock ticker symbol")
    units: int = Field(..., description="Number of units held")
    unit_price: float = Field(..., description="Price per unit at purchase")
    total_cost: float = Field(..., description="Total cost of the holding")


class Account(BaseModel):
    account_id: str = Field(..., description="The ID of the account")
    account_name: str = Field(..., description="The name of the account")
    account_type: str = Field(..., description="The type of the account")
    account_balance: float = Field(default=INITIAL_BALANCE, description="The balance of the account")
    account_currency: str = Field(..., description="The currency of the account")
    account_status: str = Field(..., description="The status of the account")
    account_created_at: str = Field(..., description="The date and time the account was created")
    account_updated_at: str = Field(..., description="The date and time the account was last updated")
    account_holdings: List[Holdings] = Field(default=[], description="The holdings of the account")
    account_strategy: str = Field(default=DEFAULT_STRATEGY, description="The strategy of the account")
    account_transactions: List[Transaction] = Field(default=[], description="The transactions of the account")
    account_memory: List[dict] = Field(default=[], description="The memory of the account")
    account_portfolio_value_time_series: List[tuple[str, float]] = Field(default=[], description="The portfolio value time series of the account")


class Idea(BaseModel):
    symbol: str = Field(..., description="The stock ticker symbol")
    action: str = Field(..., description="The action to take")
    reason: str = Field(..., description="The reason for the action")
    confidence: float = Field(..., description="The confidence in the action")
    price: float = Field(..., description="The price of the stock")

class TradeIdeas(BaseModel):
    trade_ideas: List[Idea] = Field(..., description="The trade ideas for the account")

class Trade(BaseModel):
    approved: bool = Field(..., description="Whether the trade is approved")
    symbol: str = Field(..., description="The stock ticker symbol")
    action: str = Field(..., description="The action to take")
    units: int = Field(..., description="The number of units to trade")
    price: float = Field(..., description="The price of the stock")
    rationale: str = Field(..., description="The rationale for the trade")
    

class Trades(BaseModel):
    trades: List[Trade] = Field(..., description="The approved trades for the account")

class QueryItem(BaseModel):
    q: str = Field(..., description="The query to search for")

class QueryList(RootModel):
    root: List[QueryItem] = Field(..., description="List of search queries to run in parallel")

class SharePriceRequest(BaseModel):
    symbols: list[str] = Field(
        description="List of all stock ticker symbols to fetch prices for e.g. ['AAPL', 'MSFT', 'TSLA']. "
                    "Pass ALL candidate symbols at once — do NOT call this tool more than once per session."
    )

class SharePriceResult(BaseModel):
    prices: dict[str, float] = Field(
        description="Map of ticker symbol to current price in USD e.g. {'AAPL': 189.50, 'MSFT': 415.20}"
    )