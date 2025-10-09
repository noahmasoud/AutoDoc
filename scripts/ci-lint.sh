#!/bin/bash
# CI Lint Script for AutoDoc
# Runs linting and formatting checks

set -e  # Exit on any error

echo "🔍 Starting CI Lint Suite for AutoDoc"
echo "====================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Install dependencies if needed
print_status "Installing lint dependencies..."
pip install -e ".[lint]" --quiet

# Run ruff linting
print_status "Running ruff linting..."
ruff check . --statistics
if [ $? -eq 0 ]; then
    print_success "Ruff linting passed"
else
    print_error "Ruff linting failed"
    exit 1
fi

# Run ruff formatting check
print_status "Running ruff format check..."
ruff format --check --diff .
if [ $? -eq 0 ]; then
    print_success "Code formatting is correct"
else
    print_error "Code formatting issues found"
    print_warning "Run 'ruff format .' to fix formatting issues"
    exit 1
fi

# Run mypy type checking
print_status "Running mypy type checking..."
mypy . --show-error-codes --show-error-context
if [ $? -eq 0 ]; then
    print_success "Type checking passed"
else
    print_error "Type checking failed"
    exit 1
fi

# Check for security issues (if bandit is available)
if command -v bandit &> /dev/null; then
    print_status "Running security check with bandit..."
    bandit -r . -f json -o bandit-report.json || true
    print_warning "Security check completed (bandit report: bandit-report.json)"
fi

# Summary
echo ""
echo "====================================="
print_success "All linting checks passed! ✅"
echo "====================================="
echo ""
echo "Lint Summary:"
echo "• Ruff Linting: ✅ Passed"
echo "• Code Formatting: ✅ Passed"
echo "• Type Checking: ✅ Passed"
echo ""
