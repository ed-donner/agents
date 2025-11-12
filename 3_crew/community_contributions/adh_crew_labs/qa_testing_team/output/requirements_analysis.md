# Testable Requirements Analysis for Trading Simulation Platform

## 1. Functional Requirements (FR)

| Story ID | Requirement ID | Requirement Description | Acceptance Criteria (Testable Task) | Priority |
| :--- | :--- | :--- | :--- | :--- |
| **ACC-001** | FR-ACC-001.1 | The system must allow a new visitor to create an account using a unique email address. | GIVEN on registration page, WHEN unique valid credentials entered, THEN account created and user is logged in. | High |
| | FR-ACC-001.2 | The system must initialize the user's cash balance to $0.00 upon successful account creation. | VERIFY the initial `cash_balance` field for the new user record equals $0.00 (two decimal places). | High |
| | FR-ACC-001.3 | The system must validate that the provided password and confirmed password match. | VERIFY registration fails and error "Passwords do not match." is displayed if inputs differ. | High |
| | FR-ACC-001.4 | The system must validate the input format of the email address. | VERIFY registration fails and error "Please enter a valid email address." is displayed for invalid formats (e.g., missing @). | High |
| | FR-ACC-001.5 | The system must prevent the creation of accounts with an already registered email address. | VERIFY registration fails and error "This email address is already registered." is displayed if email exists. | High |
| **ACC-002** | FR-ACC-002.1 | The system must allow logged-in users to increase their cash balance via deposit. | GIVEN balance X, WHEN deposit Y, THEN new balance is X+Y. | High |
| | FR-ACC-002.2 | The system must record a "DEPOSIT" transaction for every successful fund deposit. | VERIFY a transaction record is created with Type="DEPOSIT" and Amount=Y, timestamped. | High |
| | FR-ACC-002.3 | The system must enforce that the deposit amount is greater than zero. | VERIFY transaction fails and error "Deposit amount must be greater than zero." for $0.00 input. | High |
| | FR-ACC-002.4 | The system must enforce that the deposit amount is a positive number. | VERIFY transaction fails and error "Deposit amount must be a positive number." for negative input. | High |
| | FR-ACC-002.5 | The deposit input field must only accept valid numeric (including decimal) values. | VERIFY transaction fails and error "Please enter a valid number." for non-numeric input (e.g., text). | High |
| **PTM-001** | FR-PTM-001.1 | The system must execute a "BUY" transaction if the user has sufficient available cash to cover the total cost (Quantity * Price). | VERIFY successful trade: Cash reduced, Portfolio updated, "BUY" transaction recorded (symbol, quantity, price). | High |
| | FR-PTM-001.2 | The system must calculate the trade cost using the real-time share price obtained immediately prior to execution. | VERIFY cost calculation uses the value returned by `get_share_price(symbol)` at the time of submission. | High |
| | FR-PTM-001.3 | The system must prevent transactions where the resulting cash balance would be negative. | GIVEN cost > cash, VERIFY trade blocked and error "Insufficient funds to complete this transaction." is displayed. | High |
| | FR-PTM-001.4 | The system must validate that the stock symbol is recognized by the pricing function. | VERIFY trade blocked and error "Stock symbol '[SYMBOL]' not found." if `get_share_price` returns an invalid result/error. | High |
| | FR-PTM-001.5 | The system must enforce that the quantity of shares bought is a positive number (Quantity > 0). | VERIFY trade blocked and error "Quantity must be a positive number." for quantity input of zero or negative. | High |
| | FR-PTM-001.6 | The system must detect and handle price fluctuation between order viewing and execution. | GIVEN order cost equals available cash, WHEN price increases before execution, THEN trade is blocked and message "The price has changed. Please try again." is displayed. | High |
| **PTM-003** | FR-PTM-003.1 | The system must retrieve and display the user's current holdings (Symbol, Quantity). | VERIFY all unique symbols owned by the user are listed. | High |
| | FR-PTM-003.2 | The system must calculate and display the current value of each holding. | VERIFY Holding Value = Quantity * `get_share_price(Symbol)`, displayed accurate to two decimals. | High |
| | FR-PTM-003.3 | The system must calculate and display the "Total Holdings Value" sum of all individual holding values. | VERIFY sum calculation is correct, even if individual price returns are $0.00 (e.g., for DELISTED stock). | High |
| | FR-PTM-003.4 | The system must calculate and display the "Total Portfolio Value." | VERIFY Total Portfolio Value = Total Holdings Value + Current Cash Balance. | High |
| | FR-PTM-003.5 | The system must display a distinct message if the user has zero stock holdings. | GIVEN 0 shares owned, VERIFY message "You do not own any shares." is displayed. | High |
| | FR-PTM-003.6 | The portfolio view must update holdings and total values when data is refreshed. | VERIFY Total Portfolio Value recalculates immediately after a manual or automated refresh based on new `get_share_price` data. | High |

## 2. Non-Functional Requirements (NFR)

| Story ID | NFR Category | Requirement Description | Measurement/Validation | Priority |
| :--- | :--- | :--- | :--- | :--- |
| **ACC-001** | Security | User passwords must be stored securely (hashed and salted) in the database. | Penetration testing and code review must confirm industry-standard encryption algorithms are used. | High |
| | Usability | Registration validation errors must be displayed clearly next to the corresponding input field. | UI review confirms error messages adhere to UI/UX specs regarding placement. | High |
| **ACC-002, PTM-001, PTM-003** | Data Integrity | All monetary calculations (cash balance, trade cost, portfolio value) must use a high-precision data type (e.g., Decimal/BigDecimal) to prevent floating-point errors. | Unit tests must confirm that calculations involving high decimal precision (e.g., $100.50 + $50.25 = $150.75) are exact. | High |
| **PTM-001, PTM-003** | Performance (Latency) | Trade execution (PTM-001) must complete within 500ms, including the price fetching call. | Load testing and monitoring of trade execution endpoints. | High |
| **PTM-003** | Performance (Scalability) | The portfolio view must efficiently handle fetching prices for a large number of distinct symbols (up to 100+ per user). | System design review must confirm optimization techniques (batching or caching) for external price API calls. | Medium |
| **PTM-003** | Data Freshness | Portfolio pricing data should be considered "current" if fetched within the last 5 minutes, or on manual refresh. | System monitoring confirms refresh mechanisms pull the latest price data on user request. | High |

## 3. Testable Scenarios (Consolidated)

| Scenario ID | Story ID | Action/Setup | Input Data | Expected Result | Validation Target |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **TS-ACC-001.1** | ACC-001 | Successful registration and initial state check. | Email: `new@test.com`, Pass: `Secure123`, Confirm: `Secure123` | Account created, initial balance $0.00, user is logged in. | FR-ACC-001.1, FR-ACC-001.2 |
| **TS-ACC-001.2** | ACC-001 | Attempt to register with existing email. | Email: `user@example.com` (pre-existing) | Error message: "This email address is already registered." Account count remains unchanged. | FR-ACC-001.5 |
| **TS-ACC-002.1** | ACC-002 | Happy Path Deposit with decimals. | Current Balance: $50.25, Deposit Amount: $100.50 | New Balance: $150.75. Transaction log updated with Type=DEPOSIT. | FR-ACC-002.1, FR-ACC-002.2 |
| **TS-ACC-002.2** | ACC-002 | Deposit of zero amount. | Current Balance: $1,000.00, Deposit Amount: $0.00 | Error message: "Deposit amount must be greater than zero." Balance remains $1,000.00. | FR-ACC-002.3 |
| **TS-PTM-001.1** | PTM-001 | Successful buy, adding to zero position. | Cash: $5,000, Symbol: AAPL, Quantity: 10, Price: $150.00 | New Cash: $3,500. Portfolio: 10 AAPL. Transaction recorded. | FR-PTM-001.1 |
| **TS-PTM-001.2** | PTM-001 | Buy fails due to insufficient funds check. | Cash: $299, Symbol: AAPL, Quantity: 2, Price: $150.00 (Cost $300) | Error: "Insufficient funds..." Cash remains $299. | FR-PTM-001.3 |
| **TS-PTM-001.3** | PTM-001 | Buy fails due to non-positive quantity. | Cash: $5,000, Symbol: GOOGL, Quantity: 0 | Error: "Quantity must be a positive number." | FR-PTM-001.5 |
| **TS-PTM-001.4** | PTM-001 | Buy fails due to symbol not found. | Cash: $5,000, Symbol: FAKE, Quantity: 5 | Error: "Stock symbol 'FAKE' not found." | FR-PTM-001.4 |
| **TS-PTM-001.5** | PTM-001 | Edge Case: Price slippage check. | Cash: $151.00. Initial Price: $150.00. Execution Price: $152.00. Quantity: 1. | Trade blocked. Error: "The price has changed. Please try again." | FR-PTM-001.6 |
| **TS-PTM-003.1** | PTM-003 | View portfolio with multiple holdings. | Holdings: 10 AAPL, 5 TSLA. Cash: $1,000. Prices: AAPL $150, TSLA $200. | Total Holdings Value: $2,500. Total Portfolio Value: $3,500. | FR-PTM-003.2, FR-PTM-003.4 |
| **TS-PTM-003.2** | PTM-003 | View portfolio with zero holdings. | Holdings: 0. Cash: $5,000. | Message: "You do not own any shares." Total Portfolio Value: $5,000. | FR-PTM-003.5 |
| **TS-PTM-003.3** | PTM-003 | View portfolio with delisted stock (zero price). | Holdings: 100 DELISTED. Cash: $100. Price: $0.00. | DELISTED Current Value: $0.00. Total Portfolio Value: $100.00. | FR-PTM-003.3 |

## 4. Dependencies and Constraints

| Story ID | Type | Description | Mitigation/Context |
| :--- | :--- | :--- | :--- |
| **ACC-001** | Dependency | Database Schema: Requires the existence of a `Users` table with fields for Email (unique index), Encrypted Password, and Cash Balance (defaulting to $0.00). | Must be implemented before full account creation functionality. |
| **ACC-002** | Dependency | Requires **ACC-001** (User Account) and the **Transaction History Model** (used by PTM-005). | Transaction model structure must support Type, Symbol, Quantity, Price, and Amount. |
| **PTM-001, PTM-003** | Constraint (Technical) | All currency calculations must utilize a high-precision data type (e.g., Decimal) to maintain accuracy. | Mandated across backend data persistence and business logic layers. |
| **PTM-001, PTM-003** | Dependency (External) | **`get_share_price(symbol)` function:** A stable external or mocked service is required to provide real-time pricing data. | Development must stabilize the interface (API/function call) for this service first. |
| **PTM-001** | Constraint (Timing) | The check for sufficient funds and price fluctuation must be atomic to prevent edge-case failures where a user's balance changes between checking the price and submitting the order. | Use database transactions or locking mechanisms to ensure atomicity for trade execution. |
| **PTM-003** | Dependency | Requires data from **PTM-001** (Trade execution) to populate holdings data accurately. | Portfolio aggregation queries must be stable prior to view implementation. |

## 5. Priority Levels

| Epic | Story ID | Title | Priority | Rationale |
| :--- | :--- | :--- | :--- | :--- |
| EPIC-01 | ACC-001 | User Account Creation | High | Platform foundation and user entry point. |
| EPIC-01 | ACC-002 | Deposit Funds into Account | High | Essential setup for core trading functionality. |
| EPIC-02 | PTM-001 | Buy Shares of a Stock | High | Core value proposition/primary user activity. |
| EPIC-02 | PTM-003 | View Portfolio Holdings and Value | High | Critical visibility and feedback loop for traders. |
| EPIC-01 | ACC-003 | Withdraw Funds (Omitted Details) | Medium | Secondary cash management feature. |
| EPIC-02 | PTM-002 | Sell Shares of a Stock (Omitted Details) | High | Essential part of the core trading loop. |
| EPIC-02 | PTM-004 | View P&L (Omitted Details) | Medium | Performance tracking metric (important, but not transactional). |
| EPIC-02 | PTM-005 | View Transaction History (Omitted Details) | Medium | Audit and transparency feature. |