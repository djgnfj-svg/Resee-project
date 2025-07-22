import { test, expect } from '@playwright/test';

test.describe('Authentication Flow', () => {
  test.beforeEach(async ({ page }) => {
    // Clear storage before each test
    await page.context().clearCookies();
    await page.evaluate(() => localStorage.clear());
  });

  test('should show login page by default', async ({ page }) => {
    await page.goto('/');
    
    await expect(page.getByRole('heading', { name: /로그인/i })).toBeVisible();
    await expect(page.getByLabelText(/이메일/i)).toBeVisible();
    await expect(page.getByLabelText(/비밀번호/i)).toBeVisible();
    await expect(page.getByRole('button', { name: /로그인/i })).toBeVisible();
  });

  test('should navigate to registration page', async ({ page }) => {
    await page.goto('/');
    
    await page.getByText(/회원가입/i).click();
    
    await expect(page).toHaveURL(/\/register/);
    await expect(page.getByRole('heading', { name: /회원가입/i })).toBeVisible();
  });

  test('should complete full registration flow with email verification', async ({ page }) => {
    await page.goto('/register');
    
    // Fill registration form
    const timestamp = Date.now();
    const testEmail = `e2etest${timestamp}@example.com`;
    
    await page.getByLabelText(/이메일/i).fill(testEmail);
    await page.getByLabelText(/성/i).fill('E2E');
    await page.getByLabelText(/이름/i).fill('User');
    await page.getByLabelText(/^비밀번호$/i).fill('e2epassword123!');
    await page.getByLabelText(/비밀번호 확인/i).fill('e2epassword123!');
    
    // Submit registration
    await page.getByRole('button', { name: /회원가입/i }).click();
    
    // Should show email verification message
    await expect(page.getByText(/이메일 인증이 필요합니다/i)).toBeVisible();
  });

  test('should show validation errors for invalid registration', async ({ page }) => {
    await page.goto('/register');
    
    // Try to submit with mismatched passwords
    await page.getByLabelText(/이메일/i).fill('test@example.com');
    await page.getByLabelText(/^비밀번호$/i).fill('password123');
    await page.getByLabelText(/비밀번호 확인/i).fill('differentpassword');
    
    await page.getByRole('button', { name: /회원가입/i }).click();
    
    await expect(page.getByText(/비밀번호가 일치하지 않습니다/i)).toBeVisible();
  });

  test('should complete login flow with test user', async ({ page }) => {
    await page.goto('/');
    
    // Fill login form with test user
    await page.getByLabelText(/이메일/i).fill('test@resee.com');
    await page.getByLabelText(/비밀번호/i).fill('test123!');
    
    // Submit login
    await page.getByRole('button', { name: /로그인/i }).click();
    
    // Should redirect to dashboard
    await expect(page).toHaveURL(/\//);
    await expect(page.getByText(/대시보드/i)).toBeVisible();
    
    // Should show user info in navigation
    await expect(page.getByText('test@resee.com')).toBeVisible();
  });

  test('should show error for invalid login credentials', async ({ page }) => {
    await page.goto('/');
    
    await page.getByLabelText(/이메일/i).fill('wrong@example.com');
    await page.getByLabelText(/비밀번호/i).fill('wrongpassword');
    
    await page.getByRole('button', { name: /로그인/i }).click();
    
    await expect(page.getByText(/로그인에 실패했습니다/i)).toBeVisible();
  });

  test('should logout successfully', async ({ page }) => {
    // Login first
    await page.goto('/');
    await page.getByLabelText(/이메일/i).fill('test@resee.com');
    await page.getByLabelText(/비밀번호/i).fill('test123!');
    await page.getByRole('button', { name: /로그인/i }).click();
    
    await expect(page).toHaveURL(/\//);
    
    // Logout
    await page.getByRole('button', { name: /로그아웃/i }).click();
    
    // Should redirect to login page
    await expect(page).toHaveURL(/\/login/);
    await expect(page.getByRole('heading', { name: /로그인/i })).toBeVisible();
  });

  test('should remember login state on page refresh', async ({ page }) => {
    // Login
    await page.goto('/');
    await page.getByLabelText(/이메일/i).fill('test@resee.com');
    await page.getByLabelText(/비밀번호/i).fill('test123!');
    await page.getByRole('button', { name: /로그인/i }).click();
    
    await expect(page).toHaveURL(/\//);
    
    // Refresh page
    await page.reload();
    
    // Should still be logged in
    await expect(page.getByText('test@resee.com')).toBeVisible();
    await expect(page.getByText(/대시보드/i)).toBeVisible();
  });

  test('should handle session expiration', async ({ page }) => {
    // Login
    await page.goto('/');
    await page.getByLabelText(/이메일/i).fill('test@resee.com');
    await page.getByLabelText(/비밀번호/i).fill('test123!');
    await page.getByRole('button', { name: /로그인/i }).click();
    
    await expect(page).toHaveURL(/\//);
    
    // Simulate session expiration by clearing tokens
    await page.evaluate(() => {
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
    });
    
    // Try to navigate to protected route
    await page.goto('/content');
    
    // Should redirect to login
    await expect(page).toHaveURL(/\/login/);
  });

  test('should show loading states during authentication', async ({ page }) => {
    await page.goto('/');
    
    await page.getByLabelText(/이메일/i).fill('test@resee.com');
    await page.getByLabelText(/비밀번호/i).fill('test123!');
    
    // Click login and immediately check for loading state
    await page.getByRole('button', { name: /로그인/i }).click();
    
    // Should show loading state
    await expect(page.getByText(/로그인 중/i)).toBeVisible();
    await expect(page.getByRole('button', { name: /로그인/i })).toBeDisabled();
  });

  test('should validate email format in registration', async ({ page }) => {
    await page.goto('/register');
    
    await page.getByLabelText(/이메일/i).fill('invalid-email');
    await page.getByRole('button', { name: /회원가입/i }).click();
    
    await expect(page.getByText(/올바른 이메일 형식이 아닙니다/i)).toBeVisible();
  });

  test('should handle keyboard navigation', async ({ page }) => {
    await page.goto('/');
    
    // Tab through form elements
    await page.keyboard.press('Tab');
    await expect(page.getByLabelText(/이메일/i)).toBeFocused();
    
    await page.keyboard.press('Tab');
    await expect(page.getByLabelText(/비밀번호/i)).toBeFocused();
    
    await page.keyboard.press('Tab');
    await expect(page.getByRole('button', { name: /로그인/i })).toBeFocused();
  });

  test('should submit form with Enter key', async ({ page }) => {
    await page.goto('/');
    
    await page.getByLabelText(/이메일/i).fill('test@resee.com');
    await page.getByLabelText(/비밀번호/i).fill('test123!');
    
    // Press Enter in password field
    await page.getByLabelText(/비밀번호/i).press('Enter');
    
    // Should submit the form
    await expect(page).toHaveURL(/\//);
  });

  test('should show Google Sign-In button', async ({ page }) => {
    await page.goto('/');
    
    // Should show Google login option
    await expect(page.getByRole('button', { name: /Google로 로그인/i })).toBeVisible();
  });

  test('should handle email verification workflow', async ({ page }) => {
    // First register a user (without actually verifying email)
    await page.goto('/register');
    
    const timestamp = Date.now();
    const testEmail = `verify${timestamp}@example.com`;
    
    await page.getByLabelText(/이메일/i).fill(testEmail);
    await page.getByLabelText(/성/i).fill('Test');
    await page.getByLabelText(/이름/i).fill('User');
    await page.getByLabelText(/^비밀번호$/i).fill('testpass123!');
    await page.getByLabelText(/비밀번호 확인/i).fill('testpass123!');
    
    await page.getByRole('button', { name: /회원가입/i }).click();
    
    // Should show email verification required message
    await expect(page.getByText(/이메일 인증이 필요합니다/i)).toBeVisible();
    
    // Should have option to resend verification email
    await expect(page.getByRole('button', { name: /인증 메일 다시 보내기/i })).toBeVisible();
  });

  test('should show password strength indicator during registration', async ({ page }) => {
    await page.goto('/register');
    
    const passwordInput = page.getByLabelText(/^비밀번호$/i);
    
    // Test weak password
    await passwordInput.fill('123');
    await expect(page.getByText(/약함/i)).toBeVisible();
    
    // Test medium password  
    await passwordInput.clear();
    await passwordInput.fill('password123');
    await expect(page.getByText(/보통/i)).toBeVisible();
    
    // Test strong password
    await passwordInput.clear();
    await passwordInput.fill('StrongPass123!');
    await expect(page.getByText(/강함/i)).toBeVisible();
  });
});