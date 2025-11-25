import logging
import time
from uuid import uuid4
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger("autodoc")
logging.basicConfig(level=logging.INFO)


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start = time.time()
        cid = request.headers.get("X-Request_ID") or str(uuid4())
        request.state.correlation_id = cid

        try:
            logger.info(
                {
                    "event": "request.start",
                    "cid": cid,
                    "method": request.method,
                    "path": request.url.path,
                },
            )
            response = await call_next(request)
            # Add correlation ID to response headers
            response.headers["X-Request-ID"] = cid
            return response
        except Exception as exc:
            elapsed = round((time.time() - start) * 1000, 2)
            logger.exception(
                "Request error",
                extra={
                    "event": "request.error",
                    "cid": cid,
                    "method": request.method,
                    "path": request.url.path,
                    "error": str(exc),
                    "ms": elapsed,
                },
            )
            raise
        finally:
            elapsed = round((time.time() - start) * 1000, 2)
            logger.info(
                {
                    "event": "request.end",
                    "cid": cid,
                    "method": request.method,
                    "path": request.url.path,
                    "ms": elapsed,
                },
            )
