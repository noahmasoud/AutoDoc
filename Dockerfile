# =============================================================================
# AutoDoc CI/CD Runner Docker Image
# Simple 2-stage build for CI pipeline execution
# Runs autodoc.sh script in GitHub Actions / GitLab CI
# Supports semver versioning for container registry publishing
# =============================================================================

# Build arguments for versioning
ARG VERSION=0.1.0
ARG BUILD_DATE
ARG VCS_REF
ARG REGISTRY=ghcr.io

# -----------------------------------------------------------------------------
# Stage 1: Builder - Install dependencies
# -----------------------------------------------------------------------------
FROM python:3.11-slim AS builder

LABEL maintainer="Noah Masoud - SM Group 6"
LABEL description="AutoDoc CI/CD Runner - Builder Stage"
LABEL course="CS4398"

WORKDIR /build

# Install minimal build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# -----------------------------------------------------------------------------
# Stage 2: Runtime - Minimal CI runner image
# -----------------------------------------------------------------------------
FROM python:3.11-slim

# Build arguments
ARG VERSION=0.1.0
ARG BUILD_DATE
ARG VCS_REF
ARG REGISTRY=ghcr.io

# Labels with versioning and OCI metadata
LABEL maintainer="Noah Masoud - SM Group 6"
LABEL description="AutoDoc CI/CD Runner"
LABEL version="${VERSION}"
LABEL course="CS4398"
LABEL purpose="CI/CD pipeline execution"
LABEL org.opencontainers.image.title="AutoDoc CI/CD Runner"
LABEL org.opencontainers.image.description="AutoDoc CI/CD Runner for GitHub Actions and GitLab CI"
LABEL org.opencontainers.image.version="${VERSION}"
LABEL org.opencontainers.image.created="${BUILD_DATE}"
LABEL org.opencontainers.image.revision="${VCS_REF}"
LABEL org.opencontainers.image.source="https://github.com/autodoc-team/autodoc"

WORKDIR /app

# Copy Python packages from builder
COPY --from=builder /root/.local /root/.local

# Add Python packages to PATH
ENV PATH=/root/.local/bin:$PATH

# Install minimal runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    curl \
    jq \
    && rm -rf /var/lib/apt/lists/*

# Copy only CI-related files
COPY autodoc.sh .
COPY requirements.txt .

# Make script executable
RUN chmod +x autodoc.sh

# Create non-root user for security (NFR-9)
RUN useradd -m -u 1000 autodoc && \
    chown -R autodoc:autodoc /app

# Switch to non-root user
USER autodoc

# Health check verifies script is functional
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD ./autodoc.sh --help > /dev/null 2>&1 || exit 1

# Set entrypoint to the CI script
ENTRYPOINT ["./autodoc.sh"]

# Default command shows help
CMD ["--help"]