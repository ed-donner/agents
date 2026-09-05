# Design: Simple Account Management System for Trading Simulation

## Goals

Build a simple in-memory account management system for a trading simulation platform.

The system must allow users to:

- Create an account.
- Deposit funds.
- Withdraw funds.
- Buy shares.
- Sell shares.
- View current holdings.
- View holdings at a point in time.
- View current portfolio value.
- View profit/loss.
- View profit/loss at a point in time.
- List all transactions over time.
- Prevent invalid operations:
  - Withdrawals that would create a negative cash balance.
  - Buying shares without enough cash.
  - Selling more shares than owned.

The system has access to:

```python
get_share_price(symbol: str) -> float
```

The test implementation should return fixed prices for:

- `AAPL`
- `TSLA`
- `GOOGL`

All files must live in the same directory. No packages or subdirectories.

---

# File Structure

All files should be created in the same sandbox directory:

```text
account_backend.py
app.py
test_account_backend.py
```

Optional if desired:

```text
README.md
```

---

# Backend Design

Assigned to: `backend_engineer`

Main backend file:

```text
account_backend.py
```

The backend should contain all business logic and should not depend on Gradio.

The backend should use only the Python standard library.

Recommended standard library modules:

```python
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Callable, Optional, Any
```

---

## Backend Concepts

### Account

An account represents one user's trading simulation account.

Each account tracks:

- Account ID.
- User name.
- Cash balance.
- Holdings by stock symbol.
- Transaction history.
- Initial deposit amount.
- Net cash contributed.

### Holdings

Holdings are represented as:

```python
dict[str, int]
```

Example:

```python
{
    "AAPL": 10,
    "TSLA": 2
}
```

Quantities are whole shares only.

### Cash Balance

Cash balance represents uninvested cash.

### Portfolio Value

Portfolio value is:

```text
cash balance + market value of all current holdings
```

Where market value is:

```text
quantity * get_share_price(symbol)
```

### Profit/Loss

Use this definition:

```text
profit_loss = total_portfolio_value - net_cash_contributed
```

Where:

```text
net_cash_contributed = total deposits - total withdrawals
```

This handles additional deposits and withdrawals correctly.

If the user only makes one deposit, this is equivalent to:

```text
total_portfolio_value - initial deposit
```

### Point-in-Time Reports

The backend should support reporting holdings and profit/loss at a point in time by replaying transactions up to and including the requested timestamp.

Because the provided `get_share_price(symbol)` returns only current prices, not historical prices, point-in-time portfolio value should use:

- The account state as of that timestamp.
- The current price returned by `get_share_price`.

Each transaction should also record the execution price at the time of the trade.

---

# Backend Module: `account_backend.py`

## Constants

```python
SUPPORTED_SYMBOLS: tuple[str, ...]
```

Expected value:

```python
("AAPL", "TSLA", "GOOGL")
```

---

## Price Function

```python
def get_share_price(symbol: str) -> float:
    ...
```

### Behavior

Returns a fixed price for supported symbols.

Suggested fixed prices:

```text
AAPL  = 180.00
TSLA  = 250.00
GOOGL = 140.00
```

### Validation

- Symbol should be normalized to uppercase.
- If symbol is unsupported, raise `UnknownSymbolError`.

---

# Exceptions

Define custom exceptions for business-rule failures.

```python
class AccountError(Exception):
    ...
```

Base exception for all backend errors.

```python
class UnknownSymbolError(AccountError):
    ...
```

Raised when an unsupported symbol is used.

```python
class ValidationError(AccountError):
    ...
```

Raised for invalid input such as negative amounts or zero quantity.

```python
class InsufficientFundsError(AccountError):
    ...
```

Raised when trying to withdraw more cash than available or buy shares without enough cash.

```python
class InsufficientHoldingsError(AccountError):
    ...
```

Raised when trying to sell more shares than currently owned.

```python
class AccountNotInitializedError(AccountError):
    ...
```

Optional. Raised if an operation is attempted before an account exists.

---

# Enum: `TransactionType`

```python
class TransactionType(Enum):
    DEPOSIT = "DEPOSIT"
    WITHDRAWAL = "WITHDRAWAL"
    BUY = "BUY"
    SELL = "SELL"
```

---

# Dataclass: `Transaction`

```python
@dataclass(frozen=True)
class Transaction:
    transaction_id: int
    timestamp: datetime
    transaction_type: TransactionType
    symbol: Optional[str]
    quantity: int
    price: Optional[float]
    cash_amount: float
    cash_balance_after: float
    notes: str = ""
```

## Field Meaning

### `transaction_id`

Sequential transaction number starting at `1`.

### `timestamp`

Time the transaction was recorded.

### `transaction_type`

One of:

```text
DEPOSIT
WITHDRAWAL
BUY
SELL
```

### `symbol`

Stock symbol for buy/sell transactions.

Should be `None` for deposit and withdrawal.

### `quantity`

Number of shares for buy/sell transactions.

Should be `0` for deposit and withdrawal.

### `price`

Share price used for buy/sell transactions.

Should be `None` for deposit and withdrawal.

### `cash_amount`

Cash amount of the transaction.

Use positive numbers for deposits and sell proceeds.

Use negative numbers for withdrawals and buy costs.

Examples:

```text
deposit 1000      => cash_amount = 1000
withdraw 200      => cash_amount = -200
buy 2 AAPL @ 180  => cash_amount = -360
sell 1 AAPL @ 180 => cash_amount = 180
```

### `cash_balance_after`

Cash balance after the transaction.

### `notes`

Optional human-readable description.

---

# Dataclass: `AccountSnapshot`

```python
@dataclass(frozen=True)
class AccountSnapshot:
    account_id: str
    user_name: str
    timestamp: datetime
    cash_balance: float
    holdings: dict[str, int]
    holdings_value: float
    total_portfolio_value: float
    net_cash_contributed: float
    profit_loss: float
```

Used for current and point-in-time reporting.

---

# Dataclass: `Account`

```python
@dataclass
class Account:
    account_id: str
    user_name: str
    cash_balance: float = 0.0
    holdings: dict[str, int] = field(default_factory=dict)
    transactions: list[Transaction] = field(default_factory=list)
    initial_deposit: Optional[float] = None
    total_deposits: float = 0.0
    total_withdrawals: float = 0.0
```

This dataclass stores account state.

The `AccountService` should be responsible for mutating it.

---

# Class: `AccountService`

```python
class AccountService:
    def __init__(
        self,
        account: Account,
        price_lookup: Callable[[str], float] = get_share_price,
    ) -> None:
        ...
```

## Responsibilities

`AccountService` owns business logic for a single account.

It should:

- Validate all operations.
- Update cash.
- Update holdings.
- Record transactions.
- Produce reports and snapshots.
- Replay transactions for point-in-time reporting.

---

## Constructor

```python
def __init__(
    self,
    account: Account,
    price_lookup: Callable[[str], float] = get_share_price,
) -> None:
    ...
```

### Parameters

- `account`: The account to manage.
- `price_lookup`: Function used to get current share prices.

---

## Factory Method: `create_account`

```python
@classmethod
def create_account(
    cls,
    user_name: str,
    account_id: Optional[str] = None,
    price_lookup: Callable[[str], float] = get_share_price,
) -> "AccountService":
    ...
```

### Behavior

Creates a new account service.

### Validation

- `user_name` must be non-empty.
- If `account_id` is omitted, generate one.

Recommended account ID format:

```text
ACC-YYYYMMDDHHMMSS
```

or use `uuid.uuid4()` from the standard library.

---

## Method: `deposit`

```python
def deposit(
    self,
    amount: float,
    timestamp: Optional[datetime] = None,
) -> Transaction:
    ...
```

### Behavior

- Adds cash to the account.
- Records a deposit transaction.
- If this is the first deposit, sets `initial_deposit`.

### Validation

- `amount` must be greater than zero.

---

## Method: `withdraw`

```python
def withdraw(
    self,
    amount: float,
    timestamp: Optional[datetime] = None,
) -> Transaction:
    ...
```

### Behavior

- Removes cash from the account.
- Records a withdrawal transaction.

### Validation

- `amount` must be greater than zero.
- `amount` must not exceed current cash balance.

### Important

This system should only prevent the cash balance from going negative.

It should not force liquidation of holdings.

---

## Method: `buy`

```python
def buy(
    self,
    symbol: str,
    quantity: int,
    timestamp: Optional[datetime] = None,
) -> Transaction:
    ...
```

### Behavior

- Normalizes symbol to uppercase.
- Gets current share price.
- Calculates total cost:

```text
price * quantity
```

- Deducts cost from cash balance.
- Increases holdings.
- Records a buy transaction.

### Validation

- Symbol must be supported.
- Quantity must be a positive integer.
- Total cost must not exceed cash balance.

---

## Method: `sell`

```python
def sell(
    self,
    symbol: str,
    quantity: int,
    timestamp: Optional[datetime] = None,
) -> Transaction:
    ...
```

### Behavior

- Normalizes symbol to uppercase.
- Gets current share price.
- Calculates proceeds:

```text
price * quantity
```

- Adds proceeds to cash balance.
- Decreases holdings.
- Removes symbol from holdings if resulting quantity is zero.
- Records a sell transaction.

### Validation

- Symbol must be supported.
- Quantity must be a positive integer.
- User must own at least `quantity` shares.

---

## Method: `get_cash_balance`

```python
def get_cash_balance(self) -> float:
    ...
```

Returns current cash balance.

---

## Method: `get_holdings`

```python
def get_holdings(self) -> dict[str, int]:
    ...
```

Returns a copy of current holdings.

Must not return the internal mutable dict directly.

---

## Method: `get_holdings_value`

```python
def get_holdings_value(self) -> float:
    ...
```

Returns current market value of all held shares.

---

## Method: `get_total_portfolio_value`

```python
def get_total_portfolio_value(self) -> float:
    ...
```

Returns:

```text
cash balance + holdings value
```

---

## Method: `get_net_cash_contributed`

```python
def get_net_cash_contributed(self) -> float:
    ...
```

Returns:

```text
total_deposits - total_withdrawals
```

---

## Method: `get_profit_loss`

```python
def get_profit_loss(self) -> float:
    ...
```

Returns:

```text
total_portfolio_value - net_cash_contributed
```

---

## Method: `get_transactions`

```python
def get_transactions(self) -> list[Transaction]:
    ...
```

Returns a copy of the transaction list.

Do not return the internal mutable list directly.

---

## Method: `get_snapshot`

```python
def get_snapshot(
    self,
    timestamp: Optional[datetime] = None,
) -> AccountSnapshot:
    ...
```

### Behavior

If `timestamp` is `None`, return current account state.

If `timestamp` is provided, return account state as of that timestamp by replaying transactions up to and including that timestamp.

---

## Method: `get_holdings_at`

```python
def get_holdings_at(
    self,
    timestamp: datetime,
) -> dict[str, int]:
    ...
```

Returns holdings as of the timestamp.

---

## Method: `get_profit_loss_at`

```python
def get_profit_loss_at(
    self,
    timestamp: datetime,
) -> float:
    ...
```

Returns profit/loss as of the timestamp.

---

## Method: `get_transactions_until`

```python
def get_transactions_until(
    self,
    timestamp: datetime,
) -> list[Transaction]:
    ...
```

Returns all transactions with:

```python
transaction.timestamp <= timestamp
```

---

## Private Helper: `_record_transaction`

```python
def _record_transaction(
    self,
    transaction_type: TransactionType,
    symbol: Optional[str],
    quantity: int,
    price: Optional[float],
    cash_amount: float,
    timestamp: Optional[datetime],
    notes: str = "",
) -> Transaction:
    ...
```

### Behavior

Creates a `Transaction`, assigns the next transaction ID, appends it to the account, and returns it.

---

## Private Helper: `_normalize_symbol`

```python
def _normalize_symbol(self, symbol: str) -> str:
    ...
```

### Behavior

- Strips whitespace.
- Converts to uppercase.
- Validates by calling price lookup or checking against supported symbols.

---

## Private Helper: `_validate_positive_amount`

```python
def _validate_positive_amount(
    self,
    amount: float,
    field_name: str = "amount",
) -> None:
    ...
```

---

## Private Helper: `_validate_positive_quantity`

```python
def _validate_positive_quantity(
    self,
    quantity: int,
) -> None:
    ...
```

---

## Private Helper: `_build_snapshot_from_state`

```python
def _build_snapshot_from_state(
    self,
    cash_balance: float,
    holdings: dict[str, int],
    total_deposits: float,
    total_withdrawals: float,
    timestamp: datetime,
) -> AccountSnapshot:
    ...
```

---

## Private Helper: `_replay_until`

```python
def _replay_until(
    self,
    timestamp: datetime,
) -> tuple[float, dict[str, int], float, float]:
    ...
```

### Returns

```python
cash_balance, holdings, total_deposits, total_withdrawals
```

### Behavior

Replay transactions from the beginning through the requested timestamp.

The replay rules are:

- `DEPOSIT`: increase cash, increase total deposits.
- `WITHDRAWAL`: decrease cash, increase total withdrawals.
- `BUY`: decrease cash, increase symbol holdings.
- `SELL`: increase cash, decrease symbol holdings.

---

# Backend Formatting Helpers

These helpers are useful for the frontend and tests.

## Function: `transaction_to_row`

```python
def transaction_to_row(transaction: Transaction) -> list[Any]:
    ...
```

### Returns

A row suitable for a Gradio `Dataframe`.

Suggested columns:

```text
ID
Timestamp
Type
Symbol
Quantity
Price
Cash Amount
Cash Balance After
Notes
```

---

## Function: `transactions_to_rows`

```python
def transactions_to_rows(transactions: list[Transaction]) -> list[list[Any]]:
    ...
```

---

## Function: `holdings_to_rows`

```python
def holdings_to_rows(
    holdings: dict[str, int],
    price_lookup: Callable[[str], float] = get_share_price,
) -> list[list[Any]]:
    ...
```

Suggested columns:

```text
Symbol
Quantity
Current Price
Market Value
```

---

## Function: `snapshot_to_summary`

```python
def snapshot_to_summary(snapshot: AccountSnapshot) -> str:
    ...
```

Returns a readable multiline summary string.

Example content:

```text
Account: ACC-123
User: Alice
Cash Balance: $1,000.00
Holdings Value: $500.00
Total Portfolio Value: $1,500.00
Net Cash Contributed: $1,200.00
Profit/Loss: $300.00
```

---

# Frontend Design

Assigned to: `frontend_engineer`

Frontend file:

```text
app.py
```

The frontend should be a Gradio app using the backend in `account_backend.py`.

The app should be simple, single-user, and in-memory.

No database or file persistence is required.

---

# Gradio 6 API Guidance

Use Gradio 6 compatible APIs.

Import:

```python
import gradio as gr
```

Use:

```python
with gr.Blocks(title="Trading Simulation Account Manager") as demo:
    ...
```

Launch with:

```python
demo.launch()
```

Do not use removed or older Gradio APIs.

## Event Binding

Use:

```python
button.click(fn=handler, inputs=[...], outputs=[...])
```

or:

```python
gr.on(
    triggers=[button.click, textbox.submit],
    fn=handler,
    inputs=[...],
    outputs=[...],
)
```

Valid examples:

```python
create_button.click(
    fn=create_account_handler,
    inputs=[user_name_input],
    outputs=[account_state, status_output, summary_output],
)
```

```python
deposit_button.click(
    fn=deposit_handler,
    inputs=[account_state, deposit_amount_input],
    outputs=[
        account_state,
        status_output,
        summary_output,
        holdings_table,
        transactions_table,
    ],
)
```

## State

Use:

```python
account_state = gr.State(value=None)
```

Handlers should accept the state as an input and return the updated state as the first output if the state changes.

Example signature:

```python
def deposit_handler(
    account_service: AccountService | None,
    amount: float,
) -> tuple[AccountService | None, str, str, list[list[Any]], list[list[Any]]]:
    ...
```

## Components

Recommended components:

```python
gr.Markdown()
gr.Textbox()
gr.Number()
gr.Dropdown()
gr.Button()
gr.Dataframe()
gr.State()
gr.Tabs()
gr.Tab()
gr.Row()
gr.Column()
```

## Gradio 6 Dataframe Change

In Gradio 6, use:

```python
gr.Dataframe(
    headers=[...],
    datatype=[...],
    row_count=0,
    row_limits=None,
    column_count=4,
    column_limits=(4, 4),
    interactive=False,
)
```

Important:

- Use `column_count`, not old `col_count`.
- Use `column_limits`, not old tuple form of `col_count`.
- Use `row_limits`, not old tuple form of `row_count`.

Correct Gradio 6 style:

```python
holdings_table = gr.Dataframe(
    headers=["Symbol", "Quantity", "Current Price", "Market Value"],
    datatype=["str", "number", "number", "number"],
    row_count=0,
    row_limits=None,
    column_count=4,
    column_limits=(4, 4),
    interactive=False,
    label="Holdings",
)
```

For transactions:

```python
transactions_table = gr.Dataframe(
    headers=[
        "ID",
        "Timestamp",
        "Type",
        "Symbol",
        "Quantity",
        "Price",
        "Cash Amount",
        "Cash Balance After",
        "Notes",
    ],
    datatype=[
        "number",
        "str",
        "str",
        "str",
        "number",
        "number",
        "number",
        "number",
        "str",
    ],
    row_count=0,
    row_limits=None,
    column_count=9,
    column_limits=(9, 9),
    interactive=False,
    label="Transactions",
)
```

## Dropdown

Use:

```python
symbol_dropdown = gr.Dropdown(
    choices=["AAPL", "TSLA", "GOOGL"],
    value="AAPL",
    label="Symbol",
    allow_custom_value=False,
)
```

## Number Inputs

Use:

```python
deposit_amount = gr.Number(
    label="Deposit Amount",
    value=1000,
    minimum=0,
)
```

```python
quantity_input = gr.Number(
    label="Quantity",
    value=1,
    minimum=1,
    precision=0,
)
```

If `precision=0` is not accepted in the installed Gradio version, the frontend handler should cast to `int` and validate.

## Updating Components

For simple refreshes, return new values directly.

Use:

```python
return updated_state, status, summary, holdings_rows, transaction_rows
```

Use `gr.update(...)` only when dynamically changing component properties such as choices or visibility.

---

# Frontend Layout

## Top-Level Structure

```text
Trading Simulation Account Manager
----------------------------------

Account Setup
- User Name
- Create Account button
- Status output

Tabs:
1. Account Actions
2. Reports
3. Transactions
```

---

## Components

### Shared State

```python
account_state = gr.State(value=None)
```

Stores `AccountService | None`.

---

## Header

```python
gr.Markdown("# Trading Simulation Account Manager")
```

---

## Account Setup Section

Components:

```python
user_name_input = gr.Textbox(label="User Name", placeholder="Enter your name")
create_account_button = gr.Button("Create Account")
status_output = gr.Textbox(label="Status", interactive=False)
summary_output = gr.Textbox(label="Account Summary", lines=8, interactive=False)
```

---

## Account Actions Tab

### Deposit Section

```python
deposit_amount_input = gr.Number(label="Deposit Amount", value=1000, minimum=0)
deposit_button = gr.Button("Deposit")
```

### Withdraw Section

```python
withdraw_amount_input = gr.Number(label="Withdraw Amount", value=100, minimum=0)
withdraw_button = gr.Button("Withdraw")
```

### Buy Section

```python
buy_symbol_dropdown = gr.Dropdown(
    choices=["AAPL", "TSLA", "GOOGL"],
    value="AAPL",
    label="Buy Symbol",
    allow_custom_value=False,
)
buy_quantity_input = gr.Number(label="Buy Quantity", value=1, minimum=1, precision=0)
buy_button = gr.Button("Buy")
```

### Sell Section

```python
sell_symbol_dropdown = gr.Dropdown(
    choices=["AAPL", "TSLA", "GOOGL"],
    value="AAPL",
    label="Sell Symbol",
    allow_custom_value=False,
)
sell_quantity_input = gr.Number(label="Sell Quantity", value=1, minimum=1, precision=0)
sell_button = gr.Button("Sell")
```

---

## Reports Tab

### Current Holdings Table

```python
holdings_table = gr.Dataframe(
    headers=["Symbol", "Quantity", "Current Price", "Market Value"],
    datatype=["str", "number", "number", "number"],
    row_count=0,
    row_limits=None,
    column_count=4,
    column_limits=(4, 4),
    interactive=False,
    label="Current Holdings",
)
```

### Point-in-Time Report Controls

Use ISO timestamp input as a simple textbox.

```python
report_timestamp_input = gr.Textbox(
    label="Point-in-Time Timestamp",
    placeholder="YYYY-MM-DD HH:MM:SS",
)
point_in_time_button = gr.Button("Generate Point-in-Time Report")
point_in_time_summary_output = gr.Textbox(
    label="Point-in-Time Summary",
    lines=8,
    interactive=False,
)
point_in_time_holdings_table = gr.Dataframe(
    headers=["Symbol", "Quantity", "Current Price", "Market Value"],
    datatype=["str", "number", "number", "number"],
    row_count=0,
    row_limits=None,
    column_count=4,
    column_limits=(4, 4),
    interactive=False,
    label="Point-in-Time Holdings",
)
```

---

## Transactions Tab

```python
transactions_table = gr.Dataframe(
    headers=[
        "ID",
        "Timestamp",
        "Type",
        "Symbol",
        "Quantity",
        "Price",
        "Cash Amount",
        "Cash Balance After",
        "Notes",
    ],
    datatype=[
        "number",
        "str",
        "str",
        "str",
        "number",
        "number",
        "number",
        "number",
        "str",
    ],
    row_count=0,
    row_limits=None,
    column_count=9,
    column_limits=(9, 9),
    interactive=False,
    label="Transactions",
)
```

---

# Frontend Handler Functions

All handler functions should be defined in `app.py`.

They should catch `AccountError` and return user-friendly messages.

---

## Helper: `empty_holdings_rows`

```python
def empty_holdings_rows() -> list[list[Any]]:
    ...
```

Returns:

```python
[]
```

---

## Helper: `empty_transaction_rows`

```python
def empty_transaction_rows() -> list[list[Any]]:
    ...
```

Returns:

```python
[]
```

---

## Helper: `refresh_outputs`

```python
def refresh_outputs(
    account_service: AccountService | None,
) -> tuple[str, list[list[Any]], list[list[Any]]]:
    ...
```

### Returns

```python
summary_text, holdings_rows, transaction_rows
```

### Behavior

If no account exists:

```text
summary_text = "No account created yet."
holdings_rows = []
transaction_rows = []
```

Otherwise:

- Get current snapshot.
- Convert snapshot to summary.
- Convert holdings to rows.
- Convert transactions to rows.

---

## Handler: `create_account_handler`

```python
def create_account_handler(
    user_name: str,
) -> tuple[AccountService | None, str, str, list[list[Any]], list[list[Any]]]:
    ...
```

### Returns

```python
account_state, status_text, summary_text, holdings_rows, transaction_rows
```

### Behavior

- Create new account.
- Return success status.
- Refresh summary/tables.

### Errors

If username is empty, return:

```text
Please enter a user name.
```

---

## Handler: `deposit_handler`

```python
def deposit_handler(
    account_service: AccountService | None,
    amount: float,
) -> tuple[AccountService | None, str, str, list[list[Any]], list[list[Any]]]:
    ...
```

### Returns

```python
account_state, status_text, summary_text, holdings_rows, transaction_rows
```

---

## Handler: `withdraw_handler`

```python
def withdraw_handler(
    account_service: AccountService | None,
    amount: float,
) -> tuple[AccountService | None, str, str, list[list[Any]], list[list[Any]]]:
    ...
```

---

## Handler: `buy_handler`

```python
def buy_handler(
    account_service: AccountService | None,
    symbol: str,
    quantity: float,
) -> tuple[AccountService | None, str, str, list[list[Any]], list[list[Any]]]:
    ...
```

### Notes

Gradio `Number` may pass a float.

Handler should convert:

```python
int(quantity)
```

Backend should still validate quantity.

---

## Handler: `sell_handler`

```python
def sell_handler(
    account_service: AccountService | None,
    symbol: str,
    quantity: float,
) -> tuple[AccountService | None, str, str, list[list[Any]], list[list[Any]]]:
    ...
```

---

## Helper: `parse_timestamp`

```python
def parse_timestamp(timestamp_text: str) -> datetime:
    ...
```

### Accepted Formats

At minimum support:

```text
YYYY-MM-DD HH:MM:SS
```

Optionally also support:

```text
YYYY-MM-DDTHH:MM:SS
```

---

## Handler: `point_in_time_report_handler`

```python
def point_in_time_report_handler(
    account_service: AccountService | None,
    timestamp_text: str,
) -> tuple[str, list[list[Any]]]:
    ...
```

### Returns

```python
point_in_time_summary_text, point_in_time_holdings_rows
```

### Behavior

- Validate account exists.
- Parse timestamp.
- Get snapshot for that timestamp.
- Return summary and holdings rows.

---

## Handler: `refresh_handler`

```python
def refresh_handler(
    account_service: AccountService | None,
) -> tuple[str, list[list[Any]], list[list[Any]]]:
    ...
```

Optional manual refresh button.

Returns:

```python
summary_text, holdings_rows, transaction_rows
```

---

# Frontend Event Wiring

Use this output list consistently for account-changing actions:

```python
main_outputs = [
    account_state,
    status_output,
    summary_output,
    holdings_table,
    transactions_table,
]
```

## Create Account

```python
create_account_button.click(
    fn=create_account_handler,
    inputs=[user_name_input],
    outputs=main_outputs,
)
```

## Deposit

```python
deposit_button.click(
    fn=deposit_handler,
    inputs=[account_state, deposit_amount_input],
    outputs=main_outputs,
)
```

## Withdraw

```python
withdraw_button.click(
    fn=withdraw_handler,
    inputs=[account_state, withdraw_amount_input],
    outputs=main_outputs,
)
```

## Buy

```python
buy_button.click(
    fn=buy_handler,
    inputs=[account_state, buy_symbol_dropdown, buy_quantity_input],
    outputs=main_outputs,
)
```

## Sell

```python
sell_button.click(
    fn=sell_handler,
    inputs=[account_state, sell_symbol_dropdown, sell_quantity_input],
    outputs=main_outputs,
)
```

## Point-in-Time Report

```python
point_in_time_button.click(
    fn=point_in_time_report_handler,
    inputs=[account_state, report_timestamp_input],
    outputs=[point_in_time_summary_output, point_in_time_holdings_table],
)
```

---

# Unit Test Design

Assigned to: `test_engineer`

Test file:

```text
test_account_backend.py
```

Use Python standard library `unittest`.

Do not require pytest.

Run tests with:

```bash
uv run python -m unittest test_account_backend.py
```

---

# Test Coverage Requirements

The test engineer should write tests for backend behavior only.

Do not test Gradio UI directly.

---

## Test Class: `TestPriceLookup`

```python
class TestPriceLookup(unittest.TestCase):
    ...
```

### Tests

```python
def test_get_share_price_known_symbols(self) -> None:
    ...
```

Verify:

- `AAPL` returns expected fixed price.
- `TSLA` returns expected fixed price.
- `GOOGL` returns expected fixed price.

```python
def test_get_share_price_is_case_insensitive(self) -> None:
    ...
```

Verify:

- `aapl` works.
- `tsla` works.
- `googl` works.

```python
def test_get_share_price_unknown_symbol_raises(self) -> None:
    ...
```

Verify unsupported symbol raises `UnknownSymbolError`.

---

## Test Class: `TestAccountCreation`

```python
class TestAccountCreation(unittest.TestCase):
    ...
```

### Tests

```python
def test_create_account(self) -> None:
    ...
```

Verify:

- Account is created.
- User name is set.
- Cash balance is zero.
- Holdings are empty.
- Transactions are empty.

```python
def test_create_account_requires_user_name(self) -> None:
    ...
```

Verify empty username raises `ValidationError`.

---

## Test Class: `TestDepositsAndWithdrawals`

```python
class TestDepositsAndWithdrawals(unittest.TestCase):
    ...
```

### Setup

```python
def setUp(self) -> None:
    ...
```

Create account.

### Tests

```python
def test_deposit_increases_cash(self) -> None:
    ...
```

Verify:

- Cash increases by deposited amount.
- Transaction is recorded.
- Initial deposit is set for first deposit.

```python
def test_multiple_deposits_update_total_deposits(self) -> None:
    ...
```

Verify:

- Total deposits accumulates.
- Net cash contributed updates.

```python
def test_deposit_requires_positive_amount(self) -> None:
    ...
```

Verify zero and negative deposit raise `ValidationError`.

```python
def test_withdraw_decreases_cash(self) -> None:
    ...
```

Verify cash decreases.

```python
def test_withdraw_requires_positive_amount(self) -> None:
    ...
```

Verify zero and negative withdrawals raise `ValidationError`.

```python
def test_withdraw_cannot_exceed_cash_balance(self) -> None:
    ...
```

Verify `InsufficientFundsError`.

```python
def test_withdraw_updates_net_cash_contributed(self) -> None:
    ...
```

Example:

- Deposit `1000`.
- Withdraw `200`.
- Net cash contributed should be `800`.

---

## Test Class: `TestBuySell`

```python
class TestBuySell(unittest.TestCase):
    ...
```

### Setup

```python
def setUp(self) -> None:
    ...
```

Create account and deposit funds.

### Tests

```python
def test_buy_reduces_cash_and_adds_holdings(self) -> None:
    ...
```

Example:

- Deposit `1000`.
- Buy `2 AAPL` at `180`.
- Cash should be `640`.
- Holdings should be `{"AAPL": 2}`.

```python
def test_buy_records_transaction(self) -> None:
    ...
```

Verify transaction type, symbol, quantity, price, cash amount.

```python
def test_buy_requires_positive_quantity(self) -> None:
    ...
```

Verify zero and negative quantity raise `ValidationError`.

```python
def test_buy_cannot_exceed_cash(self) -> None:
    ...
```

Verify buying too many shares raises `InsufficientFundsError`.

```python
def test_buy_unknown_symbol_raises(self) -> None:
    ...
```

Verify `UnknownSymbolError`.

```python
def test_sell_increases_cash_and_reduces_holdings(self) -> None:
    ...
```

Example:

- Deposit `1000`.
- Buy `2 AAPL`.
- Sell `1 AAPL`.
- Holdings should be `{"AAPL": 1}`.
- Cash should increase by `180`.

```python
def test_sell_removes_symbol_when_quantity_zero(self) -> None:
    ...
```

After selling all shares, symbol should not remain with quantity zero.

```python
def test_sell_requires_positive_quantity(self) -> None:
    ...
```

Verify zero and negative quantity raise `ValidationError`.

```python
def test_sell_cannot_exceed_holdings(self) -> None:
    ...
```

Verify `InsufficientHoldingsError`.

```python
def test_sell_unknown_symbol_raises(self) -> None:
    ...
```

---

## Test Class: `TestPortfolioValueAndProfitLoss`

```python
class TestPortfolioValueAndProfitLoss(unittest.TestCase):
    ...
```

### Tests

```python
def test_portfolio_value_cash_only(self) -> None:
    ...
```

Example:

- Deposit `1000`.
- Portfolio value should be `1000`.

```python
def test_portfolio_value_with_holdings(self) -> None:
    ...
```

Example:

- Deposit `1000`.
- Buy `2 AAPL`.
- Portfolio value should still be `1000` if price unchanged.

```python
def test_profit_loss_no_price_change(self) -> None:
    ...
```

Example:

- Deposit `1000`.
- Buy shares at fixed current price.
- Profit/loss should be `0`.

```python
def test_profit_loss_after_withdrawal_uses_net_cash_contributed(self) -> None:
    ...
```

Example:

- Deposit `1000`.
- Withdraw `200`.
- Portfolio value `800`.
- Net cash contributed `800`.
- Profit/loss `0`.

```python
def test_profit_loss_with_custom_price_lookup(self) -> None:
    ...
```

Use injected price lookup where trade price and current price differ.

Suggested approach:

- Create account with price lookup returning `100` initially.
- Buy `5 TEST` if using custom symbol support is allowed, or use AAPL with custom lookup.
- Change lookup to return `120`.
- Portfolio value should reflect new price.
- Profit/loss should reflect unrealized gain.

Implementation note for backend engineer:

- If supporting only fixed symbols in `_normalize_symbol`, this test should use `AAPL` and custom lookup.
- The backend should allow custom price lookup for supported symbols.

---

## Test Class: `TestSnapshotsAndPointInTimeReports`

```python
class TestSnapshotsAndPointInTimeReports(unittest.TestCase):
    ...
```

### Tests

```python
def test_get_current_snapshot(self) -> None:
    ...
```

Verify snapshot fields match current account.

```python
def test_holdings_at_timestamp(self) -> None:
    ...
```

Use explicit timestamps.

Example:

- `t1`: deposit.
- `t2`: buy 2 AAPL.
- `t3`: buy 1 TSLA.
- Holdings at `t2` should include AAPL only.
- Holdings at `t3` should include both.

```python
def test_profit_loss_at_timestamp(self) -> None:
    ...
```

Verify profit/loss is calculated from replayed state.

```python
def test_transactions_until_timestamp(self) -> None:
    ...
```

Verify only transactions up to requested timestamp are included.

```python
def test_snapshot_before_any_transactions(self) -> None:
    ...
```

Verify:

- Cash is zero.
- Holdings are empty.
- Portfolio value is zero.
- Profit/loss is zero.

---

## Test Class: `TestTransactionFormatting`

```python
class TestTransactionFormatting(unittest.TestCase):
    ...
```

### Tests

```python
def test_transaction_to_row(self) -> None:
    ...
```

Verify row has expected number of columns and expected values.

```python
def test_transactions_to_rows(self) -> None:
    ...
```

Verify multiple transactions convert to rows.

```python
def test_holdings_to_rows(self) -> None:
    ...
```

Verify holdings rows include:

- Symbol.
- Quantity.
- Current price.
- Market value.

```python
def test_snapshot_to_summary(self) -> None:
    ...
```

Verify summary includes major fields.

---

# Acceptance Criteria

## Backend Acceptance Criteria

The backend is complete when:

- Account creation works.
- Deposits work.
- Withdrawals work.
- Buys work.
- Sells work.
- Invalid withdrawals are rejected.
- Invalid buys are rejected.
- Invalid sells are rejected.
- Holdings are tracked correctly.
- Transactions are recorded in order.
- Portfolio value is calculated correctly.
- Profit/loss is calculated correctly.
- Holdings can be reported for a timestamp.
- Profit/loss can be reported for a timestamp.
- Backend unit tests pass.

---

## Frontend Acceptance Criteria

The frontend is complete when:

- The app launches with:

```bash
uv run python app.py
```

- User can create an account.
- User can deposit funds.
- User can withdraw funds.
- User can buy shares.
- User can sell shares.
- UI displays account summary.
- UI displays holdings table.
- UI displays transaction table.
- UI displays point-in-time report.
- User-friendly errors are shown for invalid operations.
- The app uses Gradio 6 compatible APIs.

---

## Test Acceptance Criteria

The tests are complete when:

- Tests can be run with:

```bash
uv run python -m unittest test_account_backend.py
```

- Tests cover all major backend behavior.
- Tests cover invalid operations.
- Tests cover point-in-time reporting.
- Tests cover transaction formatting helpers.
- All tests pass.

---

# Engineering Assignments

## `backend_engineer`

Create:

```text
account_backend.py
```

Implement:

- `SUPPORTED_SYMBOLS`
- `get_share_price`
- Exceptions:
  - `AccountError`
  - `UnknownSymbolError`
  - `ValidationError`
  - `InsufficientFundsError`
  - `InsufficientHoldingsError`
  - `AccountNotInitializedError`
- `TransactionType`
- `Transaction`
- `AccountSnapshot`
- `Account`
- `AccountService`
- Formatting helpers:
  - `transaction_to_row`
  - `transactions_to_rows`
  - `holdings_to_rows`
  - `snapshot_to_summary`

Focus on correctness and clean business logic.

Do not import Gradio in the backend.

---

## `frontend_engineer`

Create:

```text
app.py
```

Implement Gradio app using:

```python
import gradio as gr
```

Import backend objects from:

```python
from account_backend import ...
```

Implement:

- Account state using `gr.State(value=None)`.
- Create account UI.
- Deposit UI.
- Withdraw UI.
- Buy UI.
- Sell UI.
- Current holdings table.
- Transactions table.
- Current account summary.
- Point-in-time report UI.
- Handler functions listed above.
- Error handling for backend exceptions.

Use Gradio 6 `Dataframe` parameters:

```python
column_count
column_limits
row_count
row_limits
```

Do not use older `col_count` APIs.

---

## `test_engineer`

Create:

```text
test_account_backend.py
```

Use:

```python
import unittest
```

Implement unit tests for:

- Price lookup.
- Account creation.
- Deposits.
- Withdrawals.
- Buying.
- Selling.
- Portfolio value.
- Profit/loss.
- Point-in-time snapshots.
- Transaction list.
- Formatting helpers.
- Invalid operation handling.

Run with:

```bash
uv run python -m unittest test_account_backend.py
```

Coordinate with `backend_engineer` if signatures or exception names need clarification, but the signatures in this design should be treated as the source of truth.