```markdown
# Trading Simulation Platform Test Cases

## Feature: Account Registration and Initialization

**Goal:** Verify that new users can register successfully with valid credentials and that their initial cash balance is correctly set to $0.00.

| Test ID | Requirement Traceability |
| :--- | :--- |
| ACC-REG-POS-001 | FR-ACC-1.1, FR-ACC-1.2 |
| ACC-REG-NEG-002 | FR-ACC-1.3 |
| ACC-REG-NEG-003 | FR-ACC-1.4 |

### Scenario: Successful Account Creation and Zero Balance Initialization
**Test ID:** ACC-REG-POS-001
**Precondition:** The user is on the Account Creation section. No existing account uses `newuser@test.com`.
**Expected Result:** Account creation is successful, and the initial Cash Balance displayed is "$0.00".

```gherkin
Scenario: Successful Account Creation and Zero Balance Initialization
  Given the user is on the Registration interface
  When the user enters registration details
    | Element ID | Label | Value |
    | component-6 | Email | newuser@test.com |
    | component-7 | Password | SecureP@ss1 |
    | component-8 | Confirm Password | SecureP@ss1 |
  And the user clicks the "Create Account" button (component-9)
  Then the system displays the success message in component-28
  And the "Cash Balance" (component-29) is displayed as "$0.00"
```

### Scenario Outline: Negative Registration Scenarios
**Test ID:** ACC-REG-NEG-002, ACC-REG-NEG-003
**Precondition:** `existing@test.com` is already registered in the system.
**Expected Result:** Account creation fails, and the specific error message is displayed in the message component (component-28).

```gherkin
Scenario Outline: Attempt Registration with Invalid Data (Existing Email or Mismatched Passwords)
  Given the user is on the Registration interface
    | Precondition | Email |
    | Existing Account | existing@test.com |
  When the user attempts to register with invalid credentials
    | Email | Password | Confirm Password |
    | <Email Attempt> | <Password> | <Confirm Password> |
  And the user clicks the "Create Account" button (component-9)
  Then the system displays the error message "<Expected Error Message>" in component-28

  Examples: Invalid Registration Attempts
    | Test ID | Email Attempt | Password | Confirm Password | Expected Error Message | FR Mapping |
    | ACC-REG-NEG-002 | existing@test.com | PwD12345 | PwD12345 | This email address is already registered. | FR-ACC-1.3 |
    | ACC-REG-NEG-003 | new_bad@test.com | PwD12345 | PwD_MISMATCH | Passwords do not match. | FR-ACC-1.4 |
```

## Feature: Fund Management (Deposit and Withdrawal)

**Goal:** Ensure fund management processes (deposit and withdrawal) correctly update the cash balance and handle edge cases like zero, negative, and overdraw attempts.

| Test ID | Requirement Traceability |
| :--- | :--- |
| ACC-FUND-POS-010 | FR-ACC-2.1, FR-ACC-2.2 |
| ACC-FUND-NEG-011 | FR-ACC-2.3 |
| ACC-FUND-POS-012 | FR-ACC-3.1 |
| ACC-FUND-NEG-013 | FR-ACC-3.2 |

### Scenario: Successful Deposit and Transaction Recording
**Test ID:** ACC-FUND-POS-010
**Precondition:** User is logged in with an initial Cash Balance of $50.25.
**Expected Result:** Balance increases correctly, and a 'DEPOSIT' record is created in the history log.

```gherkin
Scenario: Successful Deposit and Transaction Recording
  Given the user is logged in with a cash balance of $50.25
  When the user enters "100.50" into the "Deposit Amount" field (component-11)
  And the user clicks the "Deposit" button (component-12)
  Then the "Cash Balance" (component-29) updates to "$150.75"
  And the transaction history (component-34) contains a record with:
    | Type | Amount |
    | DEPOSIT | 100.50 |
```

### Scenario Outline: Negative Deposit and Withdrawal Scenarios
**Test ID:** ACC-FUND-NEG-011, ACC-FUND-NEG-013
**Precondition:** User is logged in with a Cash Balance of $500.00.
**Expected Result:** Balance remains unchanged, and the specific error message is displayed.

```gherkin
Scenario Outline: Rejecting Invalid Fund Operations (Zero/Negative Deposit, Overdraw)
  Given the user is logged in with a cash balance of <Initial Balance>
  When the user attempts to perform a <Operation Type> with amount <Input Amount>
    | Element ID | Action Button |
    | <Input Element ID> | <Button Element ID> |
  Then the "Cash Balance" (component-29) remains at $<Initial Balance>
  And the system displays the error message "<Expected Error Message>" in component-28
  And no new transaction record is found in the history (component-34)

  Examples: Fund Operation Failures
    | Test ID | Operation Type | Initial Balance | Input Amount | Input Element ID | Button Element ID | Expected Error Message | FR Mapping |
    | ACC-FUND-NEG-011 | Deposit | 500.00 | 0.00 | component-11 | component-12 | Deposit amount must be greater than zero. | FR-ACC-2.3 |
    | ACC-FUND-NEG-011 | Deposit | 500.00 | -10.00 | component-11 | component-12 | Deposit amount must be greater than zero. | FR-ACC-2.3 |
    | ACC-FUND-NEG-013 | Withdrawal | 500.00 | 500.01 | component-13 | component-14 | Withdrawal amount exceeds current cash balance. | FR-ACC-3.2 |
    | ACC-FUND-NEG-013 | Withdrawal | 0.00 | 1.00 | component-13 | component-14 | Withdrawal amount exceeds current cash balance. | FR-ACC-3.2 |
```

## Feature: Trading Operations (Buying Shares)

**Goal:** Test successful share purchases and validation checks, including insufficient funds, invalid symbols, and edge cases related to quantity and price fluctuations.

**Assumed Price:** AAPL = $150.00

| Test ID | Requirement Traceability |
| :--- | :--- |
| PTM-BUY-POS-020 | FR-PTM-1.1, 1.2, 1.3 |
| PTM-BUY-NEG-021 | FR-PTM-1.4 |
| PTM-BUY-NEG-022 | FR-PTM-1.5 |
| PTM-BUY-NEG-023 | FR-PTM-1.6 |
| PTM-BUY-EDGE-024 | FR-PTM-1.7 |

### Scenario: Successful Stock Purchase and Portfolio Update
**Test ID:** PTM-BUY-POS-020
**Precondition:** User is logged in with Cash Balance of $5,000.00. AAPL price is $150.00.
**Expected Result:** Cash balance is reduced by $1,500.00. Portfolio shows 10 shares of AAPL. A 'BUY' transaction is logged.

```gherkin
Scenario: Successful Stock Purchase
  Given the user is logged in with a cash balance of $5000.00
  And the current real-time price for AAPL is $150.00
  When the user enters "AAPL" into the "Stock Symbol" field (component-17)
  And the user enters "10" into the "Quantity" field (component-18)
  And the user clicks the "Buy Shares" button (component-21)
  Then the "Cash Balance" (component-29) updates to "$3500.00"
  And the "Holdings" (component-30) shows 10 shares of AAPL
  And the transaction history (component-34) contains a record with:
    | Type | Symbol | Quantity | Price |
    | BUY | AAPL | 10 | 150.00 |
```

### Scenario Outline: Negative Buy Scenarios (Insufficient Funds, Invalid Symbol/Quantity)
**Test ID:** PTM-BUY-NEG-021, PTM-BUY-NEG-022, PTM-BUY-NEG-023
**Precondition:** User is logged in with a Cash Balance of $500.00. AAPL price is $150.00.
**Expected Result:** Cash balance remains unchanged, and the specific error message is displayed.

```gherkin
Scenario Outline: Blocking Trades Due to Invalid Conditions
  Given the user is logged in with a cash balance of $500.00
  When the user attempts to buy <Quantity> shares of <Symbol>
    | Stock Symbol Element ID | Quantity Element ID |
    | component-17 | component-18 |
  And the user clicks the "Buy Shares" button (component-21)
  Then the "Cash Balance" (component-29) remains at "$500.00"
  And the system displays the error message "<Expected Error Message>" in component-28
  And the "Holdings" (component-30) remains unchanged

  Examples: Buy Transaction Failures
    | Test ID | Symbol | Quantity | Total Cost (Approx) | Expected Error Message | FR Mapping |
    | PTM-BUY-NEG-021 | AAPL | 4 | $600.00 | Insufficient funds to cover the transaction cost of $600.00. | FR-PTM-1.4 |
    | PTM-BUY-NEG-022 | FAKE | 1 | N/A | Stock symbol 'FAKE' not found. | FR-PTM-1.5 |
    | PTM-BUY-NEG-023 | TSLA | 0 | $0.00 | Quantity must be a positive number. | FR-PTM-1.6 |
    | PTM-BUY-NEG-023 | GOOGL | -5 | N/A | Quantity must be a positive number. | FR-PTM-1.6 |
```

### Scenario: Edge Case - Price Fluctuation Rejection
**Test ID:** PTM-BUY-EDGE-024
**Precondition:** User has just enough cash for the displayed price, but the price increases during execution.
**Expected Result:** Transaction fails, and the user is informed about the price change.

```gherkin
Scenario: Price Fluctuation Causes Insufficient Funds Error
  Given the user is logged in with a cash balance of $151.00
  And the displayed real-time price for AAPL is $150.00
  When the user enters "AAPL" and "1" share to buy
  And the underlying system simulates a price increase of AAPL to $152.00 upon execution
  And the user clicks the "Buy Shares" button (component-21)
  Then the "Cash Balance" (component-29) remains at "$151.00"
  And the system displays the error message "The price has changed, and you now have insufficient funds. Please review the new price." in component-28
```

## Feature: Trading Operations (Selling Shares)

**Goal:** Test successful share sales and ensure the system prevents selling more shares than owned.

**Assumed Price:** TSLA = $200.00

| Test ID | Requirement Traceability |
| :--- | :--- |
| PTM-SELL-POS-030 | FR-PTM-2.1, FR-PTM-2.3 |
| PTM-SELL-NEG-031 | FR-PTM-2.2 |

### Scenario: Successful Stock Sale and Portfolio Update
**Test ID:** PTM-SELL-POS-030
**Precondition:** User owns 10 shares of TSLA. Cash Balance is $1,000.00. TSLA price is $200.00.
**Expected Result:** Cash balance increases by $1,000.00. Portfolio shows 5 shares of TSLA remaining. A 'SELL' transaction is logged.

```gherkin
Scenario: Successful Stock Sale
  Given the user is logged in with a cash balance of $1000.00
  And the user owns 10 shares of TSLA
  And the current real-time price for TSLA is $200.00
  When the user enters "TSLA" into the "Stock Symbol" field (component-17)
  And the user enters "5" into the "Quantity" field (component-18)
  And the user clicks the "Sell Shares" button (component-22)
  Then the "Cash Balance" (component-29) updates to "$2000.00"
  And the "Holdings" (component-30) shows 5 shares of TSLA
  And the transaction history (component-34) contains a record with:
    | Type | Symbol | Quantity | Price |
    | SELL | TSLA | 5 | 200.00 |
```

### Scenario: Negative Sale Scenario (Selling More Than Owned)
**Test ID:** PTM-SELL-NEG-031
**Precondition:** User owns 10 shares of TSLA. Cash Balance is $1,000.00. TSLA price is $200.00.
**Expected Result:** Cash balance and holdings remain unchanged. Error message is displayed.

```gherkin
Scenario: Attempt to Sell More Shares Than Owned
  Given the user is logged in with a cash balance of $1000.00
  And the user owns 10 shares of AAPL
  When the user enters "AAPL" into the "Stock Symbol" field (component-17)
  And the user enters "11" into the "Quantity" field (component-18)
  And the user clicks the "Sell Shares" button (component-22)
  Then the "Cash Balance" (component-29) remains at "$1000.00"
  And the "Holdings" (component-30) still shows 10 shares of AAPL
  And the system displays the error message "You cannot sell 11 shares of AAPL, you only own 10." in component-28
```

## Feature: Portfolio Summary and Transaction History View

**Goal:** Verify accurate calculation and display of portfolio summaries and comprehensive transaction history logging.

| Test ID | Requirement Traceability |
| :--- | :--- |
| PTM-VIEW-POS-040 | FR-PTM-3.1, FR-PTM-3.2, FR-PTM-3.4 |
| PTM-VIEW-POS-041 | FR-PTM-3.3 |
| PTM-HIST-POS-042 | FR-PTM-5.1 |

### Scenario: Portfolio Summary Calculation Verification
**Test ID:** PTM-VIEW-POS-040
**Precondition:** User is logged in. Cash Balance: $1,000.00. Holdings: 10 AAPL ($150.00 price), 5 TSLA ($200.00 price).
**Expected Result:** All summary components display calculated values correctly.

```gherkin
Scenario: Accurate Portfolio Summary Calculation
  Given the user is logged in with the following holdings and cash
    | Symbol | Quantity | Price |
    | AAPL | 10 | 150.00 |
    | TSLA | 5 | 200.00 |
    | Cash | N/A | 1000.00 |
  And the total calculated Holdings Value is $2500.00 (10*150 + 5*200)
  When the user views the "Account Status" section
  Then the "Cash Balance" (component-29) displays "$1000.00"
  And the "Holdings" (component-30) table displays:
    | Symbol | Quantity | Price | Value |
    | AAPL | 10 | $150.00 | $1500.00 |
    | TSLA | 5 | $200.00 | $1000.00 |
  And the "Portfolio Summary" (component-31) displays "Total Holdings Value: $2500.00"
  And the "Portfolio Summary" (component-31) displays "Total Portfolio Value: $3500.00"
```

### Scenario: Portfolio Summary with Zero Holdings (Edge Case)
**Test ID:** PTM-VIEW-POS-041
**Precondition:** User is logged in. Cash Balance: $5,000.00. Holdings: 0 shares.
**Expected Result:** Specific message for zero holdings is shown, and Total Portfolio Value equals Cash Balance.

```gherkin
Scenario: Displaying Portfolio Summary When No Shares Are Held
  Given the user is logged in with a cash balance of $5000.00
  And the user has no stock holdings
  When the user views the "Account Status" section
  Then the "Cash Balance" (component-29) displays "$5000.00"
  And the "Holdings" (component-30) displays the message "You do not own any shares."
  And the "Portfolio Summary" (component-31) displays "Total Holdings Value: $0.00"
  And the "Portfolio Summary" (component-31) displays "Total Portfolio Value: $5000.00"
```

### Scenario: Verification of Comprehensive Transaction History
**Test ID:** PTM-HIST-POS-042
**Precondition:** User has performed a sequence of transactions: Deposit, Buy, Sell, Withdrawal.
**Expected Result:** The transaction history displays all four types of transactions chronologically and correctly formatted.

```gherkin
Scenario: Verify Complete Transaction History Log
  Given the user has previously executed the following chronological transactions:
    | Transaction Time | Type | Amount/Quantity | Symbol | Price |
    | T1 | DEPOSIT | 500.00 | N/A | N/A |
    | T2 | BUY | 1 | GOOGL | 100.00 |
    | T3 | SELL | 1 | GOOGL | 105.00 |
    | T4 | WITHDRAWAL | 50.00 | N/A | N/A |
  When the user clicks the "Refresh Transactions" button (component-33)
  Then the "Recent Transactions" table (component-34) shows 4 entries in chronological order (T1 to T4)
  And the table confirms the details for each transaction type:
    | Entry Index | Type | Quantity/Amount | Symbol | Price |
    | 1 (Oldest) | DEPOSIT | 500.00 | N/A | N/A |
    | 2 | BUY | 1 | GOOGL | 100.00 |
    | 3 | SELL | 1 | GOOGL | 105.00 |
    | 4 (Newest) | WITHDRAWAL | 50.00 | N/A | N/A |
  And all necessary data points (Symbol, Quantity, Price, Type) are present for BUY/SELL transactions (FR-PTM-5.1)
```