"""Playwright automation of the Microsoft Entra ID sign-in pages.

Selectors target the standard AAD work/school account sign-in flow:
  1. Email page
  2. Password page
  3. Optional "Stay signed in?" KMSI prompt
  4. Redirect to http://localhost:<port>/?code=...
"""
from __future__ import annotations

from playwright.sync_api import TimeoutError as PWTimeoutError, sync_playwright


def complete_aad_login(auth_url: str, username: str, password: str,
                       headless: bool = True, nav_timeout_ms: int = 30000) -> None:
    """Drive a headless browser through the AAD sign-in for `auth_url`."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        try:
            # Fresh context = no cookies, no cached accounts.
            ctx = browser.new_context()
            page = ctx.new_page()
            page.set_default_timeout(nav_timeout_ms)

            page.goto(auth_url)

            # --- Email page ---------------------------------------------------
            page.wait_for_selector('input[type="email"]')
            page.fill('input[type="email"]', username)
            page.click('input[type="submit"]')

            # --- Password page ------------------------------------------------
            page.wait_for_selector('input[type="password"]')
            page.fill('input[type="password"]', password)
            page.click('input[type="submit"]')

            # --- Optional "Stay signed in?" prompt ----------------------------
            try:
                page.wait_for_selector('input[value="No"]', timeout=5000)
                page.click('input[value="No"]')
            except PWTimeoutError:
                pass  # KMSI screen not shown - that's fine.

            # --- Wait for redirect back to the CLI's localhost listener ------
            page.wait_for_url(
                lambda u: u.startswith("http://localhost"),
                timeout=nav_timeout_ms,
            )
        finally:
            browser.close()
