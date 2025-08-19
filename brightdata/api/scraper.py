import time
from typing import Union, Dict, Any, List
from concurrent.futures import ThreadPoolExecutor, as_completed

from ..utils import (
    validate_url, validate_zone_name, validate_country_code,
    validate_timeout, validate_max_workers, validate_url_list,
    validate_response_format, validate_http_method, retry_request,
    get_logger, log_request, safe_json_parse, validate_response_size
)
from ..exceptions import ValidationError, APIError, AuthenticationError

logger = get_logger('api.scraper')


class WebScraper:
    """Handles web scraping operations using Bright Data Web Unlocker API"""
    
    def __init__(self, session, default_timeout=30, max_retries=3, retry_backoff=1.5):
        self.session = session
        self.default_timeout = default_timeout
        self.max_retries = max_retries
        self.retry_backoff = retry_backoff
    
    def scrape(
        self,
        url: Union[str, List[str]],
        zone: str,
        response_format: str = "raw",
        method: str = "GET", 
        country: str = "",
        data_format: str = "markdown",
        async_request: bool = False,
        max_workers: int = 10,
        timeout: int = None
    ) -> Union[Dict[str, Any], str, List[Union[Dict[str, Any], str]]]:
        """
        **Unlock and scrape websites using Bright Data Web Unlocker API**
        
        Scrapes one or multiple URLs through Bright Data's proxy network with anti-bot detection bypass.
        
        **Parameters:**
        - `url` (str | List[str]): Single URL string or list of URLs to scrape
        - `zone` (str): Your Bright Data zone identifier 
        - `response_format` (str, optional): Response format - `"json"` for structured data, `"raw"` for HTML string (default: `"raw"`)
        - `method` (str, optional): HTTP method for the request (default: `"GET"`)
        - `country` (str, optional): Two-letter ISO country code for proxy location (default: `"us"`)
        - `data_format` (str, optional): Additional format transformation (default: `"html"`)
        - `async_request` (bool, optional): Enable asynchronous processing (default: `False`)
        - `max_workers` (int, optional): Maximum parallel workers for multiple URLs (default: `10`)
        - `timeout` (int, optional): Request timeout in seconds (default: `30`)
        
        **Returns:**
        - Single URL: `Dict[str, Any]` if `response_format="json"`, `str` if `response_format="raw"`
        - Multiple URLs: `List[Union[Dict[str, Any], str]]` corresponding to each input URL
        
        **Example Usage:**
        ```python
        # Single URL scraping
        result = client.scrape(
            url="https://example.com", 
            zone="your_zone_name",
            response_format="json"
        )
        
        # Multiple URLs scraping
        urls = ["https://site1.com", "https://site2.com"]
        results = client.scrape(
            url=urls,
            zone="your_zone_name", 
            response_format="raw",
            max_workers=5
        )
        ```
        
        **Raises:**
        - `ValidationError`: Invalid URL format or empty URL list
        - `AuthenticationError`: Invalid API token or insufficient permissions
        - `APIError`: Request failed or server error
        """
        
        timeout = timeout or self.default_timeout
        validate_zone_name(zone)
        validate_response_format(response_format)
        validate_http_method(method)
        validate_country_code(country)
        validate_timeout(timeout)
        validate_max_workers(max_workers)
        
        if isinstance(url, list):
            validate_url_list(url)
            effective_max_workers = min(len(url), max_workers or 10)
            
            results = [None] * len(url)
            
            with ThreadPoolExecutor(max_workers=effective_max_workers) as executor:
                future_to_index = {
                    executor.submit(
                        self._perform_single_scrape,
                        single_url, zone, response_format, method, country,
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
                        raise APIError(f"Failed to scrape {url[index]}: {str(e)}")
            
            return results
        else:
            validate_url(url)
            return self._perform_single_scrape(
                url, zone, response_format, method, country, 
                data_format, async_request, timeout
            )

    def _perform_single_scrape(
        self,
        url: str,
        zone: str,
        response_format: str,
        method: str,
        country: str,
        data_format: str,
        async_request: bool,
        timeout: int
    ) -> Union[Dict[str, Any], str]:
        """
        Perform a single scrape operation with comprehensive logging
        """
        endpoint = "https://api.brightdata.com/request"
        start_time = time.time()
        
        logger.info(f"Starting scrape request for URL: {url[:100]}{'...' if len(url) > 100 else ''}")
        
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
        
        try:
            response = make_request()
            response_time = (time.time() - start_time) * 1000
            
            # Log request details
            log_request(logger, 'POST', endpoint, response.status_code, response_time)
            
            if response.status_code == 200:
                logger.info(f"Scrape completed successfully in {response_time:.2f}ms")
                
                validate_response_size(response.text)
                
                if response_format == "json":
                    result = safe_json_parse(response.text)
                    logger.debug(f"Processed response with {len(str(result))} characters")
                    return result
                else:
                    logger.debug(f"Returning raw response with {len(response.text)} characters")
                    return response.text
                    
            elif response.status_code == 400:
                logger.error(f"Bad Request (400) for URL {url}: {response.text}")
                raise ValidationError(f"Bad Request (400): {response.text}")
            elif response.status_code == 401:
                logger.error(f"Unauthorized (401) for URL {url}: Check API token")
                raise AuthenticationError(f"Unauthorized (401): Check your API token. {response.text}")
            elif response.status_code == 403:
                logger.error(f"Forbidden (403) for URL {url}: Insufficient permissions")
                raise AuthenticationError(f"Forbidden (403): Insufficient permissions. {response.text}")
            elif response.status_code == 404:
                logger.error(f"Not Found (404) for URL {url}: {response.text}")
                raise APIError(f"Not Found (404): {response.text}")
            else:
                logger.error(f"API Error ({response.status_code}) for URL {url}: {response.text}")
                raise APIError(f"API Error ({response.status_code}): {response.text}", 
                              status_code=response.status_code, response_text=response.text)
        
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            logger.error(f"Request failed after {response_time:.2f}ms for URL {url}: {str(e)}", exc_info=True)
            raise