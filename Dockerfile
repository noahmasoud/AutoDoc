# =============================================================================
# AutoDoc CI/CD Runner Docker Image
# Simple 2-stage build for CI pipeline execution
# Runs autodoc.sh script in GitHub Actions / GitLab CI
# =============================================================================

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

LABEL maintainer="Noah Masoud - SM Group 6"
LABEL description="AutoDoc CI/CD Runner"
LABEL version="0.1.0-sprint0"
LABEL course="CS4398"
LABEL purpose="CI/CD pipeline execution (SCRUM-7)"

WORKDIR /app

# Copy Python packages from builder
COPY --from=builder /root/.local /root/.local

# Add Python packages to PATH
ENV PATH=/root/.local/bin:$PATH

# Install minimal runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
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