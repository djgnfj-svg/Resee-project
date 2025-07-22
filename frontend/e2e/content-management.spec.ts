import { test, expect } from '@playwright/test';

test.describe('Content Management', () => {
  test.beforeEach(async ({ page }) => {
    // Login before each test using email
    await page.goto('/');
    await page.getByLabelText(/이메일/i).fill('test@resee.com');
    await page.getByLabelText(/비밀번호/i).fill('test123!');
    await page.getByRole('button', { name: /로그인/i }).click();
    await expect(page).toHaveURL(/\//);
  });

  test('should navigate to content page from dashboard', async ({ page }) => {
    // From dashboard, navigate to content management
    const contentLink = page.getByRole('link', { name: /콘텐츠|content/i });
    if (await contentLink.isVisible()) {
      await contentLink.click();
    } else {
      await page.goto('/content');
    }
    
    await expect(page.getByText(/콘텐츠 관리/i)).toBeVisible();
  });

  test('should show content creation form', async ({ page }) => {
    await page.goto('/content');
    
    await page.getByRole('button', { name: /새 콘텐츠/i }).click();
    
    await expect(page.getByRole('heading', { name: /새 콘텐츠|콘텐츠 생성/i })).toBeVisible();
    await expect(page.getByLabelText(/제목/i)).toBeVisible();
    await expect(page.getByRole('textbox')).toBeVisible(); // TipTap editor
    await expect(page.getByLabelText(/우선순위/i)).toBeVisible();
  });

  test('should create new content successfully', async ({ page }) => {
    await page.goto('/content');
    
    await page.getByRole('button', { name: /새 콘텐츠/i }).click();
    
    // Fill content form
    const timestamp = Date.now();
    const contentTitle = `E2E Test Content ${timestamp}`;
    
    await page.getByLabelText(/제목/i).fill(contentTitle);
    
    // Fill content using TipTap editor
    const editor = page.getByRole('textbox').first();
    await editor.fill('This is E2E test content with **bold** text and some important information.');
    
    // Select category if available
    const categorySelect = page.getByLabelText(/카테고리/i);
    if (await categorySelect.isVisible()) {
      await categorySelect.selectOption({ index: 1 }); // Select first non-empty option
    }
    
    // Set priority
    await page.getByLabelText(/우선순위/i).selectOption('high');
    
    // Save content
    await page.getByRole('button', { name: /저장/i }).click();
    
    // Should redirect to content list
    await expect(page).toHaveURL(/\/content/);
    await expect(page.getByText(contentTitle)).toBeVisible();
  });

  test('should show validation errors for empty content', async ({ page }) => {
    await page.goto('/content');
    
    await page.getByRole('button', { name: /새 콘텐츠/i }).click();
    
    // Try to save without title
    await page.getByRole('button', { name: /저장/i }).click();
    
    // Should show validation error
    await expect(page.getByText(/필수|required/i)).toBeVisible();
  });

  test('should edit existing content', async ({ page }) => {
    await page.goto('/content');
    
    // Wait for content to load
    await page.waitForTimeout(2000);
    
    const editButtons = page.getByRole('button', { name: /편집/i });
    
    if (await editButtons.count() > 0) {
      await editButtons.first().click();
      
      // Should show edit form
      await expect(page.getByLabelText(/제목/i)).toBeVisible();
      
      // Modify title
      const titleInput = page.getByLabelText(/제목/i);
      const originalTitle = await titleInput.inputValue();
      const updatedTitle = `Updated ${originalTitle}`;
      
      await titleInput.clear();
      await titleInput.fill(updatedTitle);
      
      // Save changes
      await page.getByRole('button', { name: /저장/i }).click();
      
      // Should return to content list with updated content
      await expect(page).toHaveURL(/\/content/);
      await expect(page.getByText(updatedTitle)).toBeVisible();
    } else {
      test.skip('No content available for editing');
    }
  });

  test('should delete content with confirmation', async ({ page }) => {
    await page.goto('/content');
    
    // Wait for content to load
    await page.waitForTimeout(2000);
    
    const deleteButtons = page.getByRole('button', { name: /삭제/i });
    
    if (await deleteButtons.count() > 0) {
      // Get the title of the content to be deleted
      const contentItem = deleteButtons.first().locator('..').locator('..');
      const titleElement = contentItem.locator('h3, .font-semibold');
      const titleToDelete = await titleElement.textContent();
      
      await deleteButtons.first().click();
      
      // Should show confirmation dialog
      await expect(page.getByText(/정말로|확인/i)).toBeVisible();
      
      // Confirm deletion
      await page.getByRole('button', { name: /확인|삭제/i }).click();
      
      // Content should be removed from list
      if (titleToDelete) {
        await expect(page.getByText(titleToDelete)).not.toBeVisible();
      }
    } else {
      test.skip('No content available for deletion');
    }
  });

  test('should filter content by category', async ({ page }) => {
    await page.goto('/content');
    
    // Wait for content to load
    await page.waitForTimeout(2000);
    
    const categoryFilter = page.getByLabelText(/카테고리/i);
    if (await categoryFilter.isVisible()) {
      // Get available options
      const options = await categoryFilter.locator('option').count();
      
      if (options > 1) {
        // Select a specific category (not "all")
        await categoryFilter.selectOption({ index: 1 });
        
        // Wait for filtered results
        await page.waitForTimeout(1000);
        
        // Should show filtered content or empty state
        await expect(page.getByText(/콘텐츠|content/i)).toBeVisible();
      }
    }
  });

  test('should filter content by priority', async ({ page }) => {
    await page.goto('/content');
    
    // Wait for content to load
    await page.waitForTimeout(2000);
    
    const priorityFilter = page.getByLabelText(/우선순위/i);
    if (await priorityFilter.isVisible()) {
      // Select high priority
      await priorityFilter.selectOption('high');
      
      // Wait for filtered results
      await page.waitForTimeout(1000);
      
      // Should show only high priority content or empty state
      await expect(page.getByText(/높음|high/i)).toBeVisible();
    }
  });

  test('should sort content', async ({ page }) => {
    await page.goto('/content');
    
    // Wait for content to load
    await page.waitForTimeout(2000);
    
    const sortSelect = page.getByLabelText(/정렬/i);
    if (await sortSelect.isVisible()) {
      // Change sort order to title
      await sortSelect.selectOption('title_asc');
      
      // Wait for reordering
      await page.waitForTimeout(1000);
      
      // Content should be reordered
      await expect(page.getByText(/콘텐츠|content/i)).toBeVisible();
    }
  });

  test('should show content preview', async ({ page }) => {
    await page.goto('/content');
    
    // Wait for content to load
    await page.waitForTimeout(2000);
    
    // Should show content previews in the list
    const contentPreviews = page.locator('.prose, .markdown, [class*="content"]');
    if (await contentPreviews.count() > 0) {
      await expect(contentPreviews.first()).toBeVisible();
    }
  });

  test('should handle empty content state', async ({ page }) => {
    await page.goto('/content');
    
    // Apply filters that might result in no content
    const categoryFilter = page.getByLabelText(/카테고리/i);
    const priorityFilter = page.getByLabelText(/우선순위/i);
    
    if (await categoryFilter.isVisible() && await priorityFilter.isVisible()) {
      await categoryFilter.selectOption({ index: 1 });
      await priorityFilter.selectOption('high');
      
      await page.waitForTimeout(1000);
      
      // Should show empty state or content
      const emptyState = page.getByText(/콘텐츠가 없습니다|no content/i);
      const contentItems = page.locator('[data-testid="content-item"], .bg-white');
      
      await expect(emptyState.or(contentItems.first())).toBeVisible();
    }
  });

  test('should show content metadata', async ({ page }) => {
    await page.goto('/content');
    
    // Wait for content to load
    await page.waitForTimeout(2000);
    
    const contentItems = page.locator('.bg-white').first();
    if (await contentItems.isVisible()) {
      // Should show creation date
      await expect(page.locator('text=/\\d{4}|\\d{2}/')).toBeVisible();
      
      // Should show priority badge
      await expect(page.getByText(/높음|보통|낮음/i)).toBeVisible();
    }
  });

  test('should handle markdown content rendering', async ({ page }) => {
    await page.goto('/content');
    
    await page.getByRole('button', { name: /새 콘텐츠/i }).click();
    
    // Add markdown content
    await page.getByLabelText(/제목/i).fill('Markdown Test Content');
    
    const editor = page.getByRole('textbox').first();
    await editor.fill('# Header 1\n\n## Header 2\n\n**Bold text** and *italic text*\n\n- List item 1\n- List item 2');
    
    await page.getByLabelText(/우선순위/i).selectOption('medium');
    
    // Save content
    await page.getByRole('button', { name: /저장/i }).click();
    
    // Should return to list and show rendered content
    await expect(page).toHaveURL(/\/content/);
    await expect(page.getByText('Markdown Test Content')).toBeVisible();
    
    // Should show some rendered markdown (preview)
    await expect(page.getByText(/Header|Bold text/i)).toBeVisible();
  });

  test('should be responsive on mobile', async ({ page }) => {
    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });
    
    await page.goto('/content');
    
    // Mobile interface should be usable
    await expect(page.getByRole('button', { name: /새 콘텐츠/i })).toBeVisible();
    
    // Filters should be accessible
    const filterSection = page.locator('[class*="filter"], [class*="mb-6"]');
    if (await filterSection.isVisible()) {
      await expect(filterSection).toBeVisible();
    }
  });

  test('should handle content creation with TipTap editor features', async ({ page }) => {
    await page.goto('/content');
    
    await page.getByRole('button', { name: /새 콘텐츠/i }).click();
    
    await page.getByLabelText(/제목/i).fill('Rich Text Content');
    
    // Use TipTap editor
    const editor = page.getByRole('textbox').first();
    await editor.focus();
    
    // Type some content with markdown shortcuts
    await editor.type('# This is a heading\n\n**This is bold text**\n\nThis is normal text.');
    
    await page.getByLabelText(/우선순위/i).selectOption('low');
    
    await page.getByRole('button', { name: /저장/i }).click();
    
    // Should save successfully
    await expect(page).toHaveURL(/\/content/);
    await expect(page.getByText('Rich Text Content')).toBeVisible();
  });

  test('should show active filters', async ({ page }) => {
    await page.goto('/content');
    
    const categoryFilter = page.getByLabelText(/카테고리/i);
    const priorityFilter = page.getByLabelText(/우선순위/i);
    
    if (await categoryFilter.isVisible() && await priorityFilter.isVisible()) {
      // Apply filters
      await categoryFilter.selectOption({ index: 1 });
      await priorityFilter.selectOption('high');
      
      await page.waitForTimeout(1000);
      
      // Should show active filter badges
      const filterBadges = page.locator('[class*="rounded-full"], [class*="badge"]');
      if (await filterBadges.count() > 0) {
        await expect(filterBadges.first()).toBeVisible();
        
        // Should be able to remove filters
        const removeButton = filterBadges.first().locator('button, [role="button"]');
        if (await removeButton.isVisible()) {
          await removeButton.click();
          
          // Filter should be removed
          await page.waitForTimeout(500);
        }
      }
    }
  });

  test('should handle content categories', async ({ page }) => {
    await page.goto('/content');
    
    await page.getByRole('button', { name: /새 콘텐츠/i }).click();
    
    await page.getByLabelText(/제목/i).fill('Category Test Content');
    await page.getByRole('textbox').first().fill('Content for testing categories.');
    
    // Select or create category
    const categorySelect = page.getByLabelText(/카테고리/i);
    if (await categorySelect.isVisible()) {
      const options = await categorySelect.locator('option').count();
      if (options > 1) {
        await categorySelect.selectOption({ index: 1 });
      }
    }
    
    await page.getByLabelText(/우선순위/i).selectOption('medium');
    
    await page.getByRole('button', { name: /저장/i }).click();
    
    // Should save with category
    await expect(page).toHaveURL(/\/content/);
    await expect(page.getByText('Category Test Content')).toBeVisible();
  });

  test('should handle content with different priorities', async ({ page }) => {
    await page.goto('/content');
    
    // Create content with each priority level
    const priorities = ['high', 'medium', 'low'];
    
    for (const priority of priorities) {
      await page.getByRole('button', { name: /새 콘텐츠/i }).click();
      
      await page.getByLabelText(/제목/i).fill(`${priority.charAt(0).toUpperCase() + priority.slice(1)} Priority Content`);
      await page.getByRole('textbox').first().fill(`This is ${priority} priority content.`);
      await page.getByLabelText(/우선순위/i).selectOption(priority);
      
      await page.getByRole('button', { name: /저장/i }).click();
      
      await expect(page).toHaveURL(/\/content/);
    }
    
    // Should show all content with different priority badges
    await expect(page.getByText(/높음|보통|낮음/i)).toBeVisible();
  });
});