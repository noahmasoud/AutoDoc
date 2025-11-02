"""Service for detecting changes between run artifacts."""

import logging
from typing import Any

from schemas.changes import RunArtifact, SymbolData, ChangeDetected


logger = logging.getLogger(__name__)


class ChangeDetectionError(Exception):
    """Raised when change detection fails."""


def detect_changes(
    previous_artifact: RunArtifact | None,
    current_artifact: RunArtifact,
) -> list[ChangeDetected]:
    """Detect changes between two run artifacts.

    This function compares symbols from the previous and current artifacts,
    identifying added, removed, and modified symbols based on name and type.

    Args:
        previous_artifact: Previous run's artifact (None for initial run)
        current_artifact: Current run's artifact

    Returns:
        List of detected changes

    Raises:
        ChangeDetectionError: If detection fails
    """
    try:
        # If no previous artifact, all current symbols are added
        if previous_artifact is None:
            logger.info(
                "No previous artifact found - all symbols are additions",
                extra={"current_run_id": current_artifact.run_id},
            )
            return _detect_additions_only(current_artifact)

        # Create lookup maps by symbol key (name + type + file_path)
        previous_symbols = _create_symbol_map(previous_artifact.symbols)
        current_symbols = _create_symbol_map(current_artifact.symbols)

        logger.debug(
            f"Comparing artifacts: previous={len(previous_symbols)}, "
            f"current={len(current_symbols)}",
            extra={
                "previous_run_id": previous_artifact.run_id,
                "current_run_id": current_artifact.run_id,
            },
        )

        changes = []

        # Detect removals (in previous but not in current)
        changes.extend(
            _detect_removals(previous_symbols, current_symbols),
        )

        # Detect additions (in current but not in previous)
        changes.extend(
            _detect_additions(current_symbols, previous_symbols),
        )

        # Detect modifications (in both but changed)
        changes.extend(
            _detect_modifications(previous_symbols, current_symbols),
        )

        logger.info(
            f"Detected {len(changes)} changes: "
            f"{sum(1 for c in changes if c.change_type == 'added')} added, "
            f"{sum(1 for c in changes if c.change_type == 'removed')} removed, "
            f"{sum(1 for c in changes if c.change_type == 'modified')} modified",
            extra={
                "previous_run_id": previous_artifact.run_id,
                "current_run_id": current_artifact.run_id,
                "total_changes": len(changes),
            },
        )

        return changes

    except Exception as e:
        logger.exception(
            f"Error detecting changes: {e}",
            extra={
                "previous_run_id": previous_artifact.run_id
                if previous_artifact
                else None,
                "current_run_id": current_artifact.run_id,
            },
        )
        raise ChangeDetectionError(f"Failed to detect changes: {e}") from e


def _create_symbol_map(symbols: list[SymbolData]) -> dict[str, SymbolData]:
    """Create a lookup map from symbols keyed by name+type+file_path.

    Args:
        symbols: List of symbols

    Returns:
        Dictionary mapping symbol key to SymbolData
    """
    symbol_map = {}
    for symbol in symbols:
        key = _get_symbol_key(symbol)
        if key in symbol_map:
            logger.warning(
                f"Duplicate symbol key found: {key}",
                extra={"symbol_name": symbol.symbol_name},
            )
        symbol_map[key] = symbol
    return symbol_map


def _get_symbol_key(symbol: SymbolData) -> str:
    """Generate a unique key for a symbol.

    The key combines file_path, symbol_name, and symbol_type to uniquely
    identify a symbol across different runs.

    Args:
        symbol: Symbol data

    Returns:
        Unique key string
    """
    return f"{symbol.file_path}:{symbol.symbol_name}:{symbol.symbol_type}"


def _detect_additions_only(current_artifact: RunArtifact) -> list[ChangeDetected]:
    """Detect additions when no previous artifact exists.

    Args:
        current_artifact: Current run's artifact

    Returns:
        List of changes (all marked as 'added')
    """
    changes = []
    for symbol in current_artifact.symbols:
        change = ChangeDetected(
            file_path=symbol.file_path,
            symbol_name=symbol.symbol_name,
            change_type="added",
            signature_before=None,
            signature_after=_symbol_to_signature_dict(symbol),
            is_breaking=False,  # Additions are not breaking
        )
        changes.append(change)
    return changes


def _detect_removals(
    previous_symbols: dict[str, SymbolData],
    current_symbols: dict[str, SymbolData],
) -> list[ChangeDetected]:
    """Detect removed symbols.

    Args:
        previous_symbols: Previous symbol map
        current_symbols: Current symbol map

    Returns:
        List of removed symbols
    """
    changes = []
    for key, symbol in previous_symbols.items():
        if key not in current_symbols:
            change = ChangeDetected(
                file_path=symbol.file_path,
                symbol_name=symbol.symbol_name,
                change_type="removed",
                signature_before=_symbol_to_signature_dict(symbol),
                signature_after=None,
                is_breaking=True,  # Removals are always breaking
            )
            changes.append(change)
    return changes


def _detect_additions(
    current_symbols: dict[str, SymbolData],
    previous_symbols: dict[str, SymbolData],
) -> list[ChangeDetected]:
    """Detect added symbols.

    Args:
        current_symbols: Current symbol map
        previous_symbols: Previous symbol map

    Returns:
        List of added symbols
    """
    changes = []
    for key, symbol in current_symbols.items():
        if key not in previous_symbols:
            change = ChangeDetected(
                file_path=symbol.file_path,
                symbol_name=symbol.symbol_name,
                change_type="added",
                signature_before=None,
                signature_after=_symbol_to_signature_dict(symbol),
                is_breaking=False,  # Additions are not breaking
            )
            changes.append(change)
    return changes


def _detect_modifications(
    previous_symbols: dict[str, SymbolData],
    current_symbols: dict[str, SymbolData],
) -> list[ChangeDetected]:
    """Detect modified symbols.

    Args:
        previous_symbols: Previous symbol map
        current_symbols: Current symbol map

    Returns:
        List of modified symbols
    """
    changes = []
    for key, previous_symbol in previous_symbols.items():
        if key in current_symbols:
            current_symbol = current_symbols[key]

            # Check if symbols are actually different
            if _symbols_differ(previous_symbol, current_symbol):
                is_breaking = _is_breaking_change(
                    previous_symbol,
                    current_symbol,
                )

                change = ChangeDetected(
                    file_path=current_symbol.file_path,
                    symbol_name=current_symbol.symbol_name,
                    change_type="modified",
                    signature_before=_symbol_to_signature_dict(previous_symbol),
                    signature_after=_symbol_to_signature_dict(current_symbol),
                    is_breaking=is_breaking,
                )
                changes.append(change)

    return changes


def _symbols_differ(
    previous: SymbolData,
    current: SymbolData,
) -> bool:
    """Check if two symbols are different.

    Args:
        previous: Previous symbol
        current: Current symbol

    Returns:
        True if symbols differ, False otherwise
    """
    # Compare signatures
    if _signatures_differ(previous.signature, current.signature):
        return True

    # Compare docstrings
    if previous.docstring != current.docstring:
        return True

    # Compare public visibility
    return previous.is_public != current.is_public


def _signatures_differ(
    previous: Any | None,
    current: Any | None,
) -> bool:
    """Check if two signatures are different.

    Args:
        previous: Previous signature
        current: Current signature

    Returns:
        True if signatures differ, False otherwise
    """
    # Both None - no difference
    if previous is None and current is None:
        return False

    # One None and one not - difference
    if previous is None or current is None:
        return True

    # Compare return annotations
    if previous.return_annotation != current.return_annotation:
        return True

    # Compare parameter count
    if len(previous.parameters) != len(current.parameters):
        return True

    # Compare parameters in detail
    for prev_param, curr_param in zip(
        previous.parameters,
        current.parameters,
        strict=True,
    ):
        if _parameters_differ(prev_param, curr_param):
            return True

    return False


def _parameters_differ(
    previous: Any,
    current: Any,
) -> bool:
    """Check if two parameters are different.

    Args:
        previous: Previous parameter
        current: Current parameter

    Returns:
        True if parameters differ, False otherwise
    """
    if previous.name != current.name:
        return True
    if previous.annotation != current.annotation:
        return True
    if previous.default_value != current.default_value:
        return True
    return previous.kind != current.kind


def _is_breaking_change(  # noqa: PLR0911
    previous: SymbolData,
    current: SymbolData,
) -> bool:
    """Determine if a change is breaking.

    A breaking change is one that would break existing code:
    - Parameter removal
    - Return type change
    - Parameter type change

    Args:
        previous: Previous symbol
        current: Current symbol

    Returns:
        True if the change is breaking, False otherwise
    """
    # If signatures don't exist, check docstring/visibility only (not breaking)
    if previous.signature is None or current.signature is None:
        return False

    # Return type change is breaking
    if previous.signature.return_annotation != current.signature.return_annotation:
        return True

    # Parameter addition is breaking
    if len(previous.signature.parameters) < len(current.signature.parameters):
        return True

    # Parameter removal is breaking
    if len(previous.signature.parameters) > len(current.signature.parameters):
        return True

    # Check for parameter type changes
    for prev_param, curr_param in zip(
        previous.signature.parameters,
        current.signature.parameters,
        strict=True,
    ):
        # Parameter name changed - breaking
        if prev_param.name != curr_param.name:
            return True

        # Parameter type changed - breaking
        if prev_param.annotation != curr_param.annotation:
            # Allow None vs explicit type (not breaking)
            if prev_param.annotation is not None and curr_param.annotation is not None:
                return True

        # Parameter lost default value - breaking
        if prev_param.default_value is not None and curr_param.default_value is None:
            return True

    return False


def _symbol_to_signature_dict(symbol: SymbolData) -> dict[str, Any]:
    """Convert SymbolData to a signature dictionary.

    This creates a serializable representation of the symbol's signature
    for storage in the database.

    Args:
        symbol: Symbol data

    Returns:
        Dictionary representation of the signature
    """
    signature_dict = {
        "name": symbol.symbol_name,
        "symbol_type": symbol.symbol_type,
        "docstring": symbol.docstring,
        "is_public": symbol.is_public,
    }

    if symbol.signature:
        signature_dict.update(
            {
                "return_annotation": symbol.signature.return_annotation,
                "line_start": symbol.signature.line_start,
                "line_end": symbol.signature.line_end,
                "parameters": [
                    {
                        "name": param.name,
                        "annotation": param.annotation,
                        "default_value": param.default_value,
                        "kind": param.kind,
                    }
                    for param in symbol.signature.parameters
                ],
            },
        )

    return signature_dict
