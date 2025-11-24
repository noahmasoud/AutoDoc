"""Security middleware for masking sensitive data in logs (FR-28, NFR-9)."""

import logging
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware


logger = logging.getLogger(__name__)

# Fields that should be masked in logs
SENSITIVE_FIELDS = [
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


class SecurityLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware to redact sensitive fields from request/response logs.

    Implements FR-28 (token masking) and NFR-9 (secrets never logged).
    """

    async def dispatch(self, request: Request, call_next):
        """Process request and mask sensitive data in logs."""
        # Log request with masked sensitive data
        await self._log_request_safely(request)

        response = None
        try:
            response = await call_next(request)
            # Log response with masked sensitive data (if applicable)
            await self._log_response_safely(request, response)
            return response
        except Exception as e:
            # Mask sensitive data in error logs
            await self._log_error_safely(request, e)
            raise

    async def _log_request_safely(self, request: Request) -> None:
        """Log request with sensitive fields masked."""
        try:
            # Only log for potentially sensitive endpoints
            if self._is_sensitive_endpoint(request.url.path):
                # Mask headers (body will be logged by route handlers with masking)
                headers = dict(request.headers)
                masked_headers = self._mask_headers(headers)

                logger.debug(
                    "Request received",
                    extra={
                        "method": request.method,
                        "path": request.url.path,
                        "headers": masked_headers,
                    },
                )
        except Exception as e:
            # Don't fail requests due to logging issues
            logger.warning(f"Error logging request safely: {e}")

    async def _log_response_safely(self, request: Request, response: Response) -> None:
        """Log response with sensitive fields masked."""
        try:
            if self._is_sensitive_endpoint(request.url.path) and hasattr(
                response, "body"
            ):
                # For streaming responses, we can't easily read the body
                # Just log status and headers
                masked_headers = self._mask_headers(dict(response.headers))
                logger.debug(
                    "Response sent",
                    extra={
                        "method": request.method,
                        "path": request.url.path,
                        "status_code": response.status_code,
                        "headers": masked_headers,
                    },
                )
        except Exception as e:
            logger.warning(f"Error logging response safely: {e}")

    async def _log_error_safely(self, request: Request, error: Exception) -> None:
        """Log error with sensitive data masked."""
        try:
            error_message = str(error)
            # Mask any sensitive data in error messages
            masked_message = self._mask_string(error_message)

            logger.error(
                "Request failed",
                extra={
                    "method": request.method,
                    "path": request.url.path,
                    "error_type": type(error).__name__,
                    "error_message": masked_message,
                },
                exc_info=False,  # Don't include full traceback to avoid exposing sensitive data
            )
        except Exception as e:
            logger.warning(f"Error logging error safely: {e}")

    def _is_sensitive_endpoint(self, path: str) -> bool:
        """Check if endpoint might contain sensitive data."""
        sensitive_paths = ["/connections", "/login", "/auth", "/api-key"]
        return any(sensitive_path in path.lower() for sensitive_path in sensitive_paths)

    def _mask_headers(self, headers: dict[str, str]) -> dict[str, str]:
        """Mask sensitive header values."""
        masked = headers.copy()
        for key in list(masked.keys()):
            key_lower = key.lower()
            if any(field in key_lower for field in SENSITIVE_FIELDS):
                masked[key] = "••••••••••"
        return masked

    def _mask_string(self, text: str) -> str:
        """Mask any sensitive patterns in a string."""
        masked = text
        # Simple heuristic: mask if contains token-like patterns
        import re

        # Mask token patterns (e.g., ATATT...)
        masked = re.sub(r"ATATT[A-Za-z0-9_-]+", "ATATT••••••••", masked)
        # Mask other token-like patterns
        return re.sub(
            r"[A-Za-z0-9_-]{20,}",
            lambda m: m.group()[:8] + "••••••••" if len(m.group()) > 20 else m.group(),
            masked,
        )


def mask_exception_message(exception: Exception) -> str:
    """
    Mask sensitive data in exception messages.

    Used in error handlers to ensure tokens never appear in error traces (NFR-9).

    Args:
        exception: Exception to mask

    Returns:
        Masked exception message
    """
    message = str(exception)

    # Mask common sensitive patterns
    import re

    # Mask Confluence API token patterns (ATATT...)
    message = re.sub(r"ATATT[A-Za-z0-9_-]{20,}", "ATATT••••••••", message)
    # Mask long alphanumeric strings that might be tokens (20+ chars)
    message = re.sub(
        r"\b[A-Za-z0-9_-]{20,}\b",
        lambda m: m.group()[:8] + "••••••••" if len(m.group()) > 20 else m.group(),
        message,
    )
    # Mask patterns like "token=..." or "api_token=..."
    return re.sub(
        r"(token|api_token|password|secret|api_key|access_token|refresh_token|auth_token)\s*[=:]\s*[A-Za-z0-9_-]{10,}",
        lambda m: m.group().split("=")[0] + "=••••••••"
        if "=" in m.group()
        else m.group().split(":")[0] + ":••••••••",
        message,
        flags=re.IGNORECASE,
    )
