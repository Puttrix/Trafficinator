"""
Authentication and Security Module

Provides API key authentication and security utilities.
"""
import os
import secrets
from typing import Optional
from fastapi import Header, HTTPException, status
from fastapi.security import APIKeyHeader


# API Key configuration
API_KEY_NAME = "X-API-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)


def get_api_key() -> Optional[str]:
    """
    Get the configured API key from environment
    
    Returns:
        API key string or None if not configured
    """
    return os.getenv("CONTROL_UI_API_KEY")


def is_auth_enabled() -> bool:
    """
    Check if authentication is enabled
    
    Returns:
        True if API key is configured and not empty
    """
    api_key = get_api_key()
    return api_key is not None and api_key != ""


async def verify_api_key(api_key: Optional[str] = Header(None, alias=API_KEY_NAME)) -> bool:
    """
    Verify API key from request header
    
    Args:
        api_key: API key from X-API-Key header
        
    Returns:
        True if authentication is disabled or key is valid
        
    Raises:
        HTTPException: If authentication is enabled and key is invalid
    """
    # If authentication is disabled, allow access
    if not is_auth_enabled():
        return True
    
    # If authentication is enabled, require valid key
    configured_key = get_api_key()
    
    # Check if key was provided
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key required. Provide X-API-Key header.",
            headers={"WWW-Authenticate": "ApiKey"},
        )
    
    # Constant-time comparison to prevent timing attacks
    if not secrets.compare_digest(api_key, configured_key):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid API key",
        )
    
    return True


def generate_api_key(length: int = 32) -> str:
    """
    Generate a secure random API key
    
    Args:
        length: Length of the API key (default 32)
        
    Returns:
        Random API key string
    """
    return secrets.token_urlsafe(length)


def mask_sensitive_value(value: Optional[str], show_chars: int = 4) -> str:
    """
    Mask sensitive values for logging/display
    
    Args:
        value: Sensitive value to mask
        show_chars: Number of characters to show at start/end
        
    Returns:
        Masked string like "abc...xyz" or "[not set]"
    """
    if not value:
        return "[not set]"
    
    if len(value) <= show_chars * 2:
        return "*" * len(value)
    
    return f"{value[:show_chars]}...{value[-show_chars:]}"
