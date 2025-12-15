# How to Adopt AutoDoc

This guide helps you integrate AutoDoc into your CI/CD pipeline.

## Overview

AutoDoc analyzes code changes and automatically updates Confluence documentation. It integrates into your existing CI/CD workflow with minimal configuration.

## Prerequisites

- CI/CD pipeline (GitHub Actions or GitLab CI)
- Confluence Cloud account with API token
- Docker (for container-based execution)

## Quick Start

### GitHub Actions

Add this step to your `.github/workflows/ci.yml`:

```yaml
- name: Run AutoDoc
  uses: docker://autodoc:1.2.3
  with:
    commit: ${{ github.sha }}
    repo: ${{ github.repository }}
    branch: ${{ github.ref_name }}
  env:
    CONFLUENCE_URL: ${{ secrets.CONFLUENCE_URL }}
    CONFLUENCE_TOKEN: ${{ secrets.CONFLUENCE_TOKEN }}
    CONFLUENCE_SPACE_KEY: ${{ secrets.CONFLUENCE_SPACE_KEY }}
```

**⚠️ IMPORTANT: Always pin a specific version** (e.g., `autodoc:1.2.3`). Never use `latest` or `autodoc:latest` in production.

### GitLab CI

Add this job to your `.gitlab-ci.yml`:

```yaml
autodoc:
  stage: test
  image: autodoc:1.2.3
  script:
    - autodoc.sh --commit $CI_COMMIT_SHA --repo $CI_PROJECT_PATH --branch $CI_COMMIT_REF_NAME
  artifacts:
    paths:
      - artifacts/
    expire_in: 30 days
  only:
    - merge_requests
    - main
  variables:
    CONFLUENCE_URL: ${CONFLUENCE_URL}
    CONFLUENCE_TOKEN: ${CONFLUENCE_TOKEN}
    CONFLUENCE_SPACE_KEY: ${CONFLUENCE_SPACE_KEY}
```

**⚠️ IMPORTANT: Always pin a specific version** (e.g., `autodoc:1.2.3`). Never use `latest` in production.

## Required Secrets

Configure these secrets in your CI/CD platform:

| Secret Name | Description | Required |
|------------|-------------|----------|
| `CONFLUENCE_URL` | Base URL of your Confluence instance (e.g., `https://yourcompany.atlassian.net`) | Yes |
| `CONFLUENCE_TOKEN` | Confluence API token with page edit permissions | Yes |
| `CONFLUENCE_SPACE_KEY` | Confluence space key where documentation lives | Yes |

### Creating a Confluence API Token

1. Go to: https://id.atlassian.com/manage-profile/security/api-tokens
2. Click "Create API token"
3. Give it a label (e.g., "AutoDoc CI")
4. Copy the token immediately (you won't see it again)
5. Add it to your CI/CD secrets

**⚠️ CRITICAL SECURITY NOTE**: Secrets are **never** written to disk or artifacts. They are only passed via environment variables and handled securely by the CI/CD platform. AutoDoc uses them in-memory only and never logs or persists token values.

## Version Pinning

**Always pin AutoDoc to a specific version tag:**

✅ **Correct:**
```yaml
image: autodoc:1.2.3
```

❌ **Wrong:**
```yaml
image: autodoc:latest  # NEVER use latest
image: autodoc         # Ambiguous, defaults to latest
```

### Why Version Pinning Matters

- **Reproducibility**: Ensures consistent behavior across runs
- **Stability**: Prevents unexpected changes from breaking your pipeline
- **Debugging**: Makes it easier to track down issues to specific versions
- **Security**: Allows you to review changes before updating

### Updating Versions

When updating to a new version:

1. Review the [changelog](CHANGELOG.md)
2. Test in a development branch first
3. Update the version tag in your CI/CD config
4. Monitor the first few runs for issues

## Compatibility Matrix

| Component | Minimum Version | Notes |
|-----------|----------------|-------|
| **Runner OS** | Linux (Ubuntu 20.04+) | Required for Docker execution |
| **Docker** | 20.10+ | Required for container execution |
| **Git** | 2.25+ | Required for diff analysis |
| **GitHub Actions** | ubuntu-latest | Tested on ubuntu-20.04, ubuntu-22.04 |
| **GitLab CI** | 13.0+ | Tested on GitLab.com and self-hosted |

### Required Permissions

- **Git**: Read access to repository (clone, fetch, diff)
- **Filesystem**: Write access to `artifacts/` directory
- **Network**: HTTPS access to Confluence API endpoint

### Runner Requirements

- **CPU**: 2+ cores recommended
- **Memory**: 4GB+ RAM recommended
- **Disk**: 1GB+ free space for temporary files
- **Network**: Outbound HTTPS to Confluence

## Configuration

### Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `CONFLUENCE_URL` | Confluence base URL | - | Yes |
| `CONFLUENCE_TOKEN` | API token | - | Yes |
| `CONFLUENCE_SPACE_KEY` | Space key | - | Yes |
| `AUTODOC_DRY_RUN` | Run without updating Confluence | `false` | No |
| `AUTODOC_WORKSPACE` | Workspace directory | `.` | No |

### Command Line Options

```bash
autodoc.sh --commit <sha> --repo <repo> [OPTIONS]

Options:
  --commit SHA         Commit SHA to analyze (required)
  --repo REPO          Repository identifier (required)
  --branch BRANCH      Branch name (default: detect from git)
  --pr-id ID           Pull/Merge request ID (optional)
  --dry-run            Generate patches without applying (default: false)
  --workspace PATH     Workspace directory (default: current directory)
  --help               Show help message
```

## Artifacts

AutoDoc produces the following artifacts (saved to `artifacts/`):

- **`change_report.json`**: Machine-readable report of detected changes
- **`patches.json`**: Generated Confluence page patches (if rules match)

Artifacts are automatically uploaded by most CI/CD platforms when placed in the `artifacts/` directory.

## Troubleshooting

### Common Issues

**Error: "Confluence token invalid"**
- Verify token is correctly set in secrets
- Check token has not expired
- Ensure token has page edit permissions

**Error: "No matching rules found"**
- This is normal if no code changes match configured rules
- Run completes successfully with no patches

**Error: "Docker image not found"**
- Verify you're using the correct image name and version tag
- Check image is available in your container registry

**Performance: Job takes longer than expected**
- Per SRS NFR-1: Analyzer runtime ≤5 minutes for ≤500 LOC change set on ≤10k LOC repo
- If consistently slower, check runner resources (CPU, memory)

## Getting Help

- **Documentation**: See [README.md](../README.md) and other docs in `docs/`
- **Issues**: Report issues on the project repository
- **Security**: Report security vulnerabilities via private channels

## Next Steps

1. Configure Confluence connection in the AutoDoc UI
2. Create mapping rules to connect code areas to Confluence pages
3. Create templates for patch generation
4. Test with `--dry-run` flag first
5. Enable in your main branch workflow

---

**Remember**: Always pin versions, never use `latest`, and keep your secrets secure!

