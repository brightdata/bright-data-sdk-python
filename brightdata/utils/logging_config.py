"""
Structured logging configuration for Bright Data SDK
"""
import logging
import json
import time
from typing import Dict, Any
import uuid


class StructuredFormatter(logging.Formatter):
    """Custom formatter that outputs structured JSON logs"""
    
    def __init__(self):
        super().__init__()
        self.start_time = time.time()
    
    def format(self, record):
        log_data = {
            'timestamp': self.formatTime(record),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        
        correlation_id = getattr(record, 'correlation_id', None)
        if correlation_id:
            log_data['correlation_id'] = correlation_id
            
        if hasattr(record, 'url'):
            log_data['url'] = record.url
        if hasattr(record, 'method'):
            log_data['method'] = record.method
        if hasattr(record, 'status_code'):
            log_data['status_code'] = record.status_code
        if hasattr(record, 'response_time'):
            log_data['response_time_ms'] = record.response_time
            
        if record.exc_info:
            log_data['exception'] = {
                'type': record.exc_info[0].__name__ if record.exc_info[0] else None,
                'message': str(record.exc_info[1]) if record.exc_info[1] else None,
                'traceback': self.formatException(record.exc_info)
            }
        
        log_data = self._sanitize_log_data(log_data)
        
        return json.dumps(log_data, default=str)
    
    def _sanitize_log_data(self, log_data: Dict[str, Any]) -> Dict[str, Any]:
        """Remove or mask sensitive information from log data"""
        sensitive_keys = ['authorization', 'token', 'api_token', 'password', 'secret']
        
        def sanitize_value(key: str, value: Any) -> Any:
            if isinstance(key, str) and any(sensitive in key.lower() for sensitive in sensitive_keys):
                return "***REDACTED***"
            elif isinstance(value, str) and len(value) > 20:
                if value.isalnum() and len(value) > 32:
                    return f"{value[:8]}***REDACTED***{value[-4:]}"
            return value
        
        def recursive_sanitize(obj):
            if isinstance(obj, dict):
                return {k: recursive_sanitize(sanitize_value(k, v)) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [recursive_sanitize(item) for item in obj]
            else:
                return obj
        
        return recursive_sanitize(log_data)


def setup_logging(level: str = "INFO", structured: bool = True, verbose: bool = True) -> None:
    """
    Setup logging configuration for the SDK
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        structured: Whether to use structured JSON logging
        verbose: Whether to show verbose logging (default: True)
                When False, only WARNING and above are shown
                When True, uses the specified level
    """
    if not verbose:
        log_level = logging.WARNING
    else:
        log_level = getattr(logging, level.upper(), logging.INFO)
    
    root_logger = logging.getLogger('brightdata')
    root_logger.handlers.clear()
    
    handler = logging.StreamHandler()
    handler.setLevel(log_level)
    
    if structured:
        formatter = StructuredFormatter()
    else:
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    handler.setFormatter(formatter)
    root_logger.addHandler(handler)
    root_logger.setLevel(log_level)
    
    root_logger.propagate = False


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with the specified name
    
    Args:
        name: Logger name
        
    Returns:
        Configured logger instance
    """
    return logging.getLogger(f'brightdata.{name}')


def log_request(logger: logging.Logger, method: str, url: str, 
                status_code: int = None, response_time: float = None,
                correlation_id: str = None) -> None:
    """
    Log HTTP request details
    
    Args:
        logger: Logger instance
        method: HTTP method
        url: Request URL (will be sanitized)
        status_code: HTTP response status code
        response_time: Response time in milliseconds
        correlation_id: Request correlation ID
    """
    extra = {
        'method': method,
        'url': _sanitize_url(url),
        'correlation_id': correlation_id or str(uuid.uuid4())
    }
    
    if status_code is not None:
        extra['status_code'] = status_code
    if response_time is not None:
        extra['response_time'] = response_time
    
    if status_code and status_code >= 400:
        logger.error(f"HTTP request failed: {method} {_sanitize_url(url)}", extra=extra)
    else:
        logger.info(f"HTTP request: {method} {_sanitize_url(url)}", extra=extra)


def _sanitize_url(url: str) -> str:
    """Sanitize URL to remove sensitive query parameters"""
    try:
        from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
        
        parsed = urlparse(url)
        query_params = parse_qs(parsed.query)
        
        sensitive_params = ['token', 'api_key', 'secret', 'password']
        for param in sensitive_params:
            if param in query_params:
                query_params[param] = ['***REDACTED***']
        
        sanitized_query = urlencode(query_params, doseq=True)
        sanitized = urlunparse((
            parsed.scheme, parsed.netloc, parsed.path,
            parsed.params, sanitized_query, parsed.fragment
        ))
        
        return sanitized
    except Exception:
        return url.split('?')[0] + ('?***PARAMS_REDACTED***' if '?' in url else '')