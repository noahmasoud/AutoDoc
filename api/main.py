from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from core.config import settings
from core.logging import CorrelationIdMiddleware
from core.errors import install_handlers
from db.session import engine, Base
from api.routers import (
    health,
    runs,
    rules,
    templates,
    patches,
    diff_parser,
    pages,
    connections,
    auth,
    prompts,
)


def create_app() -> FastAPI:
    app = FastAPI(
        title="AutoDoc API",
        version="0.1.0",
        docs_url="/docs",
        openapi_url="/openapi.json",
    )

    # DB: dev-time auto-create tables (hand off to Alembic os)
    # Skip for in-memory SQLite (used in tests) to avoid conflicts with test fixtures
    db_url = str(engine.url)
    if ":memory:" not in db_url:
        Base.metadata.create_all(bind=engine)

    # Global error handlers (problem+json) - install before CORS to avoid interfering
    install_handlers(app)

    # CORS for Angular dev - must be added AFTER error handlers but handles preflight automatically
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
        allow_headers=["*"],
        expose_headers=["X-Request-ID"],
    )

    # Observability: correlation-id middleware (after CORS)
    app.add_middleware(CorrelationIdMiddleware)

    # API routers under /api/v1
    api_prefix = "/api/v1"
    app.include_router(health.router, prefix=api_prefix)
    app.include_router(runs.router, prefix=api_prefix)
    app.include_router(rules.router, prefix=api_prefix)
    app.include_router(templates.router, prefix=api_prefix)
    app.include_router(patches.router, prefix=api_prefix)
    app.include_router(pages.router, prefix=api_prefix)
    app.include_router(prompts.router, prefix=api_prefix)
    # Register diff parser at /api/diff (without v1 prefix as per FR-3/FR-24)
    app.include_router(diff_parser.router, prefix="/api")
    # Register connections at /api/connections (without v1 prefix as per requirements)
    app.include_router(connections.router, prefix="/api")
    # Register auth at /api/login (without v1 prefix for consistency with frontend)
    app.include_router(auth.router, prefix="/api")

    return app


app = create_app()
