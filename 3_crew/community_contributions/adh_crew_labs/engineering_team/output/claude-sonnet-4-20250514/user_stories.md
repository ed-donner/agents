# User Stories: Trading Simulation Platform

This document outlines the user stories for the initial development of the Trading Simulation Platform's account and portfolio management system. Each story is designed to be developer-ready, following INVEST principles and including comprehensive acceptance criteria, UI/UX specifications, and test scenarios.

## Epics

*   **EPIC-01: Account & Fund Management:** Covers all functionality related to user account creation, authentication, and cash management.
*   **EPIC-02: Portfolio & Trade Management:** Covers all functionality related to buying/selling shares, viewing portfolio status, and tracking performance.

---

## EPIC-01: Account & Fund Management

### **Story ID:** ACC-001
**Title:** User Account Creation

*   **User Story:** As a new visitor, I want to create a new account so that I can start using the trading simulation platform.
*   **Business Value:** Enables user acquisition, which is the foundation of the platform's user base.
*   **Priority:** High

**Acceptance Criteria:**
*   **Scenario 1 (Happy Path):**
    *   **Given** I am on the registration page
    *   **When** I enter a unique email, a valid password, and confirm the password
    *   **Then** my account is created, my initial cash balance is set to $0.00, and I am logged into the platform.
*   **Scenario 2 (Happy Path):**
    *   **Given** I am on the registration page
    *   **When** I successfully create an account
    *   **Then** a new user record is created in the database with my encrypted password.
*   **Scenario 3 (Error Case):**
    *   **Given** an account with the email "user@example.com" already exists
    *   **When** I try to register with the email "user@example.com"
    *   **Then** the system shows an error message "This email address is already registered." and my account is not created.
*   **Scenario 4 (Error Case):**
    *   **Given** I am on the registration page
    *   **When** I enter a password that does not match the confirmed password
    *   **Then** the system shows an error message "Passwords do not match." and my account is not created.
*   **Scenario 5 (Error Case):**
    *   **Given** I am on the registration page
    *   **When** I enter an invalid email format (e.g., "not-an-email")
    *   **Then** the system shows an error message "Please enter a valid email address."

**UI/UX Specs:**
*   **Wireframe/Mockup:** A wireframe is required for a standard registration form.
*   **Components:**
    *   Input field for "Email Address"
    *   Input field for "Password" (type="password")
    *   Input field for "Confirm Password" (type="password")
    *   "Create Account" button
    *   Links to "Login" and "Forgot Password" pages.
    *   Display areas for validation error messages next to each field.

**Test Scenarios:**
| Input Data (Email, Pass, Confirm Pass) | Expected Output | Test Case Type |
| :--- | :--- | :--- |
| `test@new.com`, `P@ssword1`, `P@ssword1` | Account created, logged in, balance is $0.00. | Happy Path |
| `user@example.com`, `P@ssword1`, `P@ssword1` | Error: "email...already registered." | Error Case |
| `test@new.com`, `P@ssword1`, `P@ssword2` | Error: "Passwords do not match." | Error Case |
| `invalid-email`, `P@ssword1`, `P@ssword1` | Error: "Please enter a valid email address." | Error Case |

**Definition of Ready (DoR) Checklist:**
*   [x] Story is clear, concise, and understood.
*   [x] Acceptance criteria are defined and testable.
*   [ ] Dependencies (e.g., database schema) are identified.
*   [x] UI/UX specs are defined.
*   [ ] Story is sized by the development team.
*   [x] Story has clear business value.

---

### **Story ID:** ACC-002
**Title:** Deposit Funds into Account

*   **User Story:** As a registered user, I want to deposit funds into my account so that I have the cash available to buy shares.
*   **Business Value:** Enables users to engage with the core trading simulation feature.
*   **Priority:** High

**Acceptance Criteria:**
*   **Scenario 1 (Happy Path):**
    *   **Given** I am a logged-in user with a cash balance of $1,000.00
    *   **When** I deposit $500.00
    *   **Then** my new cash balance is $1,500.00 and a "DEPOSIT" transaction of $500.00 is recorded in my transaction history.
*   **Scenario 2 (Happy Path):**
    *   **Given** I am a logged-in user with a cash balance of $0.00
    *   **When** I deposit $10,000.00
    *   **Then** my new cash balance is $10,000.00.
*   **Scenario 3 (Happy Path - Decimal values):**
    *   **Given** I am a logged-in user with a cash balance of $50.25
    *   **When** I deposit $100.50
    *   **Then** my new cash balance is $150.75.
*   **Scenario 4 (Error Case - Zero amount):**
    *   **Given** I am a logged-in user
    *   **When** I attempt to deposit $0.00
    *   **Then** the system shows an error message "Deposit amount must be greater than zero." and my balance does not change.
*   **Scenario 5 (Error Case - Negative amount):**
    *   **Given** I am a logged-in user
    *   **When** I attempt to deposit -$100.00
    *   **Then** the system shows an error message "Deposit amount must be a positive number." and my balance does not change.
*   **Scenario 6 (Error Case - Invalid input):**
    *   **Given** I am a logged-in user
    *   **When** I enter a non-numeric value like "one hundred" in the deposit amount field
    *   **Then** the system shows a validation error message "Please enter a valid number."

**UI/UX Specs:**
*   **Wireframe/Mockup:** A wireframe is required for a simple deposit modal/page.
*   **Components:**
    *   Display of "Current Cash Balance".
    *   Numeric input field for "Deposit Amount".
    *   "Deposit" button.
    *   Confirmation message on success (e.g., "Successfully deposited $500.00").
    *   Display area for validation errors.

**Test Scenarios:**
| Current Balance | Input Amount | Expected New Balance | Expected Output Message | Test Case Type |
| :--- | :--- | :--- | :--- | :--- |
| $1,000.00 | $500.00 | $1,500.00 | "Successfully deposited $500.00" | Happy Path |
| $0.00 | $10,000.00 | $10,000.00 | "Successfully deposited $10,000.00"| Happy Path |
| $100.00 | $0.00 | $100.00 | "Deposit amount must be greater than zero." | Error Case |
| $100.00 | -$50.00 | $100.00 | "Deposit amount must be a positive number."| Error Case |
| $100.00 | "abc" | $100.00 | "Please enter a valid number." | Error Case |

**Definition of Ready (DoR) Checklist:**
*   [x] Story is clear, concise, and understood.
*   [x] Acceptance criteria are defined and testable.
*   [ ] Dependencies (ACC-001, Transaction History Model) are identified.
*   [x] UI/UX specs are defined.
*   [ ] Story is sized by the development team.
*   [x] Story has clear business value.

---
### **Story ID:** ACC-003
**Title:** Withdraw Funds from Account
*   **User Story:** As a registered user, I want to withdraw available funds from my account so that I can realize my simulated profits.
*   **Business Value:** Completes the core cash management loop, allowing users to interact with their balance.
*   **Priority:** Medium
*   **(Details Omitted for Brevity - would follow the same structure as above, with key ACs focusing on preventing negative balances)**

---
## EPIC-02: Portfolio & Trade Management

### **Story ID:** PTM-001
**Title:** Buy Shares of a Stock

*   **User Story:** As a trader, I want to buy shares of a stock using my available cash so that I can build my investment portfolio.
*   **Business Value:** This is the primary engagement feature of the platform, allowing users to actively participate in the simulation.
*   **Priority:** High

**Acceptance Criteria:**
*   **Scenario 1 (Happy Path - Sufficient Funds):**
    *   **Given** I am a logged-in user with a cash balance of $10,000.00 and 0 shares of AAPL
    *   **And** the current price of AAPL is $150.00 per share
    *   **When** I buy 10 shares of AAPL
    *   **Then** my cash balance is reduced by $1,500.00 to $8,500.00
    *   **And** my portfolio shows I own 10 shares of AAPL
    *   **And** a "BUY" transaction for 10 shares of AAPL at $150.00 each is recorded.
*   **Scenario 2 (Happy Path - Exact Funds):**
    *   **Given** I am a logged-in user with a cash balance of $300.00
    *   **And** the current price of AAPL is $150.00 per share
    *   **When** I buy 2 shares of AAPL
    *   **Then** my cash balance becomes $0.00 and my portfolio shows 2 shares of AAPL.
*   **Scenario 3 (Happy Path - Adding to Existing Position):**
    *   **Given** I am a logged-in user with a cash balance of $10,000.00 and I already own 5 shares of GOOGL
    *   **And** the current price of GOOGL is $100.00 per share
    *   **When** I buy 10 more shares of GOOGL
    *   **Then** my cash balance is reduced by $1,000.00 to $9,000.00 and my portfolio shows I own a total of 15 shares of GOOGL.
*   **Scenario 4 (Error Case - Insufficient Funds):**
    *   **Given** I am a logged-in user with a cash balance of $500.00
    *   **And** the current price of TSLA is $200.00 per share
    *   **When** I attempt to buy 3 shares of TSLA (total cost $600.00)
    *   **Then** the transaction is blocked, my cash balance remains $500.00, and I see an error message "Insufficient funds to complete this transaction."
*   **Scenario 5 (Error Case - Invalid Symbol):**
    *   **Given** I am a logged-in user with a cash balance of $10,000.00
    *   **When** I attempt to buy 10 shares of "FAKESYMBOL"
    *   **Then** the transaction is blocked and I see an error message "Stock symbol 'FAKESYMBOL' not found."
*   **Scenario 6 (Error Case - Non-positive Quantity):**
    *   **Given** I am a logged-in user with a cash balance of $10,000.00
    *   **When** I attempt to buy 0 shares of AAPL
    *   **Then** the transaction is blocked and I see an error message "Quantity must be a positive number."
*   **Scenario 7 (Edge Case - Price Fluctuation):**
    *   **Given** I see the price of AAPL is $150.00
    *   **And** I have a cash balance of $151.00
    *   **When** I submit my order to buy 1 share, but the price has increased to $152.00 before the transaction is processed
    *   **Then** the transaction is blocked due to insufficient funds and a message is displayed: "The price has changed. Please try again."

**UI/UX Specs:**
*   **Wireframe/Mockup:** A wireframe is required for a "Trade" widget or page.
*   **Components:**
    *   Input field for "Stock Symbol" (e.g., AAPL, TSLA).
    *   Input field for "Quantity".
    *   Display area for "Current Market Price" (refreshes or is fetched on symbol entry).
    *   Display area for "Estimated Cost" (Price x Quantity).
    *   Display of "Available Cash".
    *   "Buy" button.
    *   Confirmation modal on successful purchase.
    *   Display area for validation/error messages.

**Technical Notes:**
*   The system must call the `get_share_price(symbol)` function to get the real-time price before executing the trade.
*   The test implementation of `get_share_price(symbol)` should return fixed values for AAPL, TSLA, and GOOGL to ensure test predictability.
*   All calculations involving currency should be handled with a high-precision data type (e.g., Decimal) to avoid floating-point errors.

**Test Scenarios:**
| Cash Balance | Symbol | Quantity | Price (`get_share_price`) | Expected Result | Test Case Type |
| :--- | :--- | :--- | :--- | :--- | :--- |
| $5,000 | AAPL | 10 | $150 | Success. New Balance: $3,500. Holdings: 10 AAPL. | Happy Path |
| $300 | TSLA | 1 | $200 | Success. New Balance: $100. Holdings: 1 TSLA. | Happy Path |
| $299 | AAPL | 2 | $150 | Error: "Insufficient funds..." | Error Case |
| $5,000 | FAKE | 5 | N/A | Error: "Stock symbol 'FAKE' not found." | Error Case |
| $5,000 | GOOGL | 0 | $100 | Error: "Quantity must be a positive number." | Error Case |

**Definition of Ready (DoR) Checklist:**
*   [x] Story is clear, concise, and understood.
*   [x] Acceptance criteria are defined and testable.
*   [x] Dependencies (ACC-002, `get_share_price` function) are identified.
*   [x] UI/UX specs are defined.
*   [ ] Story is sized by the development team.
*   [x] Story has clear business value.

---

### **Story ID:** PTM-002
**Title:** Sell Shares of a Stock
*   **User Story:** As a trader, I want to sell shares that I own so that I can liquidate my position and increase my cash balance.
*   **Business Value:** Allows users to complete the trading cycle and realize gains or losses.
*   **Priority:** High
*   **(Details Omitted for Brevity - would follow the same structure, with key ACs focusing on preventing users from selling shares they do not own or selling more shares than they own)**

---

### **Story ID:** PTM-003
**Title:** View Portfolio Holdings and Value

*   **User Story:** As a trader, I want to view a summary of all the shares I own and their current market value so that I can understand the composition and total value of my portfolio.
*   **Business Value:** Provides critical visibility for users to make informed trading decisions.
*   **Priority:** High

**Acceptance Criteria:**
*   **Scenario 1 (Happy Path - Multiple Holdings):**
    *   **Given** I am a logged-in user and I own 10 shares of AAPL and 5 shares of TSLA
    *   **And** my cash balance is $1,000.00
    *   **And** the current price of AAPL is $150.00 and TSLA is $200.00
    *   **When** I view my portfolio
    *   **Then** I see a list of my holdings:
        *   AAPL: 10 shares, Current Value: $1,500.00
        *   TSLA: 5 shares, Current Value: $1,000.00
    *   **And** I see my "Total Portfolio Value" is $3,500.00 (Holdings Value $2,500 + Cash $1,000).
*   **Scenario 2 (Happy Path - Single Holding):**
    *   **Given** I own 20 shares of GOOGL and have $500.00 cash
    *   **And** the current price of GOOGL is $100.00
    *   **When** I view my portfolio
    *   **Then** I see GOOGL: 20 shares, Current Value: $2,000.00
    *   **And** my "Total Portfolio Value" is $2,500.00.
*   **Scenario 3 (Edge Case - No Holdings):**
    *   **Given** I am a logged-in user with $10,000.00 cash and I own no shares
    *   **When** I view my portfolio
    *   **Then** I see a message "You do not own any shares."
    *   **And** my "Total Portfolio Value" is equal to my cash balance of $10,000.00.
*   **Scenario 4 (Edge Case - Share Price is Zero):**
    *   **Given** I own 100 shares of a stock "DELISTED"
    *   **And** the `get_share_price("DELISTED")` function returns $0.00
    *   **When** I view my portfolio
    *   **Then** I see DELISTED: 100 shares, Current Value: $0.00.
*   **Scenario 5 (UI Behavior - Real-time update):**
    *   **Given** my portfolio view is open
    *   **And** the price of AAPL changes from $150.00 to $155.00
    *   **When** the portfolio data is refreshed (automatically or manually)
    *   **Then** the "Current Value" for my AAPL holding and the "Total Portfolio Value" are updated to reflect the new price.

**UI/UX Specs:**
*   **Wireframe/Mockup:** A wireframe is required for a "Portfolio" dashboard/page.
*   **Components:**
    *   A summary section displaying:
        *   "Total Portfolio Value" (Market Value of Holdings + Cash)
        *   "Total Holdings Value"
        *   "Total Cash"
    *   A table of holdings with columns: "Symbol", "Quantity", "Current Price", "Current Value".
    *   A "Refresh" button or auto-refresh mechanism.

**Technical Notes:**
*   The page must call `get_share_price(symbol)` for each distinct stock symbol in the user's portfolio to calculate the current value.
*   This could result in multiple API calls; consider a batching mechanism or caching strategy if performance is a concern.

**Test Scenarios:**
| Holdings | Cash | Prices (AAPL, TSLA) | Expected Holdings Value | Expected Total Portfolio Value |
| :--- | :--- | :--- | :--- | :--- |
| 10 AAPL, 5 TSLA | $1,000 | $150, $200 | $2,500 | $3,500 |
| 0 shares | $5,000 | N/A | $0 | $5,000 |
| 20 AAPL | $0 | $150 | $3,000 | $3,000 |

**Definition of Ready (DoR) Checklist:**
*   [x] Story is clear, concise, and understood.
*   [x] Acceptance criteria are defined and testable.
*   [x] Dependencies (`get_share_price` function, user holdings data) are identified.
*   [x] UI/UX specs are defined.
*   [ ] Story is sized by the development team.
*   [x] Story has clear business value.

---

### **Story ID:** PTM-004
**Title:** View Portfolio Profit & Loss
*   **User Story:** As a trader, I want to see my total profit or loss since I started so that I can quickly assess my overall performance.
*   **Business Value:** Provides a key performance indicator that is highly valuable and engaging for users.
*   **Priority:** Medium
*   **(Details Omitted for Brevity - would follow the same structure, with key ACs focusing on the calculation: Total Portfolio Value - Total Deposits + Total Withdrawals)**

---

### **Story ID:** PTM-005
**Title:** View Transaction History
*   **User Story:** As a trader, I want to see a chronological list of all my transactions so that I can review my trading activity.
*   **Business Value:** Provides transparency and allows users to audit their own actions on the platform.
*   **Priority:** Medium
*   **(Details Omitted for Brevity - would follow the same structure, with key ACs focusing on displaying a list of all deposits, withdrawals, buys, and sells with relevant details like date, type, amount/quantity, and price)**