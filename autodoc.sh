#!/bin/bash

############################################################
# AutoDoc CI/CD Entrypoint Script - Sprint 3 Integration
# Updated to call actual Python analysis engine and persist changes
############################################################

set -e
set -u
set -o pipefail

SCRIPT_VERSION="1.0.0"
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

echo "  Arguments validated"

# Display configuration
echo ""
echo "Configuration:"
echo "  Commit SHA:    $COMMIT_SHA"
echo "  Repository:    $REPO_NAME"
echo "  Branch:        $BRANCH_NAME"
echo "  PR/MR ID:      ${PR_ID:-none}"
echo "  Dry Run:       $DRY_RUN"
echo "  Verbose:       $VERBOSE"

echo ""

# Main execution
echo "========================================"
echo "Running AutoDoc Analysis"
echo "========================================"
echo ""

# Step 1: Get list of changed Python files
echo "Step 1: Finding changed Python files..."
CHANGED_FILES=$(git diff --name-only HEAD^ HEAD | grep '\.py$' || echo "")

if [[ -z "$CHANGED_FILES" ]]; then
    echo "No Python files changed"
    
    # Generate empty report
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
    "files_changed": 0,
    "functions_added": 0,
    "functions_modified": 0,
    "functions_removed": 0,
    "breaking_changes": 0
  },
  "detailed_changes": [],
  "patches": [],
  "status": "success",
  "message": "No Python files changed"
}
EOF
    
    echo "  Empty report generated"
    exit 0
fi

FILE_COUNT=$(echo "$CHANGED_FILES" | wc -l | tr -d ' ')
echo "  Found ${FILE_COUNT} changed Python file(s)"

# Step 2: Use Python CLI for proper analysis
echo ""
echo "Step 2: Analyzing code changes using Python CLI..."

# Determine AutoDoc project root (where this script lives)
AUTODOC_ROOT="$(cd "$(dirname "$0")" && pwd)"
export PYTHONPATH="${AUTODOC_ROOT}${PYTHONPATH:+:${PYTHONPATH}}"

# Set database path to use AutoDoc's database
# The CLI needs to access the same database as the backend
if [ -f "${AUTODOC_ROOT}/.env" ]; then
    # Read DATABASE_URL from .env file
    ENV_DB_URL=$(grep "^DATABASE_URL=" "${AUTODOC_ROOT}/.env" | cut -d'=' -f2- | tr -d '"' | tr -d "'" | head -1)
    if [ -n "$ENV_DB_URL" ]; then
        # If it's a relative path (sqlite:///./), convert to absolute
        if [[ "$ENV_DB_URL" == sqlite:///./* ]]; then
            DB_FILE="${ENV_DB_URL#sqlite:///./}"
            export DATABASE_URL="sqlite:///${AUTODOC_ROOT}/${DB_FILE}"
        else
            export DATABASE_URL="$ENV_DB_URL"
        fi
    else
        export DATABASE_URL="sqlite:///${AUTODOC_ROOT}/autodoc.db"
    fi
else
    export DATABASE_URL="sqlite:///${AUTODOC_ROOT}/autodoc.db"
fi

# Check if we're in a virtual environment or need to activate one
if [ -f "${AUTODOC_ROOT}/venv/bin/activate" ]; then
    source "${AUTODOC_ROOT}/venv/bin/activate"
fi

# Store current directory (the git repo being analyzed)
# The CLI needs to run git commands from here
CURRENT_DIR="$(pwd)"

# Use Python CLI module which handles all analysis properly
# Note: We stay in CURRENT_DIR so git commands work correctly
python3 -m autodoc.cli.main \
    --commit "$COMMIT_SHA" \
    --repo "$REPO_NAME" \
    --branch "$BRANCH_NAME" \
    $([ -n "$PR_ID" ] && echo "--pr-id $PR_ID" || echo "") \
    $([ "$DRY_RUN" = "true" ] && echo "--dry-run" || echo "") \
    2>&1 | tee /tmp/autodoc_cli_output.log

CLI_EXIT_CODE=${PIPESTATUS[0]}

if [ $CLI_EXIT_CODE -ne 0 ]; then
    echo "Error: Python CLI analysis failed with exit code $CLI_EXIT_CODE"
    echo "Check /tmp/autodoc_cli_output.log for details"
    exit 2
fi

# Extract run ID from CLI output (look for patterns like "Created run 63" or "Run ID: 63")
RUN_ID=$(grep -E "Created run [0-9]+|Run ID: [0-9]+" /tmp/autodoc_cli_output.log 2>/dev/null | grep -oE "[0-9]+" | head -1 || echo "")

echo "  Analysis complete"

# Step 3: The Python CLI already handles all database operations
# (creating runs, analyzing files, detecting changes, generating patches)
echo ""
echo "Step 3: Results saved by Python CLI (Run ID: ${RUN_ID:-N/A})"

# Step 4: Verify artifacts were created
echo ""
echo "Step 4: Verifying artifacts..."

# Artifacts are created in the AutoDoc root directory, not current directory
if [ -f "${AUTODOC_ROOT}/artifacts/change_report.json" ]; then
  echo "  ✓ Change report: ${AUTODOC_ROOT}/artifacts/change_report.json"
  # Copy to current directory for CI/CD compatibility
  mkdir -p ./artifacts
  cp "${AUTODOC_ROOT}/artifacts/change_report.json" ./artifacts/change_report.json 2>/dev/null || true
elif [ -f "./artifacts/change_report.json" ]; then
  echo "  ✓ Change report: ./artifacts/change_report.json"
else
  echo "  ⚠ Change report not found"
fi

if [ -f "${AUTODOC_ROOT}/artifacts/patches.json" ]; then
  echo "  ✓ Patches: ${AUTODOC_ROOT}/artifacts/patches.json"
  mkdir -p ./artifacts
  cp "${AUTODOC_ROOT}/artifacts/patches.json" ./artifacts/patches.json 2>/dev/null || true
elif [ -f "./artifacts/patches.json" ]; then
  echo "  ✓ Patches: ./artifacts/patches.json"
fi

# Display summary
echo ""
echo "========================================"
echo "  AutoDoc analysis completed!"
echo "========================================"
echo ""

# Summarize results from change_report.json if available
REPORT_FILE="./artifacts/change_report.json"
if [ ! -f "$REPORT_FILE" ] && [ -f "${AUTODOC_ROOT}/artifacts/change_report.json" ]; then
  REPORT_FILE="${AUTODOC_ROOT}/artifacts/change_report.json"
fi

if [ -f "$REPORT_FILE" ] && command -v jq &> /dev/null; then
  ADDED=$(jq '.analysis.functions_added // 0' "$REPORT_FILE" 2>/dev/null || echo "0")
  MODIFIED=$(jq '.analysis.functions_modified // 0' "$REPORT_FILE" 2>/dev/null || echo "0")
  REMOVED=$(jq '.analysis.functions_removed // 0' "$REPORT_FILE" 2>/dev/null || echo "0")
  BREAKING=$(jq '.analysis.breaking_changes // 0' "$REPORT_FILE" 2>/dev/null || echo "0")
  FILES=$(jq '.analysis.files_changed // 0' "$REPORT_FILE" 2>/dev/null || echo "0")
  
  echo "Summary:"
  echo "  Files analyzed:      ${FILES}"
  echo "  Functions added:     ${ADDED}"
  echo "  Functions modified:  ${MODIFIED}"
  echo "  Functions removed:   ${REMOVED}"
  echo "  Breaking changes:    ${BREAKING}"
  echo "  Run ID:              ${RUN_ID:-N/A}"
  echo ""
  echo "Output:"
  echo "  change_report.json"
  if [ -f "./artifacts/patches.json" ]; then
    echo "  patches.json"
  fi
  if [ -n "$RUN_ID" ]; then
    echo "  Artifacts:            artifacts/${RUN_ID}/"
    echo ""
    echo "  View results at: http://localhost:4200/runs/${RUN_ID}"
  fi
else
  echo "Summary:"
  echo "  Run ID:              ${RUN_ID:-N/A}"
  echo "  Check artifacts/ directory for output files"
  if [ -n "$RUN_ID" ]; then
    echo "  View results at: http://localhost:4200/runs/${RUN_ID}"
  fi
fi
echo ""

if [[ "$VERBOSE" == "true" ]] && command -v jq &> /dev/null; then
    if [ -f "./artifacts/change_report.json" ]; then
        echo "Full report:"
        cat ./artifacts/change_report.json | jq '.'
    fi
fi

exit 0
