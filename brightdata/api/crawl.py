import json
from typing import Union, Dict, Any, List, Optional
from ..utils import get_logger, validate_url
from ..exceptions import ValidationError, APIError, AuthenticationError

logger = get_logger('api.crawl')


class CrawlAPI:
    """Handles crawl operations using Bright Data's Web Crawl API"""
    
    CRAWL_DATASET_ID = "gd_m6gjtfmeh43we6cqc"
    
    AVAILABLE_OUTPUT_FIELDS = [
        "markdown", "url", "html2text", "page_html", "ld_json", 
        "page_title", "timestamp", "input", "discovery_input", 
        "error", "error_code", "warning", "warning_code"
    ]
    
    def __init__(self, session, api_token, default_timeout=30, max_retries=3, retry_backoff=1.5):
        self.session = session
        self.api_token = api_token
        self.default_timeout = default_timeout
        self.max_retries = max_retries
        self.retry_backoff = retry_backoff
    
    def crawl(
        self,
        url: Union[str, List[str]],
        ignore_sitemap: Optional[bool] = None,
        depth: Optional[int] = None,
        filter: Optional[str] = None,
        exclude_filter: Optional[str] = None,
        custom_output_fields: Optional[List[str]] = None,
        include_errors: bool = True
    ) -> Dict[str, Any]:
        """
        ## Crawl websites using Bright Data's Web Crawl API
        
        Performs web crawling to discover and scrape multiple pages from a website
        starting from the specified URL(s).
        
        ### Parameters:
        - `url` (str | List[str]): Domain URL(s) to crawl (required)
        - `ignore_sitemap` (bool, optional): Ignore sitemap when crawling
        - `depth` (int, optional): Maximum depth to crawl relative to the entered URL
        - `filter` (str, optional): Regular expression to include only certain URLs (e.g. "/product/")
        - `exclude_filter` (str, optional): Regular expression to exclude certain URLs (e.g. "/ads/")
        - `custom_output_fields` (List[str], optional): Custom output schema fields to include
        - `include_errors` (bool, optional): Include errors in response (default: True)
        
        ### Returns:
        - `Dict[str, Any]`: Crawl response with snapshot_id for tracking
        
        ### Example Usage:
        ```python
        # Single URL crawl
        result = client.crawl("https://example.com/")
        
        # Multiple URLs with filters
        urls = ["https://example.com/", "https://example2.com/"]
        result = client.crawl(
            url=urls,
            filter="/product/",
            exclude_filter="/ads/",
            depth=2,
            ignore_sitemap=True
        )
        
        # Custom output schema
        result = client.crawl(
            url="https://example.com/",
            custom_output_fields=["markdown", "url", "page_title"]
        )
        ```
        
        ### Raises:
        - `ValidationError`: Invalid URL or parameters
        - `AuthenticationError`: Invalid API token or insufficient permissions
        - `APIError`: Request failed or server error
        """
        if isinstance(url, str):
            urls = [url]
        elif isinstance(url, list):
            urls = url
        else:
            raise ValidationError("URL must be a string or list of strings")
        
        if not urls:
            raise ValidationError("At least one URL is required")
        
        for u in urls:
            if not isinstance(u, str) or not u.strip():
                raise ValidationError("All URLs must be non-empty strings")
            validate_url(u)
        
        if custom_output_fields is not None:
            if not isinstance(custom_output_fields, list):
                raise ValidationError("custom_output_fields must be a list")
            
            invalid_fields = [field for field in custom_output_fields if field not in self.AVAILABLE_OUTPUT_FIELDS]
            if invalid_fields:
                raise ValidationError(f"Invalid output fields: {invalid_fields}. Available fields: {self.AVAILABLE_OUTPUT_FIELDS}")
        
        crawl_inputs = []
        for u in urls:
            crawl_input = {"url": u}
            
            if ignore_sitemap is not None:
                crawl_input["ignore_sitemap"] = ignore_sitemap
            if depth is not None:
                crawl_input["depth"] = depth
            if filter is not None:
                crawl_input["filter"] = filter
            if exclude_filter is not None:
                crawl_input["exclude_filter"] = exclude_filter
                
            crawl_inputs.append(crawl_input)
        
        api_url = "https://api.brightdata.com/datasets/v3/trigger"
        
        params = {
            "dataset_id": self.CRAWL_DATASET_ID,
            "include_errors": str(include_errors).lower(),
            "type": "discover_new",
            "discover_by": "domain_url"
        }
        
        if custom_output_fields:
            payload = {
                "input": crawl_inputs,
                "custom_output_fields": custom_output_fields
            }
        else:
            payload = crawl_inputs
        
        logger.info(f"Starting crawl for {len(urls)} URL(s)")
        logger.debug(f"Crawl parameters: depth={depth}, filter={filter}, exclude_filter={exclude_filter}")
        
        try:
            response = self.session.post(
                api_url,
                params=params,
                json=payload,
                timeout=self.default_timeout
            )
            
            if response.status_code == 200:
                result = response.json()
                snapshot_id = result.get('snapshot_id')
                logger.info(f"Crawl initiated successfully. Snapshot ID: {snapshot_id}")
                return result
                
            elif response.status_code == 401:
                logger.error("Unauthorized (401): Check API token")
                raise AuthenticationError(f"Unauthorized (401): Check your API token. {response.text}")
            elif response.status_code == 403:
                logger.error("Forbidden (403): Insufficient permissions")
                raise AuthenticationError(f"Forbidden (403): Insufficient permissions. {response.text}")
            elif response.status_code == 400:
                logger.error(f"Bad request (400): {response.text}")
                raise APIError(f"Bad request (400): {response.text}")
            else:
                logger.error(f"Crawl request failed ({response.status_code}): {response.text}")
                raise APIError(
                    f"Crawl request failed ({response.status_code}): {response.text}",
                    status_code=response.status_code,
                    response_text=response.text
                )
                
        except Exception as e:
            if isinstance(e, (ValidationError, AuthenticationError, APIError)):
                raise
            logger.error(f"Unexpected error during crawl: {e}")
            raise APIError(f"Unexpected error during crawl: {str(e)}")