
<img width="1300" height="200" alt="sdk-banner(1)" src="https://github.com/user-attachments/assets/c4a7857e-10dd-420b-947a-ed2ea5825cb8" />

```python
pip install brightdata-sdk
```
<h3 align="center">Python SDK by Bright Data, Easy-to-use scalable methods for web search & scraping</h3>
<p></p>

## Installation
To install the package, open your terminal:

```python
pip install brightdata-sdk
```
> If using macOS, first open a virtual environment for your project

## Quick Start

Create a [Bright Data](https://brightdata.com/) account and copy your API key

### Initialize the Client

```python
from brightdata import bdclient

client = bdclient(api_token="your_api_token_here") # can also be defined as BRIGHTDATA_API_TOKEN in your .env file
```

### Launch first request
Add to your code a serp function
```python
results = client.search("best selling shoes")

print(client.parse_content(results))
```

## Features

| Feature                        | Functions                   | Description
|--------------------------|-----------------------------|-------------------------------------
| **Scrape every website** | `scrape`                    | Scrape every website using Bright's scraping and unti bot-detection capabilities
| **Web search**           | `search`                    | Search google and other search engines by query (supports batch searches)
| **Web crawling**         | `crawl`                     | Discover and scrape multiple pages from websites with advanced filtering and depth control
| **Content parsing**      | `parse_content`             | Extract text, links, images and structured data from API responses (JSON or HTML)
| **Browser automation**   | `connect_browser`           | Get WebSocket endpoint for Playwright/Selenium integration with Bright Data's scraping browser
| **Search chatGPT**       | `search_chatGPT`            | Prompt chatGPT and scrape its answers, support multiple inputs and follow-up prompts
| **Search linkedin**      | `search_linkedin.posts()`, `search_linkedin.jobs()`, `search_linkedin.profiles()` | Search LinkedIn by specific queries, and recieve structured data
| **Scrape linkedin**      | `scrape_linkedin.posts()`, `scrape_linkedin.jobs()`, `scrape_linkedin.profiles()`, `scrape_linkedin.companies()` | Scrape LinkedIn and recieve structured data
| **Download functions**   | `download_snapshot`, `download_content`  | Download content for both sync and async requests
| **Client class**         | `bdclient`         | Handles authentication, automatic zone creation and managment, and options for robust error handling
| **Parallel processing**  | **all functions**  | All functions use Concurrent processing for multiple URLs or queries, and support multiple Output Formats

### Try usig one of the functions

#### `Search()`
```python
# Simple single query search
result = client.search("pizza restaurants")

# Try using multiple queries (parallel processing), with custom configuration
queries = ["pizza", "restaurants", "delivery"]
results = client.search(
    queries,
    search_engine="bing",
    country="gb",
    format="raw"
)
```
#### `scrape()`
```python
# Simple single URL scrape
result = client.scrape("https://example.com")

# Multiple URLs (parallel processing) with custom options
urls = ["https://example1.com", "https://example2.com", "https://example3.com"]
results = client.scrape(
    "urls",
    format="raw",
    country="gb",
    data_format="screenshot"
)
```
#### `search_chatGPT()`
```python
result = client.search_chatGPT(
    prompt="what day is it today?"
    # prompt=["What are the top 3 programming languages in 2024?", "Best hotels in New York", "Explain quantum computing"],
    # additional_prompt=["Can you explain why?", "Are you sure?", ""]  
)

client.download_content(result) # In case of timeout error, your snapshot_id is presented and you will downloaded it using download_snapshot()
```

#### `search_linkedin.`
Available functions:
client.**`search_linkedin.posts()`**,client.**`search_linkedin.jobs()`**,client.**`search_linkedin.profiles()`**
```python
# Search LinkedIn profiles by name
first_names = ["James", "Idan"]
last_names = ["Smith", "Vilenski"]

result = client.search_linkedin.profiles(first_names, last_names) # can also be changed to async
# will print the snapshot_id, which can be downloaded using the download_snapshot() function
```

#### `scrape_linkedin.`
Available functions

client.**`scrape_linkedin.posts()`**,client.**`scrape_linkedin.jobs()`**,client.**`scrape_linkedin.profiles()`**,client.**`scrape_linkedin.companies()`**
```python
post_urls = [
    "https://www.linkedin.com/posts/orlenchner_scrapecon-activity-7180537307521769472-oSYN?trk=public_profile",
    "https://www.linkedin.com/pulse/getting-value-out-sunburst-guillaume-de-b%C3%A9naz%C3%A9?trk=public_profile_article_view"
]

results = client.scrape_linkedin.posts(post_urls) # can also be changed to async

print(results) # will print the snapshot_id, which can be downloaded using the download_snapshot() function
```

#### `crawl()`
```python
# Single URL crawl with filters
result = client.crawl(
    url="https://example.com/",
    depth=2,
    filter="/product/",           # Only crawl URLs containing "/product/"
    exclude_filter="/ads/",       # Exclude URLs containing "/ads/"
    custom_output_fields=["markdown", "url", "page_title"]
)
print(f"Crawl initiated. Snapshot ID: {result['snapshot_id']}")

# Download crawl results
data = client.download_snapshot(result['snapshot_id'])
```

#### `parse_content()`
```python
# Parse scraping results
scraped_data = client.scrape("https://example.com")
parsed = client.parse_content(
    scraped_data, 
    extract_text=True, 
    extract_links=True, 
    extract_images=True
)
print(f"Title: {parsed['title']}")
print(f"Text length: {len(parsed['text'])}")
print(f"Found {len(parsed['links'])} links")
```

#### `connect_browser()`
```python
# For Playwright (default browser_type)
from playwright.sync_api import sync_playwright

client = bdclient(
    api_token="your_api_token",
    browser_username="username-zone-browser_zone1",
    browser_password="your_password"
)

with sync_playwright() as playwright:
    browser = playwright.chromium.connect_over_cdp(client.connect_browser())
    page = browser.new_page()
    page.goto("https://example.com")
    print(f"Title: {page.title()}")
    browser.close()
```

**`download_content`** (for sync requests)
```python
data = client.scrape("https://example.com")
client.download_content(data) 
```
**`download_snapshot`** (for async requests)
```python
# Save this function to seperate file
client.download_snapshot("") # Insert your snapshot_id
```

> [!TIP]
> Hover over the "search" or each function in the package, to see all its available parameters.

![Hover-Over1](https://github.com/user-attachments/assets/51324485-5769-48d5-8f13-0b534385142e)

## Function Parameters
<details>
    <summary>🔍 <strong>Search(...)</strong></summary>
    
Searches using the SERP API. Accepts the same arguments as scrape(), plus:

```python
- `query`: Search query string or list of queries
- `search_engine`: "google", "bing", or "yandex"
- Other parameters same as scrape()
```
    
</details>
<details>
    <summary>🔗 <strong>scrape(...)</strong></summary>

Scrapes a single URL or list of URLs using the Web Unlocker.

```python
- `url`: Single URL string or list of URLs
- `zone`: Zone identifier (auto-configured if None)
- `format`: "json" or "raw"
- `method`: HTTP method
- `country`: Two-letter country code
- `data_format`: "markdown", "screenshot", etc.
- `async_request`: Enable async processing
- `max_workers`: Max parallel workers (default: 10)
- `timeout`: Request timeout in seconds (default: 30)
```

</details>
<details>
    <summary>🕷️ <strong>crawl(...)</strong></summary>

Discover and scrape multiple pages from websites with advanced filtering.

```python
- `url`: Single URL string or list of URLs to crawl (required)
- `ignore_sitemap`: Ignore sitemap when crawling (optional)
- `depth`: Maximum crawl depth relative to entered URL (optional)
- `filter`: Regex to include only certain URLs (e.g. "/product/")
- `exclude_filter`: Regex to exclude certain URLs (e.g. "/ads/")
- `custom_output_fields`: List of output fields to include (optional)
- `include_errors`: Include errors in response (default: True)
```

</details>
<details>
    <summary>🔍 <strong>parse_content(...)</strong></summary>

Extract and parse useful information from API responses.

```python
- `data`: Response data from scrape(), search(), or crawl() methods
- `extract_text`: Extract clean text content (default: True)
- `extract_links`: Extract all links from content (default: False)
- `extract_images`: Extract image URLs from content (default: False)
```

</details>
<details>
    <summary>🌐 <strong>connect_browser(...)</strong></summary>

Get WebSocket endpoint for browser automation with Bright Data's scraping browser.

```python
# Required client parameters:
- `browser_username`: Username for browser API (format: "username-zone-{zone_name}")
- `browser_password`: Password for browser API authentication
- `browser_type`: "playwright", "puppeteer", or "selenium" (default: "playwright")

# Returns: WebSocket endpoint URL string
```

</details>
<details>
    <summary>💾 <strong>Download_Content(...)</strong></summary>

Save content to local file.

```python
- `content`: Content to save
- `filename`: Output filename (auto-generated if None)
- `format`: File format ("json", "csv", "txt", etc.)
```

</details>
<details>
    <summary>⚙️ <strong>Configuration Constants</strong></summary>

<p></p>

| Constant               | Default | Description                     |
| ---------------------- | ------- | ------------------------------- |
| `DEFAULT_MAX_WORKERS`  | `10`    | Max parallel tasks              |
| `DEFAULT_TIMEOUT`      | `30`    | Request timeout (in seconds)    |
| `CONNECTION_POOL_SIZE` | `20`    | Max concurrent HTTP connections |
| `MAX_RETRIES`          | `3`     | Retry attempts on failure       |
| `RETRY_BACKOFF_FACTOR` | `1.5`   | Exponential backoff multiplier  |

</details>

##  Advanced Configuration

<details>
    <summary>🔧 <strong>Environment Variables</strong></summary>

Create a `.env` file in your project root:

```env
BRIGHTDATA_API_TOKEN=your_bright_data_api_token
WEB_UNLOCKER_ZONE=your_web_unlocker_zone        # Optional
SERP_ZONE=your_serp_zone                        # Optional
BROWSER_ZONE=your_browser_zone                  # Optional
BRIGHTDATA_BROWSER_USERNAME=username-zone-name  # For browser automation
BRIGHTDATA_BROWSER_PASSWORD=your_browser_password  # For browser automation
```

</details>
<details>
    <summary>🌐 <strong>Manage Zones</strong></summary>

List all active zones

```python
# List all active zones
zones = client.list_zones()
print(f"Found {len(zones)} zones")
```

Configure a custom zone name

```python
client = bdclient(
    api_token="your_token",
    auto_create_zones=False,          # Else it creates the Zone automatically
    web_unlocker_zone="custom_zone",
    serp_zone="custom_serp_zone"
)

```

</details>
<details>
    <summary>👥 <strong>Client Management</strong></summary>
    
bdclient Class - Complete parameter list
    
```python
bdclient(
    api_token: str = None,                    # Your Bright Data API token (required)
    auto_create_zones: bool = True,           # Auto-create zones if they don't exist
    web_unlocker_zone: str = None,            # Custom web unlocker zone name
    serp_zone: str = None,                    # Custom SERP zone name
    browser_zone: str = None,                 # Custom browser zone name
    browser_username: str = None,             # Browser API username (format: "username-zone-{zone_name}")
    browser_password: str = None,             # Browser API password
    browser_type: str = "playwright",         # Browser automation tool: "playwright", "puppeteer", "selenium"
    log_level: str = "INFO",                  # Logging level: "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"
    structured_logging: bool = True,          # Use structured JSON logging
    verbose: bool = None                      # Enable verbose logging (overrides log_level if True)
)
```
    
</details>
<details>
    <summary>⚠️ <strong>Error Handling</strong></summary>
    
bdclient Class
    
The SDK includes built-in input validation and retry logic

In case of zone related problems, use the **list_zones()** function to check your active zones, and check that your [**account settings**](https://brightdata.com/cp/setting/users), to verify that your API key have **"admin permissions"**.
    
</details>

## Support

For any issues, contact [Bright Data support](https://brightdata.com/contact), or open an issue in this repository.
