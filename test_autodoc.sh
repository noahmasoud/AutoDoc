#!/bin/bash

echo "========================================="
echo "Testing AutoDoc Locally"
echo "========================================="
echo ""

# Save the original directory (where AutoDoc repo is)
ORIGINAL_DIR=$(pwd)

# Create a test repository with two versions
TEST_DIR=$(mktemp -d)
echo "Test directory: $TEST_DIR"

cd "$TEST_DIR"
git init

# Create initial version (commit 1)
cat > calculator.py << 'PYTHON'
class Calculator:
    def add(self, x, y):
        return x + y
    
    def subtract(self, x, y):
        return x - y
    
    def multiply(self, x, y):
        return x * y
PYTHON

git add calculator.py
git commit -m "Initial version"

# Create updated version (commit 2)
cat > calculator.py << 'PYTHON'
class Calculator:
    """Advanced calculator with extended operations."""
    
    def calculate(self, operation: str, x: float, y: float) -> float:
        """
        Perform a calculation based on operation type.
        
        Args:
            operation: Type of operation
            x: First number
            y: Second number
            
        Returns:
            Result of the calculation
        """
        if operation == 'add':
            return x + y
        elif operation == 'subtract':
            return x - y
        elif operation == 'multiply':
            return x * y
        else:
            raise ValueError(f"Unknown operation: {operation}")
    
    def multiply(self, x: float, y: float) -> float:
        """Multiply two numbers."""
        return x * y
    
    def power(self, base: float, exponent: float) -> float:
        """Raise a number to a power."""
        return base ** exponent
PYTHON

git add calculator.py
git commit -m "Add type hints and new methods"

# Get commit SHA
COMMIT_SHA=$(git rev-parse HEAD)

echo ""
echo "Test repository created with 2 commits"
echo "Latest commit: $COMMIT_SHA"
echo ""

# Copy your autodoc.sh from original directory
echo "Copying autodoc.sh from: $ORIGINAL_DIR"
if [[ ! -f "$ORIGINAL_DIR/autodoc.sh" ]]; then
    echo "✗ Error: autodoc.sh not found in $ORIGINAL_DIR"
    echo "Make sure you're running this from the AutoDoc repository root"
    cd "$ORIGINAL_DIR"
    rm -rf "$TEST_DIR"
    exit 1
fi

cp "$ORIGINAL_DIR/autodoc.sh" .
chmod +x autodoc.sh

# Copy src directory (needed for Python imports)
echo "Copying src directory..."
cp -r "$ORIGINAL_DIR/src" .

# Run autodoc.sh
echo ""
echo "Running autodoc.sh..."
./autodoc.sh --commit "$COMMIT_SHA" --repo "test/repo" --verbose

# Check results
echo ""
echo "========================================="
echo "Test Results"
echo "========================================="

if [[ -f "change_report.json" ]]; then
    echo "✓ change_report.json created"
    echo ""
    echo "Contents:"
    
    # Check if jq is available
    if command -v jq &> /dev/null; then
        cat change_report.json | jq '.'
    else
        cat change_report.json
        echo ""
        echo "Note: Install jq for better JSON formatting: brew install jq"
    fi
    
    # Validate structure
    echo ""
    echo "Validation:"
    
    if command -v jq &> /dev/null; then
        FILES_CHANGED=$(jq '.analysis.files_changed' change_report.json 2>/dev/null || echo "0")
        FUNCTIONS_ADDED=$(jq '.analysis.functions_added' change_report.json 2>/dev/null || echo "0")
        
        echo "  Files changed: $FILES_CHANGED"
        echo "  Functions added: $FUNCTIONS_ADDED"
        
        if [[ "$FILES_CHANGED" -gt 0 ]]; then
            echo "  ✓ Analysis ran (files changed > 0)"
        else
            echo "  ⚠ Warning: Files changed = 0"
            echo "  This might mean the analysis didn't run correctly"
        fi
    else
        echo "  (Install jq for validation: brew install jq)"
    fi
else
    echo "✗ change_report.json not created"
    echo ""
    echo "Check for errors above"
    echo ""
    echo "Troubleshooting:"
    echo "  1. Make sure autodoc.sh exists in your repo"
    echo "  2. Check that src/ directory exists with your Python code"
    echo "  3. Look for error messages in the output above"
fi

# Return to original directory before cleanup
cd "$ORIGINAL_DIR"

# Cleanup
echo ""
echo "Cleaning up test directory: $TEST_DIR"
rm -rf "$TEST_DIR"

echo ""
echo "Test complete!"
