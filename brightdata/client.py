import os
import json
import requests
from datetime import datetime
from typing import Union, Dict, Any, List

from .api import WebScraper, SearchAPI
from .utils import ZoneManager, setup_logging, get_logger
from .exceptions import ValidationError, AuthenticationError, APIError

def _get_version():
    """Get version from __init__.py, cached at module import time."""
    try:
        import os
        init_file = os.path.join(os.path.dirname(__file__), '__init__.py')
        with open(init_file, 'r', encoding='utf-8') as f:
            for line in f:
                if line.startswith('__version__'):
                    return line.split('"')[1]
    except (OSError, IndexError):
        pass
    return "unknown"

__version__ = _get_version()

logger = get_logger('client')


class bdclient:
    """Main client for the Bright Data SDK"""
    
    DEFAULT_MAX_WORKERS = 10
    DEFAULT_TIMEOUT = 30
    CONNECTION_POOL_SIZE = 20
    MAX_RETRIES = 3
    RETRY_BACKOFF_FACTOR = 1.5
    RETRY_STATUSES = {429, 500, 502, 503, 504}
    
    def __init__(
        self, 
        api_token: str = None,
        auto_create_zones: bool = True,
        web_unlocker_zone: str = None,
        serp_zone: str = None,
        log_level: str = "INFO",
        structured_logging: bool = True,
        verbose: bool = None
    ):
        """
        Initialize the Bright Data client with your API token
        
        Create an account at https://brightdata.com/ to get your API token.
        Go to settings > API keys , and verify that your API key have "Admin" permissions.

        Args:
            api_token: Your Bright Data API token (can also be set via BRIGHTDATA_API_TOKEN env var)
            auto_create_zones: Automatically create required zones if they don't exist (default: True)
            web_unlocker_zone: Custom zone name for web unlocker (default: from env or 'sdk_unlocker')
            serp_zone: Custom zone name for SERP API (default: from env or 'sdk_serp')
            log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            structured_logging: Whether to use structured JSON logging (default: True)
            verbose: Enable verbose logging (default: False). Can also be set via BRIGHTDATA_VERBOSE env var.
                    When False, only shows WARNING and above. When True, shows all logs per log_level.
        """
        try:
            from dotenv import load_dotenv
            load_dotenv()
        except ImportError:
            pass
        
        if verbose is None:
            env_verbose = os.getenv('BRIGHTDATA_VERBOSE', '').lower()
            verbose = env_verbose in ('true', '1', 'yes', 'on')
        
        setup_logging(log_level, structured_logging, verbose)
        logger.info("Initializing Bright Data SDK client")
            
        self.api_token = api_token or os.getenv('BRIGHTDATA_API_TOKEN')
        if not self.api_token:
            logger.error("API token not provided")
            raise ValidationError("API token is required. Provide it as parameter or set BRIGHTDATA_API_TOKEN environment variable")
        
        if not isinstance(self.api_token, str):
            logger.error("API token must be a string")
            raise ValidationError("API token must be a string")
        
        if len(self.api_token.strip()) < 10:
            logger.error("API token appears to be invalid (too short)")
            raise ValidationError("API token appears to be invalid")
        
        token_preview = f"{self.api_token[:4]}***{self.api_token[-4:]}" if len(self.api_token) > 8 else "***"
        logger.info(f"API token validated successfully: {token_preview}")
            
        self.web_unlocker_zone = web_unlocker_zone or os.getenv('WEB_UNLOCKER_ZONE', 'sdk_unlocker')
        self.serp_zone = serp_zone or os.getenv('SERP_ZONE', 'sdk_serp')
        self.auto_create_zones = auto_create_zones
        
        self.session = requests.Session()
        
        auth_header = f'Bearer {self.api_token}'
        self.session.headers.update({
            'Authorization': auth_header,
            'Content-Type': 'application/json',
            'User-Agent': f'brightdata-sdk/{__version__}'
        })
        
        logger.info("HTTP session configured with secure headers")
        
        adapter = requests.adapters.HTTPAdapter(
            pool_connections=self.CONNECTION_POOL_SIZE,
            pool_maxsize=self.CONNECTION_POOL_SIZE,
            max_retries=0
        )
        self.session.mount('https://', adapter)
        self.session.mount('http://', adapter)
        
        self.zone_manager = ZoneManager(self.session)
        self.web_scraper = WebScraper(
            self.session, 
            self.DEFAULT_TIMEOUT, 
            self.MAX_RETRIES, 
            self.RETRY_BACKOFF_FACTOR
        )
        self.search_api = SearchAPI(
            self.session,
            self.DEFAULT_TIMEOUT,
            self.MAX_RETRIES,
            self.RETRY_BACKOFF_FACTOR
        )
        
        if self.auto_create_zones:
            self.zone_manager.ensure_required_zones(
                self.web_unlocker_zone, 
                self.serp_zone
            )
    
    def scrape(
        self,
        url: Union[str, List[str]],
        zone: str = None,
        response_format: str = "raw",
        method: str = "GET", 
        country: str = "",
        data_format: str = "markdown",
        async_request: bool = False,
        max_workers: int = None,
        timeout: int = None
    ) -> Union[Dict[str, Any], str, List[Union[Dict[str, Any], str]]]:
        """
        ## Unlock and scrape websites using Bright Data Web Unlocker API
        
        Scrapes one or multiple URLs through Bright Data's proxy network with anti-bot detection bypass.
        
        ### Parameters:
        - `url` (str | List[str]): Single URL string or list of URLs to scrape
        - `zone` (str, optional): Zone identifier (default: auto-configured web_unlocker_zone)
        - `response_format` (str, optional): Response format - `"json"` for structured data, `"raw"` for HTML string (default: `"json"`)
        - `method` (str, optional): HTTP method for the request (default: `"GET"`)
        - `country` (str, optional): Two-letter ISO country code for proxy location (defaults to fastest connection)
        - `data_format` (str, optional): Additional format transformation (default: `"markdown"`)
        - `async_request` (bool, optional): Enable asynchronous processing (default: `False`)
        - `max_workers` (int, optional): Maximum parallel workers for multiple URLs (default: `10`)
        - `timeout` (int, optional): Request timeout in seconds (default: `30`)
        
        ### Returns:
        - Single URL: `Dict[str, Any]` if `response_format="json"`, `str` if `response_format="raw"`
        - Multiple URLs: `List[Union[Dict[str, Any], str]]` corresponding to each input URL
        
        ### Example Usage:
        ```python
        # Single URL scraping
        result = client.scrape(
            url="https://example.com", 
            response_format="json"
        )
        
        # Multiple URLs scraping
        urls = ["https://site1.com", "https://site2.com"]
        results = client.scrape(
            url=urls,
            response_format="raw",
            max_workers=5
        )
        ```
        
        ### Raises:
        - `ValidationError`: Invalid URL format or empty URL list
        - `AuthenticationError`: Invalid API token or insufficient permissions
        - `APIError`: Request failed or server error
        """
        zone = zone or self.web_unlocker_zone
        max_workers = max_workers or self.DEFAULT_MAX_WORKERS
        
        return self.web_scraper.scrape(
            url, zone, response_format, method, country, data_format,
            async_request, max_workers, timeout
        )

    def search(
        self,
        query: Union[str, List[str]],
        search_engine: str = "google",
        zone: str = None,
        response_format: str = "raw",
        method: str = "GET",
        country: str = "",
        data_format: str = "markdown",
        async_request: bool = False,
        max_workers: int = None,
        timeout: int = None
    ) -> Union[Dict[str, Any], str, List[Union[Dict[str, Any], str]]]:
        """
        ## Search the web using Bright Data SERP API
        
        Performs web searches through major search engines using Bright Data's proxy network 
        for reliable, bot-detection-free results.
        
        ### Parameters:
        - `query` (str | List[str]): Search query string or list of search queries
        - `search_engine` (str, optional): Search engine to use - `"google"`, `"bing"`, or `"yandex"` (default: `"google"`)
        - `zone` (str, optional): Zone identifier (default: auto-configured serp_zone)
        - `response_format` (str, optional): Response format - `"json"` for structured data, `"raw"` for HTML string (default: `"json"`)
        - `method` (str, optional): HTTP method for the request (default: `"GET"`)
        - `country` (str, optional): Two-letter ISO country code for proxy location (default: `"us"`)
        - `data_format` (str, optional): Additional format transformation (default: `"markdown"`)
        - `async_request` (bool, optional): Enable asynchronous processing (default: `False`)
        - `max_workers` (int, optional): Maximum parallel workers for multiple queries (default: `10`)
        - `timeout` (int, optional): Request timeout in seconds (default: `30`)
        
        ### Returns:
        - Single query: `Dict[str, Any]` if `response_format="json"`, `str` if `response_format="raw"`
        - Multiple queries: `List[Union[Dict[str, Any], str]]` corresponding to each input query
        
        ### Example Usage:
        ```python
        # Single search query
        result = client.search(
            query="best laptops 2024",
            search_engine="google",
            response_format="json"
        )
        
        # Multiple search queries
        queries = ["python tutorials", "machine learning courses", "web development"]
        results = client.search(
            query=queries,
            search_engine="bing",
            max_workers=3
        )
        ```
        
        ### Supported Search Engines:
        - `"google"` - Google Search
        - `"bing"` - Microsoft Bing
        - `"yandex"` - Yandex Search
        
        ### Raises:
        - `ValidationError`: Invalid search engine, empty query, or validation errors
        - `AuthenticationError`: Invalid API token or insufficient permissions  
        - `APIError`: Request failed or server error
        """
        zone = zone or self.serp_zone
        max_workers = max_workers or self.DEFAULT_MAX_WORKERS
        
        return self.search_api.search(
            query, search_engine, zone, response_format, method, country,
            data_format, async_request, max_workers, timeout
        )

    def download_content(self, content: Union[Dict, str], filename: str = None, format: str = "json") -> str:
        """
        ## Download content to a file based on its format
        
        ### Args:
            content: The content to download (dict for JSON, string for other formats)
            filename: Optional filename. If not provided, generates one with timestamp
            format: Format of the content ("json", "csv", "ndjson", "jsonl", "txt")
        
        ### Returns:
            Path to the downloaded file
        """
        
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"brightdata_results_{timestamp}.{format}"
        
        if not filename.endswith(f".{format}"):
            filename = f"{filename}.{format}"
        
        try:
            if format == "json":
                with open(filename, 'w', encoding='utf-8') as f:
                    if isinstance(content, dict) or isinstance(content, list):
                        json.dump(content, f, indent=2, ensure_ascii=False)
                    else:
                        f.write(str(content))
            else:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(str(content))
            
            logger.info(f"Content downloaded to: {filename}")
            return filename
            
        except IOError as e:
            raise APIError(f"Failed to write file {filename}: {str(e)}")
        except json.JSONEncodeError as e:
            raise APIError(f"Failed to encode JSON content: {str(e)}")
        except Exception as e:
            raise APIError(f"Failed to download content: {str(e)}")
    
    def list_zones(self) -> List[Dict[str, Any]]:
        """
        ## List all active zones in your Bright Data account
        
        ### Returns:
            List of zone dictionaries with their configurations
        """
        return self.zone_manager.list_zones()