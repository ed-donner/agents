# Technical Design: `accounts.py` Module

## 1. Overview

This document provides a detailed technical design for the `accounts.py` module. This module is self-contained and encapsulates all the necessary logic for a user's trading account in the simulation platform. It handles cash management (deposits, withdrawals), trade execution (buying, selling shares), and portfolio reporting.

The design is based on the user stories `ACC-002` through `ACC-006`. The core of the module is the `Account` class, which maintains the state of a single user's account, including cash balance, share holdings, and transaction history.

**Developer:** This design is for the backend engineer. Implement the classes, methods, and logic as described below. Pay close attention to the use of the `Decimal` type for financial calculations to ensure accuracy.

## 2. Module Dependencies

The module will require the following standard Python libraries:

```python
import datetime
from decimal import Decimal, ROUND_HALF_UP
from typing import List, Dict, Union, Any
```

## 3. Helper Function

This function is required by the `Account` class to fetch share prices. As per the requirements, a test implementation is provided directly within this module.

### `get_share_price(symbol: str) -> Decimal`

-   **Description**: A mock function that simulates fetching the current market price for a given stock symbol.
-   **Parameters**:
    -   `symbol` (str): The stock ticker symbol (e.g., 'AAPL').
-   **Returns**:
    -   (`Decimal`): The current price per share.
-   **Raises**:
    -   `InvalidSymbolError`: If the symbol is not one of the recognized test symbols.
-   **Implementation Details**:
    -   Uses a predefined dictionary of prices for 'AAPL', 'TSLA', and 'GOOGL'.
    -   The function should be case-insensitive to the symbol.

## 4. Custom Exceptions

To provide clear, specific error feedback to the calling code (e.g., an API layer or UI), we will define the following custom exceptions.

```python
class AccountError(Exception):
    """Base exception for all account-related errors."""
    pass

class InvalidAmountError(AccountError):
    """Raised for invalid deposit or withdrawal amounts (e.g., negative or zero)."""
    pass

class InsufficientFundsError(AccountError):
    """Raised when an operation cannot be completed due to lack of cash."""
    pass

class InsufficientSharesError(AccountError):
    """Raised when attempting to sell more shares than are owned."""
    pass

class InvalidSymbolError(AccountError):
    """Raised when a stock symbol is not found or is invalid."""
    pass
```

## 5. `Account` Class Design

This is the main class of the module, representing a single user's trading account.

### Class: `Account`

-   **Description**: Manages all aspects of a user's trading account, including cash, holdings, transactions, and reporting.

#### `__init__(self, account_holder: str)`

-   **Description**: Initializes a new `Account` instance.
-   **Parameters**:
    -   `account_holder` (str): The name of the person or entity that owns the account.
-   **Instance Attributes**:
    -   `self.account_holder` (str): Stores the name of the account holder.
    -   `self.cash_balance` (Decimal): The user's available cash for trading. Initialized to `Decimal('0.00')`.
    -   `self.holdings` (Dict[str, int]): A dictionary where keys are stock symbols (e.g., 'AAPL') and values are the integer quantity of shares owned.
    -   `self.transactions` (List[Dict[str, Any]]): A chronological list of all transactions that have occurred in the account. Each transaction is a dictionary.

#### Method: `deposit(self, amount: Decimal)`

-   **Description**: Deposits a specified amount of cash into the account. Corresponds to User Story `ACC-002`.
-   **Parameters**:
    -   `amount` (Decimal): The amount of money to deposit.
-   **Returns**:
    -   `None`
-   **Raises**:
    -   `InvalidAmountError`: If the `amount` is less than or equal to zero.
-   **Logic**:
    1.  Validate that `amount > 0`.
    2.  Increase `self.cash_balance` by `amount`.
    3.  Record a 'DEPOSIT' transaction in `self.transactions`.

#### Method: `withdraw(self, amount: Decimal)`

-   **Description**: Withdraws a specified amount of cash from the account. Corresponds to User Story `ACC-003`.
-   **Parameters**:
    -   `amount` (Decimal): The amount of money to withdraw.
-   **Returns**:
    -   `None`
-   **Raises**:
    -   `InvalidAmountError`: If the `amount` is less than or equal to zero.
    -   `InsufficientFundsError`: If the `amount` is greater than `self.cash_balance`.
-   **Logic**:
    1.  Validate that `amount > 0`.
    2.  Validate that `amount <= self.cash_balance`.
    3.  Decrease `self.cash_balance` by `amount`.
    4.  Record a 'WITHDRAW' transaction in `self.transactions`.

#### Method: `buy(self, symbol: str, quantity: int)`

-   **Description**: Executes a buy order for a given quantity of shares. Corresponds to User Story `ACC-004`.
-   **Parameters**:
    -   `symbol` (str): The stock symbol to purchase.
    -   `quantity` (int): The number of shares to purchase.
-   **Returns**:
    -   `None`
-   **Raises**:
    -   `InvalidAmountError`: If `quantity` is less than or equal to zero.
    -   `InvalidSymbolError`: If the `symbol` price cannot be retrieved.
    -   `InsufficientFundsError`: If the total cost of the purchase exceeds the `cash_balance`.
-   **Logic**:
    1.  Validate that `quantity > 0`.
    2.  Call `get_share_price(symbol)` to get the current price. Handle `InvalidSymbolError`.
    3.  Calculate `total_cost = price * quantity`.
    4.  Validate that `total_cost <= self.cash_balance`.
    5.  Decrease `self.cash_balance` by `total_cost`.
    6.  Update `self.holdings`: add `quantity` to the existing holding or create a new entry.
    7.  Record a 'BUY' transaction.

#### Method: `sell(self, symbol: str, quantity: int)`

-   **Description**: Executes a sell order for a given quantity of shares. Corresponds to User Story `ACC-005`.
-   **Parameters**:
    -   `symbol` (str): The stock symbol to sell.
    -   `quantity` (int): The number of shares to sell.
-   **Returns**:
    -   `None`
-   **Raises**:
    -   `InvalidAmountError`: If `quantity` is less than or equal to zero.
    -   `InvalidSymbolError`: If the `symbol` is not found or its price cannot be retrieved.
    -   `InsufficientSharesError`: If the user tries to sell more shares of a symbol than they currently own.
-   **Logic**:
    1.  Validate that `quantity > 0`.
    2.  Normalize the symbol (e.g., to uppercase).
    3.  Validate that the user owns the symbol and that `owned_quantity >= quantity`.
    4.  Call `get_share_price(symbol)` to get the current price. Handle `InvalidSymbolError`.
    5.  Calculate `total_credit = price * quantity`.
    6.  Increase `self.cash_balance` by `total_credit`.
    7.  Update `self.holdings`: decrease the quantity of the holding. If the quantity becomes zero, remove the symbol from the dictionary.
    8.  Record a 'SELL' transaction.

---

### Reporting Methods

These methods provide calculated views of the account's state, corresponding to User Story `ACC-006`.

#### Method: `get_transaction_history(self) -> List[Dict[str, Any]]`

-   **Description**: Returns a copy of the full transaction history for the account.
-   **Parameters**: None.
-   **Returns**:
    -   (`List[Dict]`): A list of all transaction dictionaries.

#### Method: `get_holdings(self) -> Dict[str, int]`

-   **Description**: Returns a copy of the current share holdings.
-   **Parameters**: None.
-   **Returns**:
    -   (`Dict[str, int]`): A dictionary of owned symbols and their quantities.

#### Method: `get_total_deposits(self) -> Decimal`

-   **Description**: Calculates the sum of all 'DEPOSIT' transactions ever made.
-   **Parameters**: None.
-   **Returns**:
    -   (`Decimal`): The total cumulative amount deposited into the account.
-   **Logic**:
    1.  Iterate through `self.transactions`.
    2.  Sum the `amount` for all transactions where `type == 'DEPOSIT'`.

#### Method: `get_portfolio_value(self) -> Dict[str, Decimal]`

-   **Description**: Calculates the current total market value of the account, including cash and all share holdings.
-   **Parameters**: None.
-   **Returns**:
    -   A dictionary containing a breakdown of the portfolio's value:
        -   `'cash'` (Decimal): The current cash balance.
        -   `'holdings_value'` (Decimal): The sum of the market value of all shares.
        -   `'total_value'` (Decimal): The sum of cash and holdings value.
-   **Logic**:
    1.  Initialize `holdings_value = Decimal('0.00')`.
    2.  Iterate through `self.holdings`.
    3.  For each symbol, call `get_share_price(symbol)` and multiply by the quantity. Add this to `holdings_value`.
    4.  Gracefully handle any `InvalidSymbolError` that might occur (e.g., a delisted stock), logging the issue but not crashing the calculation.
    5.  Calculate `total_value = self.cash_balance + holdings_value`.
    6.  Return the structured dictionary.

#### Method: `get_profit_loss(self) -> Decimal`

-   **Description**: Calculates the total profit or loss of the account based on its current value versus the total amount deposited.
-   **Parameters**: None.
--   **Returns**:
    -   (`Decimal`): The profit (positive value) or loss (negative value).
-   **Logic**:
    1.  Call `self.get_portfolio_value()` to get the current total value.
    2.  Call `self.get_total_deposits()` to get the cost basis.
    3.  Calculate `profit_loss = total_value - total_deposits`.
    4.  Return the result.