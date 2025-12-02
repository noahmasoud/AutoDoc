"""Service for generating patches from file changes using rule engine.

This module integrates the rule engine to map changed files to Confluence pages
and generate patches for documentation updates using templates (FR-10).
"""

import logging
from collections import defaultdict
from typing import Any
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import select

from db.models import Change, Patch, PythonSymbol, Rule, Run
from services.change_persister import get_changes_for_run
from services.rule_engine import resolve_target_page
from autodoc.templates.engine import TemplateEngine

logger = logging.getLogger(__name__)


class PatchGenerationError(Exception):
    """Raised when patch generation fails."""


def generate_patches_for_run(  # noqa: PLR0915
    db: Session,
    run_id: int,
) -> list[Patch]:
    """Generate patches for a run based on analyzer findings and mapping rules.

    This function implements FR-10: Generate patches using templates (Markdown or Storage Format).
    It:
    1. Loads analyzer findings (Change and PythonSymbol records) for the run
    2. Applies mapping rules (FR-9) to group changes by target Confluence page
    3. Builds context objects for each rule and invokes TemplateEngine.render
    4. Persists generated patches and associates them with the run and pages

    Args:
        db: Database session
        run_id: ID of the run to generate patches for

    Returns:
        List of created Patch database records

    Raises:
        PatchGenerationError: If patch generation fails
    """
    try:
        # Verify run exists
        run = db.get(Run, run_id)
        if not run:
            raise PatchGenerationError(f"Run {run_id} not found")

        logger.info(
            f"Starting patch generation for run {run_id}",
            extra={"run_id": run_id},
        )

        # Step 1: Load analyzer findings for the run
        changes = get_changes_for_run(db, run_id)
        python_symbols = (
            db.execute(select(PythonSymbol).where(PythonSymbol.run_id == run_id))
            .scalars()
            .all()
        )

        if not changes:
            logger.info(
                f"No changes found for run {run_id}, no patches to generate",
                extra={"run_id": run_id},
            )
            return []

        # Get all active rules from database with template relationship loaded
        rules = (
            db.execute(select(Rule).options(joinedload(Rule.template)))
            .unique()
            .scalars()
            .all()
        )
        if not rules:
            logger.warning(
                "No rules found in database, cannot generate patches",
                extra={"run_id": run_id},
            )
            return []

        logger.info(
            f"Found {len(changes)} changes, {len(python_symbols)} Python symbols, and {len(rules)} rules",
            extra={
                "run_id": run_id,
                "change_count": len(changes),
                "symbol_count": len(python_symbols),
                "rule_count": len(rules),
            },
        )

        # Step 2: Apply mapping rules to group changes by target Confluence page
        # Group changes by file path first
        changes_by_file: dict[str, list[Change]] = defaultdict(list)
        for change in changes:
            changes_by_file[change.file_path].append(change)

        # Group by target page (rule.page_id) - multiple files can map to same page
        changes_by_page: dict[tuple[str, Rule], list[Change]] = defaultdict(list)
        files_without_rules = []

        for file_path, file_changes in changes_by_file.items():
            try:
                # Use rule engine to resolve target page (FR-9)
                matching_rule = resolve_target_page(file_path, list(rules))

                if not matching_rule:
                    files_without_rules.append(file_path)
                    logger.debug(
                        f"No matching rule for file: {file_path}",
                        extra={"run_id": run_id, "file_path": file_path},
                    )
                    continue

                # Group changes by page_id and rule
                page_id = matching_rule.page_id
                changes_by_page[(page_id, matching_rule)].extend(file_changes)

            except Exception as e:
                logger.exception(
                    f"Error processing file {file_path}: {e}",
                    extra={"run_id": run_id, "file_path": file_path},
                )
                files_without_rules.append(file_path)
                continue

        # Step 3: Generate one patch per page (combining all files for that page)
        patches_created = []
        for (page_id, rule), page_changes in changes_by_page.items():
            try:
                # Generate patch content
                # Use template engine if rule has an associated template
                diff_before = _generate_before_content(page_changes)
                diff_after = _generate_after_content(page_changes, rule, run)

                # Create patch record
                patch = Patch(
                    run_id=run_id,
                    page_id=page_id,
                    diff_before=diff_before,
                    diff_after=diff_after,
                    status="Proposed",
                )
                db.add(patch)
                patches_created.append(patch)

                logger.info(
                    f"Generated patch for page {page_id} using rule {rule.name}",
                    extra={
                        "run_id": run_id,
                        "page_id": page_id,
                        "rule_id": rule.id,
                        "rule_name": rule.name,
                        "template_id": rule.template_id,
                        "change_count": len(page_changes),
                    },
                )

            except Exception as e:
                logger.exception(
                    f"Error generating patch for page {page_id}: {e}",
                    extra={"run_id": run_id, "page_id": page_id},
                )
                # Continue with other pages even if one fails
                continue

        # Commit all patches at once
        if patches_created:
            db.commit()

            # Refresh records to get IDs
            for patch in patches_created:
                db.refresh(patch)

            logger.info(
                f"Successfully generated {len(patches_created)} patches for run {run_id}",
                extra={
                    "run_id": run_id,
                    "patch_count": len(patches_created),
                    "files_without_rules": len(files_without_rules),
                },
            )
        else:
            logger.info(
                f"No patches generated for run {run_id}",
                extra={
                    "run_id": run_id,
                    "files_without_rules": len(files_without_rules),
                },
            )

        # Update run status if no patches were generated
        if not patches_created and files_without_rules:
            if run.status == "Awaiting Review":
                run.status = "Completed (no patches)"
                db.commit()
                logger.info(
                    f"Updated run {run_id} status to 'Completed (no patches)'",
                    extra={"run_id": run_id},
                )

        return patches_created

    except PatchGenerationError:
        raise
    except Exception as e:
        db.rollback()
        logger.exception(
            f"Error generating patches for run {run_id}: {e}",
            extra={"run_id": run_id},
        )
        raise PatchGenerationError(f"Failed to generate patches: {e}") from e


def _build_patch_context(
    run: Run,
    rule: Rule,
    changes: list[Change],
    python_symbols: list[PythonSymbol],
) -> dict[str, Any]:
    """Build context object for template rendering from analyzer findings.

    Args:
        run: The Run database record
        rule: The matching Rule
        changes: List of Change records for this patch
        python_symbols: List of PythonSymbol records for the run

    Returns:
        Dictionary with context variables for template rendering
    """
    # Group changes by type
    added_changes = [c for c in changes if c.change_type == "added"]
    removed_changes = [c for c in changes if c.change_type == "removed"]
    modified_changes = [c for c in changes if c.change_type == "modified"]

    # Get Python symbols for changed files
    changed_files = {c.file_path for c in changes}
    relevant_symbols = [s for s in python_symbols if s.file_path in changed_files]

    # Build context
    context: dict[str, Any] = {
        "run": {
            "id": run.id,
            "repo": run.repo,
            "branch": run.branch,
            "commit_sha": run.commit_sha,
            "status": run.status,
        },
        "rule": {
            "id": rule.id,
            "name": rule.name,
            "selector": rule.selector,
            "space_key": rule.space_key,
            "page_id": rule.page_id,
        },
        "changes": {
            "all": [
                {
                    "file_path": c.file_path,
                    "symbol": c.symbol,
                    "change_type": c.change_type,
                    "signature_before": c.signature_before,
                    "signature_after": c.signature_after,
                }
                for c in changes
            ],
            "added": [
                {
                    "file_path": c.file_path,
                    "symbol": c.symbol,
                    "signature_after": c.signature_after,
                }
                for c in added_changes
            ],
            "removed": [
                {
                    "file_path": c.file_path,
                    "symbol": c.symbol,
                    "signature_before": c.signature_before,
                }
                for c in removed_changes
            ],
            "modified": [
                {
                    "file_path": c.file_path,
                    "symbol": c.symbol,
                    "signature_before": c.signature_before,
                    "signature_after": c.signature_after,
                }
                for c in modified_changes
            ],
        },
        "symbols": [
            {
                "file_path": s.file_path,
                "symbol_name": s.symbol_name,
                "qualified_name": s.qualified_name,
                "symbol_type": s.symbol_type,
                "docstring": s.docstring,
                "lineno": s.lineno,
                "metadata": s.symbol_metadata,
            }
            for s in relevant_symbols
        ],
        "files": list(changed_files),
    }

    return context


def _generate_before_content(changes: list[Change]) -> str:
    """Generate 'before' content for a patch.

    Args:
        changes: List of changes for a file

    Returns:
        String representation of the before state
    """
    lines = ["# Before Changes", ""]
    for change in changes:
        if change.change_type == "removed":
            lines.append(f"- **{change.symbol}** (removed)")
        elif change.change_type == "modified":
            lines.append(f"- **{change.symbol}** (modified)")
            if change.signature_before:
                lines.append(f"  - Previous: {change.signature_before}")
    return "\n".join(lines)


def _generate_after_content(changes: list[Change], rule: Rule, db: Session) -> str:
    """Generate 'after' content for a patch.

    Uses template if available, otherwise falls back to simple markdown generation.

    Args:
        changes: List of changes for a file
        rule: The matching rule for this file
        db: Database session for loading template

    Returns:
        String representation of the after state
    """
    # Try to use template if rule has one
    if rule.template_id:
        try:
            template = db.get(Template, rule.template_id)
            if template:
                variables = _extract_template_variables(changes, rule)
                try:
                    return TemplateEngine.render(
                        template.body, template.format, variables
                    )
                except (TemplateEngineError, TemplateValidationError) as e:
                    logger.warning(
                        f"Template rendering failed for rule {rule.id}, "
                        f"template {rule.template_id}: {e}. Falling back to simple generation.",
                        extra={
                            "rule_id": rule.id,
                            "template_id": rule.template_id,
                            "error": str(e),
                        },
                    )
                    # Fall through to simple generation
        except Exception as e:
            logger.warning(
                f"Error loading template {rule.template_id} for rule {rule.id}: {e}. "
                "Falling back to simple generation.",
                extra={"rule_id": rule.id, "template_id": rule.template_id},
            )
            # Fall through to simple generation

    # Fallback to simple markdown generation
    return _generate_simple_after_content(changes, rule)


def _extract_template_variables(changes: list[Change], rule: Rule) -> dict:
    """Extract variables from changes for template rendering.

    Args:
        changes: List of changes for a file
        rule: The matching rule

    Returns:
        Dictionary of variables for template substitution
    """
    file_path = changes[0].file_path if changes else ""

    # Group changes by type
    added_changes = [c for c in changes if c.change_type == "added"]
    modified_changes = [c for c in changes if c.change_type == "modified"]
    removed_changes = [c for c in changes if c.change_type == "removed"]

    # Extract symbol names
    added_symbols = [c.symbol for c in added_changes]
    modified_symbols = [c.symbol for c in modified_changes]
    removed_symbols = [c.symbol for c in removed_changes]

    # Build variables dictionary
    variables = {
        "file_path": file_path,
        "rule_name": rule.name,
        "page_id": rule.page_id,
        "space_key": rule.space_key,
        "change_count": len(changes),
        "added_count": len(added_changes),
        "modified_count": len(modified_changes),
        "removed_count": len(removed_changes),
        "added_symbols": ", ".join(added_symbols) if added_symbols else "",
        "modified_symbols": ", ".join(modified_symbols) if modified_symbols else "",
        "removed_symbols": ", ".join(removed_symbols) if removed_symbols else "",
    }

    # Add detailed change information
    change_details = []
    for change in changes:
        detail = {
            "symbol": change.symbol,
            "type": change.change_type,
        }
        if change.signature_before:
            detail["signature_before"] = str(change.signature_before)
        if change.signature_after:
            detail["signature_after"] = str(change.signature_after)
        change_details.append(detail)

    variables["changes"] = change_details

    # Add first change details for simple templates
    if changes:
        first_change = changes[0]
        variables["symbol"] = first_change.symbol
        variables["change_type"] = first_change.change_type
        if first_change.signature_after:
            variables["signature"] = str(first_change.signature_after)
        elif first_change.signature_before:
            variables["signature"] = str(first_change.signature_before)

    return variables


def _generate_simple_after_content(changes: list[Change], rule: Rule) -> str:
    """Generate simple 'after' content for a patch (fallback).

    Args:
        changes: List of changes for a file
        rule: The matching rule for this file
        run: The run entity for metadata

    Returns:
        String representation of the after state
    """
    # If rule has a template, use template engine
    if rule.template_id and rule.template:
        try:
            engine = TemplateEngine()
            variables = _build_template_variables(changes, rule, run)
            return engine.render_template(rule.template, variables)
        except Exception as e:
            logger.warning(
                f"Failed to render template for rule {rule.id}: {e}. "
                "Falling back to default format.",
                extra={"rule_id": rule.id, "template_id": rule.template_id},
            )
            # Fall through to default format

    # Default hardcoded format (fallback or when no template)
    lines = ["# After Changes", ""]
    lines.append(f"**File:** `{changes[0].file_path}`")
    lines.append(f"**Target Page:** {rule.page_id}")
    lines.append(f"**Rule:** {rule.name}")
    lines.append("")

    for change in changes:
        if change.change_type == "added":
            lines.append(f"- **{change.symbol}** (added)")
        elif change.change_type == "modified":
            lines.append(f"- **{change.symbol}** (modified)")
            if change.signature_after:
                lines.append(f"  - New: {change.signature_after}")
        elif change.change_type == "removed":
            lines.append(f"- **{change.symbol}** (removed)")

    lines.append("")
    lines.append("---")
    lines.append("*This patch was automatically generated by AutoDoc*")

    return "\n".join(lines)


def _build_template_variables(changes: list[Change], rule: Rule, run: Run) -> dict:
    """Build variable context for template rendering.

    Args:
        changes: List of changes for a file
        rule: The matching rule
        run: The run entity

    Returns:
        Dictionary of variables for template substitution
    """
    file_path = changes[0].file_path if changes else ""

    # Build changes list with structured data
    changes_data = []
    for change in changes:
        change_data = {
            "symbol": change.symbol,
            "change_type": change.change_type,
            "signature_before": change.signature_before,
            "signature_after": change.signature_after,
        }
        changes_data.append(change_data)

    # Build a string representation of changes for templates that expect {{changes.all}}
    # This is a workaround for templates that can't iterate over lists
    changes_str = "\n".join(
        [f"- {c['symbol']} ({c['change_type']})" for c in changes_data]
    )

    # Build variables context
    variables = {
        "file_path": file_path,
        "rule": {
            "name": rule.name,
            "page_id": rule.page_id,
            "space_key": rule.space_key,
        },
        "run": {
            "repo": run.repo,
            "branch": run.branch,
            "commit_sha": run.commit_sha,
        },
        "changes": {
            "all": changes_str,  # String representation for {{changes.all}}
        },
        "change_count": len(changes),
        "files": file_path,  # Single file path as string
    }

    # Add individual change data if there's only one change
    if len(changes) == 1:
        change = changes[0]
        variables["symbol"] = change.symbol
        variables["change_type"] = change.change_type
        if change.signature_before:
            variables["signature_before"] = change.signature_before
        if change.signature_after:
            variables["signature_after"] = change.signature_after

    return variables
