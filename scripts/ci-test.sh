#!/bin/bash
# CI Test Script for AutoDoc
# Runs tests with specific CI requirements

set -e  # Exit on any error

echo "🚀 Starting CI Test Suite for AutoDoc"
echo "======================================"

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

# Check if we're in a virtual environment
if [[ "$VIRTUAL_ENV" == "" ]]; then
    print_warning "No virtual environment detected. Consider using one for isolation."
fi

# Install dependencies if needed
print_status "Installing test dependencies..."
pip install -e ".[test,lint,dev]" --quiet

# Run linting first
print_status "Running code linting with ruff..."
ruff check . --output-format=github
if [ $? -eq 0 ]; then
    print_success "Linting passed"
else
    print_error "Linting failed"
    exit 1
fi

# Run type checking
print_status "Running type checking with mypy..."
mypy .
if [ $? -eq 0 ]; then
    print_success "Type checking passed"
else
    print_error "Type checking failed"
    exit 1
fi

# Run unit tests with CI-specific settings
print_status "Running unit tests..."
pytest -q --maxfail=1 --disable-warnings \
    -m "unit and not slow" \
    --cov=autodoc --cov=api --cov=cli --cov=core --cov=db --cov=schemas --cov=services \
    --cov-report=term-missing \
    --cov-report=xml:coverage.xml \
    --cov-fail-under=70 \
    --tb=short \
    --strict-markers \
    --strict-config \
    tests/unit/

if [ $? -eq 0 ]; then
    print_success "Unit tests passed with ≥70% coverage"
else
    print_error "Unit tests failed or coverage below 70%"
    exit 1
fi

# Run integration tests (if any)
print_status "Running integration tests..."
pytest -q --maxfail=1 --disable-warnings \
    -m "integration and not slow" \
    --tb=short \
    tests/integration/

if [ $? -eq 0 ]; then
    print_success "Integration tests passed"
else
    print_error "Integration tests failed"
    exit 1
fi

# Run analyzer-specific tests
print_status "Running analyzer tests..."
pytest -q --maxfail=1 --disable-warnings \
    -m "analyzer" \
    --tb=short \
    tests/

if [ $? -eq 0 ]; then
    print_success "Analyzer tests passed"
else
    print_error "Analyzer tests failed"
    exit 1
fi

# Run connector-specific tests
print_status "Running connector tests..."
pytest -q --maxfail=1 --disable-warnings \
    -m "connector and not external" \
    --tb=short \
    tests/

if [ $? -eq 0 ]; then
    print_success "Connector tests passed"
else
    print_error "Connector tests failed"
    exit 1
fi

# Generate coverage report
print_status "Generating coverage report..."
coverage report --show-missing --fail-under=70

if [ $? -eq 0 ]; then
    print_success "Coverage report generated successfully"
else
    print_error "Coverage below 70% threshold"
    exit 1
fi

# Summary
echo ""
echo "======================================"
print_success "All CI tests passed! ✅"
echo "======================================"
echo ""
echo "Test Summary:"
echo "• Linting: ✅ Passed"
echo "• Type Checking: ✅ Passed" 
echo "• Unit Tests: ✅ Passed (≥70% coverage)"
echo "• Integration Tests: ✅ Passed"
echo "• Analyzer Tests: ✅ Passed"
echo "• Connector Tests: ✅ Passed"
echo ""
echo "Coverage reports generated:"
echo "• Terminal: coverage report above"
echo "• XML: coverage.xml"
echo "• HTML: htmlcov/index.html (if generated)"
echo ""
