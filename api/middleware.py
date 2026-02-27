from __future__ import annotations

import base64
import secrets
import uuid
from collections.abc import Awaitable
from typing import Callable

import structlog
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from api.config import get_settings

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


class BasicAuthMiddleware(BaseHTTPMiddleware):
    """Middleware to enforce Basic Auth on all requests."""

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        # Allow health check and docs without auth? (Optional)
        # Lock everything except health endpoint for monitoring
        if request.url.path == "/api/health":
            return await call_next(request)

        # Allow CORS preflight
        if request.method == "OPTIONS":
            return await call_next(request)

        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Basic "):
            return Response(status_code=401, headers={"WWW-Authenticate": "Basic"})

        try:
            encoded_creds = auth_header.split(" ")[1]
            decoded_creds = base64.b64decode(encoded_creds).decode("utf-8")
            username, password = decoded_creds.split(":", 1)
        except Exception:
             return Response(status_code=401, headers={"WWW-Authenticate": "Basic"})

        settings = get_settings()
        correct_username = settings.auth_username
        correct_password = settings.auth_password

        # Constant time comparison to prevent timing attacks
        if not (secrets.compare_digest(username, correct_username) and
                secrets.compare_digest(password, correct_password)):
             return Response(status_code=401, headers={"WWW-Authenticate": "Basic"})

        return await call_next(request)
