"""Connections API router.

Implements:
- POST /api/connections - Save/update connection
- GET /api/connections - Get connection (without token)
- POST /api/connections/test - Test connection

Security requirements (FR-28, NFR-9):
- Never return token in responses
- Never log token values
- Always encrypt tokens at rest
"""

import logging
from datetime import datetime
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import select
import httpx

from db.session import get_db
from db.models import Connection
from schemas.connections import (
    ConnectionCreate,
    ConnectionOut,
    ConnectionTestRequest,
    ConnectionTestResponse,
)
from core.encryption import encrypt_token
from core.token_masking import mask_payload, mask_token

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/connections", tags=["connections"])


@router.post("", response_model=ConnectionOut, status_code=201)
def save_connection(
    payload: ConnectionCreate, db: Session = Depends(get_db)
) -> ConnectionOut:
    """
    Save or update a Confluence connection.

    Only one connection is allowed. If one exists, it will be updated.
    Token is encrypted before storage (NFR-9).
    """
    safe_payload = mask_payload(payload.model_dump())
    logger.info("Saving connection", extra={"payload": safe_payload})

    # Check if connection already exists (only one connection allowed)
    existing = db.execute(select(Connection).limit(1)).scalar_one_or_none()

    if existing:
        # Update existing connection
        existing.confluence_base_url = str(payload.confluence_base_url)
        existing.space_key = payload.space_key
        existing.username = payload.username
        existing.encrypted_token = encrypt_token(payload.api_token)
        db.commit()
        db.refresh(existing)
        return ConnectionOut.model_validate(existing)
    # Create new connection
    new_connection = Connection(
        confluence_base_url=str(payload.confluence_base_url),
        space_key=payload.space_key,
        username=payload.username,
        encrypted_token=encrypt_token(payload.api_token),
    )
    db.add(new_connection)
    db.commit()
    db.refresh(new_connection)
    return ConnectionOut.model_validate(new_connection)


@router.get("", response_model=ConnectionOut | None)
def get_connection(db: Session = Depends(get_db)) -> ConnectionOut | None:
    """
    Get the stored connection (if any).

    Never returns the token value (security requirement).
    """
    connection = db.execute(select(Connection).limit(1)).scalar_one_or_none()
    if not connection:
        return None
    return ConnectionOut.model_validate(connection)


def _normalize_base_url(url: str) -> str:
    """Normalize base URL by removing trailing slashes."""
    return str(url).rstrip("/")


@router.post("/test", response_model=ConnectionTestResponse)
async def test_connection(  # noqa: PLR0911
    payload: ConnectionTestRequest,
) -> ConnectionTestResponse:
    """
    Test a Confluence connection by making a harmless API call.

    Validates:
    - Base URL format
    - Token validity via GET /rest/api/space/{spaceKey}

    Security (FR-28, NFR-9):
    - Token is never logged
    - Only masked token appears in logs
    """
    base_url = _normalize_base_url(str(payload.confluence_base_url))
    space_key = payload.space_key
    username = payload.username
    token = payload.api_token

    # Mask token for logging (FR-28)
    masked_token = mask_token(token)
    safe_payload = {
        "confluence_base_url": base_url,
        "space_key": space_key,
        "username": username,
        "api_token": masked_token,
    }
    logger.info("Testing connection", extra={"payload": safe_payload})

    # Validate base URL format
    if not base_url.startswith(("http://", "https://")):
        return ConnectionTestResponse(
            ok=False,
            details="Invalid base URL format. Must start with http:// or https://",
            timestamp=datetime.utcnow(),
        )

    # Make test API call to Confluence
    # Confluence Cloud API requires Basic auth with email:token format
    import base64

    # Confluence API token authentication: Basic base64(email:token)
    auth_credentials = f"{username}:{token}"
    auth_string = base64.b64encode(auth_credentials.encode()).decode()

    # Confluence Cloud API path includes /wiki/rest/api
    test_url = f"{base_url}/wiki/rest/api/space/{space_key}"
    headers = {
        "Authorization": f"Basic {auth_string}",
        "Accept": "application/json",
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(test_url, headers=headers)

            if response.status_code == 200:
                logger.info(
                    "Connection test successful",
                    extra={"base_url": base_url, "space_key": space_key},
                )
                return ConnectionTestResponse(
                    ok=True,
                    details="Connection OK - Successfully connected to Confluence",
                    timestamp=datetime.utcnow(),
                )
            if response.status_code == 401:
                logger.warning(
                    "Connection test failed: Invalid token",
                    extra={"base_url": base_url, "space_key": space_key},
                )
                return ConnectionTestResponse(
                    ok=False,
                    details="Token invalid - please re-enter.",
                    timestamp=datetime.utcnow(),
                )
            if response.status_code == 404:
                logger.warning(
                    "Connection test failed: Space not found",
                    extra={"base_url": base_url, "space_key": space_key},
                )
                return ConnectionTestResponse(
                    ok=False,
                    details=f"Space '{space_key}' not found. Please check the space key.",
                    timestamp=datetime.utcnow(),
                )
            error_detail = "Unknown error"
            try:
                error_json = response.json()
                error_detail = error_json.get(
                    "message", error_json.get("error", str(response.text))
                )
            except Exception:
                error_detail = (
                    response.text[:200]
                    if response.text
                    else f"HTTP {response.status_code}"
                )

            logger.warning(
                "Connection test failed",
                extra={
                    "base_url": base_url,
                    "space_key": space_key,
                    "status_code": response.status_code,
                    "detail": error_detail,
                },
            )
            return ConnectionTestResponse(
                ok=False,
                details=f"Connection failed: {error_detail}",
                timestamp=datetime.utcnow(),
            )

    except httpx.TimeoutException:
        logger.exception(
            "Connection test timeout",
            extra={"base_url": base_url, "space_key": space_key},
        )
        return ConnectionTestResponse(
            ok=False,
            details="Connection timeout - Please check your base URL and network connection.",
            timestamp=datetime.utcnow(),
        )
    except httpx.ConnectError as e:
        logger.exception(
            "Connection test connection error",
            extra={"base_url": base_url, "space_key": space_key, "error": str(e)},
        )
        return ConnectionTestResponse(
            ok=False,
            details=f"Unable to connect to {base_url}. Please check the base URL.",
            timestamp=datetime.utcnow(),
        )
    except Exception as e:
        logger.exception(
            "Connection test unexpected error",
            extra={"base_url": base_url, "space_key": space_key, "error": str(e)},
        )
        return ConnectionTestResponse(
            ok=False,
            details=f"Unexpected error: {e!s}",
            timestamp=datetime.utcnow(),
        )
