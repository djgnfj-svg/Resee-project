import { test, expect } from '@playwright/test';

test.describe('Content Management', () => {
  test.beforeEach(async ({ page }) => {
    // Login before each test
    await page.goto('/');
    await page.getByLabelText(/사용자명/i).fill('testuser');
    await page.getByLabelText(/비밀번호/i).fill('password123');
    await page.getByRole('button', { name: /로그인/i }).click();
    await expect(page).toHaveURL(/\//);
  });

  test('should navigate to content creation page', async ({ page }) => {
    await page.getByRole('button', { name: /새 콘텐츠/i }).click();
    
    await expect(page).toHaveURL(/\/content\/new/);
    await expect(page.getByRole('heading', { name: /새 콘텐츠 생성/i })).toBeVisible();
  });

  test('should create new content successfully', async ({ page }) => {
    await page.goto('/content/new');
    
    // Fill content form
    await page.getByLabelText(/제목/i).fill('E2E Test Content');
    
    // Fill content using BlockNote editor
    const editor = page.getByTestId('blocknote-editor');
    await editor.getByRole('textbox').fill('This is E2E test content with **bold** text.');
    
    // Select category
    await page.getByLabelText(/카테고리/i).selectOption('1');
    
    // Select tags
    await page.getByText('basics').click();
    await page.getByText('tutorial').click();
    
    // Set priority
    await page.getByLabelText(/우선순위/i).selectOption('high');
    
    // Save content
    await page.getByRole('button', { name: /저장/i }).click();
    
    // Should redirect to content list
    await expect(page).toHaveURL(/\/content/);
    await expect(page.getByText('E2E Test Content')).toBeVisible();
  });

  test('should show validation errors for empty content', async ({ page }) => {
    await page.goto('/content/new');
    
    // Try to save without title
    await page.getByRole('button', { name: /저장/i }).click();
    
    await expect(page.getByText(/제목은 필수입니다/i)).toBeVisible();
  });

  test('should edit existing content', async ({ page }) => {
    await page.goto('/content');
    
    // Wait for content to load
    await expect(page.getByText('Python Variables')).toBeVisible();
    
    // Click edit button for first content
    await page.getByRole('button', { name: /편집/i }).first().click();
    
    await expect(page).toHaveURL(/\/content\/\d+\/edit/);
    
    // Modify title
    const titleInput = page.getByLabelText(/제목/i);
    await titleInput.clear();
    await titleInput.fill('Updated Python Variables');
    
    // Save changes
    await page.getByRole('button', { name: /저장/i }).click();
    
    // Should return to content list with updated content
    await expect(page).toHaveURL(/\/content/);
    await expect(page.getByText('Updated Python Variables')).toBeVisible();
  });

  test('should delete content', async ({ page }) => {
    await page.goto('/content');
    
    // Wait for content to load
    await expect(page.getByText('Python Variables')).toBeVisible();
    
    // Click delete button
    await page.getByRole('button', { name: /삭제/i }).first().click();
    
    // Confirm deletion in modal
    await page.getByRole('button', { name: /확인/i }).click();
    
    // Content should be removed from list
    await expect(page.getByText('Python Variables')).not.toBeVisible();
  });

  test('should filter content by category', async ({ page }) => {
    await page.goto('/content');
    
    // Select category filter
    await page.getByLabelText(/카테고리 필터/i).selectOption('Python');
    
    // Should show only Python content
    await expect(page.getByText('Python Variables')).toBeVisible();
    await expect(page.getByText('JavaScript Functions')).not.toBeVisible();
  });

  test('should search content', async ({ page }) => {
    await page.goto('/content');
    
    // Search for content
    await page.getByPlaceholderText(/검색/i).fill('Python');
    await page.keyboard.press('Enter');
    
    // Should show filtered results
    await expect(page.getByText('Python Variables')).toBeVisible();
    await expect(page.getByText('JavaScript Functions')).not.toBeVisible();
  });

  test('should sort content', async ({ page }) => {
    await page.goto('/content');
    
    // Change sort order
    await page.getByLabelText(/정렬/i).selectOption('title');
    
    // Content should be reordered
    const contentItems = page.getByTestId('content-item');
    await expect(contentItems.first()).toContainText('JavaScript Functions');
  });

  test('should paginate content list', async ({ page }) => {
    await page.goto('/content');
    
    // If pagination exists, test it
    const nextButton = page.getByRole('button', { name: /다음/i });
    if (await nextButton.isVisible()) {
      await nextButton.click();
      
      // Should navigate to next page
      await expect(page).toHaveURL(/\/content\?page=2/);
    }
  });


  test('should create and assign new category', async ({ page }) => {
    await page.goto('/content/new');
    
    // Open category creation modal
    await page.getByRole('button', { name: /새 카테고리/i }).click();
    
    // Fill category form
    await page.getByLabelText(/카테고리 이름/i).fill('E2E Test Category');
    await page.getByLabelText(/설명/i).fill('Category created during E2E test');
    
    // Save category
    await page.getByRole('button', { name: /생성/i }).click();
    
    // Category should be available in the select
    await expect(page.getByText('E2E Test Category')).toBeVisible();
  });

  test('should create and assign new tag', async ({ page }) => {
    await page.goto('/content/new');
    
    // Create new tag
    const tagInput = page.getByPlaceholderText(/새 태그 입력/i);
    await tagInput.fill('e2e-test-tag');
    await tagInput.press('Enter');
    
    // Tag should be created and selected
    await expect(page.getByText('e2e-test-tag')).toBeVisible();
    await expect(page.getByText('e2e-test-tag')).toHaveClass(/selected/);
  });

  test('should handle content preview', async ({ page }) => {
    await page.goto('/content/new');
    
    await page.getByLabelText(/제목/i).fill('Preview Test');
    
    // Add markdown content
    const editor = page.getByTestId('blocknote-editor');
    await editor.getByRole('textbox').fill('# Header\n\nThis is **bold** text.');
    
    // Open preview
    await page.getByRole('button', { name: /미리보기/i }).click();
    
    // Should show rendered content
    await expect(page.getByRole('heading', { name: 'Header' })).toBeVisible();
    await expect(page.getByText('bold')).toHaveCSS('font-weight', '700');
  });

  test('should save content as draft', async ({ page }) => {
    await page.goto('/content/new');
    
    await page.getByLabelText(/제목/i).fill('Draft Content');
    
    // Save as draft
    await page.getByRole('button', { name: /임시저장/i }).click();
    
    // Should show draft status
    await expect(page.getByText(/임시저장되었습니다/i)).toBeVisible();
  });

  test('should handle content versioning', async ({ page }) => {
    await page.goto('/content/1/edit');
    
    // Make changes
    const titleInput = page.getByLabelText(/제목/i);
    await titleInput.clear();
    await titleInput.fill('Versioned Content');
    
    await page.getByRole('button', { name: /저장/i }).click();
    
    // Check version history
    await page.getByRole('button', { name: /버전 기록/i }).click();
    
    // Should show version history
    await expect(page.getByText(/버전 1/i)).toBeVisible();
    await expect(page.getByText(/버전 2/i)).toBeVisible();
  });

  test('should export content', async ({ page }) => {
    await page.goto('/content');
    
    // Select content
    await page.getByRole('checkbox').first().check();
    
    // Export selected content
    await page.getByRole('button', { name: /내보내기/i }).click();
    
    // Choose export format
    await page.getByRole('button', { name: /Markdown/i }).click();
    
    // Should trigger download
    const downloadPromise = page.waitForEvent('download');
    await page.getByRole('button', { name: /다운로드/i }).click();
    const download = await downloadPromise;
    
    expect(download.suggestedFilename()).toMatch(/\.md$/);
  });

  test('should import content', async ({ page }) => {
    await page.goto('/content');
    
    // Open import dialog
    await page.getByRole('button', { name: /가져오기/i }).click();
    
    // Upload file
    const fileContent = '# Imported Content\n\nThis is imported content.';
    await page.getByRole('button', { name: /파일 선택/i }).setInputFiles({
      name: 'import.md',
      mimeType: 'text/markdown',
      buffer: Buffer.from(fileContent),
    });
    
    // Import content
    await page.getByRole('button', { name: /가져오기/i }).click();
    
    // Should show imported content
    await expect(page.getByText('Imported Content')).toBeVisible();
  });

  test('should handle bulk operations', async ({ page }) => {
    await page.goto('/content');
    
    // Select multiple content items
    await page.getByRole('checkbox').first().check();
    await page.getByRole('checkbox').nth(1).check();
    
    // Perform bulk action
    await page.getByRole('button', { name: /일괄 작업/i }).click();
    await page.getByRole('button', { name: /카테고리 변경/i }).click();
    
    // Select new category
    await page.getByLabelText(/카테고리 선택/i).selectOption('Django');
    await page.getByRole('button', { name: /적용/i }).click();
    
    // Content should be updated
    await expect(page.getByText('Django')).toBeVisible();
  });

  test('should be responsive on mobile', async ({ page }) => {
    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });
    
    await page.goto('/content');
    
    // Mobile menu should be visible
    await expect(page.getByRole('button', { name: /메뉴/i })).toBeVisible();
    
    // Content cards should stack vertically
    const contentGrid = page.getByTestId('content-grid');
    await expect(contentGrid).toHaveCSS('flex-direction', 'column');
  });
});