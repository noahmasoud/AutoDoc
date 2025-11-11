"""Service for loading run artifacts from the database."""

import logging
from typing import Any
from sqlalchemy.orm import Session
from sqlalchemy import select

from db.models import Run, Change
from schemas.changes import RunArtifact, SymbolData, SignatureInfo, ParameterInfo


logger = logging.getLogger(__name__)


class ArtifactLoadError(Exception):
    """Raised when artifact loading fails."""


def load_run_artifact(db: Session, run_id: int) -> RunArtifact:
    """Load a complete run artifact from the database.

    This function loads both the run metadata and all associated symbol data
    stored in the changes table. The signature_before and signature_after
    fields contain the JSON artifacts from AST analysis.

    Args:
        db: Database session
        run_id: ID of the run to load

    Returns:
        RunArtifact containing all symbol data for the run

    Raises:
        ArtifactLoadError: If run not found or data is invalid
    """
    try:
        # Load run metadata
        run = db.get(Run, run_id)
        if not run:
            raise ArtifactLoadError(f"Run {run_id} not found")

        # Load all changes (which contain symbol data artifacts)
        changes = (
            db.execute(
                select(Change).where(Change.run_id == run_id),
            )
            .scalars()
            .all()
        )

        logger.info(
            f"Loaded run {run_id}: {len(changes)} changes found",
            extra={"run_id": run_id, "num_changes": len(changes)},
        )

        # Convert changes to symbol data
        symbols = []
        for change in changes:
            symbol_data = _change_to_symbol_data(change)
            if symbol_data:
                symbols.append(symbol_data)

        artifact = RunArtifact(
            run_id=run.id,
            repo=run.repo,
            branch=run.branch,
            commit_sha=run.commit_sha,
            symbols=symbols,
        )

        logger.debug(
            f"Created artifact with {len(artifact.symbols)} symbols",
            extra={"run_id": run_id},
        )

        return artifact

    except ArtifactLoadError:
        raise
    except Exception as e:
        logger.exception(
            f"Error loading artifact for run {run_id}: {e}",
            extra={"run_id": run_id},
        )
        raise ArtifactLoadError(f"Failed to load artifact: {e}") from e


def load_artifact_from_run(
    db: Session,
    run: Run,
) -> RunArtifact:
    """Load artifact from an existing Run object.

    This is a convenience function that avoids a database query
    when you already have the Run object loaded.

    Args:
        db: Database session
        run: Run object to load artifact from

    Returns:
        RunArtifact containing all symbol data for the run

    Raises:
        ArtifactLoadError: If data is invalid
    """
    try:
        # Load all changes (which contain symbol data artifacts)
        changes = (
            db.execute(
                select(Change).where(Change.run_id == run.id),
            )
            .scalars()
            .all()
        )

        # Convert changes to symbol data
        symbols = []
        for change in changes:
            symbol_data = _change_to_symbol_data(change)
            if symbol_data:
                symbols.append(symbol_data)

        return RunArtifact(
            run_id=run.id,
            repo=run.repo,
            branch=run.branch,
            commit_sha=run.commit_sha,
            symbols=symbols,
        )

    except Exception as e:
        logger.exception(
            f"Error loading artifact for run {run.id}: {e}",
            extra={"run_id": run.id},
        )
        raise ArtifactLoadError(f"Failed to load artifact: {e}") from e


def _change_to_symbol_data(change: Change) -> SymbolData | None:
    """Convert a Change model to SymbolData.

    The Change model stores artifacts in signature_before or signature_after
    fields. This function extracts the relevant data.

    For created symbols, we look at signature_after.
    For deleted symbols, we look at signature_before.
    For modified symbols, signature_after is the current state.

    Args:
        change: Change model to convert

    Returns:
        SymbolData or None if conversion fails
    """
    try:
        # Determine which signature to use based on change type
        # For 'added', we use signature_after (the new state)
        # For 'removed', we use signature_before (the old state)
        # For 'modified', we use signature_after (the current state)

        signature_data = None
        if change.change_type in ("added", "modified"):
            signature_data = change.signature_after
        elif change.change_type == "removed":
            signature_data = change.signature_before

        if not signature_data:
            logger.warning(
                f"No signature data found for change {change.id}",
                extra={"change_id": change.id, "change_type": change.change_type},
            )
            return None

        # Parse the signature JSON into structured data
        signature = _parse_signature(signature_data)

        # Create SymbolData
        # Note: We need to infer symbol_type from the signature if available
        symbol_type = signature_data.get("symbol_type", "function")

        return SymbolData(
            file_path=change.file_path,
            symbol_name=change.symbol,
            symbol_type=symbol_type,
            signature=signature,
            docstring=signature_data.get("docstring"),
            is_public=signature_data.get("is_public", True),
        )

    except Exception as e:
        logger.exception(
            f"Error converting change {change.id} to symbol data: {e}",
            extra={"change_id": change.id},
        )
        return None


def _parse_signature(signature_data: dict[str, Any]) -> SignatureInfo | None:
    """Parse signature data from JSON into SignatureInfo object.

    Args:
        signature_data: Dictionary containing signature information

    Returns:
        SignatureInfo or None if parsing fails
    """
    try:
        # Extract parameters
        parameters = []
        params_list = signature_data.get("parameters", [])
        for param in params_list:
            param_info = ParameterInfo(
                name=param.get("name", ""),
                annotation=param.get("annotation"),
                default_value=param.get("default_value"),
                kind=param.get("kind"),
            )
            parameters.append(param_info)

        return SignatureInfo(
            name=signature_data.get("name", ""),
            parameters=parameters,
            return_annotation=signature_data.get("return_annotation"),
            line_start=signature_data.get("line_start"),
            line_end=signature_data.get("line_end"),
        )

    except Exception as e:
        logger.warning(
            f"Error parsing signature: {e}",
            exc_info=True,
        )
        return None
