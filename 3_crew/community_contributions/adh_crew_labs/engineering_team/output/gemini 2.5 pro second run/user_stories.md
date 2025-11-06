```markdown
# Product Requirements Document: Trading Simulation Platform

This document outlines the user stories for the initial development of the Account Management System for the trading simulation platform. These stories are designed to be developer-ready, adhering to INVEST principles.

---

## Epic: Account & Portfolio Management

This epic covers the foundational features for a user to manage their account, trade simulated shares, and view their portfolio's performance.

### Story: ACC-001 - User Account Creation

-   **ID**: ACC-001
-   **Title**: User Account Creation
-   **User Story**: As a new visitor, I want to create a trading account so that I can start using the simulation platform.
-   **Business Value**: Essential for user acquisition. This is the entry point for all users into the platform.
-   **Priority**: High

#### Acceptance Criteria

1.  **Given** a new user is on the registration page
    **When** they enter a unique email, a valid password (meeting complexity rules), and their name
    **And** they click the "Sign Up" button
    **Then** their account is created successfully
    **And** they are redirected to the login page with a success message.
2.  **Given** a new account has just been created
    **When** the user logs in for the first time
    **Then** their initial cash balance is $0.00
    **And** they have no stock holdings.
3.  **Given** a user is on the registration page
    **When** they attempt to register with an email that already exists in the system
    **Then** the system displays an error message "This email is already registered."
    **And** the account is not created.
4.  **Given** a user is on the registration page
    **When** they enter a password that does not meet the complexity requirements (e.g., less than 8 characters)
    **Then** the system displays an error message detailing the password requirements
    **And** the account is not created.
5.  **Given** a user is on the registration page
    **When** they submit the form without filling in a required field (e.g., email)
    **Then** the system displays an inline error message next to the empty field
    **And** the account is not created.
6.  **Given** a user has successfully registered
    **When** an administrator checks the user database
    **Then** a new user record exists with the provided details and a securely hashed password.

#### UI/UX Specifications

-   **Wireframe**: See `wireframes/registration_form.png`.
-   **Components**:
    -   Input field for "Full Name" (Type: text)
    -   Input field for "Email Address" (Type: email)
    -   Input field for "Password" (Type: password, with a show/hide toggle)
    -   "Sign Up" button (Primary action)
    -   Link to "Already have an account? Log In"
    -   Error message display areas for each field and for general form errors.
-   **Accessibility**: All form fields must have associated labels. Error messages should be linked to the relevant input using `aria-describedby`.

#### Test Scenarios

| Input                                  | Expected Output                                                              | Test Type   |
| -------------------------------------- | ---------------------------------------------------------------------------- | ----------- |
| `name`: 'John Doe', `email`: 'john@test.com', `password`: 'Password123' (assuming valid) | Account created, user redirected to login. | Happy Path  |
| `name`: 'Jane Doe', `email`: 'john@test.com' (existing), `password`: 'Password123' | Error: "This email is already registered." | Error Case  |
| `name`: 'Jane Doe', `email`: 'jane@test.com', `password`: 'pass' (too short) | Error: "Password must be at least 8 characters." | Error Case  |
| `name`: '', `email`: 'jane@test.com', `password`: 'Password123' | Error: "Full Name is required." beside the name field. | Error Case  |

---

### Story: ACC-002 - Deposit Funds

-   **ID**: ACC-002
-   **Title**: Deposit Funds into Account
-   **User Story**: As a user with an account, I want to deposit funds so that I have the cash to buy shares.
-   **Business Value**: Enables users to start trading. A core function of the simulation.
-   **Priority**: High

#### Acceptance Criteria

1.  **Given** I am a logged-in user with a cash balance of $1,000
    **When** I navigate to the "Deposit" page and deposit $500
    **Then** my new cash balance is $1,500
    **And** a "DEPOSIT" transaction for $500 is recorded in my transaction history.
2.  **Given** I am a logged-in user with a cash balance of $0
    **When** I deposit $10,000
    **Then** my new cash balance is $10,000.
3.  **Given** I am a logged-in user with a cash balance of $50
    **When** I deposit a very small amount, like $0.01
    **Then** my new cash balance is $50.01.
4.  **Given** I am a logged-in user
    **When** I attempt to deposit $0
    **Then** I see an error message "Deposit amount must be greater than zero."
    **And** my balance remains unchanged.
5.  **Given** I am a logged-in user
    **When** I attempt to deposit a negative amount, like -$100
    **Then** I see an error message "Deposit amount cannot be negative."
    **And** my balance remains unchanged.
6.  **Given** I am a logged-in user
    **When** I enter a non-numeric value like "one hundred" in the deposit field
    **Then** the form validation prevents submission and shows an error "Please enter a valid number."
    **And** my balance remains unchanged.

#### UI/UX Specifications

-   **Wireframe**: See `wireframes/funds_management.png`.
-   **Components**:
    -   Display of "Current Cash Balance".
    -   Input field for "Deposit Amount" (Type: number, with `min="0.01"` and `step="0.01"`).
    -   "Deposit" button (Primary action).
    -   Confirmation modal on successful deposit.

#### Test Scenarios

| Initial Balance | Input Amount | Expected Final Balance | Expected Transaction | Test Type   |
| --------------- | ------------ | ---------------------- | -------------------- | ----------- |
| $1,000.00       | $500.00      | $1,500.00              | DEPOSIT +$500.00     | Happy Path  |
| $0.00           | $0.01        | $0.01                  | DEPOSIT +$0.01       | Edge Case   |
| $5,000.00       | -$100.00     | $5,000.00              | None                 | Error Case  |
| $5,000.00       | $0.00        | $5,000.00              | None                 | Error Case  |

---

### Story: ACC-003 - Withdraw Funds

-   **ID**: ACC-003
-   **Title**: Withdraw Funds from Account
-   **User Story**: As a user with an account, I want to withdraw funds so that I can realize my simulated profits.
-   **Business Value**: Completes the core cash management loop for the user.
-   **Priority**: High

#### Acceptance Criteria

1.  **Given** I am a logged-in user with a cash balance of $1,500
    **When** I navigate to the "Withdraw" page and withdraw $500
    **Then** my new cash balance is $1,000
    **And** a "WITHDRAW" transaction for $500 is recorded in my transaction history.
2.  **Given** I am a logged-in user with a cash balance of $250.50
    **When** I withdraw my entire balance of $250.50
    **Then** my new cash balance is $0.00.
3.  **Given** I am a logged-in user with a cash balance of $100
    **When** I attempt to withdraw $100.01
    **Then** I see an error message "Withdrawal amount cannot exceed your cash balance."
    **And** my balance remains $100.
4.  **Given** I am a logged-in user
    **When** I attempt to withdraw $0
    **Then** I see an error message "Withdrawal amount must be greater than zero."
    **And** my balance remains unchanged.
5.  **Given** I am a logged-in user
    **When** I attempt to withdraw a negative amount, like -$100
    **Then** I see an error message "Withdrawal amount cannot be negative."
    **And** my balance remains unchanged.

#### UI/UX Specifications

-   **Wireframe**: See `wireframes/funds_management.png`.
-   **Components**:
    -   Display of "Current Cash Balance".
    -   Input field for "Withdrawal Amount" (Type: number).
    -   "Withdraw" button.
    -   Confirmation modal on successful withdrawal.

#### Test Scenarios

| Initial Balance | Input Amount | Expected Final Balance | Expected Transaction | Test Type   |
| --------------- | ------------ | ---------------------- | -------------------- | ----------- |
| $1,000.00       | $200.00      | $800.00                | WITHDRAW -$200.00    | Happy Path  |
| $500.00         | $500.00      | $0.00                  | WITHDRAW -$500.00    | Edge Case   |
| $500.00         | $500.01      | $500.00                | None                 | Error Case  |
| $500.00         | -$50.00      | $500.00                | None                 | Error Case  |

---

### Story: ACC-004 - Buy Shares

-   **ID**: ACC-004
-   **Title**: Buy Shares of a Stock
-   **User Story**: As a user with funds, I want to buy shares of a stock so that I can build my investment portfolio.
-   **Business Value**: The primary trading action that allows users to engage with the market simulation.
-   **Priority**: High

#### Acceptance Criteria

1.  **Given** I have a cash balance of $10,000 and no shares of AAPL
    **And** the current price of AAPL is $150.00
    **When** I buy 10 shares of AAPL
    **Then** my cash balance is reduced by $1,500 to $8,500
    **And** my portfolio shows I own 10 shares of AAPL
    **And** a "BUY AAPL 10 @ $150.00" transaction is recorded.
2.  **Given** I have a cash balance of $5,000 and own 5 shares of TSLA
    **And** the current price of TSLA is $200.00
    **When** I buy 10 more shares of TSLA
    **Then** my cash balance is reduced by $2,000 to $3,000
    **And** my portfolio shows I own 15 shares of TSLA.
3.  **Given** I have a cash balance of $300
    **And** the current price of GOOGL is $100.00
    **When** I attempt to buy 4 shares of GOOGL (costing $400)
    **Then** I see an error message "Insufficient funds to complete this purchase."
    **And** my cash balance remains $300 and I own 0 shares of GOOGL.
4.  **Given** I am a logged-in user
    **When** I attempt to buy 0 shares of any stock
    **Then** I see an error message "Quantity must be greater than zero."
    **And** no transaction occurs.
5.  **Given** I have a cash balance of $150
    **And** the current price of AAPL is $150.00
    **When** I buy exactly 1 share of AAPL
    **Then** my cash balance becomes $0
    **And** my portfolio shows I own 1 share of AAPL.
6.  **Given** I am a logged-in user
    **When** I attempt to buy shares for a symbol that does not exist (e.g., "XYZ")
    **Then** I see an error message "Invalid stock symbol."
    **And** no transaction occurs.

#### Technical Notes
- This story depends on the availability of the `get_share_price(symbol)` function.
- The test implementation of `get_share_price` should return fixed prices for AAPL, TSLA, and GOOGL for predictable testing.
- The total cost of the transaction is `quantity * get_share_price(symbol)`.

#### UI/UX Specifications

-   **Wireframe**: See `wireframes/trade_execution.png`.
-   **Components**:
    -   Input field for "Stock Symbol" (e.g., AAPL).
    -   Input field for "Quantity" (Type: number, `min="1"`).
    -   "Buy" button.
    -   A real-time price quote display next to the symbol field.
    -   A display showing "Estimated Cost" before confirming the trade.

#### Test Scenarios

| Initial Cash | Symbol | Quantity | Share Price | Expected Result                                        | Test Type   |
| ------------ | ------ | -------- | ----------- | ------------------------------------------------------ | ----------- |
| $10,000      | AAPL   | 10       | $150        | Success. New Cash: $8,500. Holdings: 10 AAPL.          | Happy Path  |
| $1,499       | AAPL   | 10       | $150        | Error: "Insufficient funds."                           | Error Case  |
| $1,500       | AAPL   | 10       | $150        | Success. New Cash: $0. Holdings: 10 AAPL.              | Edge Case   |
| $10,000      | AAPL   | 0        | $150        | Error: "Quantity must be greater than zero."           | Error Case  |
| $10,000      | FAKE   | 10       | N/A         | Error: "Invalid stock symbol."                         | Error Case  |

---

### Story: ACC-005 - Sell Shares

-   **ID**: ACC-005
-   **Title**: Sell Shares of a Stock
-   **User Story**: As a user who owns shares, I want to sell shares of a stock so that I can lock in gains or cut losses.
-   **Business Value**: The second primary trading action, allowing users to complete the investment cycle.
-   **Priority**: High

#### Acceptance Criteria

1.  **Given** I own 50 shares of TSLA and have a cash balance of $1,000
    **And** the current price of TSLA is $200.00
    **When** I sell 20 shares of TSLA
    **Then** my cash balance increases by $4,000 to $5,000
    **And** my portfolio shows I own 30 shares of TSLA
    **And** a "SELL TSLA 20 @ $200.00" transaction is recorded.
2.  **Given** I own 15 shares of GOOGL
    **And** the current price of GOOGL is $100.00
    **When** I sell all 15 shares of GOOGL
    **Then** my cash balance increases by $1,500
    **And** my portfolio shows I own 0 shares of GOOGL.
3.  **Given** I own 10 shares of AAPL
    **When** I attempt to sell 11 shares of AAPL
    **Then** I see an error message "You do not have enough shares to sell."
    **And** my holdings and cash balance remain unchanged.
4.  **Given** I do not own any shares of TSLA
    **When** I attempt to sell 5 shares of TSLA
    **Then** I see an error message "You do not own any shares of this stock."
    **And** no transaction occurs.
5.  **Given** I own 10 shares of AAPL
    **When** I attempt to sell 0 shares of AAPL
    **Then** I see an error message "Quantity must be greater than zero."
    **And** no transaction occurs.

#### Technical Notes
- Also depends on `get_share_price(symbol)` to calculate the value of the sale.
- The total value of the sale is `quantity * get_share_price(symbol)`.

#### UI/UX Specifications

-   **Wireframe**: See `wireframes/trade_execution.png`.
-   **Components**:
    -   Uses the same UI as the "Buy" story, but with the "Sell" button.
    -   The UI should clearly show how many shares of the selected symbol the user currently owns.
    -   A display showing "Estimated Credit" before confirming the trade.

#### Test Scenarios

| Initial Holdings | Symbol | Quantity | Share Price | Expected Result                                         | Test Type   |
| ---------------- | ------ | -------- | ----------- | ------------------------------------------------------- | ----------- |
| 50 TSLA          | TSLA   | 20       | $200        | Success. New Cash += $4,000. Holdings: 30 TSLA.         | Happy Path  |
| 20 AAPL          | AAPL   | 20       | $150        | Success. New Cash += $3,000. Holdings: 0 AAPL.          | Edge Case   |
| 20 AAPL          | AAPL   | 21       | $150        | Error: "You do not have enough shares to sell."         | Error Case  |
| 0 GOOGL          | GOOGL  | 1        | $100        | Error: "You do not own any shares of this stock."       | Error Case  |

---

### Story: ACC-006 - View Portfolio Dashboard

-   **ID**: ACC-006
-   **Title**: View Portfolio Dashboard
-   **User Story**: As a user, I want to view my portfolio dashboard so that I can see the total value of my holdings, my cash balance, and my overall profit/loss at a glance.
-   **Business Value**: Provides users with critical feedback on their performance, driving engagement.
-   **Priority**: High

#### Acceptance Criteria

1.  **Given** I have a cash balance of $5,000
    **And** I own 10 shares of AAPL (current price $150) and 20 shares of TSLA (current price $200)
    **And** my total deposits are $10,000 and total withdrawals are $0
    **When** I view my portfolio dashboard
    **Then** I see my Cash Balance as $5,000
    **And** I see my Total Portfolio Value as $10,500 ($5,000 cash + $1,500 AAPL + $4,000 TSLA)
    **And** I see my Total P/L as +$500 ($10,500 value - $10,000 deposits).
2.  **Given** I have just created my account and deposited $1,000
    **When** I view my portfolio dashboard
    **Then** I see my Cash Balance as $1,000
    **And** I see my Total Portfolio Value as $1,000
    **And** I see my Total P/L as $0.
3.  **Given** my portfolio value has dropped below my net deposits
    **And** my Total Portfolio Value is $8,000 and my net deposits are $10,000
    **When** I view my portfolio dashboard
    **Then** I see my Total P/L as -$2,000, displayed in red.
4.  **Given** I have a portfolio
    **When** I view the holdings table on the dashboard
    **Then** each row displays the Stock Symbol, Quantity, Current Price, and Total Value.
5.  **Given** I sell all my shares and have only cash
    **When** I view the dashboard
    **Then** the holdings table is empty or shows a message "You do not own any shares."
    **And** the Total Portfolio Value is equal to my Cash Balance.

#### Technical Notes
- `Total Portfolio Value = Cash Balance + SUM(quantity * get_share_price(symbol) for each holding)`
- `Total P/L = Total Portfolio Value - Total Deposits + Total Withdrawals`

#### UI/UX Specifications

-   **Wireframe**: See `wireframes/dashboard.png`.
-   **Components**:
    -   Large "cards" or "widgets" for:
        -   Total Portfolio Value
        -   Total P/L (Profit/Loss), conditionally colored (green for profit, red for loss)
        -   Cash Balance
    -   A table of current "Holdings" with columns: Symbol, Quantity, Current Price, Total Value.

#### Test Scenarios

| Cash    | Holdings                | Net Deposits | Share Prices           | Expected Portfolio Value | Expected P/L | Test Type  |
| ------- | ----------------------- | ------------ | ---------------------- | ------------------------ | ------------ | ---------- |
| $5,000  | 10 AAPL, 20 TSLA        | $10,000      | AAPL: $150, TSLA: $200 | $10,500                  | +$500        | Happy Path |
| $1,000  | (none)                  | $1,000       | N/A                    | $1,000                   | $0           | Edge Case  |
| $2,000  | 5 GOOGL                 | $5,000       | GOOGL: $90             | $2,450                   | -$2,550      | Happy Path |

---

### Story: ACC-007 - View Transaction History

-   **ID**: ACC-007
-   **Title**: View Transaction History
-   **User Story**: As a user, I want to view a list of all my past transactions so that I can review my trading activity.
-   **Business Value**: Provides transparency and allows users to track their actions over time.
-   **Priority**: Medium

#### Acceptance Criteria

1.  **Given** I have made a deposit, a withdrawal, a stock purchase, and a stock sale
    **When** I view my transaction history page
    **Then** I see four distinct entries corresponding to each action.
2.  **Given** I have multiple transactions
    **When** I view the transaction history
    **Then** the transactions are listed in reverse chronological order (most recent first).
3.  **Given** I view my transaction history
    **When** I look at a "BUY" transaction entry
    **Then** it clearly shows the date/time, type ("BUY"), a description (e.g., "10 shares of AAPL @ $150.00"), and the total value of the transaction (-$1,500.00).
4.  **Given** I view my transaction history
    **When** I look at a "DEPOSIT" transaction entry
    **Then** it clearly shows the date/time, type ("DEPOSIT"), and the amount (+$500.00).
5.  **Given** I am a new user with no transactions
    **When** I view the transaction history page
    **Then** I see a message like "You have no transactions yet."

#### UI/UX Specifications

-   **Wireframe**: See `wireframes/transaction_history.png`.
-   **Components**:
    -   A table with columns: `Date`, `Type`, `Description`, `Amount/Value`.
    -   Pagination controls (for future consideration, not required for MVP).

#### Test Scenarios

| Action Sequence                                  | Expected Transaction Log (most recent first)                                   | Test Type   |
| ------------------------------------------------ | ------------------------------------------------------------------------------ | ----------- |
| 1. Deposit $10k<br/>2. Buy 10 AAPL @ $150 | `[Timestamp] | BUY | 10 shares of AAPL @ $150.00 | -$1,500.00`<br/>`[Timestamp] | DEPOSIT | Deposit | +$10,000.00` | Happy Path  |
| 1. Deposit $1k<br/>2. Withdraw $200              | `[Timestamp] | WITHDRAW | Withdrawal | -$200.00`<br/>`[Timestamp] | DEPOSIT | Deposit | +$1,000.00` | Happy Path  |
| (New User)                                       | Table is empty, displays "You have no transactions yet."                       | Edge Case   |

```