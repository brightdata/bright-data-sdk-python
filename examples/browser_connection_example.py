import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from brightdata import bdclient
from playwright.sync_api import sync_playwright

client = bdclient(
    api_token="your-api-key",
    browser_username="copy-from-zone-configuration",
    browser_password="copy-from-zone-configuration",
    browser_zone="your-custom-browser-zone"
) # Hover over the function to see browser parameters (can also be taken from .env file)

with sync_playwright() as playwright:
    browser = playwright.chromium.connect_over_cdp(client.connect_browser()) # Connect to the browser using Bright Data's endpoint
    page = browser.new_page()
    page.goto("https://example.com")
    print(f"Title: {page.title()}")
    browser.close()