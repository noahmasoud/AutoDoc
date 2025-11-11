# AutoDoc Production Dockerfile
# Multi-stage build for optimized production image
# Based on Python 3.11-slim for security and size optimization

# =============================================================================
# Build Stage - Install dependencies and build the application
# =============================================================================
FROM python:3.11-slim as builder

# Set build arguments
ARG BUILDPLATFORM
ARG TARGETPLATFORM
ARG BUILD_DATE
ARG VCS_REF
ARG VERSION=0.1.0

# Add build metadata labels
LABEL org.opencontainers.image.title="AutoDoc" \
      org.opencontainers.image.description="Automated Documentation Generation and Management System" \
      org.opencontainers.image.version="${VERSION}" \
      org.opencontainers.image.created="${BUILD_DATE}" \
      org.opencontainers.image.revision="${VCS_REF}" \
      org.opencontainers.image.vendor="AutoDoc Team" \
      org.opencontainers.image.licenses="MIT" \
      org.opencontainers.image.source="https://github.com/autodoc-team/autodoc" \
      org.opencontainers.image.documentation="https://autodoc.readthedocs.io" \
      maintainer="AutoDoc Team <team@autodoc.dev>"

# Set environment variables for build
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_DEFAULT_TIMEOUT=100 \
    PYTHONPATH=/app

# Install system dependencies required for building Python packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    g++ \
    libffi-dev \
    libssl-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user for security
RUN groupadd --gid 1000 autodoc && \
    useradd --uid 1000 --gid autodoc --shell /bin/bash --create-home autodoc

# Set working directory
WORKDIR /app

# Copy dependency files and code first for better layer caching
COPY pyproject.toml ./
COPY . .

# Install Python dependencies
RUN pip install --upgrade pip setuptools wheel && \
    pip install --no-deps -e .

# =============================================================================
# Production Stage - Minimal runtime image
# =============================================================================
FROM python:3.11-slim as production

# Set production environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PATH="/home/autodoc/.local/bin:$PATH" \
    PYTHONPATH=/app

# Install only runtime system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create non-root user for security
RUN groupadd --gid 1000 autodoc && \
    useradd --uid 1000 --gid autodoc --shell /bin/bash --create-home autodoc

# Set working directory
WORKDIR /app

# Copy Python dependencies from builder stage
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY --chown=autodoc:autodoc . .

# Copy entrypoint script
COPY --chown=autodoc:autodoc scripts/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Create necessary directories with proper permissions
RUN mkdir -p /app/logs /app/data /app/temp && \
    chown -R autodoc:autodoc /app /entrypoint.sh

# Switch to non-root user
USER autodoc

# Expose port (adjust as needed for your application)
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Set entrypoint
ENTRYPOINT ["/entrypoint.sh"]

# Default command
CMD ["autodoc", "--help"]

# =============================================================================
# Development Stage - For development and testing
# =============================================================================
FROM python:3.11-slim as development

# Set development environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PATH="/home/autodoc/.local/bin:$PATH" \
    PYTHONPATH=/app

# Install system dependencies for development
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    g++ \
    libffi-dev \
    libssl-dev \
    pkg-config \
    git \
    curl \
    ca-certificates \
    vim \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create non-root user for security
RUN groupadd --gid 1000 autodoc && \
    useradd --uid 1000 --gid autodoc --shell /bin/bash --create-home autodoc

# Set working directory
WORKDIR /app

# Copy application code first (needed for version detection)
COPY --chown=autodoc:autodoc . .

# Install Python dependencies including development tools
RUN pip install --upgrade pip setuptools wheel && \
    pip install -e ".[dev,test,lint,docs]"

# Make entrypoint available at root for compose health checks
RUN install -m 755 /app/scripts/entrypoint.sh /entrypoint.sh

# Create necessary directories with proper permissions
RUN mkdir -p /app/logs /app/data /app/temp /app/htmlcov && \
    chown -R autodoc:autodoc /app

# Switch to non-root user
USER autodoc

# Expose port
EXPOSE 8000

# Set entrypoint
ENTRYPOINT ["/entrypoint.sh"]

# Default command for development
CMD ["autodoc", "--help"]

# =============================================================================
# CI Stage - For CI/CD pipelines
# =============================================================================
FROM python:3.11-slim as ci

# Set CI environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PATH="/home/autodoc/.local/bin:$PATH" \
    PYTHONPATH=/app \
    CI=true

# Install system dependencies for CI
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    g++ \
    libffi-dev \
    libssl-dev \
    pkg-config \
    git \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create non-root user for security
RUN groupadd --gid 1000 autodoc && \
    useradd --uid 1000 --gid autodoc --shell /bin/bash --create-home autodoc

# Set working directory
WORKDIR /app

# Copy application code first (needed for version detection)
COPY --chown=autodoc:autodoc . .

# Install Python dependencies including test and lint tools
RUN pip install --upgrade pip setuptools wheel && \
    pip install -e ".[dev,test,lint]"

# Make entrypoint available at root and ensure CI scripts are executable
RUN install -m 755 /app/scripts/entrypoint.sh /entrypoint.sh && \
    chmod +x scripts/ci-test.sh scripts/ci-lint.sh scripts/run-tests.sh

# Create necessary directories with proper permissions
RUN mkdir -p /app/logs /app/data /app/temp /app/htmlcov && \
    chown -R autodoc:autodoc /app

# Switch to non-root user
USER autodoc

# Set entrypoint
ENTRYPOINT ["/entrypoint.sh"]

# Default command for CI
CMD ["./scripts/ci-test.sh"]
