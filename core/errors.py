from typing import Any
from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from sqlalchemy.exc import IntegrityError, SQLAlchemyError


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
        # Skip error handling for OPTIONS requests (CORS preflight)
        if request.method == "OPTIONS":
            from fastapi.responses import Response
            return Response(status_code=200)
        return problem(
            422,
            "Validation error",
            str(exc),
            type_="urn:problem:validation",
            instance=str(request.url),
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_handler(request: Request, exc: StarletteHTTPException):
        # Skip error handling for OPTIONS requests (CORS preflight)
        if request.method == "OPTIONS":
            from fastapi.responses import Response
            return Response(status_code=200)
        return problem(
            exc.status_code,
            exc.detail or "HTTP error",
            "",
            type_="urn:problem:http",
            instance=str(request.url),
        )

    @app.exception_handler(IntegrityError)
    async def integrity_handler(request: Request, exc: IntegrityError):
        return problem(
            409,
            "Integrity error",
            str(exc.orig) if exc.orig else "Constraint violated",
            type_="urn:problem:integrity",
            instance=str(request.url),
        )

    @app.exception_handler(SQLAlchemyError)
    async def sa_handler(request: Request, exc: SQLAlchemyError):
        return problem(
            500,
            "Database error",
            str(exc),
            type_="urn:problem:database",
            instance=str(request.url),
        )
