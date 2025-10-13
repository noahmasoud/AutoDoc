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

        response = None
        try:
            logger.info(
                {
                    "event": "request.start",
                    "cid": cid,
                    "method": request.method,
                    "path": request.url.path,
                },
            )
            return await call_next(request)
        finally:
            elapsed = round((time.time() - start) * 1000, 2)
            if response is not None:
                response.headers["X-Request-ID"] = cid
            logger.info(
                {
                    "event": "request.end",
                    "cid": cid,
                    "status": getattr(response, "status_code", 500),
                    "ms": elapsed,
                },
            )
