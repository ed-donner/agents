```markdown
# Trading Simulation Platform Test Scenarios

## Feature: User Account Creation (ACC-001)

**Goal:** Ensure new users can successfully register with valid, unique credentials and that their initial account state is correctly initialized.

| Requirement Traceability | FR-ACC-001.1, FR-ACC-001.2, FR-ACC-001.3, FR-ACC-001.4, FR-ACC-001.5, NFR (Usability) |

---

### Scenario: Successful Account Registration and Initial State Check (Happy Path)
**Test ID:** ACC-REG-POS-001
**Traceability:** FR-ACC-001.1, FR-ACC-001.2 (TS-ACC-001.1)

**Preconditions:**
1. User is on the "Account Creation" section of the platform.
2. The provided email address (`valid_new_user@test.com`) is not already registered.

**Steps:**
1. GIVEN the user inputs a unique Email into the Email Input (`component-6`).
2. AND the user inputs a secure Password into the Password Input (`component-7`).
3. AND the user confirms the same Password into the Confirm Password Input (`component-8`).
4. WHEN the user clicks the "Create Account" Button (`component-9`).
5. THEN the Messages Display (`component-28`) shows a success message (e.g., "Account created successfully. User logged in.").
6. AND the Cash Balance Display (`component-29`) shows the initial balance as "$0.00".

---

### Scenario Outline: Negative Account Creation Scenarios (Validation)
**Test ID:** ACC-REG-NEG-002
**Traceability:** FR-ACC-001.3, FR-ACC-001.4, FR-ACC-001.5 (TS-ACC-001.2)

**Preconditions:**
1. A user account with email `existing@test.com` already exists in the database.
2. User is on the "Account Creation" section.

| Test Case | Email Input | Password Input | Confirm Password Input | Expected Error Message | Requirement |
| :--- | :--- | :--- | :--- | :--- | :--- |
| ACC-002a | `existing@test.com` | `Pass123` | `Pass123` | "This email address is already registered." | FR-ACC-001.5 |
| ACC-002b | `new@test.com` | `Secret1` | `Different1` | "Passwords do not match." | FR-ACC-001.3 |
| ACC-002c | `invalid-email` | `Pass123` | `Pass123` | "Please enter a valid email address." | FR-ACC-001.4 |
| ACC-002d | `missing.com` | `Pass123` | `Pass123` | "Please enter a valid email address." | FR-ACC-001.4 |

**Steps:**
1. GIVEN the user inputs `<Email Input>` into the Email Input (`component-6`).
2. AND the user inputs `<Password Input>` into the Password Input (`component-7`).
3. AND the user inputs `<Confirm Password Input>` into the Confirm Password Input (`component-8`).
4. WHEN the user clicks the "Create Account" Button (`component-9`).
5. THEN the Messages Display (`component-28`) shows the error message: `<Expected Error Message>`.
6. AND the user remains logged out (if applicable, or account details unchanged).

---
## Feature: Fund Deposit Management (ACC-002)

**Goal:** Verify that users can deposit funds successfully, calculations are accurate, and input validation is strict.

| Requirement Traceability | FR-ACC-002.1, FR-ACC-002.2, FR-ACC-002.3, FR-ACC-002.4, FR-ACC-002.5, NFR (Data Integrity) |

---

### Scenario: Successful Fund Deposit with Decimal Precision
**Test ID:** ACC-DEP-POS-001
**Traceability:** FR-ACC-002.1, FR-ACC-002.2 (TS-ACC-002.1)

**Preconditions:**
1. User is logged in.
2. The Cash Balance Display (`component-29`) shows an initial balance of "$50.25".

**Steps:**
1. GIVEN the current cash balance is $50.25.
2. WHEN the user enters "100.50" into the Deposit Amount Input (`component-11`).
3. AND the user clicks the "Deposit" Button (`component-12`).
4. THEN the Messages Display (`component-28`) shows a success message (e.g., "Deposit of $100.50 successful.").
5. AND the Cash Balance Display (`component-29`) updates to show "$150.75".
6. AND the Recent Transactions Display (`component-34`) includes a new entry with Type="DEPOSIT" and Amount="100.50".

---

### Scenario Outline: Negative Deposit Validation (Boundary and Invalid Inputs)
**Test ID:** ACC-DEP-NEG-002
**Traceability:** FR-ACC-002.3, FR-ACC-002.4, FR-ACC-002.5 (TS-ACC-002.2)

**Preconditions:**
1. User is logged in.
2. Initial Cash Balance is $1,000.00.

| Test Case | Deposit Amount Input | Expected Error Message | Expected Final Balance | Requirement |
| :--- | :--- | :--- | :--- | :--- | :--- |
| ACC-002a | `0.00` | "Deposit amount must be greater than zero." | $1,000.00 | FR-ACC-002.3 |
| ACC-002b | `-10.00` | "Deposit amount must be a positive number." | $1,000.00 | FR-ACC-002.4 |
| ACC-002c | `Text` | "Please enter a valid number." | $1,000.00 | FR-ACC-002.5 |
| ACC-002d | `` (Empty) | "Deposit amount must be greater than zero." | $1,000.00 | FR-ACC-002.3 |

**Steps:**
1. GIVEN the current cash balance is $1,000.00.
2. WHEN the user enters `<Deposit Amount Input>` into the Deposit Amount Input (`component-11`).
3. AND the user clicks the "Deposit" Button (`component-12`).
4. THEN the Messages Display (`component-28`) shows the error message: `<Expected Error Message>`.
5. AND the Cash Balance Display (`component-29`) remains unchanged at `<Expected Final Balance>`.

---
## Feature: Stock Trading - Buying Shares (PTM-001)

**Goal:** Ensure the buy transaction executes correctly, calculating cost based on real-time price and enforcing critical safety checks (funds, symbol validity, positive quantity, price slippage).

| Requirement Traceability | FR-PTM-001.1, FR-PTM-001.2, FR-PTM-001.3, FR-PTM-001.4, FR-PTM-001.5, FR-PTM-001.6 |

---

### Scenario: Successful Stock Purchase (PTM-001.1)
**Test ID:** PTM-BUY-POS-001
**Traceability:** FR-PTM-001.1, FR-PTM-001.2 (TS-PTM-001.1)

**Preconditions:**
1. User is logged in with Cash Balance of $5,000.00.
2. Stock price for AAPL is $150.00 at the time of execution.
3. User currently holds 0 shares of AAPL.

**Steps:**
1. GIVEN the current cash balance is $5,000.00.
2. WHEN the user enters "AAPL" into the Stock Symbol Input (`component-17`).
3. AND the user enters "10" into the Quantity Input (`component-18`).
4. AND the calculated trade cost is $1,500.00 (10 shares * $150.00 price).
5. AND the user clicks the "Buy Shares" Button (`component-21`).
6. THEN the Messages Display (`component-28`) shows a success message (e.g., "Bought 10 shares of AAPL for $1,500.00").
7. AND the Cash Balance Display (`component-29`) updates to show "$3,500.00".
8. AND the Holdings Display (`component-30`) shows the new position: "AAPL: 10 shares".

---

### Scenario Outline: Negative Trade Scenarios (Insufficient Funds, Invalid Input)
**Test ID:** PTM-BUY-NEG-002
**Traceability:** FR-PTM-001.3, FR-PTM-001.4, FR-PTM-001.5 (TS-PTM-001.2, TS-PTM-001.3, TS-PTM-001.4)

**Preconditions:**
1. User is logged in.
2. Cash Balance is $299.00.
3. Stock price for AAPL is $150.00.

| Test Case | Symbol Input | Quantity Input | Trade Cost | Expected Error Message | Requirement |
| :--- | :--- | :--- | :--- | :--- | :--- |
| PTM-002a | `AAPL` | `2` | $300.00 | "Insufficient funds to complete this transaction." | FR-PTM-001.3 |
| PTM-002b | `GOOGL` | `0` | $0.00 | "Quantity must be a positive number." | FR-PTM-001.5 |
| PTM-002c | `FAKE` | `5` | N/A | "Stock symbol 'FAKE' not found." | FR-PTM-001.4 |
| PTM-002d | `TSLA` | `-1` | N/A | "Quantity must be a positive number." | FR-PTM-001.5 |

**Steps:**
1. GIVEN the current cash balance is $299.00.
2. WHEN the user attempts to buy `<Quantity Input>` of `<Symbol Input>`.
3. AND the user clicks the "Buy Shares" Button (`component-21`).
4. THEN the Messages Display (`component-28`) shows the error message: `<Expected Error Message>`.
5. AND the Cash Balance Display (`component-29`) remains unchanged at "$299.00".
6. AND the Holdings Display (`component-30`) remains unchanged.

---

### Scenario: Edge Case - Handling Price Slippage During Execution
**Test ID:** PTM-BUY-NEG-003
**Traceability:** FR-PTM-001.6 (TS-PTM-001.5)

**Preconditions:**
1. User is logged in.
2. Cash Balance is exactly $151.00.
3. Price displayed to the user when they calculate the cost is $150.00.
4. The real-time price fetched *at the moment of execution* has increased to $152.00.

**Steps:**
1. GIVEN the user is prepared to buy 1 share of TSLA when the perceived price is $150.00.
2. AND the user has insufficient funds for the execution price ($152.00).
3. WHEN the user clicks the "Buy Shares" Button (`component-21`).
4. THEN the transaction is blocked due to the cost change.
5. AND the Messages Display (`component-28`) shows the error message: "The price has changed. Please try again."
6. AND the Cash Balance Display (`component-29`) remains "$151.00".

---
## Feature: Portfolio Status and Value Calculation (PTM-003)

**Goal:** Validate that the system accurately retrieves, calculates, and displays all aspects of the user's portfolio value, including handling edge cases like zero holdings or delisted stocks.

| Requirement Traceability | FR-PTM-003.1, FR-PTM-003.2, FR-PTM-003.3, FR-PTM-003.4, FR-PTM-003.5, FR-PTM-003.6, NFR (Data Integrity) |

---

### Scenario: Portfolio Calculation with Multiple Holdings and Cash
**Test ID:** PTM-PORT-POS-001
**Traceability:** FR-PTM-003.1, FR-PTM-003.2, FR-PTM-003.3, FR-PTM-003.4 (TS-PTM-003.1)

**Preconditions:**
1. User is logged in with Cash Balance of $1,000.00.
2. User holdings are 10 shares of AAPL and 5 shares of TSLA.
3. Current stock prices are simulated: AAPL = $150.00, TSLA = $200.00.

**Steps:**
1. GIVEN the user navigates to the Portfolio View.
2. WHEN the system performs the necessary calculations.
3. THEN the Holdings Display (`component-30`) accurately lists the holdings and their current value:
    | Symbol | Quantity | Current Price | Value |
    | :--- | :--- | :--- | :--- |
    | AAPL | 10 | $150.00 | $1,500.00 |
    | TSLA | 5 | $200.00 | $1,000.00 |
4. AND the Portfolio Summary Display (`component-31`) shows:
    | Metric | Value |
    | :--- | :--- |
    | Cash Balance | $1,000.00 |
    | Total Holdings Value | $2,500.00 |
    | Total Portfolio Value | $3,500.00 |

---

### Scenario: Portfolio Display when Zero Holdings Exist
**Test ID:** PTM-PORT-POS-002
**Traceability:** FR-PTM-003.5 (TS-PTM-003.2)

**Preconditions:**
1. User is logged in with Cash Balance of $5,000.00.
2. User holdings are zero.

**Steps:**
1. GIVEN the user has no current stock holdings.
2. WHEN the Portfolio View loads.
3. THEN the Holdings Display (`component-30`) shows the distinct message: "You do not own any shares."
4. AND the Portfolio Summary Display (`component-31`) correctly calculates:
    | Metric | Value |
    | :--- | :--- |
    | Cash Balance | $5,000.00 |
    | Total Holdings Value | $0.00 |
    | Total Portfolio Value | $5,000.00 |

---

### Scenario: Portfolio Recalculation after Price Change (Refresh)
**Test ID:** PTM-PORT-POS-003
**Traceability:** FR-PTM-003.6

**Preconditions:**
1. User holds 10 shares of AAPL.
2. Initial Price: AAPL = $150.00. Initial Cash Balance: $1,000.00.
3. Initial Total Portfolio Value: $2,500.00.

**Steps:**
1. GIVEN the Portfolio Summary Display (`component-31`) shows a Total Portfolio Value of $2,500.00.
2. AND the underlying price of AAPL changes from $150.00 to $160.00 (external system change).
3. WHEN the user clicks the "Refresh Transactions" Button (`component-33`) (or a dedicated Refresh Portfolio button, assuming this button triggers the data refresh).
4. THEN the Holdings Display (`component-30`) updates the current value of AAPL to $1,600.00 (10 * $160.00).
5. AND the Portfolio Summary Display (`component-31`) updates the Total Portfolio Value to "$2,600.00".

---

### Scenario: Edge Case - Handling Delisted Stock Price ($0.00)
**Test ID:** PTM-PORT-EDGE-004
**Traceability:** FR-PTM-003.3 (TS-PTM-003.3)

**Preconditions:**
1. User is logged in with Cash Balance of $100.00.
2. User holdings include 100 shares of a stock (DELISTED).
3. The pricing function `get_share_price("DELISTED")` returns $0.00.

**Steps:**
1. GIVEN the user views the portfolio containing 100 shares of DELISTED stock.
2. WHEN the system calculates the value of DELISTED using the $0.00 price.
3. THEN the Holdings Display (`component-30`) shows "DELISTED" with a Current Value of "$0.00".
4. AND the Portfolio Summary Display (`component-31`) correctly calculates:
    | Metric | Value |
    | :--- | :--- |
    | Cash Balance | $100.00 |
    | Total Holdings Value | $0.00 |
    | Total Portfolio Value | $100.00 |
```