```markdown
# Product User Stories: Trading Simulation Platform

This document outlines the user stories for the core features of the trading simulation platform, broken down by epic. Each story is designed to be developer-ready, following INVEST principles and including comprehensive acceptance criteria, technical notes, and UI/UX specifications.

---

## Epic 1: Core Account Management

### **Story ID:** ACC-002
**Title:** Deposit Funds into Trading Account
**User Story:** As a registered user, I want to deposit funds into my account, so that I can have the capital to purchase shares.
**Business Value:** Core functionality. Enables users to engage with the primary trading features. Without this, the simulation is unusable.
**Priority:** High

#### Acceptance Criteria

1.  **Given** I am a logged-in user with a current cash balance of $10,000
    **When** I navigate to the "Deposit Funds" page and enter an amount of $5,000
    **Then** my cash balance should be updated to $15,000
    **And** a "DEPOSIT" transaction record for $5,000 should be created in my transaction history.

2.  **Given** I am a logged-in user with a new account and a cash balance of $0
    **When** I make an initial deposit of $10,000
    **Then** my cash balance should become $10,000
    **And** this amount should be recorded as my initial principal (total deposits) for profit/loss calculations.

3.  **Given** I am a logged-in user with a cash balance of $500
    **When** I deposit an amount of $150.75
    **Then** my cash balance should be updated to $650.75.

4.  **Given** I am a logged-in user on the "Deposit Funds" page
    **When** I attempt to deposit an amount of $0
    **Then** I should see an error message "Deposit amount must be greater than zero"
    **And** my balance should remain unchanged.

5.  **Given** I am a logged-in user on the "Deposit Funds" page
    **When** I attempt to deposit an amount of -$100
    **Then** I should see an error message "Deposit amount cannot be negative"
    **And** my balance should remain unchanged.

6.  **Given** I am a logged-in user on the "Deposit Funds" page
    **When** I enter "abc" as the deposit amount
    **Then** I should see a validation error "Please enter a valid number"
    **And** the deposit button should be disabled until the input is valid.

7.  **Given** I am on the deposit page
    **When** I successfully complete a deposit
    **Then** I should see a success confirmation message like "Successfully deposited $5,000. Your new balance is $15,000."

#### UI/UX Specs

*   **Wireframe/Mockup Description:**
    *   A simple form with a single input field labeled "Deposit Amount ($)".
    *   A primary button labeled "Deposit".
    *   A text element displaying the "Current Cash Balance: $X,XXX.XX".
    *   Space for displaying success or error messages below the button.
*   **Design Components:**
    *   Standard numeric input field.
    *   Standard primary button.
    *   Alert/Toast component for feedback messages.
*   **Accessibility:**
    *   The input field must have a proper `<label>`.
    *   Error messages should be associated with the input field using `aria-describedby`.
    *   The form should be navigable and submittable using only a keyboard.

#### Technical Notes
*   An API endpoint like `POST /api/v1/accounts/{accountId}/deposit` will be needed.
*   Request body should contain `{"amount": 5000.00}`.
*   The transaction should be recorded in a `transactions` table with columns like `id`, `user_id`, `type` ('DEPOSIT', 'WITHDRAW', 'BUY', 'SELL'), `amount`, `symbol`, `quantity`, `price_per_share`, `timestamp`. For a deposit, `symbol`, `quantity`, `price_per_share` would be NULL.
*   The `accounts` table needs a `cash_balance` column and a `total_deposits` column (use a `DECIMAL` type for financial precision).

#### Test Scenarios
| Input Amount | Current Balance | Expected New Balance | Expected Outcome/Message |
|--------------|-----------------|----------------------|--------------------------|
| 5000         | 10000           | 15000                | Success                  |
| 150.75       | 500             | 650.75               | Success                  |
| 0            | 1000            | 1000                 | Error: "must be > 0"     |
| -100         | 1000            | 1000                 | Error: "cannot be negative"|
| "abc"        | 1000            | 1000                 | Error: "valid number"    |

---

## Epic 2: Trading Functionality

### **Story ID:** TRD-001
**Title:** Purchase Shares with Available Funds
**User Story:** As a user with a funded account, I want to buy a specific quantity of shares for a given symbol, so that I can build my investment portfolio.
**Business Value:** The primary action of the simulation. Allows users to actively engage with the market and their portfolio.
**Priority:** High

#### Acceptance Criteria

1.  **Given** I am a logged-in user with a cash balance of $10,000
    **And** the current price of 'AAPL' is $150
    **When** I submit an order to buy 10 shares of 'AAPL'
    **Then** my cash balance should be reduced by $1,500 (10 * $150), becoming $8,500
    **And** my holdings should show I own 10 shares of 'AAPL'
    **And** a "BUY" transaction record for 10 shares of 'AAPL' at $150/share should be created.

2.  **Given** I am a logged-in user with a cash balance of $10,000 and I own 5 shares of 'TSLA'
    **And** the current price of 'TSLA' is $200
    **When** I submit an order to buy 10 more shares of 'TSLA'
    **Then** my cash balance should be reduced by $2,000 (10 * $200), becoming $8,000
    **And** my holdings should show I own 15 shares of 'TSLA'.

3.  **Given** I am a logged-in user with a cash balance of $3,000
    **And** the current price of 'GOOGL' is $100
    **When** I submit an order to buy 30 shares of 'GOOGL'
    **Then** my cash balance should be reduced to $0
    **And** my holdings should show I own 30 shares of 'GOOGL'.

4.  **Given** I am a logged-in user with a cash balance of $1,000
    **And** the current price of 'AAPL' is $150
    **When** I attempt to buy 10 shares of 'AAPL' (total cost $1,500)
    **Then** I should see an error message "Insufficient funds. You need $1,500 but only have $1,000."
    **And** my cash balance and holdings should remain unchanged.

5.  **Given** I am a logged-in user with sufficient funds
    **When** I attempt to buy shares of an invalid symbol 'XYZ'
    **Then** I should see an error message "Invalid symbol 'XYZ'."
    **And** my cash balance and holdings should remain unchanged.

6.  **Given** I am a logged-in user
    **When** I attempt to buy 0 shares of 'AAPL'
    **Then** I should see an error message "Quantity must be a positive number."
    **And** no transaction should be created.

7.  **Given** the market is volatile
    **When** I view the price of 'AAPL' as $150 and submit a buy order
    **Then** the system must use the price fetched at the moment of transaction execution (`get_share_price('AAPL')`) to calculate the final cost
    **And** the transaction should only proceed if I have sufficient funds for the executed price.

#### UI/UX Specs

*   **Wireframe/Mockup Description:**
    *   A trading form with "Symbol" (text input) and "Quantity" (numeric input).
    *   A primary button labeled "Buy".
    *   A section displaying dynamic information: "Symbol Price: $XXX.XX", "Estimated Cost: $Y,YYY.YY", "Cash Available: $Z,ZZZ.ZZ".
    *   The "Estimated Cost" should update as the user types the quantity.
*   **Design Components:**
    *   Text input with autocomplete for known symbols (AAPL, TSLA, GOOGL).
    *   Numeric input field (integer only).
    *   Primary button.
    *   Alert/Toast component for feedback.
*   **Accessibility:**
    *   All form fields must have proper `<label>`s.
    *   Dynamic updates (like estimated cost) should be announced by a screen reader using `aria-live` regions.

#### Technical Notes
*   An API endpoint like `POST /api/v1/accounts/{accountId}/trades` will be needed.
*   Request body: `{"symbol": "AAPL", "quantity": 10, "side": "BUY"}`.
*   Backend logic must be wrapped in a database transaction to ensure atomicity (debiting cash and crediting shares).
*   The `holdings` table should have `user_id`, `symbol`, `quantity` and use an `UPSERT` (or `INSERT ... ON CONFLICT UPDATE`) operation to add or update holdings.
*   The backend must call the provided `get_share_price(symbol)` function to determine the transaction cost.

#### Test Scenarios
| Cash Balance | Symbol | Quantity | Price (`get_share_price`) | Expected Outcome | New Cash Balance | New Holdings |
|--------------|--------|----------|---------------------------|------------------|------------------|--------------|
| $10,000      | AAPL   | 10       | $150                      | Success          | $8,500           | 10 AAPL      |
| $1,000       | AAPL   | 10       | $150                      | Insufficient funds| $1,000           | Unchanged    |
| $5,000       | XYZ    | 20       | N/A                       | Invalid symbol   | $5,000           | Unchanged    |
| $5,000       | TSLA   | 0        | $200                      | Invalid quantity | $5,000           | Unchanged    |

---

## Epic 3: Portfolio & Reporting

### **Story ID:** RPT-001
**Title:** View Portfolio Dashboard Summary
**User Story:** As a user, I want to view a dashboard summarizing my portfolio, so that I can quickly understand my overall financial position.
**Business Value:** Provides a high-level, at-a-glance view of performance, which is a primary user need for any investment platform. Encourages user engagement.
**Priority:** High

#### Acceptance Criteria

1.  **Given** I am a logged-in user with a total deposit of $10,000
    **And** I have a current cash balance of $5,000
    **And** I own 10 shares of 'AAPL' (current price $150) and 5 shares of 'TSLA' (current price $200)
    **When** I navigate to my dashboard
    **Then** I should see my "Total Portfolio Value" calculated as $7,500 ($5,000 cash + 10*$150 + 5*$200)
    **And** I should see my "Total Profit/Loss" displayed as -$2,500 ($7,500 current value - $10,000 total deposit).

2.  **Given** I am a logged-in user with a total deposit of $20,000
    **And** I have a current cash balance of $1,000
    **And** I own 50 shares of 'GOOGL' (current price $100)
    **When** I navigate to my dashboard
    **Then** I should see my "Total Portfolio Value" calculated as $6,000 ($1,000 cash + 50*$100)
    **And** I should see my "Total Profit/Loss" displayed as -$14,000 ($6,000 current value - $20,000 total deposit).

3.  **Given** I am a new user who has just deposited $5,000 and has no holdings
    **When** I navigate to my dashboard
    **Then** I should see my "Total Portfolio Value" as $5,000
    **And** I should see my "Total Profit/Loss" as $0
    **And** my "Current Holdings" section should be empty or show a message like "You do not own any shares yet."

4.  **Given** I own 10 shares of 'OLDCO' but the `get_share_price('OLDCO')` function now fails
    **And** I have $1,000 cash and 10 shares of 'AAPL' (price $150)
    **When** I view my dashboard
    **Then** the "Total Portfolio Value" should be calculated as $2,500 ($1,000 cash + 10*$150), ignoring 'OLDCO'
    **And** there should be a clear warning message next to the 'OLDCO' holding stating its price is unavailable.

5.  **Given** I am on the dashboard
    **When** I execute a trade (buy or sell) on a different page
    **Then** upon returning to the dashboard, the data (Cash Balance, Portfolio Value, P/L) must be refreshed to reflect the latest state.

#### UI/UX Specs

*   **Wireframe/Mockup Description:**
    *   A header section with large "Key Performance Indicators" (KPIs):
        *   **Total Portfolio Value:** $XX,XXX.XX
        *   **Total Profit/Loss:** +$Y,YYY.YY (colored green) or -$Z,ZZZ.ZZ (colored red)
        *   **Cash Balance:** $A,AAA.AA
    *   A section below titled "Current Holdings" showing a summary list.
*   **Design Components:**
    *   KPI cards for summary figures.
    *   Use of color (green for profit, red for loss).
*   **Accessibility:**
    *   Do not rely on color alone to indicate profit/loss. Use icons (e.g., up/down arrows) or screen-reader-friendly text like `aria-label="Profit of $Y,YYY.YY"`.

#### Technical Notes
*   An API endpoint like `GET /api/v1/accounts/{accountId}/dashboard` will be needed.
*   The backend logic will need to:
    1.  Fetch the user's `cash_balance` and `total_deposits` from the `accounts` table.
    2.  Fetch all of the user's records from the `holdings` table.
    3.  Iterate through each holding, calling `get_share_price(symbol)` for each.
    4.  Sum the value of all holdings and add it to the cash balance to get `total_portfolio_value`.
    5.  Calculate `profit_loss = total_portfolio_value - total_deposits`.
    6.  The endpoint should handle failures from `get_share_price` gracefully.

#### Test Scenarios
| Cash Balance | Total Deposits | Holdings                         | Current Prices                          | Expected Portfolio Value | Expected P/L |
|--------------|----------------|----------------------------------|-----------------------------------------|--------------------------|--------------|
| $5,000       | $10,000        | 10 AAPL, 5 TSLA                  | AAPL=$150, TSLA=$200                    | $7,500                   | -$2,500      |
| $1,000       | $20,000        | 50 GOOGL                         | GOOGL=$100                              | $6,000                   | -$14,000     |
| $5,000       | $5,000         | None                             | N/A                                     | $5,000                   | $0           |
| $0           | $10,000        | 100 AAPL                         | AAPL=$100                               | $10,000                  | $0           |

```