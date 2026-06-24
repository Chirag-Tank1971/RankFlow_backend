import time

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from app.core.logging import get_logger

logger = get_logger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        start = time.perf_counter()
        logger.info("Incoming request: %s %s", request.method, request.url.path)

        try:
            response = await call_next(request)
        except Exception:
            logger.exception(
                "Unhandled exception during request: %s %s",
                request.method,
                request.url.path,
            )
            raise

        duration_ms = (time.perf_counter() - start) * 1000
        logger.info(
            "Completed request: %s %s status=%s duration=%.2fms",
            request.method,
            request.url.path,
            response.status_code,
            duration_ms,
        )
        return response
