import { test, expect, type Page } from '@playwright/test';

// Test data constants
const TEST_DATA = {
  newUser: {
    email: 'newuser@test.com',
    password: 'SecureP@ss1',
  },
  existingUser: {
    email: 'existing@test.com',
    password: 'PwD12345',
  },
  invalidUser: {
    email: 'new_bad@test.com',
    password: 'PwD12345',
    mismatchedPassword: 'PwD_MISMATCH',
  },
};

// Selectors based on the page snapshot
const SELECTORS = {
  emailInput: 'textbox[name="Email"]',
  passwordInput: 'textbox[name="Password"]',
  confirmPasswordInput: 'textbox[name="Confirm Password"]',
  createAccountButton: 'button:has-text("Create Account")',
  messagesField: 'textbox[name="Messages"]',
  cashBalanceField: 'textbox[name="Cash Balance"]',
};

test.describe('Feature: Account Registration and Initialization', () => {
  
  test.beforeEach(async ({ page }) => {
    // Navigate to the application
    await page.goto('/'); // Update with your actual URL
    
    // Wait for the page to load
    await page.waitForLoadState('networkidle');
  });

  test('ACC-REG-POS-001: Successful Account Creation and Zero Balance Initialization', async ({ page }) => {
    // Given the user is on the Registration interface
    await expect(page.getByRole('heading', { name: 'Account Creation' })).toBeVisible();

    // When the user enters registration details
    await page.getByRole('textbox', { name: 'Email' }).fill(TEST_DATA.newUser.email);
    await page.getByRole('textbox', { name: 'Password' }).fill(TEST_DATA.newUser.password);
    await page.getByRole('textbox', { name: 'Confirm Password' }).fill(TEST_DATA.newUser.password);

    // And the user clicks the "Create Account" button
    await page.getByRole('button', { name: 'Create Account' }).click();

    // Then the system displays the success message
    const messagesField = page.getByRole('textbox', { name: 'Messages' });
    await expect(messagesField).toBeVisible();
    
    // Wait for success message to appear
    await page.waitForTimeout(1000); // Adjust based on your app's response time
    
    const successMessage = await messagesField.inputValue();
    expect(successMessage).toContain('success');

    // And the "Cash Balance" is displayed as "$0.00"
    const cashBalanceField = page.getByRole('textbox', { name: 'Cash Balance' });
    await expect(cashBalanceField).toBeVisible();
    
    const cashBalance = await cashBalanceField.inputValue();
    expect(cashBalance).toBe('$0.00');
  });

  test('ACC-REG-NEG-002: Registration with Existing Email Address', async ({ page }) => {
    // Given the user is on the Registration interface
    await expect(page.getByRole('heading', { name: 'Account Creation' })).toBeVisible();

    // Precondition: existing@test.com is already registered
    // (This assumes the test data is pre-seeded or you have a setup step)

    // When the user attempts to register with an existing email
    await page.getByRole('textbox', { name: 'Email' }).fill(TEST_DATA.existingUser.email);
    await page.getByRole('textbox', { name: 'Password' }).fill(TEST_DATA.existingUser.password);
    await page.getByRole('textbox', { name: 'Confirm Password' }).fill(TEST_DATA.existingUser.password);

    // And the user clicks the "Create Account" button
    await page.getByRole('button', { name: 'Create Account' }).click();

    // Then the system displays the error message
    const messagesField = page.getByRole('textbox', { name: 'Messages' });
    await expect(messagesField).toBeVisible();
    
    // Wait for error message to appear
    await page.waitForTimeout(1000);
    
    const errorMessage = await messagesField.inputValue();
    expect(errorMessage).toContain('This email address is already registered');
  });

  test('ACC-REG-NEG-003: Registration with Mismatched Passwords', async ({ page }) => {
    // Given the user is on the Registration interface
    await expect(page.getByRole('heading', { name: 'Account Creation' })).toBeVisible();

    // When the user attempts to register with mismatched passwords
    await page.getByRole('textbox', { name: 'Email' }).fill(TEST_DATA.invalidUser.email);
    await page.getByRole('textbox', { name: 'Password' }).fill(TEST_DATA.invalidUser.password);
    await page.getByRole('textbox', { name: 'Confirm Password' }).fill(TEST_DATA.invalidUser.mismatchedPassword);

    // And the user clicks the "Create Account" button
    await page.getByRole('button', { name: 'Create Account' }).click();

    // Then the system displays the error message
    const messagesField = page.getByRole('textbox', { name: 'Messages' });
    await expect(messagesField).toBeVisible();
    
    // Wait for error message to appear
    await page.waitForTimeout(1000);
    
    const errorMessage = await messagesField.inputValue();
    expect(errorMessage).toContain('Passwords do not match');
  });

  test.describe('Scenario Outline: Negative Registration Scenarios', () => {
    const negativeTestCases = [
      {
        testId: 'ACC-REG-NEG-002',
        email: TEST_DATA.existingUser.email,
        password: TEST_DATA.existingUser.password,
        confirmPassword: TEST_DATA.existingUser.password,
        expectedError: 'This email address is already registered',
        description: 'Existing Email',
      },
      {
        testId: 'ACC-REG-NEG-003',
        email: TEST_DATA.invalidUser.email,
        password: TEST_DATA.invalidUser.password,
        confirmPassword: TEST_DATA.invalidUser.mismatchedPassword,
        expectedError: 'Passwords do not match',
        description: 'Mismatched Passwords',
      },
    ];

    negativeTestCases.forEach(({ testId, email, password, confirmPassword, expectedError, description }) => {
      test(`${testId}: ${description}`, async ({ page }) => {
        // Given the user is on the Registration interface
        await expect(page.getByRole('heading', { name: 'Account Creation' })).toBeVisible();

        // When the user attempts to register with invalid credentials
        await page.getByRole('textbox', { name: 'Email' }).fill(email);
        await page.getByRole('textbox', { name: 'Password' }).fill(password);
        await page.getByRole('textbox', { name: 'Confirm Password' }).fill(confirmPassword);

        // And the user clicks the "Create Account" button
        await page.getByRole('button', { name: 'Create Account' }).click();

        // Then the system displays the expected error message
        const messagesField = page.getByRole('textbox', { name: 'Messages' });
        await expect(messagesField).toBeVisible();
        
        // Wait for error message to appear
        await page.waitForTimeout(1000);
        
        const errorMessage = await messagesField.inputValue();
        expect(errorMessage).toContain(expectedError);
      });
    });
  });
});