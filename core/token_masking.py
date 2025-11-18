"""Token masking utilities for logging.

Implements FR-28: Mask tokens in all logs.
Never writes raw token values to logs or console.
"""


def mask_token(token: str | None, visible_chars: int = 0) -> str:
    """
    Mask a token for safe logging.

    Args:
        token: Token to mask (can be None)
        visible_chars: Number of characters to show at the start (default: 0)

    Returns:
        Masked token string (e.g., "••••••••••" or "ab••••••••")
    """
    if not token:
        return "••••••••••"

    if len(token) <= visible_chars:
        return "••••••••••"

    if visible_chars > 0:
        visible = token[:visible_chars]
        return f"{visible}{'•' * max(10, len(token) - visible_chars)}"

    return "••••••••••"


def mask_in_dict(data: dict, keys_to_mask: list[str] | None = None) -> dict:
    """
    Create a copy of dict with specified keys masked.

    Args:
        data: Dictionary to process
        keys_to_mask: List of keys to mask (default: common token field names)

    Returns:
        New dictionary with masked values
    """
    if keys_to_mask is None:
        keys_to_mask = [
            "token",
            "api_token",
            "password",
            "secret",
            "api_key",
            "access_token",
            "refresh_token",
            "encrypted_token",
        ]

    masked = data.copy()
    for key in keys_to_mask:
        if key in masked and masked[key] is not None:
            masked[key] = mask_token(str(masked[key]))

    return masked

