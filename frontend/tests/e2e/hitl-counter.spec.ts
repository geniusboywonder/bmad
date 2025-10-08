import { test, expect } from '@playwright/test';

test.describe('Copilot demo HITL counter', () => {
  test('auto approvals disable and lock behaviour', async ({ page }) => {
    await page.goto('/copilot-demo');
    await page.waitForSelector('[data-testid="hitl-controls"]');
    await page.waitForFunction(() => typeof (window as any).__hitlDemoControls !== 'undefined');

    await page.evaluate(() => {
      const controls = (window as any).__hitlDemoControls;
      controls.clearRequests();
      controls.setHitlEnabled(false);
    });

    const disabledState = await page.evaluate(() => {
      const controls = (window as any).__hitlDemoControls;
      controls.sendMessage();
      controls.sendMessage();
      controls.sendMessage();
      return controls.getState();
    });

    expect(disabledState.hitlEnabled).toBe(false);
    expect(disabledState.currentCounter).toBe(disabledState.hitlCounter);
    expect(disabledState.requests.length).toBe(0);
    expect(disabledState.messageCount).toBeGreaterThanOrEqual(3);

    await expect(page.getByText('Disabled', { exact: true })).toBeVisible();

    const enabledState = await page.evaluate(() => {
      const controls = (window as any).__hitlDemoControls;
      controls.setHitlCounterLimit(2);
      controls.resetCounters();
      controls.clearRequests();
      controls.setHitlEnabled(true);
      return controls.getState();
    });

    expect(enabledState.hitlEnabled).toBe(true);
    expect(enabledState.currentCounter).toBe(2);
    expect(enabledState.requests.length).toBe(0);

    await page.evaluate(() => {
      const controls = (window as any).__hitlDemoControls;
      controls.sendMessage();
      controls.sendMessage();
      controls.sendMessage();
    });

    const lockedState = await page.evaluate(() => {
      const controls = (window as any).__hitlDemoControls;
      return controls.getState();
    });

    expect(lockedState.hitlEnabled).toBe(true);
    expect(lockedState.requests.length).toBeGreaterThan(0);
    expect(lockedState.requests[0].status).toBe('pending');
    expect(lockedState.currentCounter).toBe(lockedState.hitlCounter);

    await expect(page.locator('text=HITL approval required').first()).toBeVisible();
  });
});
