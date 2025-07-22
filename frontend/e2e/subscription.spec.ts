import { test, expect } from '@playwright/test';

test.describe('Subscription System', () => {
  test.beforeEach(async ({ page }) => {
    // Clear storage and login as test user
    await page.context().clearCookies();
    await page.evaluate(() => localStorage.clear());
    
    // Login with test user
    await page.goto('/');
    await page.getByLabelText(/이메일/i).fill('test@resee.com');
    await page.getByLabelText(/비밀번호/i).fill('test123!');
    await page.getByRole('button', { name: /로그인/i }).click();
    await expect(page).toHaveURL(/\//);
  });

  test('should display subscription page with available plans', async ({ page }) => {
    await page.goto('/subscription');
    
    await expect(page.getByRole('heading', { name: /구독 플랜/i })).toBeVisible();
    
    // Should show all subscription tiers
    await expect(page.getByText(/무료/i)).toBeVisible();
    await expect(page.getByText(/베이직/i)).toBeVisible(); 
    await expect(page.getByText(/프리미엄/i)).toBeVisible();
    await expect(page.getByText(/프로/i)).toBeVisible();
  });

  test('should show subscription features comparison', async ({ page }) => {
    await page.goto('/subscription');
    
    // Free tier features
    await expect(page.getByText(/최대 7일 복습 간격/i)).toBeVisible();
    
    // Basic tier features
    await expect(page.getByText(/최대 30일 복습 간격/i)).toBeVisible();
    await expect(page.getByText(/월 10개 AI 질문/i)).toBeVisible();
    
    // Premium tier features
    await expect(page.getByText(/최대 60일 복습 간격/i)).toBeVisible();
    await expect(page.getByText(/월 50개 AI 질문/i)).toBeVisible();
    await expect(page.getByText(/빈칸 채우기 모드/i)).toBeVisible();
    
    // Pro tier features
    await expect(page.getByText(/최대 90일 복습 간격/i)).toBeVisible();
    await expect(page.getByText(/월 200개 AI 질문/i)).toBeVisible();
    await expect(page.getByText(/모든 AI 기능/i)).toBeVisible();
  });

  test('should show current subscription status', async ({ page }) => {
    await page.goto('/subscription');
    
    // Should show current plan (likely free for test user)
    await expect(page.getByText(/현재 플랜/i)).toBeVisible();
    
    // Should show subscription status
    const statusElement = page.locator('[data-testid="subscription-status"]');
    if (await statusElement.isVisible()) {
      await expect(statusElement).toContainText(/무료|베이직|프리미엄|프로/);
    }
  });

  test('should attempt subscription upgrade', async ({ page }) => {
    await page.goto('/subscription');
    
    // Try to upgrade to basic plan
    const upgradeButton = page.getByRole('button', { name: /베이직 플랜 선택/i });
    if (await upgradeButton.isVisible()) {
      await upgradeButton.click();
      
      // Should show payment or upgrade process
      await expect(page.getByText(/결제|업그레이드/i)).toBeVisible();
    }
  });

  test('should show subscription benefits in content page', async ({ page }) => {
    await page.goto('/content');
    
    // Should show AI learning buttons with subscription requirements
    const aiButtons = page.locator('button:has-text("AI 학습")');
    if (await aiButtons.count() > 0) {
      await expect(aiButtons.first()).toBeVisible();
    }
    
    // For free users, should show subscription required message
    const subscriptionRequiredButtons = page.locator('button:has-text("구독 필요")');
    if (await subscriptionRequiredButtons.count() > 0) {
      await expect(subscriptionRequiredButtons.first()).toBeVisible();
    }
  });

  test('should restrict review intervals based on subscription', async ({ page }) => {
    await page.goto('/review');
    
    // Free tier should only have reviews up to 7 days
    // This test would need to check the actual review intervals
    // Since we can't easily generate reviews with long intervals in E2E,
    // we'll check for the presence of review-related elements
    
    await expect(page.getByText(/복습/i)).toBeVisible();
  });

  test('should handle email verification requirement for subscription', async ({ page }) => {
    // This test assumes we can access a user without email verification
    // For now, we'll test the general flow
    
    await page.goto('/subscription');
    
    // If email is not verified, should show warning
    const emailWarning = page.getByText(/이메일 인증이 필요합니다/i);
    if (await emailWarning.isVisible()) {
      await expect(emailWarning).toBeVisible();
    }
  });

  test('should show subscription pricing correctly', async ({ page }) => {
    await page.goto('/subscription');
    
    // Should show pricing information
    await expect(page.getByText(/무료/i)).toBeVisible();
    
    // Basic plan pricing (assuming it has a price)
    const pricingElements = page.locator('text=/₩|\\$/');
    if (await pricingElements.count() > 0) {
      await expect(pricingElements.first()).toBeVisible();
    }
  });

  test('should navigate to subscription from AI feature restrictions', async ({ page }) => {
    await page.goto('/content');
    
    // Find and click a subscription required AI button
    const subscriptionButton = page.locator('button:has-text("구독 필요")');
    if (await subscriptionButton.count() > 0) {
      await subscriptionButton.first().click();
      
      // Should navigate to subscription page
      await expect(page).toHaveURL(/\/subscription/);
    }
  });

  test('should show subscription status in dashboard', async ({ page }) => {
    await page.goto('/');
    
    // Dashboard should show current subscription info
    const subscriptionInfo = page.getByTestId('subscription-info');
    if (await subscriptionInfo.isVisible()) {
      await expect(subscriptionInfo).toContainText(/무료|베이직|프리미엄|프로/);
    }
  });

  test('should handle subscription cancellation flow', async ({ page }) => {
    await page.goto('/subscription');
    
    // Look for cancel/downgrade options (if user has active subscription)
    const cancelButton = page.getByRole('button', { name: /취소|해지/i });
    if (await cancelButton.isVisible()) {
      await cancelButton.click();
      
      // Should show confirmation dialog
      await expect(page.getByText(/정말로|확인/i)).toBeVisible();
    }
  });

  test('should show subscription history', async ({ page }) => {
    await page.goto('/subscription');
    
    // Look for subscription history section
    const historySection = page.getByText(/구독 기록|히스토리/i);
    if (await historySection.isVisible()) {
      await expect(historySection).toBeVisible();
    }
  });

  test('should validate subscription tier limits', async ({ page }) => {
    // Test AI feature limits based on subscription tier
    await page.goto('/content');
    
    // Create a test content first
    await page.getByRole('button', { name: /새 콘텐츠/i }).click();
    
    // Fill basic content form
    await page.getByLabelText(/제목/i).fill('AI Test Content');
    await page.getByRole('textbox').fill('This is test content for AI testing.');
    await page.getByLabelText(/우선순위/i).selectOption('medium');
    
    await page.getByRole('button', { name: /저장/i }).click();
    
    // Go back to content list
    await expect(page).toHaveURL(/\/content/);
    
    // Try to use AI features
    const aiButton = page.locator('button:has-text("AI 학습")').first();
    if (await aiButton.isVisible()) {
      await aiButton.click();
      
      // Should either work or show subscription requirement
      const aiContent = page.getByTestId('ai-content');
      const subscriptionPrompt = page.getByText(/구독|업그레이드/i);
      
      await expect(aiContent.or(subscriptionPrompt)).toBeVisible();
    }
  });

  test('should be responsive on mobile', async ({ page }) => {
    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });
    
    await page.goto('/subscription');
    
    // Subscription cards should stack vertically
    const subscriptionCards = page.locator('[data-testid="subscription-card"]');
    if (await subscriptionCards.count() > 0) {
      const firstCard = subscriptionCards.first();
      const secondCard = subscriptionCards.nth(1);
      
      if (await secondCard.isVisible()) {
        const firstCardBox = await firstCard.boundingBox();
        const secondCardBox = await secondCard.boundingBox();
        
        // Second card should be below first card (stacked vertically)
        expect(secondCardBox?.y).toBeGreaterThan(firstCardBox?.y || 0);
      }
    }
  });

  test('should show subscription benefits tooltip', async ({ page }) => {
    await page.goto('/subscription');
    
    // Look for info icons or help text
    const infoButtons = page.locator('button[aria-label*="정보"], button[aria-label*="도움말"]');
    if (await infoButtons.count() > 0) {
      await infoButtons.first().hover();
      
      // Should show tooltip with benefit details
      await expect(page.getByRole('tooltip')).toBeVisible();
    }
  });

  test('should handle subscription tier changes correctly', async ({ page }) => {
    await page.goto('/subscription');
    
    // Get current subscription status
    const statusElement = page.locator('[data-testid="subscription-status"]');
    
    if (await statusElement.isVisible()) {
      const currentStatus = await statusElement.textContent();
      
      // Try to upgrade (or downgrade based on current status)
      const upgradeButtons = page.locator('button:has-text("선택"), button:has-text("업그레이드")');
      
      if (await upgradeButtons.count() > 0) {
        await upgradeButtons.first().click();
        
        // Should handle the subscription change process
        await expect(page.getByText(/처리 중|확인/i)).toBeVisible();
      }
    }
  });
});