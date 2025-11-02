"""Pydantic schemas for change detection and symbol data."""

from typing import Any
from pydantic import BaseModel


class ParameterInfo(BaseModel):
    """Information about a function parameter."""

    name: str
    annotation: str | None = None
    default_value: str | None = None
    kind: str | None = None  # pos, varargs, varkeyword, keyword


class SignatureInfo(BaseModel):
    """Information about a function or method signature."""

    name: str
    parameters: list[ParameterInfo] = []
    return_annotation: str | None = None
    line_start: int | None = None
    line_end: int | None = None


class SymbolData(BaseModel):
    """Symbol data extracted from AST analysis."""

    file_path: str
    symbol_name: str
    symbol_type: str  # 'function', 'class', 'method'
    signature: SignatureInfo | None = None
    docstring: str | None = None
    is_public: bool = True


class RunArtifact(BaseModel):
    """Complete artifact from a single run."""

    run_id: int
    repo: str
    branch: str
    commit_sha: str
    symbols: list[SymbolData] = []


class ChangeDetected(BaseModel):
    """A detected change in a symbol."""

    file_path: str
    symbol_name: str
    change_type: str  # 'added', 'removed', 'modified'
    signature_before: dict[str, Any] | None = None
    signature_after: dict[str, Any] | None = None
    is_breaking: bool = False


class ChangeCreate(BaseModel):
    """Schema for creating a change record in the database."""

    run_id: int
    file_path: str
    symbol: str
    change_type: str
    signature_before: dict[str, Any] | None = None
    signature_after: dict[str, Any] | None = None


class ChangeOut(BaseModel):
    """Schema for change output."""

    id: int
    run_id: int
    file_path: str
    symbol: str
    change_type: str
    signature_before: dict[str, Any] | None = None
    signature_after: dict[str, Any] | None = None

    model_config = {"from_attributes": True}
