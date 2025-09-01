"""
## Bright Data SDK for Python

A comprehensive SDK for Bright Data's Web Scraping and SERP APIs, providing
easy-to-use methods for web scraping, search engine result parsing, and data management.
## Functions:
First import the package and create a client:
```python
from brightdata import bdclient
client = bdclient(your-apy-key)
```
Then use the client to call the desired functions:  
#### scrape()
- Scrapes a website using Bright Data Web Unblocker API with proxy support (or multiple websites sequentially)
- syntax: `results = client.scrape(url, country, max_workers, ...)`
#### .scrape_linkedin. class
- Scrapes LinkedIn data including posts, jobs, companies, and profiles, recieve structured data as a result
- syntax: `results = client.scrape_linkedin.posts()/jobs()/companies()/profiles() # insert parameters per function`
#### search()
- Performs web searches using Bright Data SERP API with customizable search engines (or multiple search queries sequentially)
- syntax: `results = client.search(query, search_engine, country, ...)`
#### .search_linkedin. class
- Search LinkedIn data including for specific posts, jobs, profiles. recieve the relevent data as a result
- syntax: `results = client.search_linkedin.posts()/jobs()/profiles() # insert parameters per function`
#### search_chatGPT()
- Interact with ChatGPT using Bright Data's ChatGPT API, sending prompts and receiving responses
- syntax: `results = client.search_chatGPT(prompt, additional_prompt, max_workers, ...)`
#### download_content() / download_snapshot()
- Saves the scraped content to local files in various formats (JSON, CSV, etc.)
- syntax: `client.download_content(results)`
- syntax: `client.download_snapshot(results)`
#### connect_browser()
- Get WebSocket endpoint for connecting to Bright Data's scraping browser with Playwright/Selenium
- syntax: `endpoint_url = client.connect_browser()` then use with browser automation tools
#### crawl()
- Crawl websites to discover and scrape multiple pages using Bright Data's Web Crawl API
- syntax: `result = client.crawl(url, filter, exclude_filter, depth, ...)`
#### parse_content()
- Parse and extract useful information from API responses (JSON or HTML)
- syntax: `parsed = client.parse_content(data, extract_text=True, extract_links=True)`

### Features:
- Web Scraping: Scrape websites using Bright Data Web Unlocker API with proxy support
- Search Engine Results: Perform web searches using Bright Data SERP API  
- Web Crawling: Discover and scrape multiple pages from websites with advanced filtering
- Content Parsing: Extract text, links, images, and structured data from API responses
- Browser Automation: Simple authentication for Bright Data's scraping browser with Playwright/Selenium
- Multiple Search Engines: Support for Google, Bing, and Yandex
- Parallel Processing: Concurrent processing for multiple URLs or queries
- Robust Error Handling: Comprehensive error handling with retry logic
- Input Validation: Automatic validation of URLs, zone names, and parameters
- Zone Management: Automatic zone creation and management
- Multiple Output Formats: JSON, raw HTML, markdown, and more
"""

from .client import bdclient
from .exceptions import (
    BrightDataError,
    ValidationError,
    AuthenticationError,
    ZoneError,
    NetworkError,
    APIError
)
from .utils import parse_content, parse_multiple, extract_structured_data

__version__ = "1.1.0"
__author__ = "Bright Data"
__email__ = "support@brightdata.com"

__all__ = [
    'bdclient',
    'BrightDataError',
    'ValidationError', 
    'AuthenticationError',
    'ZoneError',
    'NetworkError',
    'APIError',
    'parse_content',
    'parse_multiple',
    'extract_structured_data'
]