import playwright.sync_api as p
import os
import time

# Clever/Smartpass Headless Auth
# Requires: pip install playwright && playwright install chromium


USERNAME = os.getenv("CLEVER_USERNAME")
PASSWORD = os.getenv("CLEVER_PASSWORD")
SCHOOLNAME = os.getenv("CLEVER_SCHOOLNAME")
CLEVER_LOGIN_URL = f"https://clever.com/in/{SCHOOLNAME}" # Update for your district

def get_new_token():
    with p.sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()

        print("[*] Navigating to Clever...")
        page.goto(CLEVER_LOGIN_URL)
        
        # Mason specific login flow usually involves "Log in with Google" or similar
        # This part is school-specific. Assuming standard Clever login:
        if page.query_selector('input[name="username"]'):
            page.fill('input[name="username"]', USERNAME)
            page.fill('input[name="password"]', PASSWORD)
            page.click('button[type="submit"]')
        
        print("[*] Waiting for redirect to Smartpass...")
        # Search for Smartpass icon and click or go direct
        page.goto("https://app.smartpass.app")
        
        # Wait for auth to complete
        page.wait_for_selector('.sp-app-root', timeout=60000)
        
        cookies = context.cookies()
        token = next((c['value'] for c in cookies if c['name'] == 'smartpassToken'), None)
        
        browser.close()
        return token

if __name__ == "__main__":
    token = get_new_token()
    if token:
        print(f"TOKEN={token}")
    else:
        print("Failed to get token")
