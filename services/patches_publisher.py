"""Service for publishing patches to Confluence pages.

This module handles the automatic publishing of patches to Confluence pages,
used as a fallback when LLM summary generation fails.
"""

import logging
from datetime import UTC, datetime
from typing import Any

from sqlalchemy.orm import Session
from sqlalchemy import select

from db.models import Patch, Rule, Run
from services.confluence_client import ConfluenceClient
from services.confluence_publisher import ConfluencePublisher
from services.confluence_content_modifier import ConfluenceContentModifier

logger = logging.getLogger(__name__)


def publish_patches_to_confluence(
    db: Session,
    run_id: int,
) -> dict[str, Any]:
    """Publish all patches for a run to Confluence.

    This function is used as a fallback when LLM summary generation fails.
    It publishes the raw patch content (diff_after) to each patch's Confluence page.

    Args:
        db: Database session
        run_id: ID of the run to publish patches for

    Returns:
        Dictionary with publishing results:
        {
            "success": bool,
            "patches_published": int,
            "pages_updated": list[str],
            "errors": list[str]
        }

    Raises:
        ValueError: If run not found
    """
    # Verify run exists
    run = db.get(Run, run_id)
    if not run:
        raise ValueError(f"Run {run_id} not found")

    # Check if this is a dry-run
    if run.is_dry_run:
        logger.info(
            f"Skipping Confluence publishing for patches (dry-run mode) for run {run_id}",
            extra={"run_id": run_id, "is_dry_run": True},
        )
        return {
            "success": True,
            "patches_published": 0,
            "pages_updated": [],
            "skipped": True,
            "reason": "dry_run",
        }

    # Get all patches for the run
    patches = (
        db.execute(select(Patch).where(Patch.run_id == run_id).order_by(Patch.id))
        .scalars()
        .all()
    )

    if not patches:
        logger.warning(f"No patches found for run {run_id}, nothing to publish")
        return {
            "success": False,
            "patches_published": 0,
            "pages_updated": [],
            "errors": ["No patches found for run"],
        }

    # Initialize Confluence client and publisher using database connection
    try:
        # Load connection from database
        from db.models import Connection
        from core.encryption import decrypt_token
        from autodoc.config.settings import ConfluenceSettings, get_settings

        connection = db.execute(select(Connection).limit(1)).scalar_one_or_none()
        if not connection:
            raise ValueError(
                "No Confluence connection found. Please configure a connection first."
            )

        # Decrypt the token
        try:
            decrypted_token = decrypt_token(connection.encrypted_token)
        except Exception as e:
            raise ValueError(f"Failed to decrypt connection token: {e}") from e

        # Get app settings for timeout and max_retries
        app_settings = get_settings()

        # Create ConfluenceSettings from database connection
        # For Confluence API tokens, username must be an email address, not the token
        username = app_settings.confluence.username
        if not username:
            raise ValueError(
                "CONFLUENCE_USERNAME is required for Confluence API authentication. "
                "Please set CONFLUENCE_USERNAME in your .env file with your Confluence email address."
            )

        confluence_settings = ConfluenceSettings(
            url=connection.confluence_base_url,
            username=username,
            token=decrypted_token,
            space_key=connection.space_key,
            timeout=app_settings.confluence.timeout,
            max_retries=app_settings.confluence.max_retries,
        )

        # Get Confluence client and publisher with database connection settings
        client = ConfluenceClient(settings=confluence_settings)
        publisher = ConfluencePublisher(client)
    except Exception as e:
        logger.error(
            f"Failed to initialize Confluence client for run {run_id}: {e}",
            extra={"run_id": run_id},
            exc_info=True,
        )
        return {
            "success": False,
            "patches_published": 0,
            "pages_updated": [],
            "errors": [f"Confluence client initialization failed: {e}"],
        }

    pages_updated = []
    errors = []
    patches_published = 0

    try:
        for patch in patches:
            # Skip ERROR patches
            if patch.status == "ERROR":
                logger.debug(
                    f"Skipping ERROR patch {patch.id} for run {run_id}",
                    extra={"run_id": run_id, "patch_id": patch.id},
                )
                continue

            try:
                # Get the rule to find page title
                rule = (
                    db.execute(
                        select(Rule).where(Rule.page_id == patch.page_id)
                    )
                    .scalars()
                    .first()
                )

                if not rule:
                    errors.append(
                        f"Rule not found for patch {patch.id} (page_id: {patch.page_id})"
                    )
                    continue

                # Get current page content to apply strategy
                current_page = client.get_page(patch.page_id)
                current_content = ""
                if current_page:
                    current_content = (
                        current_page.get("body", {})
                        .get("storage", {})
                        .get("value", "")
                    )

                # Get strategy from rule (default to "replace" for backward compatibility)
                strategy = getattr(rule, "update_strategy", "replace") or "replace"

                # Apply strategy to modify content
                modified_content = ConfluenceContentModifier.apply_strategy(
                    current_content=current_content,
                    new_content=patch.diff_after,
                    strategy=strategy,
                    separator="<hr/>",  # Default separator for append
                )

                # Update the Confluence page with modified content
                result = client.update_page(
                    page_id=patch.page_id,
                    title=f"AutoDoc: {rule.name}",
                    body=modified_content,
                    representation="storage",
                )

                # Update patch status to Applied
                patch.status = "Applied"
                patch.applied_at = datetime.now(UTC)
                db.commit()

                pages_updated.append(patch.page_id)
                patches_published += 1

                logger.info(
                    f"Successfully published patch {patch.id} to page {patch.page_id} for run {run_id}",
                    extra={
                        "run_id": run_id,
                        "patch_id": patch.id,
                        "page_id": patch.page_id,
                        "version": result.get("version"),
                    },
                )

            except Exception as e:
                error_msg = f"Failed to publish patch {patch.id} to page {patch.page_id}: {e}"
                errors.append(error_msg)
                logger.error(
                    error_msg,
                    extra={"run_id": run_id, "patch_id": patch.id, "page_id": patch.page_id},
                    exc_info=True,
                )
                # Mark patch as ERROR
                patch.status = "ERROR"
                patch.error_message = {"error": str(e), "type": type(e).__name__}
                db.commit()

    finally:
        client.close()

    return {
        "success": len(errors) == 0,
        "patches_published": patches_published,
        "pages_updated": pages_updated,
        "errors": errors,
    }

