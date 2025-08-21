import json
import time
from typing import Union, Dict, Any, List
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import quote_plus

from ..utils import (
    validate_zone_name, validate_country_code, validate_timeout,
    validate_max_workers, validate_search_engine, validate_query,
    validate_response_format, validate_http_method, retry_request,
    get_logger, log_request, safe_json_parse, validate_response_size
)
from ..exceptions import ValidationError, APIError, AuthenticationError

logger = get_logger('api.search')


class SearchAPI:
    """Handles search operations using Bright Data SERP API"""
    
    def __init__(self, session, default_timeout=30, max_retries=3, retry_backoff=1.5):
        self.session = session
        self.default_timeout = default_timeout
        self.max_retries = max_retries
        self.retry_backoff = retry_backoff
    
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
        max_workers: int = 10,
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
        - `zone` (str, optional): Your Bright Data zone identifier (default: `None`)
        - `response_format` (str, optional): Response format - `"json"` for structured data, `"raw"` for HTML string (default: `"raw"`)
        - `method` (str, optional): HTTP method for the request (default: `"GET"`)
        - `country` (str, optional): Two-letter ISO country code for proxy location (default: `"us"`)
        - `data_format` (str, optional): Additional format transformation (default: `"markdown"`)
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
            zone="your_zone_name",
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
        
        timeout = timeout or self.default_timeout
        validate_zone_name(zone)
        validate_search_engine(search_engine)
        validate_query(query)
        validate_response_format(response_format)
        validate_http_method(method)
        validate_country_code(country)
        validate_timeout(timeout)
        validate_max_workers(max_workers)
        
        base_url_map = {
            "google": "https://www.google.com/search?q=",
            "bing": "https://www.bing.com/search?q=",
            "yandex": "https://yandex.com/search/?text="
        }
        
        base_url = base_url_map[search_engine.lower()]
        
        if isinstance(query, list):
            effective_max_workers = min(len(query), max_workers or 10)
            results = [None] * len(query)
            
            with ThreadPoolExecutor(max_workers=effective_max_workers) as executor:
                future_to_index = {
                    executor.submit(
                        self._perform_single_search,
                        single_query, zone, response_format, method, country,
                        data_format, async_request, base_url, timeout, parse
                    ): i
                    for i, single_query in enumerate(query)
                }
                
                for future in as_completed(future_to_index):
                    index = future_to_index[future]
                    try:
                        result = future.result()
                        results[index] = result
                    except Exception as e:
                        raise APIError(f"Failed to search '{query[index]}': {str(e)}")
            
            return results
        else:
            return self._perform_single_search(
                query, zone, response_format, method, country, 
                data_format, async_request, base_url, timeout, parse
            )

    def _perform_single_search(
        self,
        query: str,
        zone: str,
        response_format: str,
        method: str,
        country: str,
        data_format: str,
        async_request: bool,
        base_url: str,
        timeout: int,
        parse: bool
    ) -> Union[Dict[str, Any], str]:
        """
        Perform a single search operation
        """
        encoded_query = quote_plus(query)
        url = f"{base_url}{encoded_query}"
        
        if parse:
            url += "&brd_json=1"
        
        endpoint = "https://api.brightdata.com/request"
        
        payload = {
            "zone": zone,
            "url": url,
            "format": response_format,
            "method": method,
            "data_format": data_format
        }
        
        params = {}
        if async_request:
            params['async'] = 'true'
        
        @retry_request(
            max_retries=self.max_retries,
            backoff_factor=self.retry_backoff,
            retry_statuses={429, 500, 502, 503, 504}
        )
        def make_request():
            return self.session.post(
                endpoint,
                json=payload,
                params=params,
                timeout=timeout
            )
        
        response = make_request()
        
        if response.status_code == 200:
            if response_format == "json":
                try:
                    return response.json()
                except json.JSONDecodeError as e:
                    logger.warning(f"Failed to parse JSON response: {e}")
                    return response.text
            else:
                return response.text
                
        elif response.status_code == 400:
            raise ValidationError(f"Bad Request (400): {response.text}")
        elif response.status_code == 401:
            raise AuthenticationError(f"Unauthorized (401): Check your API token. {response.text}")
        elif response.status_code == 403:
            raise AuthenticationError(f"Forbidden (403): Insufficient permissions. {response.text}")
        elif response.status_code == 404:
            raise APIError(f"Not Found (404): {response.text}")
        else:
            raise APIError(f"API Error ({response.status_code}): {response.text}",
                          status_code=response.status_code, response_text=response.text)