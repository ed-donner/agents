```markdown
# output/user_stories.md

## Story 1: Account Creation and Initialization

| Field | Detail |
| :--- | :--- |
| **ID** | ACCT-001 |
| **Title** | Account Creation and Initial Cash Balance Setup |
| **Business Value** | Enables new users to access the platform and begin simulating trades. |
| **Priority** | P1 - Must Have |

**User Story Statement**
As a potential trading simulation user,
I want to be able to create an account,
So that I can receive a unique identifier and start managing my simulated funds and portfolio.

**Acceptance Criteria**

| ID | Type | Given | When | Then |
| :--- | :--- | :--- | :--- | :--- |
| AC-1.1 | Happy Path | The user provides required registration details (e.g., username). | The system processes the request. | A new account is created, and the initial cash balance is set to $0.00. |
| AC-1.2 | Happy Path | A new account has been successfully created. | I check the transaction history. | The history is empty (no transactions recorded yet). |
| AC-1.3 | Happy Path | A new account has been successfully created. | I request the portfolio holdings report. | The report shows $0.00 cash balance and zero shares held. |
| AC-1.4 | Edge Case | The user attempts to register with an already existing username/ID. | The system attempts to create the account. | The operation fails, and an error message "User ID already exists" is returned. |
| AC-1.5 | Technical | The account is created successfully. | The system stores the account data. | The cash balance field is stored in a suitable financial data type (e.g., DECIMAL(19, 4)) to prevent rounding errors. |

**UI/UX Specs**
*   **Component:** Simple registration form (Username field, Submit button).
*   **Feedback:** Success message upon creation ("Welcome! Your initial balance is $0.00."). Error message for failure (AC-1.4).
*   **Accessibility:** All form fields must have appropriate labels and keyboard navigation support.

**Test Scenarios (Data Examples)**

| Input (Username) | Expected Initial Cash Balance | Expected Holdings | Expected System Response |
| :--- | :--- | :--- | :--- |
| user_alpha | $0.00 | {} (Empty Dictionary) | Account Created Successfully |
| user_alpha | N/A | N/A | Error: User ID already exists |

---

## Story 2: Fund Withdrawal (Balance Check Enforced)

| Field | Detail |
| :--- | :--- |
| **ID** | ACCT-003 |
| **Title** | Withdraw Funds Safely |
| **Business Value** | Allows users to manage their cash balance while ensuring financial simulation integrity by preventing overdrafts. |
| **Priority** | P1 - Must Have (Crucial Constraint) |

**User Story Statement**
As an account manager,
I want to withdraw a specified amount of funds,
So that I can reduce the cash balance, but only if the remaining balance does not become negative.

**Acceptance Criteria**

| ID | Type | Given | When | Then |
| :--- | :--- | :--- | :--- | :--- |
| AC-2.1 | Happy Path | Current cash balance is $500.00. | I attempt to withdraw $150.00. | The withdrawal succeeds, and the new cash balance is $350.00. |
| AC-2.2 | Edge Case | Current cash balance is $200.00. | I attempt to withdraw $200.00 (the exact balance). | The withdrawal succeeds, and the new cash balance is $0.00. |
| AC-2.3 | Edge Case | Current cash balance is $100.00. | I attempt to withdraw $0.00. | The withdrawal fails (or is ignored), and the balance remains $100.00. |
| AC-2.4 | Error Case | Current cash balance is $100.00. | I attempt to withdraw $100.01. | The withdrawal is rejected, the balance remains $100.00, and an error message "Insufficient funds" is displayed. |
| AC-2.5 | Technical | A withdrawal transaction occurs. | The system records the event. | A detailed transaction record (type: WITHDRAWAL, amount, timestamp) is logged in the user's transaction history. |
| AC-2.6 | Error Case | I attempt to withdraw a negative amount (-50.00). | The system processes the request. | The withdrawal is rejected, and an error message "Amount must be positive" is displayed. |

**UI/UX Specs**
*   **Component:** Withdrawal input field (numeric, two decimal places), "Withdraw" button.
*   **Pre-requisite:** Display current available cash balance clearly above the input field.
*   **Error Handling:** Non-blocking modal or inline error message detailing *why* the transaction failed (e.g., "Withdrawal amount exceeds available balance of $X.XX").

**Test Scenarios (Data Examples)**

| Start Balance | Withdrawal Amount | Expected End Balance | Expected Outcome |
| :--- | :--- | :--- | :--- |
| $500.00 | $150.00 | $350.00 | Success |
| $100.00 | $100.01 | $100.00 | Failure (Insufficient Funds) |
| $75.50 | $75.50 | $0.00 | Success |
| $100.00 | $-50.00 | $100.00 | Failure (Invalid Amount) |

---

## Story 3: Buying Shares (Affordability Check Enforced)

| Field | Detail |
| :--- | :--- |
| **ID** | TRADE-001 |
| **Title** | Execute Buy Order with Insufficient Funds Check |
| **Business Value** | Enables core simulation trading functionality while enforcing the critical constraint that users cannot spend more cash than they possess. |
| **Priority** | P1 - Must Have (Crucial Constraint) |

**User Story Statement**
As a trading simulation user,
I want to buy a specified quantity of shares (symbol),
So that my cash balance is debited by the total cost, my holdings are updated, and the transaction is blocked if I cannot afford it.

**Acceptance Criteria**

| ID | Type | Given | When | Then |
| :--- | :--- | :--- | :--- | :--- |
| AC-3.1 | Technical Setup | The system requires the current price of 'AAPL'. | The function `get_share_price('AAPL')` is called. | The function returns the simulated price (e.g., $150.00) used for calculation. |
| AC-3.2 | Happy Path | Cash balance is $2,000.00. AAPL price is $150.00. | I buy 10 shares of AAPL (Total Cost: $1,500.00). | The transaction succeeds, cash balance updates to $500.00, and holdings increase by 10 AAPL. |
| AC-3.3 | Edge Case | Cash balance is $1,950.00. TSLA price is $195.00. | I buy 10 shares of TSLA (Total Cost: $1,950.00). | The transaction succeeds, cash balance updates to $0.00, and holdings increase by 10 TSLA. |
| AC-3.4 | Error Case | Cash balance is $100.00. GOOGL price is $130.00. | I attempt to buy 1 share of GOOGL (Total Cost: $130.00). | The transaction is rejected, cash balance remains $100.00, and an error message "Insufficient funds to cover trade cost" is returned. |
| AC-3.5 | Technical | A successful buy order is recorded. | The system logs the transaction. | The log includes the share symbol, quantity, price *at time of execution*, total cost, and transaction type (BUY). |
| AC-3.6 | Error Case | I attempt to buy 10 shares of an invalid symbol (e.g., "MSFT"). | The system attempts to retrieve the price. | The transaction is rejected, and an error message "Invalid or unsupported share symbol" is returned. |

**UI/UX Specs**
*   **Component:** Trading form with fields for Symbol (Dropdown/Autocomplete), Quantity (Integer input), and a "Buy" button.
*   **Real-time Feedback:** Display calculated total cost dynamically based on input quantity and current simulated price before submission.
*   **Success:** Confirmation message showing executed price and new balance.

**Test Scenarios (Data Examples, using simulated prices: AAPL=$150, TSLA=$195, GOOGL=$130)**

| Start Balance | Symbol | Price Used | Quantity | Total Cost | Expected End Balance | Expected Outcome |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| $5,000.00 | AAPL | $150.00 | 15 | $2,250.00 | $2,750.00 | Success |
| $1,000.00 | TSLA | $195.00 | 6 | $1,170.00 | $1,000.00 | Failure (Insufficient Funds) |
| $1,300.00 | GOOGL | $130.00 | 10 | $1,300.00 | $0.00 | Success |
| $5,000.00 | INVALID | N/A | 10 | N/A | $5,000.00 | Failure (Invalid Symbol) |

---

## Story 4: Selling Shares (Possession Check Enforced)

| Field | Detail |
| :--- | :--- |
| **ID** | TRADE-002 |
| **Title** | Execute Sell Order with Insufficient Holdings Check |
| **Business Value** | Allows users to liquidate holdings while enforcing the constraint that users cannot sell shares they do not currently own (preventing short selling in this simple simulation). |
| **Priority** | P1 - Must Have (Crucial Constraint) |

**User Story Statement**
As a trading simulation user,
I want to sell a specified quantity of shares (symbol),
So that my cash balance is credited by the sale proceeds, my holdings are reduced, and the transaction is blocked if I do not own enough shares.

**Acceptance Criteria**

| ID | Type | Given | When | Then |
| :--- | :--- | :--- | :--- | :--- |
| AC-4.1 | Happy Path | User holds 20 AAPL. AAPL price is $150.00. | I sell 10 shares of AAPL (Total Proceeds: $1,500.00). | The transaction succeeds, cash balance increases by $1,500.00, and holdings decrease to 10 AAPL. |
| AC-4.2 | Edge Case | User holds 5 TSLA. TSLA price is $195.00. | I sell 5 shares of TSLA (liquidating entire position). | The transaction succeeds, cash balance is credited, and holdings for TSLA become 0. |
| AC-4.3 | Error Case | User holds 5 AAPL. AAPL price is $150.00. | I attempt to sell 6 shares of AAPL. | The transaction is rejected, holdings remain 5 AAPL, and an error message "Insufficient holdings for AAPL" is returned. |
| AC-4.4 | Error Case | User holds 10 AAPL and 5 TSLA. | I attempt to sell 5 shares of GOOGL (which I do not hold). | The transaction is rejected, and an error message "Insufficient holdings for GOOGL" is returned. |
| AC-4.5 | Technical | A successful sell order is recorded. | The system logs the transaction. | The log includes the share symbol, quantity, price *at time of execution*, total proceeds, and transaction type (SELL). |
| AC-4.6 | Technical | The system requires the current price of 'GOOGL'. | The function `get_share_price('GOOGL')` is called. | The function returns the simulated price (e.g., $130.00) used for calculation. |

**UI/UX Specs**
*   **Component:** Trading form (Symbol, Quantity, "Sell" button).
*   **Information Display:** Must prominently display the user's current holdings for the selected symbol (e.g., "Available to Sell: 20 AAPL").
*   **Error Handling:** Clear, immediate feedback when attempting to sell more than held.

**Test Scenarios (Data Examples, using simulated prices: AAPL=$150, TSLA=$195, GOOGL=$130)**

| Start Holdings | Symbol | Price Used | Quantity Sold | Expected Change in Holdings | Expected Outcome |
| :--- | :--- | :--- | :--- | :--- | :--- |
| 20 AAPL | AAPL | $150.00 | 15 | -15 AAPL (New: 5) | Success |
| 5 TSLA | TSLA | $195.00 | 6 | 0 | Failure (Insufficient Holdings) |
| 0 GOOGL | GOOGL | $130.00 | 1 | 0 | Failure (Insufficient Holdings) |
| 10 AAPL | AAPL | $150.00 | 10 | -10 AAPL (New: 0) | Success (Full liquidation) |

---

## Story 5: Portfolio Summary and P&L Reporting

| Field | Detail |
| :--- | :--- |
| **ID** | RPT-001 |
| **Title** | View Real-time Portfolio Value, Holdings, and P&L |
| **Business Value** | Provides users with critical visibility into their financial performance and current assets, fulfilling core simulation requirements. |
| **Priority** | P2 - Should Have (Requires core trading stories to be complete) |

**User Story Statement**
As a trading simulation user,
I want to view a summary of my portfolio, including current share holdings, total market value, cash balance, and profit/loss relative to my initial deposits,
So that I can quickly assess my financial standing and performance.

**Acceptance Criteria**

| ID | Type | Given | When | Then |
| :--- | :--- | :--- | :--- | :--- |
| AC-5.1 | Technical Setup | The report is generated. | The system calculates the market value of shares. | The system must call `get_share_price(symbol)` for every held symbol to determine the current value. |
| AC-5.2 | Calculation | Portfolio: 10 AAPL (Current $160), Cash: $500. Total Deposits: $2,000. | I request the portfolio summary. | Total Portfolio Value is reported as $2,100.00 ($1,600 share value + $500 cash). |
| AC-5.3 | Calculation | Total Portfolio Value is $2,100.00. Total Deposits is $2,000.00. | I request the profit/loss (P&L). | The realized/unrealized P&L is reported as +$100.00. |
| AC-5.4 | Edge Case | User has $0.00 cash and zero holdings. Total Deposits: $100.00. | I request the P&L report. | The P&L is reported as -$100.00. |
| AC-5.5 | Happy Path | User holds 10 AAPL and 5 TSLA, and $50 cash. | I request the holdings report. | The report lists both AAPL and TSLA with their current quantity, current price, and individual market value. |
| AC-5.6 | Technical | The P&L calculation relies on initial deposits. | The system must maintain a running tally of all 'Deposit' transactions (ignoring withdrawals) to establish the 'Initial Deposit' baseline. | The baseline calculation is: SUM(All Deposit Transactions). |

**UI/UX Specs**
*   **Dashboard View:** A dedicated dashboard screen or section showing key metrics.
*   **Data Layout:** Use a structured table for Holdings (Symbol, Quantity, Current Price, Total Value). Separate cards/sections for Cash Balance, Total Portfolio Value, and P&L.
*   **P&L Visualization:** P&L should be color-coded (Green for positive, Red for negative).

**Test Scenarios (Simulated Prices: AAPL=$160, TSLA=$200, GOOGL=$120)**

| Start Deposits | Holdings | Current Cash | Calculated Total Value | Calculated P&L |
| :--- | :--- | :--- | :--- | :--- |
| $10,000.00 | 50 AAPL, 10 TSLA | $1,000.00 | $11,000.00 ($8k + $2k + $1k) | +$1,000.00 |
| $5,000.00 | 0 Holdings | $4,500.00 | $4,500.00 | -$500.00 |
| $2,000.00 | 10 GOOGL | $0.00 | $1,200.00 | -$800.00 |
| $1,000.00 | 0 Holdings | $1,000.00 | $1,000.00 | $0.00 (Breakeven) |
```