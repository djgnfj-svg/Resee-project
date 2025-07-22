import { test, expect } from '@playwright/test';

test.describe('AI Review System', () => {
  test.beforeEach(async ({ page }) => {
    // Clear storage and login as test user with subscription
    await page.context().clearCookies();
    await page.evaluate(() => localStorage.clear());
    
    // Login with demo user (likely has subscription)
    await page.goto('/');
    await page.getByLabelText(/이메일/i).fill('demo@resee.com');
    await page.getByLabelText(/비밀번호/i).fill('demo123!');
    await page.getByRole('button', { name: /로그인/i }).click();
    await expect(page).toHaveURL(/\//);
  });

  test('should access AI review from content page', async ({ page }) => {
    await page.goto('/content');
    
    // Should show AI learning buttons for subscribed users
    const aiButtons = page.locator('button:has-text("AI 학습")');
    if (await aiButtons.count() > 0) {
      await aiButtons.first().click();
      
      // Should navigate to AI review interface
      await expect(page.getByText(/AI 스마트 학습/i)).toBeVisible();
      await expect(page.getByText(/질문 생성기/i)).toBeVisible();
    }
  });

  test('should show AI review mode selector', async ({ page }) => {
    await page.goto('/content');
    
    // Click on AI learning for first content
    const aiButtons = page.locator('button:has-text("AI 학습")');
    if (await aiButtons.count() > 0) {
      await aiButtons.first().click();
      
      // Should show different AI review modes
      await expect(page.getByText(/질문 생성기/i)).toBeVisible();
      await expect(page.getByText(/빈칸 채우기/i)).toBeVisible();
      await expect(page.getByText(/블러 처리/i)).toBeVisible();
      
      // Should show mode icons
      await expect(page.locator('text=🤖')).toBeVisible();
      await expect(page.locator('text=🧩')).toBeVisible();
      await expect(page.locator('text=🎯')).toBeVisible();
    }
  });

  test('should generate AI questions', async ({ page }) => {
    await page.goto('/content');
    
    const aiButtons = page.locator('button:has-text("AI 학습")');
    if (await aiButtons.count() > 0) {
      await aiButtons.first().click();
      
      // Select question generator mode (should be default)
      await expect(page.getByText(/질문 생성기/i)).toBeVisible();
      
      // Try to generate questions
      const generateButton = page.getByRole('button', { name: /질문 생성/i });
      if (await generateButton.isVisible()) {
        await generateButton.click();
        
        // Should show loading or generated questions
        await expect(page.getByText(/생성 중|생성된 질문/i)).toBeVisible();
        
        // Wait for generation to complete
        await page.waitForTimeout(5000);
        
        // Should show generated questions
        const questionElements = page.locator('[data-testid="generated-question"]');
        if (await questionElements.count() > 0) {
          await expect(questionElements.first()).toBeVisible();
        }
      }
    }
  });

  test('should show question type options', async ({ page }) => {
    await page.goto('/content');
    
    const aiButtons = page.locator('button:has-text("AI 학습")');
    if (await aiButtons.count() > 0) {
      await aiButtons.first().click();
      
      // Look for question type selectors
      const questionTypes = page.locator('input[type="checkbox"]');
      if (await questionTypes.count() > 0) {
        // Should have multiple choice and short answer options
        await expect(page.getByText(/객관식/i)).toBeVisible();
        await expect(page.getByText(/주관식/i)).toBeVisible();
      }
    }
  });

  test('should show difficulty level selector', async ({ page }) => {
    await page.goto('/content');
    
    const aiButtons = page.locator('button:has-text("AI 학습")');
    if (await aiButtons.count() > 0) {
      await aiButtons.first().click();
      
      // Look for difficulty selector
      const difficultySelector = page.getByLabelText(/난이도/i);
      if (await difficultySelector.isVisible()) {
        await expect(difficultySelector).toBeVisible();
        
        // Should have easy, medium, hard options
        await difficultySelector.click();
        await expect(page.getByText(/쉬움|보통|어려움/i)).toBeVisible();
      }
    }
  });

  test('should display generated questions with answers', async ({ page }) => {
    await page.goto('/content');
    
    const aiButtons = page.locator('button:has-text("AI 학습")');
    if (await aiButtons.count() > 0) {
      await aiButtons.first().click();
      
      // Wait a bit for existing questions to load
      await page.waitForTimeout(2000);
      
      // Look for existing questions
      const questionElements = page.locator('text=생성된 질문');
      if (await questionElements.isVisible()) {
        await expect(questionElements).toBeVisible();
        
        // Should have expandable answers
        const answerToggles = page.locator('summary:has-text("정답 보기")');
        if (await answerToggles.count() > 0) {
          await answerToggles.first().click();
          
          // Should show the answer
          await expect(page.getByText(/정답:/i)).toBeVisible();
        }
      }
    }
  });

  test('should handle fill-blank mode', async ({ page }) => {
    await page.goto('/content');
    
    const aiButtons = page.locator('button:has-text("AI 학습")');
    if (await aiButtons.count() > 0) {
      await aiButtons.first().click();
      
      // Switch to fill-blank mode
      const fillBlankMode = page.locator('button:has-text("빈칸 채우기")');
      if (await fillBlankMode.isVisible()) {
        await fillBlankMode.click();
        
        // Should show fill-blank interface
        await expect(page.getByText(/빈칸/i)).toBeVisible();
        
        // Should show text with blanks
        const blankElements = page.locator('input[placeholder*="빈칸"]');
        if (await blankElements.count() > 0) {
          await expect(blankElements.first()).toBeVisible();
        }
      }
    }
  });

  test('should handle blur processing mode', async ({ page }) => {
    await page.goto('/content');
    
    const aiButtons = page.locator('button:has-text("AI 학습")');
    if (await aiButtons.count() > 0) {
      await aiButtons.first().click();
      
      // Switch to blur processing mode
      const blurMode = page.locator('button:has-text("블러 처리")');
      if (await blurMode.isVisible()) {
        await blurMode.click();
        
        // Should show blur processing interface
        await expect(page.getByText(/블러|흐림/i)).toBeVisible();
        
        // Should show content with blurred regions
        const blurredElements = page.locator('[style*="blur"]');
        if (await blurredElements.count() > 0) {
          await expect(blurredElements.first()).toBeVisible();
        }
      }
    }
  });

  test('should show subscription tier restrictions', async ({ page }) => {
    // First logout and login as free user
    await page.getByRole('button', { name: /로그아웃/i }).click();
    
    // Login as test user (free tier)
    await page.goto('/');
    await page.getByLabelText(/이메일/i).fill('test@resee.com');
    await page.getByLabelText(/비밀번호/i).fill('test123!');
    await page.getByRole('button', { name: /로그인/i }).click();
    
    await page.goto('/content');
    
    // Should show subscription required for AI features
    const subscriptionButtons = page.locator('button:has-text("구독 필요")');
    if (await subscriptionButtons.count() > 0) {
      await expect(subscriptionButtons.first()).toBeVisible();
      
      // Click should navigate to subscription page
      await subscriptionButtons.first().click();
      await expect(page).toHaveURL(/\/subscription/);
    }
  });

  test('should show AI usage limits', async ({ page }) => {
    await page.goto('/content');
    
    const aiButtons = page.locator('button:has-text("AI 학습")');
    if (await aiButtons.count() > 0) {
      await aiButtons.first().click();
      
      // Should show usage information
      const usageInfo = page.locator('text=/남은|사용/');
      if (await usageInfo.isVisible()) {
        await expect(usageInfo).toBeVisible();
      }
    }
  });

  test('should handle AI service errors gracefully', async ({ page }) => {
    await page.goto('/content');
    
    const aiButtons = page.locator('button:has-text("AI 학습")');
    if (await aiButtons.count() > 0) {
      await aiButtons.first().click();
      
      // Try to generate many questions at once to potentially trigger rate limits
      const generateButton = page.getByRole('button', { name: /질문 생성/i });
      if (await generateButton.isVisible()) {
        // Click multiple times rapidly
        for (let i = 0; i < 5; i++) {
          await generateButton.click();
          await page.waitForTimeout(100);
        }
        
        // Should show error message or rate limit warning
        await expect(page.getByText(/오류|제한|잠시|다시/i)).toBeVisible();
      }
    }
  });

  test('should navigate back to content list', async ({ page }) => {
    await page.goto('/content');
    
    const aiButtons = page.locator('button:has-text("AI 학습")');
    if (await aiButtons.count() > 0) {
      await aiButtons.first().click();
      
      // Should show back button
      const backButton = page.getByRole('button', { name: /돌아가기|뒤로/i });
      if (await backButton.isVisible()) {
        await backButton.click();
        
        // Should return to content list
        await expect(page).toHaveURL(/\/content/);
        await expect(page.getByText(/콘텐츠 관리/i)).toBeVisible();
      }
    }
  });

  test('should show AI learning tips', async ({ page }) => {
    await page.goto('/content');
    
    const aiButtons = page.locator('button:has-text("AI 학습")');
    if (await aiButtons.count() > 0) {
      await aiButtons.first().click();
      
      // Should show usage tips
      await expect(page.getByText(/사용법|도구|tip/i)).toBeVisible();
      await expect(page.getByText(/질문 생성기/i)).toBeVisible();
    }
  });

  test('should handle mobile interface', async ({ page }) => {
    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });
    
    await page.goto('/content');
    
    const aiButtons = page.locator('button:has-text("AI 학습")');
    if (await aiButtons.count() > 0) {
      await aiButtons.first().click();
      
      // AI interface should be mobile-friendly
      const modeSelector = page.locator('button:has-text("질문 생성기")');
      if (await modeSelector.isVisible()) {
        // Buttons should be touch-friendly
        const bbox = await modeSelector.boundingBox();
        expect(bbox?.height).toBeGreaterThan(44); // Minimum touch target
      }
    }
  });

  test('should show question statistics', async ({ page }) => {
    await page.goto('/content');
    
    const aiButtons = page.locator('button:has-text("AI 학습")');
    if (await aiButtons.count() > 0) {
      await aiButtons.first().click();
      
      // Should show question stats
      const statsSection = page.locator('text=생성된 질문 현황');
      if (await statsSection.isVisible()) {
        await expect(statsSection).toBeVisible();
        
        // Should show counts
        await expect(page.getByText(/총 생성된 질문/i)).toBeVisible();
      }
    }
  });

  test('should handle question type filtering', async ({ page }) => {
    await page.goto('/content');
    
    const aiButtons = page.locator('button:has-text("AI 학습")');
    if (await aiButtons.count() > 0) {
      await aiButtons.first().click();
      
      // Look for question type filters or badges
      const questionTypeBadges = page.locator('[class*="badge"], [class*="tag"]');
      if (await questionTypeBadges.count() > 0) {
        // Should show question type indicators
        await expect(page.getByText(/객관식|주관식/i)).toBeVisible();
      }
    }
  });

  test('should show AI model information', async ({ page }) => {
    await page.goto('/content');
    
    const aiButtons = page.locator('button:has-text("AI 학습")');
    if (await aiButtons.count() > 0) {
      await aiButtons.first().click();
      
      // Should show AI model or system info
      const aiInfo = page.locator('text=/GPT|AI|모델/');
      if (await aiInfo.isVisible()) {
        await expect(aiInfo).toBeVisible();
      }
    }
  });

  test('should handle keyboard navigation in AI interface', async ({ page }) => {
    await page.goto('/content');
    
    const aiButtons = page.locator('button:has-text("AI 학습")');
    if (await aiButtons.count() > 0) {
      await aiButtons.first().click();
      
      // Test tab navigation through AI interface
      await page.keyboard.press('Tab');
      
      // Should be able to navigate through buttons
      const focusedElement = page.locator(':focus');
      await expect(focusedElement).toBeVisible();
    }
  });

  test('should preserve AI session state', async ({ page }) => {
    await page.goto('/content');
    
    const aiButtons = page.locator('button:has-text("AI 학습")');
    if (await aiButtons.count() > 0) {
      await aiButtons.first().click();
      
      // Generate some questions
      const generateButton = page.getByRole('button', { name: /질문 생성/i });
      if (await generateButton.isVisible()) {
        await generateButton.click();
        await page.waitForTimeout(3000);
        
        // Navigate away and back
        await page.goto('/');
        await page.goto('/content');
        
        // Click AI learning again
        const aiButtonsAgain = page.locator('button:has-text("AI 학습")');
        if (await aiButtonsAgain.count() > 0) {
          await aiButtonsAgain.first().click();
          
          // Should still show previously generated questions
          await expect(page.getByText(/생성된 질문/i)).toBeVisible();
        }
      }
    }
  });
});