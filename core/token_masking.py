"""Utilities for masking sensitive tokens in logs (FR-28, NFR-9)."""

from __future__ import annotations
from typing import Any, Dict, List


def mask_token(token: str | None, visible_chars: int = 0) -> str:
    """
    Return a masked version of a token suitable for logging.
    
    Args:
        token: Token string to mask
        visible_chars: Number of characters to show (default: 0, fully masked)
    
    Returns:
        Masked token string (e.g., "••••••••••")
    """
    if not token:
        return "••••••••••"

    token = str(token)
    if visible_chars <= 0 or visible_chars >= len(token):
        return "••••••••••"

    visible = token[:visible_chars]
    return f"{visible}{'•' * max(10, len(token) - visible_chars)}"


def mask_payload(payload: Dict[str, Any], keys: List[str] | None = None, deep: bool = True) -> Dict[str, Any]:
    """
    Return a copy of a payload with sensitive fields masked.
    
    Args:
        payload: Dictionary to mask
        keys: List of keys to mask (default: common sensitive field names)
        deep: If True, recursively mask nested dictionaries
    
    Returns:
        Masked copy of the payload
    """
    if keys is None:
        keys = [
            "token",
            "api_token",
            "password",
            "secret",
            "api_key",
            "access_token",
            "refresh_token",
            "auth_token",
            "authorization",
            "x-api-key",
        ]

    if not isinstance(payload, dict):
        return payload

    masked = {}
    for key, value in payload.items():
        key_lower = key.lower()
        # Check if this key should be masked
        should_mask = any(mask_key in key_lower for mask_key in keys)
        
        if should_mask and value is not None:
            masked[key] = mask_token(str(value))
        elif deep and isinstance(value, dict):
            # Recursively mask nested dictionaries
            masked[key] = mask_payload(value, keys, deep=True)
        elif deep and isinstance(value, list):
            # Mask items in lists
            masked[key] = [
                mask_payload(item, keys, deep=True) if isinstance(item, dict) else item
                for item in value
            ]
        else:
            masked[key] = value
    
    return masked


def mask_dict_keys(data: Dict[str, Any], keys_to_mask: List[str]) -> Dict[str, Any]:
    """Mask specific keys in a dictionary (non-recursive)."""
    masked = data.copy()
    for key in keys_to_mask:
        if key in masked:
            masked[key] = mask_token(masked[key])
    return masked


__all__ = ["mask_token", "mask_payload", "mask_dict_keys"]
