"""LLM configuration API router.

Implements:
- POST /api/llm-config - Save/update LLM configuration
- GET /api/llm-config - Get LLM configuration (without API key)
- POST /api/llm-config/test - Test LLM configuration

Security requirements (FR-28, NFR-9):
- Never return API key in responses
- Never log API key values
- Always encrypt API keys at rest
"""

import logging
from datetime import datetime
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import select
import anthropic

from db.session import get_db
from db.models import LLMConfig
from schemas.llm_config import (
    LLMConfigCreate,
    LLMConfigOut,
    LLMConfigTestRequest,
    LLMConfigTestResponse,
)
from core.encryption import encrypt_token, decrypt_token
from core.token_masking import mask_payload, mask_token

logger = logging.getLogger(__name__)

# Try to import OpenAI, but make it optional
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    logger.warning("OpenAI package not installed. OpenAI models will not be available.")


def _is_openai_model(model: str) -> bool:
    """Check if the model is an OpenAI model."""
    return model.startswith(("gpt-", "o1-", "o3-"))

router = APIRouter(prefix="/llm-config", tags=["llm-config"])


@router.post("", response_model=LLMConfigOut, status_code=201)
def save_llm_config(
    payload: LLMConfigCreate, db: Session = Depends(get_db)
) -> LLMConfigOut:
    """
    Save or update LLM configuration.

    Only one LLM configuration is allowed. If one exists, it will be updated.
    API key is encrypted before storage (NFR-9).
    """
    safe_payload = mask_payload(payload.model_dump())
    logger.info("Saving LLM configuration", extra={"payload": safe_payload})

    # Check if LLM config already exists (only one config allowed)
    existing = db.execute(select(LLMConfig).limit(1)).scalar_one_or_none()

    if existing:
        # Update existing configuration
        existing.model = payload.model
        existing.encrypted_api_key = encrypt_token(payload.api_key)
        db.commit()
        db.refresh(existing)
        return LLMConfigOut.model_validate(existing)
    # Create new configuration
    new_config = LLMConfig(
        model=payload.model,
        encrypted_api_key=encrypt_token(payload.api_key),
    )
    db.add(new_config)
    db.commit()
    db.refresh(new_config)
    return LLMConfigOut.model_validate(new_config)


@router.get("", response_model=LLMConfigOut | None)
def get_llm_config(db: Session = Depends(get_db)) -> LLMConfigOut | None:
    """
    Get the stored LLM configuration (if any).

    Never returns the API key value (security requirement).
    """
    config = db.execute(select(LLMConfig).limit(1)).scalar_one_or_none()
    if not config:
        return None
    return LLMConfigOut.model_validate(config)


@router.post("/test-saved", response_model=LLMConfigTestResponse)
async def test_saved_llm_config(
    db: Session = Depends(get_db),
) -> LLMConfigTestResponse:
    """
    Test the saved LLM configuration using the stored API key and model.

    This endpoint uses the configuration saved in the database to test the connection.
    """
    config = db.execute(select(LLMConfig).limit(1)).scalar_one_or_none()
    if not config:
        return LLMConfigTestResponse(
            ok=False,
            details="No LLM configuration found. Please save a configuration first.",
            timestamp=datetime.utcnow(),
        )

    model = config.model
    api_key = decrypt_token(config.encrypted_api_key)

    # Mask API key for logging (FR-28)
    masked_key = mask_token(api_key)
    logger.info(
        "Testing saved LLM configuration",
        extra={"model": model, "api_key": masked_key},
    )

    # Route to appropriate API based on model
    if _is_openai_model(model):
        return _test_openai_config(model, api_key)
    else:
        return _test_anthropic_config(model, api_key)


@router.post("/test", response_model=LLMConfigTestResponse)
async def test_llm_config(
    payload: LLMConfigTestRequest,
) -> LLMConfigTestResponse:
    """
    Test LLM configuration by making a simple API call.

    Validates:
    - API key validity
    - Model availability

    Security (FR-28, NFR-9):
    - API key is never logged
    - Only masked key appears in logs
    """
    model = payload.model
    api_key = payload.api_key

    # Mask API key for logging (FR-28)
    masked_key = mask_token(api_key)
    safe_payload = {
        "model": model,
        "api_key": masked_key,
    }
    logger.info("Testing LLM configuration", extra={"payload": safe_payload})

    # Route to appropriate API based on model
    if _is_openai_model(model):
        return _test_openai_config(model, api_key)
    else:
        return _test_anthropic_config(model, api_key)


def _test_openai_config(model: str, api_key: str) -> LLMConfigTestResponse:
    """Test OpenAI configuration."""
    if not OPENAI_AVAILABLE:
        return LLMConfigTestResponse(
            ok=False,
            details="OpenAI package is not installed. Please install it with: pip install openai",
            timestamp=datetime.utcnow(),
        )
    
    try:
        client = openai.OpenAI(api_key=api_key)
        # Make a simple test call with minimal tokens
        response = client.chat.completions.create(
            model=model,
            max_tokens=10,
            messages=[{"role": "user", "content": "Hi"}],
        )

        logger.info(
            "LLM configuration test successful",
            extra={"model": model, "provider": "openai"},
        )
        return LLMConfigTestResponse(
            ok=True,
            details="LLM configuration OK - Successfully connected to OpenAI API",
            timestamp=datetime.utcnow(),
        )

    except openai.APIError as e:
        error_msg = f"OpenAI API returned error: {e.status_code if hasattr(e, 'status_code') else 'unknown'} - {str(e)}"
        
        if hasattr(e, "status_code"):
            if e.status_code == 401:
                logger.warning(
                    "LLM configuration test failed: Invalid API key",
                    extra={"model": model, "provider": "openai"},
                )
                return LLMConfigTestResponse(
                    ok=False,
                    details="API key invalid - please re-enter.",
                    timestamp=datetime.utcnow(),
                )
            if e.status_code == 400:
                logger.warning(
                    "LLM configuration test failed: Invalid model",
                    extra={"model": model, "provider": "openai"},
                )
                return LLMConfigTestResponse(
                    ok=False,
                    details=f"Model '{model}' is invalid or not available. Please check the model name.",
                    timestamp=datetime.utcnow(),
                )
            if e.status_code == 429:
                logger.warning(
                    "LLM configuration test failed: Rate limit",
                    extra={"model": model, "provider": "openai"},
                )
                return LLMConfigTestResponse(
                    ok=False,
                    details="Rate limit exceeded. Please try again later.",
                    timestamp=datetime.utcnow(),
                )
        
        logger.warning(
            "LLM configuration test failed",
            extra={"model": model, "provider": "openai", "error": error_msg},
        )
        return LLMConfigTestResponse(
            ok=False,
            details=f"API error: {error_msg}",
            timestamp=datetime.utcnow(),
        )

    except Exception as e:
        logger.exception(
            "LLM configuration test unexpected error",
            extra={"model": model, "provider": "openai", "error": str(e)},
        )
        return LLMConfigTestResponse(
            ok=False,
            details=f"Unexpected error: {e!s}",
            timestamp=datetime.utcnow(),
        )


def _test_anthropic_config(model: str, api_key: str) -> LLMConfigTestResponse:
    """Test Anthropic configuration."""
    try:
        client = anthropic.Anthropic(api_key=api_key)
        # Make a simple test call with minimal tokens
        message = client.messages.create(
            model=model,
            max_tokens=10,
            messages=[{"role": "user", "content": "Hi"}],
        )

        logger.info(
            "LLM configuration test successful",
            extra={"model": model, "provider": "anthropic"},
        )
        return LLMConfigTestResponse(
            ok=True,
            details="LLM configuration OK - Successfully connected to Anthropic API",
            timestamp=datetime.utcnow(),
        )

    except anthropic.APIError as e:
        error_detail = e.response.json() if hasattr(e.response, "json") else str(e)
        error_msg = f"LLM API returned error: {e.status_code} - {error_detail}"
        
        if e.status_code == 401:
            logger.warning(
                "LLM configuration test failed: Invalid API key",
                extra={"model": model},
            )
            return LLMConfigTestResponse(
                ok=False,
                details="API key invalid - please re-enter.",
                timestamp=datetime.utcnow(),
            )
        if e.status_code == 400:
            logger.warning(
                "LLM configuration test failed: Invalid model",
                extra={"model": model},
            )
            return LLMConfigTestResponse(
                ok=False,
                details=f"Model '{model}' is invalid or not available. Please check the model name.",
                timestamp=datetime.utcnow(),
            )
        if e.status_code == 429:
            logger.warning(
                "LLM configuration test failed: Rate limit",
                extra={"model": model},
            )
            return LLMConfigTestResponse(
                ok=False,
                details="Rate limit exceeded. Please try again later.",
                timestamp=datetime.utcnow(),
            )
        logger.warning(
            "LLM configuration test failed",
            extra={"model": model, "status_code": e.status_code, "detail": error_detail},
        )
        return LLMConfigTestResponse(
            ok=False,
            details=f"API error: {error_msg}",
            timestamp=datetime.utcnow(),
        )

    except Exception as e:
        logger.exception(
            "LLM configuration test unexpected error",
            extra={"model": model, "error": str(e)},
        )
        return LLMConfigTestResponse(
            ok=False,
            details=f"Unexpected error: {e!s}",
            timestamp=datetime.utcnow(),
        )

