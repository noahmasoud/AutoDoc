"""FastAPI router for Confluence connections.

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
from httpx import AsyncClient, HTTPStatusError

from db.session import get_db
from db.models import Connection
from schemas.connections import (
    ConnectionCreate,
    ConnectionOut,
    ConnectionTestRequest,
    ConnectionTestResponse,
)
from core.encryption import encrypt_token
from core.token_masking import mask_in_dict

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/connections", tags=["connections"])


@router.post("", response_model=ConnectionOut, status_code=201)
def save_connection(
    payload: ConnectionCreate,
    db: Session = Depends(get_db),
) -> ConnectionOut:
    """
    Save or update a Confluence connection.

    Only one connection is allowed. If a connection exists, it will be updated.
    Token is encrypted before storage (NFR-9).
    """
    # Check if connection exists
    existing = db.execute(
        select(Connection).where(
            Connection.confluence_base_url == payload.confluence_base_url
        )
    ).scalar_one_or_none()

    # Mask token in logs (FR-28)
    safe_payload = mask_in_dict(payload.model_dump())

    if existing:
        # Update existing connection
        logger.info(
            f"Updating connection for {payload.confluence_base_url}",
            extra={"payload": safe_payload},
        )
        existing.confluence_base_url = payload.confluence_base_url
        existing.space_key = payload.space_key
        existing.encrypted_token = encrypt_token(payload.api_token)
        existing.updated_at = datetime.utcnow()
        db.add(existing)
        db.flush()
        return existing

    # Create new connection
    logger.info(
        f"Creating new connection for {payload.confluence_base_url}",
        extra={"payload": safe_payload},
    )
    new_connection = Connection(
        confluence_base_url=payload.confluence_base_url,
        space_key=payload.space_key,
        encrypted_token=encrypt_token(payload.api_token),
    )
    db.add(new_connection)
    db.flush()
    return new_connection


@router.get("", response_model=ConnectionOut | None)
def get_connection(db: Session = Depends(get_db)) -> ConnectionOut | None:
    """
    Get the stored connection (if any).

    Never returns the token value (security requirement).
    """
    connection = db.execute(select(Connection)).scalar_one_or_none()
    if connection:
        logger.info(
            f"Retrieved connection for {connection.confluence_base_url}",
            extra={"connection_id": connection.id},
        )
    else:
        logger.info("No connection found")
    return connection


@router.post("/test", response_model=ConnectionTestResponse)
async def test_connection(
    payload: ConnectionTestRequest,
) -> ConnectionTestResponse:
    """
    Test a Confluence connection.

    Attempts to access the Confluence API with the provided credentials.
    Never logs the actual token (FR-28).
    """
    # Mask token in logs (FR-28)
    safe_payload = mask_in_dict(payload.model_dump())
    logger.info(
        f"Testing connection to {payload.confluence_base_url}",
        extra={"payload": safe_payload},
    )

    # Build API URL
    api_url = f"{payload.confluence_base_url}/rest/api/space/{payload.space_key}"

    try:
        async with AsyncClient(timeout=30.0) as client:
            # Confluence API typically uses Basic Auth with email:token
            # For API tokens, try using token as both username and password
            # Alternatively, use Bearer token in Authorization header
            # First try Basic Auth with token:token
            response = await client.get(
                api_url,
                auth=(payload.api_token, payload.api_token),
                headers={"Accept": "application/json"},
            )
            response.raise_for_status()

            logger.info(
                f"Connection test successful for {payload.confluence_base_url}",
                extra={"status_code": response.status_code},
            )

            return ConnectionTestResponse(
                success=True,
                message=f"Successfully connected to Confluence space '{payload.space_key}'",
            )

    except HTTPStatusError as e:
        error_msg = f"Confluence API error: {e.response.status_code}"
        if e.response.status_code == 401:
            error_msg = "Authentication failed. Please check your API token."
        elif e.response.status_code == 404:
            error_msg = f"Space '{payload.space_key}' not found."
        elif e.response.status_code == 403:
            error_msg = "Access forbidden. Please check your permissions."

        logger.warning(
            f"Connection test failed for {payload.confluence_base_url}",
            extra={"status_code": e.response.status_code, "error": error_msg},
        )

        return ConnectionTestResponse(success=False, message=error_msg)

    except Exception as e:
        error_msg = f"Connection test failed: {e!s}"
        logger.exception(
            f"Connection test error for {payload.confluence_base_url}",
            extra={"error": error_msg},
        )

        return ConnectionTestResponse(
            success=False,
            message=error_msg,
        )
