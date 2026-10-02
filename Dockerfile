# ==============================================================================
# OpenIntel - Production Multi-Stage Hardened Dockerfile
# Stage 1: Build React 18 + TailwindCSS Frontend (Bilingual EN/ES)
# Stage 2: Build Rust Native Performance Core (PyO3 + Maturin)
# Stage 3: Python 3.12 Runtime with Dropped Privileges
# ==============================================================================

# --- Stage 1: Build Frontend ---
FROM node:20-alpine AS frontend-builder
WORKDIR /build

COPY src/ui/package.json src/ui/package-lock.json* ./
RUN npm ci

COPY src/ui/ ./
RUN npm run build

# --- Stage 2: Build Rust Core Extension ---
FROM rust:1-slim AS rust-builder
WORKDIR /rust-build

# Install python and maturin
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 \
    python3-pip \
    python3-venv \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install --no-cache-dir --break-system-packages maturin

COPY Cargo.toml Cargo.lock ./
COPY crates/ crates/

RUN maturin build --release -m crates/openintel-core/Cargo.toml --out /rust-build/wheels

# --- Stage 3: Backend Runtime ---
FROM python:3.12-slim AS runtime
WORKDIR /app

# Install minimal system runtime libraries
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Install uv for high-speed package management
RUN pip install --no-cache-dir uv

# Copy and install the compiled Rust PyO3 wheel from Stage 2
COPY --from=rust-builder /rust-build/wheels /wheels
RUN uv pip install --system --no-cache /wheels/*.whl && rm -rf /wheels

# Copy Python package definition and source code
COPY pyproject.toml README.md ./
COPY src/ /app/src/

# Install Python dependencies globally
RUN uv pip install --system --no-cache -e .

# Copy built frontend static assets from Stage 1 into FastAPI's static directory
COPY --from=frontend-builder /build/dist /app/src/ui/dist

# Copy PostgreSQL schema file (using tracked example schema so builds succeed on clean clones)
COPY examples/openintel_schema_example.sql /app/openintel.sql

# Create unprivileged runtime user and data directories
RUN groupadd -g 10001 openintel && \
    useradd -u 10001 -g openintel -s /bin/bash -m openintel && \
    mkdir -p /app/data /app/data/exports && \
    chown -R openintel:openintel /app

# Set runtime environment
ENV PYTHONUNBUFFERED=1 \
    OPENINTEL_HOST=0.0.0.0 \
    OPENINTEL_PORT=8000

# Run container as unprivileged user
USER openintel:openintel

# Expose unified application port
EXPOSE 8000

# Container Healthcheck
HEALTHCHECK --interval=15s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://127.0.0.1:8000/api/v1/health || exit 1

# Launch OpenIntel unified server
CMD ["uvicorn", "src.app.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
