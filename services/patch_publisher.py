"""Service for publishing patches to Confluence."""

import logging
from datetime import datetime, timezone
from sqlalchemy.orm import Session
import httpx
import os

from db.models import Patch

logger = logging.getLogger(__name__)


class PatchPublishError(Exception):
    """Raised when patch publishing fails."""


def publish_patch_to_confluence(
    db: Session,
    patch_id: int,
    approved_by: str = "system"
) -> Patch:
    """Publish a patch to Confluence.
    
    Args:
        db: Database session
        patch_id: ID of the patch to publish
        approved_by: Who approved the patch (system, manual, username)
        
    Returns:
        Updated Patch object with Applied status
        
    Raises:
        PatchPublishError: If publishing fails
    """
    # Get the patch
    patch = db.get(Patch, patch_id)
    if not patch:
        raise PatchPublishError(f"Patch {patch_id} not found")
    
    if patch.status == "Applied":
        logger.info(f"Patch {patch_id} already applied")
        return patch
    
    # Get Confluence credentials from environment
    confluence_url = os.getenv("CONFLUENCE_URL")
    confluence_email = os.getenv("CONFLUENCE_EMAIL")
    confluence_token = os.getenv("CONFLUENCE_TOKEN")
    
    if not all([confluence_url, confluence_email, confluence_token]):
        raise PatchPublishError("Confluence credentials not configured in environment")
    
    try:
        # Create HTTP client
        client = httpx.Client(
            base_url=f"{confluence_url}/wiki/rest/api",
            auth=(confluence_email, confluence_token),
            headers={
                "Accept": "application/json",
                "Content-Type": "application/json"
            },
            timeout=30.0
        )
        
        # Get current page version
        logger.info(f"Fetching Confluence page {patch.page_id}")
        response = client.get(
            f"/content/{patch.page_id}",
            params={"expand": "body.storage,version,space"}
        )
        response.raise_for_status()
        page_data = response.json()
        
        # Update the page
        logger.info(f"Publishing patch {patch_id} to page {patch.page_id}")
        update_response = client.put(
            f"/content/{patch.page_id}",
            json={
                "id": patch.page_id,
                "type": "page",
                "title": page_data["title"],
                "space": {"key": page_data["space"]["key"]},
                "body": {
                    "storage": {
                        "value": patch.diff_after,
                        "representation": "storage"
                    }
                },
                "version": {"number": page_data["version"]["number"] + 1}
            }
        )
        update_response.raise_for_status()
        
        # Update patch status in database
        patch.status = "Applied"
        patch.approved_by = approved_by
        patch.applied_at = datetime.now(timezone.utc)
        db.commit()
        
        logger.info(
            f"Successfully published patch {patch_id} to Confluence page {patch.page_id}",
            extra={
                "patch_id": patch_id,
                "page_id": patch.page_id,
                "approved_by": approved_by
            }
        )
        
        return patch
        
    except httpx.HTTPStatusError as e:
        error_msg = f"Confluence API error: {e.response.status_code} - {e.response.text}"
        logger.error(error_msg, extra={"patch_id": patch_id})
        raise PatchPublishError(error_msg) from e
    
    except Exception as e:
        error_msg = f"Failed to publish patch: {str(e)}"
        logger.error(error_msg, extra={"patch_id": patch_id})
        raise PatchPublishError(error_msg) from e
    
    finally:
        client.close()
