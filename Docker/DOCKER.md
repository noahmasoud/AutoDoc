# AutoDoc Docker Configuration

This document describes the Docker setup for the AutoDoc project, including production-grade containerization, CI/CD integration, and development workflows.

## 🐳 Docker Images

The project includes multiple Docker images optimized for different use cases:

### Multi-Stage Build

- **`builder`** - Build stage for compiling dependencies
- **`production`** - Minimal runtime image for production
- **`development`** - Full development environment with tools
- **`ci`** - Optimized for CI/CD pipelines

### Image Tags

- `autodoc:latest` - Production image
- `autodoc:dev` - Development image
- `autodoc:ci` - CI image
- `autodoc:prod` - Production image (explicit)

## 🚀 Quick Start

### Development Environment

```bash
# Start development environment
docker-compose up autodoc-dev

# Start with all services
docker-compose --profile dev-tools up

# Run tests
docker-compose run --rm autodoc-dev ./scripts/ci-test.sh

# Run linting
docker-compose run --rm autodoc-dev ./scripts/ci-lint.sh
```

### Production Environment

```bash
# Build production image
docker build --target production -t autodoc:prod .

# Run production container
docker run -d \
  --name autodoc-prod \
  -p 8000:8000 \
  -e DATABASE_URL=postgresql://user:pass@host:5432/db \
  autodoc:prod
```

### CI Environment

```bash
# Build CI image
docker build --target ci -t autodoc:ci .

# Run CI pipeline
docker run --rm autodoc:ci

# Run specific CI commands
docker run --rm autodoc:ci ./scripts/ci-test.sh
docker run --rm autodoc:ci ./scripts/ci-lint.sh
```

## 📁 Docker Files

### Core Files

- **`Dockerfile`** - Multi-stage Docker build configuration
- **`.dockerignore`** - Excludes unnecessary files from build context
- **`docker-compose.yml`** - Service orchestration
- **`docker-compose.override.yml`** - Local development overrides

### Scripts

- **`scripts/entrypoint.sh`** - POSIX-compatible entrypoint script
- **`scripts/init-db.sql`** - Database initialization
- **`scripts/redis.conf`** - Redis configuration

### Configuration

- **`.env.example`** - Environment variable template
- **`DOCKER.md`** - This documentation

## 🔧 Configuration

### Environment Variables

Key environment variables for container configuration:

```bash
# Application
ENVIRONMENT=production
LOG_LEVEL=INFO
PYTHONPATH=/app

# Database
DATABASE_URL=postgresql://autodoc:autodoc@postgres:5432/autodoc_prod

# Redis
REDIS_URL=redis://redis:6379/1

# Security
SECRET_KEY=your-secret-key
```

### Volume Mounts

- `/app/logs` - Application logs
- `/app/data` - Persistent data
- `/app/temp` - Temporary files

### Ports

- `8000` - Application HTTP server
- `5432` - PostgreSQL database
- `6379` - Redis cache

## 🏗️ Build Process

### Multi-Stage Build Benefits

1. **Security** - Minimal attack surface in production
2. **Size** - Smaller production images
3. **Speed** - Faster builds with layer caching
4. **Flexibility** - Different targets for different needs

### Build Arguments

```bash
docker build \
  --build-arg BUILD_DATE="$(date -u +'%Y-%m-%dT%H:%M:%SZ')" \
  --build-arg VCS_REF="$(git rev-parse --short HEAD)" \
  --build-arg VERSION="0.1.0" \
  --target production \
  -t autodoc:prod .
```

## 🔒 Security Features

### Non-Root User

All containers run as non-root user (`autodoc:autodoc`):

```dockerfile
RUN groupadd --gid 1000 autodoc && \
    useradd --uid 1000 --gid autodoc --shell /bin/bash --create-home autodoc
```

### Minimal Base Image

Uses `python:3.11-slim` for minimal attack surface.

### Health Checks

Built-in health checks for all services:

```dockerfile
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1
```

## 🚦 Entrypoint Script

The POSIX-compatible entrypoint script provides:

### Commands

- `test` - Run test suites
- `lint` - Run linting checks
- `ci` - Full CI pipeline
- `server` - Start application server
- `cli` - Run CLI commands
- `worker` - Start background worker
- `health` - Health check
- `shell` - Interactive shell

### Usage

```bash
# Run tests
docker run --rm autodoc:ci /entrypoint.sh test unit 60

# Run CI pipeline
docker run --rm autodoc:ci /entrypoint.sh ci

# Start server
docker run --rm autodoc:prod /entrypoint.sh server

# Run CLI command
docker run --rm autodoc:prod /entrypoint.sh cli analyze --file /path/to/file.py

# Interactive shell
docker run --rm -it autodoc:dev /entrypoint.sh shell bash
```

## 🔄 CI/CD Integration

### GitHub Actions

```yaml
name: CI
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Build CI image
        run: docker build --target ci -t autodoc:ci .
      - name: Run tests
        run: docker run --rm autodoc:ci
```

### GitLab CI

```yaml
test:
  stage: test
  image: docker:latest
  services:
    - docker:dind
  script:
    - docker build --target ci -t autodoc:ci .
    - docker run --rm autodoc:ci
```

### Jenkins

```groovy
pipeline {
    agent any
    stages {
        stage('Build') {
            steps {
                sh 'docker build --target ci -t autodoc:ci .'
            }
        }
        stage('Test') {
            steps {
                sh 'docker run --rm autodoc:ci'
            }
        }
    }
}
```

## 📊 Monitoring

### Health Checks

All services include health checks:

```yaml
healthcheck:
  test: ["CMD", "/entrypoint.sh", "health"]
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 40s
```

### Logging

Centralized logging with structured output:

```bash
# View logs
docker-compose logs -f autodoc-dev

# Follow specific service
docker-compose logs -f postgres
```

### Metrics

Optional Prometheus and Grafana setup:

```bash
# Start monitoring stack
docker-compose --profile monitoring up
```

## 🛠️ Development Workflow

### Local Development

```bash
# Start development environment
docker-compose up -d

# Run tests
docker-compose exec autodoc-dev pytest

# Run linting
docker-compose exec autodoc-dev ruff check .

# Access database
docker-compose exec postgres psql -U autodoc -d autodoc_dev
```

### Debugging

```bash
# Attach to running container
docker-compose exec autodoc-dev bash

# View container logs
docker-compose logs autodoc-dev

# Inspect container
docker-compose exec autodoc-dev /entrypoint.sh shell
```

## 📦 Production Deployment

### Docker Swarm

```bash
# Initialize swarm
docker swarm init

# Deploy stack
docker stack deploy -c docker-compose.yml autodoc
```

### Kubernetes

```bash
# Generate Kubernetes manifests
docker-compose -f docker-compose.yml config > k8s-config.yaml

# Apply to cluster
kubectl apply -f k8s-config.yaml
```

### Environment-Specific Configs

```bash
# Production
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up

# Staging
docker-compose -f docker-compose.yml -f docker-compose.staging.yml up
```

## 🔍 Troubleshooting

### Common Issues

1. **Build Failures**
   ```bash
   # Clear build cache
   docker builder prune
   
   # Rebuild without cache
   docker build --no-cache --target production -t autodoc:prod .
   ```

2. **Permission Issues**
   ```bash
   # Fix ownership
   sudo chown -R $(id -u):$(id -g) .
   ```

3. **Network Issues**
   ```bash
   # Recreate networks
   docker-compose down
   docker network prune
   docker-compose up
   ```

### Debug Commands

```bash
# Inspect image layers
docker history autodoc:prod

# Check container processes
docker-compose exec autodoc-dev ps aux

# View environment variables
docker-compose exec autodoc-dev env

# Test connectivity
docker-compose exec autodoc-dev curl -f http://postgres:5432
```

## 📚 Best Practices

1. **Use specific tags** instead of `latest`
2. **Scan images** for vulnerabilities
3. **Limit resources** in production
4. **Use secrets** for sensitive data
5. **Monitor logs** and metrics
6. **Keep base images** updated
7. **Use multi-stage builds** for optimization
8. **Test locally** before deployment

## 🔗 Related Documentation

- [Docker Best Practices](https://docs.docker.com/develop/dev-best-practices/)
- [Docker Security](https://docs.docker.com/engine/security/)
- [Compose File Reference](https://docs.docker.com/compose/compose-file/)
- [Multi-stage Builds](https://docs.docker.com/develop/dev-best-practices/dockerfile_best-practices/#use-multi-stage-builds)
