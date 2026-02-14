from __future__ import annotations

import uuid
from collections.abc import Awaitable
from typing import Callable

import structlog
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

log = structlog.get_logger()


class RequestIdMiddleware(BaseHTTPMiddleware):
    """Middleware to add a unique request ID to every request.

    - Generates a UUID4.
    - Binds it to structlog context (so all logs include it).
    - Adds 'X-Request-ID' header to the response.
    """

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        request_id = str(uuid.uuid4())

        # Clear context vars at start of request to avoid leakage from previous requests
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(request_id=request_id)

        response = await call_next(request)

        response.headers["X-Request-ID"] = request_id
        return response
