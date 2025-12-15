#!/bin/bash

############################################################
# Test script for CI Adapter
# Simulates CI environments and tests the adapter
############################################################

set -e
set -u

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$PROJECT_ROOT"

echo "========================================"
echo "CI Adapter Test Script"
echo "========================================"
echo ""

# Test 1: GitHub Actions simulation
echo "Test 1: GitHub Actions environment..."
export GITHUB_ACTIONS=true
export GITHUB_SHA="abc123def456"
export GITHUB_REPOSITORY="testorg/testrepo"
export GITHUB_REF="refs/heads/main"
unset GITLAB_CI
unset CI

# Capture the output (we expect it to fail because we're not actually running the CLI)
if scripts/ci-adapter.sh 2>&1 | grep -q "Detected: GitHub Actions"; then
    echo "  ✓ GitHub Actions detection works"
else
    echo "  ✗ GitHub Actions detection failed"
    exit 1
fi

# Test 2: GitLab CI simulation
echo "Test 2: GitLab CI environment..."
unset GITHUB_ACTIONS
export CI=true
export GITLAB_CI=true
export CI_COMMIT_SHA="xyz789ghi012"
export CI_PROJECT_PATH="testgroup/testproject"
export CI_COMMIT_REF_NAME="dev"

if scripts/ci-adapter.sh 2>&1 | grep -q "Detected: GitLab CI"; then
    echo "  ✓ GitLab CI detection works"
else
    echo "  ✗ GitLab CI detection failed"
    exit 1
fi

# Test 3: PR/MR detection
echo "Test 3: Pull Request detection (GitHub)..."
export GITHUB_ACTIONS=true
export GITHUB_SHA="pr-commit-123"
export GITHUB_REPOSITORY="testorg/testrepo"
export GITHUB_REF="refs/pull/42/merge"
export GITHUB_BASE_REF="main"
unset GITLAB_CI
unset CI

if scripts/ci-adapter.sh 2>&1 | grep -q "PR/MR ID: 42"; then
    echo "  ✓ GitHub PR detection works"
else
    echo "  ✗ GitHub PR detection failed"
    exit 1
fi

# Test 4: Merge Request detection (GitLab)
echo "Test 4: Merge Request detection (GitLab)..."
unset GITHUB_ACTIONS
export CI=true
export GITLAB_CI=true
export CI_COMMIT_SHA="mr-commit-456"
export CI_PROJECT_PATH="testgroup/testproject"
export CI_COMMIT_REF_NAME="feature-branch"
export CI_MERGE_REQUEST_IID="99"
export CI_MERGE_REQUEST_TARGET_BRANCH_NAME="main"

if scripts/ci-adapter.sh 2>&1 | grep -q "PR/MR ID: 99"; then
    echo "  ✓ GitLab MR detection works"
else
    echo "  ✗ GitLab MR detection failed"
    exit 1
fi

# Test 5: Dry-run mode
echo "Test 5: Dry-run mode detection..."
export GITHUB_ACTIONS=true
export GITHUB_SHA="dry-run-test"
export GITHUB_REPOSITORY="testorg/testrepo"
export GITHUB_REF="refs/heads/main"
export INPUT_DRY_RUN="true"
unset GITLAB_CI
unset CI

if scripts/ci-adapter.sh 2>&1 | grep -q "Dry-run mode: enabled"; then
    echo "  ✓ GitHub Actions dry-run detection works"
else
    echo "  ✗ GitHub Actions dry-run detection failed"
    exit 1
fi

# Test 6: Error handling (missing variables)
echo "Test 6: Error handling (missing commit SHA)..."
unset GITHUB_ACTIONS
unset GITLAB_CI
unset CI
unset COMMIT_SHA
unset GITHUB_SHA
unset CI_COMMIT_SHA

if scripts/ci-adapter.sh 2>&1 | grep -q "Could not determine commit SHA"; then
    echo "  ✓ Error handling works for missing commit SHA"
else
    echo "  ✗ Error handling failed"
    exit 1
fi

echo ""
echo "========================================"
echo "✓ All CI adapter tests passed!"
echo "========================================"
echo ""
echo "CI adapter is ready for:"
echo "  - GitHub Actions (with PR support)"
echo "  - GitLab CI (with MR support)"
echo "  - Dry-run mode detection"
echo "  - Error handling for missing variables"
echo ""

