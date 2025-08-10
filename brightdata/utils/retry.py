import time
import random
import requests
from functools import wraps
from ..exceptions import NetworkError, APIError


def retry_request(max_retries=3, backoff_factor=1.5, retry_statuses=None, max_backoff=60):
    """
    Decorator for retrying requests with exponential backoff and jitter
    
    Args:
        max_retries: Maximum number of retry attempts
        backoff_factor: Exponential backoff multiplier
        retry_statuses: HTTP status codes that should trigger retries
        max_backoff: Maximum backoff time in seconds
    """
    if retry_statuses is None:
        retry_statuses = {429, 500, 502, 503, 504}
    
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_retries + 1):  # +1 to include initial attempt
                try:
                    response = func(*args, **kwargs)
                    
                    # Check if we should retry based on status code
                    if hasattr(response, 'status_code') and response.status_code in retry_statuses:
                        if attempt >= max_retries:
                            raise APIError(
                                f"Server error after {max_retries} retries: HTTP {response.status_code}",
                                status_code=response.status_code,
                                response_text=getattr(response, 'text', '')
                            )
                        
                        # Calculate backoff with jitter
                        backoff_time = min(backoff_factor ** attempt, max_backoff)
                        jitter = backoff_time * 0.1 * random.random()  # Add up to 10% jitter
                        total_delay = backoff_time + jitter
                        
                        time.sleep(total_delay)
                        continue
                    
                    return response
                    
                except requests.exceptions.ConnectTimeout as e:
                    last_exception = NetworkError(f"Connection timeout: {str(e)}")
                except requests.exceptions.ReadTimeout as e:
                    last_exception = NetworkError(f"Read timeout: {str(e)}")
                except requests.exceptions.Timeout as e:
                    last_exception = NetworkError(f"Request timeout: {str(e)}")
                except requests.exceptions.ConnectionError as e:
                    # Handle DNS resolution, connection refused, etc.
                    if "Name or service not known" in str(e):
                        last_exception = NetworkError(f"DNS resolution failed: {str(e)}")
                    elif "Connection refused" in str(e):
                        last_exception = NetworkError(f"Connection refused: {str(e)}")
                    else:
                        last_exception = NetworkError(f"Connection error: {str(e)}")
                except requests.exceptions.SSLError as e:
                    last_exception = NetworkError(f"SSL/TLS error: {str(e)}")
                except requests.exceptions.ProxyError as e:
                    last_exception = NetworkError(f"Proxy error: {str(e)}")
                except requests.exceptions.RequestException as e:
                    last_exception = NetworkError(f"Network error: {str(e)}")
                except Exception as e:
                    # Catch any other unexpected exceptions
                    last_exception = NetworkError(f"Unexpected error: {str(e)}")
                
                # If this was the last attempt, raise the exception
                if attempt >= max_retries:
                    raise last_exception
                
                # Calculate backoff with jitter for network errors
                backoff_time = min(backoff_factor ** attempt, max_backoff)
                jitter = backoff_time * 0.1 * random.random()
                total_delay = backoff_time + jitter
                
                time.sleep(total_delay)
            
            # This should never be reached, but just in case
            if last_exception:
                raise last_exception
            return None
            
        return wrapper
    return decorator