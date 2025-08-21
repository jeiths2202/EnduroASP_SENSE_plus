const { test, expect } = require('@playwright/test');

test.describe('OpenASP DevOps - Complete User Flow', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');
  });

  test('homepage loads and displays main navigation', async ({ page }) => {
    // Check main title
    await expect(page.locator('h1')).toContainText('DevOps Dashboard');
    
    // Check navigation menu
    await expect(page.locator('text=DevOps Dashboard')).toBeVisible();
    await expect(page.locator('text=COBOL Converter')).toBeVisible();
    await expect(page.locator('text=CL Converter')).toBeVisible();
    
    // Check system status
    await expect(page.locator('text=System Operational')).toBeVisible();
  });

  test('COBOL converter workflow', async ({ page }) => {
    // Navigate to COBOL converter
    await page.click('text=COBOL Converter');
    await expect(page.locator('h1')).toContainText('DevOps COBOL Converter');
    
    // Check initial state
    await expect(page.locator('text=Ready for Deployment')).toBeVisible();
    
    // Enter COBOL source code
    const sourceTextarea = page.locator('textarea').first();
    await sourceTextarea.fill(`IDENTIFICATION DIVISION.
PROGRAM-ID. HELLO-WORLD.

PROCEDURE DIVISION.
DISPLAY 'Hello, DevOps World!'.
STOP RUN.`);
    
    // Select target language (Java)
    await page.click('button:has-text("Java")');
    
    // Check convert button is enabled
    const convertButton = page.locator('button:has-text("Convert")');
    await expect(convertButton).not.toBeDisabled();
    
    // Start conversion
    await convertButton.click();
    
    // Check conversion progress
    await expect(page.locator('text=Converting...')).toBeVisible();
    
    // Wait for conversion completion (with timeout)
    await expect(page.locator('text=Converting...')).not.toBeVisible({ timeout: 10000 });
    
    // Check converted code appears
    const outputTextarea = page.locator('textarea').nth(1);
    await expect(outputTextarea).not.toBeEmpty();
    
    // Verify download button appears
    await expect(page.locator('button:has-text("Download")')).toBeVisible();
    
    // Check pipeline status changed
    await expect(page.locator('text=Pipeline Success')).toBeVisible({ timeout: 15000 });
  });

  test('CL converter workflow', async ({ page }) => {
    // Navigate to CL converter
    await page.click('text=CL Converter');
    await expect(page.locator('h1')).toContainText('DevOps CL Converter');
    
    // Enter CL source code
    const sourceTextarea = page.locator('textarea').first();
    await sourceTextarea.fill(`PGM
CPYF FROMFILE(SOURCE) TOFILE(TARGET)
CALL PGM(PROCESS)
ENDPGM`);
    
    // Select target language (Shell)
    await page.click('button:has-text("Shell")');
    
    // Start conversion
    await page.click('button:has-text("Convert")');
    
    // Wait for conversion
    await expect(page.locator('text=Converting...')).toBeVisible();
    await expect(page.locator('text=Converting...')).not.toBeVisible({ timeout: 10000 });
    
    // Verify conversion completed
    const outputTextarea = page.locator('textarea').nth(1);
    await expect(outputTextarea).not.toBeEmpty();
    
    // Check command reference is visible
    await expect(page.locator('text=CL Command Reference')).toBeVisible();
    await expect(page.locator('text=File Operations')).toBeVisible();
  });

  test('dashboard real-time updates', async ({ page }) => {
    // Check initial dashboard state
    await expect(page.locator('text=Active Pipelines')).toBeVisible();
    await expect(page.locator('text=Real-time Activity')).toBeVisible();
    
    // Check pipeline metrics
    await expect(page.locator('text=Conversion Success Rate')).toBeVisible();
    await expect(page.locator('text=Average Build Time')).toBeVisible();
    
    // Check activity feed updates (wait for dynamic content)
    const activityFeed = page.locator('[data-testid="activity-feed"]').or(
      page.locator('text=Real-time Activity').locator('..').locator('..')
    );
    
    // Wait for activity items to load
    await page.waitForTimeout(2000);
    
    // Check architecture overview
    await expect(page.locator('text=DevOps Architecture')).toBeVisible();
    await expect(page.locator('text=Source Conversion')).toBeVisible();
    await expect(page.locator('text=CI/CD Pipeline')).toBeVisible();
  });

  test('language switching functionality', async ({ page }) => {
    // Check language selector
    const languageSelect = page.locator('select').first();
    await expect(languageSelect).toBeVisible();
    
    // Switch to Japanese
    await languageSelect.selectOption('ja');
    await page.waitForTimeout(500);
    
    // Switch to Korean
    await languageSelect.selectOption('ko');
    await page.waitForTimeout(500);
    
    // Switch back to English
    await languageSelect.selectOption('en');
    await page.waitForTimeout(500);
    
    // Verify page still works
    await expect(page.locator('h1')).toContainText('DevOps Dashboard');
  });

  test('dark mode toggle', async ({ page }) => {
    // Find and click dark mode toggle
    const darkModeToggle = page.locator('button:has-text("🌙")').or(
      page.locator('button').filter({ hasText: /🌙|☀️/ })
    );
    
    await expect(darkModeToggle).toBeVisible();
    await darkModeToggle.click();
    
    // Verify dark mode is applied (check for dark theme classes)
    await expect(page.locator('body')).toHaveClass(/dark/);
    
    // Toggle back to light mode
    await page.locator('button:has-text("☀️")').click();
    await expect(page.locator('body')).not.toHaveClass(/dark/);
  });

  test('responsive design on mobile', async ({ page }) => {
    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });
    
    // Check mobile navigation works
    await expect(page.locator('h1')).toBeVisible();
    
    // Navigate to COBOL converter on mobile
    await page.click('text=COBOL Converter');
    
    // Check mobile-friendly layout
    await expect(page.locator('h1')).toContainText('DevOps COBOL Converter');
    
    // Test mobile form interaction
    const textarea = page.locator('textarea').first();
    await textarea.fill('IDENTIFICATION DIVISION.');
    await expect(textarea).toHaveValue('IDENTIFICATION DIVISION.');
  });

  test('file upload functionality', async ({ page }) => {
    await page.click('text=COBOL Converter');
    
    // Create a test file
    const fileContent = `IDENTIFICATION DIVISION.
PROGRAM-ID. TEST-UPLOAD.
PROCEDURE DIVISION.
DISPLAY 'File upload test'.
STOP RUN.`;
    
    // Find file input
    const fileInput = page.locator('input[type="file"]');
    
    // Create a temporary file for upload test
    await fileInput.setInputFiles({
      name: 'test-program.cbl',
      mimeType: 'text/plain',
      buffer: Buffer.from(fileContent)
    });
    
    // Verify file content appears in textarea
    const textarea = page.locator('textarea').first();
    await expect(textarea).toHaveValue(fileContent);
  });

  test('error handling and edge cases', async ({ page }) => {
    await page.click('text=COBOL Converter');
    
    // Test empty conversion attempt
    const convertButton = page.locator('button:has-text("Convert")');
    await expect(convertButton).toBeDisabled();
    
    // Add minimal code
    await page.locator('textarea').first().fill('INVALID CODE');
    await expect(convertButton).not.toBeDisabled();
    
    // Test conversion with invalid code
    await convertButton.click();
    
    // Should handle gracefully (mock conversion will still work)
    await expect(page.locator('text=Converting...')).toBeVisible();
  });

  test('pipeline deployment simulation', async ({ page }) => {
    await page.click('text=COBOL Converter');
    
    // Complete a conversion first
    await page.locator('textarea').first().fill('IDENTIFICATION DIVISION.\nPROGRAM-ID. DEPLOY-TEST.');
    await page.click('button:has-text("Java")');
    await page.click('button:has-text("Convert")');
    
    // Wait for conversion
    await expect(page.locator('text=Converting...')).not.toBeVisible({ timeout: 10000 });
    
    // Click deploy to pipeline
    const deployButton = page.locator('button:has-text("Deploy to Pipeline")');
    await expect(deployButton).not.toBeDisabled();
    await deployButton.click();
    
    // Check pipeline status updates
    await expect(page.locator('text=Pipeline Running')).toBeVisible({ timeout: 5000 });
    
    // Wait for completion
    await expect(page.locator('text=Pipeline Success')).toBeVisible({ timeout: 10000 });
  });

  test('accessibility compliance', async ({ page }) => {
    // Check main heading structure
    const h1 = page.locator('h1');
    await expect(h1).toBeVisible();
    
    // Check form labels
    await page.click('text=COBOL Converter');
    
    // Check buttons have accessible names
    const convertButton = page.locator('button:has-text("Convert")');
    await expect(convertButton).toHaveAttribute('type', 'button');
    
    // Check focus management
    await convertButton.focus();
    await expect(convertButton).toBeFocused();
    
    // Test keyboard navigation
    await page.keyboard.press('Tab');
    await page.keyboard.press('Tab');
  });
});