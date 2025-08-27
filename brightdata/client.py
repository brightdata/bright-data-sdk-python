import os
import json
import requests
from datetime import datetime
from typing import Union, Dict, Any, List

from .api import WebScraper, SearchAPI
from .api.chatgpt import ChatGPTAPI
from .api.linkedin import LinkedInAPI, LinkedInScraper, LinkedInSearcher
from .api.download import DownloadAPI
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
    DEFAULT_TIMEOUT = 65
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
        self.chatgpt_api = ChatGPTAPI(
            self.session,
            self.api_token,
            self.DEFAULT_TIMEOUT,
            self.MAX_RETRIES,
            self.RETRY_BACKOFF_FACTOR
        )
        self.linkedin_api = LinkedInAPI(
            self.session,
            self.api_token,
            self.DEFAULT_TIMEOUT,
            self.MAX_RETRIES,
            self.RETRY_BACKOFF_FACTOR
        )
        self.download_api = DownloadAPI(
            self.session,
            self.api_token,
            self.DEFAULT_TIMEOUT
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
        data_format: str = "html",
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
        - `response_format` (str, optional): Response format - `"json"` for structured data, `"raw"` for HTML string (default: `"raw"`)
        - `method` (str, optional): HTTP method for the request (default: `"GET"`)
        - `country` (str, optional): Two-letter ISO country code for proxy location (defaults to fastest connection)
        - `data_format` (str, optional): Additional format transformation (default: `"html"`)
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
        data_format: str = "html",
        async_request: bool = False,
        max_workers: int = None,
        timeout: int = None,
        parse: bool = False
    ) -> Union[Dict[str, Any], str, List[Union[Dict[str, Any], str]]]:
        """
        ## Search the web using Bright Data SERP API
        
        Performs web searches through major search engines using Bright Data's proxy network 
        for reliable, bot-detection-free results.
        
        ### Parameters:
        - `query` (str | List[str]): Search query string or list of search queries
        - `search_engine` (str, optional): Search engine to use - `"google"`, `"bing"`, or `"yandex"` (default: `"google"`)
        - `zone` (str, optional): Zone identifier (default: auto-configured serp_zone)
        - `response_format` (str, optional): Response format - `"json"` for structured data, `"raw"` for HTML string (default: `"raw"`)
        - `method` (str, optional): HTTP method for the request (default: `"GET"`)
        - `country` (str, optional): Two-letter ISO country code for proxy location (default: `"us"`)
        - `data_format` (str, optional): Additional format transformation (default: `"html"`)
        - `async_request` (bool, optional): Enable asynchronous processing (default: `False`)
        - `max_workers` (int, optional): Maximum parallel workers for multiple queries (default: `10`)
        - `timeout` (int, optional): Request timeout in seconds (default: `30`)
        - `parse` (bool, optional): Enable JSON parsing by adding brd_json=1 to URL (default: `False`)
        
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
            data_format, async_request, max_workers, timeout, parse
        )

    def download_content(self, content: Union[Dict, str], filename: str = None, format: str = "json", parse: bool = False) -> str:
        """
        ## Download content to a file based on its format
        
        ### Args:
            content: The content to download (dict for JSON, string for other formats)
            filename: Optional filename. If not provided, generates one with timestamp
            format: Format of the content ("json", "csv", "ndjson", "jsonl", "txt")
            parse: If True, automatically parse JSON strings in 'body' fields to objects (default: False)
        
        ### Returns:
            Path to the downloaded file
        """
        return self.download_api.download_content(content, filename, format, parse)
    

    def search_chatGPT(
        self,
        prompt: Union[str, List[str]],
        country: Union[str, List[str]] = "",
        additional_prompt: Union[str, List[str]] = "",
        web_search: Union[bool, List[bool]] = False,
        sync: bool = True
    ) -> Dict[str, Any]:
        """
        ## Search ChatGPT responses using Bright Data's ChatGPT dataset API
        
        Sends one or multiple prompts to ChatGPT through Bright Data's proxy network 
        with support for both synchronous and asynchronous processing.
        
        ### Parameters:
        - `prompt` (str | List[str]): Single prompt string or list of prompts to send to ChatGPT
        - `country` (str | List[str], optional): Two-letter ISO country code(s) for proxy location (default: "")
        - `additional_prompt` (str | List[str], optional): Follow-up prompt(s) after receiving the first answer (default: "")
        - `web_search` (bool | List[bool], optional): Whether to click the web search button in ChatGPT (default: False)
        - `sync` (bool, optional): If True (default), returns data immediately. If False, returns snapshot_id for async processing
        
        ### Returns:
        - `Dict[str, Any]`: If sync=True, returns ChatGPT response data directly. If sync=False, returns response with snapshot_id for async processing
        
        ### Example Usage:
        ```python
        # Single prompt (synchronous - returns data immediately)
        result = client.search_chatGPT(prompt="Top hotels in New York")
        
        # Multiple prompts (synchronous - returns data immediately)
        result = client.search_chatGPT(
            prompt=["Top hotels in New York", "Best restaurants in Paris", "Tourist attractions in Tokyo"],
            additional_prompt=["Are you sure?", "", "What about hidden gems?"]
        )
        
        # Asynchronous with web search enabled (returns snapshot_id)
        result = client.search_chatGPT(
            prompt="Latest AI developments", 
            web_search=True,
            sync=False
        )
        # Snapshot ID is automatically printed for async requests
        ```
        
        ### Raises:
        - `ValidationError`: Invalid prompt or parameters
        - `AuthenticationError`: Invalid API token or insufficient permissions
        - `APIError`: Request failed or server error
        """
        # Normalize inputs to lists
        if isinstance(prompt, str):
            prompts = [prompt]
        else:
            prompts = prompt
            
        if not prompts or len(prompts) == 0:
            raise ValidationError("At least one prompt is required")
            
        # Validate all prompts
        for p in prompts:
            if not p or not isinstance(p, str):
                raise ValidationError("All prompts must be non-empty strings")
        
        # Normalize other parameters to match prompts length
        def normalize_param(param, param_name):
            if isinstance(param, list):
                if len(param) != len(prompts):
                    raise ValidationError(f"{param_name} list must have same length as prompts list")
                return param
            else:
                return [param] * len(prompts)
        
        countries = normalize_param(country, "country")
        additional_prompts = normalize_param(additional_prompt, "additional_prompt")
        web_searches = normalize_param(web_search, "web_search")
        
        # Validate parameters
        for c in countries:
            if not isinstance(c, str):
                raise ValidationError("All countries must be strings")
                
        for ap in additional_prompts:
            if not isinstance(ap, str):
                raise ValidationError("All additional_prompts must be strings")
                
        for ws in web_searches:
            if not isinstance(ws, bool):
                raise ValidationError("All web_search values must be booleans")
        
        # Use the ChatGPT API class to handle the request
        return self.chatgpt_api.scrape_chatgpt(
            prompts, 
            countries, 
            additional_prompts, 
            web_searches,
            sync,
            self.DEFAULT_TIMEOUT
        )

    @property
    def scrape_linkedin(self):
        """
        ## LinkedIn Data Scraping Interface
        
        Provides specialized methods for scraping different types of LinkedIn data
        using Bright Data's collect API with pre-configured dataset IDs.
        
        ### Available Methods:
        - `profiles(url)` - Scrape LinkedIn profile data
        - `companies(url)` - Scrape LinkedIn company data  
        - `jobs(url)` - Scrape LinkedIn job listing data
        - `posts(url)` - Scrape LinkedIn post content
        
        ### Example Usage:
        ```python
        # Scrape LinkedIn profiles
        result = client.scrape_linkedin.profiles("https://www.linkedin.com/in/username/")
        
        # Scrape multiple companies
        companies = [
            "https://www.linkedin.com/company/ibm",
            "https://www.linkedin.com/company/bright-data"
        ]
        result = client.scrape_linkedin.companies(companies)
        
        # Scrape job listings
        result = client.scrape_linkedin.jobs("https://www.linkedin.com/jobs/view/123456/")
        
        # Scrape posts
        result = client.scrape_linkedin.posts("https://www.linkedin.com/posts/user-activity-123/")
        ```
        
        ### Returns:
        Each method returns a `Dict[str, Any]` containing snapshot_id and metadata for tracking the request.
        Use the snapshot_id with `download_snapshot()` to retrieve the collected data.
        """
        if not hasattr(self, '_linkedin_scraper'):
            self._linkedin_scraper = LinkedInScraper(self.linkedin_api)
        return self._linkedin_scraper

    @property
    def search_linkedin(self):
        """
        ## LinkedIn Data Search Interface
        
        Provides specialized methods for discovering new LinkedIn data by various search criteria
        using Bright Data's collect API with pre-configured dataset IDs.
        
        ### Available Methods:
        - `profiles(first_name, last_name)` - Search LinkedIn profiles by name
        - `jobs(url=..., location=...)` - Search LinkedIn jobs by URL or keyword criteria
        - `posts(profile_url=..., company_url=..., url=...)` - Search LinkedIn posts by various methods
        
        ### Example Usage:
        ```python
        # Search profiles by name
        result = client.search_linkedin.profiles("James", "Smith")
        
        # Search jobs by location and keywords
        result = client.search_linkedin.jobs(
            location="Paris", 
            keyword="product manager", 
            country="FR"
        )
        
        # Search posts by profile URL with date range
        result = client.search_linkedin.posts(
            profile_url="https://www.linkedin.com/in/username",
            start_date="2018-04-25T00:00:00.000Z",
            end_date="2021-05-25T00:00:00.000Z"
        )
        ```
        
        ### Returns:
        Each method returns a `Dict[str, Any]` containing snapshot_id (async) or direct data (sync) for tracking the request.
        Use the snapshot_id with `download_snapshot()` to retrieve the collected data.
        """
        if not hasattr(self, '_linkedin_searcher'):
            self._linkedin_searcher = LinkedInSearcher(self.linkedin_api)
        return self._linkedin_searcher

    def download_snapshot(
        self,
        snapshot_id: str,
        format: str = "json",
        compress: bool = False,
        batch_size: int = None,
        part: int = None
    ) -> Union[Dict[str, Any], List[Dict[str, Any]], str]:
        """
        ## Download snapshot content from Bright Data dataset API
        
        Downloads the snapshot content using the snapshot ID returned from scrape_chatGPT() 
        or other dataset collection triggers.
        
        ### Parameters:
        - `snapshot_id` (str): The snapshot ID returned when collection was triggered (required)
        - `format` (str, optional): Format of the data - "json", "ndjson", "jsonl", or "csv" (default: "json")
        - `compress` (bool, optional): Whether the result should be compressed (default: False)
        - `batch_size` (int, optional): Divide into batches of X records (minimum: 1000)
        - `part` (int, optional): If batch_size provided, specify which part to download
        
        ### Returns:
        - `Union[Dict, List, str]`: Snapshot data in the requested format
        
        ### Example Usage:
        ```python
        # Download complete snapshot
        data = client.download_snapshot("s_m4x7enmven8djfqak")
        
        # Download as CSV format
        csv_data = client.download_snapshot("s_m4x7enmven8djfqak", format="csv")
        
        # Download in batches
        batch_data = client.download_snapshot(
            "s_m4x7enmven8djfqak", 
            batch_size=1000, 
            part=1
        )
        ```
        
        ### Raises:
        - `ValidationError`: Invalid parameters or snapshot_id format
        - `AuthenticationError`: Invalid API token or insufficient permissions
        - `APIError`: Request failed, snapshot not found, or server error
        """
        return self.download_api.download_snapshot(snapshot_id, format, compress, batch_size, part)


    def list_zones(self) -> List[Dict[str, Any]]:
        """
        ## List all active zones in your Bright Data account
        
        ### Returns:
            List of zone dictionaries with their configurations
        """
        return self.zone_manager.list_zones()