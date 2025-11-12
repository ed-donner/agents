import { test, expect, Page, Locator } from '@playwright/test';

const BASE_URL = 'http://127.0.0.1:7860';

// =========================================================================
// LOCATORS (Based on Gradio Component IDs)
// =========================================================================

// Tabs
const FUNDS_TAB = '[data-tab-id="4"]';
const TRADING_TAB = '[data-tab-id="21"]';
const PORTFOLIO_TAB = '[data-tab-id="46"]';
const HISTORY_TAB = '[data-tab-id="53"]';
const DEMO_TAB = '[data-tab-id="58"]';

// Global
const CASH_BALANCE_OUTPUT = '[id="component-2"] textarea';

// Funds (ID 4)
const DEPOSIT_AMOUNT_INPUT = '[id="component-9"] textarea';
const DEPOSIT_BUTTON = '[id="component-10"]';
const DEPOSIT_RESULT_OUTPUT = '[id="component-11"] textarea';
const WITHDRAW_AMOUNT_INPUT = '[id="component-16"] textarea';
const WITHDRAW_BUTTON = '[id="component-17"]';
const WITHDRAW_RESULT_OUTPUT = '[id="component-18"] textarea';

// Trading (ID 21)
const BUY_SYMBOL_DROPDOWN_INPUT = '[id="component-26"] input'; 
const BUY_QUANTITY_INPUT = '[id="component-27"] textarea';
const BUY_BUTTON = '[id="component-28"]';
const BUY_RESULT_OUTPUT = '[id="component-29"] textarea';

const SELL_SYMBOL_DROPDOWN_INPUT = '[id="component-34"] input'; 
const SELL_QUANTITY_INPUT = '[id="component-35"] textarea';
const SELL_BUTTON = '[id="component-36"]';
const SELL_RESULT_OUTPUT = '[id="component-37"] textarea';

const PRICE_SYMBOL_DROPDOWN_INPUT = '[id="component-41"] input';
const GET_PRICE_BUTTON = '[id="component-42"]';
const PRICE_OUTPUT = '[id="component-43"] textarea';

// Portfolio (ID 46)
const REFRESH_PORTFOLIO_BUTTON = '[id="component-48"]';
const PORTFOLIO_SUMMARY_OUTPUT = '[id="component-50"] textarea';
const CURRENT_HOLDINGS_OUTPUT = '[id="component-51"] textarea';

// Transaction History (ID 53)
const REFRESH_HISTORY_BUTTON = '[id="component-55"]';
const HISTORY_OUTPUT = '[id="component-56"] textarea';

// Demo (ID 58)
const RUN_DEMO_BUTTON = '[id="component-60"]';
const DEMO_RESULTS_OUTPUT = '[id="component-61"] textarea';


// =========================================================================
// HELPERS / SETUP
// =========================================================================

async function navigateToTab(page: Page, tabSelector: string) {
    await page.locator(tabSelector).click();
    await page.waitForTimeout(100); 
}

/** Resets state by running the demo scenario on a clean state (which the backend handles implicitly), 
 * and then deposits a specific amount, navigating to Funds tab. */
async function clearAndDeposit(page: Page, amount: string) {
    // 1. Reset state
    await navigateToTab(page, DEMO_TAB);
    await page.locator(RUN_DEMO_BUTTON).click();
    await expect(page.locator(DEMO_RESULTS_OUTPUT)).toContainText(/Account reset/i, { timeout: 10000 });

    // 2. Navigate to Funds tab and Deposit
    await navigateToTab(page, FUNDS_TAB);

    await page.locator(DEPOSIT_AMOUNT_INPUT).fill(amount);
    await page.locator(DEPOSIT_BUTTON).click();
    await expect(page.locator(DEPOSIT_RESULT_OUTPUT)).toContainText('Deposit successful', { timeout: 5000 });
}

/** Helper to select a symbol in a Gradio dropdown input field */
async function selectSymbol(page: Page, inputLocator: string, symbol: string) {
    await page.locator(inputLocator).fill(symbol);
    await page.waitForTimeout(50);
}

/** Checks cash balance without navigation */
async function checkCashBalance(page: Page, expectedBalance: string) {
    // Assuming the balance output is always formatted as $X.XXXX
    await expect(page.locator(CASH_BALANCE_OUTPUT)).toHaveValue(`$${expectedBalance.replace(',', '')}`);
}

// =========================================================================
// FEATURE: Funds Management (TEST_FUNDS.feature)
// =========================================================================

test.describe('Funds Management - Deposit and Withdrawal Operations', () => {

    test.beforeEach(async ({ page }) => {
        await page.goto(BASE_URL);
        // Ensure starting state is clean/reset (0.0000 balance)
        await navigateToTab(page, DEMO_TAB);
        await page.locator(RUN_DEMO_BUTTON).click();
        // await expect(page.locator(DEMO_RESULTS_OUTPUT)).toContainText(/Account reset/i, { timeout: 10000 });
        
        await navigateToTab(page, FUNDS_TAB);
    });

    test.describe('FND-POS-001: Successful Deposit and Boundary Checks', () => {
        
        // Note: These tests run sequentially to maintain state
        const deposits = [
            { amount: '10000.00', expected: '10000.0000', id: 'FND-POS-001a' },
            { amount: '0.01', expected: '10000.0100', id: 'FND-POS-001b' }, 
            { amount: '999999.9999', expected: '1009999.9999', id: 'FND-POS-001c' },
        ];

        test(`Test ID: ${deposits[0].id} - Standard positive deposit`, async ({ page }) => {
            await page.locator(DEPOSIT_AMOUNT_INPUT).fill(deposits[0].amount);
            await page.locator(DEPOSIT_BUTTON).click();
            await expect(page.locator(DEPOSIT_RESULT_OUTPUT)).toContainText('Deposit successful');
            await checkCashBalance(page, deposits[0].expected);
        });
        
        test(`Test ID: ${deposits[1].id} - Minimum positive deposit boundary`, async ({ page }) => {
            await page.locator(DEPOSIT_AMOUNT_INPUT).fill(deposits[1].amount);
            await page.locator(DEPOSIT_BUTTON).click();
            await expect(page.locator(DEPOSIT_RESULT_OUTPUT)).toContainText('Deposit successful');
            await checkCashBalance(page, deposits[1].expected);
        });

        test(`Test ID: ${deposits[2].id} - High precision deposit check`, async ({ page }) => {
            await page.locator(DEPOSIT_AMOUNT_INPUT).fill(deposits[2].amount);
            await page.locator(DEPOSIT_BUTTON).click();
            await expect(page.locator(DEPOSIT_RESULT_OUTPUT)).toContainText('Deposit successful');
            await checkCashBalance(page, deposits[2].expected);
        });
    });

    test.describe('FND-NEG-002: Invalid and Non-Positive Deposit Attempts', () => {
        
        test.beforeEach(async ({ page }) => {
            await clearAndDeposit(page, '1000.00');
            await checkCashBalance(page, '1000.0000');
            await navigateToTab(page, FUNDS_TAB); 
            await page.locator(DEPOSIT_RESULT_OUTPUT).fill(''); 
        });

        const invalidDeposits = [
            { amount: '0', error: 'Amount must be positive', id: 'FND-NEG-002a' },
            { amount: '-500.00', error: 'Amount must be positive', id: 'FND-NEG-002b' },
            { amount: 'invalid_text', error: 'Invalid input format', id: 'FND-NEG-002c' },
            { amount: '100,000', error: 'Invalid input format', id: 'FND-NEG-002d' },
        ];

        for (const { amount, error, id } of invalidDeposits) {
            test(`Test ID: ${id} - Deposit ${amount} fails`, async ({ page }) => {
                await page.locator(DEPOSIT_AMOUNT_INPUT).fill(amount);
                await page.locator(DEPOSIT_BUTTON).click();

                await expect(page.locator(DEPOSIT_RESULT_OUTPUT)).toContainText(error);
                await checkCashBalance(page, '1000.0000');
            });
        }
    });

    test.describe('FND-POS-003: Successful Withdrawal and Boundary Check', () => {
        
        const validWithdrawals = [
            { amount: '100.00', expected: '400.0000', id: 'FND-POS-003a' },
            { amount: '500.00', expected: '0.0000', id: 'FND-POS-003b' }, 
            { amount: '0.01', expected: '499.9900', id: 'FND-POS-003c' }, 
        ];

        for (const { amount, expected, id } of validWithdrawals) {
            test(`Test ID: ${id} - Withdraw ${amount}`, async ({ page }) => {
                // Setup: Initial balance of 500.0000
                await clearAndDeposit(page, '500.00');
                await navigateToTab(page, FUNDS_TAB);

                await page.locator(WITHDRAW_AMOUNT_INPUT).fill(amount);
                await page.locator(WITHDRAW_BUTTON).click();
                await expect(page.locator(WITHDRAW_RESULT_OUTPUT)).toContainText('Withdrawal successful');
                await checkCashBalance(page, expected);
            });
        }
    });

    test.describe('FND-NEG-004: Withdrawal Failure - Overdraft Protection', () => {
        
        test.beforeEach(async ({ page }) => {
            await clearAndDeposit(page, '100.00');
            await checkCashBalance(page, '100.0000');
            await navigateToTab(page, FUNDS_TAB);
            await page.locator(WITHDRAW_RESULT_OUTPUT).fill('');
        });

        const overdraftAttempts = [
            { amount: '100.01', id: 'FND-NEG-004a' },
            { amount: '500.00', id: 'FND-NEG-004b' },
        ];

        for (const { amount, id } of overdraftAttempts) {
            test(`Test ID: ${id} - Attempt to withdraw ${amount} (Overdraft)`, async ({ page }) => {
                await page.locator(WITHDRAW_AMOUNT_INPUT).fill(amount);
                await page.locator(WITHDRAW_BUTTON).click();

                await expect(page.locator(WITHDRAW_RESULT_OUTPUT)).toContainText('Insufficient funds');
                await checkCashBalance(page, '100.0000');
            });
        }
    });

    test.describe('FND-NEG-005: Invalid Withdrawal Amounts', () => {
        
        test.beforeEach(async ({ page }) => {
            await clearAndDeposit(page, '1000.00');
            await checkCashBalance(page, '1000.0000');
            await navigateToTab(page, FUNDS_TAB);
            await page.locator(WITHDRAW_RESULT_OUTPUT).fill('');
        });

        const invalidWithdrawals = [
            { amount: '0', error: 'Amount must be positive', id: 'FND-NEG-005a' },
            { amount: '-10.00', error: 'Amount must be positive', id: 'FND-NEG-005b' },
            { amount: '10.00.00', error: 'Invalid input format', id: 'FND-NEG-005c' },
        ];

        for (const { amount, error, id } of invalidWithdrawals) {
            test(`Test ID: ${id} - Withdraw ${amount} fails`, async ({ page }) => {
                await page.locator(WITHDRAW_AMOUNT_INPUT).fill(amount);
                await page.locator(WITHDRAW_BUTTON).click();

                await expect(page.locator(WITHDRAW_RESULT_OUTPUT)).toContainText(error);
                await checkCashBalance(page, '1000.0000');
            });
        }
    });
});

// =========================================================================
// FEATURE: Trading Operations (TEST_TRADING.feature)
// =========================================================================

test.describe('Trading Operations - Buy, Sell, and Price Retrieval', () => {

    test.beforeEach(async ({ page }) => {
        await clearAndDeposit(page, '10000.00'); 
        await navigateToTab(page, TRADING_TAB);
    });

    test.describe('TRD-POS-006: Successful Stock Price Retrieval', () => {
        
        const symbols = ['AAPL', 'GOOGL', 'XOM'];

        for (const symbol of symbols) {
            test(`TRD-POS-006: Get price for ${symbol}`, async ({ page }) => {
                await selectSymbol(page, PRICE_SYMBOL_DROPDOWN_INPUT, symbol);
                await page.locator(GET_PRICE_BUTTON).click();

                await expect(page.locator(PRICE_OUTPUT)).not.toHaveValue('', { timeout: 10000 });
                
                const priceValue = await page.locator(PRICE_OUTPUT).inputValue();
                expect(priceValue).toMatch(/^\$[0-9]+\.[0-9]{2,}$/);
                expect(parseFloat(priceValue.substring(1))).toBeGreaterThan(0);
            });
        }
    });

    test('TRD-NEG-007: Price Retrieval Failure for Invalid Symbol', async ({ page }) => {
        await selectSymbol(page, PRICE_SYMBOL_DROPDOWN_INPUT, 'BAD');
        await page.locator(GET_PRICE_BUTTON).click();

        await expect(page.locator(PRICE_OUTPUT)).toContainText('Invalid or unsupported share symbol', { timeout: 5000 });
    });


    test.describe('TRD-POS-008: Successful Buy Order (Sufficient Funds)', () => {

        test('TRD-POS-008a: Standard Purchase (MSFT 100)', async ({ page }) => {
            // Cost: 50 * 100 = 5000. Expected: 5000.0000
            await selectSymbol(page, BUY_SYMBOL_DROPDOWN_INPUT, 'MSFT');
            await page.locator(BUY_QUANTITY_INPUT).fill('100');
            await page.locator(BUY_BUTTON).click();

            await expect(page.locator(BUY_RESULT_OUTPUT)).toContainText('Buy order executed successfully');
            await checkCashBalance(page, '5000.0000');
            
            await navigateToTab(page, PORTFOLIO_TAB);
            await page.locator(REFRESH_PORTFOLIO_BUTTON).click();
            await expect(page.locator(CURRENT_HOLDINGS_OUTPUT)).toContainText('MSFT | 100'); 
        });

        test('TRD-POS-008b: Buying exact remaining balance (AMD 200)', async ({ page }) => {
            await clearAndDeposit(page, '10000.00'); 
            await navigateToTab(page, TRADING_TAB);
            
            // Cost: 50 * 200 = 10000. Expected: 0.0000
            await selectSymbol(page, BUY_SYMBOL_DROPDOWN_INPUT, 'AMD');
            await page.locator(BUY_QUANTITY_INPUT).fill('200');
            await page.locator(BUY_BUTTON).click();

            await expect(page.locator(BUY_RESULT_OUTPUT)).toContainText('Buy order executed successfully');
            await checkCashBalance(page, '0.0000');
            
            await navigateToTab(page, PORTFOLIO_TAB);
            await page.locator(REFRESH_PORTFOLIO_BUTTON).click();
            await expect(page.locator(CURRENT_HOLDINGS_OUTPUT)).toContainText('AMD | 200'); 
        });
    });

    test.describe('TRD-NEG-009: Buy Order Failure - Insufficient Funds', () => {
        
        test.beforeEach(async ({ page }) => {
            await clearAndDeposit(page, '499.00');
            await navigateToTab(page, TRADING_TAB);
            await page.locator(BUY_RESULT_OUTPUT).fill('');
            await selectSymbol(page, BUY_SYMBOL_DROPDOWN_INPUT, 'TSLA');
        });

        const insufficientBuys = [
            { quantity: '10', id: 'TRD-NEG-009a' },
            { quantity: '100', id: 'TRD-NEG-009b' },
        ];

        for (const { quantity, id } of insufficientBuys) {
            test(`Test ID: ${id} - Buy ${quantity} TSLA (Insufficient Funds)`, async ({ page }) => {
                await page.locator(BUY_QUANTITY_INPUT).fill(quantity);
                await page.locator(BUY_BUTTON).click();

                await expect(page.locator(BUY_RESULT_OUTPUT)).toContainText('Insufficient funds to cover trade cost');
                await checkCashBalance(page, '499.0000');
            });
        }
    });

    test.describe('TRD-NEG-010: Buy Order Failure - Invalid Input and Symbol', () => {
        
        test.beforeEach(async ({ page }) => {
            await clearAndDeposit(page, '1000.00');
            await navigateToTab(page, TRADING_TAB);
            await page.locator(BUY_RESULT_OUTPUT).fill('');
        });

        const invalidBuys = [
            { symbol: 'NOT_SUPPORTED', quantity: '10', error: 'Invalid or unsupported share symbol', id: 'TRD-NEG-010a' },
            { symbol: 'AAPL', quantity: '0', error: 'Quantity must be positive', id: 'TRD-NEG-010b' },
            { symbol: 'AAPL', quantity: '-5', error: 'Quantity must be positive', id: 'TRD-NEG-010c' },
            { symbol: 'AAPL', quantity: '1.5', error: 'Quantity must be an integer', id: 'TRD-NEG-010d' },
        ];

        for (const { symbol, quantity, error, id } of invalidBuys) {
            test(`Test ID: ${id} - Invalid Buy: Symbol: ${symbol}, Qty: ${quantity}`, async ({ page }) => {
                await selectSymbol(page, BUY_SYMBOL_DROPDOWN_INPUT, symbol);
                await page.locator(BUY_QUANTITY_INPUT).fill(quantity);
                await page.locator(BUY_BUTTON).click();

                await expect(page.locator(BUY_RESULT_OUTPUT)).toContainText(error);
                await checkCashBalance(page, '1000.0000');
            });
        }
    });

    test.describe('TRD-POS-011: Successful Sell Order', () => {
        
        test.beforeEach(async ({ page }) => {
            const initialDeposit = '1700.00'; 
            await clearAndDeposit(page, initialDeposit); 
            await navigateToTab(page, TRADING_TAB);
            
            // Buy 20 AAPL (Cost 1200 @ $60/share assumed) -> Cash 500.0000
            await selectSymbol(page, BUY_SYMBOL_DROPDOWN_INPUT, 'AAPL');
            await page.locator(BUY_QUANTITY_INPUT).fill('20');
            await page.locator(BUY_BUTTON).click();
            await expect(page.locator(BUY_RESULT_OUTPUT)).toContainText('Buy order executed successfully');
            
            await checkCashBalance(page, '500.0000');
            await navigateToTab(page, TRADING_TAB);
            await page.locator(SELL_RESULT_OUTPUT).fill('');
        });


        test('TRD-POS-011a: Partial Sale (5 AAPL)', async ({ page }) => {
            // Sell 5 AAPL @ $60/share assumed = $300 proceeds. Expected balance: 800.0000
            await selectSymbol(page, SELL_SYMBOL_DROPDOWN_INPUT, 'AAPL');
            await page.locator(SELL_QUANTITY_INPUT).fill('5');
            await page.locator(SELL_BUTTON).click();

            await expect(page.locator(SELL_RESULT_OUTPUT)).toContainText('Sell order executed successfully');
            await checkCashBalance(page, '800.0000');

            await navigateToTab(page, PORTFOLIO_TAB);
            await page.locator(REFRESH_PORTFOLIO_BUTTON).click();
            await expect(page.locator(CURRENT_HOLDINGS_OUTPUT)).toContainText('AAPL | 15');
        });

        test('TRD-POS-011b: Partial Sale (15 AAPL)', async ({ page }) => {
            // Sell 15 AAPL @ $60/share assumed = $900 proceeds. Expected balance: 1400.0000
            await selectSymbol(page, SELL_SYMBOL_DROPDOWN_INPUT, 'AAPL');
            await page.locator(SELL_QUANTITY_INPUT).fill('15');
            await page.locator(SELL_BUTTON).click();

            await expect(page.locator(SELL_RESULT_OUTPUT)).toContainText('Sell order executed successfully');
            await checkCashBalance(page, '1400.0000'); 

            await navigateToTab(page, PORTFOLIO_TAB);
            await page.locator(REFRESH_PORTFOLIO_BUTTON).click();
            await expect(page.locator(CURRENT_HOLDINGS_OUTPUT)).toContainText('AAPL | 5');
        });
    });

    test.describe('TRD-NEG-012: Sell Order Failure - Insufficient Holdings', () => {

        test.beforeEach(async ({ page }) => {
            // Setup: 10 XOM holdings, $1000.0000 cash balance. (Implied Buy Price: 50)
            const initialDeposit = '1500.00'; 
            await clearAndDeposit(page, initialDeposit); 
            await navigateToTab(page, TRADING_TAB);
            
            await selectSymbol(page, BUY_SYMBOL_DROPDOWN_INPUT, 'XOM');
            await page.locator(BUY_QUANTITY_INPUT).fill('10');
            await page.locator(BUY_BUTTON).click();
            
            await checkCashBalance(page, '1000.0000');
            
            await navigateToTab(page, TRADING_TAB);
            await page.locator(SELL_RESULT_OUTPUT).fill('');
        });

        const insufficientSells = [
            { symbol: 'XOM', quantity: '11', id: 'TRD-NEG-012a' },
            { symbol: 'MSFT', quantity: '1', id: 'TRD-NEG-012b' },
        ];

        for (const { symbol, quantity, id } of insufficientSells) {
            test(`Test ID: ${id} - Sell ${quantity} ${symbol} (Insufficient Holdings)`, async ({ page }) => {
                await selectSymbol(page, SELL_SYMBOL_DROPDOWN_INPUT, symbol);
                await page.locator(SELL_QUANTITY_INPUT).fill(quantity);
                await page.locator(SELL_BUTTON).click();

                await expect(page.locator(SELL_RESULT_OUTPUT)).toContainText(`Insufficient holdings for ${symbol}`);
                await checkCashBalance(page, '1000.0000');
            });
        }
    });

});


// =========================================================================
// FEATURE: Portfolio Reporting and Transaction History (TEST_REPORTING.feature)
// =========================================================================

test.describe('Reporting and Transaction History', () => {

    test.beforeEach(async ({ page }) => {
        // --- Setup Complex Transaction History for RPT tests ---
        await page.goto(BASE_URL);

        // Reset state
        await navigateToTab(page, DEMO_TAB);
        await page.locator(RUN_DEMO_BUTTON).click();
        await expect(page.locator(DEMO_RESULTS_OUTPUT)).toContainText(/Account reset/i, { timeout: 10000 });
        
        // 1. Deposit 10000.00
        await navigateToTab(page, FUNDS_TAB);
        await page.locator(DEPOSIT_AMOUNT_INPUT).fill('10000.00');
        await page.locator(DEPOSIT_BUTTON).click();
        
        // 2. Trading
        await navigateToTab(page, TRADING_TAB);

        // Buy AAPL 20 (Cost: 3000 @ 150)
        await selectSymbol(page, BUY_SYMBOL_DROPDOWN_INPUT, 'AAPL');
        await page.locator(BUY_QUANTITY_INPUT).fill('20');
        await page.locator(BUY_BUTTON).click();

        // Buy GOOGL 10 (Cost: 2500 @ 250)
        await selectSymbol(page, BUY_SYMBOL_DROPDOWN_INPUT, 'GOOGL');
        await page.locator(BUY_QUANTITY_INPUT).fill('10');
        await page.locator(BUY_BUTTON).click();
        
        // Sell AAPL 5 (Proceeds: 800 @ 160)
        await selectSymbol(page, SELL_SYMBOL_DROPDOWN_INPUT, 'AAPL');
        await page.locator(SELL_QUANTITY_INPUT).fill('5');
        await page.locator(SELL_BUTTON).click();

        // 3. Withdraw 1000.00
        await navigateToTab(page, FUNDS_TAB);
        await page.locator(WITHDRAW_AMOUNT_INPUT).fill('1000.00');
        await page.locator(WITHDRAW_BUTTON).click();
        
        // Final Cash Check: 4300.0000
        await checkCashBalance(page, '4300.0000');
    });

    test('RPT-POS-013: Verify Comprehensive Portfolio Calculation and P&L', async ({ page }) => {
        
        await navigateToTab(page, PORTFOLIO_TAB);
        await page.locator(REFRESH_PORTFOLIO_BUTTON).click();
        
        const summary = page.locator(PORTFOLIO_SUMMARY_OUTPUT);
        
        await expect(summary).toContainText('Current Cash Balance | $4,300.00');
        await expect(summary).toContainText('Market Value | $5,000.00'); 
        await expect(summary).toContainText('Total Portfolio Value | $9,300.00'); 
        await expect(summary).toContainText('Total Deposits Base | $10,000.00');
        await expect(summary).toContainText('P&L | -$700.00'); 

        const holdings = page.locator(CURRENT_HOLDINGS_OUTPUT);
        await expect(holdings).toContainText('AAPL | 15'); 
        await expect(holdings).toContainText('GOOGL | 10');
    });

    test('RPT-POS-014: Verify Transaction History Log Content (All Types)', async ({ page }) => {
        
        await navigateToTab(page, HISTORY_TAB);
        await page.locator(REFRESH_HISTORY_BUTTON).click();
        
        const historyText = page.locator(HISTORY_OUTPUT);

        await expect(historyText).toContainText(/Type: DEPOSIT.*Amount: 10000\.00/i);
        await expect(historyText).toContainText(/Type: BUY.*Symbol: AAPL/i); 
        await expect(historyText).toContainText(/Type: BUY.*Symbol: GOOGL/i);
        await expect(historyText).toContainText(/Type: SELL.*Symbol: AAPL/i);
        await expect(historyText).toContainText(/Type: WITHDRAWAL.*Amount: 1000\.00/i);
    });

    test('RPT-POS-015: Portfolio Report for Zero Holdings and Zero Cash', async ({ page }) => {
        // Run a fresh reset test
        await navigateToTab(page, DEMO_TAB);
        await page.locator(RUN_DEMO_BUTTON).click();
        await expect(page.locator(DEMO_RESULTS_OUTPUT)).toContainText(/Account reset/i);
        
        await navigateToTab(page, PORTFOLIO_TAB);
        await page.locator(REFRESH_PORTFOLIO_BUTTON).click();

        await expect(page.locator(PORTFOLIO_SUMMARY_OUTPUT)).toContainText('Total Portfolio Value | $0.00');
        await expect(page.locator(CURRENT_HOLDINGS_OUTPUT)).toContainText(/No current holdings|Empty|0/i);
    });
});


// =========================================================================
// FEATURE: Demo Scenario Execution (TEST_DEMO.feature)
// =========================================================================

test.describe('Demo Scenario Execution', () => {

    test.beforeEach(async ({ page }) => {
        await page.goto(BASE_URL);
        // Ensure initial clean state before demo run
        await navigateToTab(page, DEMO_TAB);
        await page.locator(RUN_DEMO_BUTTON).click();
        await expect(page.locator(DEMO_RESULTS_OUTPUT)).toContainText(/Account reset/i, { timeout: 10000 });
        
        await navigateToTab(page, DEMO_TAB);
    });

    test('DEMO-E2E-016: Successful Execution of Pre-configured Demo Workflow', async ({ page }) => {
        
        await page.locator(RUN_DEMO_BUTTON).click();
        
        // 1. Verify Demo Results success message
        await expect(page.locator(DEMO_RESULTS_OUTPUT)).toContainText('5 required operations were successful', { timeout: 15000 });
        
        // 2. Verify Cash Balance update (non-zero and valid format)
        const finalBalanceValue = await page.locator(CASH_BALANCE_OUTPUT).inputValue();
        expect(finalBalanceValue).toMatch(/^\$[0-9,]+\.[0-9]{4}$/);
        expect(parseFloat(finalBalanceValue.replace('$', '').replace(/,/g, ''))).toBeGreaterThan(0);
        
        // 3. Verify Portfolio Holdings (15 AAPL, 10 TSLA)
        await navigateToTab(page, PORTFOLIO_TAB);
        await page.locator(REFRESH_PORTFOLIO_BUTTON).click();
        
        const holdingsOutput = page.locator(CURRENT_HOLDINGS_OUTPUT);
        await expect(holdingsOutput).toContainText('AAPL | 15');
        await expect(holdingsOutput).toContainText('TSLA | 10');
        
        // 4. Verify Transaction History count
        await navigateToTab(page, HISTORY_TAB);
        await page.locator(REFRESH_HISTORY_BUTTON).click();
        
        const historyValue = await page.locator(HISTORY_OUTPUT).inputValue();
        const transactionLines = historyValue.split('\n').filter(line => line.includes('Type:'));
        
        expect(transactionLines.length).toBeGreaterThanOrEqual(5); 
    });
});