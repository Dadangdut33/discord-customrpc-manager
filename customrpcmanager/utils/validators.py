"""
Input validation utilities.

Validates Discord RPC fields according to Discord's specifications.
"""

import re
from typing import Optional, Tuple


def validate_app_id(app_id: str) -> Tuple[bool, Optional[str]]:
    """
    Validate Discord Application ID.
    
    Args:
        app_id: Application ID string
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not app_id:
        return False, "Application ID cannot be empty"
    
    if not app_id.isdigit():
        return False, "Application ID must contain only numbers"
    
    if len(app_id) < 17 or len(app_id) > 20:
        return False, "Application ID must be 17-20 digits"
    
    return True, None


def validate_url(url: str) -> Tuple[bool, Optional[str]]:
    """
    Validate URL for RPC buttons.
    
    Args:
        url: URL string
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not url:
        return False, "URL cannot be empty"
    
    # Basic URL validation
    url_pattern = re.compile(
        r'^https?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE
    )
    
    if not url_pattern.match(url):
        return False, "Invalid URL format (must start with http:// or https://)"
    
    if len(url) > 512:
        return False, "URL too long (max 512 characters)"
    
    return True, None


def validate_text_field(text: str, field_name: str, max_length: int = 128) -> Tuple[bool, Optional[str]]:
    """
    Validate text field length.
    
    Args:
        text: Text to validate
        field_name: Name of field for error message
        max_length: Maximum allowed length
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if len(text) > max_length:
        return False, f"{field_name} exceeds maximum length of {max_length} characters"
    
    return True, None


def validate_timestamp(timestamp: Optional[int]) -> Tuple[bool, Optional[str]]:
    """
    Validate Unix timestamp.
    
    Args:
        timestamp: Unix timestamp in seconds
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if timestamp is None:
        return True, None
    
    if timestamp < 0:
        return False, "Timestamp cannot be negative"
    
    # Check if timestamp is reasonable (between 2000 and 2100)
    if timestamp < 946684800 or timestamp > 4102444800:
        return False, "Timestamp appears to be invalid"
    
    return True, None


def validate_party_size(current: Optional[int], max_size: Optional[int]) -> Tuple[bool, Optional[str]]:
    """
    Validate party size values.
    
    Args:
        current: Current party size
        max_size: Maximum party size
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if current is None and max_size is None:
        return True, None
    
    if current is not None and current < 0:
        return False, "Party size cannot be negative"
    
    if max_size is not None and max_size < 0:
        return False, "Max party size cannot be negative"
    
    if current is not None and max_size is not None:
        if current > max_size:
            return False, "Current party size cannot exceed maximum"
    
    return True, None


def validate_button_label(label: str) -> Tuple[bool, Optional[str]]:
    """
    Validate button label.
    
    Args:
        label: Button label text
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not label:
        return False, "Button label cannot be empty"
    
    if len(label) > 32:
        return False, "Button label exceeds maximum length of 32 characters"
    
    return True, None
