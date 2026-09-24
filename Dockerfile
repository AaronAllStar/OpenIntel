# ==============================================================================
# OpenIntel - Unified Single Container Multi-Stage Dockerfile
# Combines React/Vite Frontend and FastAPI/Python OSINT Backend
# ==============================================================================

# --- Stage 1: Build Frontend ---
FROM node:20-alpine AS frontend-builder
WORKDIR /build

# Install dependencies
COPY src/ui/package.json src/ui/package-lock.json* ./
RUN npm ci

# Copy frontend source code and build production assets
COPY src/ui/ ./
RUN npm run build

# --- Stage 2: Backend Runtime ---
FROM python:3.12-slim AS runtime
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    git \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install uv for fast dependency management
RUN pip install --no-cache-dir uv

# Copy package definitions and source code
COPY pyproject.toml README.md ./
COPY src/ /app/src/

# Install Python dependencies globally in the container
RUN uv pip install --system --no-cache -e .

# Copy built frontend static assets from Stage 1 into the location expected by FastAPI
COPY --from=frontend-builder /build/dist /app/src/ui/dist

# Set runtime environment
ENV PYTHONUNBUFFERED=1 \
    OPENINTEL_HOST=0.0.0.0 \
    OPENINTEL_PORT=8000

# Expose unified application port
EXPOSE 8000

# Healthcheck
HEALTHCHECK --interval=15s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://127.0.0.1:8000/api/v1/health || exit 1

# Launch OpenIntel unified server
CMD ["uvicorn", "src.app.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
