Thought: The user wants me to generate a complete, executable TypeScript Playwright test script based on the provided test scenarios and DOM structure.

I need to cover three main features: Account Creation (ACC-001), Fund Deposit (ACC-002), and Stock Trading/Portfolio Status (PTM-001, PTM-003).

The base URL is `http://127.0.0.1:7860`. I must use absolute URLs for `page.goto()`.

I will define locators using the unique `id` attributes provided by `dom_scan_agent`.

**Locators Mapping:**
1.  **Email Input (component-6):** `//div[@id='component-6']//textarea[@data-testid='textbox']` (or simply `page.locator('#component-6 textarea')`)
2.  **Password Input (component-7):** `page.locator('#component-7 input[data-testid="password"]')`
3.  **Confirm Password Input (component-8):** `page.locator('#component-8 input[data-testid="password"]')`
4.  **Create Account Button (component-9):** `page.locator('#component-9')`
5.  **Messages Display (component-28):** `page.locator('#component-28 textarea')`
6.  **Cash Balance Display (component-29):** `page.locator('#component-29 textarea')`
7.  **Holdings Display (component-30):** `page.locator('#component-30 textarea')`
8.  **Portfolio Summary Display (component-31):** `page.locator('#component-31 textarea')`
9.  **Deposit Amount Input (component-11):** `page.locator('#component-11 input[aria-label="Deposit Amount"]')`
10. **Deposit Button (component-12):** `page.locator('#component-12')`
11. **Stock Symbol Input (component-17):** `page.locator('#component-17 textarea')`
12. **Quantity Input (component-18):** `page.locator('#component-18 input[aria-label="Quantity"]')`
13. **Buy Shares Button (component-21):** `page.locator('#component-21')`
14. **Refresh Transactions Button (component-33):** `page.locator('#component-33')`
15. **Recent Transactions Display (component-34):** `page.locator('#component-34 textarea')`

Since this is a single-page Gradio app, I must assume that interactions are stateful. To handle the different test scenarios (especially those requiring specific initial states like existing user, or specific cash balances), I will implement setup/teardown steps (like an initial login or specific deposits) within the tests, or rely on the application's behavior to reset (which is typical for simple demos like this). For robustness, I'll attempt a fresh registration for the positive case.

### Implementation Plan:

1.  **Setup:** Define `test` block, base URL, and selectors.
2.  **ACC-REG-POS-001 (Successful Registration):** Register a new user and check initial state ($0.00 balance).
3.  **ACC-REG-NEG-002 (Negative Scenarios):** Test validation rules (existing email, password mismatch, invalid email format).
4.  **ACC-DEP-POS-001 (Successful Deposit):** Register a user, then deposit funds with decimals, verifying balance update and transaction record.
5.  **ACC-DEP-NEG-002 (Negative Deposit):** Test zero, negative, and text inputs for deposit.
6.  **PTM-BUY-POS-001 (Successful Buy):** Register/Deposit funds, execute a trade, check balance reduction and holdings update.
7.  **PTM-BUY-NEG-002 (Negative Buy):** Test insufficient funds, zero quantity, and fake symbol.
8.  **PTM-PORT-POS-001 (Portfolio Calculation):** Simulate a portfolio state (by performing trades), then verify summary calculations.
9.  **PTM-PORT-POS-003 (Refresh):** Simulate a state and refresh to check recalculation (This requires simulating price change, which might not be possible purely through UI actions unless the app uses dynamic pricing upon refresh. I will check if the app updates *something* upon refresh).

I will use helper functions for common actions like registration and setting the balance (by making deposits) to ensure test isolation and clarity. Since I don't control the backend, I'll use unique emails for registration to avoid conflicts where possible.

---
*Self-Correction on Gradio Locators:* Gradio elements often use `label` text alongside the `id` component. I will use the `id` locator combined with the `textarea` or `input` tag for precision.

**Helper Function for Registration:**

```typescript
async function registerUser(page: Page, email: string, password: string) {
    const emailInput = page.locator('#component-6 textarea');
    const passwordInput = page.locator('#component-7 input[data-testid="password"]');
    const confirmPasswordInput = page.locator('#component-8 input[data-testid="password"]');
    const createAccountButton = page.locator('#component-9');
    const messageDisplay = page.locator('#component-28 textarea');

    await emailInput.fill(email);
    await passwordInput.fill(password);
    await confirmPasswordInput.fill(password);
    await createAccountButton.click();
    await expect(messageDisplay).toHaveText(/Account created successfully/);
}
```

Now, construct the full test file. I will use a class wrapper or plain fixture-based approach. Since the requirements don't mandate a Page Object Model (POM), I'll stick to clear selectors within the test file itself for simplicity and direct traceability.

I will use dynamic unique emails for positive registration tests to guarantee the "unique" precondition, e.g., `user_${Date.now()}@test.com`.

```typescript
import { test, expect, Page } from '@playwright/test';

const BASE_URL = 'http://127.0.0.1:7860';

// --- Locators Map ---
const LOCATORS = {
    // Account Creation
    emailInput: (page: Page) => page.locator('#component-6 textarea'),
    passwordInput: (page: Page) => page.locator('#component-7 input[data-testid="password"]'),
    confirmPasswordInput: (page: Page) => page.locator('#component-8 input[data-testid="password"]'),
    createAccountButton: (page: Page) => page.locator('#component-9'),
    
    // Funds & Status
    cashBalanceDisplay: (page: Page) => page.locator('#component-29 textarea'),
    messagesDisplay: (page: Page) => page.locator('#component-28 textarea'),
    depositAmountInput: (page: Page) => page.locator('#component-11 input[aria-label="Deposit Amount"]'),
    depositButton: (page: Page) => page.locator('#component-12'),
    recentTransactionsDisplay: (page: Page) => page.locator('#component-34 textarea'),
    refreshButton: (page: Page) => page.locator('#component-33'),
    holdingsDisplay: (page: Page) => page.locator('#component-30 textarea'),
    portfolioSummaryDisplay: (page: Page) => page.locator('#component-31 textarea'),

    // Trading
    stockSymbolInput: (page: Page) => page.locator('#component-17 textarea'),
    quantityInput: (page: Page) => page.locator('#component-18 input[aria-label="Quantity"]'),
    buySharesButton: (page: Page) => page.locator('#component-21'),
};

// --- Helper Functions ---

/** Registers a new user and asserts success. Returns a unique email. */
async function setupNewUser(page: Page, password = 'SecurePassword123') {
    const uniqueEmail = `user_${Date.now()}@test.com`;
    await LOCATORS.emailInput(page).fill(uniqueEmail);
    await LOCATORS.passwordInput(page).fill(password);
    await LOCATORS.confirmPasswordInput(page).fill(password);
    await LOCATORS.createAccountButton(page).click();
    
    await expect(LOCATORS.messagesDisplay(page)).toContainText('Account created successfully');
    await expect(LOCATORS.cashBalanceDisplay(page)).toHaveText('$0.00'); // Initial state check
    
    return uniqueEmail;
}

/** Deposits a specific amount and asserts success and new balance. */
async function depositFunds(page: Page, amount: string, expectedBalance: string) {
    await LOCATORS.depositAmountInput(page).fill(amount);
    await LOCATORS.depositButton(page).click();
    
    await expect(LOCATORS.messagesDisplay(page)).toContainText(`Deposit of $${amount} successful.`);
    await expect(LOCATORS.cashBalanceDisplay(page)).toHaveText(expectedBalance);
}

// --- Test Suite ---

test.describe('Feature: User Account Creation (ACC-001)', () => {
    
    test.beforeEach(async ({ page }) => {
        await page.goto(BASE_URL);
    });

    test('ACC-REG-POS-001: Successful Account Registration and Initial State Check', async ({ page }) => {
        // 1. GIVEN the user inputs a unique Email
        const testEmail = `valid_new_user_${Date.now()}@test.com`;
        await LOCATORS.emailInput(page).fill(testEmail);
        
        // 2. AND the user inputs a secure Password
        const password = 'StrongPassword123';
        await LOCATORS.passwordInput(page).fill(password);
        
        // 3. AND the user confirms the same Password
        await LOCATORS.confirmPasswordInput(page).fill(password);
        
        // 4. WHEN the user clicks the "Create Account" Button
        await LOCATORS.createAccountButton(page).click();
        
        // 5. THEN the Messages Display shows a success message
        await expect(LOCATORS.messagesDisplay(page)).toContainText('Account created successfully. User logged in.');
        
        // 6. AND the Cash Balance Display shows the initial balance as "$0.00"
        await expect(LOCATORS.cashBalanceDisplay(page)).toHaveText('$0.00');
    });

    // Setup: Register a known user for conflict testing (ACC-002a)
    test.beforeAll(async ({ page }) => {
        await page.goto(BASE_URL);
        await LOCATORS.emailInput(page).fill('existing@test.com');
        await LOCATORS.passwordInput(page).fill('Pass123');
        await LOCATORS.confirmPasswordInput(page).fill('Pass123');
        await LOCATORS.createAccountButton(page).click();
        // Wait for creation message, then proceed (assuming a cleanup/reset occurs between test files)
        await expect(LOCATORS.messagesDisplay(page)).toContainText('Account created successfully'); 
    });


    test.describe('ACC-REG-NEG-002: Negative Account Creation Scenarios (Validation)', () => {
        
        const negativeTestCases = [
            { email: 'existing@test.com', pass: 'Pass123', confirm: 'Pass123', expectedError: 'This email address is already registered.', name: 'ACC-002a: Existing Email' },
            { email: 'new@test.com', pass: 'Secret1', confirm: 'Different1', expectedError: 'Passwords do not match.', name: 'ACC-002b: Password Mismatch' },
            { email: 'invalid-email', pass: 'Pass123', confirm: 'Pass123', expectedError: 'Please enter a valid email address.', name: 'ACC-002c: Invalid Format (missing domain)' },
            { email: 'missing.com', pass: 'Pass123', confirm: 'Pass123', expectedError: 'Please enter a valid email address.', name: 'ACC-002d: Invalid Format (missing username)' },
        ];

        for (const { email, pass, confirm, expectedError, name } of negativeTestCases) {
            test(`${name}`, async ({ page }) => {
                await LOCATORS.emailInput(page).fill(email);
                await LOCATORS.passwordInput(page).fill(pass);
                await LOCATORS.confirmPasswordInput(page).fill(confirm);
                
                await LOCATORS.createAccountButton(page).click();
                
                // THEN the Messages Display shows the error message
                await expect(LOCATORS.messagesDisplay(page)).toContainText(expectedError);
                
                // AND the user remains logged out (Cash Balance unchanged/still showing old state or logged out state, which is implicitly handled by the error)
            });
        }
    });
});

test.describe('Feature: Fund Deposit Management (ACC-002)', () => {
    
    test.beforeEach(async ({ page }) => {
        await page.goto(BASE_URL);
        // Precondition 1: User is logged in.
        await setupNewUser(page);
    });

    test('ACC-DEP-POS-001: Successful Fund Deposit with Decimal Precision', async ({ page }) => {
        // Precondition: Set initial balance to $50.25 (by making a deposit)
        await depositFunds(page, '50.25', '$50.25');
        
        // 1. GIVEN the current cash balance is $50.25 (verified in setup)
        
        // 2. WHEN the user enters "100.50" into the Deposit Amount Input
        const depositAmount = '100.50';
        await LOCATORS.depositAmountInput(page).fill(depositAmount);
        
        // 3. AND the user clicks the "Deposit" Button
        await LOCATORS.depositButton(page).click();
        
        // 4. THEN the Messages Display shows a success message
        await expect(LOCATORS.messagesDisplay(page)).toContainText(`Deposit of $${depositAmount} successful.`);
        
        // 5. AND the Cash Balance Display updates to show "$150.75" (50.25 + 100.50)
        await expect(LOCATORS.cashBalanceDisplay(page)).toHaveText('$150.75');
        
        // 6. AND the Recent Transactions Display includes a new entry
        await expect(LOCATORS.recentTransactionsDisplay(page)).toContainText(/DEPOSIT.*100\.50/);
    });

    test.describe('ACC-DEP-NEG-002: Negative Deposit Validation', () => {
        const initialBalance = '$1,000.00';
        
        test.beforeEach(async ({ page }) => {
            // Set initial balance to $1,000.00
            await depositFunds(page, '1000', initialBalance);
        });

        const negativeDepositCases = [
            { input: '0.00', expectedError: 'Deposit amount must be greater than zero.', name: 'ACC-002a: Zero Deposit' },
            { input: '-10.00', expectedError: 'Deposit amount must be a positive number.', name: 'ACC-002b: Negative Deposit' },
            { input: 'Text', expectedError: 'Please enter a valid number.', name: 'ACC-002c: Invalid Text Input' },
            // Note: Gradio input[type=number] usually prevents non-numeric input, but we test the backend validation for safety.
            { input: '', expectedError: 'Deposit amount must be greater than zero.', name: 'ACC-002d: Empty Input' },
        ];

        for (const { input, expectedError, name } of negativeDepositCases) {
            test(`${name}`, async ({ page }) => {
                await LOCATORS.depositAmountInput(page).fill(input);
                await LOCATORS.depositButton(page).click();
                
                // THEN the Messages Display shows the error message
                await expect(LOCATORS.messagesDisplay(page)).toContainText(expectedError);
                
                // AND the Cash Balance Display remains unchanged
                await expect(LOCATORS.cashBalanceDisplay(page)).toHaveText(initialBalance);
            });
        }
    });
});


test.describe('Feature: Stock Trading (PTM-001) & Portfolio (PTM-003)', () => {
    
    test.beforeEach(async ({ page }) => {
        await page.goto(BASE_URL);
        // Setup: Register a user and deposit a large enough base amount ($5000)
        await setupNewUser(page);
        await depositFunds(page, '5000.00', '$5,000.00');
    });

    test('PTM-BUY-POS-001: Successful Stock Purchase (AAPL)', async ({ page }) => {
        // Preconditions: Cash Balance $5,000.00, AAPL price simulated at $150.00
        
        // 1. WHEN the user enters "AAPL" into the Stock Symbol Input
        await LOCATORS.stockSymbolInput(page).fill('AAPL');
        
        // 2. AND the user enters "10" into the Quantity Input
        await LOCATORS.quantityInput(page).fill('10');
        
        // 3. AND the user clicks the "Buy Shares" Button
        await LOCATORS.buySharesButton(page).click();
        
        // Assume price is $150.00 -> Cost $1500.00
        
        // 4. THEN the Messages Display shows a success message
        await expect(LOCATORS.messagesDisplay(page)).toContainText(/Bought 10 shares of AAPL for \$1,500\.00/);
        
        // 5. AND the Cash Balance Display updates to show "$3,500.00" (5000 - 1500)
        await expect(LOCATORS.cashBalanceDisplay(page)).toHaveText('$3,500.00');
        
        // 6. AND the Holdings Display shows the new position
        await expect(LOCATORS.holdingsDisplay(page)).toContainText('AAPL: 10 shares');
    });

    test.describe('PTM-BUY-NEG-002: Negative Trade Scenarios', () => {
        
        test.beforeEach(async ({ page }) => {
            // Set cash balance to $299.00 (re-deposit to reset from $5000 initial setup)
            // Assuming the system is idempotent/resets state based on inputs.
            // A quick way to "set" balance might be registering a new user, but since we rely on the same page instance, we'll try to explicitly set it to 299.
            
            // To achieve 299.00, we must clear the existing 5000, or assume a fresh login handles the reset. 
            // Since Gradio state persists, let's assume we re-register and deposit 299.
            await setupNewUser(page, 'resetpass'); // Force a fresh state by logging in a new user
            await depositFunds(page, '299.00', '$299.00');
        });
        
        const negativeTradeCases = [
            { symbol: 'AAPL', quantity: '2', expectedError: 'Insufficient funds to complete this transaction.', name: 'PTM-002a: Insufficient Funds (Cost $300 > $299)' },
            { symbol: 'GOOGL', quantity: '0', expectedError: 'Quantity must be a positive number.', name: 'PTM-002b: Zero Quantity' },
            { symbol: 'FAKE', quantity: '5', expectedError: /Stock symbol 'FAKE' not found./, name: 'PTM-002c: Invalid Symbol' },
            { symbol: 'TSLA', quantity: '-1', expectedError: 'Quantity must be a positive number.', name: 'PTM-002d: Negative Quantity' },
        ];
        
        for (const { symbol, quantity, expectedError, name } of negativeTradeCases) {
            test(`${name}`, async ({ page }) => {
                await LOCATORS.stockSymbolInput(page).fill(symbol);
                await LOCATORS.quantityInput(page).fill(quantity);
                await LOCATORS.buySharesButton(page).click();
                
                // THEN the Messages Display shows the error message
                await expect(LOCATORS.messagesDisplay(page)).toContainText(expectedError);
                
                // AND the Cash Balance Display remains unchanged at "$299.00"
                await expect(LOCATORS.cashBalanceDisplay(page)).toHaveText('$299.00');
                
                // AND the Holdings Display remains unchanged (likely showing "You do not own any shares." if a new user)
                // We assert it doesn't contain a specific symbol (except for FAKE, where it shouldn't try to trade anyway)
                if (symbol !== 'FAKE') {
                    await expect(LOCATORS.holdingsDisplay(page)).not.toContainText(symbol);
                }
            });
        }
    });

    test('PTM-BUY-NEG-003: Edge Case - Handling Price Slippage During Execution', async ({ page }) => {
        // Preconditions: Cash Balance is exactly $151.00. (TSLA execution price changes from $150 to $152)
        
        // Reset and set cash balance to $151.00
        await setupNewUser(page, 'slippagepass'); 
        await depositFunds(page, '151.00', '$151.00');

        // GIVEN the user is prepared to buy 1 share of TSLA (symbol input is TSLA, qty 1)
        await LOCATORS.stockSymbolInput(page).fill('TSLA');
        await LOCATORS.quantityInput(page).fill('1');
        
        // WHEN the user clicks the "Buy Shares" Button (This action triggers the simulated price spike)
        await LOCATORS.buySharesButton(page).click();
        
        // THEN the Messages Display shows the error message: "The price has changed. Please try again."
        // We rely on the application backend simulating this price change failure.
        await expect(LOCATORS.messagesDisplay(page)).toContainText('The price has changed. Please try again.');
        
        // AND the Cash Balance Display remains "$151.00"
        await expect(LOCATORS.cashBalanceDisplay(page)).toHaveText('$151.00');
    });
    
    test.describe('Feature: Portfolio Status and Value Calculation (PTM-003)', () => {

        test('PTM-PORT-POS-001: Portfolio Calculation with Multiple Holdings and Cash', async ({ page }) => {
            // Setup: Register new user (done in global beforeEach)
            // Setup: Deposit 5000.00 (done in global beforeEach)
            
            // Execute Trades to meet Preconditions:
            // 10 shares of AAPL (Price $150.00 -> $1,500.00 cost. Balance: $3,500.00)
            await LOCATORS.stockSymbolInput(page).fill('AAPL');
            await LOCATORS.quantityInput(page).fill('10');
            await LOCATORS.buySharesButton(page).click();
            await expect(LOCATORS.messagesDisplay(page)).toContainText('Bought 10 shares of AAPL');
            
            // 5 shares of TSLA (Price $200.00 -> $1,000.00 cost. Balance: $2,500.00)
            await LOCATORS.stockSymbolInput(page).fill('TSLA');
            await LOCATORS.quantityInput(page).fill('5');
            await LOCATORS.buySharesButton(page).click();
            await expect(LOCATORS.messagesDisplay(page)).toContainText('Bought 5 shares of TSLA');
            
            // Deposit funds back to $1,000.00 cash balance
            // Current Balance: $2,500.00. Need to deposit -1500 + 1000 = -500? No. 
            // Wait, initial deposit was $5000. Final cost was $2500. Remaining cash is $2,500.00.
            // To get to $1,000.00 cash balance, we must withdraw $1,500.
            // Since I don't have a reliable withdraw implementation defined in the test plan, I will assume the initial cash balance *was* $3,500 + 1000 cash needed = 4500.
            
            // Let's reset and buy exactly what we need, aiming for $1000 cash remaining.
            // Total portfolio value needed: $2,500 (holdings) + $1,000 (cash) = $3,500 initial cash.
            
            await setupNewUser(page, 'portfolioPass'); // Reset state
            await depositFunds(page, '3500.00', '$3,500.00'); 

            // Buy AAPL (10 * 150 = $1500)
            await LOCATORS.stockSymbolInput(page).fill('AAPL');
            await LOCATORS.quantityInput(page).fill('10');
            await LOCATORS.buySharesButton(page).click(); // Cash: $2,000.00
            
            // Buy TSLA (5 * 200 = $1000)
            await LOCATORS.stockSymbolInput(page).fill('TSLA');
            await LOCATORS.quantityInput(page).fill('5');
            await LOCATORS.buySharesButton(page).click(); // Cash: $1,000.00 (Target achieved)
            
            // Refresh to ensure portfolio calculations update (Step 2: When system calculates)
            await LOCATORS.refreshButton(page).click();
            
            // 3. THEN the Holdings Display accurately lists the holdings and their current value
            const holdingsText = await LOCATORS.holdingsDisplay(page).inputValue();
            expect(holdingsText).toContain('AAPL: 10 shares');
            expect(holdingsText).toContain('TSLA: 5 shares');
            
            // 4. AND the Portfolio Summary Display shows correct values
            const summaryText = await LOCATORS.portfolioSummaryDisplay(page).inputValue();
            
            // Cash Balance | $1,000.00
            expect(summaryText).toContain('Cash Balance | $1,000.00');
            // Total Holdings Value | $2,500.00
            expect(summaryText).toContain('Total Holdings Value | $2,500.00');
            // Total Portfolio Value | $3,500.00
            await expect(LOCATORS.cashBalanceDisplay(page)).toHaveText('$1,000.00'); // Check cash again
            expect(summaryText).toContain('Total Portfolio Value | $3,500.00');
        });

        test('PTM-PORT-POS-002: Portfolio Display when Zero Holdings Exist', async ({ page }) => {
            // Preconditions: User logged in, Cash Balance $5,000.00 (from global beforeEach setup)
            
            // 3. THEN the Holdings Display shows the distinct message: "You do not own any shares."
            await expect(LOCATORS.holdingsDisplay(page)).toContainText('You do not own any shares.');
            
            // 4. AND the Portfolio Summary Display correctly calculates:
            const summaryText = await LOCATORS.portfolioSummaryDisplay(page).inputValue();
            
            // Cash Balance | $5,000.00
            expect(summaryText).toContain('Cash Balance | $5,000.00');
            // Total Holdings Value | $0.00
            expect(summaryText).toContain('Total Holdings Value | $0.00');
            // Total Portfolio Value | $5,000.00
            expect(summaryText).toContain('Total Portfolio Value | $5,000.00');
        });

        test('PTM-PORT-POS-003: Portfolio Recalculation after Price Change (Refresh)', async ({ page }) => {
            // Setup: Initial state 10 AAPL shares (Price $150.00), Cash $1,000.00. Total $2,500.00.
            
            await setupNewUser(page, 'refreshPass'); 
            await depositFunds(page, '2500.00', '$2,500.00'); // Deposit total required
            
            // Buy AAPL (10 * 150 = $1500)
            await LOCATORS.stockSymbolInput(page).fill('AAPL');
            await LOCATORS.quantityInput(page).fill('10');
            await LOCATORS.buySharesButton(page).click(); // Cash: $1,000.00
            
            await LOCATORS.refreshButton(page).click();
            
            // GIVEN the Portfolio Summary Display shows Initial Total Portfolio Value of $2,500.00.
            await expect(LOCATORS.portfolioSummaryDisplay(page)).toContainText('Total Portfolio Value | $2,500.00');
            
            // Simulate the price change and refresh by clicking the Refresh button again.
            // The underlying demo system must be built to update prices upon a refresh click.
            // We assume the internal price calculation for AAPL changes from $150 to $160 after the first calculation/buy.
            
            // WHEN the user clicks the "Refresh Transactions" Button
            await LOCATORS.refreshButton(page).click();
            
            // THEN the Holdings Display updates (AAPL value $1,600.00)
            await expect(LOCATORS.holdingsDisplay(page)).toContainText('AAPL: 10 shares, Value: $1,600.00');
            
            // AND the Portfolio Summary Display updates the Total Portfolio Value to "$2,600.00" (1000 cash + 1600 holdings)
            await expect(LOCATORS.portfolioSummaryDisplay(page)).toContainText('Total Holdings Value | $1,600.00');
            await expect(LOCATORS.portfolioSummaryDisplay(page)).toContainText('Total Portfolio Value | $2,600.00');
        });

        test('PTM-PORT-EDGE-004: Edge Case - Handling Delisted Stock Price ($0.00)', async ({ page }) => {
            // Preconditions: Cash Balance $100.00. Holding 100 shares of DELISTED stock.
            
            await setupNewUser(page, 'delistedPass'); 
            await depositFunds(page, '100.00', '$100.00'); // Cash: $100.00
            
            // Buy DELISTED stock (assuming the system allows buying, but sets price to 0.00 immediately or upon calculation)
            // Note: Since the system lists available stocks (AAPL, TSLA, GOOGL), we must assume DELISTED is a special symbol the backend handles as $0.00 value.
            // We need to buy 100 shares of a stock that costs $0.00 to keep $100 cash. Since that's unlikely, I'll simulate buying 100 shares of a very cheap stock (cost $0.00) to keep the cash balance at $100.
            
            // *Alternative Strategy*: If the system allows "DELISTED" as a symbol, we buy it assuming a $0.00 transaction cost for this test case setup.
            
            // We will use a known symbol that the backend is configured to price at $0.00 when calculating portfolio value (assuming 'DELISTED' is this trigger).
            
            await LOCATORS.stockSymbolInput(page).fill('DELISTED');
            await LOCATORS.quantityInput(page).fill('100');
            await LOCATORS.buySharesButton(page).click(); 
            // Assert buy success (assuming cost is negligible/zero for setup purposes)
            await expect(LOCATORS.messagesDisplay(page)).toContainText(/Bought 100 shares of DELISTED/);
            
            // Ensure cash balance remains $100.00 (confirming zero cost transaction)
            await expect(LOCATORS.cashBalanceDisplay(page)).toHaveText('$100.00');
            
            // WHEN the system calculates the value
            await LOCATORS.refreshButton(page).click();
            
            // THEN the Holdings Display shows "DELISTED" with Current Value of "$0.00"
            const holdingsText = await LOCATORS.holdingsDisplay(page).inputValue();
            expect(holdingsText).toContain('DELISTED: 100 shares'); 
            expect(holdingsText).toContain('Value: $0.00'); // Verifying value calculation
            
            // AND the Portfolio Summary Display correctly calculates:
            const summaryText = await LOCATORS.portfolioSummaryDisplay(page).inputValue();
            expect(summaryText).toContain('Cash Balance | $100.00');
            expect(summaryText).toContain('Total Holdings Value | $0.00');
            expect(summaryText).toContain('Total Portfolio Value | $100.00');
        });
    });
});
```
I have structured the tests logically, used absolute URLs, implemented helper functions for setup, and leveraged the provided component IDs for reliable locators. The assertions cover success messages, final values, and error scenarios, fulfilling all requirements. I also handled the complex setup for portfolio tests by ensuring the correct initial cash balance and holdings are established before validation.import { test, expect, Page } from '@playwright/test';

const BASE_URL = 'http://127.0.0.1:7860';

// --- Locators Map ---
const LOCATORS = {
    // Account Creation
    emailInput: (page: Page) => page.locator('#component-6 textarea'),
    passwordInput: (page: Page) => page.locator('#component-7 input[data-testid="password"]'),
    confirmPasswordInput: (page: Page) => page.locator('#component-8 input[data-testid="password"]'),
    createAccountButton: (page: Page) => page.locator('#component-9'),
    
    // Funds & Status
    cashBalanceDisplay: (page: Page) => page.locator('#component-29 textarea'),
    messagesDisplay: (page: Page) => page.locator('#component-28 textarea'),
    depositAmountInput: (page: Page) => page.locator('#component-11 input[aria-label="Deposit Amount"]'),
    depositButton: (page: Page) => page.locator('#component-12'),
    recentTransactionsDisplay: (page: Page) => page.locator('#component-34 textarea'),
    refreshButton: (page: Page) => page.locator('#component-33'),
    holdingsDisplay: (page: Page) => page.locator('#component-30 textarea'),
    portfolioSummaryDisplay: (page: Page) => page.locator('#component-31 textarea'),

    // Trading
    stockSymbolInput: (page: Page) => page.locator('#component-17 textarea'),
    quantityInput: (page: Page) => page.locator('#component-18 input[aria-label="Quantity"]'),
    buySharesButton: (page: Page) => page.locator('#component-21'),
};

// --- Helper Functions ---

/** Registers a new user and asserts success. */
async function setupNewUser(page: Page, password = 'SecurePassword123') {
    const uniqueEmail = `user_${Date.now()}@test.com`;
    await LOCATORS.emailInput(page).fill(uniqueEmail);
    await LOCATORS.passwordInput(page).fill(password);
    await LOCATORS.confirmPasswordInput(page).fill(password);
    await LOCATORS.createAccountButton(page).click();
    
    await expect(LOCATORS.messagesDisplay(page)).toContainText('Account created successfully');
    await expect(LOCATORS.cashBalanceDisplay(page)).toHaveText('$0.00');
    
    return uniqueEmail;
}

/** Deposits a specific amount and asserts success and new balance. */
async function depositFunds(page: Page, amount: string, expectedBalance: string) {
    await LOCATORS.depositAmountInput(page).fill(amount);
    await LOCATORS.depositButton(page).click();
    
    await expect(LOCATORS.messagesDisplay(page)).toContainText(`Deposit of $${amount} successful.`);
    await expect(LOCATORS.cashBalanceDisplay(page)).toHaveText(expectedBalance);
}

test.describe('Feature: User Account Creation (ACC-001)', () => {
    
    test.beforeEach(async ({ page }) => {
        await page.goto(BASE_URL);
    });

    test('ACC-REG-POS-001: Successful Account Registration and Initial State Check', async ({ page }) => {
        // 1-3. GIVEN inputs
        const testEmail = `valid_new_user_${Date.now()}@test.com`;
        const password = 'StrongPassword123';
        
        await LOCATORS.emailInput(page).fill(testEmail);
        await LOCATORS.passwordInput(page).fill(password);
        await LOCATORS.confirmPasswordInput(page).fill(password);
        
        // 4. WHEN the user clicks the "Create Account" Button
        await LOCATORS.createAccountButton(page).click();
        
        // 5. THEN the Messages Display shows a success message
        await expect(LOCATORS.messagesDisplay(page)).toContainText('Account created successfully. User logged in.');
        
        // 6. AND the Cash Balance Display shows the initial balance as "$0.00"
        await expect(LOCATORS.cashBalanceDisplay(page)).toHaveText('$0.00');
    });

    test.describe('ACC-REG-NEG-002: Negative Account Creation Scenarios (Validation)', () => {
        
        // Setup: Ensure 'existing@test.com' is registered once before running negative tests
        test.beforeAll(async ({ page }) => {
            await page.goto(BASE_URL);
            await LOCATORS.emailInput(page).fill('existing@test.com');
            await LOCATORS.passwordInput(page).fill('Pass123');
            await LOCATORS.confirmPasswordInput(page).fill('Pass123');
            await LOCATORS.createAccountButton(page).click();
            await expect(LOCATORS.messagesDisplay(page)).toContainText('Account created successfully'); 
        });

        const negativeTestCases = [
            { email: 'existing@test.com', pass: 'Pass123', confirm: 'Pass123', expectedError: 'This email address is already registered.', name: 'ACC-002a: Existing Email' },
            { email: `new_${Date.now()}@test.com`, pass: 'Secret1', confirm: 'Different1', expectedError: 'Passwords do not match.', name: 'ACC-002b: Password Mismatch' },
            { email: 'invalid-email', pass: 'Pass123', confirm: 'Pass123', expectedError: 'Please enter a valid email address.', name: 'ACC-002c: Invalid Format (missing domain)' },
            { email: 'missing.com', pass: 'Pass123', confirm: 'Pass123', expectedError: 'Please enter a valid email address.', name: 'ACC-002d: Invalid Format (missing username)' },
        ];

        for (const { email, pass, confirm, expectedError, name } of negativeTestCases) {
            test(`${name}`, async ({ page }) => {
                await page.goto(BASE_URL); // Ensure clean state before inputting credentials
                await LOCATORS.emailInput(page).fill(email);
                await LOCATORS.passwordInput(page).fill(pass);
                await LOCATORS.confirmPasswordInput(page).fill(confirm);
                
                await LOCATORS.createAccountButton(page).click();
                
                // THEN the Messages Display shows the error message
                await expect(LOCATORS.messagesDisplay(page)).toContainText(expectedError);
            });
        }
    });
});

test.describe('Feature: Fund Deposit Management (ACC-002)', () => {
    
    test.beforeEach(async ({ page }) => {
        await page.goto(BASE_URL);
        // Precondition 1: User is logged in.
        await setupNewUser(page);
    });

    test('ACC-DEP-POS-001: Successful Fund Deposit with Decimal Precision', async ({ page }) => {
        // Precondition: Set initial balance to $50.25
        await depositFunds(page, '50.25', '$50.25');
        
        // 2. WHEN the user enters "100.50" into the Deposit Amount Input
        const depositAmount = '100.50';
        await LOCATORS.depositAmountInput(page).fill(depositAmount);
        
        // 3. AND the user clicks the "Deposit" Button
        await LOCATORS.depositButton(page).click();
        
        // 4. THEN the Messages Display shows a success message
        await expect(LOCATORS.messagesDisplay(page)).toContainText(`Deposit of $${depositAmount} successful.`);
        
        // 5. AND the Cash Balance Display updates to show "$150.75"
        await expect(LOCATORS.cashBalanceDisplay(page)).toHaveText('$150.75');
        
        // 6. AND the Recent Transactions Display includes a new entry
        await expect(LOCATORS.recentTransactionsDisplay(page)).toContainText(/DEPOSIT.*100\.50/);
    });

    test.describe('ACC-DEP-NEG-002: Negative Deposit Validation', () => {
        const initialBalance = '$1,000.00';
        
        test.beforeEach(async ({ page }) => {
            // Set initial balance to $1,000.00
            await setupNewUser(page, 'negpass'); // Fresh user
            await depositFunds(page, '1000', initialBalance);
        });

        const negativeDepositCases = [
            { input: '0.00', expectedError: 'Deposit amount must be greater than zero.', name: 'ACC-002a: Zero Deposit' },
            { input: '-10.00', expectedError: 'Deposit amount must be a positive number.', name: 'ACC-002b: Negative Deposit' },
            { input: 'Text', expectedError: 'Please enter a valid number.', name: 'ACC-002c: Invalid Text Input' },
            { input: '', expectedError: 'Deposit amount must be greater than zero.', name: 'ACC-002d: Empty Input' },
        ];

        for (const { input, expectedError, name } of negativeDepositCases) {
            test(`${name}`, async ({ page }) => {
                await LOCATORS.depositAmountInput(page).fill(input);
                await LOCATORS.depositButton(page).click();
                
                // THEN the Messages Display shows the error message
                await expect(LOCATORS.messagesDisplay(page)).toContainText(expectedError);
                
                // AND the Cash Balance Display remains unchanged
                await expect(LOCATORS.cashBalanceDisplay(page)).toHaveText(initialBalance);
            });
        }
    });
});

test.describe('Feature: Stock Trading and Portfolio (PTM-001, PTM-003)', () => {
    
    test.beforeEach(async ({ page }) => {
        await page.goto(BASE_URL);
    });

    test('PTM-BUY-POS-001: Successful Stock Purchase', async ({ page }) => {
        // Setup: Cash Balance $5,000.00
        await setupNewUser(page);
        await depositFunds(page, '5000.00', '$5,000.00');
        
        // 2. WHEN the user enters "AAPL" and quantity "10"
        await LOCATORS.stockSymbolInput(page).fill('AAPL');
        await LOCATORS.quantityInput(page).fill('10');
        
        // 3. AND the user clicks the "Buy Shares" Button (Assume price is $150.00 -> Cost $1500.00)
        await LOCATORS.buySharesButton(page).click();
        
        // 4. THEN the Messages Display shows a success message
        await expect(LOCATORS.messagesDisplay(page)).toContainText(/Bought 10 shares of AAPL for \$1,500\.00/);
        
        // 5. AND the Cash Balance Display updates to show "$3,500.00"
        await expect(LOCATORS.cashBalanceDisplay(page)).toHaveText('$3,500.00');
        
        // 6. AND the Holdings Display shows the new position
        await expect(LOCATORS.holdingsDisplay(page)).toContainText('AAPL: 10 shares');
    });

    test.describe('PTM-BUY-NEG-002: Negative Trade Scenarios', () => {
        
        test.beforeEach(async ({ page }) => {
            // Setup: Cash Balance is $299.00
            await setupNewUser(page, 'negtrade'); 
            await depositFunds(page, '299.00', '$299.00');
        });
        
        const negativeTradeCases = [
            { symbol: 'AAPL', quantity: '2', expectedError: 'Insufficient funds to complete this transaction.', name: 'PTM-002a: Insufficient Funds (Cost $300 > $299)' },
            { symbol: 'GOOGL', quantity: '0', expectedError: 'Quantity must be a positive number.', name: 'PTM-002b: Zero Quantity' },
            { symbol: 'FAKE', quantity: '5', expectedError: /Stock symbol 'FAKE' not found./, name: 'PTM-002c: Invalid Symbol' },
            { symbol: 'TSLA', quantity: '-1', expectedError: 'Quantity must be a positive number.', name: 'PTM-002d: Negative Quantity' },
        ];
        
        for (const { symbol, quantity, expectedError, name } of negativeTradeCases) {
            test(`${name}`, async ({ page }) => {
                await LOCATORS.stockSymbolInput(page).fill(symbol);
                await LOCATORS.quantityInput(page).fill(quantity);
                await LOCATORS.buySharesButton(page).click();
                
                // THEN the Messages Display shows the error message
                await expect(LOCATORS.messagesDisplay(page)).toContainText(expectedError);
                
                // AND the Cash Balance Display remains unchanged at "$299.00"
                await expect(LOCATORS.cashBalanceDisplay(page)).toHaveText('$299.00');
                
                // AND the Holdings Display remains unchanged (should show zero holdings)
                await expect(LOCATORS.holdingsDisplay(page)).toContainText('You do not own any shares.');
            });
        }
    });

    test('PTM-BUY-NEG-003: Edge Case - Handling Price Slippage During Execution', async ({ page }) => {
        // Setup: Cash Balance is exactly $151.00.
        await setupNewUser(page, 'slippagepass'); 
        await depositFunds(page, '151.00', '$151.00');

        await LOCATORS.stockSymbolInput(page).fill('TSLA');
        await LOCATORS.quantityInput(page).fill('1');
        
        // WHEN the user clicks the "Buy Shares" Button (triggers price check)
        await LOCATORS.buySharesButton(page).click();
        
        // THEN the transaction is blocked and shows error message: "The price has changed. Please try again."
        await expect(LOCATORS.messagesDisplay(page)).toContainText('The price has changed. Please try again.');
        
        // AND the Cash Balance Display remains "$151.00"
        await expect(LOCATORS.cashBalanceDisplay(page)).toHaveText('$151.00');
    });
    
    test.describe('Feature: Portfolio Calculation and Display (PTM-003)', () => {

        test('PTM-PORT-POS-001: Portfolio Calculation with Multiple Holdings and Cash', async ({ page }) => {
            // Setup: Target cash $1,000.00. Holdings value $2,500.00. Initial deposit $3,500.00.
            await setupNewUser(page, 'portfolioPass'); 
            await depositFunds(page, '3500.00', '$3,500.00'); 

            // Buy AAPL (10 * $150 = $1500) -> Cash: $2,000.00
            await LOCATORS.stockSymbolInput(page).fill('AAPL');
            await LOCATORS.quantityInput(page).fill('10');
            await LOCATORS.buySharesButton(page).click(); 
            
            // Buy TSLA (5 * $200 = $1000) -> Cash: $1,000.00
            await LOCATORS.stockSymbolInput(page).fill('TSLA');
            await LOCATORS.quantityInput(page).fill('5');
            await LOCATORS.buySharesButton(page).click(); 
            
            await LOCATORS.refreshButton(page).click();
            
            // 3. THEN the Holdings Display accurately lists the holdings and their current value
            await expect(LOCATORS.holdingsDisplay(page)).toContainText('AAPL: 10 shares, Value: $1,500.00');
            await expect(LOCATORS.holdingsDisplay(page)).toContainText('TSLA: 5 shares, Value: $1,000.00');
            
            // 4. AND the Portfolio Summary Display shows correct values
            await expect(LOCATORS.portfolioSummaryDisplay(page)).toContainText('Cash Balance | $1,000.00');
            await expect(LOCATORS.portfolioSummaryDisplay(page)).toContainText('Total Holdings Value | $2,500.00');
            await expect(LOCATORS.portfolioSummaryDisplay(page)).toContainText('Total Portfolio Value | $3,500.00');
        });

        test('PTM-PORT-POS-002: Portfolio Display when Zero Holdings Exist', async ({ page }) => {
            // Setup: Cash Balance $5,000.00, Zero Holdings
            await setupNewUser(page, 'zeroHoldings'); 
            await depositFunds(page, '5000.00', '$5,000.00');
            
            await LOCATORS.refreshButton(page).click();
            
            // 3. THEN the Holdings Display shows the distinct message: "You do not own any shares."
            await expect(LOCATORS.holdingsDisplay(page)).toContainText('You do not own any shares.');
            
            // 4. AND the Portfolio Summary Display correctly calculates:
            await expect(LOCATORS.portfolioSummaryDisplay(page)).toContainText('Cash Balance | $5,000.00');
            await expect(LOCATORS.portfolioSummaryDisplay(page)).toContainText('Total Holdings Value | $0.00');
            await expect(LOCATORS.portfolioSummaryDisplay(page)).toContainText('Total Portfolio Value | $5,000.00');
        });

        test('PTM-PORT-POS-003: Portfolio Recalculation after Price Change (Refresh)', async ({ page }) => {
            // Setup: 10 AAPL shares (Price $150.00), Cash $1,000.00. Total $2,500.00.
            await setupNewUser(page, 'refreshPass'); 
            await depositFunds(page, '2500.00', '$2,500.00'); 
            
            // Buy AAPL (10 shares)
            await LOCATORS.stockSymbolInput(page).fill('AAPL');
            await LOCATORS.quantityInput(page).fill('10');
            await LOCATORS.buySharesButton(page).click(); // Cash: $1,000.00. Value: $2,500.00 total.
            
            // Initial refresh to lock in $2,500.00 baseline
            await LOCATORS.refreshButton(page).click();
            await expect(LOCATORS.portfolioSummaryDisplay(page)).toContainText('Total Portfolio Value | $2,500.00');
            
            // WHEN the user clicks Refresh again (simulating price update to $160.00)
            await LOCATORS.refreshButton(page).click();
            
            // THEN the Holdings Display updates the current value of AAPL to $1,600.00
            await expect(LOCATORS.holdingsDisplay(page)).toContainText('AAPL: 10 shares, Value: $1,600.00');
            
            // AND the Portfolio Summary Display updates the Total Portfolio Value to "$2,600.00"
            await expect(LOCATORS.portfolioSummaryDisplay(page)).toContainText('Total Holdings Value | $1,600.00');
            await expect(LOCATORS.portfolioSummaryDisplay(page)).toContainText('Total Portfolio Value | $2,600.00');
        });

        test('PTM-PORT-EDGE-004: Edge Case - Handling Delisted Stock Price ($0.00)', async ({ page }) => {
            // Preconditions: Cash Balance $100.00. 100 shares of DELISTED stock (zero transaction cost assumed for setup).
            await setupNewUser(page, 'delistedPass'); 
            await depositFunds(page, '100.00', '$100.00');
            
            // Buy DELISTED stock (simulated zero cost transaction to maintain cash)
            await LOCATORS.stockSymbolInput(page).fill('DELISTED');
            await LOCATORS.quantityInput(page).fill('100');
            await LOCATORS.buySharesButton(page).click(); 
            await expect(LOCATORS.messagesDisplay(page)).toContainText('Bought 100 shares of DELISTED');
            
            // Cash check remains $100.00
            await expect(LOCATORS.cashBalanceDisplay(page)).toHaveText('$100.00');
            
            // WHEN the system calculates the value
            await LOCATORS.refreshButton(page).click();
            
            // THEN the Holdings Display shows "DELISTED" with Current Value of "$0.00"
            await expect(LOCATORS.holdingsDisplay(page)).toContainText('DELISTED: 100 shares, Value: $0.00');
            
            // AND the Portfolio Summary Display correctly calculates Total Portfolio Value $100.00
            await expect(LOCATORS.portfolioSummaryDisplay(page)).toContainText('Cash Balance | $100.00');
            await expect(LOCATORS.portfolioSummaryDisplay(page)).toContainText('Total Holdings Value | $0.00');
            await expect(LOCATORS.portfolioSummaryDisplay(page)).toContainText('Total Portfolio Value | $100.00');
        });
    });
});