import { test, expect } from '@playwright/test';

const ADMIN_USERNAME = process.env.ADMIN_USERNAME || 'JackDaddy';
const ADMIN_PASSWORD = process.env.ADMIN_PASSWORD || 'Buff2025!';

const TEST_ITEM = {
  title: 'E2E Test Roadmap Item',
  description: 'This is a roadmap item created by an E2E test.',
  updatedTitle: 'E2E Test Roadmap Item (Edited)',
  updatedDescription: 'This roadmap item was edited by an E2E test.'
};

test('admin can perform full CRUD on roadmap items', async ({ page }) => {
  // Login as admin
  await page.goto('/admin/login');
  await page.getByLabel('Username').fill(ADMIN_USERNAME);
  await page.getByLabel('Password').fill(ADMIN_PASSWORD);
  await page.getByRole('button', { name: /sign in/i }).click();
  await expect(page).toHaveURL(/\/admin/);

  // Navigate to roadmap management (assume /admin/roadmap or a visible tab/button)
  // If roadmap is on the main admin page, adjust selector accordingly
  await page.getByRole('tab', { name: /roadmap/i }).click().catch(() => {});
  await expect(page.getByRole('heading', { name: /roadmap/i })).toBeVisible();

  // Add a new roadmap item
  await page.getByRole('button', { name: /add roadmap item/i }).click();
  await page.getByLabel(/title/i).fill(TEST_ITEM.title);
  await page.getByLabel(/description/i).fill(TEST_ITEM.description);
  await page.getByRole('button', { name: /save/i }).click();
  await expect(page.getByText(TEST_ITEM.title)).toBeVisible();
  await expect(page.getByText(TEST_ITEM.description)).toBeVisible();

  // Edit the roadmap item
  await page.getByRole('button', { name: /edit/i, exact: false }).first().click();
  await page.getByLabel(/title/i).fill(TEST_ITEM.updatedTitle);
  await page.getByLabel(/description/i).fill(TEST_ITEM.updatedDescription);
  await page.getByRole('button', { name: /save/i }).click();
  await expect(page.getByText(TEST_ITEM.updatedTitle)).toBeVisible();
  await expect(page.getByText(TEST_ITEM.updatedDescription)).toBeVisible();

  // Delete the roadmap item
  await page.getByRole('button', { name: /delete/i, exact: false }).first().click();
  // Confirm delete if a modal appears
  await page.getByRole('button', { name: /confirm/i }).click().catch(() => {});
  await expect(page.getByText(TEST_ITEM.updatedTitle)).not.toBeVisible();
}); 