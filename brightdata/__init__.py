"""
## Bright Data SDK for Python

A comprehensive SDK for Bright Data's Web Scraping and SERP APIs, providing
easy-to-use methods for web scraping, search engine result parsing, and data management.
### Functions:
#### scrape()
- Scrapes a website using Bright Data Web Unblocker API with proxy support (or multiple websites sequentially)
#### search()
- Performs web searches using Bright Data SERP API with customizable search engines (or multiple search queries sequentially)
#### download_content()
- Saves the scraped content to local files in various formats (JSON, CSV, etc.)

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

__version__ = "1.0.3"
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