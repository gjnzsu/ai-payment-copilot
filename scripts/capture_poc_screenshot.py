from pathlib import Path

from playwright.sync_api import sync_playwright

APP_URL = "http://localhost:8501"
SCREENSHOT_PATH = Path("docs/assets/ai-payment-copilot-poc.png")


def main() -> None:
    SCREENSHOT_PATH.parent.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1440, "height": 1400})
        page.goto(APP_URL, wait_until="networkidle")
        page.get_by_text("AI Payment Copilot").first.wait_for(timeout=30_000)
        page.screenshot(path=str(SCREENSHOT_PATH), full_page=True)
        browser.close()

    print(SCREENSHOT_PATH)


if __name__ == "__main__":
    main()
