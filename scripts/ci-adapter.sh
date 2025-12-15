#!/bin/bash

############################################################
# AutoDoc CI Adapter Script
# Translates CI environment variables to CLI arguments
# Implements Section 3.1: CI Adapters
############################################################

set -e
set -u
set -o pipefail

SCRIPT_NAME="ci-adapter.sh"
SCRIPT_VERSION="1.0.0"

# Error handling
trap 'handle_error $? $LINENO' ERR

handle_error() {
    local exit_code=$1
    local line_number=$2
    
    echo ""
    echo "========================================"
    echo "✗ Error occurred!"
    echo "========================================"
    echo "Exit code: $exit_code"
    echo "Line: $line_number"
    echo ""
    echo "Please check the logs above for details."
    echo ""
    
    exit "$exit_code"
}

# Print header
echo "========================================"
echo "AutoDoc CI Adapter v${SCRIPT_VERSION}"
echo "========================================"

# Detect CI environment and extract variables
COMMIT_SHA=""
REPO_NAME=""
BRANCH_NAME="main"
PR_ID=""
DRY_RUN=false

# GitHub Actions
if [ -n "${GITHUB_ACTIONS:-}" ]; then
    echo "Detected: GitHub Actions"
    COMMIT_SHA="${GITHUB_SHA:-}"
    REPO_NAME="${GITHUB_REPOSITORY:-}"
    BRANCH_NAME="${GITHUB_REF#refs/heads/}"  # Remove refs/heads/ prefix
    # For PRs, GITHUB_REF is like refs/pull/123/merge
    if [[ "${GITHUB_REF:-}" =~ ^refs/pull/([0-9]+)/merge$ ]]; then
        PR_ID="${BASH_REMATCH[1]}"
        # Use the base branch for PRs
        BRANCH_NAME="${GITHUB_BASE_REF:-main}"
    fi
    # Check if dry-run mode is requested
    if [ "${INPUT_DRY_RUN:-false}" = "true" ]; then
        DRY_RUN=true
    fi
fi

# GitLab CI
if [ -n "${CI:-}" ] && [ -n "${GITLAB_CI:-}" ]; then
    echo "Detected: GitLab CI"
    COMMIT_SHA="${CI_COMMIT_SHA:-}"
    REPO_NAME="${CI_PROJECT_PATH:-}"
    BRANCH_NAME="${CI_COMMIT_REF_NAME:-main}"
    # For merge requests
    if [ -n "${CI_MERGE_REQUEST_IID:-}" ]; then
        PR_ID="${CI_MERGE_REQUEST_IID}"
        BRANCH_NAME="${CI_MERGE_REQUEST_TARGET_BRANCH_NAME:-main}"
    fi
    # Check if dry-run mode is requested
    if [ "${AUTODOC_DRY_RUN:-false}" = "true" ]; then
        DRY_RUN=true
    fi
fi

# Generic CI fallback (try common env vars)
if [ -z "$COMMIT_SHA" ] || [ -z "$REPO_NAME" ]; then
    echo "Detected: Generic CI environment"
    COMMIT_SHA="${COMMIT_SHA:-${CI_COMMIT:-${GIT_COMMIT:-}}}"
    REPO_NAME="${REPO_NAME:-${CI_REPO:-${REPO:-}}}"
    BRANCH_NAME="${BRANCH_NAME:-${CI_BRANCH:-${GIT_BRANCH:-${BRANCH:-main}}}}"
    PR_ID="${PR_ID:-${CI_PULL_REQUEST:-${PULL_REQUEST:-${PR_NUMBER:-}}}}"
    
    # Remove common branch prefixes
    BRANCH_NAME="${BRANCH_NAME#origin/}"
    BRANCH_NAME="${BRANCH_NAME#refs/heads/}"
fi

# Validate required variables
echo ""
echo "Validating CI environment variables..."

if [ -z "$COMMIT_SHA" ]; then
    echo "Error: Could not determine commit SHA from CI environment"
    echo "Available environment variables:"
    env | grep -iE "(commit|sha|git)" | sort || true
    exit 1
fi

if [ -z "$REPO_NAME" ]; then
    echo "Error: Could not determine repository name from CI environment"
    echo "Available environment variables:"
    env | grep -iE "(repo|repository|project)" | sort || true
    exit 1
fi

echo "  ✓ Commit SHA: $COMMIT_SHA"
echo "  ✓ Repository: $REPO_NAME"
echo "  ✓ Branch: $BRANCH_NAME"
if [ -n "$PR_ID" ]; then
    echo "  ✓ PR/MR ID: $PR_ID"
fi
if [ "$DRY_RUN" = "true" ]; then
    echo "  ✓ Dry-run mode: enabled"
fi

# Build CLI command
echo ""
echo "Invoking AutoDoc CLI..."
echo ""

CLI_ARGS=(
    "--commit" "$COMMIT_SHA"
    "--repo" "$REPO_NAME"
    "--branch" "$BRANCH_NAME"
)

if [ -n "$PR_ID" ]; then
    CLI_ARGS+=("--pr-id" "$PR_ID")
fi

if [ "$DRY_RUN" = "true" ]; then
    CLI_ARGS+=("--dry-run")
fi

# Find the CLI entrypoint
# Try common locations
CLI_SCRIPT=""
if [ -f "autodoc/cli/main.py" ]; then
    CLI_SCRIPT="python3 -m autodoc.cli.main"
elif [ -f "python3" ] && python3 -c "import autodoc.cli.main" 2>/dev/null; then
    CLI_SCRIPT="python3 -m autodoc.cli.main"
elif command -v autodoc >/dev/null 2>&1; then
    CLI_SCRIPT="autodoc"
else
    echo "Error: Could not find AutoDoc CLI"
    echo "Tried:"
    echo "  - autodoc/cli/main.py"
    echo "  - python3 -m autodoc.cli.main"
    echo "  - autodoc command"
    exit 1
fi

echo "Command: $CLI_SCRIPT ${CLI_ARGS[*]}"
echo ""

# Execute CLI
exec $CLI_SCRIPT "${CLI_ARGS[@]}"

