"""Utilities for masking sensitive tokens in logs (FR-28)."""

from __future__ import annotations
from typing import Any, Dict


def mask_token(token: str | None, visible_chars: int = 0) -> str:
    """Return a masked version of a token suitable for logging."""

    if not token:
        return "••••••••••"

    token = str(token)
    if visible_chars <= 0 or visible_chars >= len(token):
        return "••••••••••"

    visible = token[:visible_chars]
    return f"{visible}{'•' * max(10, len(token) - visible_chars)}"


def mask_payload(payload: Dict[str, Any], keys: list[str] | None = None) -> Dict[str, Any]:
    """Return a shallow copy of a payload with sensitive fields masked."""

    if keys is None:
        keys = ["token", "api_token", "password", "secret"]

    masked = payload.copy()
    for key in keys:
        if key in masked and masked[key] is not None:
            masked[key] = mask_token(str(masked[key]))
    return masked


__all__ = ["mask_token", "mask_payload"]

