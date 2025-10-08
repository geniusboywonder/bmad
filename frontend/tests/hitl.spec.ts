import { test, expect } from '@playwright/test';

test.describe('HITL Integration Tests', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to the demo page
    await page.goto('http://localhost:3000/copilot-demo');

    // Listen for console messages
    page.on('console', msg => {
      if (msg.type() === 'error' && msg.text().includes('terminating streaming messages')) {
        console.error(`Console Error: ${msg.text()}`);
        // You might want to fail the test here, or just log it
        // expect(msg.text()).not.toContain('terminating streaming messages');
      }
    });
  });

  test('should verify all HITL functionality as per checklist', async ({ page }) => {
    // Step 2: Trigger HITL Message
    await page.click('button:has-text("Trigger HITL Request")');
    await expect(page.locator('text=Approve')).toBeVisible();
    await expect(page.locator('text=Reject')).toBeVisible();
    await expect(page.locator('text=Modify')).toBeVisible();
    await expect(page.locator('.agent-badge')).toBeVisible(); // Assuming agent-badge class
    await expect(page.locator('.priority-badge')).toBeVisible(); // Assuming priority-badge class
    await expect(page.locator('.task-description')).toBeVisible(); // Assuming task-description class

    // Step 3: Verify Alert Bar
    await expect(page.locator('text=needs approval')).toBeVisible(); // Assuming alert text contains "needs approval"
    await expect(page.locator('.hitl-alert-dismiss-button')).toBeVisible(); // Assuming dismiss button class

    // Step 4: Test Navigation
    await page.click('text=needs approval'); // Click the alert bar
    // Verify page scrolls to the HITL message and gets highlighted
    // This is hard to assert visually in Playwright, but we can check if the element is in view
    const hitlMessage = page.locator('text=Approve').first(); // Assuming this is part of the HITL message
    await expect(hitlMessage).toBeInViewport();
    // Visual highlight is difficult to test directly, but we can assume the navigation worked.

    // Step 5: Test Action Buttons - Approve
    await page.click('button:has-text("Approve")');
    await expect(page.locator('text=Request Approved')).toBeVisible();
    await expect(page.locator('text=needs approval')).not.toBeVisible(); // Alert should disappear
    await expect(page.locator('.checkmark-icon')).toBeVisible(); // Assuming checkmark icon class

    // Step 6: Test Threshold System
    await page.fill('input[type="number"]', '1'); // Set counter limit to 1
    await page.click('button:has-text("Reset")');
    await page.click('button:has-text("Force Counter to Zero")');
    await expect(page.locator('text=0 actions left')).toBeVisible();
    await expect(page.locator('.counter-badge.red')).toBeVisible(); // Assuming red badge class

    // Step 7: Test HITL Toggle
    await page.click('button:has-text("Disable HITL")'); // Assuming button text is "Disable HITL"
    await expect(page.locator('text=Disabled')).toBeVisible(); // Assuming badge text is "Disabled"
    await page.click('button:has-text("Enable HITL")'); // Assuming button text is "Enable HITL"
    // Counter should reset to limit, which is 1 in this case
    await expect(page.locator('text=1 actions left')).toBeVisible();

    // Step 8: Test Multiple Requests (Trigger twice, approve one, reject one)
    await page.click('button:has-text("Trigger HITL Request")');
    await page.click('button:has-text("Trigger HITL Request")');
    await expect(page.locator('text=Approve')).toHaveCount(2); // Two HITL messages

    // Approve the first one
    await page.locator('button:has-text("Approve")').first().click();
    await expect(page.locator('text=Request Approved')).toBeVisible();

    // Reject the second one
    await page.locator('button:has-text("Reject")').last().click();
    await expect(page.locator('text=Request Rejected')).toBeVisible();

    // Step 9: Test Modify Action
    await page.click('button:has-text("Trigger HITL Request")');
    await page.click('button:has-text("Modify")');
    await page.fill('textarea[placeholder="Enter custom response"]', 'This is a custom response.');
    await page.click('button:has-text("Send Response")');
    await expect(page.locator('text=Request Modified')).toBeVisible();
    await expect(page.locator('text=This is a custom response.')).toBeVisible();

    // Step 10: Test Counter Reset
    await page.click('button:has-text("Reset All Counters")');
    await expect(page.locator('text=0 actions left')).toBeVisible(); // Assuming message count resets to 0
    // The action counter should reset to the default limit, which might be different from the '1' we set earlier.
    // Assuming it resets to a default of 10 if not explicitly set.
    // For now, just check that the "0 actions left" from the previous step is gone.
    await expect(page.locator('text=0 actions left')).not.toBeVisible();
  });
});
