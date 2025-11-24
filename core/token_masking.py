"""Utilities for masking sensitive tokens in logs (FR-28)."""

from __future__ import annotations
from typing import Any


def mask_token(token: str | None, visible_chars: int = 0) -> str:
    """Return a masked version of a token suitable for logging."""

    if not token:
        return "••••••••••"

    token = str(token)
    if visible_chars <= 0 or visible_chars >= len(token):
        return "••••••••••"

    visible = token[:visible_chars]
    return f"{visible}{'•' * max(10, len(token) - visible_chars)}"


def mask_payload(
    payload: dict[str, Any], keys: list[str] | None = None, deep: bool = False
) -> dict[str, Any]:
    """Return a shallow copy of a payload with sensitive fields masked."""

    if keys is None:
        keys = ["token", "api_token", "password", "secret", "api_key"]

    masked = payload.copy()
    for key in keys:
        if key in masked and masked[key] is not None:
            masked[key] = mask_token(str(masked[key]))

    if deep:
        for key, value in masked.items():
            if isinstance(value, dict):
                masked[key] = mask_payload(value, keys=keys, deep=True)

    return masked


def mask_dict_keys(data: dict[str, Any], keys: list[str]) -> dict[str, Any]:
    """Return a shallow copy of a dictionary with specified keys masked."""
    masked = data.copy()
    for key in keys:
        if key in masked and masked[key] is not None:
            masked[key] = mask_token(str(masked[key]))
    return masked


__all__ = ["mask_token", "mask_payload", "mask_dict_keys"]
