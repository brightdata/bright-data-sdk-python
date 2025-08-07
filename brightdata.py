"""
## Bright Data SDK Functions:
#### scrape() 
- Scrapes a website using Bright Data Web Unlocker API with proxy support (or multiple webstites sequentially)
#### search() 
- Performs web searches using Bright Data SERP API with customizable search engines (or multiple search queries sequentially)
#### download_content() 
- Saves scraped content to local files in various formats (JSON, CSV, etc.)
"""

from datetime import datetime
import requests
import json
import os
import time
from typing import Union, Dict, Any, List
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import quote_plus, urlparse
import logging
from functools import wraps

logger = logging.getLogger(__name__)

class bdclient:
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
        browser_zone: str = None
    ):
        """
        Initialize the Bright Data client with your API token
        
        #### Create an account at https://brightdata.com/ to get your API token.

        Args:
            api_token: Your Bright Data API token (can also be set via API_TOKEN env var)
            auto_create_zones: Automatically create required zones if they don't exist (default: True)
            web_unlocker_zone: Custom zone name for web unlocker (default: from env or 'sdk_unlocker')
            browser_zone: Custom zone name for browser API (default: from env or 'sdk_browser')
        """
        try:
            from dotenv import load_dotenv
            load_dotenv()
        except ImportError:
            pass
        self.api_token = api_token or os.getenv('API_TOKEN')
        if not self.api_token:
            raise ValueError("API token is required. Provide it as parameter or set API_TOKEN environment variable")
        self.web_unlocker_zone = web_unlocker_zone or os.getenv('WEB_UNLOCKER_ZONE', 'sdk_unlocker')
        self.browser_zone = browser_zone or os.getenv('BROWSER_ZONE', 'sdk_browser')
        self.serp_zone = os.getenv('SERP_ZONE', 'sdk_serp')
        self.auto_create_zones = auto_create_zones
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {self.api_token}',
            'Content-Type': 'application/json',
            'User-Agent': 'brightdata-sdk/1.0.0'
        })
        
        adapter = requests.adapters.HTTPAdapter(
            pool_connections=self.CONNECTION_POOL_SIZE,
            pool_maxsize=self.CONNECTION_POOL_SIZE,
            max_retries=0
        )
        self.session.mount('https://', adapter)
        self.session.mount('http://', adapter)
        if self.auto_create_zones:
            self._ensure_required_zones()
    
    def _ensure_required_zones(self):
        """
        Check if required zones exist and create them if they don't.
        This mimics the server.js behavior.
        """
        try:
            response = self.session.get('https://api.brightdata.com/zone/get_active_zones')
            
            if response.status_code != 200:
                return
            
            zones = response.json() or []
            zone_names = {zone.get('name') for zone in zones}
            if self.web_unlocker_zone not in zone_names:
                self._create_zone(self.web_unlocker_zone, 'unblocker')
            if self.browser_zone not in zone_names:
                self._create_zone(self.browser_zone, 'unblocker')
            if self.serp_zone not in zone_names:
                self._create_zone(self.serp_zone, 'serp')
                
        except requests.exceptions.RequestException as e:
            logger.warning(f"Network error while ensuring zones exist: {e}")
        except json.JSONDecodeError as e:
            logger.warning(f"Invalid JSON response while checking zones: {e}")
        except KeyError as e:
            logger.warning(f"Unexpected response format while checking zones: {e}")
        except Exception as e:
            logger.warning(f"Unexpected error while ensuring zones exist: {e}")
    
    def _create_zone(self, zone_name: str, zone_type: str):
        """
        Create a new zone in Bright Data
        
        Args:
            zone_name: Name for the new zone
            zone_type: Type of zone ('unblocker' or 'serp')
        """
        payload = {
            "zone": {
                "name": zone_name,
                "type": zone_type
            },
            "plan": {
                "type": "static",
                "ips_type": "shared",
                "bandwidth": "1",
                "ip_alloc_preset": "shared_block",
                "ips": 0,
                "country": "any",
                "country_city": "any",
                "mobile": "false",
                "serp": "false",
                "city": "false",
                "asn": "false",
                "vip": "false",
                "vips_type": "shared",
                "vips": "0",
                "vip_country": "any",
                "vip_country_city": "any",
                "ub_premium": False,
                "solve_captcha_disable": True,
                "custom_headers": False
            }
        }
        
        response = self.session.post(
            'https://api.brightdata.com/zone',
            json=payload
        )
        
        if response.status_code not in [200, 201]:
            if "Duplicate zone name" in response.text or "already exists" in response.text.lower():
                return
            else:
                raise Exception(f"Failed to create zone: {response.text}")

    def _validate_url(self, url: str) -> None:
        """Validate URL format"""
        if not isinstance(url, str) or not url.strip():
            raise ValueError("URL must be a non-empty string")
        
        try:
            parsed = urlparse(url)
            if not parsed.scheme or not parsed.netloc:
                raise ValueError("URL must include scheme (http/https) and domain")
        except Exception:
            raise ValueError(f"Invalid URL format: {url}")
    
    def _validate_zone_name(self, zone: str) -> None:
        """Validate zone name format"""
        if not isinstance(zone, str) or not zone.strip():
            raise ValueError("Zone name must be a non-empty string")
        
        if not zone.replace('_', '').replace('-', '').isalnum():
            raise ValueError("Zone name can only contain letters, numbers, hyphens, and underscores")
    
    def _retry_request(self, func):
        """Decorator for retrying requests with exponential backoff"""
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(self.MAX_RETRIES):
                try:
                    response = func(*args, **kwargs)
                    if hasattr(response, 'status_code') and response.status_code in self.RETRY_STATUSES:
                        if attempt == self.MAX_RETRIES - 1:
                            raise requests.exceptions.HTTPError(f"Server error after {self.MAX_RETRIES} attempts: {response.status_code}")
                        time.sleep(self.RETRY_BACKOFF_FACTOR ** attempt)
                        continue
                    return response
                except requests.exceptions.Timeout:
                    if attempt == self.MAX_RETRIES - 1:
                        raise Exception(f"Request timed out after {self.MAX_RETRIES} attempts")
                    time.sleep(self.RETRY_BACKOFF_FACTOR ** attempt)
                except requests.exceptions.ConnectionError as e:
                    if attempt == self.MAX_RETRIES - 1:
                        raise Exception(f"Connection error after {self.MAX_RETRIES} attempts: {str(e)}")
                    time.sleep(self.RETRY_BACKOFF_FACTOR ** attempt)
                except requests.exceptions.RequestException as e:
                    if attempt == self.MAX_RETRIES - 1:
                        raise Exception(f"Network error after {self.MAX_RETRIES} attempts: {str(e)}")
                    time.sleep(self.RETRY_BACKOFF_FACTOR ** attempt)
            return None
        return wrapper
    
    def scrape(
        self,
        url: Union[str, List[str]],
        zone: str = None,
        format: str = "json",
        method: str = "GET", 
        country: str = "us",
        data_format: str = "markdown",
        async_request: bool = False,
        max_workers: int = None,
        timeout: int = None
    ) -> Union[Dict[str, Any], str, List[Union[Dict[str, Any], str]]]:
        """
        Unlock and scrape a website using Bright Data Web Unlocker API
        
        ## Args:
            #### Required
            url: Single URL string (e.g., "https://example.com") or list of URLs (e.g., ["https://site1.com", "https://site2.com"])
            #### Optional
            zone: Zone identifier (default: auto-configured web_unlocker_zone)
            format: Response format - "raw" returns HTML as string, "json" returns structured data
            method: HTTP method for the request (default: "GET")
            country: Two-letter ISO country code for proxy location (e.g., "us", "gb", "de", "ca", "au")
            data_format: Additional format transformation - "markdown" converts HTML to markdown, "screenshot" captures PNG
            async_request: Set to True for asynchronous processing
            max_workers: Maximum parallel workers for multiple URLs (default: 10)
            timeout: Request timeout in seconds (default: 30)
        
        ## Returns:
            For single URL: Dict with response data if format="json", or string if format="raw"
            For multiple URLs: List of results corresponding to each URL (processed in parallel)
        
        ## Examples:
            #### Single URL
            result = bdclient.scrape("https://example.com")
            
            #### Multiple URLs
            results = bdclient.scrape(["https://example1.com", "https://example2.com", "https://example3.com"])
            
            #### Custom country and raw HTML
            result = bdclient.scrape("https://example.com", format="raw", country="gb")
            
            #### Screenshot capture
            result = bdclient.scrape("https://example.com", data_format="screenshot")
        """
        
        zone = zone or self.web_unlocker_zone
        max_workers = max_workers or self.DEFAULT_MAX_WORKERS
        timeout = timeout or self.DEFAULT_TIMEOUT
        
        self._validate_zone_name(zone)
        
        if isinstance(url, list):
            if not url:
                raise ValueError("URL list cannot be empty")
            for single_url in url:
                self._validate_url(single_url)
            
            results = [None] * len(url)
            
            with ThreadPoolExecutor(max_workers=min(len(url), max_workers)) as executor:
                future_to_index = {
                    executor.submit(
                        self._perform_single_scrape,
                        single_url, zone, format, method, country,
                        data_format, async_request, timeout
                    ): i
                    for i, single_url in enumerate(url)
                }
                for future in as_completed(future_to_index):
                    index = future_to_index[future]
                    try:
                        result = future.result()
                        results[index] = result
                    except Exception as e:
                        raise Exception(f"Failed to scrape {url[index]}: {str(e)}")
            
            return results
        else:
            self._validate_url(url)
            return self._perform_single_scrape(
                url, zone, format, method, country, 
                data_format, async_request, timeout
            )

    def _perform_single_scrape(
        self,
        url: str,
        zone: str,
        format: str,
        method: str,
        country: str,
        data_format: str,
        async_request: bool,
        timeout: int
    ) -> Union[Dict[str, Any], str]:
        """
        Perform a single scrape operation
        """
        endpoint = "https://api.brightdata.com/request"
        
        payload = {
            "zone": zone,
            "url": url,
            "format": format,
            "method": method,
            "country": country,
            "data_format": data_format
        }
        
        params = {}
        if async_request:
            params['async'] = 'true'
        
        @self._retry_request
        def make_request():
            return self.session.post(
                endpoint,
                json=payload,
                params=params,
                timeout=timeout
            )
        
        response = make_request()
        
        if response.status_code == 200:
            if format == "json":
                try:
                    return response.json()
                except json.JSONDecodeError as e:
                    logger.warning(f"Failed to parse JSON response: {e}")
                    return response.text
            else:
                return response.text
                
        elif response.status_code == 400:
            raise ValueError(f"Bad Request (400): {response.text}")
        elif response.status_code == 401:
            raise ValueError(f"Unauthorized (401): Check your API token. {response.text}")
        elif response.status_code == 403:
            raise ValueError(f"Forbidden (403): Insufficient permissions. {response.text}")
        elif response.status_code == 404:
            raise ValueError(f"Not Found (404): {response.text}")
        else:
            raise Exception(f"API Error ({response.status_code}): {response.text}")

    def search(
        self,
        query: Union[str, List[str]],
        search_engine: str = "google",
        zone: str = None,
        format: str = "json",
        method: str = "GET",
        country: str = "us",
        data_format: str = "markdown",
        async_request: bool = False,
        max_workers: int = None,
        timeout: int = None
    ) -> Union[Dict[str, Any], str, List[Union[Dict[str, Any], str]]]:
        """
        Search the web using Bright Data SERP API
        
        ## Args:
            #### Required
            query: Search query string (e.g., "pizza") or list of queries (e.g., ["pizza", "restaurants"])
            #### Optional
            zone: Zone identifier (default: auto-configured serp_zone)
            search_engine: Search engine to use - "google", "bing", or "yandex" (default: "google")
            format: Response format - "raw" returns HTML as string, "json" returns structured data
            method: HTTP method for the request (default: "GET")
            country: Two-letter ISO country code for proxy location (e.g., "us", "gb", "de", "ca", "au")
            data_format: Additional format transformation - "markdown" converts HTML to markdown, "screenshot" captures PNG
            async_request: Set to True for asynchronous processing
            max_workers: Maximum parallel workers for multiple queries (default: 10)
            timeout: Request timeout in seconds (default: 30)
        
        ## Returns:
            For single query: Dict with response data if format="json", or string if format="raw"
            For multiple queries: List of results corresponding to each query (processed in parallel)
        
        ## Examples:

        Single query
        result = client.search("pizza")

        Multiple queries
        results = client.search(["pizza", "restaurants", "delivery"])

        With options
        results = client.search(["pizza", "sushi"], country="gb", format="raw")
            
        Search on different search engines
        result = client.search("pizza", search_engine="google")
        result = client.search("pizza", search_engine="bing")
        result = client.search("pizza", search_engine="yandex")
        """
        
        zone = zone or self.serp_zone
        max_workers = max_workers or self.DEFAULT_MAX_WORKERS
        timeout = timeout or self.DEFAULT_TIMEOUT
        
        self._validate_zone_name(zone)
        
        base_url_map = {
            "google": "https://www.google.com/search?q=",
            "bing": "https://www.bing.com/search?q=",
            "yandex": "https://yandex.com/search/?text="
        }
        
        if search_engine not in base_url_map:
            raise ValueError(f"Unsupported search engine: {search_engine}. Supported engines: {list(base_url_map.keys())}")
        
        base_url = base_url_map[search_engine]
        
        if isinstance(query, list):
            if not query:
                raise ValueError("Query list cannot be empty")
            for single_query in query:
                if not isinstance(single_query, str) or not single_query.strip():
                    raise ValueError("All queries must be non-empty strings")
            
            results = [None] * len(query)
            
            with ThreadPoolExecutor(max_workers=min(len(query), max_workers)) as executor:
                future_to_index = {
                    executor.submit(
                        self._perform_single_search,
                        single_query, zone, format, method, country,
                        data_format, async_request, base_url, timeout
                    ): i
                    for i, single_query in enumerate(query)
                }
                
                for future in as_completed(future_to_index):
                    index = future_to_index[future]
                    try:
                        result = future.result()
                        results[index] = result
                    except Exception as e:
                        raise Exception(f"Failed to search '{query[index]}': {str(e)}")
            
            return results
        else:
            if not isinstance(query, str) or not query.strip():
                raise ValueError("Query must be a non-empty string")
            return self._perform_single_search(
                query, zone, format, method, country, 
                data_format, async_request, base_url, timeout
            )

    def _perform_single_search(
        self,
        query: str,
        zone: str,
        format: str,
        method: str,
        country: str,
        data_format: str,
        async_request: bool,
        base_url: str,
        timeout: int
    ) -> Union[Dict[str, Any], str]:
        """
        Perform a single search operation
        """
        encoded_query = quote_plus(query)
        url = f"{base_url}{encoded_query}"
        
        endpoint = "https://api.brightdata.com/request"
        
        payload = {
            "zone": zone,
            "url": url,
            "format": format,
            "method": method,
            "country": country,
            "data_format": data_format
        }
        
        params = {}
        if async_request:
            params['async'] = 'true'
        
        @self._retry_request
        def make_request():
            return self.session.post(
                endpoint,
                json=payload,
                params=params,
                timeout=timeout
            )
        
        response = make_request()
        
        if response.status_code == 200:
            if format == "json":
                try:
                    return response.json()
                except json.JSONDecodeError as e:
                    logger.warning(f"Failed to parse JSON response: {e}")
                    return response.text
            else:
                return response.text
                
        elif response.status_code == 400:
            raise ValueError(f"Bad Request (400): {response.text}")
        elif response.status_code == 401:
            raise ValueError(f"Unauthorized (401): Check your API token. {response.text}")
        elif response.status_code == 403:
            raise ValueError(f"Forbidden (403): Insufficient permissions. {response.text}")
        elif response.status_code == 404:
            raise ValueError(f"Not Found (404): {response.text}")
        else:
            raise Exception(f"API Error ({response.status_code}): {response.text}")


    def download_content(self, content: Union[Dict, str], filename: str = None, format: str = "json") -> str:
        """
        Download content to a file based on its format
        
        ## Args:
        - content: The content to download (dict for JSON, string for other formats)
        - filename: Optional filename. If not provided, generates one with timestamp
        - format: Format of the content ("json", "csv", "ndjson", "jsonl", "txt")
        
        ## Returns:
        - Path to the downloaded file
        
        ## Examples:
        - #### Download JSON content
            filepath = download_content(json_data, "results.json", "json")
            
        - #### Download CSV content
            filepath = download_content(csv_string, "data.csv", "csv")
            
        - #### Auto-generate filename
            filepath = download_content(data, format="json")
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
            raise Exception(f"Failed to write file {filename}: {str(e)}")
        except json.JSONEncodeError as e:
            raise Exception(f"Failed to encode JSON content: {str(e)}")
        except Exception as e:
            raise Exception(f"Failed to download content: {str(e)}")
    
    def list_zones(self) -> List[Dict[str, Any]]:
        """
        List all active zones in your Bright Data account
        
        Returns:
            List of zone dictionaries with their configurations
        """
        try:
            response = self.session.get('https://api.brightdata.com/zone/get_active_zones')
            if response.status_code == 200:
                try:
                    return response.json() or []
                except json.JSONDecodeError as e:
                    raise Exception(f"Invalid JSON response from zones API: {str(e)}")
            elif response.status_code == 401:
                raise ValueError(f"Unauthorized (401): Check your API token")
            else:
                raise Exception(f"Failed to list zones ({response.status_code}): {response.text}")
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error listing zones: {e}")
            raise Exception(f"Network error while listing zones: {str(e)}")
        except Exception as e:
            logger.error(f"Error listing zones: {e}")
            raise