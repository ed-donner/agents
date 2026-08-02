# Design: Simple Account Management System for Trading Simulation

## Goals

Build a simple in-memory account management system for a trading simulation platform.

The system must allow a user to:

- Create an account.
- Deposit funds.
- Withdraw funds.
- Buy shares by symbol and quantity.
- Sell shares by symbol and quantity.
- View current holdings.
- View holdings at a point in time.
- View current portfolio value.
- View profit/loss from the initial deposit.
- View profit/loss at a point in time.
- List all transactions over time.
- Prevent invalid operations:
  - Withdrawals that make cash balance negative.
  - Buys that exceed available cash.
  - Sells that exceed owned quantity.

The system has access to:

```python
get_share_price(symbol: str) -> Decimal
```

A test implementation should return fixed prices for:

- `AAPL`
- `TSLA`
- `GOOGL`

No persistence is required. State can live in memory for the duration of the Gradio session.

---

# File Structure

All files must be in the same sandbox directory.

```text
backend.py
share_prices.py
app.py
test_backend.py
```

No subdirectories or packages.

---

# Module: `share_prices.py`

## Responsibility

Provide a simple share price lookup function used by the backend and tests.

Prices are fixed for this project.

## Constants

```python
SUPPORTED_SYMBOLS: tuple[str, ...]
```

Recommended symbols:

```text
AAPL
TSLA
GOOGL
```

```python
FIXED_SHARE_PRICES: dict[str, Decimal]
```

Recommended values:

```text
AAPL  = 150.00
TSLA  = 250.00
GOOGL = 2800.00
```

## Functions

```python
def normalize_symbol(symbol: str) -> str:
    ...
```

### Behavior

- Strips whitespace.
- Converts to uppercase.
- Raises `ValidationError` or `ValueError` if empty.

```python
def get_share_price(symbol: str) -> Decimal:
    ...
```

### Behavior

- Normalizes the symbol.
- Returns the fixed price for supported symbols.
- Raises `UnknownSymbolError` or `ValueError` for unsupported symbols.

---

# Module: `backend.py`

## Responsibility

Contain all domain models, business logic, account operations, calculations, validation, and transaction replay.

The backend should not depend on Gradio.

---

## Core Design Decisions

### Money Representation

Use Python standard library `Decimal` for all money values.

```python
from decimal import Decimal
```

Do not use floats internally for money.

### Quantity Representation

Share quantity should be an integer.

- Buying fractional shares is not required.
- Quantity must be positive.

### In-Memory State

Each account is represented by an `Account` object.

The frontend can store the current `Account` in `gr.State`.

### Transaction Replay

To report holdings or profit/loss at a point in time, replay all transactions whose timestamps are less than or equal to the requested timestamp.

Because only current prices are available through `get_share_price(symbol)`, historical holdings are valued using the current share price at the time the report is generated.

---

# Exceptions

Define custom backend exceptions so the frontend can display clean error messages.

```python
class AccountError(Exception):
    ...
```

Base exception for all account-related errors.

```python
class ValidationError(AccountError):
    ...
```

Raised when user input is invalid.

Examples:

- Empty account name.
- Deposit amount is zero or negative.
- Withdrawal amount is zero or negative.
- Quantity is zero or negative.
- Invalid timestamp format.

```python
class InsufficientFundsError(AccountError):
    ...
```

Raised when:

- A withdrawal would leave cash negative.
- A buy order costs more than available cash.

```python
class InsufficientSharesError(AccountError):
    ...
```

Raised when trying to sell more shares than currently owned.

```python
class UnknownSymbolError(AccountError):
    ...
```

Raised when a symbol does not exist in the fixed price lookup.

```python
class AccountNotCreatedError(AccountError):
    ...
```

Used by frontend handlers if the user attempts an operation before creating an account.

---

# Enums

```python
class TransactionType(str, Enum):
    CREATE_ACCOUNT = "CREATE_ACCOUNT"
    DEPOSIT = "DEPOSIT"
    WITHDRAW = "WITHDRAW"
    BUY = "BUY"
    SELL = "SELL"
```

---

# Data Classes

## `Transaction`

```python
@dataclass(frozen=True)
class Transaction:
    id: int
    timestamp: datetime
    type: TransactionType
    amount: Decimal | None = None
    symbol: str | None = None
    quantity: int | None = None
    price: Decimal | None = None
    cash_balance_after: Decimal | None = None
    note: str = ""
```

### Field Meaning

| Field | Meaning |
|---|---|
| `id` | Monotonic transaction ID starting at 1 |
| `timestamp` | Time transaction occurred |
| `type` | Transaction type |
| `amount` | Cash amount for deposits/withdrawals, or total trade value for buys/sells |
| `symbol` | Share symbol for buys/sells |
| `quantity` | Number of shares bought/sold |
| `price` | Share price used for trade |
| `cash_balance_after` | Cash balance after transaction |
| `note` | Optional human-readable detail |

---

## `Holding`

```python
@dataclass(frozen=True)
class Holding:
    symbol: str
    quantity: int
    current_price: Decimal
    market_value: Decimal
```

---

## `PortfolioSnapshot`

```python
@dataclass(frozen=True)
class PortfolioSnapshot:
    account_name: str
    as_of: datetime
    cash_balance: Decimal
    holdings: dict[str, int]
    holding_values: list[Holding]
    total_holdings_value: Decimal
    total_portfolio_value: Decimal
    initial_deposit: Decimal
    net_cash_contributions: Decimal
    profit_loss_from_initial_deposit: Decimal
    profit_loss_from_net_contributions: Decimal
```

### Profit/Loss Definitions

The system should expose both calculations to avoid ambiguity.

```text
profit_loss_from_initial_deposit =
    total_portfolio_value - initial_deposit
```

```text
net_cash_contributions =
    all deposits, including initial deposit, minus all withdrawals
```

```text
profit_loss_from_net_contributions =
    total_portfolio_value - net_cash_contributions
```

The UI should label both clearly.

---

## `Account`

```python
@dataclass
class Account:
    name: str
    initial_deposit: Decimal
    cash_balance: Decimal
    holdings: dict[str, int]
    transactions: list[Transaction]
    created_at: datetime
    next_transaction_id: int = 1
```

### Invariants

- `cash_balance >= 0`
- `initial_deposit >= 0`
- Holdings never contain negative quantities.
- Symbols in holdings are normalized uppercase symbols.
- Transaction IDs are unique and increasing.

---

# Backend Service Class

## `AccountService`

The main API used by the Gradio frontend and backend tests.

```python
class AccountService:
    def __init__(self, price_provider: Callable[[str], Decimal]) -> None:
        ...
```

### Constructor Behavior

- Stores the injected price provider.
- Tests can inject the fixed `get_share_price`.
- Future implementations could inject a real price service.

---

## Account Creation

```python
def create_account(
    self,
    name: str,
    initial_deposit: Decimal | int | float | str,
    timestamp: datetime | None = None,
) -> Account:
    ...
```

### Behavior

- Validates name is non-empty.
- Converts `initial_deposit` to `Decimal`.
- Requires `initial_deposit >= 0`.
- Creates an `Account`.
- Sets `cash_balance = initial_deposit`.
- Creates a `CREATE_ACCOUNT` transaction.
- If `initial_deposit > 0`, either:
  - Record the amount on the `CREATE_ACCOUNT` transaction, or
  - Also add a `DEPOSIT` transaction.
- Recommended: one `CREATE_ACCOUNT` transaction with `amount=initial_deposit`.

---

## Deposits

```python
def deposit(
    self,
    account: Account,
    amount: Decimal | int | float | str,
    timestamp: datetime | None = None,
) -> Account:
    ...
```

### Behavior

- Requires `amount > 0`.
- Increases `cash_balance`.
- Appends a `DEPOSIT` transaction.
- Returns the mutated `Account`.

---

## Withdrawals

```python
def withdraw(
    self,
    account: Account,
    amount: Decimal | int | float | str,
    timestamp: datetime | None = None,
) -> Account:
    ...
```

### Behavior

- Requires `amount > 0`.
- Rejects withdrawal if `amount > account.cash_balance`.
- Decreases `cash_balance`.
- Appends a `WITHDRAW` transaction.
- Raises `InsufficientFundsError` if withdrawal would make cash negative.
- Returns the mutated `Account`.

---

## Buying Shares

```python
def buy(
    self,
    account: Account,
    symbol: str,
    quantity: int | str,
    timestamp: datetime | None = None,
) -> Account:
    ...
```

### Behavior

- Normalizes symbol.
- Requires `quantity > 0`.
- Gets current share price from `price_provider`.
- Calculates:

```text
total_cost = price * quantity
```

- Rejects buy if `total_cost > account.cash_balance`.
- Decreases cash balance by total cost.
- Increases holdings for the symbol.
- Appends a `BUY` transaction.
- Raises `InsufficientFundsError` if cash is insufficient.
- Returns the mutated `Account`.

---

## Selling Shares

```python
def sell(
    self,
    account: Account,
    symbol: str,
    quantity: int | str,
    timestamp: datetime | None = None,
) -> Account:
    ...
```

### Behavior

- Normalizes symbol.
- Requires `quantity > 0`.
- Gets current share price from `price_provider`.
- Rejects sell if currently held quantity is less than requested quantity.
- Decreases holdings for the symbol.
- Removes symbol from holdings if quantity becomes zero.
- Increases cash balance by:

```text
sale_proceeds = price * quantity
```

- Appends a `SELL` transaction.
- Raises `InsufficientSharesError` if shares are insufficient.
- Returns the mutated `Account`.

---

# Reporting Methods

## Current Holdings

```python
def get_holdings(self, account: Account) -> dict[str, int]:
    ...
```

### Behavior

- Returns a copy of current holdings.
- Excludes zero-quantity symbols.

---

## Holdings at a Point in Time

```python
def get_holdings_at(
    self,
    account: Account,
    as_of: datetime,
) -> dict[str, int]:
    ...
```

### Behavior

- Replays transactions up to and including `as_of`.
- Returns holdings after those transactions.
- Only `BUY` and `SELL` transactions affect holdings.

---

## Cash Balance at a Point in Time

```python
def get_cash_balance_at(
    self,
    account: Account,
    as_of: datetime,
) -> Decimal:
    ...
```

### Behavior

- Replays transactions up to and including `as_of`.
- Applies:
  - `CREATE_ACCOUNT`: increases cash by initial amount.
  - `DEPOSIT`: increases cash.
  - `WITHDRAW`: decreases cash.
  - `BUY`: decreases cash by trade amount.
  - `SELL`: increases cash by trade amount.

---

## Current Portfolio Snapshot

```python
def get_portfolio_snapshot(
    self,
    account: Account,
    as_of: datetime | None = None,
) -> PortfolioSnapshot:
    ...
```

### Behavior

- If `as_of is None`, use current account state and current time.
- If `as_of` is provided, replay transactions up to that time.
- Calculates:
  - Cash balance.
  - Holdings.
  - Current price of each held symbol.
  - Market value of each holding.
  - Total holdings value.
  - Total portfolio value.
  - Net cash contributions.
  - Profit/loss from initial deposit.
  - Profit/loss from net contributions.

---

## Profit/Loss Current

```python
def get_profit_loss(
    self,
    account: Account,
    as_of: datetime | None = None,
) -> Decimal:
    ...
```

### Behavior

- Returns `profit_loss_from_initial_deposit` from `get_portfolio_snapshot`.

---

## Transactions

```python
def list_transactions(
    self,
    account: Account,
    as_of: datetime | None = None,
) -> list[Transaction]:
    ...
```

### Behavior

- Returns all transactions if `as_of is None`.
- Returns transactions with `timestamp <= as_of` if `as_of` is provided.
- Return a copy of the transaction list, not the internal list.

---

# Backend Utility Functions

## Decimal Parsing

```python
def parse_money(value: Decimal | int | float | str) -> Decimal:
    ...
```

### Behavior

- Converts input to `Decimal`.
- String inputs should be stripped.
- Reject empty strings.
- Reject non-numeric values.
- Quantize to two decimal places if desired.
- Raises `ValidationError` on failure.

---

## Quantity Parsing

```python
def parse_quantity(value: int | str) -> int:
    ...
```

### Behavior

- Converts string/int input to integer.
- Rejects empty string.
- Rejects floats.
- Rejects zero and negative values.
- Raises `ValidationError` on failure.

---

## Timestamp Parsing

```python
def parse_datetime(value: str | datetime | None) -> datetime | None:
    ...
```

### Behavior

- `None` or empty string returns `None`.
- `datetime` returns itself.
- String input should support ISO-like formats:

```text
YYYY-MM-DD
YYYY-MM-DD HH:MM
YYYY-MM-DD HH:MM:SS
```

- Raises `ValidationError` if parsing fails.

---

## Symbol Normalization

```python
def normalize_symbol(symbol: str) -> str:
    ...
```

### Behavior

- Strip whitespace.
- Uppercase.
- Reject empty values.

---

## Formatting Helpers

These are useful for frontend display and tests.

```python
def format_money(value: Decimal) -> str:
    ...
```

Expected display format:

```text
$1,234.56
```

```python
def transaction_to_row(transaction: Transaction) -> list[str]:
    ...
```

Returns a row suitable for a Gradio `Dataframe`.

Recommended columns:

```text
ID
Timestamp
Type
Symbol
Quantity
Price
Amount
Cash After
Note
```

```python
def holding_to_row(holding: Holding) -> list[str]:
    ...
```

Recommended columns:

```text
Symbol
Quantity
Current Price
Market Value
```

```python
def snapshot_to_summary_lines(snapshot: PortfolioSnapshot) -> list[str]:
    ...
```

Returns display lines for account summary.

---

# Module: `app.py`

## Responsibility

Create the Gradio frontend.

The frontend should call only `AccountService` methods and backend formatting helpers.

The frontend should not duplicate business rules.

---

# Gradio 6 API Guidance for `frontend_engineer`

Use:

```python
import gradio as gr
```

## Blocks

In Gradio 6, app-level parameters such as `theme` and `css` should be passed to `launch()`, not to `gr.Blocks()`.

Use:

```python
with gr.Blocks() as demo:
    ...
```

Then:

```python
demo.launch(
    theme=...,
    css=...,
    show_error=True,
)
```

Do **not** use old-style:

```python
gr.Blocks(theme=..., css=...)
```

## Events

Button event handlers should use:

```python
button.click(
    fn=handler_function,
    inputs=[...],
    outputs=[...],
)
```

This is valid in Gradio 6.

You may also use:

```python
gr.on(
    triggers=[button.click, textbox.submit],
    fn=handler_function,
    inputs=[...],
    outputs=[...],
)
```

But for this project, simple `button.click(...)` is preferred.

## State

Use `gr.State` for the current account.

```python
account_state = gr.State(value=None)
```

Event handlers that mutate the account should take the current account from state and return the updated account back to state.

## Component Constructor Guidance

Use current Gradio component names:

```python
gr.Markdown(...)
gr.Textbox(label=..., value=..., interactive=...)
gr.Number(label=..., value=..., precision=...)
gr.Dropdown(choices=..., value=..., label=..., allow_custom_value=...)
gr.Button(...)
gr.Dataframe(headers=..., value=..., interactive=False)
gr.State(value=...)
```

### Important Notes

- Prefer `gr.Textbox` for money inputs to avoid float precision issues from browser number inputs.
- For quantity, `gr.Number(precision=0)` is acceptable, but backend still must validate integer quantity.
- For symbol selection, use `gr.Dropdown`.
- Use `allow_custom_value=False` if only supported symbols should be selectable.
- Use `interactive=False` for output-only fields and tables.
- Dataframes can be updated by returning a list of rows.

---

# Gradio UI Layout

Recommended layout:

## Header

```text
Trading Simulation Account Manager
```

## Account Creation Section

Inputs:

```python
account_name_input: gr.Textbox
initial_deposit_input: gr.Textbox
create_account_button: gr.Button
```

Outputs:

```python
status_output: gr.Markdown
account_summary_output: gr.Markdown
account_state: gr.State
```

## Cash Operations Section

Inputs:

```python
cash_amount_input: gr.Textbox
deposit_button: gr.Button
withdraw_button: gr.Button
```

Outputs:

```python
status_output
account_summary_output
holdings_table
transactions_table
account_state
```

## Trade Section

Inputs:

```python
symbol_input: gr.Dropdown
quantity_input: gr.Number
buy_button: gr.Button
sell_button: gr.Button
```

Outputs:

```python
status_output
account_summary_output
holdings_table
transactions_table
account_state
```

## Reports Section

Inputs:

```python
as_of_input: gr.Textbox
refresh_button: gr.Button
```

`as_of_input` should tell the user:

```text
Optional timestamp: YYYY-MM-DD HH:MM:SS
```

Outputs:

```python
account_summary_output
holdings_table
transactions_table
status_output
```

---

# Frontend Handler Functions

All handlers should live in `app.py`.

They should catch `AccountError` and display the error message in `status_output`.

They should also catch unexpected exceptions and return a generic failure message.

## Service Factory

```python
def build_service() -> AccountService:
    ...
```

### Behavior

- Creates `AccountService(price_provider=get_share_price)`.

---

## Account Required Helper

```python
def require_account(account: Account | None) -> Account:
    ...
```

### Behavior

- Returns account if not `None`.
- Raises `AccountNotCreatedError` otherwise.

---

## Full UI Refresh Helper

```python
def build_display_outputs(
    account: Account | None,
    status_message: str = "",
    as_of_text: str | None = None,
) -> tuple[str, str, list[list[str]], list[list[str]]]:
    ...
```

### Returns

```text
status_markdown
summary_markdown
holdings_rows
transaction_rows
```

### Behavior

- If no account exists:
  - Return status.
  - Return empty summary.
  - Return empty holdings rows.
  - Return empty transactions rows.
- If account exists:
  - Parse `as_of_text` if present.
  - Build portfolio snapshot.
  - Format holdings rows.
  - Format transaction rows.
  - Format summary markdown.

---

## Create Account Handler

```python
def handle_create_account(
    name: str,
    initial_deposit: str,
) -> tuple[Account | None, str, str, list[list[str]], list[list[str]]]:
    ...
```

### Inputs

```text
name
initial_deposit
```

### Outputs

```text
account_state
status_output
account_summary_output
holdings_table
transactions_table
```

---

## Deposit Handler

```python
def handle_deposit(
    account: Account | None,
    amount: str,
) -> tuple[Account | None, str, str, list[list[str]], list[list[str]]]:
    ...
```

---

## Withdraw Handler

```python
def handle_withdraw(
    account: Account | None,
    amount: str,
) -> tuple[Account | None, str, str, list[list[str]], list[list[str]]]:
    ...
```

---

## Buy Handler

```python
def handle_buy(
    account: Account | None,
    symbol: str,
    quantity: int | float | str,
) -> tuple[Account | None, str, str, list[list[str]], list[list[str]]]:
    ...
```

---

## Sell Handler

```python
def handle_sell(
    account: Account | None,
    symbol: str,
    quantity: int | float | str,
) -> tuple[Account | None, str, str, list[list[str]], list[list[str]]]:
    ...
```

---

## Refresh Report Handler

```python
def handle_refresh_report(
    account: Account | None,
    as_of_text: str,
) -> tuple[str, str, list[list[str]], list[list[str]]]:
    ...
```

### Outputs

```text
status_output
account_summary_output
holdings_table
transactions_table
```

---

# Gradio Component Output Tables

## Holdings Table

Headers:

```python
HOLDINGS_HEADERS: list[str]
```

Recommended:

```text
Symbol
Quantity
Current Price
Market Value
```

## Transactions Table

Headers:

```python
TRANSACTION_HEADERS: list[str]
```

Recommended:

```text
ID
Timestamp
Type
Symbol
Quantity
Price
Amount
Cash After
Note
```

---

# App Entrypoint

```python
def build_app() -> gr.Blocks:
    ...
```

### Behavior

- Builds the full Gradio app.
- Defines all components.
- Wires event handlers.
- Returns the `demo` object.

```python
def main() -> None:
    ...
```

### Behavior

- Calls `build_app()`.
- Launches the Gradio app.

Use:

```python
if __name__ == "__main__":
    main()
```

---

# Recommended UI Event Wiring

## Create Account

```python
create_account_button.click(
    fn=handle_create_account,
    inputs=[account_name_input, initial_deposit_input],
    outputs=[
        account_state,
        status_output,
        account_summary_output,
        holdings_table,
        transactions_table,
    ],
)
```

## Deposit

```python
deposit_button.click(
    fn=handle_deposit,
    inputs=[account_state, cash_amount_input],
    outputs=[
        account_state,
        status_output,
        account_summary_output,
        holdings_table,
        transactions_table,
    ],
)
```

## Withdraw

```python
withdraw_button.click(
    fn=handle_withdraw,
    inputs=[account_state, cash_amount_input],
    outputs=[
        account_state,
        status_output,
        account_summary_output,
        holdings_table,
        transactions_table,
    ],
)
```

## Buy

```python
buy_button.click(
    fn=handle_buy,
    inputs=[account_state, symbol_input, quantity_input],
    outputs=[
        account_state,
        status_output,
        account_summary_output,
        holdings_table,
        transactions_table,
    ],
)
```

## Sell

```python
sell_button.click(
    fn=handle_sell,
    inputs=[account_state, symbol_input, quantity_input],
    outputs=[
        account_state,
        status_output,
        account_summary_output,
        holdings_table,
        transactions_table,
    ],
)
```

## Refresh Report

```python
refresh_button.click(
    fn=handle_refresh_report,
    inputs=[account_state, as_of_input],
    outputs=[
        status_output,
        account_summary_output,
        holdings_table,
        transactions_table,
    ],
)
```

---

# Module: `test_backend.py`

## Responsibility

Unit test the backend module.

Tests should not use Gradio.

Use standard library `unittest`.

No third-party test packages are required.

---

# Test Price Provider

The tests can import the implementation from `share_prices.py`.

Alternatively, define a deterministic local test provider:

```python
def test_price_provider(symbol: str) -> Decimal:
    ...
```

Recommended prices:

```text
AAPL  = 150.00
TSLA  = 250.00
GOOGL = 2800.00
```

---

# Test Cases

## Account Creation

```python
def test_create_account_with_initial_deposit(self) -> None:
    ...
```

Verify:

- Account name set.
- Initial deposit set.
- Cash balance equals initial deposit.
- Holdings empty.
- One transaction exists.
- Transaction type is `CREATE_ACCOUNT`.

```python
def test_create_account_rejects_negative_initial_deposit(self) -> None:
    ...
```

```python
def test_create_account_rejects_empty_name(self) -> None:
    ...
```

---

## Deposits

```python
def test_deposit_increases_cash_balance(self) -> None:
    ...
```

```python
def test_deposit_records_transaction(self) -> None:
    ...
```

```python
def test_deposit_rejects_zero_or_negative_amount(self) -> None:
    ...
```

---

## Withdrawals

```python
def test_withdraw_decreases_cash_balance(self) -> None:
    ...
```

```python
def test_withdraw_records_transaction(self) -> None:
    ...
```

```python
def test_withdraw_rejects_insufficient_funds(self) -> None:
    ...
```

```python
def test_withdraw_rejects_zero_or_negative_amount(self) -> None:
    ...
```

---

## Buying Shares

```python
def test_buy_decreases_cash_and_increases_holdings(self) -> None:
    ...
```

Example:

- Initial deposit: `1000`
- Buy `2 AAPL`
- AAPL price: `150`
- Expected cash: `700`
- Expected holdings: `{"AAPL": 2}`

```python
def test_buy_records_transaction(self) -> None:
    ...
```

```python
def test_buy_rejects_insufficient_funds(self) -> None:
    ...
```

```python
def test_buy_rejects_invalid_quantity(self) -> None:
    ...
```

```python
def test_buy_rejects_unknown_symbol(self) -> None:
    ...
```

---

## Selling Shares

```python
def test_sell_increases_cash_and_decreases_holdings(self) -> None:
    ...
```

Example:

- Initial deposit: `1000`
- Buy `4 AAPL`
- Sell `1 AAPL`
- Expected holdings: `{"AAPL": 3}`
- Expected cash:
  - After buy: `400`
  - After sell: `550`

```python
def test_sell_removes_holding_when_quantity_zero(self) -> None:
    ...
```

```python
def test_sell_records_transaction(self) -> None:
    ...
```

```python
def test_sell_rejects_insufficient_shares(self) -> None:
    ...
```

```python
def test_sell_rejects_invalid_quantity(self) -> None:
    ...
```

---

## Portfolio Valuation

```python
def test_portfolio_value_cash_only(self) -> None:
    ...
```

Example:

- Initial deposit: `1000`
- No holdings.
- Portfolio value should be `1000`.

```python
def test_portfolio_value_with_holdings(self) -> None:
    ...
```

Example:

- Initial deposit: `1000`
- Buy `2 AAPL` at `150`.
- Cash: `700`
- Holding value: `300`
- Total portfolio value: `1000`

```python
def test_profit_loss_from_initial_deposit(self) -> None:
    ...
```

With fixed prices and no price changes, buying/selling at current fixed prices should have zero P/L unless deposits/withdrawals affect the initial-deposit calculation.

```python
def test_profit_loss_from_net_contributions(self) -> None:
    ...
```

---

## Historical Reports

Use explicit timestamps for deterministic tests.

```python
def test_holdings_at_point_in_time(self) -> None:
    ...
```

Example sequence:

1. Create account at `2024-01-01 09:00:00`.
2. Buy `2 AAPL` at `2024-01-01 10:00:00`.
3. Buy `1 TSLA` at `2024-01-01 11:00:00`.
4. Sell `1 AAPL` at `2024-01-01 12:00:00`.

Assertions:

- At `09:30`: no holdings.
- At `10:30`: `AAPL: 2`.
- At `11:30`: `AAPL: 2`, `TSLA: 1`.
- At `12:30`: `AAPL: 1`, `TSLA: 1`.

```python
def test_cash_balance_at_point_in_time(self) -> None:
    ...
```

```python
def test_transactions_filtered_by_point_in_time(self) -> None:
    ...
```

```python
def test_snapshot_at_point_in_time(self) -> None:
    ...
```

---

## Validation Utilities

```python
def test_parse_money_accepts_valid_strings(self) -> None:
    ...
```

```python
def test_parse_money_rejects_invalid_strings(self) -> None:
    ...
```

```python
def test_parse_quantity_accepts_positive_integer_strings(self) -> None:
    ...
```

```python
def test_parse_quantity_rejects_zero_negative_and_decimal_values(self) -> None:
    ...
```

```python
def test_parse_datetime_accepts_supported_formats(self) -> None:
    ...
```

```python
def test_parse_datetime_rejects_invalid_formats(self) -> None:
    ...
```

---

# Engineer Assignments

## `backend_engineer`

Owns:

```text
backend.py
share_prices.py
```

### Tasks

1. Implement `share_prices.py`.
2. Implement all backend exceptions.
3. Implement `TransactionType`.
4. Implement all dataclasses:
   - `Transaction`
   - `Holding`
   - `PortfolioSnapshot`
   - `Account`
5. Implement `AccountService`.
6. Implement all validation helpers:
   - `parse_money`
   - `parse_quantity`
   - `parse_datetime`
   - `normalize_symbol`
7. Implement all formatting helpers:
   - `format_money`
   - `transaction_to_row`
   - `holding_to_row`
   - `snapshot_to_summary_lines`
8. Ensure backend has no Gradio dependency.
9. Ensure invalid operations raise the correct custom exceptions.
10. Ensure account state invariants are maintained.

### Backend Completion Criteria

- All service methods work as specified.
- All exceptions are meaningful and frontend-friendly.
- Unit tests from `test_backend.py` pass.
- Backend can be imported without launching Gradio.

---

## `frontend_engineer`

Owns:

```text
app.py
```

### Tasks

1. Build a Gradio 6 app using `gr.Blocks`.
2. Use `gr.State` to store the current `Account`.
3. Create UI sections:
   - Account creation.
   - Deposit/withdraw.
   - Buy/sell.
   - Reports.
   - Holdings table.
   - Transactions table.
4. Implement frontend handler functions:
   - `build_service`
   - `require_account`
   - `build_display_outputs`
   - `handle_create_account`
   - `handle_deposit`
   - `handle_withdraw`
   - `handle_buy`
   - `handle_sell`
   - `handle_refresh_report`
   - `build_app`
   - `main`
5. Catch backend exceptions and display messages in `status_output`.
6. Ensure all backend state mutations return the updated account into `account_state`.
7. Use Gradio 6 API correctly:
   - Pass `theme`, `css`, and `show_error` to `launch()`.
   - Use `button.click(fn=..., inputs=[...], outputs=[...])`.
   - Use `gr.Dataframe(..., interactive=False)` for display tables.
   - Prefer `gr.Textbox` for money inputs.

### Frontend Completion Criteria

- App launches with `uv run python app.py`.
- User can create an account.
- User can deposit and withdraw funds.
- User can buy and sell supported shares.
- Invalid operations show a clear error message.
- Holdings table updates after trades.
- Transaction table updates after every operation.
- Portfolio summary updates after every operation.
- Historical report input filters reports by timestamp.

---

## `test_engineer`

Owns:

```text
test_backend.py
```

### Tasks

1. Write unit tests using standard library `unittest`.
2. Test backend only.
3. Cover:
   - Account creation.
   - Deposits.
   - Withdrawals.
   - Buys.
   - Sells.
   - Validation errors.
   - Insufficient funds.
   - Insufficient shares.
   - Unknown symbols.
   - Current portfolio valuation.
   - Historical holdings.
   - Historical cash balance.
   - Historical transaction filtering.
   - Profit/loss calculations.
4. Use deterministic timestamps in historical tests.
5. Ensure tests can run with:

```text
uv run python -m unittest test_backend.py
```

### Test Completion Criteria

- Tests are deterministic.
- Tests do not require Gradio.
- Tests do not depend on execution order.
- Tests pass after backend implementation.
- Tests cover all core business rules.

---

# Acceptance Criteria

The system is complete when:

1. `uv run python -m unittest test_backend.py` passes.
2. `uv run python app.py` launches the Gradio app.
3. A user can create an account with an initial deposit.
4. A user can deposit funds.
5. A user can withdraw funds only when sufficient cash exists.
6. A user can buy shares only when sufficient cash exists.
7. A user can sell shares only when sufficient shares exist.
8. The system reports current holdings.
9. The system reports holdings at a point in time.
10. The system reports current profit/loss.
11. The system reports profit/loss at a point in time.
12. The system lists all transactions.
13. The system lists transactions filtered by point in time.
14. Unsupported symbols are rejected.
15. Invalid money, quantity, and timestamp inputs are rejected with clear messages.