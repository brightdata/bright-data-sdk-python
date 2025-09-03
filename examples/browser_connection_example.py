import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from brightdata import bdclient
from playwright.sync_api import sync_playwright, Playwright

client = bdclient(
    api_token="your-api-key",
    browser_username="copy-from-zone-configuration",
    browser_password="copy-from-zone-configuration",
    browser_zone="your-custom-browser-zone"
) # Hover over the function to see browser parameters (can also be taken from .env file)

def scrape(playwright: Playwright, url="https://example.com"):
    browser = playwright.chromium.connect_over_cdp(client.connect_browser()) # Connect to the browser using Bright Data's endpoint
    try:
        print(f'Connected! Navigating to {url}...')
        page = browser.new_page()
        page.goto(url, timeout=2*60_000)
        print('Navigated! Scraping page content...')
        data = page.content()
        print(f'Scraped! Data: {data}')
    finally:
        browser.close()


def main():
    with sync_playwright() as playwright:
        scrape(playwright)


if __name__ == '__main__':
    main()