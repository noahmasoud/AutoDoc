"""Schema exports for AutoDoc."""

from schemas.changes import (
    ParameterInfo,
    SignatureInfo,
    SymbolData,
    RunArtifact,
    ChangeDetected,
    ChangeCreate,
    ChangeOut,
)
from schemas.patches import PatchBase, PatchCreate, PatchUpdate, PatchOut
from schemas.rules import RuleBase, RuleCreate, RuleUpdate, RuleOut
from schemas.runs import RunCreate, RunOut, RunsPage
from schemas.templates import TemplateBase, TemplateCreate, TemplateUpdate, TemplateOut

__all__ = [
    # Changes
    "ParameterInfo",
    "SignatureInfo",
    "SymbolData",
    "RunArtifact",
    "ChangeDetected",
    "ChangeCreate",
    "ChangeOut",
    # Patches
    "PatchBase",
    "PatchCreate",
    "PatchUpdate",
    "PatchOut",
    # Rules
    "RuleBase",
    "RuleCreate",
    "RuleUpdate",
    "RuleOut",
    # Runs
    "RunCreate",
    "RunOut",
    "RunsPage",
    # Templates
    "TemplateBase",
    "TemplateCreate",
    "TemplateUpdate",
    "TemplateOut",
]
