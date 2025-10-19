#!/bin/bash
# Test Runner Script for AutoDoc
# Comprehensive test runner with different test categories

set -e  # Exit on any error

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

# Help function
show_help() {
    echo "AutoDoc Test Runner"
    echo "=================="
    echo ""
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -h, --help              Show this help message"
    echo "  -u, --unit              Run unit tests only"
    echo "  -i, --integration       Run integration tests only"
    echo "  -a, --analyzer          Run analyzer tests only"
    echo "  -c, --connector         Run connector tests only"
    echo "  -s, --slow              Include slow tests"
    echo "  -v, --verbose           Verbose output"
    echo "  -c, --coverage          Generate coverage report"
    echo "  --min-coverage N        Minimum coverage percentage (default: 70)"
    echo "  --max-fail N            Maximum number of failures before stopping (default: 1)"
    echo "  --no-warnings           Disable warning messages"
    echo ""
    echo "Examples:"
    echo "  $0                      # Run all tests (default)"
    echo "  $0 -u                   # Run unit tests only"
    echo "  $0 -i -s                # Run integration tests including slow tests"
    echo "  $0 -a -c --coverage     # Run analyzer and connector tests with coverage"
    echo ""
}

# Default values
RUN_UNIT=true
RUN_INTEGRATION=true
RUN_ANALYZER=true
RUN_CONNECTOR=true
INCLUDE_SLOW=false
VERBOSE=false
GENERATE_COVERAGE=true
MIN_COVERAGE=70
MAX_FAIL=1
DISABLE_WARNINGS=false

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_help
            exit 0
            ;;
        -u|--unit)
            RUN_INTEGRATION=false
            RUN_ANALYZER=false
            RUN_CONNECTOR=false
            shift
            ;;
        -i|--integration)
            RUN_UNIT=false
            RUN_ANALYZER=false
            RUN_CONNECTOR=false
            shift
            ;;
        -a|--analyzer)
            RUN_INTEGRATION=false
            RUN_CONNECTOR=false
            shift
            ;;
        -c|--connector)
            RUN_INTEGRATION=false
            RUN_ANALYZER=false
            shift
            ;;
        -s|--slow)
            INCLUDE_SLOW=true
            shift
            ;;
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        --coverage)
            GENERATE_COVERAGE=true
            shift
            ;;
        --min-coverage)
            MIN_COVERAGE="$2"
            shift 2
            ;;
        --max-fail)
            MAX_FAIL="$2"
            shift 2
            ;;
        --no-warnings)
            DISABLE_WARNINGS=true
            shift
            ;;
        *)
            print_error "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

echo "🧪 AutoDoc Test Runner"
echo "======================"

# Build pytest command
PYTEST_CMD="pytest"

# Add verbosity
if [ "$VERBOSE" = true ]; then
    PYTEST_CMD="$PYTEST_CMD -v"
else
    PYTEST_CMD="$PYTEST_CMD -q"
fi

# Add max failures
PYTEST_CMD="$PYTEST_CMD --maxfail=$MAX_FAIL"

# Add warning settings
if [ "$DISABLE_WARNINGS" = true ]; then
    PYTEST_CMD="$PYTEST_CMD --disable-warnings"
fi

# Add coverage if requested
if [ "$GENERATE_COVERAGE" = true ]; then
    PYTEST_CMD="$PYTEST_CMD --cov=autodoc --cov=api --cov=cli --cov=core --cov=db --cov=schemas --cov=services"
    PYTEST_CMD="$PYTEST_CMD --cov-report=term-missing --cov-report=html:htmlcov"
    PYTEST_CMD="$PYTEST_CMD --cov-fail-under=$MIN_COVERAGE"
fi

# Add test markers
MARKERS=""
if [ "$INCLUDE_SLOW" = false ]; then
    MARKERS="$MARKERS and not slow"
fi

# Install dependencies
print_status "Installing test dependencies..."
pip install -e ".[test,lint,dev]" --quiet

# Run tests based on selection
TOTAL_TESTS=0
FAILED_TESTS=0

if [ "$RUN_UNIT" = true ]; then
    print_status "Running unit tests..."
    UNIT_CMD="$PYTEST_CMD -m 'unit$MARKERS' tests/unit/"
    if eval $UNIT_CMD; then
        print_success "Unit tests passed"
    else
        print_error "Unit tests failed"
        FAILED_TESTS=$((FAILED_TESTS + 1))
    fi
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
fi

if [ "$RUN_INTEGRATION" = true ]; then
    print_status "Running integration tests..."
    INTEGRATION_CMD="$PYTEST_CMD -m 'integration$MARKERS' tests/integration/"
    if eval $INTEGRATION_CMD; then
        print_success "Integration tests passed"
    else
        print_error "Integration tests failed"
        FAILED_TESTS=$((FAILED_TESTS + 1))
    fi
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
fi

if [ "$RUN_ANALYZER" = true ]; then
    print_status "Running analyzer tests..."
    ANALYZER_CMD="$PYTEST_CMD -m 'analyzer$MARKERS' tests/"
    if eval $ANALYZER_CMD; then
        print_success "Analyzer tests passed"
    else
        print_error "Analyzer tests failed"
        FAILED_TESTS=$((FAILED_TESTS + 1))
    fi
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
fi

if [ "$RUN_CONNECTOR" = true ]; then
    print_status "Running connector tests..."
    CONNECTOR_CMD="$PYTEST_CMD -m 'connector$MARKERS' tests/"
    if eval $CONNECTOR_CMD; then
        print_success "Connector tests passed"
    else
        print_error "Connector tests failed"
        FAILED_TESTS=$((FAILED_TESTS + 1))
    fi
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
fi

# Summary
echo ""
echo "======================"
if [ $FAILED_TESTS -eq 0 ]; then
    print_success "All $TOTAL_TESTS test categories passed! ✅"
else
    print_error "$FAILED_TESTS out of $TOTAL_TESTS test categories failed! ❌"
    exit 1
fi
echo "======================"

if [ "$GENERATE_COVERAGE" = true ]; then
    echo ""
    echo "Coverage reports generated:"
    echo "• Terminal: coverage report above"
    echo "• HTML: htmlcov/index.html"
fi
