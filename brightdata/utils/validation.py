from urllib.parse import urlparse
from typing import Union, List
from ..exceptions import ValidationError


def validate_url(url: str) -> None:
    """Validate URL format with comprehensive checks"""
    if not isinstance(url, str):
        raise ValidationError(f"URL must be a string, got {type(url).__name__}")
    
    if not url.strip():
        raise ValidationError("URL cannot be empty or whitespace")
    
    # Check URL length
    if len(url) > 8192:  # Common URL length limit
        raise ValidationError("URL exceeds maximum length of 8192 characters")
    
    try:
        parsed = urlparse(url.strip())
        if not parsed.scheme:
            raise ValidationError(f"URL must include a scheme (http/https): {url}")
        if parsed.scheme.lower() not in ['http', 'https']:
            raise ValidationError(f"URL scheme must be http or https, got: {parsed.scheme}")
        if not parsed.netloc:
            raise ValidationError(f"URL must include a valid domain: {url}")
        # Check for suspicious characters
        if any(char in url for char in ['<', '>', '"', "'"]):
            raise ValidationError("URL contains invalid characters")
    except Exception as e:
        if isinstance(e, ValidationError):
            raise
        raise ValidationError(f"Invalid URL format '{url}': {str(e)}")


def validate_zone_name(zone: str = None) -> None:
    """Validate zone name format with enhanced checks"""
    if zone is None:
        return  # Zone can be None (optional parameter)
    
    if not isinstance(zone, str):
        raise ValidationError(f"Zone name must be a string, got {type(zone).__name__}")
    
    zone = zone.strip()
    if not zone:
        raise ValidationError("Zone name cannot be empty or whitespace")
    
    if len(zone) < 3:
        raise ValidationError("Zone name must be at least 3 characters long")
    
    if len(zone) > 63:
        raise ValidationError("Zone name must not exceed 63 characters")
    
    if not zone.replace('_', '').replace('-', '').isalnum():
        raise ValidationError("Zone name can only contain letters, numbers, hyphens, and underscores")
    
    if zone.startswith('-') or zone.endswith('-'):
        raise ValidationError("Zone name cannot start or end with a hyphen")
    
    if zone.startswith('_') or zone.endswith('_'):
        raise ValidationError("Zone name cannot start or end with an underscore")


def validate_country_code(country: str) -> None:
    """Validate ISO country code format"""
    if not isinstance(country, str):
        raise ValidationError(f"Country code must be a string, got {type(country).__name__}")
    
    country = country.strip().lower()
    if len(country) == 0:
        return
    
    if len(country) != 2:
        raise ValidationError("Country code must be exactly 2 characters (ISO 3166-1 alpha-2) or empty")
    
    if not country.isalpha():
        raise ValidationError("Country code must contain only letters")


def validate_timeout(timeout: int) -> None:
    """Validate timeout value"""
    if timeout is None:
        return  # Timeout can be None (use default)
    
    if not isinstance(timeout, int):
        raise ValidationError(f"Timeout must be an integer, got {type(timeout).__name__}")
    
    if timeout <= 0:
        raise ValidationError("Timeout must be greater than 0 seconds")
    
    if timeout > 300:  # 5 minutes max
        raise ValidationError("Timeout cannot exceed 300 seconds (5 minutes)")


def validate_max_workers(max_workers: int) -> None:
    """Validate max_workers parameter"""
    if max_workers is None:
        return  # Can be None (use default)
    
    if not isinstance(max_workers, int):
        raise ValidationError(f"max_workers must be an integer, got {type(max_workers).__name__}")
    
    if max_workers <= 0:
        raise ValidationError("max_workers must be greater than 0")
    
    if max_workers > 50:  # Reasonable upper limit
        raise ValidationError("max_workers cannot exceed 50 (to prevent resource exhaustion)")


def validate_url_list(urls: List[str], max_urls: int = 100) -> None:
    """Validate list of URLs with size limits"""
    if not isinstance(urls, list):
        raise ValidationError(f"URL list must be a list, got {type(urls).__name__}")
    
    if len(urls) == 0:
        raise ValidationError("URL list cannot be empty")
    
    if len(urls) > max_urls:
        raise ValidationError(f"URL list cannot contain more than {max_urls} URLs")
    
    for i, url in enumerate(urls):
        try:
            validate_url(url)
        except ValidationError as e:
            raise ValidationError(f"Invalid URL at index {i}: {str(e)}")


def validate_search_engine(search_engine: str) -> None:
    """Validate search engine parameter"""
    if not isinstance(search_engine, str):
        raise ValidationError(f"Search engine must be a string, got {type(search_engine).__name__}")
    
    valid_engines = ['google', 'bing', 'yandex']
    search_engine = search_engine.strip().lower()
    
    if search_engine not in valid_engines:
        raise ValidationError(f"Invalid search engine '{search_engine}'. Valid options: {', '.join(valid_engines)}")


def validate_query(query: Union[str, List[str]]) -> None:
    """Validate search query parameter"""
    if isinstance(query, str):
        if not query.strip():
            raise ValidationError("Search query cannot be empty or whitespace")
        if len(query) > 2048:
            raise ValidationError("Search query cannot exceed 2048 characters")
    elif isinstance(query, list):
        if len(query) == 0:
            raise ValidationError("Query list cannot be empty")
        if len(query) > 50:  # Reasonable limit
            raise ValidationError("Query list cannot contain more than 50 queries")
        for i, q in enumerate(query):
            if not isinstance(q, str):
                raise ValidationError(f"Query at index {i} must be a string, got {type(q).__name__}")
            if not q.strip():
                raise ValidationError(f"Query at index {i} cannot be empty or whitespace")
            if len(q) > 2048:
                raise ValidationError(f"Query at index {i} cannot exceed 2048 characters")
    else:
        raise ValidationError(f"Query must be a string or list of strings, got {type(query).__name__}")


def validate_response_format(response_format: str) -> None:
    """Validate response format parameter"""
    if not isinstance(response_format, str):
        raise ValidationError(f"Response format must be a string, got {type(response_format).__name__}")
    
    valid_formats = ['json', 'raw']
    response_format = response_format.strip().lower()
    
    if response_format not in valid_formats:
        raise ValidationError(f"Invalid response format '{response_format}'. Valid options: {', '.join(valid_formats)}")


def validate_http_method(method: str) -> None:
    """Validate HTTP method parameter"""
    if not isinstance(method, str):
        raise ValidationError(f"HTTP method must be a string, got {type(method).__name__}")
    
    valid_methods = ['GET', 'POST', 'PUT', 'DELETE', 'PATCH']
    method = method.strip().upper()
    
    if method not in valid_methods:
        raise ValidationError(f"Invalid HTTP method '{method}'. Valid options: {', '.join(valid_methods)}")