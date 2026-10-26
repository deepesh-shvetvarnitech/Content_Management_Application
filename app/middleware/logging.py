import logging
import time
from starlette.types import ASGIApp, Scope, Receive, Send

request_logger = logging.getLogger("app.requests")


class RequestLoggingMiddleware:
    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        start_time = time.perf_counter()
        status_code = 500
        request_id = scope.get("state", {}).get("request_id", "-")

        async def capture_status(message):
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = message["status"]
            await send(message)

        try:
            await self.app(scope, receive, capture_status)
        except Exception:
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            request_logger.exception(
                "request_id=%s method=%s path=%s status=%s duration_ms=%.2f",
                request_id,
                scope.get("method", "-"),
                scope.get("path", "-"),
                status_code,
                elapsed_ms,
            )
            raise
        else:
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            request_logger.info(
                "request_id=%s method=%s path=%s status=%s duration_ms=%.2f",
                request_id,
                scope.get("method", "-"),
                scope.get("path", "-"),
                status_code,
                elapsed_ms,
            )
