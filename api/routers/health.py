"""Health check endpoint with system resource metrics."""
from __future__ import annotations

import os

import psutil
from fastapi import APIRouter

from api.schemas import HealthResponse

router = APIRouter()

# Pre-warm psutil CPU measurement so subsequent calls are non-blocking
psutil.cpu_percent(interval=None)

# Cache the process object
_proc = psutil.Process(os.getpid())


def _get_cache_stats() -> tuple[int, int]:
    """Get current cache size and maxsize from the case data cache."""
    try:
        from api.dependencies import _case_data_cache
        return len(_case_data_cache), _case_data_cache.maxsize
    except (ImportError, AttributeError):
        return 0, 0


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Health check — fast, non-blocking."""
    cache_size, cache_maxsize = _get_cache_stats()

    return HealthResponse(
        status="ok",
        cpu=psutil.cpu_percent(interval=None),
        memory=psutil.virtual_memory().percent,
        memory_mb=round(_proc.memory_info().rss / 1024 / 1024, 1),
        disk_read_mb=0.0,  # Skipped on Windows — too slow for health check
        disk_write_mb=0.0,
        open_files=0,  # proc.open_files() is expensive on Windows
        cache_size=cache_size,
        cache_maxsize=cache_maxsize,
    )
