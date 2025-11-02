from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from core.config import settings
from core.logging import CorrelationIdMiddleware
from core.errors import install_handlers
from db.session import engine, Base
from api.routers import health, runs, rules, templates, patches, diff_parser


def create_app() -> FastAPI:
    app = FastAPI(
        title="AutoDoc API",
        version="0.1.0",
        docs_url="/docs",
        openapi_url="/openapi.json",
    )

    # DB: dev-time auto-create tables (hand off to Alembic os)
    Base.metadata.create_all(bind=engine)

    # CORS for Angular dev
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Request-ID"],
    )

    # Observability: correlation-id middleware
    app.add_middleware(CorrelationIdMiddleware)

    # Global error handlers (problem+json)
    install_handlers(app)

    # API routers under /api/v1
    api_prefix = "/api/v1"
    app.include_router(health.router, prefix=api_prefix)
    app.include_router(runs.router, prefix=api_prefix)
    app.include_router(rules.router, prefix=api_prefix)
    app.include_router(templates.router, prefix=api_prefix)
    app.include_router(patches.router, prefix=api_prefix)
    # Register diff parser at /api/diff (without v1 prefix as per FR-3/FR-24)
    app.include_router(diff_parser.router, prefix="/api")

    return app


app = create_app()
