from __future__ import annotations

import structlog
from fastapi import Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from starlette.exceptions import HTTPException as StarletteHTTPException

from api.exceptions import AgentError

log = structlog.get_logger()


class ErrorDetail(BaseModel):
    code: str
    message: str
    request_id: str | None = None


class ErrorResponse(BaseModel):
    error: ErrorDetail


async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    """Handle standard HTTP exceptions."""
    ctx = structlog.contextvars.get_contextvars()
    request_id = ctx.get("request_id")

    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error=ErrorDetail(
                code=str(exc.status_code),  # e.g. "404"
                message=exc.detail,
                request_id=request_id,
            )
        ).model_dump(),
    )


async def agent_exception_handler(request: Request, exc: AgentError) -> JSONResponse:
    """Handle internal agent logic errors as 500s (or 400s if likely user error)."""
    ctx = structlog.contextvars.get_contextvars()
    request_id = ctx.get("request_id")

    log.error("agent_error_caught", error=str(exc), request_id=request_id)

    # AgentErrors are usually recoverable but unexpected API-level logic failures
    # define status code mapping here if needed. Default to 500 for safety.
    status_code = 500

    return JSONResponse(
        status_code=status_code,
        content=ErrorResponse(
            error=ErrorDetail(
                code="AGENT_ERROR",
                message=exc.message,
                request_id=request_id,
            )
        ).model_dump(),
    )


async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle unexpected server errors."""
    ctx = structlog.contextvars.get_contextvars()
    request_id = ctx.get("request_id")

    log.error("unhandled_exception", exc_info=exc, request_id=request_id)

    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error=ErrorDetail(
                code="INTERNAL_SERVER_ERROR",
                message="An unexpected error occurred.",
                request_id=request_id,
            )
        ).model_dump(),
    )
