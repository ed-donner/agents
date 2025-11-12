```typescript
// File: output/tests/financial_app.spec.ts

import { test, expect, Page } from '@playwright/test';

const baseURL = 'http://127.0.0.1:7860';

// Helper function to create a unique user for each test run to ensure isolation
const createTestUser = async (page: Page, testId: string) => {
    const email = `user_${testId}_${Date.now()}@test.com`;
    const password = 'SecurePass123!';
    await page.locator('#component-6 textarea').fill(email);
    await page.locator('#component-7 input[type="password"]').fill(password);
    await page.locator('#component-8 input[type="password"]').fill(password);
    await page.getByRole('button', { name: 'Create Account' }).click();
    await expect(page.locator('#component-28 textarea')).toHaveValue(`Account created successfully for ${email}. You are now logged in.`);
    return { email, password };
};

test.describe('ACC-001 User Account Creation and Validation', () => {

    test('ACC-001-T01: Successful Account Registration (Happy Path)', async ({ page }) => {
        await page.goto(baseURL);
        const email = `new_user_${Date.now()}@test.com`;
        
        await page.locator('#component-6 textarea').fill(email);
        await page.locator('#component-7 input[type="password"]').fill('SecurePass123!');
        await page.locator('#component-8 input[type="password"]').fill('SecurePass123!');
        await page.getByRole('button', { name: 'Create Account' }).click();
        
        await expect(page.locator('#component-28 textarea')).toHaveValue(`Account created successfully for ${email}. You are now logged in.`);
        await expect(page.locator('#component-29 textarea')).toHaveValue('$0.00');
    });

    const validationTestCases = [
        {
            id: 'ACC-001-T02',
            email: 'existing@test.com',
            pass: 'Pass123',
            confirmPass: 'Pass123',
            errorMessage: 'This email address is already registered.'
        },
        {
            id: 'ACC-001-T03',
            email: 'mismatch@test.com',
            pass: 'Pass123',
            confirmPass: 'Pass456',
            errorMessage: 'Passwords do not match.'
        },
        {
            id: 'ACC-001-T04',
            email: 'invalid-email',
            pass: 'Pass123',
            confirmPass: 'Pass123',
            errorMessage: 'Please enter a valid email address.'
        }
    ];

    test.beforeAll(async ({ browser }) => {
        // Pre-create the user for the "already registered" test case
        const page = await browser.newPage();
        await page.goto(baseURL);
        await page.locator('#component-6 textarea').fill('existing@test.com');
        await page.locator('#component-7 input[type="password"]').fill('Pass123');
        await page.locator('#component-8 input[type="password"]').fill('Pass123');
        await page.getByRole('button', { name: 'Create Account' }).click();
        await page.close();
    });

    for (const { id, email, pass, confirmPass, errorMessage } of validationTestCases) {
        test(`${id}: Block Account Creation due to invalid input - ${errorMessage}`, async ({ page }) => {
            await page.goto(baseURL);
            
            await page.locator('#component-6 textarea').fill(email);
            await page.locator('#component-7 input[type="password"]').fill(pass);
            await page.locator('#component-8 input[type="password"]').fill(confirmPass);
            await page.getByRole('button', { name: 'Create Account' }).click();
            
            await expect(page.locator('#component-28 textarea')).toHaveValue(errorMessage);
        });
    }
});

test.describe('ACC-002 & ACC-003 Fund Management', () => {

    test.beforeEach(async ({ page }) => {
        await page.goto(baseURL);
        await createTestUser(page, 'fund-management');
    });

    test('ACC-002-T01: Successfully deposit funds (500)', async ({ page }) => {
        await page.getByLabel('Deposit Amount').fill('500.00');
        await page.getByRole('button', { name: 'Deposit' }).click();
        
        await expect(page.locator('#component-28 textarea')).toHaveValue('Successfully deposited $500.00.');
        await expect(page.locator('#component-29 textarea')).toHaveValue('$500.00');
    });
    
    test('ACC-002-T02: Successfully deposit decimal funds (100.50)', async ({ page }) => {
        await page.getByLabel('Deposit Amount').fill('50.25');
        await page.getByRole('button', { name: 'Deposit' }).click();
        await page.getByLabel('Deposit Amount').fill('100.50');
        await page.getByRole('button', { name: 'Deposit' }).click();

        await expect(page.locator('#component-28 textarea')).toHaveValue('Successfully deposited $100.50.');
        await expect(page.locator('#component-29 textarea')).toHaveValue('$150.75');
    });

    const invalidDepositCases = [
        { id: 'ACC-002-T03', amount: '0.00', message: 'Deposit amount must be greater than zero.' },
        { id: 'ACC-002-T04', amount: '-50.00', message: 'Deposit amount must be a positive number.' },
        { id: 'ACC-002-T05', amount: 'TEXT', message: 'Deposit amount must be a valid number.' }
    ];

    for (const { id, amount, message } of invalidDepositCases) {
        test(`${id}: Block deposit for invalid amount: ${amount}`, async ({ page }) => {
            await page.getByLabel('Deposit Amount').fill('100');
            await page.getByRole('button', { name: 'Deposit' }).click();
            await expect(page.locator('#component-29 textarea')).toHaveValue('$100.00');

            await page.getByLabel('Deposit Amount').fill(amount);
            await page.getByRole('button', { name: 'Deposit' }).click();

            await expect(page.locator('#component-29 textarea')).toHaveValue('$100.00');
            await expect(page.locator('#component-28 textarea')).toHaveValue(message);
        });
    }
    
    const withdrawalCases = [
        { id: 'ACC-003-T01', amount: '100.00', newBalance: '$400.00', message: 'Successfully withdrew $100.00.' },
        { id: 'ACC-003-T02', amount: '500.00', newBalance: '$0.00', message: 'Successfully withdrew $500.00.' },
        { id: 'ACC-003-T03', amount: '500.01', newBalance: '$500.00', message: 'Insufficient funds for withdrawal.' },
        { id: 'ACC-003-T04', amount: '0.00', newBalance: '$500.00', message: 'Withdrawal amount must be greater than zero.' }
    ];
    
    for (const { id, amount, newBalance, message } of withdrawalCases) {
        test(`${id}: Withdraw funds and check balance`, async ({ page }) => {
            await page.getByLabel('Deposit Amount').fill('500');
            await page.getByRole('button', { name: 'Deposit' }).click();
            await expect(page.locator('#component-29 textarea')).toHaveValue('$500.00');

            await page.getByLabel('Withdraw Amount').fill(amount);
            await page.getByRole('button', { name: 'Withdraw' }).click();

            await expect(page.locator('#component-28 textarea')).toHaveValue(message);
            await expect(page.locator('#component-29 textarea')).toHaveValue(newBalance);
        });
    }
});


test.describe('PTM-001 & PTM-002 Trading Operations', () => {

    test('PTM-001-T01: Execute valid stock buy order', async ({ page }) => {
        await page.goto(baseURL);
        await createTestUser(page, 'trading-buy');
        await page.getByLabel('Deposit Amount').fill('10000');
        await page.getByRole('button', { name: 'Deposit' }).click();

        await page.locator('#component-17 textarea').fill('AAPL');
        await page.getByLabel('Quantity').fill('10');
        await page.getByRole('button', { name: 'Buy Shares' }).click();
        
        await expect(page.locator('#component-28 textarea')).toContainText('Bought 10 shares of AAPL at $');
        await expect(page.locator('#component-29 textarea')).not.toHaveValue('$10000.00'); // Price is dynamic, so just check it changed
        await expect(page.locator('#component-30 textarea')).toContainText('AAPL: 10 shares');
    });

    const failedBuyCases = [
        { id: 'PTM-001-T03', symbol: 'TSLA', quantity: '3', message: 'Insufficient funds to complete this transaction.' },
        { id: 'PTM-001-T04', symbol: 'FAKE', quantity: '10', message: "Stock symbol 'FAKE' not found." },
        { id: 'PTM-001-T06', symbol: 'AAPL', quantity: '0', message: 'Quantity must be a positive integer.' }
    ];

    for (const { id, symbol, quantity, message } of failedBuyCases) {
        test(`${id}: Block stock buy order due to invalid input`, async ({ page }) => {
            await page.goto(baseURL);
            await createTestUser(page, `trading-buy-fail-${id}`);
            await page.getByLabel('Deposit Amount').fill('500');
            await page.getByRole('button', { name: 'Deposit' }).click();
            await expect(page.locator('#component-29 textarea')).toHaveValue('$500.00');

            await page.locator('#component-17 textarea').fill(symbol);
            await page.getByLabel('Quantity').fill(quantity);
            await page.getByRole('button', { name: 'Buy Shares' }).click();

            await expect(page.locator('#component-29 textarea')).toHaveValue('$500.00');
            await expect(page.locator('#component-28 textarea')).toHaveValue(message);
        });
    }

    const sellCases = [
        { id: 'PTM-002-T01', symbol: 'AAPL', quantity: '5', message: 'Sold 5 shares of AAPL for $', holdings: 'AAPL: 5 shares' },
        { id: 'PTM-002-T02', symbol: 'AAPL', quantity: '10', message: 'Sold 10 shares of AAPL for $', holdings: '' }, // Holdings should be empty
        { id: 'PTM-002-T03', symbol: 'AAPL', quantity: '11', message: 'You can only sell 10 shares of AAPL.', holdings: 'AAPL: 10 shares' },
        { id: 'PTM-002-T04', symbol: 'GOOGL', quantity: '1', message: 'You do not own GOOGL shares.', holdings: 'AAPL: 10 shares' },
    ];

    for (const { id, symbol, quantity, message, holdings } of sellCases) {
        test(`${id}: Execute valid and invalid stock sell orders`, async ({ page }) => {
            await page.goto(baseURL);
            await createTestUser(page, `trading-sell-${id}`);
            await page.getByLabel('Deposit Amount').fill('2000'); // Enough to buy 10 AAPL
            await page.getByRole('button', { name: 'Deposit' }).click();

            // Buy 10 AAPL shares to set up state
            await page.locator('#component-17 textarea').fill('AAPL');
            await page.getByLabel('Quantity').fill('10');
            await page.getByRole('button', { name: 'Buy Shares' }).click();
            await expect(page.locator('#component-30 textarea')).toContainText('AAPL: 10 shares');
            const initialBalanceText = await page.locator('#component-29 textarea').inputValue();

            // Now, perform the sell operation
            await page.locator('#component-17 textarea').fill(symbol);
            await page.getByLabel('Quantity').fill(quantity);
            await page.getByRole('button', { name: 'Sell Shares' }).click();

            // Assertions
            await expect(page.locator('#component-28 textarea')).toContainText(message);
            if (id === 'PTM-002-T01' || id === 'PTM-002-T02') { // Successful sells
                await expect(page.locator('#component-29 textarea')).not.toHaveValue(initialBalanceText);
            } else { // Failed sells
                await expect(page.locator('#component-29 textarea')).toHaveValue(initialBalanceText);
            }
            if (holdings) {
                await expect(page.locator('#component-30 textarea')).toContainText(holdings);
            } else {
                await expect(page.locator('#component-30 textarea')).toHaveValue('');
            }
        });
    }
});


test.describe('PTM-005 Portfolio and History Verification', () => {

    test('PTM-005-T01: Verify transaction history is displayed correctly', async ({ page }) => {
        await page.goto(baseURL);
        await createTestUser(page, 'history');

        // 1. Deposit $1000
        await page.getByLabel('Deposit Amount').fill('1000');
        await page.getByRole('button', { name: 'Deposit' }).click();
        
        // 2. Buy 5 AAPL
        await page.locator('#component-17 textarea').fill('AAPL');
        await page.getByLabel('Quantity').fill('5');
        await page.getByRole('button', { name: 'Buy Shares' }).click();
        
        // 3. Withdraw $100
        await page.getByLabel('Withdraw Amount').fill('100');
        await page.getByRole('button', { name: 'Withdraw' }).click();

        // 4. Sell 2 AAPL
        await page.locator('#component-17 textarea').fill('AAPL');
        await page.getByLabel('Quantity').fill('2');
        await page.getByRole('button', { name: 'Sell Shares' }).click();

        // 5. Refresh and check history
        await page.getByRole('button', { name: 'Refresh Transactions' }).click();

        const historyText = await page.locator('#component-34 textarea').inputValue();
        const historyLines = historyText.split('\n').filter(line => line.trim() !== '');

        await expect(historyLines).toHaveLength(4);
        expect(historyLines[0]).toMatch(/Type: SELL, Symbol: AAPL, Quantity: 2, Price: \S+, Total: \S+/);
        expect(historyLines[1]).toMatch(/Type: WITHDRAWAL, Amount: \$100.00/);
        expect(historyLines[2]).toMatch(/Type: BUY, Symbol: AAPL, Quantity: 5, Price: \S+, Total: \S+/);
        expect(historyLines[3]).toMatch(/Type: DEPOSIT, Amount: \$1000.00/);
    });

});
```