from typing import Any
from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from core.security_middleware import mask_exception_message


def problem(
    status: int,
    title: str,
    detail: str,
    type_: str = "about:blank",
    instance: str = "",
) -> JSONResponse:
    payload: dict[str, Any] = {
        "type": type_,
        "title": title,
        "status": status,
        "detail": detail,
        "instance": instance,
    }
    return JSONResponse(
        content=payload,
        status_code=status,
        media_type="application/problem+json",
    )


def install_handlers(app):
    @app.exception_handler(RequestValidationError)
    async def validation_handler(request: Request, exc: RequestValidationError):
        return problem(
            422,
            "Validation error",
            str(exc),
            type_="urn:problem:validation",
            instance=str(request.url),
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_handler(request: Request, exc: StarletteHTTPException):
        return problem(
            exc.status_code,
            exc.detail or "HTTP error",
            "",
            type_="urn:problem:http",
            instance=str(request.url),
        )

    @app.exception_handler(IntegrityError)
    async def integrity_handler(request: Request, exc: IntegrityError):
        # Mask any sensitive data in error message (NFR-9)
        error_detail = mask_exception_message(exc.orig) if exc.orig else "Constraint violated"
        return problem(
            409,
            "Integrity error",
            error_detail,
            type_="urn:problem:integrity",
            instance=str(request.url),
        )

    @app.exception_handler(SQLAlchemyError)
    async def sa_handler(request: Request, exc: SQLAlchemyError):
        # Mask any sensitive data in error message (NFR-9)
        error_detail = mask_exception_message(exc)
        return problem(
            500,
            "Database error",
            error_detail,
            type_="urn:problem:database",
            instance=str(request.url),
        )
    
    @app.exception_handler(Exception)
    async def general_handler(request: Request, exc: Exception):
        # Catch-all handler - mask sensitive data in any exception
        error_detail = mask_exception_message(exc)
        return problem(
            500,
            "Internal server error",
            error_detail,
            type_="urn:problem:server",
            instance=str(request.url),
        )
