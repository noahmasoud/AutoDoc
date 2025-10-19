#!/bin/sh
# AutoDoc POSIX Entrypoint Script
# Production-grade entrypoint for CI runners and containerized deployments
# Compatible with POSIX shell for maximum compatibility

set -e  # Exit on any error
set -u  # Exit on undefined variables

# =============================================================================
# Configuration and Constants
# =============================================================================

# Script metadata
readonly SCRIPT_NAME="$(basename "$0")"
readonly SCRIPT_VERSION="1.0.0"

# Default configuration
readonly DEFAULT_LOG_LEVEL="INFO"
readonly DEFAULT_WORKDIR="/app"
readonly DEFAULT_USER="autodoc"
readonly DEFAULT_TIMEOUT="30"

# Color codes for output (POSIX compatible)
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly BLUE='\033[0;34m'
readonly PURPLE='\033[0;35m'
readonly CYAN='\033[0;36m'
readonly WHITE='\033[1;37m'
readonly NC='\033[0m' # No Color

# =============================================================================
# Logging Functions
# =============================================================================

log_info() {
    printf "${BLUE}[INFO]${NC} %s\n" "$*" >&2
}

log_success() {
    printf "${GREEN}[SUCCESS]${NC} %s\n" "$*" >&2
}

log_warning() {
    printf "${YELLOW}[WARNING]${NC} %s\n" "$*" >&2
}

log_error() {
    printf "${RED}[ERROR]${NC} %s\n" "$*" >&2
}

log_debug() {
    if [ "${LOG_LEVEL:-INFO}" = "DEBUG" ]; then
        printf "${PURPLE}[DEBUG]${NC} %s\n" "$*" >&2
    fi
}

# =============================================================================
# Utility Functions
# =============================================================================

# Check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check if we're running in a container
is_container() {
    [ -f /.dockerenv ] || [ -n "${CONTAINER:-}" ] || [ -n "${DOCKER:-}" ]
}

# Check if we're running in CI
is_ci() {
    [ -n "${CI:-}" ] || [ -n "${CONTINUOUS_INTEGRATION:-}" ] || [ -n "${GITHUB_ACTIONS:-}" ] || [ -n "${GITLAB_CI:-}" ]
}

# Wait for a service to be ready
wait_for_service() {
    local host="${1:-localhost}"
    local port="${2:-8000}"
    local timeout="${3:-30}"
    local interval="${4:-1}"
    
    log_info "Waiting for service at ${host}:${port} (timeout: ${timeout}s)"
    
    local count=0
    while [ $count -lt $timeout ]; do
        if command_exists nc && nc -z "$host" "$port" 2>/dev/null; then
            log_success "Service is ready at ${host}:${port}"
            return 0
        fi
        sleep "$interval"
        count=$((count + interval))
    done
    
    log_error "Service at ${host}:${port} not ready after ${timeout}s"
    return 1
}

# Validate environment variables
validate_env() {
    local required_vars="${1:-}"
    local missing_vars=""
    
    for var in $required_vars; do
        eval "value=\$${var:-}"
        if [ -z "${value:-}" ]; then
            missing_vars="${missing_vars} ${var}"
        fi
    done
    
    if [ -n "$missing_vars" ]; then
        log_error "Missing required environment variables:$missing_vars"
        return 1
    fi
    
    return 0
}

# =============================================================================
# Health Check Functions
# =============================================================================

# Check Python environment
check_python_env() {
    log_info "Checking Python environment..."
    
    if ! command_exists python3; then
        log_error "Python 3 not found"
        return 1
    fi
    
    local python_version
    python_version=$(python3 --version 2>&1)
    log_info "Python version: $python_version"
    
    # Check if we're in a virtual environment
    if [ -n "${VIRTUAL_ENV:-}" ]; then
        log_info "Virtual environment: $VIRTUAL_ENV"
    fi
    
    # Check Python path
    log_debug "Python path: $(which python3)"
    
    return 0
}

# Check application dependencies
check_dependencies() {
    log_info "Checking application dependencies..."
    
    # Check if autodoc package is installed
    if ! python3 -c "import autodoc" 2>/dev/null; then
        log_error "AutoDoc package not found"
        return 1
    fi
    
    log_success "AutoDoc package is available"
    
    # Check critical dependencies
    local critical_deps="fastapi uvicorn pydantic sqlalchemy alembic httpx"
    for dep in $critical_deps; do
        if ! python3 -c "import $dep" 2>/dev/null; then
            log_error "Critical dependency '$dep' not found"
            return 1
        fi
    done
    
    log_success "All critical dependencies are available"
    return 0
}

# Check file permissions
check_permissions() {
    log_info "Checking file permissions..."
    
    local workdir="${WORKDIR:-$DEFAULT_WORKDIR}"
    
    # Check if we can read the working directory
    if ! [ -r "$workdir" ]; then
        log_error "Cannot read working directory: $workdir"
        return 1
    fi
    
    # Check if we can write to the working directory
    if ! [ -w "$workdir" ]; then
        log_error "Cannot write to working directory: $workdir"
        return 1
    fi
    
    log_success "File permissions are correct"
    return 0
}

# =============================================================================
# Command Execution Functions
# =============================================================================

# Execute command with timeout
execute_with_timeout() {
    local timeout="${1:-$DEFAULT_TIMEOUT}"
    shift
    
    log_debug "Executing command with ${timeout}s timeout: $*"
    
    if command_exists timeout; then
        timeout "$timeout" "$@"
    else
        # Fallback for systems without timeout command
        "$@" &
        local pid=$!
        sleep "$timeout"
        if kill -0 "$pid" 2>/dev/null; then
            kill "$pid" 2>/dev/null || true
            log_error "Command timed out after ${timeout}s"
            return 124
        fi
        wait "$pid"
    fi
}

# Run tests
run_tests() {
    local test_type="${1:-all}"
    local timeout="${2:-300}"
    
    log_info "Running tests (type: $test_type, timeout: ${timeout}s)"
    
    case "$test_type" in
        "unit")
            execute_with_timeout "$timeout" python3 -m pytest tests/unit/ -v
            ;;
        "integration")
            execute_with_timeout "$timeout" python3 -m pytest tests/integration/ -v
            ;;
        "all")
            execute_with_timeout "$timeout" python3 -m pytest tests/ -v
            ;;
        "ci")
            if [ -f "./scripts/ci-test.sh" ]; then
                execute_with_timeout "$timeout" ./scripts/ci-test.sh
            else
                execute_with_timeout "$timeout" python3 -m pytest tests/ -v --maxfail=1
            fi
            ;;
        *)
            log_error "Unknown test type: $test_type"
            return 1
            ;;
    esac
}

# Run linting
run_linting() {
    local timeout="${1:-120}"
    
    log_info "Running linting checks (timeout: ${timeout}s)"
    
    # Run ruff if available
    if command_exists ruff; then
        log_info "Running ruff linting..."
        execute_with_timeout "$timeout" ruff check . || return 1
    fi
    
    # Run mypy if available
    if command_exists mypy; then
        log_info "Running mypy type checking..."
        execute_with_timeout "$timeout" mypy . || return 1
    fi
    
    log_success "All linting checks passed"
    return 0
}

# Run the application
run_application() {
    local app_type="${1:-server}"
    local timeout="${2:-0}"
    
    log_info "Starting application (type: $app_type)"
    
    case "$app_type" in
        "server")
            # Start FastAPI server
            log_info "Starting FastAPI server..."
            if [ "$timeout" -gt 0 ]; then
                execute_with_timeout "$timeout" python3 -m uvicorn autodoc.api.main:app --host 0.0.0.0 --port 8000
            else
                python3 -m uvicorn autodoc.api.main:app --host 0.0.0.0 --port 8000
            fi
            ;;
        "cli")
            # Run CLI command
            shift 2
            log_info "Running CLI command: $*"
            if [ "$timeout" -gt 0 ]; then
                execute_with_timeout "$timeout" python3 -m autodoc.cli.main "$@"
            else
                python3 -m autodoc.cli.main "$@"
            fi
            ;;
        "worker")
            # Start background worker
            log_info "Starting background worker..."
            if [ "$timeout" -gt 0 ]; then
                execute_with_timeout "$timeout" python3 -m autodoc.worker.main
            else
                python3 -m autodoc.worker.main
            fi
            ;;
        *)
            log_error "Unknown application type: $app_type"
            return 1
            ;;
    esac
}

# =============================================================================
# Signal Handling
# =============================================================================

# Setup signal handlers for graceful shutdown
setup_signal_handlers() {
    log_debug "Setting up signal handlers"
    
    # Function to handle shutdown signals
    handle_shutdown() {
        log_info "Received shutdown signal, cleaning up..."
        
        # Kill any background processes
        jobs -p | xargs -r kill 2>/dev/null || true
        
        # Wait for processes to finish
        wait 2>/dev/null || true
        
        log_info "Cleanup complete"
        exit 0
    }
    
    # Trap common shutdown signals
    trap handle_shutdown TERM INT QUIT
}

# =============================================================================
# Main Entry Point
# =============================================================================

main() {
    # Parse command line arguments
    local command="${1:-help}"
    shift || true
    
    # Set up logging
    LOG_LEVEL="${LOG_LEVEL:-$DEFAULT_LOG_LEVEL}"
    
    # Show startup information
    log_info "AutoDoc Entrypoint v${SCRIPT_VERSION}"
    log_info "Command: $command"
    log_info "User: $(whoami)"
    log_info "Working directory: $(pwd)"
    log_info "Container: $(is_container && echo 'yes' || echo 'no')"
    log_info "CI: $(is_ci && echo 'yes' || echo 'no')"
    
    # Setup signal handlers
    setup_signal_handlers
    
    # Perform health checks
    if ! check_python_env; then
        log_error "Python environment check failed"
        exit 1
    fi
    
    if ! check_dependencies; then
        log_error "Dependencies check failed"
        exit 1
    fi
    
    if ! check_permissions; then
        log_error "Permissions check failed"
        exit 1
    fi
    
    # Execute the requested command
    case "$command" in
        "test")
            run_tests "$@"
            ;;
        "lint")
            run_linting "$@"
            ;;
        "ci")
            log_info "Running CI pipeline..."
            run_linting 120 || exit 1
            run_tests "ci" 300 || exit 1
            log_success "CI pipeline completed successfully"
            ;;
        "server")
            run_application "server" 0
            ;;
        "cli")
            run_application "cli" 0 "$@"
            ;;
        "worker")
            run_application "worker" 0
            ;;
        "health")
            log_success "Health check passed"
            ;;
        "shell")
            log_info "Starting shell..."
            exec "$@"
            ;;
        "help"|"--help"|"-h")
            cat << EOF
AutoDoc Entrypoint Script

Usage: $SCRIPT_NAME <command> [options]

Commands:
    test [type] [timeout]    Run tests (unit|integration|all|ci)
    lint [timeout]          Run linting checks
    ci                      Run full CI pipeline
    server                  Start FastAPI server
    cli [args...]           Run CLI command
    worker                  Start background worker
    health                  Perform health check
    shell [cmd]             Start shell or run command
    help                    Show this help message

Environment Variables:
    LOG_LEVEL               Logging level (DEBUG|INFO|WARNING|ERROR)
    WORKDIR                 Working directory (default: /app)
    TIMEOUT                 Default timeout in seconds (default: 30)

Examples:
    $SCRIPT_NAME test unit 60
    $SCRIPT_NAME ci
    $SCRIPT_NAME server
    $SCRIPT_NAME cli analyze --file /path/to/file.py
    $SCRIPT_NAME shell bash

EOF
            ;;
        *)
            log_error "Unknown command: $command"
            log_info "Run '$SCRIPT_NAME help' for usage information"
            exit 1
            ;;
    esac
}

# =============================================================================
# Script Execution
# =============================================================================

# Only run main if script is executed directly
if [ "${0##*/}" = "entrypoint.sh" ] || [ "${0##*/}" = "entrypoint" ]; then
    main "$@"
fi
