# User Stories: Trading Simulation Platform - Account Management

This document breaks down the client requirements for the trading simulation platform into a series of actionable, developer-ready user stories. Each story follows the INVEST principles (Independent, Negotiable, Valuable, Estimable, Small, Testable) and includes comprehensive acceptance criteria, UI/UX specifications, and technical context to eliminate ambiguity.

---

### **Epic 1: Account & Cash Management**

This epic covers the fundamental user actions of managing their cash balance, which is the prerequisite for all trading activity.

---

#### **Story 1: Deposit Funds into Account**

*   **ID**: `ACC-002`
*   **Title**: User Deposits Funds into their Trading Account
*   **User Story**: As a registered user, I want to deposit funds into my account, so that I have the cash balance required to buy shares.
*   **Business Value**: Enables users to start trading. A fundamental prerequisite for platform engagement and the core monetization loop (in a real-world scenario).
*   **Priority**: High

**Acceptance Criteria:**

| Type         | Scenario                                          | Given                                                            | When                                                | Then                                                                                                                                     |
|--------------|---------------------------------------------------|------------------------------------------------------------------|-----------------------------------------------------|------------------------------------------------------------------------------------------------------------------------------------------|
| **Happy Path** | Initial Deposit                                   | I am a logged-in user with a cash balance of $0.00                 | I submit a deposit for $5,000.00                      | my cash balance is updated to $5,000.00 AND a 'DEPOSIT' transaction for $5,000.00 is recorded in my transaction history.               |
| **Happy Path** | Subsequent Deposit                                | I am a logged-in user with a cash balance of $2,500.00               | I submit a deposit for $1,000.00                      | my cash balance is updated to $3,500.00 AND a new 'DEPOSIT' transaction for $1,000.00 is recorded.                                      |
| **Happy Path** | Deposit with Cents                                | I am a logged-in user with a cash balance of $100.00                 | I submit a deposit for $50.75                         | my cash balance is updated to $150.75.                                                                                                   |
| **Edge Case**  | Depositing Zero                                   | I am a logged-in user                                            | I attempt to deposit $0                               | the system shows an error message "Deposit amount must be greater than zero." AND my balance and transactions remain unchanged.          |
| **Edge Case**  | Extremely Large Deposit                           | I am a logged-in user                                            | I attempt to deposit $1,000,000,000,000               | the system should handle the large number without crashing AND successfully update the balance.                                          |
| **Error Case** | Negative Deposit                                  | I am a logged-in user                                            | I attempt to deposit -$100                            | the system shows an error message "Deposit amount cannot be negative." AND my balance remains unchanged.                                 |
| **Error Case** | Non-numeric Input                                 | I am a logged-in user                                            | I enter "abc" as the deposit amount and submit        | the system shows an error message "Please enter a valid numeric amount." AND my balance remains unchanged.                               |

**UI/UX Specs:**

*   **Wireframe/Mockup Description**:
    *   A simple form within the user's "Account" or "Dashboard" page.
    *   **UI Components**:
        *   Text Input: `Deposit Amount` (numeric, accepts up to 2 decimal places).
        *   Button: `Deposit Funds`.
        *   Static Text Display: `Current Cash Balance: $X,XXX.XX`.
        *   Feedback:
            *   Success: A toast notification "Success: $5,000.00 has been added to your account."
            *   Error: Inline error message below the input field (e.g., "Please enter a valid amount.").
*   **Accessibility Checklist**:
    *   [x] All form inputs have associated `<label>` elements.
    *   [x] Error messages are programmatically linked to inputs using `aria-describedby`.
    *   [x] All interactive elements are keyboard accessible and have focus indicators.

**Test Scenarios:**

| Input Amount | Initial Balance | Action         | Expected Final Balance | Expected Transaction Logged |
|--------------|-----------------|----------------|------------------------|-----------------------------|
| 5000         | 0               | Deposit        | 5000                   | Yes (DEPOSIT, +5000)        |
| 123.45       | 1000            | Deposit        | 1123.45                | Yes (DEPOSIT, +123.45)      |
| 0            | 5000            | Attempt Deposit| 5000                   | No                          |
| -50          | 5000            | Attempt Deposit| 5000                   | No                          |
| "test"       | 5000            | Attempt Deposit| 5000                   | No                          |

---

#### **Story 2: Withdraw Funds from Account**

*   **ID**: `ACC-003`
*   **Title**: User Withdraws Funds from their Trading Account
*   **User Story**: As a registered user, I want to withdraw available funds from my account, so that I can realize my cash holdings.
*   **Business Value**: Provides users with a way to take out funds, building trust and completing the financial loop of the simulation.
*   **Priority**: High

**Acceptance Criteria:**

| Type         | Scenario                                          | Given                                                            | When                                                | Then                                                                                                                                     |
|--------------|---------------------------------------------------|------------------------------------------------------------------|-----------------------------------------------------|------------------------------------------------------------------------------------------------------------------------------------------|
| **Happy Path** | Partial Withdrawal                                | I am a logged-in user with a cash balance of $5,000.00               | I submit a withdrawal for $1,000.00                   | my cash balance is updated to $4,000.00 AND a 'WITHDRAW' transaction for $1,000.00 is recorded in my transaction history.             |
| **Happy Path** | Full Withdrawal                                   | I am a logged-in user with a cash balance of $4,000.00               | I submit a withdrawal for $4,000.00                   | my cash balance is updated to $0.00 AND a 'WITHDRAW' transaction for $4,000.00 is recorded.                                            |
| **Happy Path** | Withdrawal with Cents                             | I am a logged-in user with a cash balance of $150.75                 | I submit a withdrawal for $50.25                      | my cash balance is updated to $100.50.                                                                                                   |
| **Edge Case**  | Withdrawing Zero                                  | I am a logged-in user                                            | I attempt to withdraw $0                              | the system shows an error message "Withdrawal amount must be greater than zero." AND my balance remains unchanged.                       |
| **Error Case** | Insufficient Funds (Overdraft)                    | I am a logged-in user with a cash balance of $500.00                 | I attempt to withdraw $600.00                         | the system shows an error message "Insufficient funds. You cannot withdraw more than your available balance." AND my balance is unchanged. |
| **Error Case** | Negative Withdrawal                               | I am a logged-in user                                            | I attempt to withdraw -$100                           | the system shows an error message "Withdrawal amount cannot be negative." AND my balance remains unchanged.                              |
| **Error Case** | Non-numeric Input                                 | I am a logged-in user                                            | I enter "abc" as the withdrawal amount and submit     | the system shows an error message "Please enter a valid numeric amount." AND my balance remains unchanged.                               |

**UI/UX Specs:**

*   **Wireframe/Mockup Description**:
    *   Similar form to the Deposit feature, located in the "Account" page.
    *   **UI Components**:
        *   Text Input: `Withdrawal Amount` (numeric, currency format).
        *   Button: `Withdraw Funds`.
        *   Static Text Display: `Available for Withdrawal: $X,XXX.XX`.
        *   Feedback: Success toast and inline error messages.
*   **Accessibility Checklist**:
    *   [x] All form inputs have associated `<label>` elements.
    *   [x] Error messages are programmatically linked to inputs.
    *   [x] All interactive elements are keyboard accessible.

**Test Scenarios:**

| Input Amount | Initial Balance | Action            | Expected Final Balance | Expected Transaction Logged |
|--------------|-----------------|-------------------|------------------------|-----------------------------|
| 1000         | 5000            | Withdraw          | 4000                   | Yes (WITHDRAW, -1000)       |
| 5000         | 5000            | Withdraw          | 0                      | Yes (WITHDRAW, -5000)       |
| 5000.01      | 5000            | Attempt Withdraw  | 5000                   | No                          |
| -50          | 5000            | Attempt Withdraw  | 5000                   | No                          |

---

### **Epic 2: Trading Simulation**

This epic covers the core trading functionality, allowing users to buy and sell simulated shares.

---

#### **Story 3: Execute a Buy Order for Shares**

*   **ID**: `ACC-004`
*   **Title**: User Buys a Quantity of Shares
*   **User Story**: As a registered user, I want to buy a specified quantity of shares for a given stock symbol, so that I can invest my available cash and build my portfolio.
*   **Business Value**: This is the primary engagement feature of the simulation. It allows users to act on market information and build their portfolio.
*   **Priority**: High

**Acceptance Criteria:**

| Type         | Scenario                                          | Given                                                                              | When                                                         | Then                                                                                                                                                                                                                                   |
|--------------|---------------------------------------------------|------------------------------------------------------------------------------------|--------------------------------------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Happy Path** | New Stock Purchase                                | I am a logged-in user with a cash balance of $10,000 and the price of 'AAPL' is $150 | I submit a buy order for 10 shares of 'AAPL'                 | my cash balance is reduced by $1,500 to $8,500 AND my portfolio shows a new holding of 10 'AAPL' shares AND a 'BUY' transaction for 10 'AAPL' at $150/share is recorded.                                                          |
| **Happy Path** | Add to Existing Holding                           | I am a user with $10,000 cash and 5 'AAPL' shares, and 'AAPL' price is $150         | I submit a buy order for 10 more shares of 'AAPL'            | my cash balance is reduced by $1,500 to $8,500 AND my 'AAPL' holding is updated to 15 shares AND a new 'BUY' transaction is recorded.                                                                                                |
| **Happy Path** | Purchase with Exact Funds                         | I am a user with $1,500 cash and the price of 'AAPL' is $150                       | I submit a buy order for 10 shares of 'AAPL'                 | my cash balance becomes $0.00 AND my portfolio shows a new holding of 10 'AAPL' shares.                                                                                                                                                |
| **Edge Case**  | Buying Zero Shares                                | I am a logged-in user                                                              | I attempt to submit a buy order for 0 shares                 | the system shows an error "Quantity must be greater than zero." AND my balance and holdings are unchanged.                                                                                                                             |
| **Edge Case**  | Non-integer Shares (if unsupported)               | I am a logged-in user                                                              | I attempt to buy 1.5 shares of 'TSLA'                        | the system shows an error "Fractional shares are not supported." AND no transaction occurs.                                                                                                                                            |
| **Error Case** | Insufficient Funds                                | I am a user with $1,000 cash and the price of 'AAPL' is $150                       | I attempt to buy 10 shares of 'AAPL' (cost $1,500)           | the system shows an error "Insufficient funds to complete this transaction." AND my cash and holdings are unchanged.                                                                                                                   |
| **Error Case** | Invalid Stock Symbol                              | I am a logged-in user                                                              | I attempt to buy 10 shares of 'INVALID_SYMBOL'               | the system shows an error "Stock symbol 'INVALID_SYMBOL' not found." AND no transaction occurs.                                                                                                                                      |

**UI/UX Specs:**

*   **Wireframe/Mockup Description**:
    *   A "Trade" widget or page with a simple form.
    *   **UI Components**:
        *   Text Input: `Symbol` (e.g., AAPL).
        *   Number Input: `Quantity`.
        *   Toggle/Buttons: `Buy` / `Sell`. `Buy` is selected.
        *   Dynamic Text: `Estimated Cost: $XXXX.XX` (updates on quantity change).
        *   Static Text: `Available Cash: $YYYY.YY`.
        *   Button: `Execute Buy Order`.
        *   Feedback: Success/error toast notifications.
*   **Accessibility Checklist**:
    *   [x] All form inputs have associated `<label>` elements.
    *   [x] Dynamic cost calculation is announced by screen readers.
    *   [x] All interactive elements are keyboard accessible.

**Technical Notes:**

*   This story is dependent on the `get_share_price(symbol)` function. The front-end or back-end logic must call this function to calculate the estimated cost before submitting the transaction.
*   The transaction must be atomic: either the cash is debited AND shares are added, or the transaction fails completely. No partial states.

---

#### **Story 4: Execute a Sell Order for Shares**

*   **ID**: `ACC-005`
*   **Title**: User Sells a Quantity of Owned Shares
*   **User Story**: As a portfolio owner, I want to sell a specified quantity of shares I own, so that I can realize profits or reallocate my capital.
*   **Business Value**: Allows users to complete the trading cycle. Key for calculating profit/loss and making strategic decisions in the simulation.
*   **Priority**: High

**Acceptance Criteria:**

| Type         | Scenario                                          | Given                                                                              | When                                                         | Then                                                                                                                                                                                                                                   |
|--------------|---------------------------------------------------|------------------------------------------------------------------------------------|--------------------------------------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Happy Path** | Partial Sale of Holding                           | I am a user with $1,000 cash and 50 'TSLA' shares, and the price of 'TSLA' is $200  | I submit a sell order for 20 shares of 'TSLA'                | my cash balance is increased by $4,000 to $5,000 AND my 'TSLA' holding is reduced to 30 shares AND a 'SELL' transaction for 20 'TSLA' at $200/share is recorded.                                                                     |
| **Happy Path** | Complete Sale of Holding                          | I am a user with $1,000 cash and 50 'TSLA' shares, and 'TSLA' price is $200         | I submit a sell order for all 50 shares of 'TSLA'            | my cash balance is increased by $10,000 to $11,000 AND my 'TSLA' holding is removed from my portfolio AND a 'SELL' transaction is recorded.                                                                                             |
| **Edge Case**  | Selling Zero Shares                               | I am a logged-in user who owns 'TSLA' shares                                       | I attempt to submit a sell order for 0 shares                | the system shows an error "Quantity must be greater than zero." AND my balance and holdings are unchanged.                                                                                                                             |
| **Error Case** | Selling More Shares Than Owned                    | I am a user with 50 'TSLA' shares                                                  | I attempt to sell 51 shares of 'TSLA'                        | the system shows an error "You cannot sell more shares than you own. You have 50 TSLA shares." AND no transaction occurs.                                                                                                                |
| **Error Case** | Selling Shares Not Owned                          | I am a user with no 'GOOGL' shares                                                 | I attempt to sell 10 shares of 'GOOGL'                       | the system shows an error "You do not own any shares of GOOGL." AND no transaction occurs.                                                                                                                                              |
| **Error Case** | Invalid Stock Symbol                              | I am a logged-in user                                                              | I attempt to sell 10 shares of 'INVALID_SYMBOL'              | the system shows an error "Stock symbol 'INVALID_SYMBOL' not found."                                                                                                                                                                    |

**UI/UX Specs:**

*   **Wireframe/Mockup Description**:
    *   Utilizes the same "Trade" widget as the Buy story.
    *   **UI Components**:
        *   The `Sell` option would be selected in the `Buy` / `Sell` toggle.
        *   Dynamic Text: `Estimated Credit: $XXXX.XX`.
        *   Static Text: `Shares Owned: YY`.
        *   Button: `Execute Sell Order`.
*   **Technical Notes:**
    *   The sell action must validate against the user's current holdings for that specific symbol *before* executing.

---

### **Epic 3: Portfolio Reporting & Analytics**

This epic focuses on providing the user with feedback on their account status and trading performance.

---

#### **Story 5: View Portfolio Dashboard**

*   **ID**: `ACC-006`
*   **Title**: User Views their Portfolio Dashboard
*   **User Story**: As a trader, I want to see a dashboard summarizing my portfolio, so that I can quickly understand my current financial position, holdings, and overall performance.
*   **Business Value**: Provides critical feedback to the user, driving engagement and informing future trading decisions. This is the main "status" screen for the user.
*   **Priority**: High

**Acceptance Criteria:**

| Type         | Scenario                                          | Given                                                                                                                                   | When                             | Then                                                                                                                                                                                                                                                                                           |
|--------------|---------------------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------|----------------------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Happy Path** | User with cash and holdings                       | I have deposited a total of $10,000, have $1,500 in cash, and own 10 'AAPL' shares. The current price of 'AAPL' is $170.                  | I navigate to my dashboard       | I see: 'Total Portfolio Value: $10,200' ($1,500 cash + 10*$170 shares) AND 'Total Profit/Loss: +$200' ($10,200 value - $10,000 deposit) AND a holdings list showing 'AAPL', Quantity: 10, Current Value: $1,700.                                                                        |
| **Happy Path** | User at a loss                                    | I have deposited $10,000, have $1,500 in cash, and own 10 'AAPL' shares. The current price of 'AAPL' is $130.                           | I navigate to my dashboard       | I see: 'Total Portfolio Value: $2,800' ($1,500 cash + 10*$130 shares) AND 'Total Profit/Loss: -$7,200' ($2,800 value - $10,000 deposit). The P/L should be displayed in red.                                                                                                           |
| **Happy Path** | User with only cash                               | I have deposited $5,000 and have not made any trades.                                                                                   | I navigate to my dashboard       | I see: 'Total Portfolio Value: $5,000' AND 'Total Profit/Loss: $0' AND the holdings list is empty or shows "You do not have any holdings."                                                                                                                                                 |
| **Happy Path** | User with multiple holdings                       | I have $1,000 cash, 10 'AAPL' at $150 each, and 5 'TSLA' at $200 each. My total deposits are $3,000.                                      | I navigate to my dashboard       | I see: 'Total Portfolio Value: $3,500' ($1k cash + $1.5k AAPL + $1k TSLA) AND 'Total Profit/Loss: +$500' AND the holdings list shows both 'AAPL' and 'TSLA' with their respective quantities and values.                                                                                       |
| **Edge Case**  | User with zero balance and no holdings            | I have withdrawn all funds and sold all shares.                                                                                         | I navigate to my dashboard       | I see: 'Total Portfolio Value: $0', 'Total Profit/Loss: $X' (based on historical performance), and an empty holdings list.                                                                                                                                                           |
| **Error Case** | Share price service is unavailable                | The `get_share_price(symbol)` function fails for one of my holdings.                                                                    | I navigate to my dashboard       | The dashboard should still load AND show an error message for the affected holding (e.g., "Price data unavailable") AND calculate total value based on the available data, clearly indicating that the total is incomplete. The application should not crash. |

**UI/UX Specs:**

*   **Wireframe/Mockup Description**:
    *   A dashboard layout with several key sections (widgets).
    *   **UI Components**:
        *   **Summary Widget**: Large display for `Total Portfolio Value` and `Total Profit/Loss` (color-coded green/red).
        *   **Cash Widget**: Displays `Available Cash`.
        *   **Holdings Table**:
            *   Columns: `Symbol`, `Quantity`, `Current Price`, `Total Value`.
            *   Each row represents a stock the user owns.
        *   **Transaction History Link**: A button or link to a separate page showing all transactions.
*   **Technical Notes:**
    *   The backend needs to calculate `Total Deposits` by summing all 'DEPOSIT' transactions.
    *   `Total Portfolio Value` = `Current Cash Balance` + Σ(`quantity_of_holding` * `get_share_price(symbol)`) for all holdings.
    *   `Total Profit/Loss` = `Total Portfolio Value` - `Total Deposits`.
    *   This page will make multiple calls to `get_share_price` for each holding, so performance and error handling are key. Consider a batch API call if possible.