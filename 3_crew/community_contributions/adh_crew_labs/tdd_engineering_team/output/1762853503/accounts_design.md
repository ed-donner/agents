Thought: I have received all the necessary inputs: User Stories, derived Requirements Analysis (which detailed functional and non-functional needs, dependencies, and priorities), and comprehensive Test Cases (which define expected behavior and edge cases).

My role is to synthesize this information into a comprehensive, implementation-ready technical design document for a self-contained Python module named `accounts`, centered around the `Account` class. I must adhere strictly to the specified format and ensure all constraints (high-precision math, specific error messages, full method signatures) are met.

**Design Strategy:**
1.  **Data Precision:** Use Python's `Decimal` type for all monetary and quantity values (cash, price, cost, holdings) to meet NFR-1.1.
2.  **Dependencies:** Define a clear interface for the external price lookup function (`get_share_price`) and include a test implementation within the module for self-containment/testing.
3.  **Core Class (`Account`):** This class will manage state (`cash_balance`, `holdings`, `transactions`, `deposits_baseline`) and encapsulate all business logic (deposit, withdraw, buy, sell, reporting).
4.  **Data Structures:** Define robust `TypedDict` or small data classes (`TransactionRecord`, `HoldingDetail`) to ensure schema clarity.
5.  **Error Handling:** Implement custom exceptions to handle specific error conditions (InsufficientFunds, InvalidSymbol, InsufficientHoldings, InvalidAmount) as required by the user stories and acceptance criteria.

**Step-by-Step Implementation Outline:**

1.  **Module Setup:** Define imports (Decimal, typing).
2.  **External Dependency Mock:** Create the required `get_share_price` function.
3.  **Custom Exceptions:** Define specific error classes.
4.  **Data Models:** Define `TransactionType` enum and `TransactionRecord` schema.
5.  **Main Class (`Account`):**
    *   `__init__`: Initialize state (cash=0, holdings={}, deposits=0, transactions=[]).
    *   `deposit(amount)`: Update cash, update deposits baseline, log transaction.
    *   `withdraw(amount)`: Check FR-2.2 (overdraft), check FR-2.3 (positive amount), update cash, log transaction.
    *   `buy_shares(symbol, quantity)`: Check FR-3.3 (valid symbol), look up price, check FR-3.2 (affordability), update cash and holdings, log transaction.
    *   `sell_shares(symbol, quantity)`: Check FR-4.2 (possession), check FR-3.3 (valid symbol), look up price, update cash and holdings, log transaction.
    *   `get_holdings_report()`: Implement FR-5.4 (detail per symbol).
    *   `get_portfolio_summary()`: Implement FR-5.1 (TPV), FR-5.2/FR-5.3 (P&L calculation).
    *   `get_transaction_history()`: Return transaction list.

I will now compile the final design document following the required markdown structure.

---
*(Self-Correction during design): Ensure quantity tracking in holdings uses Decimal for high precision, though typical shares are integers, allowing for fractional share support if the platform expands, aligning with high data precision NFR-1.1.* I will treat quantity as `Decimal`.

---
*(Self-Correction on `get_share_price`): The original requirement states, "The system has access to a function get_share_price(symbol) which returns the current price of a share, and includes a test implementation that returns fixed prices for AAPL, TSLA, GOOGL." I must include this mock implementation.*

---
The design is complete and ready for formatting.# Technical Design Document: Accounts Management Module

**Document Version:** 1.0
**Engineering Lead:** [Your Name/Role]
**Date:** October 26, 2023

## 1. Overview & Architecture

This document specifies the technical design for the `accounts` module, providing core account management, fund operation, and trading simulation capabilities for a trading platform. The design prioritizes data integrity (using high-precision decimals) and enforces critical financial constraints (no overdraft, no selling unowned shares).

The architecture is a single, self-contained Python module (`accounts.py`) centered around the `Account` class, which serves as the aggregate root for all financial state (cash, holdings, transactions, deposits baseline).

### Key Design Principles

1.  **High Precision:** All financial calculations and persistent states (cash, holdings quantity, prices) utilize Python's `decimal.Decimal` type (NFR-1.1).
2.  **Self-Containment:** The module includes a test implementation for external dependencies (`get_share_price`) to facilitate immediate unit testing and integration.
3.  **Constraint Enforcement:** Custom exceptions are raised immediately upon violation of core constraints (e.g., Insufficient funds, Insufficient holdings).

## 2. Module Structure

The `accounts.py` module will contain utility functions, data model definitions, custom exceptions, and the primary `Account` class.

```python
# accounts.py Structure
import decimal
import time
from typing import Dict, List, TypedDict, Optional, Callable
from enum import Enum

# 1. Custom Exceptions
class AccountError(Exception): pass
class InsufficientFunds(AccountError): pass
class InsufficientHoldings(AccountError): pass
class InvalidSymbol(AccountError): pass
class InvalidAmount(AccountError): pass

# 2. External Dependency Mock/Interface (D-1)
def get_share_price(symbol: str) -> decimal.Decimal: ...

# 3. Data Models (Schemas)
class TransactionType(Enum): pass
class TransactionRecord(TypedDict): pass
class HoldingDetail(TypedDict): pass
class PortfolioSummary(TypedDict): pass

# 4. Primary Class
class Account:
    def __init__(self, user_id: str): ...
    # Funds Management
    def deposit(self, amount: decimal.Decimal) -> None: ...
    def withdraw(self, amount: decimal.Decimal) -> None: ...
    # Trading
    def buy_shares(self, symbol: str, quantity: decimal.Decimal) -> None: ...
    def sell_shares(self, symbol: str, quantity: decimal.Decimal) -> None: ...
    # Reporting
    def get_transaction_history(self) -> List[TransactionRecord]: ...
    def get_holdings_report(self) -> Dict[str, HoldingDetail]: ...
    def get_portfolio_summary(self) -> PortfolioSummary: ...
```

## 3. Class Definitions

### 3.1 Primary Class: `Account`

Encapsulates all account state and business logic (FR-1.1).

| Property | Type | Description | Initial Value |
| :--- | :--- | :--- | :--- |
| `user_id` | `str` | Unique identifier for the account (FR-1.2). | Provided upon creation. |
| `cash_balance` | `decimal.Decimal` | Current available cash (NFR-1.1). | `Decimal('0.0000')` |
| `holdings` | `Dict[str, decimal.Decimal]` | Shares owned: `{SYMBOL: QUANTITY}` (NFR-1.1). | `{}` |
| `transactions` | `List[TransactionRecord]` | History of all deposits, withdrawals, buys, and sells. | `[]` |
| `deposits_baseline` | `decimal.Decimal` | Running sum of all 'Deposit' transactions (for P&L calculation, FR-5.3). | `Decimal('0.0000')` |

#### Public Methods

| Signature | Functionality Description | Exceptions Raised | Traceability |
| :--- | :--- | :--- | :--- |
| `__init__(self, user_id: str)` | Initializes the account with zero balance, empty holdings, and an empty history. | | FR-1.1, FR-1.3 |
| `deposit(self, amount: decimal.Decimal)` | Increases cash balance and updates the deposits baseline. Requires `amount > 0`. | `InvalidAmount` (if amount <= 0) | FR-2.3 |
| `withdraw(self, amount: decimal.Decimal)` | Reduces cash balance. Enforces constraint: resulting balance must not be negative. | `InvalidAmount`, `InsufficientFunds` | FR-2.1, FR-2.2 |
| `buy_shares(self, symbol: str, quantity: decimal.Decimal)` | Executes a buy trade. Calculates cost, checks affordability, updates holdings and cash. | `InvalidSymbol`, `InvalidAmount`, `InsufficientFunds` | FR-3.1, FR-3.2, FR-3.3 |
| `sell_shares(self, symbol: str, quantity: decimal.Decimal)` | Executes a sell trade. Checks possession, calculates proceeds, updates holdings and cash. | `InvalidSymbol`, `InvalidAmount`, `InsufficientHoldings` | FR-4.1, FR-4.2 |
| `get_transaction_history(self)` | Returns a chronological list of all recorded transactions. | | AC-1.2 |
| `get_holdings_report(self)` | Generates a report detailing current holdings, current price, and individual market values. Requires `get_share_price`. | | FR-5.4 |
| `get_portfolio_summary(self)` | Calculates and returns Total Portfolio Value (TPV) and Profit/Loss (P&L). | | FR-5.1, FR-5.2 |

#### Method Signatures and Docstrings

```python
class Account:
    def __init__(self, user_id: str):
        """
        Initializes a new trading simulation account.

        Args:
            user_id: A unique identifier for the user.
        
        Note: Assumes ID uniqueness check (FR-1.2) is handled externally during registration 
              if using a persistent store, otherwise, this implementation skips it for simplicity.
        """
        self.user_id = user_id
        self.cash_balance: decimal.Decimal = decimal.Decimal('0.0000')
        self.holdings: Dict[str, decimal.Decimal] = {}  # {SYMBOL: QUANTITY}
        self.transactions: List['TransactionRecord'] = []
        self.deposits_baseline: decimal.Decimal = decimal.Decimal('0.0000')

    def deposit(self, amount: decimal.Decimal) -> None:
        """
        Adds funds to the cash balance and tracks the total deposits baseline.

        Args:
            amount: The positive amount to deposit (NFR-1.1).

        Raises:
            InvalidAmount: If amount is less than or equal to zero.
        """
        # Implementation Detail: Requires amount validation (FR-2.3 equivalent for Deposit)
        pass

    def withdraw(self, amount: decimal.Decimal) -> None:
        """
        Withdraws funds from the cash balance. Prevents overdraft (C-2).

        Args:
            amount: The positive amount to withdraw.

        Raises:
            InvalidAmount: If amount is less than or equal to zero (FR-2.3).
            InsufficientFunds: If withdrawal exceeds current balance (FR-2.2).
        """
        pass

    def buy_shares(self, symbol: str, quantity: decimal.Decimal) -> None:
        """
        Executes a buy order. Debits cash and credits holdings. Enforces affordability (C-2).

        Args:
            symbol: The ticker symbol of the share (e.g., 'AAPL').
            quantity: The number of shares to buy.

        Raises:
            InvalidAmount: If quantity is less than or equal to zero.
            InvalidSymbol: If the symbol price cannot be retrieved (FR-3.3).
            InsufficientFunds: If total cost exceeds cash balance (FR-3.2).
        """
        pass

    def sell_shares(self, symbol: str, quantity: decimal.Decimal) -> None:
        """
        Executes a sell order. Credits cash and debits holdings. Enforces possession (C-1).

        Args:
            symbol: The ticker symbol of the share.
            quantity: The number of shares to sell.

        Raises:
            InvalidAmount: If quantity is less than or equal to zero.
            InvalidSymbol: If the symbol price cannot be retrieved (FR-3.3/FR-4.4).
            InsufficientHoldings: If user attempts to sell more than they possess (FR-4.2).
        """
        pass

    def get_transaction_history(self) -> List['TransactionRecord']:
        """Returns the full chronological list of all transactions."""
        return self.transactions

    def get_holdings_report(self) -> Dict[str, 'HoldingDetail']:
        """
        Generates a detailed report of current share holdings including market value (FR-5.4).
        Requires real-time price lookup (D-1).

        Returns:
            A dictionary mapping symbol to HoldingDetail.
        """
        # Implementation Detail: Iterates through self.holdings and calls get_share_price for each symbol.
        pass

    def get_portfolio_summary(self) -> 'PortfolioSummary':
        """
        Calculates and returns the Total Portfolio Value (TPV) and Profit/Loss (P&L) (FR-5.1, FR-5.2).

        Returns:
            A dictionary containing summary metrics.
        """
        # Implementation Detail: Calls get_holdings_report internally to get TPV components.
        pass

```

## 4. Function Definitions (Module-Level Utilities)

### 4.1 External Dependency Mock: `get_share_price` (D-1)

This function simulates an external market data service required for trading and reporting (FR-3.1, FR-4.1, FR-5.1).

```python
FIXED_PRICES = {
    'AAPL': decimal.Decimal('150.0000'),  # Used for testing AC-3.2, AC-4.1
    'TSLA': decimal.Decimal('195.0000'),  # Used for testing AC-3.3
    'GOOGL': decimal.Decimal('130.0000'), # Used for testing AC-3.4, AC-4.6
    # Adding a few more for broader test coverage/reporting simulation
    'MSFT': decimal.Decimal('300.5000'),
    'AMD': decimal.Decimal('100.0000'),
    'XOM': decimal.Decimal('500.0000') # Used for RPT-TC-014
}

def get_share_price(symbol: str) -> decimal.Decimal:
    """
    Simulates retrieving the current market price for a given stock symbol.
    
    Args:
        symbol: The ticker symbol (case insensitive).

    Returns:
        The price as a Decimal.

    Raises:
        InvalidSymbol: If the symbol is not found in the fixed price list.
    """
    price = FIXED_PRICES.get(symbol.upper())
    if price is None:
        # Implements FR-3.3 / FR-3.6 / FR-4.4
        raise InvalidSymbol(f"Invalid or unsupported share symbol: {symbol}")
    return price
```

## 5. Data Models/Schemas

All monetary values (`amount`, `price`, `cost`, `value`) and share quantities (`quantity`) MUST use `decimal.Decimal` (NFR-1.1).

### 5.1 Enumeration: `TransactionType`

```python
class TransactionType(Enum):
    DEPOSIT = "DEPOSIT"
    WITHDRAWAL = "WITHDRAWAL"
    BUY = "BUY"
    SELL = "SELL"
```

### 5.2 Transaction Schema: `TransactionRecord`

Used for logging all financial operations (FR-2.4, FR-3.4, FR-4.3).

```python
class TransactionRecord(TypedDict):
    id: str  # Unique transaction ID (e.g., UUID or sequential, implementation detail)
    timestamp: float # Unix epoch time of execution
    type: TransactionType
    symbol: Optional[str] # Required for BUY/SELL
    quantity: Optional[decimal.Decimal] # Required for BUY/SELL
    price: Optional[decimal.Decimal] # Execution price for BUY/SELL
    amount: decimal.Decimal # Cash impact (positive for deposit/sell proceeds, negative for withdrawal/buy cost)
    details: str # Short description/message
```

### 5.3 Holdings Detail Schema: `HoldingDetail`

Used within the `get_holdings_report` output (FR-5.4).

```python
class HoldingDetail(TypedDict):
    symbol: str
    quantity: decimal.Decimal
    current_price: decimal.Decimal
    market_value: decimal.Decimal # quantity * current_price
```

### 5.4 Portfolio Summary Schema: `PortfolioSummary`

Used for the `get_portfolio_summary` output (FR-5.1, FR-5.2).

```python
class PortfolioSummary(TypedDict):
    cash_balance: decimal.Decimal
    total_market_value: decimal.Decimal # Sum of all HoldingDetail['market_value']
    total_portfolio_value: decimal.Decimal # cash_balance + total_market_value
    total_deposits_baseline: decimal.Decimal # Running sum of deposits (FR-5.3)
    profit_loss: decimal.Decimal # total_portfolio_value - total_deposits_baseline
```

## 6. Error Handling Strategy

The system uses specific custom exceptions derived from a base `AccountError` to clearly signal the reason for transaction rejection, aligning with specific acceptance criteria error messages (NFR-1.3).

| Exception Class | Triggers/Condition | Required Error Message Content | Traceability |
| :--- | :--- | :--- | :--- |
| `InsufficientFunds` | Withdrawal amount > Cash Balance. Total Cost > Cash Balance. | "Insufficient funds" or "Insufficient funds to cover trade cost" | FR-2.2, FR-3.2 |
| `InsufficientHoldings` | Sell Quantity > Held Quantity for that Symbol. | "Insufficient holdings for [Symbol]" | FR-4.2 |
| `InvalidSymbol` | `get_share_price` cannot resolve the provided symbol. | "Invalid or unsupported share symbol: [Symbol]" | FR-3.3, FR-4.4 |
| `InvalidAmount` | Attempt to deposit, withdraw, buy, or sell with quantity/amount <= 0. | "Amount must be positive" or "Quantity must be positive" | FR-2.3 |
| `AccountError` | General base class for unexpected account-related failures. | (Used internally/for logging) | N/A |

## 7. Usage Examples

The following example demonstrates setting up an account, performing a trade, and requesting a portfolio report.

```python
from accounts import Account, decimal, InvalidSymbol, InsufficientFunds, get_share_price

# Set up an account
user_id = "test_user_alpha"
try:
    account = Account(user_id)
    print(f"Account {user_id} created. Initial balance: {account.cash_balance}")
    
    # 1. Deposit Funds
    deposit_amount = decimal.Decimal('5000.00')
    account.deposit(deposit_amount)
    print(f"Deposited {deposit_amount}. New balance: {account.cash_balance}")
    
    # 2. Buy Shares (AAPL @ 150.00)
    symbol_buy = 'AAPL'
    quantity_buy = decimal.Decimal('10')
    
    current_price = get_share_price(symbol_buy)
    cost = current_price * quantity_buy # 1500.00
    
    account.buy_shares(symbol_buy, quantity_buy)
    print(f"Bought 10 {symbol_buy}. Cost: {cost}. Balance: {account.cash_balance}")
    
    # 3. Request Summary (Initial P&L Check)
    summary = account.get_portfolio_summary()
    print("\n--- Portfolio Summary ---")
    print(f"Holdings Value: {summary['total_market_value']}")
    print(f"Total Value: {summary['total_portfolio_value']}")
    # Should be 0.00 if we assume price hasn't moved since buy
    print(f"P&L: {summary['profit_loss']}") 

except (InvalidSymbol, InsufficientFunds, Exception) as e:
    print(f"An error occurred: {e}")
```

## 8. Testing Recommendations

The design supports direct unit testing using the included `get_share_price` mock and the stateful nature of the `Account` class.

1.  **Unit Tests (State Validation):**
    *   Test all boundary conditions defined in the Test Case Specification (e.g., FW-TC-004: exact zero withdrawal; BUY-TC-008: exact zero cash balance purchase).
    *   Validate the use of `Decimal` for all inputs and outputs to prevent precision errors (NFR-1.1).
    *   Verify that internal state (`cash_balance`, `holdings`, `deposits_baseline`) is updated correctly after each transaction.
2.  **Error Handling Tests:**
    *   Specifically test that the correct custom exceptions are raised with the exact required error messages for all failure scenarios (InsufficientFunds, InsufficientHoldings, InvalidSymbol).
3.  **Reporting Tests (TS-5.1, TS-5.2):**
    *   Test P&L calculation after multiple deposits, withdrawals, buys, and sells, ensuring the `deposits_baseline` is correctly tracked and used (FR-5.3).
    *   Use different `get_share_price` values in reporting tests to simulate market fluctuations and verify TPV calculation.
4.  **Transaction History Tests:**
    *   Verify that every successful operation (deposit, withdraw, buy, sell) generates a complete `TransactionRecord` entry (FR-2.4, FR-3.4, FR-4.3).

## 9. Integration Guidelines

### 9.1 Data Persistence Layer (External)

The current `Account` class is in-memory. For integration with a production backend (e.g., SQLAlchemy/PostgreSQL), the following guidelines apply:

1.  **Data Type Mapping:** Map Python `decimal.Decimal` state variables (cash, deposits, holdings quantities) directly to SQL `DECIMAL(19, 4)` fields (NFR-1.1).
2.  **Atomicity (D-4):** Buy and Sell operations must be wrapped in a database transaction block to ensure that both the cash debit/credit and the holdings update commit or rollback simultaneously.
3.  **Unique ID (FR-1.2):** Ensure the database layer enforces uniqueness on the `user_id` upon account creation to prevent duplicates.

### 9.2 Price Retrieval Service Integration (D-1)

If integrating with a real market data service, the `get_share_price` module function should be replaced by a connector or client call. The connector must maintain the specified signature (`symbol: str -> decimal.Decimal`) and must raise an appropriate exception (e.g., `InvalidSymbol`) if the symbol is unsupported or the API call fails.

### 9.3 UI/CLI Integration

The UI/CLI should leverage the methods as follows:

1.  **Balance Display (NFR-1.4):** Display `account.cash_balance` directly before withdrawal or buy actions.
2.  **Trading Feedback:** Use the raised exceptions (`InsufficientFunds`, `InsufficientHoldings`) to drive user-facing error messages (NFR-1.3).
3.  **Reporting:** `get_portfolio_summary()` provides all necessary high-level metrics for a dashboard view.