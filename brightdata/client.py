import os
import json
import requests
from datetime import datetime
from typing import Union, Dict, Any, List

from .api import WebScraper, SearchAPI
from .api.chatgpt import ChatGPTAPI
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
        self.chatgpt_api = ChatGPTAPI(
            self.session,
            self.api_token,
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
        
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"brightdata_results_{timestamp}.{format}"
        
        if not filename.endswith(f".{format}"):
            filename = f"{filename}.{format}"
        
        # Parse JSON strings in body fields if requested
        if parse and isinstance(content, (list, dict)):
            content = self._parse_body_json(content)
        
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
    

    def scrape_chatGPT(
        self,
        prompt: Union[str, List[str]],
        country: Union[str, List[str]] = "",
        additional_prompt: Union[str, List[str]] = "",
        web_search: Union[bool, List[bool]] = False
    ) -> Dict[str, Any]:
        """
        ## Scrape ChatGPT responses using Bright Data's ChatGPT dataset API
        
        Sends one or multiple prompts to ChatGPT through Bright Data's proxy network 
        and automatically prints the snapshot ID for easy copy/paste into download function.
        
        ### Parameters:
        - `prompt` (str | List[str]): Single prompt string or list of prompts to send to ChatGPT
        - `country` (str | List[str], optional): Two-letter ISO country code(s) for proxy location (default: "")
        - `additional_prompt` (str | List[str], optional): Follow-up prompt(s) after receiving the first answer (default: "")
        - `web_search` (bool | List[bool], optional): Whether to click the web search button in ChatGPT (default: False)
        
        ### Returns:
        - `Dict[str, Any]`: Response containing snapshot_id and other metadata for tracking the request
        
        ### Example Usage:
        ```python
        # Single prompt
        result = client.scrape_chatGPT(prompt="Top hotels in New York")
        
        # Multiple prompts
        result = client.scrape_chatGPT(
            prompt=["Top hotels in New York", "Best restaurants in Paris", "Tourist attractions in Tokyo"],
            additional_prompt=["Are you sure?", "", "What about hidden gems?"]
        )
        # Snapshot ID is automatically printed
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
            self.DEFAULT_TIMEOUT
        )

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
        if not snapshot_id or not isinstance(snapshot_id, str):
            raise ValidationError("Snapshot ID is required and must be a non-empty string")
        
        if format not in ["json", "ndjson", "jsonl", "csv"]:
            raise ValidationError("Format must be one of: json, ndjson, jsonl, csv")
        
        if not isinstance(compress, bool):
            raise ValidationError("Compress must be a boolean")
        
        if batch_size is not None:
            if not isinstance(batch_size, int) or batch_size < 1000:
                raise ValidationError("Batch size must be an integer >= 1000")
        
        if part is not None:
            if not isinstance(part, int) or part < 1:
                raise ValidationError("Part must be a positive integer")
            if batch_size is None:
                raise ValidationError("Part parameter requires batch_size to be specified")
        
        url = f"https://api.brightdata.com/datasets/v3/snapshot/{snapshot_id}"
        headers = {
            "Authorization": f"Bearer {self.api_token}"
        }
        
        params = {}
        if format != "json":  # Only add format if not default
            params["format"] = format
        if compress:
            params["compress"] = str(compress).lower()
        if batch_size is not None:
            params["batch_size"] = batch_size
        if part is not None:
            params["part"] = part
        
        try:
            response = self.session.get(url, headers=headers, params=params, timeout=self.DEFAULT_TIMEOUT)
            
            if response.status_code == 401:
                raise AuthenticationError("Invalid API token or insufficient permissions")
            elif response.status_code == 404:
                raise APIError(f"Snapshot '{snapshot_id}' not found")
            elif response.status_code != 200:
                raise APIError(f"Failed to download snapshot with status {response.status_code}: {response.text}")
            
            if format == "csv":
                data = response.text
                save_data = data
            else:
                response_text = response.text
                if '\n{' in response_text and response_text.strip().startswith('{'):
                    json_objects = []
                    for line in response_text.strip().split('\n'):
                        if line.strip():
                            try:
                                json_objects.append(json.loads(line))
                            except json.JSONDecodeError:
                                continue
                    data = json_objects
                    save_data = json_objects
                else:
                    try:
                        data = response.json()
                        save_data = data
                    except json.JSONDecodeError:
                        
                        data = response_text
                        save_data = response_text
            
            
            try:
                output_file = f"snapshot_{snapshot_id}.{format}"
                if format == "csv" or isinstance(save_data, str):
                    with open(output_file, 'w', encoding='utf-8') as f:
                        f.write(str(save_data))
                else:
                    with open(output_file, 'w', encoding='utf-8') as f:
                        json.dump(save_data, f, indent=2, ensure_ascii=False)
                print(f"Data saved to: {output_file}")
            except:
                pass
            
            return data
                    
        except requests.exceptions.Timeout:
            raise APIError(f"Timeout while downloading snapshot '{snapshot_id}'")
        except requests.exceptions.RequestException as e:
            raise APIError(f"Network error while downloading snapshot: {str(e)}")
        except Exception as e:
            if isinstance(e, (ValidationError, AuthenticationError, APIError)):
                raise
            raise APIError(f"Unexpected error while downloading snapshot: {str(e)}")

    def _parse_body_json(self, content: Union[Dict, List]) -> Union[Dict, List]:
        """
        Parse JSON strings in 'body' fields to objects
        
        Args:
            content: The content to process
            
        Returns:
            Content with parsed body fields
        """
        if content is None:
            return content
            
        if isinstance(content, list):
            # Process each item in the list
            for item in content:
                if isinstance(item, dict) and 'body' in item and isinstance(item['body'], str):
                    try:
                        # Only parse if body contains JSON-like content (starts with { or [)
                        body_str = item['body'].strip()
                        if body_str.startswith(('{', '[')):
                            item['body'] = json.loads(item['body'])
                    except (json.JSONDecodeError, AttributeError):
                        # Keep as string if not valid JSON or if any error occurs
                        logger.debug(f"Failed to parse body as JSON, keeping as string")
                        pass
        elif isinstance(content, dict) and 'body' in content and isinstance(content['body'], str):
            try:
                # Only parse if body contains JSON-like content (starts with { or [)
                body_str = content['body'].strip()
                if body_str.startswith(('{', '[')):
                    content['body'] = json.loads(content['body'])
            except (json.JSONDecodeError, AttributeError):
                # Keep as string if not valid JSON or if any error occurs
                logger.debug(f"Failed to parse body as JSON, keeping as string")
                pass
        
        return content

    def list_zones(self) -> List[Dict[str, Any]]:
        """
        ## List all active zones in your Bright Data account
        
        ### Returns:
            List of zone dictionaries with their configurations
        """
        return self.zone_manager.list_zones()