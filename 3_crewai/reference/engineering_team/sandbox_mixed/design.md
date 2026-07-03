# Design: Simple Account Management System for Trading Simulation Platform

## 1. Overview

Build a small Python/Gradio application that lets users:

- Create trading simulation accounts.
- Deposit and withdraw cash.
- Buy and sell shares.
- View current holdings.
- View portfolio value.
- View profit/loss.
- View transaction history.
- Prevent invalid operations:
  - Withdrawals that make cash negative.
  - Buys that exceed available cash.
  - Sells that exceed owned shares.

The system will use an injected `get_share_price(symbol)` function. The backend should include a default test implementation returning fixed prices for:

- `AAPL`
- `TSLA`
- `GOOGL`

All files live in the same directory. No packages/subdirectories.

---

## 2. File Layout

The engineers should create the following files in the sandbox root:

```text
account_backend.py
app.py
test_account_backend.py
```

Optional, if useful:

```text
README.md
```

---

## 3. Responsibilities

### backend_engineer

Owns:

```text
account_backend.py
```

Responsibilities:

- Define backend data models.
- Implement account creation.
- Implement deposits and withdrawals.
- Implement buy and sell transaction recording.
- Implement holdings calculation.
- Implement portfolio valuation.
- Implement profit/loss calculation.
- Implement transaction listing.
- Enforce all validation rules.
- Provide default `get_share_price(symbol)` test implementation.

### frontend_engineer

Owns:

```text
app.py
```

Responsibilities:

- Build Gradio 6 UI.
- Use backend service from `account_backend.py`.
- Allow users to perform all account operations.
- Display account summary, holdings, and transactions.
- Show clear validation messages from backend exceptions.
- Follow Gradio 6 API guidance in this design.

### test_engineer

Owns:

```text
test_account_backend.py
```

Responsibilities:

- Write unit tests for backend only.
- Test valid account flows.
- Test invalid operations.
- Test holdings, transactions, valuation, and profit/loss.
- Use only Python standard library testing tools, preferably `unittest`.

---

## 4. Backend Design

File:

```text
account_backend.py
```

### 4.1 Design Principles

- Backend must be independent of Gradio.
- Backend state can be in-memory.
- Use standard library only.
- Raise typed exceptions for validation errors.
- Keep transaction history append-only.
- Compute holdings from transactions or maintain holdings consistently.
- Monetary values should be rounded for display, but calculations should remain numeric.
- Share quantities are whole-number integers and must be positive.

---

## 5. Backend Data Model

Use `dataclasses` and standard library types.

### 5.1 Transaction Types

Supported transaction types:

```text
CREATE_ACCOUNT
DEPOSIT
WITHDRAW
BUY
SELL
```

Represent them as string constants or an enum.

Recommended enum signature:

```python
class TransactionType(str, Enum)
```

Enum values:

```text
CREATE_ACCOUNT
DEPOSIT
WITHDRAW
BUY
SELL
```

---

### 5.2 Transaction Class

Represents one account event.

Signature:

```python
@dataclass(frozen=True)
class Transaction:
    transaction_id: int
    account_id: str
    transaction_type: TransactionType
    timestamp: datetime
    amount: float = 0.0
    symbol: Optional[str] = None
    quantity: int = 0
    share_price: Optional[float] = None
    notes: str = ""
```

Field meaning:

| Field | Meaning |
|---|---|
| `transaction_id` | Monotonic integer within the service |
| `account_id` | Account identifier |
| `transaction_type` | Deposit, withdrawal, buy, sell, etc. |
| `timestamp` | Time transaction was recorded |
| `amount` | Cash value of transaction |
| `symbol` | Stock symbol for buy/sell |
| `quantity` | Number of shares for buy/sell |
| `share_price` | Price used at buy/sell time |
| `notes` | Optional details |

For buy/sell:

```text
amount = quantity * share_price
```

For deposit/withdraw:

```text
amount = cash amount
```

---

### 5.3 Account Class

Represents current account state.

Signature:

```python
@dataclass
class Account:
    account_id: str
    owner_name: str
    created_at: datetime
    initial_deposit: float
    cash_balance: float
    holdings: dict[str, int]
    transaction_ids: list[int]
```

Field meaning:

| Field | Meaning |
|---|---|
| `account_id` | Unique account ID |
| `owner_name` | Display name |
| `created_at` | Creation timestamp |
| `initial_deposit` | Initial cash deposited when account was created |
| `cash_balance` | Current cash available |
| `holdings` | Current shares by symbol |
| `transaction_ids` | IDs of transactions for this account |

---

### 5.4 Backend Exceptions

Use custom exception classes so frontend can display clean errors.

Signatures:

```python
class AccountError(Exception)
```

```python
class AccountNotFoundError(AccountError)
```

```python
class ValidationError(AccountError)
```

```python
class InsufficientFundsError(AccountError)
```

```python
class InsufficientSharesError(AccountError)
```

```python
class UnknownSymbolError(AccountError)
```

---

## 6. Backend Price Provider

### 6.1 Default Fixed Price Function

Signature:

```python
def get_share_price(symbol: str) -> float
```

Behavior:

- Normalize symbol to uppercase.
- Return fixed test prices:

```text
AAPL  -> 150.00
TSLA  -> 250.00
GOOGL -> 2800.00
```

- Raise `UnknownSymbolError` for unsupported symbols.

---

## 7. Account Service

Main backend class.

Signature:

```python
class AccountService:
    def __init__(
        self,
        price_provider: Callable[[str], float] = get_share_price,
        clock: Callable[[], datetime] | None = None,
    ) -> None
```

Responsibilities:

- Own in-memory account registry.
- Own transaction registry.
- Own transaction ID counter.
- Use injected `price_provider`.
- Use injected `clock` for deterministic tests.

Internal attributes:

```python
self._accounts: dict[str, Account]
self._transactions: list[Transaction]
self._next_transaction_id: int
self._price_provider: Callable[[str], float]
self._clock: Callable[[], datetime]
```

---

## 8. Account Service Public API

### 8.1 Create Account

Signature:

```python
def create_account(self, owner_name: str, initial_deposit: float = 0.0) -> Account
```

Behavior:

- Validate owner name is non-empty.
- Validate initial deposit is non-negative.
- Generate unique account ID.
- Create account with cash balance equal to initial deposit.
- Record a `CREATE_ACCOUNT` transaction.
- If initial deposit is greater than zero, either:
  - record the creation transaction with `amount=initial_deposit`, or
  - record a separate `DEPOSIT` transaction.
- Recommended: creation transaction has `amount=initial_deposit`.

Validation:

- Empty owner name -> `ValidationError`.
- Negative initial deposit -> `ValidationError`.

---

### 8.2 Get Account

Signature:

```python
def get_account(self, account_id: str) -> Account
```

Behavior:

- Return account by ID.
- Raise `AccountNotFoundError` if missing.

---

### 8.3 List Accounts

Signature:

```python
def list_accounts(self) -> list[Account]
```

Behavior:

- Return all accounts.

---

### 8.4 Deposit Funds

Signature:

```python
def deposit(self, account_id: str, amount: float) -> Account
```

Behavior:

- Validate account exists.
- Validate amount is positive.
- Increase cash balance.
- Record `DEPOSIT` transaction.
- Return updated account.

Validation:

- Amount less than or equal to zero -> `ValidationError`.

---

### 8.5 Withdraw Funds

Signature:

```python
def withdraw(self, account_id: str, amount: float) -> Account
```

Behavior:

- Validate account exists.
- Validate amount is positive.
- Ensure `cash_balance - amount >= 0`.
- Decrease cash balance.
- Record `WITHDRAW` transaction.
- Return updated account.

Validation:

- Amount less than or equal to zero -> `ValidationError`.
- Withdrawal greater than cash balance -> `InsufficientFundsError`.

Important:

- Withdrawals only consider cash balance.
- Existing share holdings are not automatically liquidated.

---

### 8.6 Buy Shares

Signature:

```python
def buy(self, account_id: str, symbol: str, quantity: int) -> Account
```

Behavior:

- Validate account exists.
- Normalize symbol to uppercase.
- Validate quantity is a positive integer.
- Get current share price from `price_provider`.
- Compute total cost:

```text
cost = share_price * quantity
```

- Ensure cash balance is at least cost.
- Decrease cash balance by cost.
- Increase holding quantity for symbol.
- Record `BUY` transaction.
- Return updated account.

Validation:

- Empty symbol -> `ValidationError`.
- Quantity less than or equal to zero -> `ValidationError`.
- Unknown symbol -> `UnknownSymbolError`.
- Cost greater than cash balance -> `InsufficientFundsError`.

---

### 8.7 Sell Shares

Signature:

```python
def sell(self, account_id: str, symbol: str, quantity: int) -> Account
```

Behavior:

- Validate account exists.
- Normalize symbol to uppercase.
- Validate quantity is a positive integer.
- Ensure account owns at least requested quantity.
- Get current share price from `price_provider`.
- Compute sale proceeds:

```text
proceeds = share_price * quantity
```

- Increase cash balance by proceeds.
- Decrease holding quantity.
- Remove symbol from holdings if quantity becomes zero.
- Record `SELL` transaction.
- Return updated account.

Validation:

- Empty symbol -> `ValidationError`.
- Quantity less than or equal to zero -> `ValidationError`.
- Unknown symbol -> `UnknownSymbolError`.
- Selling more shares than owned -> `InsufficientSharesError`.

---

### 8.8 Get Holdings

Signature:

```python
def get_holdings(
    self,
    account_id: str,
    as_of: datetime | None = None,
) -> dict[str, int]
```

Behavior:

- If `as_of` is `None`, return current holdings.
- If `as_of` is provided, derive holdings from transactions up to and including that timestamp.
- Only `BUY` and `SELL` transactions affect holdings.
- Exclude zero-quantity holdings from result.
- Return a copy, not internal mutable state.

---

### 8.9 Get Cash Balance

Signature:

```python
def get_cash_balance(
    self,
    account_id: str,
    as_of: datetime | None = None,
) -> float
```

Behavior:

- If `as_of` is `None`, return current account cash balance.
- If `as_of` is provided, derive cash balance from transactions up to and including that timestamp.
- Cash impact rules:
  - `CREATE_ACCOUNT`: increase by transaction amount.
  - `DEPOSIT`: increase by amount.
  - `WITHDRAW`: decrease by amount.
  - `BUY`: decrease by amount.
  - `SELL`: increase by amount.

---

### 8.10 Get Portfolio Value

Signature:

```python
def get_portfolio_value(
    self,
    account_id: str,
    as_of: datetime | None = None,
) -> float
```

Behavior:

- Calculate:

```text
cash balance as of time + market value of holdings as of time
```

- Market value uses current `price_provider` prices.
- Because only current prices are available, historical `as_of` reports use historical holdings/cash but current market prices.

Example:

```text
portfolio_value = cash_balance + sum(quantity * current_price(symbol))
```

---

### 8.11 Get Total Deposits

Signature:

```python
def get_total_deposits(
    self,
    account_id: str,
    as_of: datetime | None = None,
) -> float
```

Behavior:

- Sum:
  - `CREATE_ACCOUNT.amount`
  - all `DEPOSIT.amount`
- Include transactions up to `as_of` if provided.

---

### 8.12 Get Total Withdrawals

Signature:

```python
def get_total_withdrawals(
    self,
    account_id: str,
    as_of: datetime | None = None,
) -> float
```

Behavior:

- Sum all `WITHDRAW.amount`.
- Include transactions up to `as_of` if provided.

---

### 8.13 Get Net Contributions

Signature:

```python
def get_net_contributions(
    self,
    account_id: str,
    as_of: datetime | None = None,
) -> float
```

Behavior:

```text
net_contributions = total_deposits - total_withdrawals
```

Purpose:

- Used for profit/loss.
- Prevents additional deposits from being incorrectly counted as investment profit.

---

### 8.14 Get Profit/Loss

Signature:

```python
def get_profit_loss(
    self,
    account_id: str,
    as_of: datetime | None = None,
) -> float
```

Behavior:

```text
profit_loss = portfolio_value - net_contributions
```

This satisfies the requirement to calculate profit/loss from deposited funds while properly accounting for later deposits and withdrawals.

If the product wants strictly “from initial deposit only”, the UI can also show:

```text
portfolio_value - account.initial_deposit
```

But the backend’s primary `get_profit_loss` should use net contributions because it is the financially correct simulation metric.

---

### 8.15 Get Account Summary

Signature:

```python
def get_account_summary(
    self,
    account_id: str,
    as_of: datetime | None = None,
) -> dict[str, Any]
```

Return dictionary keys:

```text
account_id
owner_name
created_at
cash_balance
holdings
holdings_market_value
portfolio_value
initial_deposit
total_deposits
total_withdrawals
net_contributions
profit_loss
```

Behavior:

- Suitable for frontend display.
- Should not expose mutable internal state.

---

### 8.16 List Transactions

Signature:

```python
def list_transactions(
    self,
    account_id: str,
    as_of: datetime | None = None,
) -> list[Transaction]
```

Behavior:

- Return all transactions for account.
- Sort by timestamp ascending, then transaction ID ascending.
- If `as_of` is provided, include only transactions up to and including that timestamp.

---

### 8.17 List Transactions as Dictionaries

Signature:

```python
def list_transactions_as_dicts(
    self,
    account_id: str,
    as_of: datetime | None = None,
) -> list[dict[str, Any]]
```

Behavior:

- Convert transactions to dictionaries suitable for Gradio `Dataframe`.
- Recommended columns:

```text
ID
Timestamp
Type
Symbol
Quantity
Share Price
Amount
Notes
```

---

### 8.18 List Holdings as Dictionaries

Signature:

```python
def list_holdings_as_dicts(
    self,
    account_id: str,
    as_of: datetime | None = None,
) -> list[dict[str, Any]]
```

Behavior:

- Convert holdings to dictionaries suitable for Gradio `Dataframe`.
- Recommended columns:

```text
Symbol
Quantity
Current Price
Market Value
```

---

## 9. Backend Private Helper Methods

The backend engineer may add helper methods.

Recommended signatures:

```python
def _now(self) -> datetime
```

```python
def _generate_account_id(self) -> str
```

```python
def _next_id(self) -> int
```

```python
def _record_transaction(
    self,
    account_id: str,
    transaction_type: TransactionType,
    amount: float = 0.0,
    symbol: str | None = None,
    quantity: int = 0,
    share_price: float | None = None,
    notes: str = "",
) -> Transaction
```

```python
def _validate_positive_amount(self, amount: float, field_name: str = "amount") -> None
```

```python
def _validate_positive_quantity(self, quantity: int) -> None
```

```python
def _normalize_symbol(self, symbol: str) -> str
```

```python
def _transactions_for_account(
    self,
    account_id: str,
    as_of: datetime | None = None,
) -> list[Transaction]
```

---

## 10. Validation Rules

### 10.1 Account Creation

| Condition | Result |
|---|---|
| Owner name empty | `ValidationError` |
| Initial deposit negative | `ValidationError` |
| Initial deposit zero | Allowed |

### 10.2 Deposits

| Condition | Result |
|---|---|
| Amount <= 0 | `ValidationError` |
| Account missing | `AccountNotFoundError` |

### 10.3 Withdrawals

| Condition | Result |
|---|---|
| Amount <= 0 | `ValidationError` |
| Account missing | `AccountNotFoundError` |
| Amount > cash balance | `InsufficientFundsError` |

### 10.4 Buys

| Condition | Result |
|---|---|
| Symbol empty | `ValidationError` |
| Symbol unknown | `UnknownSymbolError` |
| Quantity <= 0 | `ValidationError` |
| Cost > cash balance | `InsufficientFundsError` |

### 10.5 Sells

| Condition | Result |
|---|---|
| Symbol empty | `ValidationError` |
| Symbol unknown | `UnknownSymbolError` |
| Quantity <= 0 | `ValidationError` |
| Quantity > shares owned | `InsufficientSharesError` |

---

## 11. Frontend Design

File:

```text
app.py
```

Use Gradio 6.

The frontend should import:

```python
import gradio as gr
from account_backend import AccountService, AccountError
```

Do not implement business rules in the frontend. All validation should come from backend exceptions.

---

## 12. Gradio 6 API Guidance

The frontend engineer must follow these Gradio 6 rules.

### 12.1 Blocks Construction

Use:

```python
with gr.Blocks() as demo:
```

Do not pass app-level parameters such as `theme`, `css`, or custom JS to `gr.Blocks()`.

In Gradio 6, app-level parameters moved to `launch()`.

Correct:

```python
with gr.Blocks() as demo:
    ...
demo.launch(theme=..., css=...)
```

Avoid:

```python
with gr.Blocks(theme=..., css=...) as demo:
    ...
```

---

### 12.2 Launch Parameters

Use:

```python
demo.launch()
```

If using theme or CSS:

```python
demo.launch(
    theme=gr.themes.Soft(),
    css="...",
)
```

Gradio 6 change:

- `show_api` on `launch()` has been replaced by `footer_links`.
- Do not use `demo.launch(show_api=False)`.

If hiding the API link in the footer, use:

```python
demo.launch(footer_links=["gradio", "settings"])
```

---

### 12.3 Event Listener API

Use event handlers such as:

```python
button.click(
    fn=handler_function,
    inputs=[...],
    outputs=[...],
)
```

Gradio 6 change:

- Event listener parameter `show_api` has been removed.
- `api_name=False` is no longer supported.
- If API visibility is needed, use `api_visibility`.

Allowed values:

```text
public
undocumented
private
```

Recommended for this app:

```python
button.click(
    fn=handler_function,
    inputs=[...],
    outputs=[...],
    api_visibility="private",
)
```

If this causes compatibility issues in the installed sandbox version, omit `api_visibility` entirely.

Do not use:

```python
show_api=False
```

Do not use:

```python
api_name=False
```

---

### 12.4 Components

Recommended components:

```python
gr.Markdown()
gr.Textbox()
gr.Number()
gr.Button()
gr.Dropdown()
gr.Dataframe()
gr.State()
gr.Row()
gr.Column()
gr.Tabs()
gr.Tab()
```

Use `gr.State` to store the `AccountService` object and selected/current account ID.

Recommended state components:

```python
service_state = gr.State(AccountService())
current_account_id_state = gr.State(None)
```

---

### 12.5 Dataframe Guidance

Use `gr.Dataframe` for holdings and transactions.

Recommended construction:

```python
gr.Dataframe(
    headers=[...],
    datatype=[...],
    interactive=False,
)
```

For holdings:

```text
headers = ["Symbol", "Quantity", "Current Price", "Market Value"]
datatype = ["str", "number", "number", "number"]
```

For transactions:

```text
headers = ["ID", "Timestamp", "Type", "Symbol", "Quantity", "Share Price", "Amount", "Notes"]
datatype = ["number", "str", "str", "str", "number", "number", "number", "str"]
```

Handler functions may return:

- `list[list[Any]]`, or
- compatible tabular values.

To keep things simple, frontend handlers should convert backend dicts to `list[list[Any]]`.

---

### 12.6 Dropdown Guidance

Use a dropdown to select account IDs.

Recommended:

```python
account_dropdown = gr.Dropdown(
    label="Account",
    choices=[],
    value=None,
    interactive=True,
)
```

When choices need to be refreshed, return an updated component using:

```python
gr.update(choices=new_choices, value=selected_value)
```

---

## 13. Frontend UI Layout

### 13.1 Overall Layout

Use one Gradio Blocks app with the following sections:

```text
# Trading Simulation Account Manager

Account Management
Trading Actions
Summary
Holdings
Transactions
```

Suggested layout:

```text
Markdown title

Row:
  Account creation panel
  Active account selection panel

Tabs:
  Cash Operations
  Trading
  Portfolio Summary
  Holdings
  Transactions
```

---

## 14. Frontend Handler Function Signatures

All handlers belong in `app.py`.

### 14.1 Account List Helper

Signature:

```python
def get_account_choices(service: AccountService) -> list[str]
```

Return:

```text
["account_id - owner_name", ...]
```

Alternative:

- Use raw account IDs as choices.
- Simpler recommended choice: raw account IDs.

---

### 14.2 Parse Account Choice

If dropdown choices include owner name, define:

```python
def parse_account_id(account_choice: str | None) -> str | None
```

If using raw IDs, this helper can simply return the value.

---

### 14.3 Format Summary

Signature:

```python
def format_summary(summary: dict[str, Any]) -> str
```

Return markdown such as:

```text
### Account Summary

- Account ID: ...
- Owner: ...
- Cash Balance: $...
- Holdings Market Value: $...
- Portfolio Value: $...
- Initial Deposit: $...
- Total Deposits: $...
- Total Withdrawals: $...
- Net Contributions: $...
- Profit/Loss: $...
```

---

### 14.4 Format Holdings Rows

Signature:

```python
def holdings_rows(holdings: list[dict[str, Any]]) -> list[list[Any]]
```

Return rows matching:

```text
Symbol
Quantity
Current Price
Market Value
```

---

### 14.5 Format Transaction Rows

Signature:

```python
def transaction_rows(transactions: list[dict[str, Any]]) -> list[list[Any]]
```

Return rows matching:

```text
ID
Timestamp
Type
Symbol
Quantity
Share Price
Amount
Notes
```

---

### 14.6 Refresh Account View

Signature:

```python
def refresh_account_view(
    service: AccountService,
    account_id: str | None,
) -> tuple[str, list[list[Any]], list[list[Any]], str]
```

Returns:

```text
summary_markdown
holdings_table_rows
transactions_table_rows
status_message
```

Behavior:

- If no account selected, return empty/default view.
- If selected, use backend methods:
  - `get_account_summary`
  - `list_holdings_as_dicts`
  - `list_transactions_as_dicts`

---

### 14.7 Create Account Handler

Signature:

```python
def handle_create_account(
    owner_name: str,
    initial_deposit: float,
    service: AccountService,
) -> tuple[
    AccountService,
    str,
    Any,
    str,
    list[list[Any]],
    list[list[Any]],
    str,
]
```

Inputs:

```text
owner_name
initial_deposit
service_state
```

Outputs:

```text
service_state
current_account_id_state
account_dropdown update
summary_markdown
holdings_dataframe
transactions_dataframe
status_message
```

Behavior:

- Call `service.create_account`.
- Select new account.
- Refresh dropdown choices.
- Refresh summary, holdings, transactions.
- On `AccountError`, return previous state and error status.

---

### 14.8 Select Account Handler

Signature:

```python
def handle_select_account(
    selected_account_id: str | None,
    service: AccountService,
) -> tuple[str | None, str, list[list[Any]], list[list[Any]], str]
```

Inputs:

```text
account_dropdown
service_state
```

Outputs:

```text
current_account_id_state
summary_markdown
holdings_dataframe
transactions_dataframe
status_message
```

Behavior:

- Set current account ID.
- Refresh display.

---

### 14.9 Deposit Handler

Signature:

```python
def handle_deposit(
    amount: float,
    service: AccountService,
    account_id: str | None,
) -> tuple[AccountService, str, list[list[Any]], list[list[Any]], str]
```

Inputs:

```text
deposit_amount
service_state
current_account_id_state
```

Outputs:

```text
service_state
summary_markdown
holdings_dataframe
transactions_dataframe
status_message
```

Behavior:

- Validate account selected.
- Call `service.deposit`.
- Refresh display.

---

### 14.10 Withdraw Handler

Signature:

```python
def handle_withdraw(
    amount: float,
    service: AccountService,
    account_id: str | None,
) -> tuple[AccountService, str, list[list[Any]], list[list[Any]], str]
```

Behavior:

- Validate account selected.
- Call `service.withdraw`.
- Refresh display.
- Display backend error if insufficient funds.

---

### 14.11 Buy Handler

Signature:

```python
def handle_buy(
    symbol: str,
    quantity: int,
    service: AccountService,
    account_id: str | None,
) -> tuple[AccountService, str, list[list[Any]], list[list[Any]], str]
```

Behavior:

- Validate account selected.
- Call `service.buy`.
- Refresh display.
- Display backend error if insufficient funds or unknown symbol.

---

### 14.12 Sell Handler

Signature:

```python
def handle_sell(
    symbol: str,
    quantity: int,
    service: AccountService,
    account_id: str | None,
) -> tuple[AccountService, str, list[list[Any]], list[list[Any]], str]
```

Behavior:

- Validate account selected.
- Call `service.sell`.
- Refresh display.
- Display backend error if insufficient shares or unknown symbol.

---

### 14.13 Manual Refresh Handler

Signature:

```python
def handle_refresh(
    service: AccountService,
    account_id: str | None,
) -> tuple[str, list[list[Any]], list[list[Any]], str]
```

Behavior:

- Refresh summary, holdings, transactions.

---

## 15. Frontend Components

Recommended component IDs/names in `app.py`:

```python
service_state: gr.State
current_account_id_state: gr.State
owner_name_input: gr.Textbox
initial_deposit_input: gr.Number
create_account_button: gr.Button
account_dropdown: gr.Dropdown
summary_markdown: gr.Markdown
status_markdown: gr.Markdown
deposit_amount_input: gr.Number
deposit_button: gr.Button
withdraw_amount_input: gr.Number
withdraw_button: gr.Button
trade_symbol_input: gr.Textbox
trade_quantity_input: gr.Number
buy_button: gr.Button
sell_button: gr.Button
holdings_dataframe: gr.Dataframe
transactions_dataframe: gr.Dataframe
refresh_button: gr.Button
```

Recommended stock symbol helper text:

```text
Available symbols in test price provider: AAPL, TSLA, GOOGL
```

---

## 16. Frontend Event Wiring

### 16.1 Create Account Button

Signature shape:

```python
create_account_button.click(
    fn=handle_create_account,
    inputs=[owner_name_input, initial_deposit_input, service_state],
    outputs=[
        service_state,
        current_account_id_state,
        account_dropdown,
        summary_markdown,
        holdings_dataframe,
        transactions_dataframe,
        status_markdown,
    ],
    api_visibility="private",
)
```

If `api_visibility` causes an issue, remove that kwarg.

---

### 16.2 Account Dropdown Change

Signature shape:

```python
account_dropdown.change(
    fn=handle_select_account,
    inputs=[account_dropdown, service_state],
    outputs=[
        current_account_id_state,
        summary_markdown,
        holdings_dataframe,
        transactions_dataframe,
        status_markdown,
    ],
    api_visibility="private",
)
```

---

### 16.3 Deposit Button

Signature shape:

```python
deposit_button.click(
    fn=handle_deposit,
    inputs=[deposit_amount_input, service_state, current_account_id_state],
    outputs=[
        service_state,
        summary_markdown,
        holdings_dataframe,
        transactions_dataframe,
        status_markdown,
    ],
    api_visibility="private",
)
```

---

### 16.4 Withdraw Button

Signature shape:

```python
withdraw_button.click(
    fn=handle_withdraw,
    inputs=[withdraw_amount_input, service_state, current_account_id_state],
    outputs=[
        service_state,
        summary_markdown,
        holdings_dataframe,
        transactions_dataframe,
        status_markdown,
    ],
    api_visibility="private",
)
```

---

### 16.5 Buy Button

Signature shape:

```python
buy_button.click(
    fn=handle_buy,
    inputs=[trade_symbol_input, trade_quantity_input, service_state, current_account_id_state],
    outputs=[
        service_state,
        summary_markdown,
        holdings_dataframe,
        transactions_dataframe,
        status_markdown,
    ],
    api_visibility="private",
)
```

---

### 16.6 Sell Button

Signature shape:

```python
sell_button.click(
    fn=handle_sell,
    inputs=[trade_symbol_input, trade_quantity_input, service_state, current_account_id_state],
    outputs=[
        service_state,
        summary_markdown,
        holdings_dataframe,
        transactions_dataframe,
        status_markdown,
    ],
    api_visibility="private",
)
```

---

### 16.7 Refresh Button

Signature shape:

```python
refresh_button.click(
    fn=handle_refresh,
    inputs=[service_state, current_account_id_state],
    outputs=[
        summary_markdown,
        holdings_dataframe,
        transactions_dataframe,
        status_markdown,
    ],
    api_visibility="private",
)
```

---

## 17. Test Design

File:

```text
test_account_backend.py
```

Use standard library:

```python
import unittest
```

Do not test Gradio UI.

---

## 18. Backend Unit Test Cases

### 18.1 Account Creation

Test method signatures:

```python
def test_create_account_with_initial_deposit(self) -> None
```

Verify:

- Account is created.
- Cash balance equals initial deposit.
- Initial deposit is stored.
- One transaction exists.
- Portfolio value equals initial deposit.
- Profit/loss initially equals zero.

---

```python
def test_create_account_rejects_negative_initial_deposit(self) -> None
```

Verify:

- Raises `ValidationError`.

---

```python
def test_create_account_rejects_empty_owner_name(self) -> None
```

Verify:

- Raises `ValidationError`.

---

### 18.2 Deposits

```python
def test_deposit_increases_cash_balance_and_records_transaction(self) -> None
```

Verify:

- Cash balance increases.
- Transaction list includes deposit.

---

```python
def test_deposit_rejects_non_positive_amount(self) -> None
```

Verify:

- Zero and negative deposits raise `ValidationError`.

---

### 18.3 Withdrawals

```python
def test_withdraw_decreases_cash_balance_and_records_transaction(self) -> None
```

Verify:

- Cash balance decreases.
- Transaction list includes withdrawal.

---

```python
def test_withdraw_rejects_non_positive_amount(self) -> None
```

Verify:

- Zero and negative withdrawals raise `ValidationError`.

---

```python
def test_withdraw_rejects_amount_greater_than_cash_balance(self) -> None
```

Verify:

- Raises `InsufficientFundsError`.
- Cash balance unchanged.
- No withdrawal transaction recorded.

---

### 18.4 Buys

```python
def test_buy_shares_decreases_cash_and_increases_holdings(self) -> None
```

Example:

- Create account with `$1000`.
- Buy `2` AAPL at `$150`.
- Cash becomes `$700`.
- Holdings `AAPL` equals `2`.
- Buy transaction recorded with amount `$300`.

---

```python
def test_buy_rejects_unknown_symbol(self) -> None
```

Verify:

- Raises `UnknownSymbolError`.

---

```python
def test_buy_rejects_non_positive_quantity(self) -> None
```

Verify:

- Zero and negative quantities raise `ValidationError`.

---

```python
def test_buy_rejects_when_insufficient_cash(self) -> None
```

Verify:

- Raises `InsufficientFundsError`.
- Cash and holdings unchanged.
- No buy transaction recorded.

---

### 18.5 Sells

```python
def test_sell_shares_increases_cash_and_decreases_holdings(self) -> None
```

Example:

- Create account with `$1000`.
- Buy `2` AAPL.
- Sell `1` AAPL.
- Cash increases by `$150`.
- Holdings `AAPL` equals `1`.

---

```python
def test_sell_removes_holding_when_quantity_reaches_zero(self) -> None
```

Verify:

- After selling all shares, symbol is removed from holdings or not returned by `get_holdings`.

---

```python
def test_sell_rejects_more_than_owned(self) -> None
```

Verify:

- Raises `InsufficientSharesError`.
- Cash and holdings unchanged.
- No sell transaction recorded.

---

```python
def test_sell_rejects_unknown_symbol(self) -> None
```

Verify:

- Raises `UnknownSymbolError`.

---

```python
def test_sell_rejects_non_positive_quantity(self) -> None
```

Verify:

- Zero and negative quantities raise `ValidationError`.

---

### 18.6 Portfolio Value

```python
def test_portfolio_value_includes_cash_and_market_value(self) -> None
```

Example:

- Create account with `$1000`.
- Buy `2` AAPL for `$300`.
- Cash `$700`.
- Holdings market value `$300`.
- Portfolio value `$1000`.

---

### 18.7 Profit/Loss

```python
def test_profit_loss_is_zero_when_prices_unchanged(self) -> None
```

Verify:

- With fixed prices and immediate valuation, P/L is zero after buy.

---

```python
def test_profit_loss_uses_net_contributions(self) -> None
```

Example:

- Create account with `$1000`.
- Deposit `$500`.
- Portfolio value should be `$1500`.
- Net contributions should be `$1500`.
- Profit/loss should be `$0`.

---

```python
def test_profit_loss_reflects_price_change_with_custom_price_provider(self) -> None
```

Use custom price provider:

- Buy AAPL at `$100`.
- Later price provider returns `$120`.
- Profit/loss reflects unrealized gain.

Implementation hint:

- Use a mutable dictionary-based price provider in the test.

---

### 18.8 Transaction Listing

```python
def test_list_transactions_returns_all_transactions_in_order(self) -> None
```

Verify:

- Creation, deposit, buy, sell, withdraw appear in order.

---

```python
def test_transaction_records_include_symbol_quantity_price_and_amount(self) -> None
```

Verify:

- Buy/sell transaction fields are populated correctly.

---

### 18.9 As-Of Reporting

Use injected deterministic clock.

Recommended helper class/function in tests:

```python
class FakeClock:
    def __call__(self) -> datetime
    def advance(self, seconds: int) -> None
```

Test signatures:

```python
def test_get_holdings_as_of_time(self) -> None
```

Verify:

- Holdings before buy are empty.
- Holdings after buy include shares.
- Holdings after sell reflect reduced quantity.

---

```python
def test_get_cash_balance_as_of_time(self) -> None
```

Verify:

- Cash is correctly derived at different points.

---

```python
def test_list_transactions_as_of_time(self) -> None
```

Verify:

- Only transactions up to timestamp are returned.

---

## 19. Example Acceptance Flow

The complete system should support this flow:

1. User opens Gradio app.
2. User creates account:
   - Owner: `Alice`
   - Initial deposit: `10000`
3. Summary shows:
   - Cash balance: `$10000`
   - Portfolio value: `$10000`
   - Profit/Loss: `$0`
4. User buys:
   - Symbol: `AAPL`
   - Quantity: `10`
5. Backend uses price `$150`.
6. Cash becomes `$8500`.
7. Holdings show:
   - `AAPL`, quantity `10`, market value `$1500`
8. Portfolio value remains `$10000`.
9. User attempts to buy:
   - Symbol: `GOOGL`
   - Quantity: `100`
10. Backend rejects with `InsufficientFundsError`.
11. User attempts to sell:
   - Symbol: `TSLA`
   - Quantity: `1`
12. Backend rejects with `InsufficientSharesError`.
13. User sells:
   - Symbol: `AAPL`
   - Quantity: `5`
14. Cash becomes `$9250`.
15. Holdings show:
   - `AAPL`, quantity `5`
16. Transactions show creation, buy, sell.
17. User attempts to withdraw `$10000`.
18. Backend rejects because cash balance is only `$9250`.
19. User withdraws `$1000`.
20. Cash becomes `$8250`.
21. Net contributions become `$9000`.
22. Portfolio value is cash `$8250` plus AAPL market value `$750`, total `$9000`.
23. Profit/loss remains `$0` because prices are unchanged.

---

## 20. Done Criteria

### Backend Done

- `account_backend.py` contains all required models, exceptions, service methods, and price provider.
- Invalid operations raise appropriate exceptions.
- Transactions are append-only and listable.
- Holdings and P/L can be reported currently and as-of a timestamp.
- No Gradio imports in backend.

### Frontend Done

- `app.py` launches a working Gradio 6 app.
- User can create account, deposit, withdraw, buy, and sell.
- User can see summary, holdings, and transactions.
- Backend errors are displayed clearly.
- Gradio 6 changes are respected:
  - No `show_api`.
  - No `api_name=False`.
  - App-level settings passed to `launch()`, not `Blocks()`.

### Tests Done

- `test_account_backend.py` exercises backend behavior.
- Tests can run with:

```text
uv run python -m unittest test_account_backend.py
```

- All tests pass.
- Tests cover both success and failure paths.