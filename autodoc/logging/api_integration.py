"""API integration helpers for structured logging.

Provides decorators and middleware for integrating structured logging
with API routes and request handling.
"""

import functools
import time
from typing import Any, Callable, Dict, Optional

from .correlation import set_request_context, generate_request_id
from .context import log_request_context
from .logger import get_logger


def log_api_call(
    logger_name: str = "autodoc.api",
    include_timing: bool = True,
    include_user: bool = True,
    include_metadata: bool = True,
):
    """Decorator for logging API calls with correlation IDs.
    
    Args:
        logger_name: Name of the logger to use
        include_timing: Whether to include request timing
        include_user: Whether to include user information
        include_metadata: Whether to include request metadata
        
    Returns:
        Decorated function
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            request_id = generate_request_id()
            logger = get_logger(logger_name)
            
            # Extract request information from args/kwargs
            request_info = {}
            user_id = None
            
            # Try to extract request object (common patterns)
            for arg in args:
                if hasattr(arg, 'method') and hasattr(arg, 'path'):
                    # Looks like a request object
                    request_info.update({
                        "method": getattr(arg, 'method', 'unknown'),
                        "path": getattr(arg, 'path', 'unknown'),
                        "user_agent": getattr(arg, 'headers', {}).get('User-Agent', 'unknown'),
                    })
                    # Try to get user ID from request
                    if include_user:
                        user_id = getattr(arg, 'user_id', None) or getattr(arg, 'user', {}).get('id')
                    break
            
            # Set up correlation context
            with log_request_context(
                logger_name,
                request_id=request_id,
                user_id=user_id,
                metadata=request_info if include_metadata else None,
            ) as ctx:
                start_time = time.time() if include_timing else None
                
                # Log request start
                ctx.log_event("api_call_start", f"API call started: {func.__name__}")
                
                try:
                    # Execute the function
                    result = func(*args, **kwargs)
                    
                    # Log successful completion
                    if include_timing and start_time:
                        duration = time.time() - start_time
                        ctx.log_event("api_call_success", 
                                    f"API call completed: {func.__name__}",
                                    duration_ms=round(duration * 1000, 2))
                    else:
                        ctx.log_event("api_call_success", 
                                    f"API call completed: {func.__name__}")
                    
                    return result
                    
                except Exception as e:
                    # Log error
                    if include_timing and start_time:
                        duration = time.time() - start_time
                        ctx.log_event("api_call_error", 
                                    f"API call failed: {func.__name__} - {str(e)}",
                                    duration_ms=round(duration * 1000, 2),
                                    error_type=type(e).__name__)
                    else:
                        ctx.log_event("api_call_error", 
                                    f"API call failed: {func.__name__} - {str(e)}",
                                    error_type=type(e).__name__)
                    raise
        
        return wrapper
    return decorator


def log_run_operation(
    logger_name: str = "autodoc.run",
    include_timing: bool = True,
    include_metadata: bool = True,
):
    """Decorator for logging CI/CD run operations with correlation IDs.
    
    Args:
        logger_name: Name of the logger to use
        include_timing: Whether to include operation timing
        include_metadata: Whether to include operation metadata
        
    Returns:
        Decorated function
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Extract run information from args/kwargs
            run_info = {}
            run_id = None
            
            # Try to extract run ID and metadata
            for arg in args:
                if hasattr(arg, 'run_id'):
                    run_id = arg.run_id
                if hasattr(arg, 'commit_sha'):
                    run_info['commit_sha'] = arg.commit_sha
                if hasattr(arg, 'repo'):
                    run_info['repo'] = arg.repo
                if hasattr(arg, 'branch'):
                    run_info['branch'] = arg.branch
            
            # Check kwargs for run information
            run_id = run_id or kwargs.get('run_id')
            if not run_id:
                run_id = f"run_{int(time.time())}"
            
            from .context import log_run_context
            
            with log_run_context(
                logger_name,
                run_id=run_id,
                metadata=run_info if include_metadata else None,
            ) as ctx:
                start_time = time.time() if include_timing else None
                
                # Log operation start
                ctx.log_event("operation_start", f"Operation started: {func.__name__}")
                
                try:
                    # Execute the function
                    result = func(*args, **kwargs)
                    
                    # Log successful completion
                    if include_timing and start_time:
                        duration = time.time() - start_time
                        ctx.log_event("operation_success", 
                                    f"Operation completed: {func.__name__}",
                                    duration_ms=round(duration * 1000, 2))
                    else:
                        ctx.log_event("operation_success", 
                                    f"Operation completed: {func.__name__}")
                    
                    return result
                    
                except Exception as e:
                    # Log error
                    if include_timing and start_time:
                        duration = time.time() - start_time
                        ctx.log_event("operation_error", 
                                    f"Operation failed: {func.__name__} - {str(e)}",
                                    duration_ms=round(duration * 1000, 2),
                                    error_type=type(e).__name__)
                    else:
                        ctx.log_event("operation_error", 
                                    f"Operation failed: {func.__name__} - {str(e)}",
                                    error_type=type(e).__name__)
                    raise
        
        return wrapper
    return decorator


class APILoggingMiddleware:
    """Middleware for automatic API request logging with correlation IDs."""
    
    def __init__(self, logger_name: str = "autodoc.api"):
        """Initialize the middleware.
        
        Args:
            logger_name: Name of the logger to use
        """
        self.logger = get_logger(logger_name)
    
    def __call__(self, request_handler: Callable) -> Callable:
        """Wrap a request handler with logging middleware."""
        @functools.wraps(request_handler)
        def wrapper(request, *args, **kwargs):
            request_id = generate_request_id()
            
            # Extract request information
            method = getattr(request, 'method', 'unknown')
            path = getattr(request, 'path', 'unknown')
            user_agent = getattr(request, 'headers', {}).get('User-Agent', 'unknown')
            user_id = getattr(request, 'user_id', None) or getattr(request, 'user', {}).get('id')
            
            request_info = {
                "method": method,
                "path": path,
                "user_agent": user_agent,
            }
            
            with log_request_context(
                self.logger.name,
                request_id=request_id,
                user_id=user_id,
                metadata=request_info,
            ) as ctx:
                start_time = time.time()
                
                # Log request start
                ctx.log_event("request_start", f"{method} {path}")
                
                try:
                    # Execute the request handler
                    response = request_handler(request, *args, **kwargs)
                    
                    # Log successful response
                    duration = time.time() - start_time
                    status_code = getattr(response, 'status_code', 200)
                    
                    ctx.log_event("request_success", 
                                f"{method} {path} completed",
                                status_code=status_code,
                                duration_ms=round(duration * 1000, 2))
                    
                    return response
                    
                except Exception as e:
                    # Log error response
                    duration = time.time() - start_time
                    ctx.log_event("request_error", 
                                f"{method} {path} failed - {str(e)}",
                                duration_ms=round(duration * 1000, 2),
                                error_type=type(e).__name__)
                    raise
        
        return wrapper


# Example usage for FastAPI
def fastapi_integration_example():
    """Example of integrating with FastAPI."""
    from fastapi import FastAPI, Request
    from .logger import setup_logging
    
    # Setup logging
    setup_logging(level="INFO", format_type="json")
    
    app = FastAPI()
    middleware = APILoggingMiddleware("autodoc.api")
    
    @app.get("/api/runs")
    @log_api_call("autodoc.api")
    async def get_runs(request: Request):
        """Get runs endpoint with logging."""
        return {"runs": []}
    
    @app.post("/api/runs/{run_id}/start")
    @log_api_call("autodoc.api")
    async def start_run(run_id: str, request: Request):
        """Start run endpoint with logging."""
        return {"run_id": run_id, "status": "started"}


# Example usage for Flask
def flask_integration_example():
    """Example of integrating with Flask."""
    from flask import Flask, request, g
    from .logger import setup_logging
    
    # Setup logging
    setup_logging(level="INFO", format_type="json")
    
    app = Flask(__name__)
    
    @app.before_request
    def before_request():
        """Set up correlation ID for each request."""
        g.request_id = generate_request_id()
        set_request_context(g.request_id)
    
    @app.route('/api/runs', methods=['GET'])
    @log_api_call("autodoc.api")
    def get_runs():
        """Get runs endpoint with logging."""
        return {"runs": []}
    
    @app.route('/api/runs/<run_id>/start', methods=['POST'])
    @log_api_call("autodoc.api")
    def start_run(run_id):
        """Start run endpoint with logging."""
        return {"run_id": run_id, "status": "started"}
