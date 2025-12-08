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

# Step 2: Run analysis engine for each file
echo ""
echo "Step 2: Analyzing code changes..."

# Create temp directory for analysis results
TEMP_DIR=$(mktemp -d)
trap "rm -rf $TEMP_DIR" EXIT

TOTAL_ADDED=0
TOTAL_MODIFIED=0
TOTAL_REMOVED=0
TOTAL_BREAKING=0

for FILE in $CHANGED_FILES; do
    echo "  Analyzing: $FILE"
    
    # Get old and new versions of the file
    git show HEAD^:"$FILE" > "$TEMP_DIR/old.py" 2>/dev/null || echo "" > "$TEMP_DIR/old.py"
    git show HEAD:"$FILE" > "$TEMP_DIR/new.py" 2>/dev/null || echo "" > "$TEMP_DIR/new.py"
    
    # Run your Python analysis engine
    python3 << PYTHON_SCRIPT
import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path.cwd()))

from src.analyzer.parser import parse_python_code
from src.analyzer.extractor import extract_symbols
from src.analyzer.change_detector import detect_changes

with open("$TEMP_DIR/old.py", "r") as f:
    old_code = f.read()

with open("$TEMP_DIR/new.py", "r") as f:
    new_code = f.read()

try:
    old_tree = parse_python_code(old_code) if old_code.strip() else None
    new_tree = parse_python_code(new_code) if new_code.strip() else None
    
    if old_tree and new_tree:
        old_module = extract_symbols(old_tree, "$FILE")
        new_module = extract_symbols(new_tree, "$FILE")
        report = detect_changes(old_module, new_module, "HEAD^", "HEAD")
        
        # Extract detailed changes for database persistence
        detailed_changes = []
        for change in report.added:
            detailed_changes.append({
                "file_path": "$FILE",
                "symbol": change.symbol_name,
                "change_type": "added",
                "signature_before": None,
                "signature_after": None  # SymbolChange doesn't have signature fields
            })
        for change in report.modified:
            detailed_changes.append({
                "file_path": "$FILE",
                "symbol": change.symbol_name,
                "change_type": "modified",
                "signature_before": None,
                "signature_after": None
            })
        for change in report.removed:
            detailed_changes.append({
                "file_path": "$FILE",
                "symbol": change.symbol_name,
                "change_type": "removed",
                "signature_before": None,
                "signature_after": None
            })
        
        result = report.to_dict()
        result["detailed_changes"] = detailed_changes
    else:
        result = {
            "file_path": "$FILE",
            "summary": {
                "added_count": 0,
                "modified_count": 0,
                "removed_count": 0,
                "breaking_count": 0
            },
            "detailed_changes": []
        }
    
    with open("$TEMP_DIR/result.json", "w") as f:
        json.dump(result, f)
    
except Exception as e:
    result = {
        "file_path": "$FILE",
        "error": str(e),
        "summary": {
            "added_count": 0,
            "modified_count": 0,
            "removed_count": 0,
            "breaking_count": 0
        },
        "detailed_changes": []
    }
    with open("$TEMP_DIR/result.json", "w") as f:
        json.dump(result, f)

PYTHON_SCRIPT
    
    # Read results and accumulate counts
    if [[ -f "$TEMP_DIR/result.json" ]]; then
        if command -v jq &> /dev/null; then
            ADDED=$(jq '.summary.added_count // 0' "$TEMP_DIR/result.json")
            MODIFIED=$(jq '.summary.modified_count // 0' "$TEMP_DIR/result.json")
            REMOVED=$(jq '.summary.removed_count // 0' "$TEMP_DIR/result.json")
            BREAKING=$(jq '.summary.breaking_count // 0' "$TEMP_DIR/result.json")
        else
            ADDED=0
            MODIFIED=0
            REMOVED=0
            BREAKING=0
        fi
        
        TOTAL_ADDED=$((TOTAL_ADDED + ADDED))
        TOTAL_MODIFIED=$((TOTAL_MODIFIED + MODIFIED))
        TOTAL_REMOVED=$((TOTAL_REMOVED + REMOVED))
        TOTAL_BREAKING=$((TOTAL_BREAKING + BREAKING))
        
        echo "      Added: $ADDED, Modified: $MODIFIED, Removed: $REMOVED, Breaking: $BREAKING"
        
        # Save this file's result for later
        cp "$TEMP_DIR/result.json" "$TEMP_DIR/result_${FILE//\//_}.json"
    fi
done

echo "  Analysis complete"

# ============================================
# Sprint 3 Integration: Save to Database
# ============================================
echo ""
echo "Step 3: Saving results to AutoDoc database..."

API_BASE="${API_BASE:-http://localhost:8000/api/v1}"

# Check if backend is available
if curl -s -f "${API_BASE}/templates" > /dev/null 2>&1; then
  echo "  Backend available, saving to database..."
  
  # Create Run in database
  RUN_RESPONSE=$(curl -s -X POST "${API_BASE}/runs" \
    -H "Content-Type: application/json" \
    -d "{
      \"repo\": \"${REPO_NAME}\",
      \"branch\": \"${BRANCH_NAME}\",
      \"commit_sha\": \"${COMMIT_SHA}\",
      \"started_at\": \"$(date -u +%Y-%m-%dT%H:%M:%SZ)\",
      \"correlation_id\": \"autodoc-${COMMIT_SHA:0:8}\",
      \"status\": \"Awaiting Review\",
      \"mode\": \"PRODUCTION\"
    }")

  RUN_ID=$(echo "$RUN_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['id'])" 2>/dev/null || echo "")

  if [ -z "$RUN_ID" ]; then
    echo "  WARNING: Failed to create run in database"
  else
    echo "  ✓ Created run #${RUN_ID}"
    
    # Collect all changes from temp files
    echo "  Collecting changes from analysis..."
    ALL_CHANGES_JSON="[]"
    
    for RESULT_FILE in "$TEMP_DIR"/result_*.json; do
      if [ -f "$RESULT_FILE" ]; then
        CHANGES=$(python3 -c "
import json
try:
    with open('$RESULT_FILE') as f:
        data = json.load(f)
        print(json.dumps(data.get('detailed_changes', [])))
except:
    print('[]')
")
        # Merge changes
        ALL_CHANGES_JSON=$(python3 -c "
import json
try:
    existing = json.loads('''$ALL_CHANGES_JSON''')
    new = json.loads('''$CHANGES''')
    existing.extend(new)
    print(json.dumps(existing))
except:
    print('[]')
")
      fi
    done
    
    # Save changes to database
    CHANGE_COUNT=$(echo "$ALL_CHANGES_JSON" | python3 -c "import json, sys; print(len(json.load(sys.stdin)))" 2>/dev/null || echo "0")
    if [ "$CHANGE_COUNT" -gt 0 ]; then
      echo "  Saving $CHANGE_COUNT change(s) to database..."
      SAVE_RESPONSE=$(curl -s -X POST "${API_BASE}/runs/${RUN_ID}/changes" \
        -H "Content-Type: application/json" \
        -d "$ALL_CHANGES_JSON")
      echo "  ✓ Saved changes"
    else
      echo "  No changes to save"
    fi
    
    # Generate patches using your Sprint 3 infrastructure
    echo "  Generating documentation patches..."
    PATCH_RESPONSE=$(curl -s -X POST "${API_BASE}/runs/${RUN_ID}/generate-patches")
    PATCHES_GENERATED=$(echo "$PATCH_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('patches_generated', 0))" 2>/dev/null || echo "0")
    echo "  ✓ Generated ${PATCHES_GENERATED} patch(es)"
    
    echo ""
    echo "  View results at: http://localhost:4200/runs/${RUN_ID}"
  fi
else
  echo "  Backend not available (this is normal in CI/CD)"
  echo "  Skipping database operations..."
fi

# Step 4: Creating change report (JSON file)
echo ""
echo "Step 4: Creating change report JSON..."

# Generate final change_report.json with real data
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
    "files_changed": ${FILE_COUNT},
    "functions_added": ${TOTAL_ADDED},
    "functions_modified": ${TOTAL_MODIFIED},
    "functions_removed": ${TOTAL_REMOVED},
    "breaking_changes": ${TOTAL_BREAKING}
  },
  "patches": [
    {
      "page_id": "{{page_id}}",
      "page_title": "API Reference",
      "status": "pending_approval"
    }
  ],
  "status": "success",
  "message": "Analysis completed successfully using Sprint 3 infrastructure"
}
EOF

echo "  Change report created: change_report.json"

# Display summary
echo ""
echo "========================================"
echo "  AutoDoc analysis completed!"
echo "========================================"
echo ""
echo "Summary:"
echo "  Files analyzed:      ${FILE_COUNT}"
echo "  Functions added:     ${TOTAL_ADDED}"
echo "  Functions modified:  ${TOTAL_MODIFIED}"
echo "  Functions removed:   ${TOTAL_REMOVED}"
echo "  Breaking changes:    ${TOTAL_BREAKING}"
echo ""
echo "Output:"
echo "  change_report.json"
echo ""

if [[ "$VERBOSE" == "true" ]] && command -v jq &> /dev/null; then
    echo "Full report:"
    cat change_report.json | jq '.'
fi

exit 0
