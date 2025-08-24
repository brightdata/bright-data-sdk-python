
<img width="1300" height="200" alt="sdk-banner(1)" src="https://github.com/user-attachments/assets/c4a7857e-10dd-420b-947a-ed2ea5825cb8" />

```python
pip install brightdata-sdk
```
<h3 align="center">Python SDK by Bright Data, providing easy-to-use scalable methods for web search & scraping</h3>
<p></p>

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

```python
pip install brightdata-sdk
```
> If using macOS, first open a virtual environment for your project

## Quick Start

Create a [Bright Data](https://brightdata.com/) account and copy your API key

### 1. Initialize the Client

```python
from brightdata import bdclient

client = bdclient(api_token="your_api_token_here") # can also be defined as BRIGHTDATA_API_TOKEN in your .env file
```

Or you can configure a custom zone name

```python
client = bdclient(
    api_token="your_token",
    auto_create_zones=False,          # Else it creates the Zone automatically
    web_unlocker_zone="custom_zone",
    serp_zone="custom_serp_zone"
)

```

### 2. Search Engine Results

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

> [!TIP]
> Hover over the "search" or each function in the package, to see all its available parameters.

![Hover-Over1](https://github.com/user-attachments/assets/51324485-5769-48d5-8f13-0b534385142e)

### 3. Scrape Websites

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

### 4. Download Content

```python
# Download scraped content
data = client.scrape("https://example.com")
client.download_content(data) 
```

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
WEB_UNLOCKER_ZONE=your_web_unlocker_zone  # Optional
SERP_ZONE=your_serp_zone                  # Optional
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

</details>
<details>
    <summary>👥 <strong>Client Management</strong></summary>
    
bdclient Class
    
```python
bdclient(
    api_token: str = None,
    auto_create_zones: bool = True,
    web_unlocker_zone: str = None,
    serp_zone: str = None,
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
