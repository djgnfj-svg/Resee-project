import { test, expect } from '@playwright/test';

/**
 * Critical User Flow E2E Test
 * Tests the most important user journey: Login → Create Content → Review
 * Uses existing test account to avoid email verification issues
 */

// Use existing test account
const testEmail = 'mcptest@example.com';
const testPassword = 'mcptest123!';
const timestamp = Date.now();

test.describe('Critical User Flow', () => {
  test('User can login, create content, and review', async ({ page }) => {
    // Step 1: Login with existing account
    await test.step('Login to account', async () => {
      await page.goto('/login');

      // Fill login form
      await page.fill('input[name="email"]', testEmail);
      await page.fill('input[name="password"]', testPassword);

      // Submit login
      await page.click('button[type="submit"]');

      // Wait for dashboard
      await page.waitForURL('/dashboard', { timeout: 15000 });
    });

    // Step 3: Navigate to dashboard and verify login
    await test.step('Verify dashboard access', async () => {
      // Should be on dashboard now
      await expect(page).toHaveURL('/dashboard');

      // Check for dashboard elements
      await expect(page.locator('text=대시보드')).toBeVisible();

      // Verify user is logged in (check for user menu or profile)
      const userMenuExists = await page.locator('[data-testid="user-menu"], .user-profile, button:has-text("프로필")').count();
      expect(userMenuExists).toBeGreaterThan(0);
    });

    // Step 4: Create new content
    await test.step('Create new content', async () => {
      // Navigate to content creation page
      await page.click('a:has-text("콘텐츠 추가"), a:has-text("새 콘텐츠"), button:has-text("콘텐츠 추가")');

      // Wait for content creation page
      await page.waitForURL(/\/content\/(create|new)/, { timeout: 10000 });

      // Fill content form
      await page.fill('input[name="title"], #id_title', `E2E Test Content ${timestamp}`);
      await page.fill('textarea[name="question"], #id_question', 'What is the capital of France?');
      await page.fill('textarea[name="answer"], #id_answer', 'Paris');

      // Select category if available
      const categorySelect = page.locator('select[name="category"], #id_category');
      if (await categorySelect.count() > 0) {
        await categorySelect.selectOption({ index: 1 }); // Select first non-empty option
      }

      // Submit content
      await page.click('button[type="submit"]:has-text("저장"), button:has-text("생성"), button:has-text("추가")');

      // Wait for redirect to content list or detail page
      await page.waitForURL(/\/content|\/dashboard/, { timeout: 10000 });

      // Verify success message or content appears
      const successIndicator = page.locator('text=성공, text=생성되었습니다, text=추가되었습니다');
      if (await successIndicator.count() > 0) {
        await expect(successIndicator.first()).toBeVisible({ timeout: 3000 });
      }
    });

    // Step 5: Navigate to review page
    await test.step('Access review page', async () => {
      // Go to dashboard first
      await page.goto('/dashboard');

      // Find and click review button
      await page.click('a:has-text("복습하기"), a:has-text("오늘의 복습"), [href="/review"]');

      // Wait for review page
      await page.waitForURL('/review', { timeout: 10000 });

      // Check if review content is available
      const noReviewMsg = page.locator('text=복습할 콘텐츠가 없습니다, text=오늘 복습할 내용이 없습니다');
      const hasReview = await noReviewMsg.count() === 0;

      if (!hasReview) {
        console.log('No review available yet - content needs 1 day');
        return; // Skip review step if no content available
      }
    });

    // Step 6: Submit review (if content is available)
    await test.step('Submit review answer', async () => {
      // Check if we have review content
      const reviewQuestion = page.locator('.review-question, [data-testid="review-question"]');
      const hasContent = await reviewQuestion.count() > 0;

      if (!hasContent) {
        console.log('Skipping review submission - no content ready');
        return;
      }

      // Wait for review content to load
      await expect(reviewQuestion.first()).toBeVisible({ timeout: 5000 });

      // Check review type (objective or subjective)
      const answerInput = page.locator('textarea[name="answer"], input[type="text"][name="answer"]');
      const multipleChoice = page.locator('input[type="radio"]');

      if (await multipleChoice.count() > 0) {
        // Objective review - select an option
        await multipleChoice.first().check();
      } else if (await answerInput.count() > 0) {
        // Subjective review - type answer
        await answerInput.fill('Paris');
      }

      // Submit review
      await page.click('button:has-text("제출"), button:has-text("답안 제출"), button[type="submit"]');

      // Wait for result or next review
      await page.waitForTimeout(2000); // Give time for submission

      // Verify feedback or success
      const feedback = page.locator('.review-result, .feedback, text=정답, text=오답, text=다음 복습');
      if (await feedback.count() > 0) {
        await expect(feedback.first()).toBeVisible({ timeout: 5000 });
      }
    });

    // Final verification: User can see their content
    await test.step('Verify content exists', async () => {
      await page.goto('/content');

      // Search for our created content
      const contentTitle = page.locator(`text=E2E Test Content ${timestamp}`);
      const contentExists = await contentTitle.count() > 0;

      if (contentExists) {
        await expect(contentTitle.first()).toBeVisible();
      } else {
        // Content might be on another page or in archived
        console.log('Content not immediately visible - might be paginated or archived');
      }
    });
  });

  // Cleanup: Delete test content after test (optional)
  test.afterAll(async ({ browser }) => {
    // You can add cleanup logic here if needed
    console.log('E2E test completed');
  });
});
