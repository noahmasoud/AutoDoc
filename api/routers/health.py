from datetime import datetime, UTC
from fastapi import APIRouter
from importlib.metadata import version, PackageNotFoundError

router = APIRouter()


def _app_version() -> str:
    try:
        return version("autodoc-service")  # fallback if you publish; else:
    except PackageNotFoundError:
        return "0.1.0"


@router.get("/health")
def health():
    return {
        "status": "ok",
        "version": _app_version(),
        "timestamp": datetime.now(UTC).isoformat(),
    }
