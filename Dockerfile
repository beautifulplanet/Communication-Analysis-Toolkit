# =============================================================================
# Communication Analysis Toolkit — Production Container
# =============================================================================
# Multi-stage build for a small, secure image.
#
# BUILD:  docker build -t comms-toolkit .
# RUN:    docker run --rm -v ./cases:/app/cases -v ./output:/app/output \
#             comms-toolkit --config cases/my_case/config.json --yes
# =============================================================================

# ---------------------------------------------------------------------------
# Stage 1 — Builder (install deps, build wheel)
# ---------------------------------------------------------------------------
FROM python:3.12-slim AS builder

WORKDIR /build

# Install build dependencies for pysqlcipher3
RUN apt-get update && apt-get install -y \
    build-essential \
    libsqlcipher-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy only dependency manifests first (layer caching)
COPY pyproject.toml README.md ./
COPY engine/ engine/
COPY active/ active/

# Install the package into a virtual-env so we can copy it cleanly
RUN python -m venv /opt/venv \
    && /opt/venv/bin/pip install --no-cache-dir --upgrade pip \
    && /opt/venv/bin/pip install --no-cache-dir .

# ---------------------------------------------------------------------------
# Stage 2 — Runtime (no build tools, no pip cache)
# ---------------------------------------------------------------------------
FROM python:3.12-slim AS runtime

# Install runtime dependencies for sqlcipher
RUN apt-get update && apt-get install -y \
    libsqlcipher0 \
    && rm -rf /var/lib/apt/lists/*

# Security: run as non-root
RUN groupadd --gid 1000 analyst \
    && useradd --uid 1000 --gid analyst --shell /bin/bash --create-home analyst

WORKDIR /app

# Copy the pre-built virtual-env from builder
COPY --from=builder /opt/venv /opt/venv

# Copy application source
COPY engine/ engine/
COPY active/ active/
COPY cases/ cases/

# Ensure output directory exists
RUN mkdir -p /app/output && chown -R analyst:analyst /app

# Use the venv Python
ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

USER analyst

# Health check — verify the CLI entry-point loads
HEALTHCHECK --interval=60s --timeout=5s --retries=3 \
    CMD comms-analyze --help > /dev/null 2>&1 || exit 1

ENTRYPOINT ["comms-analyze"]
CMD ["--help"]
