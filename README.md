
<img width="1300" height="200" alt="sdk-banner(1)" src="https://github.com/user-attachments/assets/c4a7857e-10dd-420b-947a-ed2ea5825cb8" />

<h3 align="center">A Python SDK for the Bright Data's Data extraction and Web unlocking tools, providing easy-to-use scalable methods for web scraping, web searches and more.</h3>


For a quick start you can try to run our example files in this repositories under the "Codespace" section.

## Features

- **Web Scraping**: Scrape websites using Bright Data Web Unlocker API with proxy support
- **Search Engine Results**: Perform web searches using Bright Data SERP API
- **Multiple Search Engines**: Support for Google, Bing, and Yandex
- **Parallel Processing**: Concurrent processing for multiple URLs or queries
- **Robust Error Handling**: Comprehensive error handling with retry logic
- **Zone Management**: Automatic zone creation and management
- **Multiple Output Formats**: JSON, raw HTML, markdown, and more

## Installation
To install the package, open your terminal:
> [!NOTE]
> If you are using macOS you will need to open a virtual environment for your project first.

```bash
pip install brightdata-sdk
```

## Quick Start

### 1. Initialize the Client
> [!IMPORTANT]
> Go to your [**account settings**](https://brightdata.com/cp/setting/users), to verify that your API key have **"admin permissions"**.

```python
from brightdata import bdclient

client = bdclient(api_token="your_api_token_here") # can also be defined as BRIGHTDATA_API_TOKEN in your .env file
```

Or you can use a custom zone name
```python
client = bdclient(
    api_token="your_token",
    auto_create_zones=False,          # Else it creates the Zone automatically
    web_unlocker_zone="custom_zone",  # Custom zone name for web scraping
    serp_zone="custom_serp_zone"      # Custom zone name for search requests
)
```
> [!TIP]
> Hover over the "bdclient" (or over each function in the package) with your cursor to see all its available parameters.


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
result = client.search("pizza", search_engine="google") # search_engine can also be set to "yandex" or "bing"

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
client.download_content(data, "results.json", "json") # Auto-generate filename if not specified
```

## Configuration

### Environment Variables

Create a `.env` file in your project root:

```env
BRIGHTDATA_API_TOKEN=your_bright_data_api_token
WEB_UNLOCKER_ZONE=your_web_unlocker_zone  # Optional
SERP_ZONE=your_serp_zone                  # Optional
```

### Manage Zones

```python
# List all active zones
zones = client.list_zones()
print(f"Found {len(zones)} zones")
```

## API Reference

### bdclient Class

```python
bdclient(
    api_token: str = None,
    auto_create_zones: bool = True,
    web_unlocker_zone: str = None,
    serp_zone: str = None,
)
```

### Key Methods

#### scrape(...)
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

#### search(...)
Searches using the SERP API. Accepts the same arguments as scrape(), plus:
```python
- `query`: Search query string or list of queries
- `search_engine`: "google", "bing", or "yandex"
- Other parameters same as scrape()
```

#### download_content(...)

Save content to local file.
```python
- `content`: Content to save
- `filename`: Output filename (auto-generated if None)
- `format`: File format ("json", "csv", "txt", etc.)
```

#### list_zones()

List all active zones in your Bright Data account.

## Error Handling

The SDK includes built-in input validation and retry logic:
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

| Constant               | Default | Description                     |
| ---------------------- | ------- | ------------------------------- |
| `DEFAULT_MAX_WORKERS`  | `10`    | Max parallel tasks              |
| `DEFAULT_TIMEOUT`      | `30`    | Request timeout (in seconds)    |
| `CONNECTION_POOL_SIZE` | `20`    | Max concurrent HTTP connections |
| `MAX_RETRIES`          | `3`     | Retry attempts on failure       |
| `RETRY_BACKOFF_FACTOR` | `1.5`   | Exponential backoff multiplier  |

## Getting Your API Token

1. Sign up at [brightdata.com](https://brightdata.com/), and navigate to your dashboard
2. Create or access your API credentials
3. Copy your API token and paste it in your .env or code file

## Development

For development installation, open your terminal:

```bash
git clone https://github.com/brightdata/bright-data-sdk-python.git

# If you are using Mac you will need to open a virtual environment for your project first.
cd bright-data-sdk-python
pip install .
```

## License

This project is licensed under the MIT License.

## Support

For any issues, contact [Bright Data support](https://brightdata.com/contact), or open an issue in this repository.
