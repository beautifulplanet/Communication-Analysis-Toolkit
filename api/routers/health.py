"""Health check endpoint with system resource metrics."""
from __future__ import annotations

from fastapi import APIRouter
import psutil

from api.schemas import HealthResponse

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Health check endpoint with CPU and memory usage."""
    return HealthResponse(
        status="ok",
        cpu=psutil.cpu_percent(interval=None),
        memory=psutil.virtual_memory().percent,
    )
