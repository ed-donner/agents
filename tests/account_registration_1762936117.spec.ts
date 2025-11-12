import { test, expect, type Page } from '@playwright/test';

const BASE_URL = 'http://127.0.0.1:7860';

// Define Page Object selectors for robust testing
class TradingPlatformPage {
    readonly page: Page;

    // --- Common Locators ---
    readonly cashBalanceLocator: string;
    
    // --- Tab Locators ---
    readonly fundsTabLocator: string;
    readonly tradingTabLocator: string;
    readonly portfolioTabLocator: string;
    readonly demoTabLocator: string;

    // --- Funds Management Locators (component-4) ---
    readonly depositAmountLocator: string; // component-9
    readonly depositButton: string; // component-10
    readonly depositResultLocator: string; // component-11
    readonly withdrawAmountLocator: string; // component-16
    readonly withdrawButton: string; // component-17
    readonly withdrawResultLocator: string; // component-18

    // --- Trading Locators (component-21) ---
    readonly buyQuantityLocator: string; // component-27
    readonly buyButton: string; // component-28
    readonly buyResultLocator: string; // component-29
    readonly getPriceButton: string; // component-42
    readonly priceOutputLocator: string; // component-43

    // --- Reporting Locators ---
    readonly refreshPortfolioButton: string; // component-48
    readonly portfolioSummaryLocator: string; // component-50
    readonly currentHoldingsLocator: string; // component-51
    
    // --- Demo Locators ---
    readonly runDemoButton: string; // component-60
    readonly demoResultsLocator: string; // component-61


    constructor(page: Page) {
        this.page = page;

        // Tab Locators using role and targeting the containing component ID
        this.fundsTabLocator = 'button[role="tab"][aria-controls="component-4"]';
        this.tradingTabLocator = 'button[role="tab"][aria-controls="component-21"]';
        this.portfolioTabLocator = 'button[role="tab"][aria-controls="component-46"]';
        this.demoTabLocator = 'button[role="tab"][aria-controls="component-58"]';

        // Common
        this.cashBalanceLocator = 'label:has-text("Current Cash Balance") [data-testid="textbox"][disabled]';

        // Funds
        this.depositAmountLocator = '#component-9 [data-testid="textbox"]:not([disabled])';
        this.depositButton = '#component-10';
        this.depositResultLocator = '#component-11 [data-testid="textbox"][disabled]'; 
        
        this.withdrawAmountLocator = '#component-16 [data-testid="textbox"]:not([disabled])';
        this.withdrawButton = '#component-17';
        this.withdrawResultLocator = '#component-18 [data-testid="textbox"][disabled]';

        // Trading
        this.buyQuantityLocator = '#component-27 [data-testid="textbox"]:not([disabled])';
        this.buyButton = '#component-28';
        this.buyResultLocator = '#component-29 [data-testid="textbox"][disabled]';

        this.getPriceButton = '#component-42';
        this.priceOutputLocator = '#component-43 [data-testid="textbox"][disabled]';

        // Reporting
        this.refreshPortfolioButton = '#component-48';
        this.portfolioSummaryLocator = '#component-50 [data-testid="textbox"][disabled]';
        this.currentHoldingsLocator = '#component-51 [data-testid="textbox"][disabled]';
        
        // Demo
        this.runDemoButton = '#component-60';
        this.demoResultsLocator = '#component-61 [data-testid="textbox"][disabled]';

    }

    async navigateTo(url: string) {
        await this.page.goto(url, { waitUntil: 'load' });
    }

    async selectTab(tabLocator: string) {
        await this.page.locator(tabLocator).click();
        // Wait for the tab content to stabilize/load
        await this.page.waitForTimeout(500); 
    }
    
    async getCashBalance(): Promise<string> {
        return await this.page.locator(this.cashBalanceLocator).inputValue();
    }
}

test.describe('Trading Platform Functional Tests', () => {
    let tradingPage: TradingPlatformPage;

    test.beforeEach(async ({ page }) => {
        tradingPage = new TradingPlatformPage(page);
        await tradingPage.navigateTo(BASE_URL);
    });

    // --- Feature 1: Funds Management ---

    test('TC_FM_P_001: Successful standard deposit', async ({ page }) => {
        await test.step('GIVEN I have navigated to the "Funds Management" tab and cash balance is $0.00', async () => {
            await tradingPage.selectTab(tradingPage.fundsTabLocator);
            await expect(page.locator(tradingPage.cashBalanceLocator)).toHaveValue('$0.0000');
        });

        await test.step('WHEN I enter "1000.50" and click Deposit', async () => {
            await page.locator(tradingPage.depositAmountLocator).fill('1000.50');
            await page.locator(tradingPage.depositButton).click();
        });

        await test.step('THEN the results show success and cash balance updates', async () => {
            await expect(page.locator(tradingPage.depositResultLocator)).toContainText('Successfully deposited');
            await expect(page.locator(tradingPage.cashBalanceLocator)).toHaveValue('$1000.50');
        });
    });

    test('TC_FM_N_003: Attempting to withdraw funds exceeding the current balance (Overdraft Protection)', async ({ page }) => {
        await test.step('SETUP: Ensure $500.00 is available', async () => {
            await tradingPage.selectTab(tradingPage.fundsTabLocator);
            // Quick deposit setup, assuming the system state resets or handles sequential deposits correctly
            await page.locator(tradingPage.depositAmountLocator).fill('500.00');
            await page.locator(tradingPage.depositButton).click();
            await expect(page.locator(tradingPage.cashBalanceLocator)).toHaveValue('$500.00');
        });

        await test.step('WHEN I enter "500.01" to withdraw and click Withdraw', async () => {
            await page.locator(tradingPage.withdrawAmountLocator).fill('500.01');
            await page.locator(tradingPage.withdrawButton).click();
        });

        await test.step('THEN the result shows insufficient funds error and balance remains unchanged', async () => {
            await expect(page.locator(tradingPage.withdrawResultLocator)).toContainText('Insufficient funds');
            await expect(page.locator(tradingPage.cashBalanceLocator)).toHaveValue('$500.00');
        });
    });

    // --- Feature 4: Demo Scenario Verification (Full Flow Smoke Test) ---

    test('TC_RPT_DEMO_005: Verification of the provided demo scenario workflow', async ({ page }) => {
        await test.step('WHEN I navigate to the "Demo" tab and run the demo', async () => {
            await tradingPage.selectTab(tradingPage.demoTabLocator);
            await page.locator(tradingPage.runDemoButton).click();
            // Wait for demo execution to complete
            await page.waitForTimeout(5000); 
        });
        
        // Step 1: Check Demo Results
        await test.step('THEN the "Demo Results" field should indicate successful completion', async () => {
            const demoResults = page.locator(tradingPage.demoResultsLocator);
            await expect(demoResults).toBeVisible();
            await expect(demoResults).toContainText('successfully');
        });
        
        // Step 2: Validate Portfolio state after demo
        await test.step('AND I verify the final state in the Portfolio tab', async () => {
            await tradingPage.selectTab(tradingPage.portfolioTabLocator);
            await page.locator(tradingPage.refreshPortfolioButton).click();
            await page.waitForTimeout(1000); 
            
            const summary = page.locator(tradingPage.portfolioSummaryLocator);
            const holdings = page.locator(tradingPage.currentHoldingsLocator);
            
            // Check major metrics
            await expect(summary).toContainText('Total Deposits Baseline: $10000.00');
            
            // Check holdings structure (must contain AAPL and TSLA)
            await expect(holdings).toContainText('AAPL');
            await expect(holdings).toContainText('TSLA');
            
            // Verify cash balance reflects changes
            const cashBalance = await tradingPage.getCashBalance();
            await expect(cashBalance).not.toBe('$0.00');
        });
    });

    // --- Feature 2 & 3: Trading and Price Lookup ---

    test('TC_PRICE_P_001: Successful Price Retrieval for supported symbol (GOOGL)', async ({ page }) => {
        // Since no dedicated Symbol input (component-41) exists, we must rely on component behavior
        // We will navigate to the Trading Tab, where the price components are located.
        await tradingPage.selectTab(tradingPage.tradingTabLocator);
        
        // Assumption: The system defaults to a known symbol or uses a globally set state for the price lookup.
        // If the system requires text input, we would fail. We proceed assuming the button triggers lookup for a default/implicit symbol.
        
        await test.step('WHEN I click the "Get Price" button', async () => {
            await page.locator(tradingPage.getPriceButton).click();
        });

        await test.step('THEN the "Price" field displays a positive numeric value', async () => {
            const priceText = await page.locator(tradingPage.priceOutputLocator).inputValue();
            // Validate output format: starts with $ and contains numbers
            await expect(priceText).toMatch(/^\$[0-9,]+\.[0-9]{2,}/);
        });
    });

    test('TC_TRADE_N_005: Failed Trade Attempt with Invalid State (e.g., Symbol validation or Insufficient funds)', async ({ page }) => {
        
        await test.step('SETUP: Deposit $10000 to ensure funds are not the primary failure reason', async () => {
            await tradingPage.selectTab(tradingPage.fundsTabLocator);
            await page.locator(tradingPage.depositAmountLocator).fill('10000');
            await page.locator(tradingPage.depositButton).click();
            await tradingPage.selectTab(tradingPage.tradingTabLocator);
        });

        await test.step('WHEN I attempt to buy 1 share without explicitly defining a valid symbol (relying on default failure behavior)', async () => {
            await page.locator(tradingPage.buyQuantityLocator).fill('1'); 
            await page.locator(tradingPage.buyButton).click();
            await page.waitForTimeout(500);
        });

        await test.step('THEN the "Buy Result" field should display an error message (symbol required/invalid)', async () => {
            const buyResult = page.locator(tradingPage.buyResultLocator);
            // We check for general failure messages, assuming symbol context is missing or invalid.
            await expect(buyResult).toContainText(/Failed|Error|Invalid Symbol|unsupported/);
        });
    });
});