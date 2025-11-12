"""Services module for AutoDoc."""

from services.artifact_loader import (
    ArtifactLoadError,
    load_artifact_from_run,
    load_run_artifact,
)
from services.change_detector import (
    ChangeDetectionError,
    detect_changes,
    get_breaking_changes_summary,
)
from services.change_persister import (
    ChangePersistenceError,
    get_changes_for_run,
    get_changes_by_type,
    save_changes_to_database,
)
from services.confluence_client import (
    ConfluenceClient,
    ConfluenceClientError,
    ConfluenceConfigurationError,
    ConfluenceRequestError,
    get_confluence_client,
)
from services.typescript_analyzer import TypeScriptAnalyzer
from services.typescript_parser import (
    NodeJSNotFoundError,
    ParseError,
    TypeScriptParser,
    TypeScriptParserError,
)

__all__ = [
    "ArtifactLoadError",
    "ChangeDetectionError",
    "ChangePersistenceError",
    "ConfluenceClient",
    "ConfluenceClientError",
    "ConfluenceConfigurationError",
    "ConfluenceRequestError",
    "NodeJSNotFoundError",
    "ParseError",
    "TypeScriptAnalyzer",
    "TypeScriptParser",
    "TypeScriptParserError",
    "detect_changes",
    "get_confluence_client",
    "get_breaking_changes_summary",
    "get_changes_for_run",
    "get_changes_by_type",
    "load_artifact_from_run",
    "load_run_artifact",
    "save_changes_to_database",
]
