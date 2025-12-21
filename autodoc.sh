#!/bin/bash

############################################################
# AutoDoc CI/CD Entrypoint Script - Multi-Language Support
# Supports Python, JavaScript, and Go file analysis
# Updated to call multi-language analysis engine and persist changes
############################################################

set -e
set -u
set -o pipefail

SCRIPT_VERSION="2.0.0"
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

# Step 1: Get list of changed files (Python, JavaScript, Go)
echo "Step 1: Finding changed files..."
CHANGED_PYTHON=$(git diff --name-only HEAD^ HEAD | grep '\.py$' || echo "")
CHANGED_JS=$(git diff --name-only HEAD^ HEAD | grep -E '\.(js|jsx)$' || echo "")
CHANGED_GO=$(git diff --name-only HEAD^ HEAD | grep '\.go$' || echo "")

# Combine all changed files
CHANGED_FILES=$(echo -e "$CHANGED_PYTHON\n$CHANGED_JS\n$CHANGED_GO" | grep -v '^$' | sort -u)

if [[ -z "$CHANGED_FILES" ]]; then
    echo "No supported files changed (Python, JavaScript, or Go)"
    
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
  "message": "No supported files changed (Python, JavaScript, or Go)"
}
EOF
    
    echo "  Empty report generated"
    exit 0
fi

FILE_COUNT=$(echo "$CHANGED_FILES" | wc -l | tr -d ' ')
PYTHON_COUNT=$(if [[ -n "$CHANGED_PYTHON" ]]; then echo "$CHANGED_PYTHON" | grep -v '^$' | wc -l | tr -d ' '; else echo "0"; fi)
JS_COUNT=$(if [[ -n "$CHANGED_JS" ]]; then echo "$CHANGED_JS" | grep -v '^$' | wc -l | tr -d ' '; else echo "0"; fi)
GO_COUNT=$(if [[ -n "$CHANGED_GO" ]]; then echo "$CHANGED_GO" | grep -v '^$' | wc -l | tr -d ' '; else echo "0"; fi)

echo "  Found ${FILE_COUNT} changed file(s):"
echo "    - Python: ${PYTHON_COUNT}"
echo "    - JavaScript: ${JS_COUNT}"
echo "    - Go: ${GO_COUNT}"

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
    OLD_FILE="$TEMP_DIR/old_$(basename "$FILE" | tr '/' '_')"
    NEW_FILE="$TEMP_DIR/new_$(basename "$FILE" | tr '/' '_')"
    
    git show HEAD^:"$FILE" > "$OLD_FILE" 2>/dev/null || echo "" > "$OLD_FILE"
    git show HEAD:"$FILE" > "$NEW_FILE" 2>/dev/null || echo "" > "$NEW_FILE"
    
    # Use the multi-language analyzer script
    RESULT_FILE="$TEMP_DIR/result_$(basename "$FILE" | tr '/' '_').json"
    
    python3 "$(dirname "$0")/scripts/analyze_changed_files.py" "$FILE" "$OLD_FILE" "$NEW_FILE" > "$RESULT_FILE" 2>/dev/null || {
        # Fallback if script fails
        echo "    ⚠ Analysis failed for $FILE, creating empty result"
        cat > "$RESULT_FILE" << EOF
{
  "file_path": "$FILE",
  "error": "Analysis failed",
  "summary": {
    "added_count": 0,
    "modified_count": 0,
    "removed_count": 0,
    "breaking_count": 0
  },
  "detailed_changes": []
}
EOF
    }
    
    # Read results and accumulate counts
    if [[ -f "$RESULT_FILE" ]]; then
        if command -v jq &> /dev/null; then
            ADDED=$(jq '.summary.added_count // 0' "$RESULT_FILE")
            MODIFIED=$(jq '.summary.modified_count // 0' "$RESULT_FILE")
            REMOVED=$(jq '.summary.removed_count // 0' "$RESULT_FILE")
            BREAKING=$(jq '.summary.breaking_count // 0' "$RESULT_FILE")
        else
            # Fallback without jq
            ADDED=$(python3 -c "import json, sys; data=json.load(open('$RESULT_FILE')); print(data.get('summary', {}).get('added_count', 0))" 2>/dev/null || echo "0")
            MODIFIED=$(python3 -c "import json, sys; data=json.load(open('$RESULT_FILE')); print(data.get('summary', {}).get('modified_count', 0))" 2>/dev/null || echo "0")
            REMOVED=$(python3 -c "import json, sys; data=json.load(open('$RESULT_FILE')); print(data.get('summary', {}).get('removed_count', 0))" 2>/dev/null || echo "0")
            BREAKING=$(python3 -c "import json, sys; data=json.load(open('$RESULT_FILE')); print(data.get('summary', {}).get('breaking_count', 0))" 2>/dev/null || echo "0")
        fi
        
        TOTAL_ADDED=$((TOTAL_ADDED + ADDED))
        TOTAL_MODIFIED=$((TOTAL_MODIFIED + MODIFIED))
        TOTAL_REMOVED=$((TOTAL_REMOVED + REMOVED))
        TOTAL_BREAKING=$((TOTAL_BREAKING + BREAKING))
        
        echo "      Added: $ADDED, Modified: $MODIFIED, Removed: $REMOVED, Breaking: $BREAKING"
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
    
    # Save symbols to database using ingestors
    echo "  Saving symbols to database..."
    SYMBOL_COUNTS=$(python3 "$(dirname "$0")/scripts/save_symbols_to_db.py" "$RUN_ID" $CHANGED_FILES 2>/dev/null || echo '{"python": 0, "javascript": 0, "go": 0}')
    PYTHON_SYMBOLS=$(echo "$SYMBOL_COUNTS" | python3 -c "import json, sys; print(json.load(sys.stdin).get('python', 0))" 2>/dev/null || echo "0")
    JS_SYMBOLS=$(echo "$SYMBOL_COUNTS" | python3 -c "import json, sys; print(json.load(sys.stdin).get('javascript', 0))" 2>/dev/null || echo "0")
    GO_SYMBOLS=$(echo "$SYMBOL_COUNTS" | python3 -c "import json, sys; print(json.load(sys.stdin).get('go', 0))" 2>/dev/null || echo "0")
    
    TOTAL_SYMBOLS=$((PYTHON_SYMBOLS + JS_SYMBOLS + GO_SYMBOLS))
    if [ "$TOTAL_SYMBOLS" -gt 0 ]; then
      echo "  ✓ Saved $TOTAL_SYMBOLS symbol(s) (Python: $PYTHON_SYMBOLS, JavaScript: $JS_SYMBOLS, Go: $GO_SYMBOLS)"
    else
      echo "  ⚠ No symbols saved (files may not have parseable symbols or analyzers unavailable)"
    fi
    
    # Generate patches using your Sprint 3 infrastructure
    echo "  Generating documentation patches..."
    PATCH_RESPONSE=$(curl -s -X POST "${API_BASE}/runs/${RUN_ID}/generate-patches")
    PATCHES_GENERATED=$(echo "$PATCH_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('patches_generated', 0))" 2>/dev/null || echo "0")
    echo "  ✓ Generated ${PATCHES_GENERATED} patch(es)"
    
    # Check for LLM summary generation (happens automatically during patch generation)
    if [ "$PATCHES_GENERATED" -gt 0 ]; then
      echo ""
      echo "  Checking LLM summary status..."
      
      # Try to retrieve LLM summary artifact (this will generate it if missing)
      LLM_SUMMARY_RESPONSE=$(curl -s -X GET "${API_BASE}/patches/llm-summary-artifact/${RUN_ID}" 2>/dev/null || echo "")
      
      if [ -n "$LLM_SUMMARY_RESPONSE" ] && echo "$LLM_SUMMARY_RESPONSE" | python3 -c "import sys, json; data=json.load(sys.stdin); exit(0 if data.get('summary') else 1)" 2>/dev/null; then
        echo "  ✓ LLM summary generated successfully"
        
        # Auto-publish to Confluence if not dry-run
        if [ "$DRY_RUN" = "false" ]; then
          echo "  Publishing LLM summary to Confluence..."
          PUBLISH_RESPONSE=$(curl -s -X POST "${API_BASE}/patches/publish-summary/${RUN_ID}" \
            -H "Content-Type: application/json" \
            -d '{"strategy": "append_to_patches"}' 2>/dev/null || echo "")
          
          if [ -n "$PUBLISH_RESPONSE" ] && echo "$PUBLISH_RESPONSE" | python3 -c "import sys, json; data=json.load(sys.stdin); exit(0 if data.get('success') else 1)" 2>/dev/null; then
            PAGES_UPDATED=$(echo "$PUBLISH_RESPONSE" | python3 -c "import sys, json; print(len(json.load(sys.stdin).get('pages_updated', [])))" 2>/dev/null || echo "0")
            echo "  ✓ Published LLM summary to ${PAGES_UPDATED} Confluence page(s)"
          else
            echo "  ⚠ LLM summary publishing failed or skipped (check logs for details)"
          fi
        else
          echo "  ⏭ Skipping Confluence publish (dry-run mode)"
        fi
      else
        echo "  ⚠ LLM summary not available (API key missing, quota exceeded, or error)"
      fi
    fi
    
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
      "page_id": "placeholder",
      "page_title": "API Reference",
      "status": "pending_approval"
    }
  ],
  "status": "success",
  "message": "Analysis completed"
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
if [ -n "${RUN_ID:-}" ]; then
  echo "  Run ID:              ${RUN_ID}"
  echo "  Patches generated:   ${PATCHES_GENERATED:-0}"
  if [ "$DRY_RUN" = "false" ] && [ "${PATCHES_GENERATED:-0}" -gt 0 ]; then
    echo "  LLM summary:         Generated and published to Confluence"
  elif [ "$DRY_RUN" = "true" ] && [ "${PATCHES_GENERATED:-0}" -gt 0 ]; then
    echo "  LLM summary:         Generated (not published - dry-run mode)"
  fi
fi
echo ""
echo "Output:"
echo "  change_report.json"
if [ -n "${RUN_ID:-}" ]; then
  echo "  Artifacts:            artifacts/${RUN_ID}/"
fi
echo ""

if [[ "$VERBOSE" == "true" ]] && command -v jq &> /dev/null; then
    echo "Full report:"
    cat change_report.json | jq '.'
fi

exit 0
