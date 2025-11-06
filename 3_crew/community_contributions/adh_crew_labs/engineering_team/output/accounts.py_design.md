# Trading Simulation Platform Account Management Module Design

## Module: `accounts.py`

This module provides a complete account management system for a trading simulation platform. It contains all the necessary functionality for managing user accounts, cash balances, portfolio holdings, and transaction history.

## Classes and Methods

### Class: `Account`

The main class that represents a user account in the trading simulation platform.

#### Constructor
```python
def __init__(self, email: str, password: str) -> None
```
- **Purpose**: Creates a new account with the given email and password
- **Parameters**:
  - `email` (str): User's email address (must be unique and valid format)
  - `password` (str): User's password (will be hashed for storage)
- **Raises**: 
  - `ValueError`: If email format is invalid or email already exists
  - `ValueError`: If password is empty or invalid
- **Side Effects**: Initializes account with $0.00 cash balance and empty portfolio

#### Account Management Methods

```python
def get_email(self) -> str
```
- **Purpose**: Returns the account's email address
- **Returns**: Account email as string

```python
def verify_password(self, password: str) -> bool
```
- **Purpose**: Verifies if the provided password matches the account password
- **Parameters**: `password` (str): Password to verify
- **Returns**: True if password matches, False otherwise

```python
def change_password(self, old_password: str, new_password: str) -> bool
```
- **Purpose**: Changes the account password after verifying the old password
- **Parameters**: 
  - `old_password` (str): Current password for verification
  - `new_password` (str): New password to set
- **Returns**: True if password changed successfully, False if old password incorrect
- **Raises**: `ValueError` if new password is invalid

#### Cash Management Methods

```python
def deposit(self, amount: float) -> None
```
- **Purpose**: Deposits funds into the account
- **Parameters**: `amount` (float): Amount to deposit (must be positive)
- **Raises**: `ValueError` if amount is not positive
- **Side Effects**: 
  - Increases cash balance
  - Records DEPOSIT transaction in history

```python
def withdraw(self, amount: float) -> None
```
- **Purpose**: Withdraws funds from the account
- **Parameters**: `amount` (float): Amount to withdraw (must be positive)
- **Raises**: 
  - `ValueError` if amount is not positive
  - `InsufficientFundsError` if withdrawal would result in negative balance
- **Side Effects**: 
  - Decreases cash balance
  - Records WITHDRAWAL transaction in history

```python
def get_cash_balance(self) -> float
```
- **Purpose**: Returns the current cash balance
- **Returns**: Current cash balance as float

#### Trading Methods

```python
def buy_shares(self, symbol: str, quantity: int) -> None
```
- **Purpose**: Purchases shares of a stock if user has sufficient funds
- **Parameters**: 
  - `symbol` (str): Stock symbol (e.g., "AAPL")
  - `quantity` (int): Number of shares to buy (must be positive)
- **Raises**: 
  - `ValueError` if quantity is not positive
  - `InvalidSymbolError` if stock symbol is not found
  - `InsufficientFundsError` if not enough cash for purchase
- **Side Effects**: 
  - Decreases cash balance by (quantity × current_price)
  - Increases holdings for the symbol
  - Records BUY transaction in history
- **Dependencies**: Uses `get_share_price(symbol)` function

```python
def sell_shares(self, symbol: str, quantity: int) -> None
```
- **Purpose**: Sells shares of a stock if user owns sufficient shares
- **Parameters**: 
  - `symbol` (str): Stock symbol (e.g., "AAPL")
  - `quantity` (int): Number of shares to sell (must be positive)
- **Raises**: 
  - `ValueError` if quantity is not positive
  - `InvalidSymbolError` if stock symbol is not found
  - `InsufficientSharesError` if not enough shares owned
- **Side Effects**: 
  - Increases cash balance by (quantity × current_price)
  - Decreases holdings for the symbol
  - Records SELL transaction in history
- **Dependencies**: Uses `get_share_price(symbol)` function

#### Portfolio Methods

```python
def get_holdings(self) -> Dict[str, int]
```
- **Purpose**: Returns current stock holdings
- **Returns**: Dictionary mapping stock symbols to quantities owned

```python
def get_portfolio_value(self) -> float
```
- **Purpose**: Calculates total portfolio value (holdings + cash)
- **Returns**: Total portfolio value as float
- **Dependencies**: Uses `get_share_price(symbol)` for each holding

```python
def get_holdings_value(self) -> float
```
- **Purpose**: Calculates current market value of all holdings (excluding cash)
- **Returns**: Total market value of holdings as float
- **Dependencies**: Uses `get_share_price(symbol)` for each holding

```python
def get_portfolio_summary(self) -> Dict[str, Any]
```
- **Purpose**: Returns comprehensive portfolio summary
- **Returns**: Dictionary containing:
  - `holdings`: Dict of symbol -> {quantity, current_price, current_value}
  - `total_holdings_value`: Total market value of holdings
  - `cash_balance`: Current cash balance
  - `total_portfolio_value`: Holdings value + cash
- **Dependencies**: Uses `get_share_price(symbol)` for each holding

#### Performance Methods

```python
def get_profit_loss(self) -> float
```
- **Purpose**: Calculates total profit/loss since account creation
- **Returns**: Profit (positive) or loss (negative) as float
- **Formula**: Current Portfolio Value - Total Deposits + Total Withdrawals

```python
def get_total_deposits(self) -> float
```
- **Purpose**: Calculates total amount deposited over account lifetime
- **Returns**: Sum of all deposit transactions

```python
def get_total_withdrawals(self) -> float
```
- **Purpose**: Calculates total amount withdrawn over account lifetime
- **Returns**: Sum of all withdrawal transactions

#### Transaction History Methods

```python
def get_transaction_history(self, limit: Optional[int] = None) -> List[Dict[str, Any]]
```
- **Purpose**: Returns transaction history in chronological order (newest first)
- **Parameters**: `limit` (optional int): Maximum number of transactions to return
- **Returns**: List of transaction dictionaries, each containing:
  - `timestamp`: Transaction date/time
  - `type`: "DEPOSIT", "WITHDRAWAL", "BUY", or "SELL"
  - `amount`: Dollar amount (for deposits/withdrawals)
  - `symbol`: Stock symbol (for buy/sell)
  - `quantity`: Share quantity (for buy/sell)
  - `price`: Price per share (for buy/sell)
  - `total_value`: Total transaction value

```python
def get_transactions_by_type(self, transaction_type: str) -> List[Dict[str, Any]]
```
- **Purpose**: Returns filtered transaction history by type
- **Parameters**: `transaction_type` (str): "DEPOSIT", "WITHDRAWAL", "BUY", or "SELL"
- **Returns**: List of transactions matching the specified type

### Exception Classes

Custom exceptions for better error handling:

```python
class InsufficientFundsError(Exception):
    """Raised when user attempts transaction without sufficient cash balance"""
    pass

class InsufficientSharesError(Exception):
    """Raised when user attempts to sell more shares than owned"""
    pass

class InvalidSymbolError(Exception):
    """Raised when user attempts to trade invalid stock symbol"""
    pass
```

### Utility Functions

```python
def get_share_price(symbol: str) -> float
```
- **Purpose**: External function to get current stock price (provided by platform)
- **Parameters**: `symbol` (str): Stock symbol
- **Returns**: Current price per share as float
- **Test Implementation**: Returns fixed prices for AAPL ($150), TSLA ($200), GOOGL ($100)
- **Raises**: `InvalidSymbolError` for unknown symbols

```python
def validate_email(email: str) -> bool
```
- **Purpose**: Validates email format
- **Parameters**: `email` (str): Email to validate
- **Returns**: True if valid format, False otherwise

```python
def hash_password(password: str) -> str
```
- **Purpose**: Hashes password for secure storage
- **Parameters**: `password` (str): Plain text password
- **Returns**: Hashed password string

```python
def verify_password_hash(password: str, hashed: str) -> bool
```
- **Purpose**: Verifies password against hash
- **Parameters**: 
  - `password` (str): Plain text password to verify
  - `hashed` (str): Stored password hash
- **Returns**: True if password matches hash

## Data Storage

The module uses internal data structures to store:
- Account information (email, hashed password)
- Current cash balance
- Stock holdings (symbol -> quantity mapping)
- Transaction history (chronological list of all transactions)

All monetary calculations use appropriate precision handling to avoid floating-point errors.

## Thread Safety

The current implementation is not thread-safe. For concurrent access, appropriate locking mechanisms should be added to critical sections.

## Testing Support

The module is designed to be easily testable with:
- Mock implementations of `get_share_price()`
- Deterministic behavior for all operations
- Clear error conditions and exception handling
- Comprehensive state inspection methods