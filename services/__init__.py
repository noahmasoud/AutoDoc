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
    ConfluenceConfigurationError,
    ConfluenceConflictError,
    ConfluenceError,
    ConfluenceHTTPError,
)
from services.patch_generator import (
    PatchGenerationError,
    generate_patches_for_run,
)
from services.rule_engine import (
    InvalidSelectorError,
    InvalidTargetError,
    RuleEngineError,
    is_glob_pattern,
    match_file_to_rules,
    match_glob,
    match_regex,
    resolve_target_page,
    validate_rule_target,
    validate_selector,
)
from services.go_analyzer import GoAnalyzer
from services.go_parser import GoParser, GoParserError, GoNotFoundError
from services.go_symbol_ingestor import GoSymbolIngestor
from services.javascript_analyzer import JavaScriptAnalyzer
from services.javascript_parser import (
    JavaScriptParser,
    JavaScriptParserError,
    NodeJSNotFoundError,
    ParseError,
)
from services.javascript_symbol_ingestor import JavaScriptSymbolIngestor
from services.typescript_analyzer import TypeScriptAnalyzer
from services.typescript_parser import (
    TypeScriptParser,
    TypeScriptParserError,
)
from services.rule_matcher import (
    RuleMatch,
    RuleMatcher,
)
from services.template_engine import (
    TemplateEngine,
    TemplateEngineError,
    TemplateValidationError,
)

__all__ = [
    "ArtifactLoadError",
    "ChangeDetectionError",
    "ChangePersistenceError",
    "ConfluenceClient",
    "ConfluenceConfigurationError",
    "ConfluenceConflictError",
    "ConfluenceError",
    "ConfluenceHTTPError",
    "GoAnalyzer",
    "GoNotFoundError",
    "GoParser",
    "GoParserError",
    "GoSymbolIngestor",
    "InvalidSelectorError",
    "InvalidTargetError",
    "JavaScriptAnalyzer",
    "JavaScriptParser",
    "JavaScriptParserError",
    "JavaScriptSymbolIngestor",
    "NodeJSNotFoundError",
    "ParseError",
    "PatchGenerationError",
    "RuleEngineError",
    "RuleMatch",
    "RuleMatcher",
    "TypeScriptAnalyzer",
    "TemplateEngine",
    "TemplateEngineError",
    "TemplateValidationError",
    "TypeScriptParser",
    "TypeScriptParserError",
    "detect_changes",
    "get_breaking_changes_summary",
    "get_changes_for_run",
    "generate_patches_for_run",
    "get_changes_by_type",
    "is_glob_pattern",
    "load_artifact_from_run",
    "load_run_artifact",
    "match_file_to_rules",
    "match_glob",
    "match_regex",
    "resolve_target_page",
    "save_changes_to_database",
    "validate_rule_target",
    "validate_selector",
]
