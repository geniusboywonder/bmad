from playwright.sync_api import sync_playwright, Page, expect

def verify_hitl_prompt(page: Page):
    """
    This script verifies that the HITL reconfiguration prompt appears
    when the temporary trigger button is clicked.
    """
    # 1. Arrange: Go to the copilot demo page.
    # The dev server runs on port 3000 by default.
    page.goto("http://localhost:3000/copilot-demo")

    # 2. Act: Find the temporary trigger button and click it.
    # Using the data-testid for a robust locator.
    trigger_button = page.get_by_test_id("test-hitl-prompt-button")

    # Ensure the button is visible before clicking
    expect(trigger_button).to_be_visible(timeout=10000) # Increased timeout for dev server
    trigger_button.click()

    # 3. Assert: Confirm that the HITL prompt component is now visible.
    # We can check for the title text of the prompt.
    prompt_title = page.get_by_text("Agent Action Limit Reached")
    expect(prompt_title).to_be_visible()

    # Also check for a button inside the prompt to be sure.
    continue_button = page.get_by_role("button", name="Continue")
    expect(continue_button).to_be_visible()

    # 4. Screenshot: Capture the final result for visual verification.
    screenshot_path = "jules-scratch/verification/verification.png"
    page.screenshot(path=screenshot_path)
    print(f"Screenshot saved to {screenshot_path}")

def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        try:
            verify_hitl_prompt(page)
        finally:
            browser.close()

if __name__ == "__main__":
    main()