"""Service for publishing LLM summaries to Confluence pages.

This module handles the automatic publishing of LLM-generated summaries to
Confluence pages, supporting multiple publishing strategies.
"""

import json
import logging
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session
from sqlalchemy import select

from db.models import Patch, Rule, Run
from services.confluence_client import ConfluenceClient
from services.confluence_publisher import ConfluencePublisher
from services.confluence_format_converter import format_llm_summary_for_confluence

logger = logging.getLogger(__name__)


def publish_llm_summary_to_confluence(
    db: Session,
    run_id: int,
    strategy: str = "append_to_patches",
) -> dict[str, Any]:
    """Publish LLM summary to Confluence using specified strategy.

    Supported strategies:
    - "append_to_patches": Append summary to each patch's Confluence page (default)
    - "create_page": Create a dedicated summary page for the run

    Args:
        db: Database session
        run_id: ID of the run to publish summary for
        strategy: Publishing strategy to use

    Returns:
        Dictionary with publishing results:
        {
            "success": bool,
            "strategy": str,
            "pages_updated": list[str],
            "errors": list[str]
        }

    Raises:
        ValueError: If run not found or strategy is invalid
        FileNotFoundError: If LLM summary artifact doesn't exist
    """
    # Verify run exists
    run = db.get(Run, run_id)
    if not run:
        raise ValueError(f"Run {run_id} not found")

    # Check if this is a dry-run
    if run.is_dry_run:
        logger.info(
            f"Skipping Confluence publishing for LLM summary (dry-run mode) for run {run_id}",
            extra={"run_id": run_id, "is_dry_run": True},
        )
        return {
            "success": True,
            "strategy": strategy,
            "pages_updated": [],
            "skipped": True,
            "reason": "dry_run",
        }

    # Load LLM summary artifact
    summary_path = Path("artifacts") / str(run_id) / "llm_summary.json"
    if not summary_path.exists():
        raise FileNotFoundError(
            f"LLM summary artifact not found for run {run_id} at {summary_path}. "
            "Please generate the summary first using export_llm_summary_artifact."
        )

    try:
        with summary_path.open("r", encoding="utf-8") as f:
            summary_artifact = json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        raise ValueError(f"Failed to read LLM summary artifact: {e}") from e

    summary_data = summary_artifact.get("summary", {})
    if not summary_data:
        raise ValueError(f"LLM summary artifact for run {run_id} is empty or invalid")

    # Convert summary to Confluence Storage Format
    summary_xml = format_llm_summary_for_confluence(summary_data)

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
        # If CONFLUENCE_USERNAME is not set, we cannot authenticate properly
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
        logger.exception(
            f"Failed to initialize Confluence client for run {run_id}: {e}",
            extra={"run_id": run_id},
        )
        return {
            "success": False,
            "strategy": strategy,
            "pages_updated": [],
            "errors": [f"Confluence client initialization failed: {e}"],
        }

    try:
        if strategy == "append_to_patches":
            return _append_summary_to_patch_pages(db, run_id, summary_xml, publisher)
        if strategy == "create_page":
            return _create_summary_page(
                db, run_id, summary_artifact, summary_xml, publisher, client
            )
        raise ValueError(
            f"Invalid strategy: {strategy}. Must be 'append_to_patches' or 'create_page'"
        )
    finally:
        client.close()


def _append_summary_to_patch_pages(
    db: Session,
    run_id: int,
    summary_xml: str,
    publisher: ConfluencePublisher,
) -> dict[str, Any]:
    """Append LLM summary to each patch's Confluence page.

    Args:
        db: Database session
        run_id: Run ID
        summary_xml: Summary content in Confluence Storage Format
        publisher: ConfluencePublisher instance

    Returns:
        Dictionary with publishing results
    """
    # Get all patches for the run
    patches = (
        db.execute(select(Patch).where(Patch.run_id == run_id).order_by(Patch.id))
        .scalars()
        .all()
    )

    if not patches:
        logger.warning(f"No patches found for run {run_id}, cannot append summary")
        return {
            "success": False,
            "strategy": "append_to_patches",
            "pages_updated": [],
            "errors": ["No patches found for run"],
        }

    pages_updated = []
    errors = []

    for patch in patches:
        try:
            # Get the rule to find page title
            rule = (
                db.execute(select(Rule).where(Rule.page_id == patch.page_id))
                .scalars()
                .first()
            )

            if not rule:
                errors.append(
                    f"Rule not found for patch {patch.id} (page_id: {patch.page_id})"
                )
                continue

            # Get current page content
            current_page = publisher._client.get_page(patch.page_id)  # noqa: SLF001
            if not current_page:
                errors.append(f"Page {patch.page_id} not found")
                continue

            current_content = (
                current_page.get("body", {}).get("storage", {}).get("value", "")
            )

            # Append summary section to existing content
            # Use a horizontal rule as separator
            separator = "<hr/>"
            new_content = f"{current_content}{separator}{summary_xml}"

            # Update the page using ConfluenceClient directly (matching patches.py pattern)
            # Note: ConfluenceClient.update_page expects keyword arguments, not a dict
            result = publisher._client.update_page(  # noqa: SLF001
                page_id=patch.page_id,
                title=f"AutoDoc: {rule.name}",
                body=new_content,
                representation="storage",
                minor_edit=False,
                message="AutoDoc: Added LLM-generated summary",
            )

            pages_updated.append(patch.page_id)
            logger.info(
                f"Successfully appended LLM summary to page {patch.page_id} for run {run_id}",
                extra={
                    "run_id": run_id,
                    "patch_id": patch.id,
                    "page_id": patch.page_id,
                    "version": result.get("version"),
                },
            )

        except Exception as e:
            error_msg = f"Failed to append summary to page {patch.page_id}: {e}"
            errors.append(error_msg)
            logger.exception(
                error_msg,
                extra={
                    "run_id": run_id,
                    "patch_id": patch.id,
                    "page_id": patch.page_id,
                },
            )

    return {
        "success": len(errors) == 0,
        "strategy": "append_to_patches",
        "pages_updated": pages_updated,
        "errors": errors,
    }


def _create_summary_page(
    db: Session,
    run_id: int,
    summary_artifact: dict[str, Any],
    summary_xml: str,
    publisher: ConfluencePublisher,
    client: ConfluenceClient,
) -> dict[str, Any]:
    """Create a dedicated Confluence page for the LLM summary.

    Args:
        db: Database session
        run_id: Run ID
        summary_artifact: Full summary artifact data
        summary_xml: Summary content in Confluence Storage Format
        publisher: ConfluencePublisher instance
        client: ConfluenceClient instance

    Returns:
        Dictionary with publishing results
    """
    run = db.get(Run, run_id)
    if not run:
        raise ValueError(f"Run {run_id} not found")

    from autodoc.config.settings import get_settings

    settings = get_settings()
    space_key = settings.confluence.space_key
    if not space_key:
        return {
            "success": False,
            "strategy": "create_page",
            "pages_updated": [],
            "errors": ["Confluence space_key not configured"],
        }

    try:
        # Create page title
        page_title = (
            f"{settings.confluence.page_prefix} Summary - Run {run_id} "
            f"({run.branch} - {run.commit_sha[:8]})"
        )

        # Create the page
        result = client.create_page(
            space_key=space_key,
            title=page_title,
            body=summary_xml,
            representation="storage",
        )

        page_id = result.get("id")
        logger.info(
            f"Successfully created LLM summary page {page_id} for run {run_id}",
            extra={
                "run_id": run_id,
                "page_id": page_id,
                "page_title": page_title,
            },
        )

        return {
            "success": True,
            "strategy": "create_page",
            "pages_updated": [page_id] if page_id else [],
            "page_id": page_id,
            "page_title": page_title,
            "errors": [],
        }

    except Exception as e:
        error_msg = f"Failed to create summary page for run {run_id}: {e}"
        logger.exception(error_msg, extra={"run_id": run_id})
        return {
            "success": False,
            "strategy": "create_page",
            "pages_updated": [],
            "errors": [error_msg],
        }
