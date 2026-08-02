# Design: Trading Simulation Account Management System

## 1. Overview

Build a simple in-memory account management system for a trading simulation platform.

The system supports:

- Creating user accounts
- Depositing and withdrawing funds
- Buying and selling shares
- Preventing invalid actions:
  - Withdrawals that would create a negative cash balance
  - Buys that exceed available cash
  - Sells that exceed current holdings
- Reporting:
  - Current holdings
  - Holdings at a point in time
  - Current portfolio value
  - Portfolio value at a point in time
  - Profit/loss
  - Profit/loss at a point in time
  - Transaction history

The backend should be implemented in pure Python using only the standard library.

The frontend should be a Gradio 6 app.

All files must live in the same directory. No packages or subdirectories.

---

## 2. File Structure

All files are in the project root:

```text
backend.py
app.py
test_backend.py
```

Optional if useful:

```text
README.md
```

---

## 3. Backend Design

### Owner

`backend_engineer`

### File

```text
backend.py
```

---

## 4. Backend Domain Model

The backend should be deterministic, testable, and independent of Gradio.

Use in-memory storage only. Persistence is not required.

Use `decimal.Decimal` for money and share prices to avoid floating point precision issues.

Use `datetime.datetime` from the standard library for transaction timestamps.

---

## 5. Price Provider

The system has access to a function:

```python
def get_share_price(symbol: str) -> Decimal:
    ...
```

For this project, provide a test implementation with fixed prices:

| Symbol | Price |
|---|---:|
| AAPL | 150.00 |
| TSLA | 250.00 |
| GOOGL | 2800.00 |

The function should normalize symbols to uppercase.

If an unsupported symbol is requested, raise an appropriate backend exception.

### Signature

```python
def get_share_price(symbol: str) -> Decimal:
    ...
```

---

## 6. Backend Exceptions

Define custom exceptions so the UI and tests can distinguish validation failures from unexpected failures.

### Classes

```python
class AccountError(Exception):
    ...
```

Base exception for expected account-management errors.

```python
class AccountNotFoundError(AccountError):
    ...
```

Raised when an operation references an unknown account.

```python
class DuplicateAccountError(AccountError):
    ...
```

Raised when trying to create an account with an ID that already exists.

```python
class InvalidAmountError(AccountError):
    ...
```

Raised when a deposit, withdrawal, price, or amount is zero, negative, or invalid.

```python
class InvalidQuantityError(AccountError):
    ...
```

Raised when a buy or sell quantity is zero, negative, or invalid.

```python
class InsufficientFundsError(AccountError):
    ...
```

Raised when a withdrawal or buy would exceed available cash.

```python
class InsufficientHoldingsError(AccountError):
    ...
```

Raised when a sell would exceed owned shares.

```python
class UnknownSymbolError(AccountError):
    ...
```

Raised when `get_share_price()` is called with an unsupported symbol.

---

## 7. Backend Data Classes

Use `@dataclass`.

---

### 7.1 Transaction

Represents one account activity.

### Fields

```python
@dataclass(frozen=True)
class Transaction:
    transaction_id: str
    account_id: str
    timestamp: datetime
    type: str
    symbol: Optional[str]
    quantity: Decimal
    price: Decimal
    cash_amount: Decimal
    cash_balance_after: Decimal
```

### Notes

`type` should be one of:

```python
"DEPOSIT"
"WITHDRAW"
"BUY"
"SELL"
```

For deposits and withdrawals:

- `symbol` is `None`
- `quantity` is `Decimal("0")`
- `price` is `Decimal("0")`
- `cash_amount` is:
  - positive for deposit
  - negative for withdrawal

For buys:

- `symbol` is uppercase
- `quantity` is positive
- `price` is the share price used at trade time
- `cash_amount` is negative total trade cost

For sells:

- `symbol` is uppercase
- `quantity` is positive
- `price` is the share price used at trade time
- `cash_amount` is positive total sale proceeds

---

### 7.2 Account

Represents the current state of an account.

### Fields

```python
@dataclass
class Account:
    account_id: str
    name: str
    cash_balance: Decimal
    initial_deposit: Decimal
    created_at: datetime
    transactions: list[Transaction]
```

### Notes

The `Account` object stores:

- Current cash balance
- Initial deposit amount
- Creation timestamp
- Full transaction history

Holdings should not be stored as mutable source-of-truth inside `Account`.

Instead, holdings should be calculated from transactions. This keeps reporting consistent and allows point-in-time reconstruction.

---

### 7.3 AccountSnapshot

Represents account state at a point in time.

### Fields

```python
@dataclass(frozen=True)
class AccountSnapshot:
    account_id: str
    as_of: datetime
    cash_balance: Decimal
    holdings: dict[str, Decimal]
    holdings_value: Decimal
    total_value: Decimal
    net_contributions: Decimal
    profit_loss: Decimal
```

### Definitions

`holdings_value`:

```text
sum(quantity * current get_share_price(symbol)) for all current holdings
```

`total_value`:

```text
cash_balance + holdings_value
```

`net_contributions`:

```text
sum(deposits) - sum(withdrawals)
```

`profit_loss`:

```text
total_value - net_contributions
```

This definition handles multiple deposits and withdrawals correctly.

The requirements mention profit/loss from the initial deposit. Since the system also supports later deposits and withdrawals, the backend should calculate profit/loss against net cash contributions. The account’s `initial_deposit` should still be stored and displayed.

---

## 8. Backend Service Class

Implement one main service class:

```python
class AccountService:
    ...
```

This class owns in-memory accounts and exposes the full application API.

---

## 9. AccountService Constructor

```python
class AccountService:
    def __init__(
        self,
        price_provider: Callable[[str], Decimal] = get_share_price,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        ...
```

### Behavior

- `price_provider` allows tests to inject controlled prices.
- `clock` allows tests to inject deterministic timestamps.
- If `clock` is `None`, use current UTC time.

---

## 10. Account Creation

### Signature

```python
def create_account(
    self,
    account_id: str,
    name: str,
    initial_deposit: Decimal | int | float | str,
) -> Account:
    ...
```

### Behavior

- Normalize `account_id` by trimming whitespace.
- Validate `account_id` is non-empty.
- Validate `name` is non-empty.
- Validate `initial_deposit` is greater than zero.
- Reject duplicate `account_id`.
- Create account with:
  - `cash_balance = initial_deposit`
  - `initial_deposit = initial_deposit`
  - one initial `DEPOSIT` transaction
- Return the created `Account`.

---

## 11. Account Lookup

### Signature

```python
def get_account(self, account_id: str) -> Account:
    ...
```

### Behavior

- Return account by ID.
- Raise `AccountNotFoundError` if not found.

---

## 12. List Accounts

### Signature

```python
def list_accounts(self) -> list[Account]:
    ...
```

### Behavior

- Return all accounts.
- Sort by `created_at`, oldest first.

---

## 13. Deposit Funds

### Signature

```python
def deposit(
    self,
    account_id: str,
    amount: Decimal | int | float | str,
) -> Transaction:
    ...
```

### Behavior

- Validate account exists.
- Validate `amount > 0`.
- Increase cash balance.
- Append `DEPOSIT` transaction.
- Return transaction.

---

## 14. Withdraw Funds

### Signature

```python
def withdraw(
    self,
    account_id: str,
    amount: Decimal | int | float | str,
) -> Transaction:
    ...
```

### Behavior

- Validate account exists.
- Validate `amount > 0`.
- Reject if `amount > cash_balance`.
- Decrease cash balance.
- Append `WITHDRAW` transaction.
- Return transaction.

---

## 15. Buy Shares

### Signature

```python
def buy(
    self,
    account_id: str,
    symbol: str,
    quantity: Decimal | int | float | str,
) -> Transaction:
    ...
```

### Behavior

- Validate account exists.
- Normalize symbol to uppercase.
- Validate quantity is greater than zero.
- Get current share price using `price_provider`.
- Calculate total cost:

```text
price * quantity
```

- Reject if total cost exceeds account cash balance.
- Decrease cash balance.
- Append `BUY` transaction.
- Return transaction.

### Fractional Shares

Support fractional share quantities by using `Decimal`.

Examples:

```text
1
10
0.5
2.25
```

---

## 16. Sell Shares

### Signature

```python
def sell(
    self,
    account_id: str,
    symbol: str,
    quantity: Decimal | int | float | str,
) -> Transaction:
    ...
```

### Behavior

- Validate account exists.
- Normalize symbol to uppercase.
- Validate quantity is greater than zero.
- Calculate current holdings for that symbol.
- Reject if sell quantity exceeds holdings.
- Get current share price using `price_provider`.
- Calculate sale proceeds:

```text
price * quantity
```

- Increase cash balance.
- Append `SELL` transaction.
- Return transaction.

---

## 17. Current Holdings

### Signature

```python
def get_holdings(self, account_id: str) -> dict[str, Decimal]:
    ...
```

### Behavior

- Return current holdings by replaying all buy/sell transactions.
- Exclude symbols with zero quantity.
- Raise `AccountNotFoundError` if account is unknown.

### Example Return

```python
{
    "AAPL": Decimal("3"),
    "TSLA": Decimal("1.5"),
}
```

---

## 18. Holdings at a Point in Time

### Signature

```python
def get_holdings_at(
    self,
    account_id: str,
    as_of: datetime,
) -> dict[str, Decimal]:
    ...
```

### Behavior

- Replay only transactions with `timestamp <= as_of`.
- Include buys and sells.
- Exclude zero-quantity holdings.
- Raise `AccountNotFoundError` if account is unknown.

---

## 19. Cash Balance at a Point in Time

### Signature

```python
def get_cash_balance_at(
    self,
    account_id: str,
    as_of: datetime,
) -> Decimal:
    ...
```

### Behavior

- Replay all cash-impacting transactions with `timestamp <= as_of`.
- Return resulting cash balance.

---

## 20. Net Contributions

### Signature

```python
def get_net_contributions(
    self,
    account_id: str,
    as_of: datetime | None = None,
) -> Decimal:
    ...
```

### Behavior

- Deposits increase contributions.
- Withdrawals decrease contributions.
- Buys and sells do not affect contributions.
- If `as_of` is provided, include only transactions with `timestamp <= as_of`.
- If `as_of` is `None`, include all transactions.

---

## 21. Portfolio Value

### Current Portfolio Value

```python
def get_portfolio_value(self, account_id: str) -> Decimal:
    ...
```

### Portfolio Value at a Point in Time

```python
def get_portfolio_value_at(
    self,
    account_id: str,
    as_of: datetime,
) -> Decimal:
    ...
```

### Behavior

Portfolio value is:

```text
cash balance + current market value of holdings
```

Since the provided `get_share_price(symbol)` only returns current prices, point-in-time portfolio reports should reconstruct historical cash and holdings as of the requested time, but value those holdings using the current available price provider.

This limitation should be documented in the UI.

---

## 22. Profit/Loss

### Current Profit/Loss

```python
def get_profit_loss(self, account_id: str) -> Decimal:
    ...
```

### Profit/Loss at a Point in Time

```python
def get_profit_loss_at(
    self,
    account_id: str,
    as_of: datetime,
) -> Decimal:
    ...
```

### Behavior

Profit/loss is:

```text
portfolio value - net contributions
```

For point-in-time profit/loss:

```text
portfolio value at as_of - net contributions at as_of
```

---

## 23. Account Snapshot

### Current Snapshot

```python
def get_snapshot(self, account_id: str) -> AccountSnapshot:
    ...
```

### Snapshot at a Point in Time

```python
def get_snapshot_at(
    self,
    account_id: str,
    as_of: datetime,
) -> AccountSnapshot:
    ...
```

### Behavior

Return a complete `AccountSnapshot` containing:

- Account ID
- Timestamp
- Cash balance
- Holdings
- Holdings market value
- Total account value
- Net contributions
- Profit/loss

---

## 24. Transaction Listing

### Signature

```python
def list_transactions(
    self,
    account_id: str,
    start: datetime | None = None,
    end: datetime | None = None,
) -> list[Transaction]:
    ...
```

### Behavior

- Return transactions for the account.
- If `start` is provided, include transactions where `timestamp >= start`.
- If `end` is provided, include transactions where `timestamp <= end`.
- Sort oldest first.
- Raise `AccountNotFoundError` if account is unknown.

---

## 25. Backend Helper Functions

These helpers should be implemented in `backend.py`.

### Money/Decimal Conversion

```python
def to_decimal(value: Decimal | int | float | str) -> Decimal:
    ...
```

### Behavior

- Convert supported numeric input to `Decimal`.
- For floats, convert using `str(value)` to avoid binary float artifacts.
- Strip strings.
- Raise `InvalidAmountError` if value cannot be converted.

---

### Symbol Normalization

```python
def normalize_symbol(symbol: str) -> str:
    ...
```

### Behavior

- Strip whitespace.
- Convert to uppercase.
- Reject empty symbols.

---

### Money Formatting

For frontend display and tests.

```python
def format_money(value: Decimal) -> str:
    ...
```

### Example

```text
Decimal("123.4") -> "$123.40"
Decimal("-12.5") -> "-$12.50"
```

---

### Decimal Formatting

For quantities.

```python
def format_decimal(value: Decimal) -> str:
    ...
```

### Example

```text
Decimal("1.5000") -> "1.5"
Decimal("3") -> "3"
```

---

### Transaction Serialization

Useful for Gradio tables.

```python
def transaction_to_row(transaction: Transaction) -> list[str]:
    ...
```

### Output Columns

```text
Timestamp
Type
Symbol
Quantity
Price
Cash Amount
Cash Balance After
Transaction ID
```

---

### Holdings Serialization

Useful for Gradio tables.

```python
def holdings_to_rows(
    holdings: dict[str, Decimal],
    price_provider: Callable[[str], Decimal] = get_share_price,
) -> list[list[str]]:
    ...
```

### Output Columns

```text
Symbol
Quantity
Current Price
Market Value
```

---

## 26. Transaction IDs

Use standard library UUIDs.

### Helper Signature

```python
def generate_transaction_id() -> str:
    ...
```

---

## 27. Timestamp Handling

Use timezone-aware UTC datetimes.

### Helper Signature

```python
def utc_now() -> datetime:
    ...
```

---

# 28. Frontend Design

### Owner

`frontend_engineer`

### File

```text
app.py
```

The frontend should be a Gradio 6 app that imports and uses `AccountService` from `backend.py`.

The app should keep a single in-memory `AccountService` instance for the lifetime of the process.

---

## 29. Gradio 6 API Guidance

Use:

```python
import gradio as gr
```

Build the UI with:

```python
with gr.Blocks() as demo:
    ...
```

Launch with:

```python
demo.launch()
```

Use event handlers like:

```python
button.click(
    fn=some_function,
    inputs=[input_component_1, input_component_2],
    outputs=[output_component_1, output_component_2],
)
```

or:

```python
gr.on(
    triggers=[button.click],
    fn=some_function,
    inputs=[...],
    outputs=[...],
)
```

### Important Gradio 6 Dataframe Change

In Gradio 6, `gr.Dataframe` changed row/column sizing arguments.

Use:

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

Do **not** use older Gradio 5 style:

```python
col_count=...
```

Use `column_count`, not `col_count`.

Use `row_limits` and `column_limits`, not tuple-style `row_count=(5, "fixed")`.

### Components to Use

Recommended components:

```python
gr.Markdown(...)
gr.Textbox(...)
gr.Number(...)
gr.Dropdown(...)
gr.Button(...)
gr.Dataframe(...)
gr.State(...)
gr.Row()
gr.Column()
gr.Tabs()
gr.Tab()
gr.Accordion()
```

### Button Guidance

Use:

```python
gr.Button("Create Account", variant="primary")
```

Supported variants include common Gradio variants such as:

```text
"primary"
"secondary"
"stop"
```

### Error Display

Use an output `gr.Markdown` or `gr.Textbox` for status messages.

The frontend should catch `AccountError` exceptions and display a friendly message instead of crashing.

---

## 30. Frontend App State

Use a module-level backend service:

```python
service: AccountService
```

Use `gr.State` to store the selected/current account ID in the UI:

```python
current_account_id_state = gr.State(value="")
```

---

## 31. Frontend Layout

The app should have the title:

```text
Trading Simulation Account Manager
```

Use tabs:

1. Account
2. Funds
3. Trade
4. Portfolio
5. Transactions

---

## 32. Frontend Tab: Account

### Purpose

Create an account and select an existing account.

### Components

```python
account_id_input = gr.Textbox(label="Account ID")
name_input = gr.Textbox(label="Name")
initial_deposit_input = gr.Number(label="Initial Deposit", value=10000)
create_account_button = gr.Button("Create Account", variant="primary")
account_dropdown = gr.Dropdown(label="Select Account", choices=[])
refresh_accounts_button = gr.Button("Refresh Accounts")
account_status = gr.Markdown()
```

### Handler Signatures

```python
def handle_create_account(
    account_id: str,
    name: str,
    initial_deposit: float,
) -> tuple[str, list[str], str]:
    ...
```

Returns:

```text
status markdown
updated account choices
current account id
```

```python
def handle_refresh_accounts() -> list[str]:
    ...
```

Returns updated dropdown choices.

```python
def handle_select_account(account_id: str) -> str:
    ...
```

Returns selected account ID for `gr.State`.

### Gradio Wiring

```python
create_account_button.click(
    fn=handle_create_account,
    inputs=[account_id_input, name_input, initial_deposit_input],
    outputs=[account_status, account_dropdown, current_account_id_state],
)
```

For updating dropdown choices in Gradio 6, the handler may return a new `gr.Dropdown(...)` object or the value expected by the component update pattern supported by the installed version. Prefer returning:

```python
gr.Dropdown(choices=choices, value=selected_value)
```

from the event handler if simple list return does not update choices.

---

## 33. Frontend Tab: Funds

### Purpose

Deposit and withdraw funds for the selected account.

### Components

```python
fund_amount_input = gr.Number(label="Amount", value=1000)
deposit_button = gr.Button("Deposit", variant="primary")
withdraw_button = gr.Button("Withdraw", variant="secondary")
fund_status = gr.Markdown()
```

### Handler Signatures

```python
def handle_deposit(
    account_id: str,
    amount: float,
) -> str:
    ...
```

```python
def handle_withdraw(
    account_id: str,
    amount: float,
) -> str:
    ...
```

### Behavior

- If no account is selected, return a message asking the user to create/select one.
- On success, return transaction summary.
- On backend validation error, return error message.

---

## 34. Frontend Tab: Trade

### Purpose

Buy and sell shares.

### Components

```python
symbol_dropdown = gr.Dropdown(
    label="Symbol",
    choices=["AAPL", "TSLA", "GOOGL"],
    value="AAPL",
)
quantity_input = gr.Number(label="Quantity", value=1)
buy_button = gr.Button("Buy", variant="primary")
sell_button = gr.Button("Sell", variant="secondary")
trade_status = gr.Markdown()
```

### Handler Signatures

```python
def handle_buy(
    account_id: str,
    symbol: str,
    quantity: float,
) -> str:
    ...
```

```python
def handle_sell(
    account_id: str,
    symbol: str,
    quantity: float,
) -> str:
    ...
```

---

## 35. Frontend Tab: Portfolio

### Purpose

Display account snapshot, holdings, portfolio value, and profit/loss.

### Components

```python
refresh_portfolio_button = gr.Button("Refresh Portfolio", variant="primary")
portfolio_summary = gr.Markdown()
holdings_table = gr.Dataframe(
    headers=["Symbol", "Quantity", "Current Price", "Market Value"],
    datatype=["str", "str", "str", "str"],
    row_count=0,
    row_limits=None,
    column_count=4,
    column_limits=(4, 4),
    interactive=False,
)
```

Optional point-in-time report:

```python
as_of_input = gr.Textbox(
    label="As Of Timestamp UTC",
    placeholder="YYYY-MM-DD HH:MM:SS",
)
refresh_portfolio_at_button = gr.Button("Refresh Portfolio At Time")
```

### Handler Signatures

```python
def handle_refresh_portfolio(
    account_id: str,
) -> tuple[str, list[list[str]]]:
    ...
```

Returns:

```text
portfolio summary markdown
holdings table rows
```

```python
def handle_refresh_portfolio_at(
    account_id: str,
    as_of_text: str,
) -> tuple[str, list[list[str]]]:
    ...
```

### Portfolio Summary Markdown Should Include

```text
Account ID
Cash Balance
Holdings Value
Total Portfolio Value
Net Contributions
Profit/Loss
```

Also include a note:

```text
Point-in-time holdings and cash are reconstructed from historical transactions. Share valuation uses the current available price provider.
```

---

## 36. Frontend Tab: Transactions

### Purpose

List all transactions for the selected account.

### Components

```python
refresh_transactions_button = gr.Button("Refresh Transactions", variant="primary")
transactions_table = gr.Dataframe(
    headers=[
        "Timestamp",
        "Type",
        "Symbol",
        "Quantity",
        "Price",
        "Cash Amount",
        "Cash Balance After",
        "Transaction ID",
    ],
    datatype=["str", "str", "str", "str", "str", "str", "str", "str"],
    row_count=0,
    row_limits=None,
    column_count=8,
    column_limits=(8, 8),
    interactive=False,
)
transaction_status = gr.Markdown()
```

### Handler Signature

```python
def handle_refresh_transactions(
    account_id: str,
) -> tuple[list[list[str]], str]:
    ...
```

Returns:

```text
transaction rows
status markdown
```

---

## 37. Frontend Helper Functions

Implement in `app.py`.

### Current Account Validation

```python
def require_selected_account(account_id: str) -> str:
    ...
```

### Behavior

- Return normalized account ID.
- Raise or return a friendly error if no account is selected.

---

### Timestamp Parsing

```python
def parse_as_of_timestamp(as_of_text: str) -> datetime:
    ...
```

### Accepted Input

```text
YYYY-MM-DD HH:MM:SS
YYYY-MM-DDTHH:MM:SS
```

Assume UTC.

---

### Snapshot Markdown

```python
def snapshot_to_markdown(snapshot: AccountSnapshot) -> str:
    ...
```

---

### Transaction Status Markdown

```python
def transaction_summary_to_markdown(transaction: Transaction) -> str:
    ...
```

---

### Safe Handler Wrapper

Optional but recommended:

```python
def error_markdown(message: str) -> str:
    ...
```

---

# 38. Unit Test Design

### Owner

`test_engineer`

### File

```text
test_backend.py
```

Use Python standard library `unittest`.

Do not test Gradio UI directly.

Tests should import `backend.py`.

---

## 39. Test Helpers

Implement deterministic helpers in `test_backend.py`.

### Fixed Clock

```python
class FixedClock:
    def __init__(self, timestamps: list[datetime]) -> None:
        ...

    def __call__(self) -> datetime:
        ...
```

### Fixed Price Provider

```python
def fixed_price_provider(symbol: str) -> Decimal:
    ...
```

Use:

```text
AAPL: 100
TSLA: 200
GOOGL: 1000
```

---

## 40. Required Unit Tests

### Account Creation

```python
def test_create_account_creates_initial_deposit_transaction(self) -> None:
    ...
```

Verify:

- Account exists
- Cash balance equals initial deposit
- Initial deposit is stored
- One transaction exists
- Transaction type is `DEPOSIT`

---

### Duplicate Account

```python
def test_create_duplicate_account_raises(self) -> None:
    ...
```

Verify `DuplicateAccountError`.

---

### Invalid Initial Deposit

```python
def test_create_account_rejects_non_positive_initial_deposit(self) -> None:
    ...
```

Verify zero and negative deposits fail.

---

### Deposit

```python
def test_deposit_increases_cash_and_records_transaction(self) -> None:
    ...
```

---

### Withdraw

```python
def test_withdraw_decreases_cash_and_records_transaction(self) -> None:
    ...
```

---

### Withdraw Insufficient Funds

```python
def test_withdraw_rejects_insufficient_funds(self) -> None:
    ...
```

Verify:

- Raises `InsufficientFundsError`
- Cash balance unchanged
- No extra transaction recorded

---

### Buy Shares

```python
def test_buy_decreases_cash_and_increases_holdings(self) -> None:
    ...
```

Example:

- Initial deposit: 1000
- Buy 3 AAPL at 100
- Cash should be 700
- Holdings should be `{"AAPL": Decimal("3")}`

---

### Buy Insufficient Funds

```python
def test_buy_rejects_insufficient_funds(self) -> None:
    ...
```

Verify:

- Raises `InsufficientFundsError`
- Cash unchanged
- Holdings unchanged

---

### Sell Shares

```python
def test_sell_increases_cash_and_decreases_holdings(self) -> None:
    ...
```

Example:

- Initial deposit: 1000
- Buy 3 AAPL at 100
- Sell 1 AAPL at 100
- Cash should be 800
- Holdings should be `{"AAPL": Decimal("2")}`

---

### Sell Insufficient Holdings

```python
def test_sell_rejects_insufficient_holdings(self) -> None:
    ...
```

Verify:

- Raises `InsufficientHoldingsError`
- Cash unchanged
- Holdings unchanged

---

### Portfolio Value

```python
def test_get_portfolio_value_includes_cash_and_holdings_value(self) -> None:
    ...
```

Example:

- Initial deposit: 1000
- Buy 3 AAPL at 100
- Cash: 700
- Holdings value: 300
- Portfolio value: 1000

---

### Profit/Loss

```python
def test_profit_loss_uses_net_contributions(self) -> None:
    ...
```

Example:

- Initial deposit: 1000
- Buy 3 AAPL at 100
- Change price provider if useful, or use fixed value.
- Verify `profit_loss = portfolio_value - net_contributions`.

---

### Transactions Are Ordered

```python
def test_list_transactions_returns_transactions_oldest_first(self) -> None:
    ...
```

---

### Holdings at Point in Time

```python
def test_get_holdings_at_reconstructs_historical_holdings(self) -> None:
    ...
```

Example:

- t1 create account
- t2 buy 3 AAPL
- t3 sell 1 AAPL
- Holdings at t2 should be 3 AAPL
- Holdings at t3 should be 2 AAPL

---

### Profit/Loss at Point in Time

```python
def test_get_profit_loss_at_reconstructs_state_at_time(self) -> None:
    ...
```

---

### Unknown Symbol

```python
def test_unknown_symbol_raises(self) -> None:
    ...
```

Verify `UnknownSymbolError`.

---

## 41. Backend Implementation Notes

### Decimal Normalization

All amounts and quantities should be converted immediately to `Decimal`.

Recommended precision:

- Money values can be quantized to cents for display.
- Internally, avoid excessive quantization except when formatting.
- Trade cost is `price * quantity`.

### Input Validation

Reject:

- Empty account IDs
- Empty names
- Empty symbols
- Non-numeric amounts
- Zero amounts
- Negative amounts
- Zero quantities
- Negative quantities

### Atomicity

Each mutating operation should validate everything before mutating account state.

For example, `buy()` should not decrease cash or append a transaction until after:

- Account exists
- Quantity is valid
- Price is available
- Cash is sufficient

Tests should confirm invalid operations leave state unchanged.

---

# 42. Engineer Assignments

## backend_engineer

Implement `backend.py`.

### Responsibilities

- Implement all exceptions.
- Implement `Transaction`, `Account`, and `AccountSnapshot`.
- Implement `get_share_price()`.
- Implement `AccountService`.
- Implement validation helpers.
- Implement serialization/formatting helpers for frontend.
- Ensure operations are atomic.
- Ensure point-in-time reporting works by replaying transactions.

### Deliverable

A working `backend.py` module exposing:

```python
get_share_price
AccountService
Transaction
Account
AccountSnapshot
AccountError
AccountNotFoundError
DuplicateAccountError
InvalidAmountError
InvalidQuantityError
InsufficientFundsError
InsufficientHoldingsError
UnknownSymbolError
to_decimal
normalize_symbol
format_money
format_decimal
transaction_to_row
holdings_to_rows
```

---

## frontend_engineer

Implement `app.py`.

### Responsibilities

- Build Gradio 6 UI with tabs:
  - Account
  - Funds
  - Trade
  - Portfolio
  - Transactions
- Use `AccountService` from `backend.py`.
- Keep one module-level service instance.
- Use `gr.State` for selected account.
- Catch backend `AccountError` exceptions and display friendly errors.
- Display tables using `gr.Dataframe` with Gradio 6-compatible arguments:
  - `column_count`
  - `column_limits`
  - `row_count`
  - `row_limits`
- Do not use deprecated `col_count`.
- Do not use Gradio 5 tuple-style `row_count=(..., "fixed")`.

### Deliverable

A working app launched by:

```bash
uv run python app.py
```

---

## test_engineer

Implement `test_backend.py`.

### Responsibilities

- Use `unittest`.
- Test backend only.
- Cover account creation, deposits, withdrawals, buys, sells, holdings, portfolio value, profit/loss, point-in-time reports, and transaction history.
- Verify invalid operations raise expected exceptions.
- Verify invalid operations do not mutate backend state.
- Use injected fixed clock and fixed price provider for deterministic tests.

### Deliverable

A passing unit test suite run by:

```bash
uv run python -m unittest test_backend.py
```

---

# 43. Acceptance Criteria

The system is complete when:

1. A user can create an account with an initial deposit.
2. A user can deposit additional funds.
3. A user can withdraw funds if sufficient cash exists.
4. A user cannot withdraw more cash than available.
5. A user can buy AAPL, TSLA, and GOOGL if sufficient cash exists.
6. A user cannot buy shares beyond available cash.
7. A user can sell shares they own.
8. A user cannot sell more shares than owned.
9. The system reports current holdings.
10. The system reports holdings at a point in time.
11. The system reports current portfolio value.
12. The system reports current profit/loss.
13. The system reports profit/loss at a point in time.
14. The system lists transactions over time.
15. Backend unit tests pass.
16. Gradio app runs successfully with Gradio 6.
17. All files are in the same directory.
18. No third-party packages are used except Gradio for the frontend.