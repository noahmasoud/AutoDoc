"""Examples of using AutoDoc structured logging with correlation IDs.

This module demonstrates how to use the logging system in various scenarios
including CI/CD runs, API requests, and error handling.
"""

from typing import Dict, Any
from .logger import get_logger, setup_logging
from .context import log_run_context, log_request_context


def example_ci_cd_run():
    """Example of logging a CI/CD run with correlation IDs."""
    logger = get_logger("autodoc.run")
    
    with log_run_context(
        "autodoc.run",
        run_id="run_001",
        commit_sha="abc123def456",
        repo="example/repo",
        branch="feature/new-feature",
        pr_id="123",
        metadata={"trigger": "push", "workflow": "autodoc"}
    ) as ctx:
        # Log run start
        ctx.log_event("run_start", "CI/CD run started")
        
        # Log analysis phase
        ctx.log_event("analyzer_start", "Starting code analysis", file_count=5)
        ctx.log_event("analyzer_complete", "Analysis completed", findings_count=3)
        
        # Log patch generation
        ctx.log_event("patch_generated", "Patch created", 
                     patch_id="patch_001", page_id="page_001", template_id="api_template")
        
        # Log Confluence update
        ctx.log_event("confluence_update", "Confluence page updated", 
                     page_id="page_001", version=5, success=True)
        
        # Log run completion
        ctx.log_event("run_complete", "Run completed successfully", status="success")


def example_api_request():
    """Example of logging an API request with correlation IDs."""
    logger = get_logger("autodoc.api")
    
    with log_request_context(
        "autodoc.api",
        request_id="req_001",
        user_id="user_123",
        metadata={"endpoint": "/api/runs", "method": "GET"}
    ) as ctx:
        # Log request start
        ctx.log_event("request_start", "API request started")
        
        # Log authentication
        ctx.log_event("authentication", "User authenticated", 
                     user_id="user_123", success=True)
        
        # Log authorization
        ctx.log_event("authorization", "Access granted", 
                     resource="/api/runs", action="read", success=True)
        
        # Log validation
        ctx.log_event("validation", "Request validated", success=True)
        
        # Log response
        ctx.log_event("response", "Response generated", 
                     status_code=200, response_size=1024)
        
        # Log request completion
        ctx.log_event("request_complete", "Request completed successfully", status="success")


def example_error_handling():
    """Example of error handling with structured logging."""
    logger = get_logger("autodoc.error")
    
    try:
        # Simulate an error
        raise ConnectionError("Failed to connect to Confluence API")
    except Exception as e:
        logger.exception(
            "Connection error occurred",
            extra={
                "service": "confluence",
                "error_type": type(e).__name__,
                "error_message": str(e),
                "retry_count": 3,
                "max_retries": 5
            }
        )


def example_structured_data():
    """Example of logging with rich structured data."""
    logger = get_logger("autodoc.structured")
    
    # Log with complex structured data
    logger.info(
        "Analysis results",
        extra={
            "event_type": "analysis_complete",
            "metrics": {
                "files_analyzed": 15,
                "symbols_found": 42,
                "breaking_changes": 2,
                "processing_time_ms": 1250
            },
            "changes": [
                {"file": "src/api.py", "type": "function_added", "symbol": "new_function"},
                {"file": "src/models.py", "type": "parameter_removed", "symbol": "old_function"}
            ],
            "tags": ["api", "breaking-change", "feature"]
        }
    )


def example_custom_correlation():
    """Example of using custom correlation IDs."""
    from .correlation import CorrelationContextManager
    
    logger = get_logger("autodoc.custom")
    
    with CorrelationContextManager(
        correlation_id="custom_corr_123",
        run_id="custom_run_456",
        metadata={"custom_field": "custom_value", "priority": "high"}
    ):
        logger.info("Message with custom correlation ID")
        logger.info("Another message with same correlation context")


def demo_all_examples():
    """Run all logging examples."""
    print("🧪 AutoDoc Logging Examples")
    print("=" * 50)
    
    # Setup JSON logging for demo
    setup_logging(level="INFO", format_type="json")
    
    print("\n1. CI/CD Run Logging Example:")
    example_ci_cd_run()
    
    print("\n2. API Request Logging Example:")
    example_api_request()
    
    print("\n3. Error Handling Example:")
    example_error_handling()
    
    print("\n4. Structured Data Example:")
    example_structured_data()
    
    print("\n5. Custom Correlation Example:")
    example_custom_correlation()
    
    print("\n✅ All examples completed - check JSON output above")


if __name__ == "__main__":
    demo_all_examples()
