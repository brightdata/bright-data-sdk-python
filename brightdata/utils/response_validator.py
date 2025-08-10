"""
Minimal response validation utilities for Bright Data SDK
"""
import json
from typing import Any, Dict, Union
from ..exceptions import ValidationError


def safe_json_parse(response_text: str) -> Dict[str, Any]:
    """
    Safely parse JSON response with minimal validation
    
    Args:
        response_text: Raw response text from API
        
    Returns:
        Parsed JSON data or original text if parsing fails
    """
    if not response_text:
        return {}
    
    try:
        return json.loads(response_text)
    except (json.JSONDecodeError, TypeError):
        # Return original text if JSON parsing fails
        return response_text


def validate_response_size(response_text: str, max_size_mb: float = 100.0) -> None:
    """
    Quick size check to prevent memory issues
    
    Args:
        response_text: Response text to validate
        max_size_mb: Maximum allowed size in megabytes
    """
    if response_text and len(response_text) > (max_size_mb * 1024 * 1024):
        raise ValidationError(f"Response too large (>{max_size_mb}MB)")


def check_response_not_empty(data: Any) -> None:
    """
    Minimal check that response contains data
    
    Args:
        data: Response data to check
    """
    if data is None or (isinstance(data, str) and len(data.strip()) == 0):
        raise ValidationError("Empty response received")