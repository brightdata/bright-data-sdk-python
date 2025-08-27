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

### Features:
- Web Scraping: Scrape websites using Bright Data Web Unlocker API with proxy support
- Search Engine Results: Perform web searches using Bright Data SERP API  
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

__version__ = "1.0.8"
__author__ = "Bright Data"
__email__ = "support@brightdata.com"

__all__ = [
    'bdclient',
    'BrightDataError',
    'ValidationError', 
    'AuthenticationError',
    'ZoneError',
    'NetworkError',
    'APIError'
]