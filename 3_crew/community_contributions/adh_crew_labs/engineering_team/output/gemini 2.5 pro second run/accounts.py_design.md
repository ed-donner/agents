# Backend Design: `accounts.py` Module

## 1. Overview

This document provides a detailed technical design for the `accounts.py` module, which will serve as the core logic for the trading simulation platform's account management system. This design is intended for the backend engineer responsible for its implementation.

The module will be entirely self-contained, encapsulating all necessary logic for account creation, fund management, trading, and reporting. It will expose a single class, `Account`, and a helper function `get_share_price` for interaction.

## 2. Module: `accounts.py`

This module will contain all the business logic for a user's trading account.

### 2.1. Dependencies

The module will use the following standard Python libraries:

-   `datetime`: For timestamping transactions.
-   `decimal`: To handle all monetary values with precision, avoiding floating-point errors. Recommended for all financial calculations.
-   `typing`: For type hints (`Dict`, `List`, `NamedTuple`, `Optional`) to improve code clarity and maintainability.

### 2.2. Custom Exceptions

To provide clear, specific error feedback, we will define custom exception classes. This allows the calling code (e.g., an API layer) to catch specific errors and return appropriate user-facing messages.

```python
# Custom exceptions for clear error handling
class InsufficientFundsError(Exception):
    """Raised when an action cannot be completed due to lack of cash."""
    pass

class InsufficientSharesError(Exception):
    """Raised when trying to sell more shares than owned."""
    pass

class InvalidSymbolError(Exception):
    """Raised when a stock symbol is not found in the price source."""
    pass

class InvalidQuantityError(Exception):
    """Raised when a quantity less than or equal to zero is provided."""
    pass
```

### 2.3. Helper Function: `get_share_price`

As required, this function will simulate a stock market price feed. For initial development and testing, it will return fixed prices for a predefined set of symbols and raise an error for any unknown symbol.

```python
from decimal import Decimal

def get_share_price(symbol: str) -> Decimal:
    """
    Retrieves the current market price for a given stock symbol.

    This is a mock implementation for simulation purposes.

    Args:
        symbol: The stock symbol (e.g., 'AAPL').

    Returns:
        The price of one share as a Decimal object.

    Raises:
        InvalidSymbolError: If the symbol is not recognized.
    """
```

### 2.4. Data Structure: `Transaction`

A `NamedTuple` will be used to represent a single transaction. This provides an immutable, readable structure for transaction records.

```python
from typing import NamedTuple
from datetime import datetime
from decimal import Decimal

class Transaction(NamedTuple):
    """
    Represents a single financial transaction in the account history.
    """
    timestamp: datetime
    type: str  # e.g., 'DEPOSIT', 'WITHDRAW', 'BUY', 'SELL'
    symbol: Optional[str]
    quantity: Optional[int]
    share_price: Optional[Decimal]
    total_value: Decimal
```

## 3. Class: `Account`

This is the main class of the module, representing a single user's trading account.

### 3.1. Class Definition

```python
class Account:
    """
    Manages a user's trading account, including cash, holdings,
    and transaction history.
    """
```

### 3.2. Constructor: `__init__`

The constructor initializes a new account. As per `ACC-001`, a new account starts with a zero balance and no holdings.

```python
def __init__(self, user_id: str):
    """
    Initializes a new trading account.

    Args:
        user_id: A unique identifier for the user.
    """
    self.user_id: str = user_id
    self.cash: Decimal = Decimal('0.00')
    self.holdings: Dict[str, int] = {} # Maps symbol -> quantity
    self.transactions: List[Transaction] = []
    
    # Internal ledgers for P/L calculation
    self._total_deposits: Decimal = Decimal('0.00')
    self._total_withdrawals: Decimal = Decimal('0.00')
```

### 3.3. Methods

#### 3.3.1. Fund Management (ACC-002, ACC-003)

**`deposit(amount: Decimal)`**

-   **Description**: Adds funds to the account's cash balance.
-   **User Story**: `ACC-002`
-   **Parameters**:
    -   `amount` (`Decimal`): The amount of money to deposit.
-   **Behavior**:
    1.  Validates that `amount` is a positive number. Raises `ValueError` if not.
    2.  Increases `self.cash` by `amount`.
    3.  Increases `self._total_deposits` by `amount`.
    4.  Creates a `Transaction` of type 'DEPOSIT' and prepends it to `self.transactions`.
-   **Returns**: `None`

**`withdraw(amount: Decimal)`**

-   **Description**: Removes funds from the account's cash balance.
-   **User Story**: `ACC-003`
-   **Parameters**:
    -   `amount` (`Decimal`): The amount of money to withdraw.
-   **Behavior**:
    1.  Validates that `amount` is a positive number. Raises `ValueError` if not.
    2.  Validates that `amount` does not exceed `self.cash`. Raises `InsufficientFundsError` if it does.
    3.  Decreases `self.cash` by `amount`.
    4.  Increases `self._total_withdrawals` by `amount`.
    5.  Creates a `Transaction` of type 'WITHDRAW' and prepends it to `self.transactions`.
-   **Returns**: `None`

#### 3.3.2. Trading (ACC-004, ACC-005)

**`buy_shares(symbol: str, quantity: int)`**

-   **Description**: Purchases a specified quantity of shares for a given stock symbol.
-   **User Story**: `ACC-004`
-   **Parameters**:
    -   `symbol` (`str`): The stock symbol to buy (e.g., 'AAPL').
    -   `quantity` (`int`): The number of shares to purchase.
-   **Behavior**:
    1.  Validates that `quantity` is greater than 0. Raises `InvalidQuantityError` if not.
    2.  Calls `get_share_price(symbol)` to get the current price. Catches `InvalidSymbolError` and re-raises it.
    3.  Calculates `total_cost = price * quantity`.
    4.  Validates that `total_cost` does not exceed `self.cash`. Raises `InsufficientFundsError` if it doesn't.
    5.  Decreases `self.cash` by `total_cost`.
    6.  Updates `self.holdings`: adds `quantity` to the existing holding or creates a new entry.
    7.  Creates a `Transaction` of type 'BUY' and prepends it to `self.transactions`.
-   **Returns**: `None`

**`sell_shares(symbol: str, quantity: int)`**

-   **Description**: Sells a specified quantity of owned shares.
-   **User Story**: `ACC-005`
-   **Parameters**:
    -   `symbol` (`str`): The stock symbol to sell.
    -   `quantity` (`int`): The number of shares to sell.
-   **Behavior**:
    1.  Validates that `quantity` is greater than 0. Raises `InvalidQuantityError` if not.
    2.  Validates that `symbol` exists in `self.holdings` and that the owned quantity is `>= quantity`. Raises `InsufficientSharesError` if not.
    3.  Calls `get_share_price(symbol)` to get the current price.
    4.  Calculates `total_sale_value = price * quantity`.
    5.  Increases `self.cash` by `total_sale_value`.
    6.  Updates `self.holdings`: subtracts `quantity`. If the resulting quantity is 0, the symbol is removed from the dictionary.
    7.  Creates a `Transaction` of type 'SELL' and prepends it to `self.transactions`.
-   **Returns**: `None`

#### 3.3.3. Reporting & View Methods (ACC-006, ACC-007)

**`get_holdings_value() -> Decimal`**

-   **Description**: Calculates the total market value of all shares currently held in the account.
-   **User Story**: Component of `ACC-006`
-   **Parameters**: None
-   **Behavior**:
    1.  Initializes `total_value` to `Decimal('0.00')`.
    2.  Iterates through `self.holdings`.
    3.  For each symbol, calls `get_share_price()` and multiplies by the quantity.
    4.  Adds this sub-total to `total_value`.
-   **Returns**: `Decimal` representing the total value of all stock holdings.

**`get_total_portfolio_value() -> Decimal`**

-   **Description**: Calculates the entire net worth of the account (cash + holdings).
-   **User Story**: `ACC-006`
-   **Parameters**: None
-   **Behavior**:
    1.  Calls `self.get_holdings_value()`.
    2.  Returns the sum of `self.cash` and the holdings value.
-   **Returns**: `Decimal` representing the total account value.

**`get_profit_or_loss() -> Decimal`**

-   **Description**: Calculates the total profit or loss relative to the net amount deposited.
-   **User Story**: `ACC-006`
-   **Parameters**: None
-   **Behavior**:
    1.  Calculates `net_deposits = self._total_deposits - self._total_withdrawals`.
    2.  Calculates `current_value = self.get_total_portfolio_value()`.
    3.  Returns `current_value - net_deposits`.
-   **Returns**: `Decimal` representing the profit (if positive) or loss (if negative).

**`get_holdings_summary() -> Dict[str, Dict]`**

-   **Description**: Provides a detailed summary of each holding, including its current market value.
-   **User Story**: Component of `ACC-006`.
-   **Parameters**: None
-   **Behavior**:
    1.  Creates an empty dictionary `summary`.
    2.  Iterates through `self.holdings`.
    3.  For each `symbol, quantity` pair:
        -   Gets the current `price` from `get_share_price()`.
        -   Calculates `total_value = price * quantity`.
        -   Adds an entry to `summary`: `symbol: {'quantity': quantity, 'current_price': price, 'total_value': total_value}`.
-   **Returns**: A dictionary where keys are stock symbols and values are dictionaries containing details about that holding.

**`get_transaction_history() -> List[Transaction]`**

-   **Description**: Returns a complete history of all transactions for the account.
-   **User Story**: `ACC-007`
-   **Parameters**: None
-   **Behavior**:
    1.  Returns a copy of the `self.transactions` list.
-   **Returns**: A list of `Transaction` named tuples, in reverse chronological order.