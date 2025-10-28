#!/bin/bash

############################################################
# NKM - 10/14/2025
# AutoDoc CI/CD Entrypoint Script
# This script is called by CI systems (GitHub Actions, GitLab CI) to run AutoDoc
############################################################


set -e  # Exit immediately if any command fails
set -u  # Exit if we try to use an undefined variable
set -o pipefail  # Catch errors in pipes

# Script metadata
SCRIPT_VERSION="0.1.0"
SCRIPT_NAME="autodoc.sh"

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
echo "AutoDoc Entrypoint v${SCRIPT_VERSION}"
echo "========================================"

# Initialize variables with defaults
COMMIT_SHA=""
REPO_NAME=""
BRANCH_NAME="main"
PR_ID=""
DRY_RUN=false
VERBOSE=false

# Help function
show_help() {
    cat << EOF
Usage: $SCRIPT_NAME [OPTIONS]

AutoDoc analyzes code changes and generates documentation patches.

Required Arguments:
  --commit <sha>        Git commit SHA to analyze
  --repo <name>         Repository name (e.g., owner/repo)

Optional Arguments:
  --branch <name>       Branch name (default: main)
  --pr-id <id>          Pull/Merge request ID
  --dry-run             Generate patches without updating Confluence
  --verbose             Enable verbose logging
  --help                Show this help message

Examples:
  $SCRIPT_NAME --commit abc123 --repo myorg/myrepo
  $SCRIPT_NAME --commit abc123 --repo myorg/myrepo --branch dev --pr-id 42
  $SCRIPT_NAME --commit abc123 --repo myorg/myrepo --dry-run

Environment Variables:
  CONFLUENCE_TOKEN      Confluence API token (required unless --dry-run)
  CONFLUENCE_BASE_URL   Confluence base URL
  CONFLUENCE_SPACE_KEY  Confluence space key

Exit Codes:
  0  Success
  1  Invalid arguments or configuration error
  2  Analysis failed
  3  Confluence update failed

EOF
}

# Parse command-line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --commit)
            COMMIT_SHA="$2"
            shift 2
            ;;
        --repo)
            REPO_NAME="$2"
            shift 2
            ;;
        --branch)
            BRANCH_NAME="$2"
            shift 2
            ;;
        --pr-id)
            PR_ID="$2"
            shift 2
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --verbose)
            VERBOSE=true
            shift
            ;;
        --help|-h)
            show_help
            exit 0
            ;;
        *)
            echo "Error: Unknown option '$1'"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Validate required arguments
echo ""
echo "Validating arguments..."

if [[ -z "$COMMIT_SHA" ]]; then
    echo "Error: --commit is required"
    echo "Use --help for usage information"
    exit 1
fi

if [[ -z "$REPO_NAME" ]]; then
    echo "Error: --repo is required"
    echo "Use --help for usage information"
    exit 1
fi

# Validate commit SHA format (basic check)
if [[ ! "$COMMIT_SHA" =~ ^[a-f0-9]{7,40}$ ]]; then
    echo "Warning: Commit SHA '$COMMIT_SHA' doesn't look like a valid git hash"
    echo "Continuing anyway (may be a test value)..."
fi

echo "✓ Arguments validated"

# Display configuration
echo ""
echo "Configuration:"
echo "  Commit SHA:    $COMMIT_SHA"
echo "  Repository:    $REPO_NAME"
echo "  Branch:        $BRANCH_NAME"
echo "  PR/MR ID:      ${PR_ID:-none}"
echo "  Dry Run:       $DRY_RUN"
echo "  Verbose:       $VERBOSE"

if [[ "$VERBOSE" == "true" ]]; then
    echo ""
    echo "Environment:"
    echo "  Working Dir:   $(pwd)"
    echo "  Script Path:   $(realpath "$0" 2>/dev/null || echo "$0")"
    echo "  Shell:         $SHELL"
    echo "  User:          $(whoami)"
fi

echo ""

# Main execution
echo "========================================"
echo "Running AutoDoc Analysis"
echo "========================================"
echo ""

# For Sprint 0, we just generate a placeholder report
# In Sprint 1+, this will call: python -m autodoc.main

echo "Step 1: Analyzing code changes..."
sleep 1  # Simulate work
echo "✓ Found 3 changed files"

echo ""
echo "Step 2: Detecting API changes..."
sleep 1  # Simulate work
echo "✓ Detected 2 function changes"

echo ""
echo "Step 3: Generating documentation patches..."
sleep 1  # Simulate work
echo "✓ Generated 1 patch"

echo ""
echo "Step 4: Creating change report..."

# Generate change_report.json
cat > change_report.json << EOF
{
  "metadata": {
    "script_version": "${SCRIPT_VERSION}",
    "commit_sha": "${COMMIT_SHA}",
    "repository": "${REPO_NAME}",
    "branch": "${BRANCH_NAME}",
    "pr_id": "${PR_ID:-null}",
    "dry_run": ${DRY_RUN},
    "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
    "hostname": "$(hostname)"
  },
  "analysis": {
    "files_changed": 3,
    "functions_added": 1,
    "functions_modified": 1,
    "functions_removed": 0,
    "breaking_changes": 0
  },
  "patches": [
    {
      "page_id": "placeholder",
      "page_title": "API Reference",
      "status": "pending_approval"
    }
  ],
  "status": "success",
  "message": "Sprint 0 - Entrypoint script test completed successfully"
}
EOF

echo "✓ Change report created: change_report.json"

# Display the report if verbose
if [[ "$VERBOSE" == "true" ]]; then
    echo ""
    echo "Report contents:"
    cat change_report.json
fi

echo ""
echo "========================================"
echo "✓ AutoDoc analysis completed successfully!"
echo "========================================"
echo ""
echo "Output:"
echo "  change_report.json"
echo ""

# Exit successfully
exit 0