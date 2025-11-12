import { test, expect, Page } from '@playwright/test';

const BASE_URL = 'http://127.0.0.1:7860';

test.describe('Trading Simulation Platform', () => {

  test.beforeEach(async ({ page }) => {
    await page.goto(BASE_URL);
  });

  test.describe('Feature: Account Registration and Security (FR-ACC-001)', () => {

    test('TS-ACC-001 - Successful User Account Creation', async ({ page }) => {
      const emailInput = page.locator('#component-6').getByTestId('textbox');
      const passwordInput = page.locator('#component-7').getByTestId('password');
      const confirmPasswordInput = page.locator('#component-8').getByTestId('password');
      const createAccountButton = page.locator('#component-9');
      const messagesOutput = page.locator('#component-28').getByTestId('textbox');
      const cashBalanceOutput = page.locator('#component-29').getByTestId('textbox');

      await emailInput.fill('success@user.com');
      await passwordInput.fill('SecureP@ss1');
      await confirmPasswordInput.fill('SecureP@ss1');
      await createAccountButton.click();

      await expect(messagesOutput).toHaveValue(/Account created successfully for success@user.com/);
      await expect(cashBalanceOutput).toHaveValue('0.00');
    });

    test.describe('TS-ACC-002 - Account Creation Validation', () => {
      const testCases = [
        {
          id: 'TS-ACC-002a',
          email: 'existing@user.com',
          password: 'P@ssword123',
          confirmPassword: 'P@ssword123',
          expectedError: 'This email address is already registered.',
        },
        {
          id: 'TS-ACC-002b',
          email: 'mismatch@test.com',
          password: 'Pass123',
          confirmPassword: 'Pass456',
          expectedError: 'Passwords do not match.',
        },
        {
          id: 'TS-ACC-002c',
          email: 'invalid-email',
          password: 'P@ssword123',
          confirmPassword: 'P@ssword123',
          expectedError: 'Please enter a valid email address.',
        },
      ];

      // Precondition: Create the 'existing@user.com' account first
      test.beforeAll(async ({ browser }) => {
        const page = await (await browser.newContext()).newPage();
        await page.goto(BASE_URL);
        await page.locator('#component-6').getByTestId('textbox').fill('existing@user.com');
        await page.locator('#component-7').getByTestId('password').fill('P@ssword123');
        await page.locator('#component-8').getByTestId('password').fill('P@ssword123');
        await page.locator('#component-9').click();
        await expect(page.locator('#component-28').getByTestId('textbox')).toHaveValue(/Account created successfully/);
        await page.close();
      });

      for (const { id, email, password, confirmPassword, expectedError } of testCases) {
        test(`${id} - should fail with error: "${expectedError}"`, async ({ page }) => {
          const emailInput = page.locator('#component-6').getByTestId('textbox');
          const passwordInput = page.locator('#component-7').getByTestId('password');
          const confirmPasswordInput = page.locator('#component-8').getByTestId('password');
          const createAccountButton = page.locator('#component-9');
          const messagesOutput = page.locator('#component-28').getByTestId('textbox');

          await emailInput.fill(email);
          await passwordInput.fill(password);
          await confirmPasswordInput.fill(confirmPassword);
          await createAccountButton.click();

          await expect(messagesOutput).toHaveValue(expectedError);
        });
      }
    });
  });

  test.describe('Feature: Fund Management', () => {

    const createAndLogin = async (page: Page, email: string) => {
      await page.locator('#component-6').getByTestId('textbox').fill(email);
      await page.locator('#component-7').getByTestId('password').fill('TestPass123!');
      await page.locator('#component-8').getByTestId('password').fill('TestPass123!');
      await page.locator('#component-9').click();
      await expect(page.locator('#component-28').getByTestId('textbox')).toHaveValue(/Account created successfully/);
    };

    test.describe('TS-FM-001 - Successful Deposit', () => {
        const depositCases = [
            { id: 'TS-FM-001a', initialBalance: 1000.00, depositAmount: '500.00', expectedBalance: '1500.00' },
            { id: 'TS-FM-001b', initialBalance: 50.75, depositAmount: '0.01', expectedBalance: '50.76' },
            { id: 'TS-FM-001c', initialBalance: 0.00, depositAmount: '1000000.00', expectedBalance: '1000000.00' },
        ];

        for(const { id, initialBalance, depositAmount, expectedBalance } of depositCases) {
            test(`${id} - should correctly handle deposit`, async ({ page }) => {
                await createAndLogin(page, `${id}@fundtest.com`);
                const depositAmountInput = page.getByLabel('Deposit Amount');
                const depositButton = page.locator('#component-12');
                const cashBalanceOutput = page.locator('#component-29').getByTestId('textbox');
                const messagesOutput = page.locator('#component-28').getByTestId('textbox');
                const transactionsOutput = page.locator('#component-34').getByTestId('textbox');

                if (initialBalance > 0) {
                    await depositAmountInput.fill(initialBalance.toString());
                    await depositButton.click();
                }

                await depositAmountInput.fill(depositAmount);
                await depositButton.click();

                await expect(messagesOutput).toHaveValue(/Deposit successful/);
                await expect(cashBalanceOutput).toHaveValue(expectedBalance);
                await expect(transactionsOutput).toContainText(`DEPOSIT: ${parseFloat(depositAmount).toFixed(2)}`);
            });
        }
    });

    test.describe('TS-FM-002 - Deposit Validation', () => {
        const invalidDepositCases = [
            { id: 'TS-FM-002a', depositInput: '0.00', expectedError: 'Deposit amount must be greater than zero.' },
            { id: 'TS-FM-002b', depositInput: '-10.50', expectedError: 'Deposit amount must be a positive number.' },
            { id: 'TS-FM-002c', depositInput: 'abc', expectedError: 'Please enter a valid number.' },
        ];

        for(const { id, depositInput, expectedError } of invalidDepositCases) {
            test(`${id} - should fail with error: "${expectedError}"`, async ({ page }) => {
                await createAndLogin(page, 'depositvalidation@test.com');
                await page.getByLabel('Deposit Amount').fill('500.00');
                await page.locator('#component-12').click();

                const depositAmountInput = page.getByLabel('Deposit Amount');
                const depositButton = page.locator('#component-12');
                const cashBalanceOutput = page.locator('#component-29').getByTestId('textbox');
                const messagesOutput = page.locator('#component-28').getByTestId('textbox');

                await depositAmountInput.fill(depositInput);
                await depositButton.click();

                await expect(messagesOutput).toHaveValue(expectedError);
                await expect(cashBalanceOutput).toHaveValue('500.00');
            });
        }
    });

    test.describe('TS-FM-003 - Withdrawal Scenarios', () => {
        const withdrawalCases = [
            { id: 'TS-FM-003a', initialBalance: '1000.00', withdrawAmount: '100.00', expectedBalance: '900.00', expectedMessage: 'Withdrawal successful.' },
            { id: 'TS-FM-003b', initialBalance: '50.00', withdrawAmount: '50.00', expectedBalance: '0.00', expectedMessage: 'Withdrawal successful.' },
            { id: 'TS-FM-003c', initialBalance: '50.00', withdrawAmount: '50.01', expectedBalance: '50.00', expectedMessage: 'Insufficient cash balance for withdrawal.' },
            { id: 'TS-FM-003d', initialBalance: '50.00', withdrawAmount: '-1.00', expectedBalance: '50.00', expectedMessage: 'Withdrawal amount must be a positive number.' },
        ];

        for(const { id, initialBalance, withdrawAmount, expectedBalance, expectedMessage } of withdrawalCases) {
            test(`${id} - should handle withdrawal correctly`, async ({ page }) => {
                await createAndLogin(page, `${id}@withdrawaltest.com`);
                await page.getByLabel('Deposit Amount').fill(initialBalance);
                await page.locator('#component-12').click();
                await expect(page.locator('#component-29').getByTestId('textbox')).toHaveValue(initialBalance);

                const withdrawAmountInput = page.getByLabel('Withdraw Amount');
                const withdrawButton = page.locator('#component-14');
                const messagesOutput = page.locator('#component-28').getByTestId('textbox');
                const cashBalanceOutput = page.locator('#component-29').getByTestId('textbox');

                await withdrawAmountInput.fill(withdrawAmount);
                await withdrawButton.click();

                await expect(messagesOutput).toHaveValue(expectedMessage);
                await expect(cashBalanceOutput).toHaveValue(expectedBalance);
            });
        }
    });
  });

  test.describe('Feature: Stock Trading', () => {

    async function setupTrader(page: Page, email: string, cash: number) {
        await page.locator('#component-6').getByTestId('textbox').fill(email);
        await page.locator('#component-7').getByTestId('password').fill('TradingPass!1');
        await page.locator('#component-8').getByTestId('password').fill('TradingPass!1');
        await page.locator('#component-9').click();
        await expect(page.locator('#component-28').getByTestId('textbox')).toHaveValue(/Account created successfully/);

        if (cash > 0) {
            await page.getByLabel('Deposit Amount').fill(cash.toString());
            await page.locator('#component-12').click();
            await expect(page.locator('#component-29').getByTestId('textbox')).toHaveValue(cash.toFixed(2));
        }
    }

    test('TS-PTM-001a - Successful stock purchase of new holding', async ({ page }) => {
        await setupTrader(page, 'buytrader-a@test.com', 5000);
        const symbolInput = page.locator('#component-17').getByTestId('textbox');
        const quantityInput = page.getByLabel('Quantity');
        const buyButton = page.locator('#component-21');
        const messagesOutput = page.locator('#component-28').getByTestId('textbox');
        const cashBalanceOutput = page.locator('#component-29').getByTestId('textbox');
        const holdingsOutput = page.locator('#component-30').getByTestId('textbox');

        await symbolInput.fill('AAPL');
        await quantityInput.fill('10');
        await buyButton.click();

        await expect(messagesOutput).toHaveValue('Successfully bought 10 shares of AAPL.');
        await expect(cashBalanceOutput).toHaveValue('3500.00');
        await expect(holdingsOutput).toContainText('AAPL: 10 shares');
    });

    test('TS-PTM-001b - Successful stock purchase of existing holding', async ({ page }) => {
        await setupTrader(page, 'buytrader-b@test.com', 5000);
        const symbolInput = page.locator('#component-17').getByTestId('textbox');
        const quantityInput = page.getByLabel('Quantity');
        const buyButton = page.locator('#component-21');
        const messagesOutput = page.locator('#component-28').getByTestId('textbox');
        const cashBalanceOutput = page.locator('#component-29').getByTestId('textbox');
        const holdingsOutput = page.locator('#component-30').getByTestId('textbox');

        // First purchase
        await symbolInput.fill('TSLA');
        await quantityInput.fill('5');
        await buyButton.click();
        await expect(messagesOutput).toHaveValue('Successfully bought 5 shares of TSLA.');

        // Second purchase
        await quantityInput.fill('5');
        await buyButton.click();

        await expect(messagesOutput).toHaveValue('Successfully bought 5 shares of TSLA.');
        await expect(cashBalanceOutput).toHaveValue('3000.00'); // 5000 - (10 * 200)
        await expect(holdingsOutput).toContainText('TSLA: 10 shares');
    });
    
    test.describe('TS-PTM-002 - Buy Transaction Failure Cases', () => {
        const failureCases = [
            { id: 'TS-PTM-002a', symbol: 'TSLA', initialCash: 299.00, quantity: '2', expectedError: 'Insufficient funds to complete this transaction.' },
            { id: 'TS-PTM-002b', symbol: 'FAKE', initialCash: 5000.00, quantity: '5', expectedError: "Stock symbol 'FAKE' not found." },
            { id: 'TS-PTM-002c', symbol: 'AAPL', initialCash: 5000.00, quantity: '0', expectedError: 'Quantity must be a positive number.' },
            { id: 'TS-PTM-002d', symbol: 'GOOGL', initialCash: 5000.00, quantity: '-1', expectedError: 'Quantity must be a positive number.' },
        ];

        for(const { id, symbol, initialCash, quantity, expectedError } of failureCases) {
            test(`${id} - Should fail with error: "${expectedError}"`, async ({ page }) => {
                await setupTrader(page, `${id}@buyfail.com`, initialCash);
                const symbolInput = page.locator('#component-17').getByTestId('textbox');
                const quantityInput = page.getByLabel('Quantity');
                const buyButton = page.locator('#component-21');
                const messagesOutput = page.locator('#component-28').getByTestId('textbox');
                const cashBalanceOutput = page.locator('#component-29').getByTestId('textbox');

                await symbolInput.fill(symbol);
                await quantityInput.fill(quantity);
                await buyButton.click();

                await expect(messagesOutput).toHaveValue(expectedError);
                await expect(cashBalanceOutput).toHaveValue(initialCash.toFixed(2));
            });
        }
    });

    test('TS-PTM-003a - Successful full sale of a position', async ({ page }) => {
        await setupTrader(page, 'selltrader-a@test.com', 1000);
        // Buy 5 TSLA, price is mocked at 200, cost is 1000
        await page.locator('#component-17').getByTestId('textbox').fill('TSLA');
        await page.getByLabel('Quantity').fill('5');
        await page.locator('#component-21').click();
        await expect(page.locator('#component-29').getByTestId('textbox')).toHaveValue('0.00');

        // Sell 5 TSLA, proceeds are 1000
        await page.locator('#component-22').click();
        
        await expect(page.locator('#component-28').getByTestId('textbox')).toHaveValue('Successfully sold 5 shares of TSLA.');
        await expect(page.locator('#component-29').getByTestId('textbox')).toHaveValue('1000.00');
        await expect(page.locator('#component-30').getByTestId('textbox')).not.toContainText('TSLA');
    });

    test('TS-PTM-003b - Successful partial sale of a position', async ({ page }) => {
        await setupTrader(page, 'selltrader-b@test.com', 2000);
         // Buy 10 AAPL, price is mocked at 150, cost is 1500
        await page.locator('#component-17').getByTestId('textbox').fill('AAPL');
        await page.getByLabel('Quantity').fill('10');
        await page.locator('#component-21').click();
        await expect(page.locator('#component-29').getByTestId('textbox')).toHaveValue('500.00');
        
        // Sell 3 AAPL, proceeds are 450
        await page.getByLabel('Quantity').fill('3');
        await page.locator('#component-22').click();

        await expect(page.locator('#component-28').getByTestId('textbox')).toHaveValue('Successfully sold 3 shares of AAPL.');
        await expect(page.locator('#component-29').getByTestId('textbox')).toHaveValue('950.00');
        await expect(page.locator('#component-30').getByTestId('textbox')).toContainText('AAPL: 7 shares');
    });

    test.describe('TS-PTM-004 - Sell Transaction Failure Cases', () => {
        test('TS-PTM-004a - Should fail when overselling', async ({ page }) => {
            await setupTrader(page, 'sellfail-a@test.com', 2000);
            await page.locator('#component-17').getByTestId('textbox').fill('AAPL');
            await page.getByLabel('Quantity').fill('10');
            await page.locator('#component-21').click(); // Own 10 AAPL

            await page.getByLabel('Quantity').fill('11');
            await page.locator('#component-22').click();

            await expect(page.locator('#component-28').getByTestId('textbox')).toHaveValue('You do not own enough shares of AAPL to sell.');
            await expect(page.locator('#component-30').getByTestId('textbox')).toContainText('AAPL: 10 shares');
        });

        test('TS-PTM-004b - Should fail when selling unowned stock', async ({ page }) => {
            await setupTrader(page, 'sellfail-b@test.com', 2000);
            
            await page.locator('#component-17').getByTestId('textbox').fill('GOOGL');
            await page.getByLabel('Quantity').fill('1');
            await page.locator('#component-22').click();
            
            await expect(page.locator('#component-28').getByTestId('textbox')).toHaveValue('You do not own any shares of GOOGL.');
        });
    });

    test('TS-PTM-005 - Comprehensive Portfolio Value Calculation', async ({ page }) => {
        await setupTrader(page, 'portfolio-test@test.com', 4000); // 1000 cash + 3000 for stocks
        const cashBalanceOutput = page.locator('#component-29').getByTestId('textbox');
        const holdingsOutput = page.locator('#component-30').getByTestId('textbox');
        const portfolioSummaryOutput = page.locator('#component-31').getByTestId('textbox');

        // Buy 10 AAPL @ 150 = 1500
        await page.locator('#component-17').getByTestId('textbox').fill('AAPL');
        await page.getByLabel('Quantity').fill('10');
        await page.locator('#component-21').click();

        // Buy 5 TSLA @ 200 = 1000
        await page.locator('#component-17').getByTestId('textbox').fill('TSLA');
        await page.getByLabel('Quantity').fill('5');
        await page.locator('#component-21').click();

        // Cash should be 4000 - 1500 - 1000 = 1500, but test case says 1000. Let's start with 3500 to match.
        // Re-setup with correct cash
        await page.reload();
        await setupTrader(page, 'portfolio-test-redux@test.com', 3500);
        await page.locator('#component-17').getByTestId('textbox').fill('AAPL');
        await page.getByLabel('Quantity').fill('10');
        await page.locator('#component-21').click();
        await page.locator('#component-17').getByTestId('textbox').fill('TSLA');
        await page.getByLabel('Quantity').fill('5');
        await page.locator('#component-21').click();

        await expect(cashBalanceOutput).toHaveValue('1000.00');
        await expect(holdingsOutput).toContainText('AAPL: 10 shares, Current Value: $1500.00');
        await expect(holdingsOutput).toContainText('TSLA: 5 shares, Current Value: $1000.00');
        await expect(portfolioSummaryOutput).toContainText('Total Holdings Value: $2500.00');
        await expect(portfolioSummaryOutput).toContainText('Total Portfolio Value: $3500.00');
    });

    test('TS-PTM-006 - Verify Transaction History Logging', async ({ page }) => {
        await setupTrader(page, 'history-test@test.com', 0);
        const transactionsOutput = page.locator('#component-34').getByTestId('textbox');
        const refreshButton = page.locator('#component-33');

        // 1. Deposit $1000.00
        await page.getByLabel('Deposit Amount').fill('1000');
        await page.locator('#component-12').click();

        // 2. Buy 2 AAPL @ $150.00
        await page.locator('#component-17').getByTestId('textbox').fill('AAPL');
        await page.getByLabel('Quantity').fill('2');
        await page.locator('#component-21').click();

        // 3. Withdraw $100.00
        await page.getByLabel('Withdraw Amount').fill('100');
        await page.locator('#component-14').click();

        // 4. Sell 1 AAPL @ $150.00
        await page.getByLabel('Quantity').fill('1');
        await page.locator('#component-22').click();

        await refreshButton.click();

        const history = await transactionsOutput.inputValue();
        const lines = history.trim().split('\n');

        expect(lines[0]).toMatch(/SELL: 1 AAPL @ 150.00/);
        expect(lines[1]).toMatch(/WITHDRAWAL: 100.00/);
        expect(lines[2]).toMatch(/BUY: 2 AAPL @ 150.00/);
        expect(lines[3]).toMatch(/DEPOSIT: 1000.00/);
    });
  });
});