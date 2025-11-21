"""Connections API router.

Implements:
- POST /api/connections - Save/update connection
- GET /api/connections - Get connection (without token)

Security requirements (FR-28, NFR-9):
- Never return token in responses
- Never log token values
- Always encrypt tokens at rest
"""

import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select

from db.session import get_db
from db.models import Connection
from schemas.connections import ConnectionCreate, ConnectionOut
from core.encryption import encrypt_token, decrypt_token
from core.token_masking import mask_payload

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/connections", tags=["connections"])


@router.post("", response_model=ConnectionOut, status_code=201)
def save_connection(payload: ConnectionCreate, db: Session = Depends(get_db)) -> ConnectionOut:
    """
    Save or update a Confluence connection.
    
    Only one connection is allowed. If one exists, it will be updated.
    Token is encrypted before storage (NFR-9).
    """
    safe_payload = mask_payload(payload.model_dump())
    logger.info("Saving connection", extra={"payload": safe_payload})

    # Check if connection already exists
    existing = db.execute(select(Connection)).scalar_one_or_none()

    if existing:
        # Update existing connection
        existing.confluence_base_url = str(payload.confluence_base_url)
        existing.space_key = payload.space_key
        existing.encrypted_token = encrypt_token(payload.api_token)
        db.commit()
        db.refresh(existing)
        return ConnectionOut.model_validate(existing)
    else:
        # Create new connection
        new_connection = Connection(
            confluence_base_url=str(payload.confluence_base_url),
            space_key=payload.space_key,
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
    connection = db.execute(select(Connection)).scalar_one_or_none()
    if not connection:
        return None
    return ConnectionOut.model_validate(connection)

