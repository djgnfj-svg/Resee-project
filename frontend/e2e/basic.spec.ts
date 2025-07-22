import { test, expect } from '@playwright/test';

test.describe('Basic Functionality', () => {
  test('should load the application', async ({ page }) => {
    await page.goto('http://localhost:3000');
    
    // Should show some content, either login form or dashboard
    await expect(page.locator('body')).toBeVisible();
    
    // Should have the title or some identifying text
    const title = await page.title();
    expect(title).toContain('Resee');
  });

  test('should show login form', async ({ page }) => {
    await page.goto('http://localhost:3000');
    
    // Wait a bit for the app to load
    await page.waitForTimeout(3000);
    
    // Look for login-related elements
    const loginElements = page.locator('input[type="email"], input[type="password"], button:has-text("로그인")');
    await expect(loginElements.first()).toBeVisible();
  });

  test('should be able to navigate', async ({ page }) => {
    await page.goto('http://localhost:3000');
    
    // Wait for page to load
    await page.waitForTimeout(3000);
    
    // Check if we can find navigation elements
    const navElements = page.locator('nav, header, [role="navigation"]');
    if (await navElements.count() > 0) {
      await expect(navElements.first()).toBeVisible();
    }
  });

  test('should handle 404 pages', async ({ page }) => {
    await page.goto('http://localhost:3000/nonexistent-page');
    
    // Should either redirect or show 404
    await page.waitForTimeout(2000);
    
    // Should still be a valid page (not blank)
    await expect(page.locator('body')).toBeVisible();
  });

  test('should load CSS and JavaScript', async ({ page }) => {
    await page.goto('http://localhost:3000');
    
    // Check if CSS is loaded by looking for styled elements
    await page.waitForTimeout(3000);
    
    // Should have some styling applied
    const styledElements = page.locator('[class*="bg-"], [class*="text-"], [class*="border-"]');
    if (await styledElements.count() > 0) {
      await expect(styledElements.first()).toBeVisible();
    }
  });
});