import logging
import time
from uuid import uuid4

from fastapi import FastAPI, Request

from app.request_context import request_id_var

logger = logging.getLogger(__name__)


def register_request_logging(
    app: FastAPI,
    service_name: str,
) -> None:
    @app.middleware("http")
    async def request_logging(request: Request, call_next):
        request_id = (
            request.headers.get("X-Request-ID")
            or uuid4().hex
        )
        token = request_id_var.set(request_id)
        started = time.perf_counter()

        try:
            response = await call_next(request)
            duration_ms = round(
                (time.perf_counter() - started) * 1000,
                2,
            )
            logger.info(
                "HTTP request completed",
                extra={
                    "service": service_name,
                    "event": "http_request_completed",
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": response.status_code,
                    "duration_ms": duration_ms,
                },
            )
            response.headers["X-Request-ID"] = request_id
            return response
        except Exception:
            duration_ms = round(
                (time.perf_counter() - started) * 1000,
                2,
            )
            logger.exception(
                "Unhandled request exception",
                extra={
                    "service": service_name,
                    "event": "http_request_failed",
                    "method": request.method,
                    "path": request.url.path,
                    "duration_ms": duration_ms,
                },
            )
            raise
        finally:
            request_id_var.reset(token)
