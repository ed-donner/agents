import { test, expect, Page } from '@playwright/test';

const baseURL = 'http://127.0.0.1:7860';

test.describe('ACC-001: User Account Creation and Validation', () => {

    test.beforeEach(async ({ page }) => {
        await page.goto(baseURL);
    });

    test('ACC-001-T01: Should register a new user successfully', async ({ page }) => {
        const uniqueEmail = `new_user_${Date.now()}@test.com`;
        
        const emailInput = page.locator('#component-6 textarea');
        const passwordInput = page.locator('#component-7 input[type="password"]');
        const confirmPasswordInput = page.locator('#component-8 input[type="password"]');
        const createAccountButton = page.locator('button#component-9');
        const messagesOutput = page.locator('#component-28 textarea');
        const cashBalanceOutput = page.locator('#component-29 textarea');

        await emailInput.fill(uniqueEmail);
        await passwordInput.fill('SecurePass123!');
        await confirmPasswordInput.fill('SecurePass123!');
        await createAccountButton.click();

        await expect(messagesOutput).toHaveValue(`Account created successfully for ${uniqueEmail}. You are now logged in.`);
        await expect(cashBalanceOutput).toHaveValue('$0.00');
    });

    test('ACC-001-T02: Should block registration for an existing email', async ({ page }) => {
        const existingEmail = `existing_${Date.now()}@test.com`;

        const emailInput = page.locator('#component-6 textarea');
        const passwordInput = page.locator('#component-7 input[type="password"]');
        const confirmPasswordInput = page.locator('#component-8 input[type="password"]');
        const createAccountButton = page.locator('button#component-9');
        const messagesOutput = page.locator('#component-28 textarea');

        await emailInput.fill(existingEmail);
        await passwordInput.fill('Pass123');
        await confirmPasswordInput.fill('Pass123');
        await createAccountButton.click();
        await expect(messagesOutput).toHaveValue(`Account created successfully for ${existingEmail}. You are now logged in.`);

        await emailInput.fill(existingEmail);
        await passwordInput.fill('Pass123');
        await confirmPasswordInput.fill('Pass123');
        await createAccountButton.click();

        await expect(messagesOutput).toHaveValue('This email address is already registered.');
    });

    test('ACC-001-T03: Should block registration if passwords do not match', async ({ page }) => {
        const emailInput = page.locator('#component-6 textarea');
        const passwordInput = page.locator('#component-7 input[type="password"]');
        const confirmPasswordInput = page.locator('#component-8 input[type="password"]');
        const createAccountButton = page.locator('button#component-9');
        const messagesOutput = page.locator('#component-28 textarea');
        
        await emailInput.fill('mismatch@test.com');
        await passwordInput.fill('Pass123');
        await confirmPasswordInput.fill('Pass456');
        await createAccountButton.click();

        await expect(messagesOutput).toHaveValue('Passwords do not match.');
    });

    test('ACC-001-T04: Should block registration for an invalid email format', async ({ page }) => {
        const emailInput = page.locator('#component-6 textarea');
        const passwordInput = page.locator('#component-7 input[type="password"]');
        const confirmPasswordInput = page.locator('#component-8 input[type="password"]');
        const createAccountButton = page.locator('button#component-9');
        const messagesOutput = page.locator('#component-28 textarea');

        await emailInput.fill('invalid-email');
        await passwordInput.fill('Pass123');
        await confirmPasswordInput.fill('Pass123');
        await createAccountButton.click();

        await expect(messagesOutput).toHaveValue('Please enter a valid email address.');
    });
});


test.describe.serial('Full User Journey: Funds and Trading', () => {
    let page: Page;
    
    const messagesOutput = () => page.locator('#component-28 textarea');
    const cashBalanceOutput = () => page.locator('#component-29 textarea');
    const holdingsOutput = () => page.locator('#component-30 textarea');
    const depositInput = () => page.getByLabel('Deposit Amount');
    const depositButton = () => page.locator('button#component-12');
    const withdrawInput = () => page.getByLabel('Withdraw Amount');
    const withdrawButton = () => page.locator('button#component-14');
    const symbolInput = () => page.locator('#component-17 textarea');
    const quantityInput = () => page.getByLabel('Quantity');
    const buyButton = () => page.locator('button#component-21');
    const sellButton = () => page.locator('button#component-22');

    test.beforeAll(async ({ browser }) => {
        page = await browser.newPage();
        await page.goto(baseURL);

        const uniqueEmail = `journey_user_${Date.now()}@test.com`;
        await page.locator('#component-6 textarea').fill(uniqueEmail);
        await page.locator('#component-7 input[type="password"]').fill('SecurePass123!');
        await page.locator('#component-8 input[type="password"]').fill('SecurePass123!');
        await page.locator('button#component-9').click();
        await expect(messagesOutput()).toHaveValue(`Account created successfully for ${uniqueEmail}. You are now logged in.`);
        await expect(cashBalanceOutput()).toHaveValue('$0.00');
    });

    test.afterAll(async () => {
        await page.close();
    });

    test('ACC-002-T01/T02: Should deposit funds successfully', async () => {
        await depositInput().fill('100.50');
        await depositButton().click();
        await expect(messagesOutput()).toHaveValue('Successfully deposited $100.50');
        await expect(cashBalanceOutput()).toHaveValue('$100.50');

        await depositInput().fill('500');
        await depositButton().click();
        await expect(messagesOutput()).toHaveValue('Successfully deposited $500.00');
        await expect(cashBalanceOutput()).toHaveValue('$600.50');
    });

    test('ACC-002-T03/T04/T05: Should block invalid deposit amounts', async () => {
        await depositInput().fill('0');
        await depositButton().click();
        await expect(messagesOutput()).toHaveValue('Deposit amount must be greater than zero.');
        await expect(cashBalanceOutput()).toHaveValue('$600.50');

        await depositInput().fill('-50.00');
        await depositButton().click();
        await expect(messagesOutput()).toHaveValue('Deposit amount must be a positive number.');
        await expect(cashBalanceOutput()).toHaveValue('$600.50');

        await depositInput().fill('TEXT');
        await depositButton().click();
        await expect(messagesOutput()).toHaveValue('Deposit amount must be a valid number.');
        await expect(cashBalanceOutput()).toHaveValue('$600.50');
    });

    test('ACC-003-T01/T02/T03/T04: Should handle valid and invalid withdrawals', async () => {
        await withdrawInput().fill('100.00');
        await withdrawButton().click();
        await expect(messagesOutput()).toHaveValue('Successfully withdrew $100.00.');
        await expect(cashBalanceOutput()).toHaveValue('$500.50');

        await withdrawInput().fill('500.51');
        await withdrawButton().click();
        await expect(messagesOutput()).toHaveValue('Insufficient funds for withdrawal.');
        await expect(cashBalanceOutput()).toHaveValue('$500.50');

        await withdrawInput().fill('0.00');
        await withdrawButton().click();
        await expect(messagesOutput()).toHaveValue('Withdrawal amount must be greater than zero.');
        await expect(cashBalanceOutput()).toHaveValue('$500.50');

        await withdrawInput().fill('500.50');
        await withdrawButton().click();
        await expect(messagesOutput()).toHaveValue('Successfully withdrew $500.50.');
        await expect(cashBalanceOutput()).toHaveValue('$0.00');
    });

    test('PTM-001: Should handle buy transactions', async () => {
        await depositInput().fill('10000');
        await depositButton().click();
        await expect(cashBalanceOutput()).toHaveValue('$10,000.00');
        
        await symbolInput().fill('AAPL');
        await quantityInput().fill('10');
        await buyButton().click();
        await expect(messagesOutput()).toContainText('Bought 10 shares of AAPL');
        await expect(holdingsOutput()).toContainText('AAPL: 10');
        const cashAfterBuy = await cashBalanceOutput().inputValue();
        expect(parseFloat(cashAfterBuy.replace(/[$,]/g, ''))).toBeLessThan(10000);

        await symbolInput().fill('FAKE');
        await quantityInput().fill('10');
        await buyButton().click();
        await expect(messagesOutput()).toHaveValue("Stock symbol 'FAKE' not found.");
        await expect(holdingsOutput()).not.toContainText('FAKE');

        await symbolInput().fill('TSLA');
        await quantityInput().fill('0');
        await buyButton().click();
        await expect(messagesOutput()).toHaveValue('Quantity must be a positive integer.');

        await symbolInput().fill('TSLA');
        await quantityInput().fill('1000');
        await buyButton().click();
        await expect(messagesOutput()).toHaveValue('Insufficient funds to complete this transaction.');
    });

    test('PTM-002: Should handle sell transactions', async () => {
        await symbolInput().fill('AAPL');
        await quantityInput().fill('5');
        await sellButton().click();
        await expect(messagesOutput()).toContainText('Sold 5 shares of AAPL');
        await expect(holdingsOutput()).toContainText('AAPL: 5');

        await symbolInput().fill('GOOGL');
        await quantityInput().fill('1');
        await sellButton().click();
        await expect(messagesOutput()).toHaveValue('You do not own GOOGL shares.');

        await symbolInput().fill('AAPL');
        await quantityInput().fill('6');
        await sellButton().click();
        await expect(messagesOutput()).toContainText('You can only sell 5 shares of AAPL.');
        
        await symbolInput().fill('AAPL');
        await quantityInput().fill('5');
        await sellButton().click();
        await expect(messagesOutput()).toContainText('Sold 5 shares of AAPL');
        await expect(holdingsOutput()).not.toContainText('AAPL');
    });

    test('PTM-005: Should display transaction history correctly', async () => {
        const refreshButton = page.locator('button#component-33');
        const historyOutput = page.locator('#component-34 textarea');

        await refreshButton.click();
        
        const historyText = await historyOutput.inputValue();
        
        expect(historyText).toContain('Type: SELL, Symbol: AAPL, Quantity: 5');
        expect(historyText).toContain('Type: BUY, Symbol: AAPL, Quantity: 10');
        expect(historyText).toContain('Type: DEPOSIT, Amount: $10000.00');
        expect(historyText).toContain('Type: WITHDRAWAL, Amount: $500.50');
        expect(historyText).toContain('Type: DEPOSIT, Amount: $500.00');
        expect(historyText).toContain('Type: DEPOSIT, Amount: $100.50');
        
        const sellIndex = historyText.indexOf('Type: SELL, Symbol: AAPL, Quantity: 5');
        const buyIndex = historyText.indexOf('Type: BUY, Symbol: AAPL, Quantity: 10');
        const depositIndex = historyText.indexOf('Type: DEPOSIT, Amount: $10000.00');
        
        expect(sellIndex).toBeGreaterThan(-1);
        expect(buyIndex).toBeGreaterThan(-1);
        expect(depositIndex).toBeGreaterThan(-1);
        expect(sellIndex).toBeLessThan(buyIndex);
        expect(buyIndex).toBeLessThan(depositIndex);
    });
});