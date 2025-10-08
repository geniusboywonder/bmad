import asyncio
from playwright.async_api import async_playwright, expect

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        # Navigate to the application
        await page.goto("http://localhost:3000/copilot-demo")

        # Wait for the policy violation banner to appear
        policy_banner = page.locator('[data-testid="policy-guidance"]')
        await expect(policy_banner).to_be_visible(timeout=10000)

        # Take a screenshot
        await page.screenshot(path="jules-scratch/verification/policy_violation_feedback.png")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())