import { test, expect } from '@playwright/test';

test.describe('Review Workflow', () => {
  test.beforeEach(async ({ page }) => {
    // Login before each test
    await page.goto('/');
    await page.getByLabelText(/사용자명/i).fill('testuser');
    await page.getByLabelText(/비밀번호/i).fill('password123');
    await page.getByRole('button', { name: /로그인/i }).click();
    await expect(page).toHaveURL(/\//);
  });

  test('should display today\'s reviews', async ({ page }) => {
    await page.goto('/review');
    
    await expect(page.getByRole('heading', { name: /오늘의 복습/i })).toBeVisible();
    
    // Should show review items or empty state
    const reviewItems = page.getByTestId('review-item');
    if (await reviewItems.count() > 0) {
      await expect(reviewItems.first()).toBeVisible();
    } else {
      await expect(page.getByText(/복습할 콘텐츠가 없습니다/i)).toBeVisible();
    }
  });

  test('should complete a review session', async ({ page }) => {
    await page.goto('/review');
    
    // Skip if no reviews available
    const reviewItems = page.getByTestId('review-item');
    if (await reviewItems.count() === 0) {
      test.skip('No reviews available for testing');
    }
    
    // Start review
    await page.getByRole('button', { name: /복습 시작/i }).click();
    
    // Should show review content
    await expect(page.getByTestId('review-content')).toBeVisible();
    
    // Complete review with "remembered"
    await page.getByRole('button', { name: /기억함/i }).click();
    
    // Should show next review or completion message
    await expect(page.getByText(/다음 복습|복습 완료/i)).toBeVisible();
  });

  test('should handle different review results', async ({ page }) => {
    await page.goto('/review');
    
    const reviewItems = page.getByTestId('review-item');
    if (await reviewItems.count() === 0) {
      test.skip('No reviews available for testing');
    }
    
    await page.getByRole('button', { name: /복습 시작/i }).click();
    
    // Test "forgot" result
    await page.getByRole('button', { name: /모름/i }).click();
    
    // Should handle the result and show next review
    await expect(page.getByText(/다시 복습하게 됩니다/i)).toBeVisible();
  });

  test('should add review notes', async ({ page }) => {
    await page.goto('/review');
    
    const reviewItems = page.getByTestId('review-item');
    if (await reviewItems.count() === 0) {
      test.skip('No reviews available for testing');
    }
    
    await page.getByRole('button', { name: /복습 시작/i }).click();
    
    // Add notes
    const notesInput = page.getByPlaceholderText(/복습 노트/i);
    await notesInput.fill('This concept was challenging to remember');
    
    // Complete review
    await page.getByRole('button', { name: /기억함/i }).click();
    
    // Notes should be saved with the review
    await expect(page.getByText(/노트가 저장되었습니다/i)).toBeVisible();
  });

  test('should track time spent on review', async ({ page }) => {
    await page.goto('/review');
    
    const reviewItems = page.getByTestId('review-item');
    if (await reviewItems.count() === 0) {
      test.skip('No reviews available for testing');
    }
    
    await page.getByRole('button', { name: /복습 시작/i }).click();
    
    // Wait some time to simulate studying
    await page.waitForTimeout(3000);
    
    // Complete review
    await page.getByRole('button', { name: /기억함/i }).click();
    
    // Should show time spent
    await expect(page.getByText(/소요 시간: \d+초/i)).toBeVisible();
  });

  test('should show review progress', async ({ page }) => {
    await page.goto('/review');
    
    // Should show progress indicator
    await expect(page.getByTestId('review-progress')).toBeVisible();
    
    // Should show counts
    await expect(page.getByText(/\d+\/\d+/)).toBeVisible();
  });

  test('should handle keyboard shortcuts in review', async ({ page }) => {
    await page.goto('/review');
    
    const reviewItems = page.getByTestId('review-item');
    if (await reviewItems.count() === 0) {
      test.skip('No reviews available for testing');
    }
    
    await page.getByRole('button', { name: /복습 시작/i }).click();
    
    // Use keyboard shortcut for "remembered" (key 1)
    await page.keyboard.press('1');
    
    // Should complete review
    await expect(page.getByText(/다음 복습|복습 완료/i)).toBeVisible();
  });

  test('should handle review navigation', async ({ page }) => {
    await page.goto('/review');
    
    const reviewItems = page.getByTestId('review-item');
    if (await reviewItems.count() < 2) {
      test.skip('Need multiple reviews for navigation testing');
    }
    
    await page.getByRole('button', { name: /복습 시작/i }).click();
    
    // Navigate to next review without completing current one
    const nextButton = page.getByRole('button', { name: /다음/i });
    if (await nextButton.isVisible()) {
      await nextButton.click();
      
      // Should show next review content
      await expect(page.getByTestId('review-content')).toBeVisible();
    }
  });

  test('should show review statistics', async ({ page }) => {
    await page.goto('/review');
    
    // Should show today's stats
    await expect(page.getByText(/오늘의 통계/i)).toBeVisible();
    await expect(page.getByText(/완료:/i)).toBeVisible();
    await expect(page.getByText(/남은:/i)).toBeVisible();
    await expect(page.getByText(/성공률:/i)).toBeVisible();
  });

  test('should handle review session interruption', async ({ page }) => {
    await page.goto('/review');
    
    const reviewItems = page.getByTestId('review-item');
    if (await reviewItems.count() === 0) {
      test.skip('No reviews available for testing');
    }
    
    await page.getByRole('button', { name: /복습 시작/i }).click();
    
    // Navigate away mid-review
    await page.goto('/content');
    
    // Return to review page
    await page.goto('/review');
    
    // Should ask to resume session
    await expect(page.getByText(/복습을 계속하시겠습니까/i)).toBeVisible();
  });

  test('should show content details during review', async ({ page }) => {
    await page.goto('/review');
    
    const reviewItems = page.getByTestId('review-item');
    if (await reviewItems.count() === 0) {
      test.skip('No reviews available for testing');
    }
    
    await page.getByRole('button', { name: /복습 시작/i }).click();
    
    // Should show content title
    await expect(page.getByTestId('content-title')).toBeVisible();
    
    // Should show content body
    await expect(page.getByTestId('content-body')).toBeVisible();
    
    // Should show category and tags
    await expect(page.getByTestId('content-category')).toBeVisible();
    await expect(page.getByTestId('content-tags')).toBeVisible();
  });

  test('should handle empty review state', async ({ page }) => {
    // Mock empty review state or test with user who has no reviews
    await page.goto('/review');
    
    // Look for empty state
    const emptyState = page.getByText(/복습할 콘텐츠가 없습니다/i);
    if (await emptyState.isVisible()) {
      // Should show call-to-action
      await expect(page.getByRole('button', { name: /새 콘텐츠 생성/i })).toBeVisible();
      
      // Should navigate to content creation
      await page.getByRole('button', { name: /새 콘텐츠 생성/i }).click();
      await expect(page).toHaveURL(/\/content\/new/);
    }
  });

  test('should show review completion celebration', async ({ page }) => {
    await page.goto('/review');
    
    const reviewItems = page.getByTestId('review-item');
    if (await reviewItems.count() === 0) {
      test.skip('No reviews available for testing');
    }
    
    // Complete all reviews
    await page.getByRole('button', { name: /모든 복습 완료/i }).click();
    
    // Should show celebration
    await expect(page.getByText(/축하합니다|잘했습니다/i)).toBeVisible();
    await expect(page.getByTestId('celebration-animation')).toBeVisible();
  });

  test('should show review history', async ({ page }) => {
    await page.goto('/review/history');
    
    await expect(page.getByRole('heading', { name: /복습 기록/i })).toBeVisible();
    
    // Should show history items
    const historyItems = page.getByTestId('history-item');
    if (await historyItems.count() > 0) {
      await expect(historyItems.first()).toBeVisible();
      
      // Should show review date, result, and time spent
      await expect(page.getByText(/\d{4}-\d{2}-\d{2}/)).toBeVisible();
      await expect(page.getByText(/기억함|애매함|모름/)).toBeVisible();
      await expect(page.getByText(/\d+초/)).toBeVisible();
    }
  });

  test('should filter review history', async ({ page }) => {
    await page.goto('/review/history');
    
    // Filter by date range
    await page.getByLabelText(/시작일/i).fill('2024-01-01');
    await page.getByLabelText(/종료일/i).fill('2024-12-31');
    
    // Filter by result
    await page.getByLabelText(/결과/i).selectOption('remembered');
    
    // Apply filters
    await page.getByRole('button', { name: /필터 적용/i }).click();
    
    // Should show filtered results
    const historyItems = page.getByTestId('history-item');
    if (await historyItems.count() > 0) {
      await expect(page.getByText(/기억함/)).toBeVisible();
    }
  });

  test('should export review data', async ({ page }) => {
    await page.goto('/review/history');
    
    // Export data
    await page.getByRole('button', { name: /내보내기/i }).click();
    
    // Choose format
    await page.getByRole('button', { name: /CSV/i }).click();
    
    // Should trigger download
    const downloadPromise = page.waitForEvent('download');
    await page.getByRole('button', { name: /다운로드/i }).click();
    const download = await downloadPromise;
    
    expect(download.suggestedFilename()).toMatch(/\.csv$/);
  });

  test('should handle review streaks', async ({ page }) => {
    await page.goto('/review');
    
    // Should show streak counter
    const streakElement = page.getByTestId('review-streak');
    if (await streakElement.isVisible()) {
      await expect(streakElement).toContainText(/\d+일 연속/);
    }
  });

  test('should show review reminders', async ({ page }) => {
    await page.goto('/');
    
    // Should show notification if reviews are due
    const reviewReminder = page.getByTestId('review-reminder');
    if (await reviewReminder.isVisible()) {
      await expect(reviewReminder).toContainText(/복습할 콘텐츠가 \d+개 있습니다/);
      
      // Should navigate to review page when clicked
      await reviewReminder.click();
      await expect(page).toHaveURL(/\/review/);
    }
  });

  test('should be responsive on mobile', async ({ page }) => {
    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });
    
    await page.goto('/review');
    
    // Review interface should be mobile-friendly
    await expect(page.getByTestId('mobile-review-interface')).toBeVisible();
    
    // Buttons should be touch-friendly
    const reviewButtons = page.getByRole('button', { name: /기억함|애매함|모름/i });
    for (let i = 0; i < await reviewButtons.count(); i++) {
      const button = reviewButtons.nth(i);
      const bbox = await button.boundingBox();
      expect(bbox?.height).toBeGreaterThan(44); // Minimum touch target size
    }
  });

  test('should handle offline review mode', async ({ page }) => {
    await page.goto('/review');
    
    // Go offline
    await page.context().setOffline(true);
    
    // Should show offline message
    await expect(page.getByText(/오프라인 모드/i)).toBeVisible();
    
    // Should still allow reviewing cached content
    const cachedReviews = page.getByTestId('cached-review');
    if (await cachedReviews.count() > 0) {
      await cachedReviews.first().click();
      await expect(page.getByTestId('review-content')).toBeVisible();
    }
  });
});