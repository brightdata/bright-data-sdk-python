"""
## Bright Data SDK Functions:
#### scrape() 
- Scrapes a website using Bright Data Web Unlocker API with proxy support (or multiple webstites sequentially)
#### search() 
- Performs web searches using Bright Data SERP API with customizable search engines (or multiple search queries sequentially)
#### download_content() 
- Saves scraped content to local files in various formats (JSON, CSV, etc.)
#### deliver_content()
- Sends scraped content to your storage (e.g., S3, GCS) or database (e.g., MongoDB, PostgreSQL)
"""

from datetime import datetime
import requests
import json
from typing import Union, Dict, Any, List
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import quote_plus

class bdclient:
    
    def __init__(self, api_token: str):
        """
        Initialize the Bright Data client with your API token\n
        #### Create an account at https://brightdata.com/ to get your API token.

        Args:
            api_token: Your Bright Data API token
        """
        self.api_token = api_token
        
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {self.api_token}',
            'Content-Type': 'application/json'
        })
        
        adapter = requests.adapters.HTTPAdapter(
            pool_connections=20,
            pool_maxsize=20,
            max_retries=0
        )
        self.session.mount('https://', adapter)
        self.session.mount('http://', adapter)

    def scrape(
        self,
        url: Union[str, List[str]],
        zone: str = "mcp_unlocker",
        format: str = "json",
        method: str = "GET", 
        country: str = "us",
        data_format: str = "markdown",
        async_request: bool = False,
        max_workers: int = 10,
        timeout: int = 30
    ) -> Union[Dict[str, Any], str, List[Union[Dict[str, Any], str]]]:
        """
        Unlock and scrape a website using Bright Data Web Unlocker API
        
        ## Args:
            url: Single URL string (e.g., "https://example.com") or list of URLs (e.g., ["https://site1.com", "https://site2.com"])
            zone: Zone identifier (default: "mcp_unlocker") - defines your product configuration
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
        
        if isinstance(url, list):
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
                        error_result = {"error": str(e), "url": url[index]}
                        results[index] = error_result
            
            return results
        else:
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
        
        try:
            response = self.session.post(
                endpoint,
                json=payload,
                params=params,
                timeout=timeout
            )
            
            if response.status_code == 200:
                if format == "json":
                    try:
                        return response.json()
                    except json.JSONDecodeError:
                        return response.text
                else:
                    return response.text
                    
            elif response.status_code == 400:
                raise Exception(f"Bad Request (400): {response.text}")
            elif response.status_code == 401:
                raise Exception(f"Unauthorized (401): Check your API token. {response.text}")
            else:
                raise Exception(f"API Error ({response.status_code}): {response.text}")
                
        except requests.exceptions.Timeout:
            raise Exception("Request timed out after 60 seconds")
        except requests.exceptions.ConnectionError:
            raise Exception("Connection error - check your internet connection")
        except requests.exceptions.RequestException as e:
            raise Exception(f"Request failed: {str(e)}")

    def search(
        self,
        query: Union[str, List[str]],
        search_engine: str = "google",
        zone: str = "serp_api1",
        format: str = "json",
        method: str = "GET",
        country: str = "us",
        data_format: str = "markdown",
        async_request: bool = False,
        max_workers: int = 10,
        timeout: int = 30
    ) -> Union[Dict[str, Any], str, List[Union[Dict[str, Any], str]]]:
        """
        Search the web using Bright Data SERP API
        
        ## Args:
            query: Search query string (e.g., "pizza") or list of queries (e.g., ["pizza", "restaurants"])
            search_engine: Search engine to use - "google", "bing", or "yandex" (default: "google")
            zone: Zone identifier (default: "serp_api1") - defines your product configuration
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
        
        base_url_map = {
            "google": "https://www.google.com/search?q=",
            "bing": "https://www.bing.com/search?q=",
            "yandex": "https://yandex.com/search/?text="
        }
        
        if search_engine not in base_url_map:
            raise ValueError(f"Unsupported search engine: {search_engine}. Supported engines: {list(base_url_map.keys())}")
        
        base_url = base_url_map[search_engine]
        
        if isinstance(query, list):
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
                        error_result = {"error": str(e), "query": query[index]}
                        results[index] = error_result
            
            return results
        else:
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
        
        try:
            response = self.session.post(
                endpoint,
                json=payload,
                params=params,
                timeout=timeout
            )
            
            if response.status_code == 200:
                if format == "json":
                    try:
                        return response.json()
                    except json.JSONDecodeError:
                        return response.text
                else:
                    return response.text
                    
            elif response.status_code == 400:
                raise Exception(f"Bad Request (400): {response.text}")
            elif response.status_code == 401:
                raise Exception(f"Unauthorized (401): Check your API token. {response.text}")
            else:
                raise Exception(f"API Error ({response.status_code}): {response.text}")
                
        except requests.exceptions.Timeout:
            raise Exception("Request timed out after 60 seconds")
        except requests.exceptions.ConnectionError:
            raise Exception("Connection error - check your internet connection")
        except requests.exceptions.RequestException as e:
            raise Exception(f"Request failed: {str(e)}")


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
            
            print(f"✅ Content downloaded to: {filename}")
            return filename
            
        except Exception as e:
            raise Exception(f"Failed to download content: {str(e)}")
