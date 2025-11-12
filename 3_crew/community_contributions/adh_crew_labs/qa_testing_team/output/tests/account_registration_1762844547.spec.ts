import { test, expect, Page } from '@playwright/test';

const BASE_URL = 'http://127.0.0.1:7860';

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
        const testEmail = `valid_new_user_${Date.now()}@test.com`;
        const password = 'StrongPassword123';
        
        await LOCATORS.emailInput(page).fill(testEmail);
        await LOCATORS.passwordInput(page).fill(password);
        await LOCATORS.confirmPasswordInput(page).fill(password);
        
        await LOCATORS.createAccountButton(page).click();
        
        await expect(LOCATORS.messagesDisplay(page)).toContainText('Account created successfully. User logged in.');
        await expect(LOCATORS.cashBalanceDisplay(page)).toHaveText('$0.00');
    });

    test.describe('ACC-REG-NEG-002: Negative Account Creation Scenarios (Validation)', () => {
        
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
                await page.goto(BASE_URL);
                await LOCATORS.emailInput(page).fill(email);
                await LOCATORS.passwordInput(page).fill(pass);
                await LOCATORS.confirmPasswordInput(page).fill(confirm);
                
                await LOCATORS.createAccountButton(page).click();
                
                await expect(LOCATORS.messagesDisplay(page)).toContainText(expectedError);
            });
        }
    });
});

test.describe('Feature: Fund Deposit Management (ACC-002)', () => {
    
    test.beforeEach(async ({ page }) => {
        await page.goto(BASE_URL);
        await setupNewUser(page);
    });

    test('ACC-DEP-POS-001: Successful Fund Deposit with Decimal Precision', async ({ page }) => {
        await depositFunds(page, '50.25', '$50.25');
        
        const depositAmount = '100.50';
        await LOCATORS.depositAmountInput(page).fill(depositAmount);
        await LOCATORS.depositButton(page).click();
        
        await expect(LOCATORS.messagesDisplay(page)).toContainText(`Deposit of $${depositAmount} successful.`);
        await expect(LOCATORS.cashBalanceDisplay(page)).toHaveText('$150.75');
        
        await expect(LOCATORS.recentTransactionsDisplay(page)).toContainText(/DEPOSIT.*100\.50/);
    });

    test.describe('ACC-DEP-NEG-002: Negative Deposit Validation', () => {
        const initialBalance = '$1,000.00';
        
        test.beforeEach(async ({ page }) => {
            await setupNewUser(page, 'negpass');
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
                
                await expect(LOCATORS.messagesDisplay(page)).toContainText(expectedError);
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
        await setupNewUser(page);
        await depositFunds(page, '5000.00', '$5,000.00');
        
        await LOCATORS.stockSymbolInput(page).fill('AAPL');
        await LOCATORS.quantityInput(page).fill('10');
        
        await LOCATORS.buySharesButton(page).click();
        
        await expect(LOCATORS.messagesDisplay(page)).toContainText(/Bought 10 shares of AAPL for \$1,500\.00/);
        await expect(LOCATORS.cashBalanceDisplay(page)).toHaveText('$3,500.00');
        
        await expect(LOCATORS.holdingsDisplay(page)).toContainText('AAPL: 10 shares');
    });

    test.describe('PTM-BUY-NEG-002: Negative Trade Scenarios', () => {
        
        test.beforeEach(async ({ page }) => {
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
                
                await expect(LOCATORS.messagesDisplay(page)).toContainText(expectedError);
                await expect(LOCATORS.cashBalanceDisplay(page)).toHaveText('$299.00');
                await expect(LOCATORS.holdingsDisplay(page)).toContainText('You do not own any shares.');
            });
        }
    });

    test('PTM-BUY-NEG-003: Edge Case - Handling Price Slippage During Execution', async ({ page }) => {
        await setupNewUser(page, 'slippagepass'); 
        await depositFunds(page, '151.00', '$151.00');

        await LOCATORS.stockSymbolInput(page).fill('TSLA');
        await LOCATORS.quantityInput(page).fill('1');
        
        await LOCATORS.buySharesButton(page).click();
        
        await expect(LOCATORS.messagesDisplay(page)).toContainText('The price has changed. Please try again.');
        await expect(LOCATORS.cashBalanceDisplay(page)).toHaveText('$151.00');
    });
    
    test.describe('Feature: Portfolio Calculation and Display (PTM-003)', () => {

        test('PTM-PORT-POS-001: Portfolio Calculation with Multiple Holdings and Cash', async ({ page }) => {
            await setupNewUser(page, 'portfolioPass'); 
            await depositFunds(page, '3500.00', '$3,500.00'); 

            // Buy AAPL (10 * $150 = $1500)
            await LOCATORS.stockSymbolInput(page).fill('AAPL');
            await LOCATORS.quantityInput(page).fill('10');
            await LOCATORS.buySharesButton(page).click(); 
            
            // Buy TSLA (5 * $200 = $1000)
            await LOCATORS.stockSymbolInput(page).fill('TSLA');
            await LOCATORS.quantityInput(page).fill('5');
            await LOCATORS.buySharesButton(page).click(); 
            
            await LOCATORS.refreshButton(page).click();
            
            await expect(LOCATORS.holdingsDisplay(page)).toContainText('AAPL: 10 shares, Value: $1,500.00');
            await expect(LOCATORS.holdingsDisplay(page)).toContainText('TSLA: 5 shares, Value: $1,000.00');
            
            await expect(LOCATORS.portfolioSummaryDisplay(page)).toContainText('Cash Balance | $1,000.00');
            await expect(LOCATORS.portfolioSummaryDisplay(page)).toContainText('Total Holdings Value | $2,500.00');
            await expect(LOCATORS.portfolioSummaryDisplay(page)).toContainText('Total Portfolio Value | $3,500.00');
        });

        test('PTM-PORT-POS-002: Portfolio Display when Zero Holdings Exist', async ({ page }) => {
            await setupNewUser(page, 'zeroHoldings'); 
            await depositFunds(page, '5000.00', '$5,000.00');
            
            await LOCATORS.refreshButton(page).click();
            
            await expect(LOCATORS.holdingsDisplay(page)).toContainText('You do not own any shares.');
            
            await expect(LOCATORS.portfolioSummaryDisplay(page)).toContainText('Cash Balance | $5,000.00');
            await expect(LOCATORS.portfolioSummaryDisplay(page)).toContainText('Total Holdings Value | $0.00');
            await expect(LOCATORS.portfolioSummaryDisplay(page)).toContainText('Total Portfolio Value | $5,000.00');
        });

        test('PTM-PORT-POS-003: Portfolio Recalculation after Price Change (Refresh)', async ({ page }) => {
            await setupNewUser(page, 'refreshPass'); 
            await depositFunds(page, '2500.00', '$2,500.00'); 
            
            await LOCATORS.stockSymbolInput(page).fill('AAPL');
            await LOCATORS.quantityInput(page).fill('10');
            await LOCATORS.buySharesButton(page).click();
            
            await LOCATORS.refreshButton(page).click();
            await expect(LOCATORS.portfolioSummaryDisplay(page)).toContainText('Total Portfolio Value | $2,500.00');
            
            await LOCATORS.refreshButton(page).click();
            
            await expect(LOCATORS.holdingsDisplay(page)).toContainText('AAPL: 10 shares, Value: $1,600.00');
            
            await expect(LOCATORS.portfolioSummaryDisplay(page)).toContainText('Total Holdings Value | $1,600.00');
            await expect(LOCATORS.portfolioSummaryDisplay(page)).toContainText('Total Portfolio Value | $2,600.00');
        });

        test('PTM-PORT-EDGE-004: Edge Case - Handling Delisted Stock Price ($0.00)', async ({ page }) => {
            await setupNewUser(page, 'delistedPass'); 
            await depositFunds(page, '100.00', '$100.00');
            
            await LOCATORS.stockSymbolInput(page).fill('DELISTED');
            await LOCATORS.quantityInput(page).fill('100');
            await LOCATORS.buySharesButton(page).click(); 
            await expect(LOCATORS.messagesDisplay(page)).toContainText('Bought 100 shares of DELISTED');
            
            await expect(LOCATORS.cashBalanceDisplay(page)).toHaveText('$100.00');
            
            await LOCATORS.refreshButton(page).click();
            
            await expect(LOCATORS.holdingsDisplay(page)).toContainText('DELISTED: 100 shares, Value: $0.00');
            
            await expect(LOCATORS.portfolioSummaryDisplay(page)).toContainText('Cash Balance | $100.00');
            await expect(LOCATORS.portfolioSummaryDisplay(page)).toContainText('Total Holdings Value | $0.00');
            await expect(LOCATORS.portfolioSummaryDisplay(page)).toContainText('Total Portfolio Value | $100.00');
        });
    });
});