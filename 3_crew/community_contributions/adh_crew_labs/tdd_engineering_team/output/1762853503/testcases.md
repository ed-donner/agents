## Test Case Specification: Trading Simulation Core Features

This document provides comprehensive test cases in BDD Gherkin format, covering functional requirements (FR), boundary conditions, and negative scenarios derived from the analysis of the core trading platform requirements.

---

### Feature: Account Management and Initialization

This feature ensures that new users can register successfully and that core account properties (cash balance, uniqueness) are correctly initialized and enforced (FR-1.1, FR-1.2, FR-1.3).

| Requirement Traceability | FR-1.1, FR-1.3, NFR-1.1 |
| :--- | :--- |
| **TC ID** | **AM-TC-001** |
| **Scenario** | **Successful Account Creation with Zero Initialization** |
| **Precondition** | The user ID `test_new_user_01` does not exist in the system. |
| **Test Data** | User ID: `test_new_user_01` |
| **Type** | Positive (Happy Path) |

```gherkin
Scenario: AM-TC-001 - Successful Account Creation with Zero Initialization
  Given the system is ready for user registration
  When a new user attempts to register with ID "test_new_user_01"
  Then the registration should be successful
  And the account state should show:
    | Metric | Expected Value | Traceability |
    | Cash Balance | 0.0000 | AC-1.1, NFR-1.1 |
    | Total Holdings | 0 | AC-1.3 |
    | Transaction History | Empty List | AC-1.2 |
```

| Requirement Traceability | FR-1.2 |
| :--- | :--- |
| **TC ID** | **AM-TC-002** |
| **Scenario** | **Rejecting Registration for Duplicate User ID** |
| **Precondition** | User ID `test_duplicate_user` already exists in the system. |
| **Test Data** | User ID: `test_duplicate_user` |
| **Type** | Negative (Error Scenario) |

```gherkin
Scenario: AM-TC-002 - Rejecting Registration for Duplicate User ID
  Given the user "test_duplicate_user" already exists
  When a second request attempts to register with the ID "test_duplicate_user"
  Then the system must return a rejection status
  And the error message should be "User ID already exists"
  And the existing account state must remain unchanged
```

---

### Feature: Fund Withdrawal Operations

This feature validates the ability to withdraw funds, focusing on boundary conditions and preventing overdrafts or invalid transactions (FR-2.1, FR-2.2, FR-2.3, FR-2.4).

| Requirement Traceability | FR-2.1, FR-2.4 |
| :--- | :--- |
| **TC ID** | **FW-TC-003** |
| **Scenario** | **Successful Withdrawal Leaving a Positive Balance** |
| **Precondition** | User `test_funder_01` has an initial balance of $1000.0000. |
| **Test Data** | Withdrawal Amount: 500.50 |
| **Type** | Positive (Happy Path) |

```gherkin
Scenario: FW-TC-003 - Successful Withdrawal Leaving a Positive Balance
  Given user "test_funder_01" has a current Cash Balance of 1000.0000
  When the user attempts to withdraw 500.50
  Then the withdrawal should be successful
  And the new Cash Balance should be 499.5000
  And a transaction record should be logged detailing TYPE: WITHDRAWAL, AMOUNT: 500.50
```

| Requirement Traceability | FR-2.1 (Boundary), NFR-1.1 |
| :--- | :--- |
| **TC ID** | **FW-TC-004** |
| **Scenario** | **Boundary Case: Exact Withdrawal Leaving Zero Balance** |
| **Precondition** | User `test_funder_02` has an initial balance of $500.0000. |
| **Test Data** | Withdrawal Amount: 500.0000 |
| **Type** | Boundary |

```gherkin
Scenario: FW-TC-004 - Boundary Case: Exact Withdrawal Leaving Zero Balance
  Given user "test_funder_02" has a current Cash Balance of 500.0000
  When the user attempts to withdraw 500.0000
  Then the withdrawal should be successful
  And the new Cash Balance should be 0.0000
  And a transaction record should be logged detailing TYPE: WITHDRAWAL, AMOUNT: 500.0000
```

| Requirement Traceability | FR-2.2 |
| :--- | :--- |
| **TC ID** | **FW-TC-005** |
| **Scenario** | **Negative: Rejecting Withdrawal Due to Insufficient Funds (Overdraft)** |
| **Precondition** | User `test_funder_03` has a current balance of $10.00. |
| **Test Data** | Withdrawal Amount: 10.01 |
| **Type** | Negative (Error Scenario) |

```gherkin
Scenario: FW-TC-005 - Negative: Rejecting Withdrawal Due to Insufficient Funds (Overdraft)
  Given user "test_funder_03" has a current Cash Balance of 10.00
  When the user attempts to withdraw 10.01
  Then the transaction should be rejected
  And the error message should be "Insufficient funds"
  And the Cash Balance of "test_funder_03" must remain 10.00
```

| Requirement Traceability | FR-2.3 |
| :--- | :--- |
| **TC ID** | **FW-TC-006** |
| **Scenario Outline** | **Negative: Rejecting Invalid or Zero Withdrawal Amounts** |
| **Precondition** | User `test_funder_04` has a current balance of $500.00. |
| **Type** | Negative (Error Scenario, Data Driven) |

```gherkin
Scenario Outline: FW-TC-006 - Negative: Rejecting Invalid or Zero Withdrawal Amounts
  Given user "test_funder_04" has a current Cash Balance of 500.00
  When the user attempts to withdraw <Amount>
  Then the transaction should be rejected
  And the error message should be "Amount must be positive"
  And the Cash Balance of "test_funder_04" must remain 500.00

  Examples: Invalid Withdrawal Data
    | Amount | Description |
    | 0.00 | Zero amount |
    | -10.00 | Negative amount |
    | 0.0000 | High precision zero |
```

---

### Feature: Stock Trading - Buying Shares

This feature verifies successful share purchasing, strict adherence to affordability checks (preventing overdrafts via trade), and input validation (FR-3.1, FR-3.2, FR-3.3, FR-3.4).

| Requirement Traceability | FR-3.1, FR-3.4, NFR-1.1, D-1 |
| :--- | :--- |
| **TC ID** | **BUY-TC-007** |
| **Scenario** | **Successful Buy Order and Financial Calculation** |
| **Precondition** | User `test_buyer_01` has a Cash Balance of $5000.00. |
| **Test Data** | Symbol: GOOGL, Quantity: 5, Simulated Price: 150.2500 |
| **Type** | Positive (Happy Path) |

```gherkin
Scenario: BUY-TC-007 - Successful Buy Order and Financial Calculation
  Given user "test_buyer_01" has a Cash Balance of 5000.0000
  And the current simulated price for GOOGL is 150.2500
  When the user places a BUY order for 5 shares of GOOGL
  Then the BUY order should be executed successfully
  And the Cash Balance should be reduced by 751.2500 (Total Cost: 5 * 150.25)
  And the new Cash Balance should be 4248.7500
  And the holdings for GOOGL should increase by 5
  And a transaction record should be logged detailing TYPE: BUY, SYMBOL: GOOGL, COST: 751.2500
```

| Requirement Traceability | FR-3.2 (Boundary) |
| :--- | :--- |
| **TC ID** | **BUY-TC-008** |
| **Scenario** | **Boundary Case: Buying to Exact Zero Cash Balance** |
| **Precondition** | User `test_buyer_02` has a Cash Balance of $1000.00. |
| **Test Data** | Symbol: AMD, Quantity: 10, Simulated Price: 100.0000 |
| **Type** | Boundary |

```gherkin
Scenario: BUY-TC-008 - Boundary Case: Buying to Exact Zero Cash Balance
  Given user "test_buyer_02" has a current Cash Balance of 1000.00
  And the current simulated price for AMD is 100.0000
  When the user places a BUY order for 10 shares of AMD
  Then the BUY order should be executed successfully
  And the new Cash Balance should be 0.00
  And the holdings for AMD should be 10
```

| Requirement Traceability | FR-3.2 |
| :--- | :--- |
| **TC ID** | **BUY-TC-009** |
| **Scenario** | **Negative: Rejecting Purchase Due to Insufficient Funds** |
| **Precondition** | User `test_buyer_03` has a Cash Balance of $99.99. |
| **Test Data** | Symbol: XYZ, Quantity: 1, Simulated Price: 100.00 |
| **Type** | Negative (Error Scenario) |

```gherkin
Scenario: BUY-TC-009 - Negative: Rejecting Purchase Due to Insufficient Funds
  Given user "test_buyer_03" has a current Cash Balance of 99.99
  And the current simulated price for XYZ is 100.00
  When the user places a BUY order for 1 share of XYZ (Cost: 100.00)
  Then the BUY order should be rejected
  And the error message should be "Insufficient funds to cover trade cost"
  And the Cash Balance and Holdings for "test_buyer_03" must remain unchanged
```

| Requirement Traceability | FR-3.3 |
| :--- | :--- |
| **TC ID** | **BUY-TC-010** |
| **Scenario** | **Negative: Rejecting Purchase of Invalid Symbol** |
| **Precondition** | User `test_buyer_04` has a Cash Balance of $5000.00. |
| **Test Data** | Symbol: INVALID_SYM, Quantity: 5 |
| **Type** | Negative (Error Scenario) |

```gherkin
Scenario: BUY-TC-010 - Negative: Rejecting Purchase of Invalid Symbol
  Given user "test_buyer_04" has a current Cash Balance of 5000.00
  And the symbol "INVALID_SYM" is not supported by the system
  When the user attempts to place a BUY order for 5 shares of INVALID_SYM
  Then the transaction should be rejected
  And the error message should be "Invalid or unsupported share symbol"
  And the Cash Balance must remain 5000.00
```

---

### Feature: Stock Trading - Selling Shares

This feature ensures that users can sell shares only if they possess them and that the financial calculations for proceeds are correct (FR-4.1, FR-4.2, FR-4.3).

| Requirement Traceability | FR-4.1, FR-4.3 |
| :--- | :--- |
| **TC ID** | **SELL-TC-011** |
| **Scenario** | **Successful Sell Order and Financial Proceeds Calculation** |
| **Precondition** | User `test_seller_01` has 10 shares of MSFT and $1000.00 cash. |
| **Test Data** | Symbol: MSFT, Quantity: 7, Simulated Price: 300.5000 |
| **Type** | Positive (Happy Path) |

```gherkin
Scenario: SELL-TC-011 - Successful Sell Order and Financial Proceeds Calculation
  Given user "test_seller_01" has 10 shares of MSFT and a Cash Balance of 1000.0000
  And the current simulated price for MSFT is 300.5000
  When the user places a SELL order for 7 shares of MSFT
  Then the SELL order should be executed successfully
  And the Cash Balance should be credited by 2103.5000 (Total Proceeds: 7 * 300.50)
  And the new Cash Balance should be 3103.5000
  And the holdings for MSFT should decrease to 3
  And a transaction record should be logged detailing TYPE: SELL, SYMBOL: MSFT, PROCEEDS: 2103.5000
```

| Requirement Traceability | FR-4.2 |
| :--- | :--- |
| **TC ID** | **SELL-TC-012** |
| **Scenario Outline** | **Negative: Rejecting Sell Order Due to Insufficient Holdings** |
| **Precondition** | User `test_seller_02` has 5 shares of TSLA. |
| **Type** | Negative (Error Scenario, Boundary) |

```gherkin
Scenario Outline: SELL-TC-012 - Negative: Rejecting Sell Order Due to Insufficient Holdings
  Given user "test_seller_02" has 5 shares of TSLA
  And the current simulated price for TSLA is 200.00
  When the user attempts to place a SELL order for <Quantity> shares of TSLA
  Then the transaction should be rejected
  And the error message should be "Insufficient holdings for TSLA"
  And the holdings for TSLA must remain 5

  Examples: Insufficient Holdings Data
    | Quantity | Description |
    | 6 | Selling more than owned |
    | 5.0001 | Selling marginally more (High Precision Test) |
```

| Requirement Traceability | FR-4.2 |
| :--- | :--- |
| **TC ID** | **SELL-TC-013** |
| **Scenario** | **Negative: Rejecting Sell Order for Unheld Symbol** |
| **Precondition** | User `test_seller_03` has 10 shares of AMZN, but 0 shares of NFLX. |
| **Test Data** | Symbol: NFLX, Quantity: 1 |
| **Type** | Negative (Error Scenario) |

```gherkin
Scenario: SELL-TC-013 - Negative: Rejecting Sell Order for Unheld Symbol
  Given user "test_seller_03" has 0 shares of NFLX
  And the current simulated price for NFLX is 500.00
  When the user attempts to place a SELL order for 1 share of NFLX
  Then the transaction should be rejected
  And the error message should be "Insufficient holdings for NFLX"
  And the Cash Balance and holdings must remain unchanged
```

---

### Feature: Portfolio Reporting and P&L Calculation

This feature validates the accuracy of the total portfolio value (TPV) and Profit & Loss (P&L) calculations, which rely on aggregating cash, market values, and tracking historical deposits (FR-5.1, FR-5.2, FR-5.3).

| Requirement Traceability | FR-5.1, FR-5.2, FR-5.3, FR-5.4 |
| :--- | :--- |
| **TC ID** | **RPT-TC-014** |
| **Scenario** | **Positive P&L Calculation Verification (Profit)** |
| **Precondition** | User `test_reporter_01` has a complex history. |
| **Test Data** | Initial Deposit: $5,000.00. Current Cash: $100.00. Holdings: 10 XOM (Current Price $500.00). |
| **Type** | Positive (Calculation Validation) |

```gherkin
Scenario: RPT-TC-014 - Positive P&L Calculation Verification (Profit)
  Given user "test_reporter_01" has the following account state:
    | Metric | Value |
    | Total Deposits Baseline | 5000.00 |
    | Current Cash Balance | 100.00 |
  And the user holds the following shares:
    | Symbol | Quantity | Current Price | Market Value |
    | XOM | 10 | 500.00 | 5000.00 |
  When the user requests the Portfolio Report
  Then the calculated Portfolio Metrics should be:
    | Metric | Expected Value | Calculation Basis |
    | Total Market Value (TMV) | 5000.00 | (10 * 500.00) |
    | Total Portfolio Value (TPV) | 5100.00 | TMV + Cash |
    | Profit / Loss (P&L) | 100.00 | TPV - Deposits |
  And the Holdings Detail must display all required fields for XOM
```

| Requirement Traceability | FR-5.1, FR-5.2, FR-5.3 |
| :--- | :--- |
| **TC ID** | **RPT-TC-015** |
| **Scenario** | **Negative P&L Calculation Verification (Loss and Zero Holdings)** |
| **Precondition** | User `test_reporter_02` has withdrawn all funds and sold all assets at a loss. |
| **Test Data** | Total Deposits: $10,000.00. Current Cash: $0.00. Holdings: 0. |
| **Type** | Boundary/Calculation Validation |

```gherkin
Scenario: RPT-TC-015 - Negative P&L Calculation Verification (Loss and Zero Holdings)
  Given user "test_reporter_02" has the following account state:
    | Metric | Value |
    | Total Deposits Baseline | 10000.00 |
    | Current Cash Balance | 0.00 |
  And the user holds 0 shares of any symbol
  When the user requests the Portfolio Report
  Then the calculated Portfolio Metrics should be:
    | Metric | Expected Value | Calculation Basis |
    | Total Market Value (TMV) | 0.00 | N/A |
    | Total Portfolio Value (TPV) | 0.00 | TMV + Cash |
    | Profit / Loss (P&L) | -10000.00 | TPV - Deposits |
  And the Holdings Detail must show an empty list or zero holdings message
```