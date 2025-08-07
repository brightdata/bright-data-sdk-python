<p align="center">
  <a href="https://brightdata.com/">
    <img src="https://mintlify.s3.us-west-1.amazonaws.com/brightdata/logo/light.svg" width="300" alt="Bright Data Logo">
  </a>
</p>

<h1 align="center">Python SDK</h1>
<h3 align="center">A Python SDK for the Bright Data Data extraction and Web unlocking tools, providing easy-to-use scalable methods for web scraping, search engine result parsing, and data management.</h3>



## Features

- **Web Scraping**: Scrape websites using Bright Data Web Unlocker API with proxy support
- **Search Engine Results**: Perform web searches using Bright Data SERP API
- **Multiple Search Engines**: Support for Google, Bing, and Yandex
- **Parallel Processing**: Concurrent processing for multiple URLs or queries
- **Robust Error Handling**: Comprehensive error handling with retry logic
- **Input Validation**: Automatic validation of URLs, zone names, and parameters
- **Zone Management**: Automatic zone creation and management
- **Multiple Output Formats**: JSON, raw HTML, markdown, and more

## Installation from package

```python
# Enter your project's folder in your terminal
pip install brightdata

# Make sure that you have pip installed on your device
```

## Installation from GitHub

```python
# Clone the repository
git clone https://github.com/brightdata/bright-data-sdk-python.git
cd bright-temp

# Install dependencies
pip install requests python-dotenv
```

## Quick Start

### 1. Initialize the Client

```python
from brightdata import bdclient

# Using API token directly
client = bdclient(api_token="your_api_token_here")

# Or using environment variables
# Set BRIGHTDATA_API_TOKEN in your environment or .env file
client = bdclient()
```

### 2. Scrape Websites

```python
# Single URL
result = client.scrape("https://example.com")

# Multiple URLs (parallel processing)
urls = ["https://example1.com", "https://example2.com", "https://example3.com"]
results = client.scrape(urls)

# Custom options
result = client.scrape(
    "https://example.com",
    format="raw",
    country="gb",
    data_format="screenshot"
)
```

### 3. Search Engine Results

```python
# Single search query
result = client.search("pizza restaurants")

# Multiple queries (parallel processing)
queries = ["pizza", "restaurants", "delivery"]
results = client.search(queries)

# Different search engines
result = client.search("pizza", search_engine="google")
result = client.search("pizza", search_engine="bing")
result = client.search("pizza", search_engine="yandex")

# Custom options
results = client.search(
    ["pizza", "sushi"],
    country="gb",
    format="raw"
)
```

### 4. Download Content

```python
# Download scraped content
data = client.scrape("https://example.com")
filepath = client.download_content(data, "results.json", "json")

# Auto-generate filename with timestamp
filepath = client.download_content(data, format="json")
```

### 5. Manage Zones

```python
# List all active zones
zones = client.list_zones()
print(f"Found {len(zones)} zones")
```

## Configuration

### Environment Variables

Create a `.env` file in your project root:

```env
BRIGHTDATA_API_TOKEN=your_bright_data_api_token
WEB_UNLOCKER_ZONE=your_web_unlocker_zone  # Optional
BROWSER_ZONE=your_browser_zone            # Optional  
SERP_ZONE=your_serp_zone                 # Optional
```

### Configuration Options

```python
client = bdclient(
    api_token="your_token",
    auto_create_zones=True,           # Automatically create missing zones
    web_unlocker_zone="custom_zone",  # Custom zone name
    browser_zone="custom_browser"     # Custom browser zone
)
```

## API Reference

### bdclient Class

#### Constructor

```python
bdclient(
    api_token: str = None,
    auto_create_zones: bool = True,
    web_unlocker_zone: str = None,
    browser_zone: str = None
)
```

#### Methods

**scrape(url, zone=None, format="json", method="GET", country="us", data_format="markdown", async_request=False, max_workers=None, timeout=None)**

Scrape websites using Bright Data Web Unlocker API.

- `url`: Single URL string or list of URLs
- `zone`: Zone identifier (auto-configured if None)
- `format`: "json" or "raw"
- `method`: HTTP method
- `country`: Two-letter country code
- `data_format`: "markdown", "screenshot", etc.
- `async_request`: Enable async processing
- `max_workers`: Max parallel workers (default: 10)
- `timeout`: Request timeout in seconds (default: 30)

**search(query, search_engine="google", zone=None, format="json", method="GET", country="us", data_format="markdown", async_request=False, max_workers=None, timeout=None)**

Search using Bright Data SERP API.

- `query`: Search query string or list of queries
- `search_engine`: "google", "bing", or "yandex"
- Other parameters same as scrape()

**download_content(content, filename=None, format="json")**

Save content to local file.

- `content`: Content to save
- `filename`: Output filename (auto-generated if None)
- `format`: File format ("json", "csv", "txt", etc.)

**list_zones()**

List all active zones in your Bright Data account.

## Error Handling

The SDK includes comprehensive error handling:

```python
try:
    result = client.scrape("https://example.com")
except ValueError as e:
    print(f"Invalid input: {e}")
except Exception as e:
    print(f"API error: {e}")
```

## Production Features

- **Retry Logic**: Automatic retries with exponential backoff for network failures
- **Input Validation**: Validates URLs, zone names, and parameters
- **Connection Pooling**: Efficient HTTP connection management
- **Logging**: Comprehensive logging for debugging and monitoring
- **Zone Auto-Creation**: Automatically creates required zones if they don't exist

## Configuration Constants

The SDK uses the following default values (configurable):

- `DEFAULT_MAX_WORKERS`: 10 parallel workers
- `DEFAULT_TIMEOUT`: 30 seconds request timeout
- `CONNECTION_POOL_SIZE`: 20 HTTP connections
- `MAX_RETRIES`: 3 retry attempts
- `RETRY_BACKOFF_FACTOR`: 1.5x exponential backoff

## Getting Your API Token

1. Sign up at [brightdata.com](https://brightdata.com/)
2. Navigate to your dashboard
3. Create or access your API credentials
4. Copy your API token

## Requirements

- Python 3.7+
- `requests` library
- `python-dotenv` (optional, for .env file support)

## License

This project is licensed under the MIT License.

## Support

For issues related to the Bright Data service, contact [Bright Data support](https://brightdata.com/support).

For SDK-related issues, please open an issue in this repository.
