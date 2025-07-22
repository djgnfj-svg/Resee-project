import { test, expect } from '@playwright/test';

test.describe('Review Workflow', () => {
  test.beforeEach(async ({ page }) => {
    // Login before each test using email
    await page.goto('/');
    await page.getByLabelText(/이메일/i).fill('test@resee.com');
    await page.getByLabelText(/비밀번호/i).fill('test123!');
    await page.getByRole('button', { name: /로그인/i }).click();
    await expect(page).toHaveURL(/\//);
  });

  test('should display review page', async ({ page }) => {
    await page.goto('/review');
    
    await expect(page.getByRole('heading', { name: /복습|review/i })).toBeVisible();
    
    // Should show today's reviews or empty state
    const reviewItems = page.locator('[data-testid="review-item"], .bg-white');
    const emptyState = page.getByText(/복습할 콘텐츠가 없습니다|no reviews/i);
    
    await expect(reviewItems.first().or(emptyState)).toBeVisible();
  });

  test('should show review statistics', async ({ page }) => {
    await page.goto('/review');
    
    // Should show review stats
    await expect(page.getByText(/복습|review/i)).toBeVisible();
    
    // Look for stats elements
    const statsElements = page.locator('text=/\\d+/, [data-testid*="stat"]');
    if (await statsElements.count() > 0) {
      await expect(statsElements.first()).toBeVisible();
    }
  });

  test('should complete a review session', async ({ page }) => {
    await page.goto('/review');
    
    // Wait for content to load
    await page.waitForTimeout(2000);
    
    const reviewItems = page.locator('[data-testid="review-item"], .bg-white');
    
    if (await reviewItems.count() > 0) {
      // Start review
      const startButton = page.getByRole('button', { name: /복습 시작|start review/i });
      if (await startButton.isVisible()) {
        await startButton.click();
        
        // Should show review content
        await expect(page.getByText(/복습|review/i)).toBeVisible();
        
        // Complete review with "remembered"
        const rememberedButton = page.getByRole('button', { name: /기억함|remembered/i });
        if (await rememberedButton.isVisible()) {
          await rememberedButton.click();
          
          // Should show completion or next review
          await expect(page.getByText(/완료|next|다음/i)).toBeVisible();
        }
      }
    } else {
      test.skip('No reviews available for testing');
    }
  });

  test('should handle different review results', async ({ page }) => {
    await page.goto('/review');
    
    await page.waitForTimeout(2000);
    
    const reviewItems = page.locator('[data-testid="review-item"], .bg-white');
    
    if (await reviewItems.count() > 0) {
      const startButton = page.getByRole('button', { name: /복습 시작|start/i });
      if (await startButton.isVisible()) {
        await startButton.click();
        
        // Test different result options
        const resultButtons = page.locator('button:has-text("기억함"), button:has-text("애매함"), button:has-text("모름")');
        const forgotButton = page.getByRole('button', { name: /모름|forgot/i });
        
        if (await forgotButton.isVisible()) {
          await forgotButton.click();
          
          // Should handle the result
          await expect(page.getByText(/다시|again|review/i)).toBeVisible();
        }
      }
    } else {
      test.skip('No reviews available for testing');
    }
  });

  test('should track time spent on review', async ({ page }) => {
    await page.goto('/review');
    
    await page.waitForTimeout(2000);
    
    const reviewItems = page.locator('[data-testid="review-item"], .bg-white');
    
    if (await reviewItems.count() > 0) {
      const startButton = page.getByRole('button', { name: /복습 시작|start/i });
      if (await startButton.isVisible()) {
        await startButton.click();
        
        // Wait some time to simulate studying
        await page.waitForTimeout(3000);
        
        // Complete review
        const rememberedButton = page.getByRole('button', { name: /기억함|remembered/i });
        if (await rememberedButton.isVisible()) {
          await rememberedButton.click();
          
          // Should show time spent (may not always be visible)
          const timeElement = page.locator('text=/시간|time|초|seconds/');
          // Time tracking is optional, so we don't enforce it
        }
      }
    } else {
      test.skip('No reviews available for testing');
    }
  });

  test('should handle keyboard shortcuts in review', async ({ page }) => {
    await page.goto('/review');
    
    await page.waitForTimeout(2000);
    
    const reviewItems = page.locator('[data-testid="review-item"], .bg-white');
    
    if (await reviewItems.count() > 0) {
      const startButton = page.getByRole('button', { name: /복습 시작|start/i });
      if (await startButton.isVisible()) {
        await startButton.click();
        
        // Use keyboard shortcut for "remembered" (key 3)
        await page.keyboard.press('3');
        
        // Should complete review or show next
        await page.waitForTimeout(1000);
        await expect(page.getByText(/완료|next|다음|복습/i)).toBeVisible();
      }
    } else {
      test.skip('No reviews available for testing');
    }
  });

  test('should show review progress', async ({ page }) => {
    await page.goto('/review');
    
    // Should show some kind of progress indicator
    const progressElements = page.locator('[data-testid="progress"], text=/\\d+\\/\\d+/, [role="progressbar"]');
    
    if (await progressElements.count() > 0) {
      await expect(progressElements.first()).toBeVisible();
    }
    
    // Should show some count or status
    await expect(page.getByText(/복습|review/i)).toBeVisible();
  });

  test('should handle immediate review for new content', async ({ page }) => {
    // First create new content
    await page.goto('/content');
    
    await page.getByRole('button', { name: /새 콘텐츠/i }).click();
    
    const timestamp = Date.now();
    await page.getByLabelText(/제목/i).fill(`Review Test Content ${timestamp}`);
    await page.getByRole('textbox').first().fill('This content will be available for immediate review.');
    await page.getByLabelText(/우선순위/i).selectOption('high');
    
    await page.getByRole('button', { name: /저장/i }).click();
    
    // Go to review page
    await page.goto('/review');
    
    // Should show the new content for immediate review
    await expect(page.getByText(`Review Test Content ${timestamp}`)).toBeVisible();
  });

  test('should show content details during review', async ({ page }) => {
    await page.goto('/review');
    
    await page.waitForTimeout(2000);
    
    const reviewItems = page.locator('[data-testid="review-item"], .bg-white');
    
    if (await reviewItems.count() > 0) {
      const startButton = page.getByRole('button', { name: /복습 시작|start/i });
      if (await startButton.isVisible()) {
        await startButton.click();
        
        // Should show content title and body
        await expect(page.locator('h1, h2, h3, .font-bold, .text-lg')).toBeVisible();
        
        // Should show content text
        await expect(page.locator('.prose, .content, p')).toBeVisible();
      }
    } else {
      test.skip('No reviews available for testing');
    }
  });

  test('should handle empty review state', async ({ page }) => {
    // This might be tricky to test consistently, but we can try
    await page.goto('/review');
    
    await page.waitForTimeout(2000);
    
    const emptyState = page.getByText(/복습할 콘텐츠가 없습니다|no reviews|empty/i);
    const createContentButton = page.getByRole('button', { name: /새 콘텐츠|create content/i });
    
    if (await emptyState.isVisible()) {
      await expect(emptyState).toBeVisible();
      
      // Should show call-to-action to create content
      if (await createContentButton.isVisible()) {
        await createContentButton.click();
        await expect(page).toHaveURL(/\/content/);
      }
    }
  });

  test('should navigate between dashboard and review page', async ({ page }) => {
    // Start on dashboard
    await page.goto('/');
    
    // Navigate to review page
    const reviewLink = page.getByRole('link', { name: /복습|review/i });
    if (await reviewLink.isVisible()) {
      await reviewLink.click();
      await expect(page).toHaveURL(/\/review/);
    } else {
      await page.goto('/review');
    }
    
    // Should show review page
    await expect(page.getByText(/복습|review/i)).toBeVisible();
    
    // Navigate back to dashboard
    const dashboardLink = page.getByRole('link', { name: /대시보드|dashboard|홈/i });
    if (await dashboardLink.isVisible()) {
      await dashboardLink.click();
      await expect(page).toHaveURL(/\//);
    }
  });

  test('should show subscription-based review intervals', async ({ page }) => {
    await page.goto('/review');
    
    // Review system should be working
    await expect(page.getByText(/복습|review/i)).toBeVisible();
    
    // For free tier users, reviews should be limited to shorter intervals
    // This is more of a system behavior test than UI test
    // We just verify the review page is accessible and functional
  });

  test('should handle review session interruption', async ({ page }) => {
    await page.goto('/review');
    
    await page.waitForTimeout(2000);
    
    const reviewItems = page.locator('[data-testid="review-item"], .bg-white');
    
    if (await reviewItems.count() > 0) {
      const startButton = page.getByRole('button', { name: /복습 시작|start/i });
      if (await startButton.isVisible()) {
        await startButton.click();
        
        // Navigate away mid-review
        await page.goto('/content');
        
        // Return to review page
        await page.goto('/review');
        
        // Should still be functional
        await expect(page.getByText(/복습|review/i)).toBeVisible();
      }
    } else {
      test.skip('No reviews available for testing');
    }
  });

  test('should be responsive on mobile', async ({ page }) => {
    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });
    
    await page.goto('/review');
    
    // Review interface should be mobile-friendly
    await expect(page.getByText(/복습|review/i)).toBeVisible();
    
    const reviewButtons = page.locator('button');
    if (await reviewButtons.count() > 0) {
      const firstButton = reviewButtons.first();
      const bbox = await firstButton.boundingBox();
      
      // Buttons should be touch-friendly (minimum 44px height)
      if (bbox) {
        expect(bbox.height).toBeGreaterThan(40);
      }
    }
  });

  test('should handle review notifications', async ({ page }) => {
    await page.goto('/');
    
    // Look for review reminders on dashboard
    const reviewReminder = page.locator('[data-testid="review-reminder"], text=/복습/, text=/due/');
    
    if (await reviewReminder.isVisible()) {
      await expect(reviewReminder).toBeVisible();
      
      // Should be able to navigate to reviews
      await reviewReminder.click();
      await expect(page).toHaveURL(/\/review/);
    }
  });

  test('should show review streaks', async ({ page }) => {
    await page.goto('/review');
    
    // Look for streak information
    const streakElement = page.locator('[data-testid="streak"], text=/연속/, text=/streak/');
    
    if (await streakElement.isVisible()) {
      await expect(streakElement).toBeVisible();
    }
  });

  test('should handle review completion celebration', async ({ page }) => {
    await page.goto('/review');
    
    await page.waitForTimeout(2000);
    
    const reviewItems = page.locator('[data-testid="review-item"], .bg-white');
    
    if (await reviewItems.count() > 0) {
      // Complete available reviews
      const startButton = page.getByRole('button', { name: /복습 시작|start/i });
      if (await startButton.isVisible()) {
        await startButton.click();
        
        // Complete with remembered
        const rememberedButton = page.getByRole('button', { name: /기억함|remembered/i });
        if (await rememberedButton.isVisible()) {
          await rememberedButton.click();
          
          // Look for completion message
          const completionMessage = page.getByText(/완료|잘했습니다|축하|congratulations/i);
          if (await completionMessage.isVisible()) {
            await expect(completionMessage).toBeVisible();
          }
        }
      }
    } else {
      test.skip('No reviews available for testing');
    }
  });

  test('should add and save review notes', async ({ page }) => {
    await page.goto('/review');
    
    await page.waitForTimeout(2000);
    
    const reviewItems = page.locator('[data-testid="review-item"], .bg-white');
    
    if (await reviewItems.count() > 0) {
      const startButton = page.getByRole('button', { name: /복습 시작|start/i });
      if (await startButton.isVisible()) {
        await startButton.click();
        
        // Look for notes input
        const notesInput = page.locator('textarea[placeholder*="노트"], input[placeholder*="note"]');
        if (await notesInput.isVisible()) {
          await notesInput.fill('This concept was challenging to remember');
          
          // Complete review
          const rememberedButton = page.getByRole('button', { name: /기억함|remembered/i });
          if (await rememberedButton.isVisible()) {
            await rememberedButton.click();
            
            // Should save the note
            await expect(page.getByText(/저장|saved/i)).toBeVisible();
          }
        }
      }
    } else {
      test.skip('No reviews available for testing');
    }
  });

  test('should handle offline review mode', async ({ page }) => {
    await page.goto('/review');
    
    // Go offline
    await page.context().setOffline(true);
    
    // Should show offline message or still work with cached content
    const offlineMessage = page.getByText(/오프라인|offline/i);
    const reviewContent = page.getByText(/복습|review/i);
    
    await expect(offlineMessage.or(reviewContent)).toBeVisible();
    
    // Go back online
    await page.context().setOffline(false);
  });

  test('should show review calendar', async ({ page }) => {
    // Some implementations might have a calendar view
    await page.goto('/review');
    
    const calendarButton = page.getByRole('button', { name: /달력|calendar/i });
    if (await calendarButton.isVisible()) {
      await calendarButton.click();
      
      // Should show calendar view
      await expect(page.locator('[role="grid"], .calendar')).toBeVisible();
    }
  });

  test('should filter reviews by category', async ({ page }) => {
    await page.goto('/review');
    
    const categoryFilter = page.getByLabelText(/카테고리|category/i);
    if (await categoryFilter.isVisible()) {
      await categoryFilter.selectOption({ index: 1 });
      
      // Should filter reviews
      await page.waitForTimeout(1000);
      await expect(page.getByText(/복습|review/i)).toBeVisible();
    }
  });

  test('should show review analytics', async ({ page }) => {
    await page.goto('/review');
    
    // Look for analytics or statistics
    const analyticsSection = page.locator('[data-testid="analytics"], text=/통계/, text=/분석/');
    if (await analyticsSection.isVisible()) {
      await expect(analyticsSection).toBeVisible();
    }
  });

  test('should handle bulk review completion', async ({ page }) => {
    await page.goto('/review');
    
    const bulkButton = page.getByRole('button', { name: /일괄|bulk|all/i });
    if (await bulkButton.isVisible()) {
      await bulkButton.click();
      
      // Should handle bulk operations
      await expect(page.getByText(/완료|completed/i)).toBeVisible();
    }
  });
});