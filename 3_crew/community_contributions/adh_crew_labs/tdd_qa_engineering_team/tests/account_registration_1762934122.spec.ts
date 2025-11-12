import { test, expect, type Page } from '@playwright/test';

const BASE_URL = 'http://127.0.0.1:7860';

const SELECTORS = {
    // Global Components
    CASH_BALANCE_DISPLAY: '#component-2 textarea[data-testid="textbox"]',

    // Tab Buttons
    TAB_FUNDS: '#component-4-button',
    TAB_TRADING: '#component-21-button',
    TAB_PORTFOLIO: '#component-46-button',
    TAB_HISTORY: '#component-53-button',
    TAB_DEMO: '#component-58-button',

    // Funds Management (Tab 4)
    DEPOSIT_AMOUNT_INPUT: '#component-9 textarea[data-testid="textbox"]',
    DEPOSIT_BUTTON: '#component-10',
    DEPOSIT_RESULT: '#component-11 textarea[data-testid="textbox"]',
    WITHDRAW_AMOUNT_INPUT: '#component-16 textarea[data-testid="textbox"]',
    WITHDRAW_BUTTON: '#component-17',
    WITHDRAW_RESULT: '#component-18 textarea[data-testid="textbox"]',

    // Trading (Tab 21)
    BUY_QUANTITY_INPUT: '#component-27 textarea[data-testid="textbox"]',
    BUY_BUTTON: '#component-28',
    BUY_RESULT: '#component-29 textarea[data-testid="textbox"]',
    SELL_QUANTITY_INPUT: '#component-35 textarea[data-testid="textbox"]',
    SELL_BUTTON: '#component-36',
    SELL_RESULT: '#component-37 textarea[data-testid="textbox"]',

    // Price Lookup (Within Trading Tab - assuming Symbol Input is the first input in component-40 row)
    SYMBOL_INPUT: '#component-40 textarea[data-testid="textbox"]',
    GET_PRICE_BUTTON: '#component-42',
    PRICE_OUTPUT: '#component-43 textarea[data-testid="textbox"]',
    
    // Reporting (Tab 46 and 53)
    REFRESH_PORTFOLIO_BUTTON: '#component-48',
    PORTFOLIO_SUMMARY: '#component-50 textarea[data-testid="textbox"]',
    CURRENT_HOLDINGS: '#component-51 textarea[data-testid="textbox"]',
    REFRESH_HISTORY_BUTTON: '#component-55',
    TRANSACTION_HISTORY: '#component-56 textarea[data-testid="textbox"]',

    // Demo (Tab 58)
    RUN_DEMO_BUTTON: '#component-60',
    DEMO_RESULTS: '#component-61 textarea[data-testid="textbox"]',
};

/**
 * Ensures the account has at least the required amount of cash by depositing if necessary.
 */
async function ensureCashBalance(page: Page, requiredAmount: number) {
    await page.locator(SELECTORS.TAB_FUNDS).click();
    
    const currentBalanceText = await page.locator(SELECTORS.CASH_BALANCE_DISPLAY).inputValue();
    let currentBalance = parseFloat(currentBalanceText.replace(/[$,]/g, '') || '0');
    
    if (currentBalance < requiredAmount) {
        const depositAmount = (requiredAmount - currentBalance).toFixed(2);
        await page.locator(SELECTORS.DEPOSIT_AMOUNT_INPUT).fill(depositAmount);
        await page.locator(SELECTORS.DEPOSIT_BUTTON).click();
        
        await expect(page.locator(SELECTORS.DEPOSIT_RESULT)).toContainText('Deposit successful');
        
        await expect(page.locator(SELECTORS.CASH_BALANCE_DISPLAY)).not.toHaveValue(currentBalanceText);
    }
}

// Global setup: Navigate to the application before each test
test.beforeEach(async ({ page }) => {
    await page.goto(BASE_URL);
    await page.waitForSelector(SELECTORS.CASH_BALANCE_DISPLAY, { state: 'visible' });
});

test.describe('1. Funds Management Tests', () => {

    test('TC_FM_P_001: Successful standard deposit', async ({ page }) => {
        await page.locator(SELECTORS.TAB_FUNDS).click();
        const initialBalanceText = await page.locator(SELECTORS.CASH_BALANCE_DISPLAY).inputValue();
        const initialAmount = parseFloat(initialBalanceText.replace(/[$,]/g, '') || '0');
        const depositValue = 1000.50;
        const expectedTotal = (initialAmount + depositValue).toFixed(2);

        await page.locator(SELECTORS.DEPOSIT_AMOUNT_INPUT).fill(depositValue.toString());
        await page.locator(SELECTORS.DEPOSIT_BUTTON).click();
        
        await expect(page.locator(SELECTORS.DEPOSIT_RESULT)).toContainText('Deposit successful');
        await expect(page.locator(SELECTORS.CASH_BALANCE_DISPLAY)).toContainText(expectedTotal);
    });

    test('TC_FM_P_002 / TS-FM-02: Successful withdrawal leaving zero balance (Boundary)', async ({ page }) => {
        // Setup: Ensure balance is at least 100.00
        await ensureCashBalance(page, 100.00); 
        
        await page.locator(SELECTORS.TAB_FUNDS).click();
        const currentBalanceText = await page.locator(SELECTORS.CASH_BALANCE_DISPLAY).inputValue();
        const currentBalance = parseFloat(currentBalanceText.replace(/[$,]/g, ''));
        
        // Withdraw all available funds
        await page.locator(SELECTORS.WITHDRAW_AMOUNT_INPUT).fill(currentBalance.toFixed(4)); 
        await page.locator(SELECTORS.WITHDRAW_BUTTON).click();
        
        await expect(page.locator(SELECTORS.WITHDRAW_RESULT)).toContainText('Withdrawal successful');
        await expect(page.locator(SELECTORS.CASH_BALANCE_DISPLAY)).toContainText('0.00');
    });

    test('TC_FM_N_003: Attempting to withdraw funds exceeding the current balance (Overdraft Protection)', async ({ page }) => {
        // Setup: Set balance to exactly $500.00
        await ensureCashBalance(page, 500.00);
        
        await page.locator(SELECTORS.WITHDRAW_AMOUNT_INPUT).fill('500.01');
        await page.locator(SELECTORS.WITHDRAW_BUTTON).click();
        
        await expect(page.locator(SELECTORS.WITHDRAW_RESULT)).toContainText('Insufficient funds');
        await expect(page.locator(SELECTORS.CASH_BALANCE_DISPLAY)).toContainText('500.00');
    });

    test('TC_FM_N_004: Attempting to deposit non-positive amounts (0.00)', async ({ page }) => {
        await page.locator(SELECTORS.TAB_FUNDS).click();
        const initialBalance = await page.locator(SELECTORS.CASH_BALANCE_DISPLAY).inputValue();

        await page.locator(SELECTORS.DEPOSIT_AMOUNT_INPUT).fill('0.00');
        await page.locator(SELECTORS.DEPOSIT_BUTTON).click();

        await expect(page.locator(SELECTORS.DEPOSIT_RESULT)).toContainText('Amount must be positive');
        await expect(page.locator(SELECTORS.CASH_BALANCE_DISPLAY)).toHaveValue(initialBalance);
    });

    test('TC_FM_E_005: Testing high-precision decimal handling in deposits', async ({ page }) => {
        // Setup: Ensure balance is exactly $100.00
        await ensureCashBalance(page, 100.00);
        
        await page.locator(SELECTORS.DEPOSIT_AMOUNT_INPUT).fill('0.0001');
        await page.locator(SELECTORS.DEPOSIT_BUTTON).click();

        await expect(page.locator(SELECTORS.DEPOSIT_RESULT)).toContainText('Deposit successful');
        await expect(page.locator(SELECTORS.CASH_BALANCE_DISPLAY)).toContainText('100.0001');
    });
});

test.describe('2. Trading and Price Lookup Tests', () => {

    // Setup: Run Demo Scenario once to ensure a complex, non-empty state with funds, holdings, and history.
    test.beforeAll(async ({ page }) => {
        await page.goto(BASE_URL);
        await page.locator(SELECTORS.TAB_DEMO).click();
        await page.locator(SELECTORS.RUN_DEMO_BUTTON).click();
        await expect(page.locator(SELECTORS.DEMO_RESULTS)).toContainText('Demo scenario finished successfully.');
    });

    test.beforeEach(async ({ page }) => {
        await page.locator(SELECTORS.TAB_TRADING).click();
    });

    test.describe('Price Retrieval (TC_PRICE_P/N)', () => {
        const supportedSymbols = ['AAPL', 'GOOGL', 'XOM'];

        for (const symbol of supportedSymbols) {
            test(`TC_PRICE_P_001: Successful Price Retrieval for ${symbol}`, async ({ page }) => {
                await page.locator(SELECTORS.SYMBOL_INPUT).fill(symbol);
                await page.locator(SELECTORS.GET_PRICE_BUTTON).click();
                
                const priceValue = await page.locator(SELECTORS.PRICE_OUTPUT).inputValue();
                
                expect(priceValue).toMatch(/^\$[0-9]+(\.[0-9]+)?$/);
                expect(parseFloat(priceValue.replace('$', ''))).toBeGreaterThan(0);
            });
        }

        test('TC_PRICE_N_002: Failed Price Retrieval for Unsupported Symbol', async ({ page }) => {
            await page.locator(SELECTORS.SYMBOL_INPUT).fill('BAD_SYM');
            await page.locator(SELECTORS.GET_PRICE_BUTTON).click();
            
            await expect(page.locator(SELECTORS.PRICE_OUTPUT)).toHaveValue(/N\/A|error|invalid/i);
        });
    });

    test.describe('Trading Execution (TC_TRADE_P/N)', () => {
        
        test('TC_TRADE_P_001: Successful Buy Order', async ({ page }) => {
            const initialCashText = await page.locator(SELECTORS.CASH_BALANCE_DISPLAY).inputValue();
            const initialCash = parseFloat(initialCashText.replace(/[$,]/g, ''));
            
            await page.locator(SELECTORS.SYMBOL_INPUT).fill('AAPL');
            await page.locator(SELECTORS.GET_PRICE_BUTTON).click();
            const priceText = await page.locator(SELECTORS.PRICE_OUTPUT).inputValue();
            const priceAAPL = parseFloat(priceText.replace('$', '')); 
            
            const quantity = 5;
            const expectedCost = quantity * priceAAPL;

            await page.locator(SELECTORS.BUY_QUANTITY_INPUT).fill(quantity.toString());
            await page.locator(SELECTORS.BUY_BUTTON).click();

            await expect(page.locator(SELECTORS.BUY_RESULT)).toContainText('Buy order executed');
            const expectedCash = (initialCash - expectedCost).toFixed(2);
            await expect(page.locator(SELECTORS.CASH_BALANCE_DISPLAY)).toContainText(expectedCash);
        });
        
        test('TC_TRADE_P_003: Successful Sell Order (TSLA)', async ({ page }) => {
            const initialCashText = await page.locator(SELECTORS.CASH_BALANCE_DISPLAY).inputValue();
            const initialCash = parseFloat(initialCashText.replace(/[$,]/g, ''));

            await page.locator(SELECTORS.SYMBOL_INPUT).fill('TSLA');
            await page.locator(SELECTORS.GET_PRICE_BUTTON).click();
            const priceText = await page.locator(SELECTORS.PRICE_OUTPUT).inputValue();
            const priceTSLA = parseFloat(priceText.replace('$', '')); 
            
            const quantity = 5;
            const expectedProceeds = quantity * priceTSLA;

            await page.locator(SELECTORS.SELL_QUANTITY_INPUT).fill(quantity.toString());
            await page.locator(SELECTORS.SELL_BUTTON).click();

            await expect(page.locator(SELECTORS.SELL_RESULT)).toContainText('Sell order executed');
            const expectedCash = (initialCash + expectedProceeds).toFixed(2);
            await expect(page.locator(SELECTORS.CASH_BALANCE_DISPLAY)).toContainText(expectedCash);
        });

        test('TC_TRADE_N_004: Failed Sell Order due to Insufficient Holdings (Short Selling)', async ({ page }) => {
            await page.locator(SELECTORS.TAB_TRADING).click();
            const initialCash = await page.locator(SELECTORS.CASH_BALANCE_DISPLAY).inputValue();

            await page.locator(SELECTORS.SYMBOL_INPUT).fill('TSLA');
            await page.locator(SELECTORS.SELL_QUANTITY_INPUT).fill('1000'); 
            await page.locator(SELECTORS.SELL_BUTTON).click();

            await expect(page.locator(SELECTORS.SELL_RESULT)).toContainText('Insufficient holdings for TSLA');
            await expect(page.locator(SELECTORS.CASH_BALANCE_DISPLAY)).toHaveValue(initialCash);
        });

        test('TC_TRADE_N_006 / TS-TR-08: Failed Trade Attempt with Negative Quantity (Buy)', async ({ page }) => {
            const initialCash = await page.locator(SELECTORS.CASH_BALANCE_DISPLAY).inputValue();

            await page.locator(SELECTORS.SYMBOL_INPUT).fill('AAPL');
            await page.locator(SELECTORS.BUY_QUANTITY_INPUT).fill('-10');
            await page.locator(SELECTORS.BUY_BUTTON).click();

            await expect(page.locator(SELECTORS.BUY_RESULT)).toContainText('Quantity must be positive');
            await expect(page.locator(SELECTORS.CASH_BALANCE_DISPLAY)).toHaveValue(initialCash);
        });
    });
});

test.describe('3. Reporting and History Tests', () => {

    test('TC_RPT_P_001: Successful Portfolio Summary Calculation (P&L verification)', async ({ page }) => {
        await page.locator(SELECTORS.TAB_PORTFOLIO).click();
        await page.locator(SELECTORS.REFRESH_PORTFOLIO_BUTTON).click();

        const summaryText = await page.locator(SELECTORS.PORTFOLIO_SUMMARY).inputValue();

        await expect(summaryText).toContain('Current Cash Balance: $');
        await expect(summaryText).toContain('Total Market Value: $');
        await expect(summaryText).toContain('Total Portfolio Value: $');
        await expect(summaryText).toContain('Profit/Loss (P&L): $');
    });

    test('TC_RPT_P_002: Detailed Holdings Report Verification', async ({ page }) => {
        await page.locator(SELECTORS.TAB_PORTFOLIO).click();
        await page.locator(SELECTORS.REFRESH_PORTFOLIO_BUTTON).click();

        const holdingsText = await page.locator(SELECTORS.CURRENT_HOLDINGS).inputValue();

        await expect(holdingsText).toContain('AAPL');
        await expect(holdingsText).toContain('TSLA');
        
        await expect(holdingsText).toMatch(/Symbol\s+Quantity\s+Cost Basis/);
    });

    test('TC_RPT_P_003: Viewing comprehensive Transaction History', async ({ page }) => {
        await page.locator(SELECTORS.TAB_HISTORY).click();
        await page.locator(SELECTORS.REFRESH_HISTORY_BUTTON).click();

        const historyText = await page.locator(SELECTORS.TRANSACTION_HISTORY).inputValue();
        
        await expect(historyText).toContain('DEPOSIT');
        await expect(historyText).toContain('BUY');
        await expect(historyText).toContain('WITHDRAWAL');
        await expect(historyText).toContain('SELL');
        
        const transactionLines = historyText.trim().split('\n').filter(line => line.trim() !== '');
        expect(transactionLines.length).toBeGreaterThanOrEqual(8); 
    });
});