# AutoDoc Production Dockerfile
# Multi-stage build for optimized production image
# Based on Python 3.11-slim for security and size optimization
#
# Stage A: Install Python dependencies
# Stage B: Install Node.js dependencies for TypeScript analyzer
# Final stages: Combine both for runtime

# =============================================================================
# Stage A: Python Builder - Install Python dependencies
# =============================================================================
FROM python:3.11-slim as python-builder

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
# Stage B: Node.js Builder - Install Node dependencies for TS analyzer
# =============================================================================
FROM node:20-slim as node-builder

# Set working directory
WORKDIR /app

# Copy package files for dependency installation
COPY package.json package-lock.json* ./

# Install Node.js dependencies for TypeScript analyzer
# Only install production dependencies needed for the TS parser script
RUN npm ci --only=production --ignore-scripts || \
    (npm install --only=production --ignore-scripts && \
     echo "Note: package-lock.json may be missing, using npm install")

# Copy the TypeScript parser script (needed for verification)
COPY scripts/parse-typescript.js ./scripts/

# Verify Node.js dependencies are installed and parser can load
RUN test -d node_modules/@typescript-eslint && \
    node -e "require('@typescript-eslint/typescript-estree'); console.log('Parser module loads successfully')" && \
    echo "TypeScript parser dependencies installed successfully"

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
    PYTHONPATH=/app \
    NODE_PATH=/app/node_modules

# Install runtime system dependencies including Node.js for TS analyzer
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Install Node.js 20.x (required for TypeScript analyzer)
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && \
    apt-get install -y --no-install-recommends nodejs && \
    rm -rf /var/lib/apt/lists/* && \
    apt-get clean

# Create non-root user for security
RUN groupadd --gid 1000 autodoc && \
    useradd --uid 1000 --gid autodoc --shell /bin/bash --create-home autodoc

# Set working directory
WORKDIR /app

# Copy Python dependencies from python-builder stage
COPY --from=python-builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=python-builder /usr/local/bin /usr/local/bin

# Copy Node.js dependencies from node-builder stage
COPY --from=node-builder /app/node_modules ./node_modules
COPY --from=node-builder /app/scripts/parse-typescript.js ./scripts/parse-typescript.js

# Copy application code
COPY --chown=autodoc:autodoc . .

# Copy entrypoint script
COPY --chown=autodoc:autodoc scripts/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Verify Node.js and TS parser are available
RUN node --version && \
    npm --version && \
    test -f scripts/parse-typescript.js && \
    test -d node_modules/@typescript-eslint || echo "Warning: TS parser deps may be missing"

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
    PYTHONPATH=/app \
    NODE_PATH=/app/node_modules

# Install system dependencies for development including Node.js
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

# Install Node.js 20.x (required for TypeScript analyzer)
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && \
    apt-get install -y --no-install-recommends nodejs && \
    rm -rf /var/lib/apt/lists/* && \
    apt-get clean

# Create non-root user for security
RUN groupadd --gid 1000 autodoc && \
    useradd --uid 1000 --gid autodoc --shell /bin/bash --create-home autodoc

# Set working directory
WORKDIR /app

# Copy Node.js dependencies from node-builder stage
COPY --from=node-builder /app/node_modules ./node_modules
COPY --from=node-builder /app/scripts/parse-typescript.js ./scripts/parse-typescript.js

# Copy application code first (needed for version detection)
COPY --chown=autodoc:autodoc . .

# Install Python dependencies including development tools
RUN pip install --upgrade pip setuptools wheel && \
    pip install -e ".[dev,test,lint,docs]"

# Install Node.js dependencies if package.json exists (for development)
RUN if [ -f package.json ]; then \
    npm ci --only=production --ignore-scripts || \
    npm install --only=production --ignore-scripts; \
    fi

# Verify Node.js and TS parser are available
RUN node --version && \
    npm --version && \
    test -f scripts/parse-typescript.js && \
    echo "Node.js and TS parser ready"

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
    NODE_PATH=/app/node_modules \
    CI=true

# Install system dependencies for CI including Node.js
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

# Install Node.js 20.x (required for TypeScript analyzer)
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && \
    apt-get install -y --no-install-recommends nodejs && \
    rm -rf /var/lib/apt/lists/* && \
    apt-get clean

# Create non-root user for security
RUN groupadd --gid 1000 autodoc && \
    useradd --uid 1000 --gid autodoc --shell /bin/bash --create-home autodoc

# Set working directory
WORKDIR /app

# Copy Node.js dependencies from node-builder stage
COPY --from=node-builder /app/node_modules ./node_modules
COPY --from=node-builder /app/scripts/parse-typescript.js ./scripts/parse-typescript.js

# Copy application code first (needed for version detection)
COPY --chown=autodoc:autodoc . .

# Install Python dependencies including test and lint tools
RUN pip install --upgrade pip setuptools wheel && \
    pip install -e ".[dev,test,lint]"

# Verify Node.js and TS parser are available
RUN node --version && \
    npm --version && \
    test -f scripts/parse-typescript.js && \
    echo "Node.js and TS parser ready for CI"

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
