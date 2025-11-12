import { test, expect, Page } from '@playwright/test';

const BASE_URL = 'http://127.0.0.1:7860';

// Selector Map using Component IDs
const Selectors = {
    CASH_BALANCE: '#component-2 textarea', // ID 2: Current Cash Balance (Read-only)
    
    // Tabs
    TAB_FUNDS_MGMT: 'button[data-tab-id="4"]', // ID 4
    TAB_TRADING: 'button[data-tab-id="21"]', // ID 21
    TAB_PORTFOLIO: 'button[data-tab-id="46"]', // ID 46
    TAB_HISTORY: 'button[data-tab-id="53"]', // ID 53
    TAB_DEMO: 'button[data-tab-id="58"]', // ID 58
    
    // Funds Management (ID 4)
    DEPOSIT_AMOUNT_INPUT: '#component-9 textarea', // ID 9
    DEPOSIT_BUTTON: '#component-10', // ID 10
    DEPOSIT_RESULT: '#component-11 textarea', // ID 11
    
    WITHDRAW_AMOUNT_INPUT: '#component-16 textarea', // ID 16
    WITHDRAW_BUTTON: '#component-17', // ID 17
    WITHDRAW_RESULT: '#component-18 textarea', // ID 18

    // Trading (ID 21) - Buy section
    BUY_SYMBOL_DROPDOWN: '#component-26', // ID 26
    BUY_QUANTITY_INPUT: '#component-27 textarea', // ID 27
    BUY_BUTTON: '#component-28', // ID 28
    BUY_RESULT: '#component-29 textarea', // ID 29

    // Trading (ID 21) - Sell section
    SELL_SYMBOL_DROPDOWN: '#component-34', // ID 34
    SELL_QUANTITY_INPUT: '#component-35 textarea', // ID 35
    SELL_BUTTON: '#component-36', // ID 36
    SELL_RESULT: '#component-37 textarea', // ID 37

    // Trading (ID 21) - Price Lookup
    PRICE_SYMBOL_DROPDOWN: '#component-41', // ID 41
    GET_PRICE_BUTTON: '#component-42', // ID 42
    PRICE_RESULT: '#component-43 textarea', // ID 43

    // Portfolio (ID 46)
    REFRESH_PORTFOLIO_BUTTON: '#component-48', // ID 48
    PORTFOLIO_SUMMARY: '#component-50 textarea', // ID 50
    CURRENT_HOLDINGS: '#component-51 textarea', // ID 51

    // History (ID 53)
    REFRESH_HISTORY_BUTTON: '#component-55', // ID 55
    TRANSACTION_HISTORY: '#component-56 textarea', // ID 56

    // Demo (ID 58)
    RUN_DEMO_BUTTON: '#component-60', // ID 60
    DEMO_RESULTS: '#component-61 textarea', // ID 61
};

// Helper function to set cash balance via deposit (assuming a $0 start for each test session)
async function ensureInitialBalance(page: Page, targetBalance: number) {
    // Clear previous results/inputs for stability
    await page.locator(Selectors.DEPOSIT_AMOUNT_INPUT).fill('');
    await page.locator(Selectors.WITHDRAW_AMOUNT_INPUT).fill('');
    await page.locator(Selectors.DEPOSIT_RESULT).fill('');
    
    if (targetBalance > 0) {
        // Deposit the required amount
        const amountStr = targetBalance.toFixed(4);
        await page.locator(Selectors.DEPOSIT_AMOUNT_INPUT).fill(amountStr);
        await page.locator(Selectors.DEPOSIT_BUTTON).click();
        await expect(page.locator(Selectors.DEPOSIT_RESULT)).toContainText('Successfully deposited');
        
        const expectedBalanceStr = targetBalance.toLocaleString('en-US', { 
            minimumFractionDigits: 4, 
            maximumFractionDigits: 4 
        }).replace(/,/g, ''); // Gradio output might strip commas if balance is low, or keep them if high. We adjust for $1,000.0000 format expectation.
        
        await expect(page.locator(Selectors.CASH_BALANCE)).toContainText(expectedBalanceStr);
    } else {
         // If target is zero, ensure it's zero
         await expect(page.locator(Selectors.CASH_BALANCE)).toHaveValue('$0.0000');
    }
}

test.describe('TRADING_SIMULATION_TEST_SUITE', () => {
    
    test.beforeEach(async ({ page }) => {
        await page.goto(BASE_URL);
    });

    // ====================================================================
    // Feature: 01_Funds_Management
    // ====================================================================

    test.describe('01_Funds_Management (Deposit/Withdrawal)', () => {
        test.beforeEach(async ({ page }) => {
            // Navigate to the Funds Management tab
            await page.locator(Selectors.TAB_FUNDS_MGMT).click();
            // Assuming $0.0000 start due to session isolation
            await expect(page.locator(Selectors.CASH_BALANCE)).toHaveValue('$0.0000');
        });
        
        // --- TC-FM-001_Deposit_HappyPath_Boundary ---
        test.describe('TC-FM-001 Positive Deposit Scenarios', () => {
            const depositCases = [
                { amount: '1000.00', expectedBalance: '$1,000.0000' },
                { amount: '0.01', expectedBalance: '$0.0100' },
                { amount: '99999.99', expectedBalance: '$99,999.9900' },
            ];

            for (const { amount, expectedBalance } of depositCases) {
                test(`Deposit ${amount}`, async ({ page }) => {
                    await page.locator(Selectors.DEPOSIT_AMOUNT_INPUT).fill(amount);
                    await page.locator(Selectors.DEPOSIT_BUTTON).click();
                    await expect(page.locator(Selectors.DEPOSIT_RESULT)).toContainText(`Successfully deposited ${amount}`);
                    await expect(page.locator(Selectors.CASH_BALANCE)).toHaveValue(expectedBalance);

                    // Clean up: Withdraw the deposited amount to reset state for the next isolated test
                    await page.locator(Selectors.WITHDRAW_AMOUNT_INPUT).fill(amount);
                    await page.locator(Selectors.WITHDRAW_BUTTON).click();
                    await expect(page.locator(Selectors.CASH_BALANCE)).toHaveValue('$0.0000');
                });
            }
        });

        // --- TC-FM-002_Deposit_Negative_EdgeCases ---
        test.describe('TC-FM-002 Invalid Deposit Attempts', () => {
            const invalidDepositCases = [
                { amount: '0.00', errorPattern: 'must be positive' },
                { amount: '-10.00', errorPattern: 'must be positive' },
                { amount: '100.00.00', errorPattern: 'invalid numeric format' },
                { amount: 'text_input', errorPattern: 'invalid numeric format' },
            ];
            
            for (const { amount, errorPattern } of invalidDepositCases) {
                test(`Invalid deposit: ${amount}`, async ({ page }) => {
                    await page.locator(Selectors.DEPOSIT_AMOUNT_INPUT).fill(amount);
                    await page.locator(Selectors.DEPOSIT_BUTTON).click();
                    await expect(page.locator(Selectors.DEPOSIT_RESULT)).toContainText(errorPattern);
                    await expect(page.locator(Selectors.CASH_BALANCE)).toHaveValue('$0.0000');
                });
            }
        });

        // --- TC-FM-003_Withdraw_HappyPath_Boundary ---
        test.describe('TC-FM-003 Valid Withdrawal Scenarios', () => {
            const initialBalance = 2000.00;
            
            // Due to state dependency (sequential withdrawals), we group these checks.
            test('Perform sequential valid withdrawals starting from $2000.0000', async ({ page }) => {
                await ensureInitialBalance(page, initialBalance);
                await page.locator(Selectors.DEPOSIT_RESULT).fill('');
                
                // Case 1: Standard withdrawal (2000.00 -> 1500.00)
                await page.locator(Selectors.WITHDRAW_AMOUNT_INPUT).fill('500.00');
                await page.locator(Selectors.WITHDRAW_BUTTON).click();
                await expect(page.locator(Selectors.WITHDRAW_RESULT)).toContainText('Successfully withdrew 500.00');
                await expect(page.locator(Selectors.CASH_BALANCE)).toHaveValue('$1,500.0000');

                // Case 2: Boundary: Exact balance withdrawal (1500.00 -> 0.00)
                await page.locator(Selectors.WITHDRAW_AMOUNT_INPUT).fill('1500.00'); 
                await page.locator(Selectors.WITHDRAW_BUTTON).click();
                await expect(page.locator(Selectors.WITHDRAW_RESULT)).toContainText('Successfully withdrew 1500.00');
                await expect(page.locator(Selectors.CASH_BALANCE)).toHaveValue('$0.0000');
                
                // Reset for Case 3 (2000.00)
                await ensureInitialBalance(page, initialBalance); 
                
                // Case 3: Minimum positive withdrawal (2000.00 -> 1999.99)
                await page.locator(Selectors.WITHDRAW_AMOUNT_INPUT).fill('0.01');
                await page.locator(Selectors.WITHDRAW_BUTTON).click();
                await expect(page.locator(Selectors.WITHDRAW_RESULT)).toContainText('Successfully withdrew 0.01');
                await expect(page.locator(Selectors.CASH_BALANCE)).toHaveValue('$1,999.9900');
            });
        });

        // --- TC-FM-004_Withdraw_Negative_OverdraftProtection ---
        test.describe('TC-FM-004 Invalid Withdrawal Attempts', () => {
            const initialBalance = 100.00;
            const expectedInitialBalanceStr = '$100.0000';
            
            test.beforeEach(async ({ page }) => {
                await ensureInitialBalance(page, initialBalance);
                await page.locator(Selectors.WITHDRAW_RESULT).fill('');
            });

            const invalidWithdrawalCases = [
                { amount: '100.01', errorPattern: /Cannot exceed current balance|Insufficient funds/i },
                { amount: '500.00', errorPattern: /Cannot exceed current balance|Insufficient funds/i },
                { amount: '0.00', errorPattern: 'must be positive' },
                { amount: '-50.00', errorPattern: 'must be positive' },
            ];

            for (const { amount, errorPattern } of invalidWithdrawalCases) {
                test(`Invalid withdrawal: ${amount}`, async ({ page }) => {
                    await page.locator(Selectors.WITHDRAW_AMOUNT_INPUT).fill(amount);
                    await page.locator(Selectors.WITHDRAW_BUTTON).click();
                    
                    await expect(page.locator(Selectors.WITHDRAW_RESULT)).toMatch(errorPattern);
                    await expect(page.locator(Selectors.CASH_BALANCE)).toHaveValue(expectedInitialBalanceStr);
                });
            }
        });
    });

    // ====================================================================
    // Feature: 02_Trading_Operations
    // ====================================================================
    
    test.describe('02_Trading_Operations', () => {
        
        // --- TC-TRD-001_Buy_Affordability_HappyPath ---
        test('TC-TRD-001 Execute valid buy trades', async ({ page }) => {
            // Setup: Deposit $5000.00
            await page.locator(Selectors.TAB_FUNDS_MGMT).click();
            await ensureInitialBalance(page, 5000.00);
            await page.locator(Selectors.TAB_TRADING).click();
            await expect(page.locator(Selectors.CASH_BALANCE)).toHaveValue('$5,000.0000');
            
            // Trade 1: AAPL 10 shares (Assumed price $100.00, Cost $1000)
            await page.locator(Selectors.BUY_SYMBOL_DROPDOWN).selectOption('AAPL');
            await page.locator(Selectors.BUY_QUANTITY_INPUT).fill('10');
            await page.locator(Selectors.BUY_BUTTON).click();
            await expect(page.locator(Selectors.BUY_RESULT)).toContainText('Buy executed');
            await expect(page.locator(Selectors.CASH_BALANCE)).toHaveValue('$4,000.0000');
            
            // Trade 2: XYZ 80 shares (Adjusted to fit remaining $4000 cash, assuming XYZ @ $50.00)
            await page.locator(Selectors.BUY_SYMBOL_DROPDOWN).selectOption('XYZ');
            await page.locator(Selectors.BUY_QUANTITY_INPUT).fill('80'); 
            await page.locator(Selectors.BUY_BUTTON).click();
            await expect(page.locator(Selectors.BUY_RESULT)).toContainText('Buy executed');
            
            // Check cash reduced further (4000 - 4000 = 0.0000, assuming stable $50 price)
            await page.waitForTimeout(500); // Wait for potential async UI update
            await expect(page.locator(Selectors.CASH_BALANCE)).toHaveValue('$0.0000');
        });
        
        // --- TC-TRD-002_Buy_Affordability_Negative_EdgeCases ---
        test.describe('TC-TRD-002 Invalid Buy Attempts', () => {
            const initialBalance = 100.00;
            const expectedInitialBalanceStr = '$100.0000';
            
            test.beforeEach(async ({ page }) => {
                await page.locator(Selectors.TAB_FUNDS_MGMT).click();
                await ensureInitialBalance(page, initialBalance);
                await page.locator(Selectors.TAB_TRADING).click();
                await page.locator(Selectors.BUY_RESULT).fill('');
            });

            const invalidBuyCases = [
                { symbol: 'AAPL', quantity: '2', errorPattern: /Insufficient funds/i }, 
                { symbol: 'AAPL', quantity: '0', errorPattern: /Invalid input|must be positive/i },
                { symbol: 'AAPL', quantity: '-5', errorPattern: /Invalid input|must be positive/i },
            ];

            for (const { symbol, quantity, errorPattern } of invalidBuyCases) {
                test(`Invalid Buy: ${symbol} Qty ${quantity}`, async ({ page }) => {
                    await page.locator(Selectors.BUY_SYMBOL_DROPDOWN).selectOption(symbol);
                    await page.locator(Selectors.BUY_QUANTITY_INPUT).fill(quantity);
                    await page.locator(Selectors.BUY_BUTTON).click();
                    await expect(page.locator(Selectors.BUY_RESULT)).toMatch(errorPattern);
                    await expect(page.locator(Selectors.CASH_BALANCE)).toHaveValue(expectedInitialBalanceStr);
                });
            }
        });

        // --- TC-TRD-003_Sell_Possession_HappyPath ---
        test('TC-TRD-003 Execute valid sell trades', async ({ page }) => {
            // Setup: Deposit 6000.00 cash, buy 50 shares of AAPL ($100 assumed price). Cost $5000. Balance $1000.
            await page.locator(Selectors.TAB_FUNDS_MGMT).click();
            await ensureInitialBalance(page, 6000.00); 
            await page.locator(Selectors.TAB_TRADING).click();

            // Buy 50 AAPL shares 
            await page.locator(Selectors.BUY_SYMBOL_DROPDOWN).selectOption('AAPL');
            await page.locator(Selectors.BUY_QUANTITY_INPUT).fill('50');
            await page.locator(Selectors.BUY_BUTTON).click();
            await expect(page.locator(Selectors.CASH_BALANCE)).toHaveValue('$1,000.0000'); 
            
            // Sale 1: Sell 10 shares of AAPL (Initial Cash 1000.0000. Proceeds ~$1100.00)
            await page.locator(Selectors.SELL_SYMBOL_DROPDOWN).selectOption('AAPL');
            await page.locator(Selectors.SELL_QUANTITY_INPUT).fill('10');
            await page.locator(Selectors.SELL_BUTTON).click();
            await expect(page.locator(Selectors.SELL_RESULT)).toContainText('Sell executed');
            await expect(page.locator(Selectors.CASH_BALANCE)).not.toHaveValue('$1,000.0000'); 
            
            // Sale 2: Sell remaining 40 shares of AAPL 
            await page.locator(Selectors.SELL_QUANTITY_INPUT).fill('40'); 
            await page.locator(Selectors.SELL_BUTTON).click();
            await expect(page.locator(Selectors.SELL_RESULT)).toContainText('Sell executed');
            await expect(page.locator(Selectors.CASH_BALANCE)).toContainText(/\$/);
        });

        // --- TC-TRD-004_Sell_Negative_InsufficientHoldings ---
        test('TC-TRD-004 Verify insufficient holdings failure', async ({ page }) => {
            const initialCash = 1000.00;
            
            // Setup: 1000.00 cash, buy 5 MSFT (Cost $500, Cash $500.0000 remaining)
            await page.locator(Selectors.TAB_FUNDS_MGMT).click();
            await ensureInitialBalance(page, initialCash); 
            await page.locator(Selectors.TAB_TRADING).click();
            
            await page.locator(Selectors.BUY_SYMBOL_DROPDOWN).selectOption('MSFT');
            await page.locator(Selectors.BUY_QUANTITY_INPUT).fill('5');
            await page.locator(Selectors.BUY_BUTTON).click();
            const initialBalanceAfterBuy = await page.locator(Selectors.CASH_BALANCE).inputValue(); 
            await page.locator(Selectors.SELL_RESULT).fill('');
            
            const invalidSellCases = [
                { symbol: 'MSFT', quantity: '6', errorPattern: /Insufficient holdings/i }, 
                { symbol: 'GOOGL', quantity: '10', errorPattern: /Insufficient holdings/i },
                { symbol: 'MSFT', quantity: '0', errorPattern: /Invalid input|must be positive/i },
            ];
            
            for (const { symbol, quantity, errorPattern } of invalidSellCases) {
                await page.locator(Selectors.SELL_SYMBOL_DROPDOWN).selectOption(symbol);
                await page.locator(Selectors.SELL_QUANTITY_INPUT).fill(quantity);
                await page.locator(Selectors.SELL_BUTTON).click();
                
                await expect(page.locator(Selectors.SELL_RESULT)).toMatch(errorPattern);
                await expect(page.locator(Selectors.CASH_BALANCE)).toHaveValue(initialBalanceAfterBuy); 
            }
        });

        // --- TC-TRD-005_PriceLookup_Functionality ---
        test.describe('TC-TRD-005 Price Lookup', () => {
            const symbols = ['AAPL', 'GOOGL', 'XOM'];

            for (const symbol of symbols) {
                test(`Lookup price for ${symbol}`, async ({ page }) => {
                    await page.locator(Selectors.TAB_TRADING).click();
                    await page.locator(Selectors.PRICE_SYMBOL_DROPDOWN).selectOption(symbol);
                    await page.locator(Selectors.GET_PRICE_BUTTON).click();
                    
                    // Price textbox should contain a non-zero, formatted price value
                    const pricePattern = /\$\d{1,3}(,\d{3})*\.\d{4}/;
                    await expect(page.locator(Selectors.PRICE_RESULT)).toMatch(pricePattern);
                });
            }
        });
    });

    // ====================================================================
    // Feature: 03_Reporting_End_to_End_Flows
    // ====================================================================

    test.describe('03_Reporting_End_to_End_Flows', () => {
        
        // --- TC-E2E-003_RunDemoScenario_Functionality --- 
        test('TC-E2E-003 Run Demo Scenario and verify final results', async ({ page }) => {
            await page.locator(Selectors.TAB_DEMO).click();
            await page.locator(Selectors.RUN_DEMO_BUTTON).click();

            // Wait for the last step's success message
            await expect(page.locator(Selectors.DEMO_RESULTS)).toContainText('Withdrawal executed', { timeout: 15000 }); 

            // Verify the sequence
            await expect(page.locator(Selectors.DEMO_RESULTS)).toContainText('Successfully deposited');
            await expect(page.locator(Selectors.DEMO_RESULTS)).toContainText('Buy executed');
            await expect(page.locator(Selectors.DEMO_RESULTS)).toContainText('Sell executed');

            // Final cash balance check (should be non-zero after 5 steps)
            await expect(page.locator(Selectors.CASH_BALANCE)).not.toHaveValue('$0.0000'); 
        });

        // --- TC-RPT-001_Portfolio_Refresh_Calculation --- (Must run demo first)
        test('TC-RPT-001 Portfolio Summary & Holdings verification (Post-Demo)', async ({ page }) => {
            await page.locator(Selectors.TAB_DEMO).click();
            await page.locator(Selectors.RUN_DEMO_BUTTON).click();
            await expect(page.locator(Selectors.DEMO_RESULTS)).toContainText('Withdrawal executed', { timeout: 15000 });

            await page.locator(Selectors.TAB_PORTFOLIO).click();
            await page.locator(Selectors.REFRESH_PORTFOLIO_BUTTON).click();
            
            // Summary checks
            const summaryText = await page.locator(Selectors.PORTFOLIO_SUMMARY).inputValue();
            expect(summaryText).toMatch(/Total Portfolio Value:\s+\$[\d,]+\.\d{4}/i);
            expect(summaryText).toMatch(/Profit\/Loss \(P&L\):\s+[\-\$][\d,]+\.\d{4}/i); 

            // Holdings checks
            const holdingsText = await page.locator(Selectors.CURRENT_HOLDINGS).inputValue();
            
            // AAPL: 15 shares remaining
            expect(holdingsText).toContain('AAPL');
            expect(holdingsText).toMatch(/AAPL\s+\|\s+15\s+\|\s+\$[\d,]+\.\d{4}/);
            
            // TSLA: 10 shares remaining
            expect(holdingsText).toContain('TSLA');
            expect(holdingsText).toMatch(/TSLA\s+\|\s+10\s+\|\s+\$[\d,]+\.\d{4}/);
        });

        // --- TC-RPT-002_TransactionHistory_Verification --- (Must run demo first)
        test('TC-RPT-002 Transaction History verification (Post-Demo)', async ({ page }) => {
            await page.locator(Selectors.TAB_DEMO).click();
            await page.locator(Selectors.RUN_DEMO_BUTTON).click();
            await expect(page.locator(Selectors.DEMO_RESULTS)).toContainText('Withdrawal executed', { timeout: 15000 });
            
            await page.locator(Selectors.TAB_HISTORY).click();
            await page.locator(Selectors.REFRESH_HISTORY_BUTTON).click();

            const historyText = await page.locator(Selectors.TRANSACTION_HISTORY).inputValue();
            
            // Verify types and minimum quantities/amounts
            expect(historyText).toContain('Deposit');
            expect(historyText).toContain('10000.00'); 
            
            expect(historyText).toContain('Buy');
            expect((historyText.match(/Buy/g) || []).length).toBeGreaterThanOrEqual(2);
            
            expect(historyText).toContain('Sell');
            
            expect(historyText).toContain('Withdrawal');
            expect(historyText).toContain('1000.00'); 
            
            // Ensure total count is >= 5
            const activityCount = (historyText.match(/Date: \d{4}-\d{2}-\d{2}/g) || []).length;
            expect(activityCount).toBeGreaterThanOrEqual(5);
        });
    });

    // ====================================================================
    // Feature: 04_Data_Integrity_and_NonFunctional
    // ====================================================================

    test.describe('04_Data_Integrity_and_NonFunctional', () => {
        
        // --- TC-FM-005_Boundary_Precision_Check ---
        test('TC-FM-005 Deposit/Withdrawal Precision Check (4 decimal places)', async ({ page }) => {
            await page.locator(Selectors.TAB_FUNDS_MGMT).click();
            await expect(page.locator(Selectors.CASH_BALANCE)).toHaveValue('$0.0000');
            
            // Deposit 0.0001
            await page.locator(Selectors.DEPOSIT_AMOUNT_INPUT).fill('0.0001');
            await page.locator(Selectors.DEPOSIT_BUTTON).click();
            await expect(page.locator(Selectors.CASH_BALANCE)).toHaveValue('$0.0001');

            // Withdraw 0.0001
            await page.locator(Selectors.WITHDRAW_AMOUNT_INPUT).fill('0.0001');
            await page.locator(Selectors.WITHDRAW_BUTTON).click();
            await expect(page.locator(Selectors.CASH_BALANCE)).toHaveValue('$0.0000');
        });
        
        // --- TC-TRD-006_Boundary_ZeroCashBuy ---
        test('TC-TRD-006 Boundary Check: Buy exactly 1 share consuming all cash ($100)', async ({ page }) => {
            // Setup: Set balance to $100.0000
            await page.locator(Selectors.TAB_FUNDS_MGMT).click();
            await ensureInitialBalance(page, 100.00); 
            await page.locator(Selectors.TAB_TRADING).click();
            
            // Buy 1 share of AAPL (Assumed price $100)
            await page.locator(Selectors.BUY_SYMBOL_DROPDOWN).selectOption('AAPL');
            await page.locator(Selectors.BUY_QUANTITY_INPUT).fill('1');
            await page.locator(Selectors.BUY_BUTTON).click();
            
            await expect(page.locator(Selectors.BUY_RESULT)).toContainText('Buy executed');
            await expect(page.locator(Selectors.CASH_BALANCE)).toHaveValue('$0.0000');
        });

        // --- TC-TRD-007_Boundary_ZeroHoldingsSell ---
        test('TC-TRD-007 Boundary Check: Sell last share, then try to sell again', async ({ page }) => {
            // Setup: Deposit $100.00, buy 1 MSFT (Cash balance: $0.0000)
            await page.locator(Selectors.TAB_FUNDS_MGMT).click();
            await ensureInitialBalance(page, 100.00); 
            await page.locator(Selectors.TAB_TRADING).click();
            
            await page.locator(Selectors.BUY_SYMBOL_DROPDOWN).selectOption('MSFT');
            await page.locator(Selectors.BUY_QUANTITY_INPUT).fill('1');
            await page.locator(Selectors.BUY_BUTTON).click();
            const balanceAfterBuy = await page.locator(Selectors.CASH_BALANCE).inputValue();
            
            // Sell 1 MSFT (Boundary: Selling the last share).
            await page.locator(Selectors.SELL_SYMBOL_DROPDOWN).selectOption('MSFT');
            await page.locator(Selectors.SELL_QUANTITY_INPUT).fill('1');
            await page.locator(Selectors.SELL_BUTTON).click();
            
            await expect(page.locator(Selectors.SELL_RESULT)).toContainText('Sell executed');
            const balanceAfterSell = await page.locator(Selectors.CASH_BALANCE).inputValue();
            expect(balanceAfterSell).not.toEqual(balanceAfterBuy); 
            
            // Attempt to sell 1 MSFT again (Insufficient holdings)
            await page.locator(Selectors.SELL_BUTTON).click();
            await expect(page.locator(Selectors.SELL_RESULT)).toContainText(/Insufficient holdings/i);
            // Cash balance must be unchanged after the failed sell
            await expect(page.locator(Selectors.CASH_BALANCE)).toHaveValue(balanceAfterSell);
        });
    });
});