"""Drive the running app in a real browser, check the main flows, and save README screenshots.

Needs both servers running (API on :8000, web on :5173) and Playwright:
    pip install playwright && playwright install chromium
    python scripts/e2e_screenshots.py
"""

import os
import time
from pathlib import Path

from playwright.sync_api import expect, sync_playwright

BASE = os.environ.get("APP_URL", "http://localhost:5173")
OUT = Path(__file__).resolve().parent.parent / "docs" / "screenshots"
EMAIL = f"demo+{int(time.time())}@example.com"
PASSWORD = "demo-password-1"
BUDGETS = {"Groceries": "500", "Dining": "250", "Shopping": "150", "Transport": "200"}


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        launch = {"args": ["--no-sandbox"]}
        if chrome := os.environ.get("CHROME_PATH"):
            launch["executable_path"] = chrome
        browser = p.chromium.launch(**launch)
        page = browser.new_page(viewport={"width": 1360, "height": 980}, device_scale_factor=2)
        errors: list[str] = []
        page.on("pageerror", lambda e: errors.append(str(e)))
        page.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)

        # Sign-up
        page.goto(BASE)
        page.screenshot(path=OUT / "login.png")
        page.get_by_role("button", name="New here? Create an account").click()
        page.get_by_label("Email").fill(EMAIL)
        page.get_by_label("Password").fill(PASSWORD)
        page.get_by_role("button", name="Create account").click()
        expect(page.get_by_text("No transactions yet")).to_be_visible()

        # Import
        page.get_by_role("button", name="Load sample data").click()
        expect(page.get_by_role("heading", name="Dashboard")).to_be_visible()

        # Budgets
        page.get_by_role("link", name="Budgets").click()
        for category, limit in BUDGETS.items():
            page.get_by_label("Category").select_option(category)
            page.get_by_label("Monthly limit in dollars").fill(limit)
            page.get_by_role("button", name="Add budget").click()
            expect(page.get_by_role("cell", name=category, exact=True)).to_be_visible()
        page.screenshot(path=OUT / "budgets.png")

        # Dashboard for a complete month
        page.get_by_role("link", name="Dashboard").click()
        page.get_by_label("Month").select_option("2026-10")
        expect(page.get_by_text("Largest expenses")).to_be_visible()
        expect(page.get_by_role("progressbar")).to_have_count(len(BUDGETS))
        page.wait_for_timeout(500)
        page.screenshot(path=OUT / "dashboard.png")

        # Transactions: re-import is a no-op, then search, recategorize, delete
        page.get_by_role("link", name="Transactions").click()
        expect(page.get_by_text("1–15 of 265")).to_be_visible()
        page.screenshot(path=OUT / "transactions.png")

        page.get_by_role("button", name="Load sample data").click()
        expect(page.get_by_text("Imported 0 transactions · 265 duplicates skipped")).to_be_visible()
        expect(page.get_by_text("1–15 of 265")).to_be_visible()

        page.get_by_label("Search descriptions").fill("lcbo")
        expect(page.get_by_text("of 265")).to_have_count(0)
        row = page.locator("tbody tr").first
        expect(row).to_contain_text("LCBO")
        row.get_by_role("combobox").select_option("Entertainment")
        expect(page.locator("tbody tr").first.get_by_role("combobox")).to_have_value("Entertainment")

        before = page.locator("tbody tr").count()
        page.locator("tbody tr").first.get_by_role("button").click()
        expect(page.locator("tbody tr")).to_have_count(before - 1)

        # Session survives a reload; sign out and back in
        page.reload()
        expect(page.get_by_role("heading", name="Transactions")).to_be_visible()
        page.get_by_role("button", name="Sign out").click()
        page.get_by_label("Email").fill(EMAIL)
        page.get_by_label("Password").fill("wrong-password")
        page.get_by_role("button", name="Sign in", exact=True).click()
        expect(page.get_by_role("alert")).to_have_text("Incorrect email or password")
        page.get_by_label("Password").fill(PASSWORD)
        page.get_by_role("button", name="Sign in", exact=True).click()
        expect(page.get_by_text("1–15 of 264")).to_be_visible()

        # Narrow screen
        page.set_viewport_size({"width": 390, "height": 844})
        page.get_by_role("link", name="Dashboard").click()
        expect(page.get_by_text("Largest expenses")).to_be_visible()
        page.wait_for_timeout(500)
        page.screenshot(path=OUT / "mobile.png")

        browser.close()
        # The wrong-password attempt above is an expected 401.
        unexpected = [e for e in errors if "401" not in e]
        assert not unexpected, unexpected
    print("End-to-end run passed. Screenshots saved to", OUT)


if __name__ == "__main__":
    main()
