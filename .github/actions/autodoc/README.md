# AutoDoc GitHub Actions Composite Action

This composite action provides a reusable way to run AutoDoc analysis in GitHub Actions workflows.

## Usage

```yaml
jobs:
  autodoc-analysis:
    runs-on: ubuntu-latest
    steps:
      - name: Run AutoDoc
        uses: ./.github/actions/autodoc
        with:
          version: '0.1.0'  # Container version tag (semver)
          commit: ${{ github.sha }}
          repo: ${{ github.repository }}
          branch: ${{ github.ref_name }}
```

## Inputs

| Input | Description | Required | Default |
|-------|-------------|----------|---------|
| `version` | Container image version/tag (semver format) | No | `latest` |
| `registry` | Container registry (e.g., ghcr.io, docker.io) | No | `ghcr.io` |
| `image-name` | Container image name (without registry) | No | `autodoc-ci` |
| `commit` | Git commit SHA to analyze | Yes | - |
| `repo` | Repository name (e.g., owner/repo) | Yes | - |
| `branch` | Branch name | No | `main` |
| `pr-id` | Pull request ID (optional) | No | - |
| `dry-run` | Generate patches without updating Confluence | No | `false` |
| `verbose` | Enable verbose logging | No | `false` |
| `workspace-path` | Path to workspace directory | No | `${{ github.workspace }}` |
| `artifacts-path` | Path to artifacts directory | No | `artifacts` |

## Outputs

| Output | Description |
|--------|-------------|
| `change-report-path` | Path to generated change_report.json |
| `run-id` | AutoDoc run ID (if backend available) |
| `status` | Execution status (success/failure) |

## Requirements

- Docker must be available in the runner
- The container image must be published to the specified registry
- Git history must be available (fetch-depth: 2 minimum)

## Container Image

The action uses a containerized AutoDoc runner. Build and publish the container using the `build-and-publish.yml` workflow or manually:

```bash
docker build \
  --build-arg VERSION="0.1.0" \
  --build-arg BUILD_DATE="$(date -u +'%Y-%m-%dT%H:%M:%SZ')" \
  --build-arg VCS_REF="$(git rev-parse HEAD)" \
  --tag ghcr.io/owner/autodoc-ci:0.1.0 \
  .
```

## Example

See `.github/workflows/autodoc-example.yml` for a complete example.

